from concurrent.futures import ThreadPoolExecutor, as_completed

import hashlib
import json
import os
import re
import secrets
import threading
import time
from datetime import datetime, timedelta
from functools import wraps

from flask import (
    Flask, abort, flash, jsonify, make_response, redirect, render_template,
    request, session, url_for
)
import sqlite3
from werkzeug.security import check_password_hash, generate_password_hash

from Database.ai_engine import recommend_career
from Database.job_market import get_job_market_data
from Database.nlp_engine import extract as nlp_extract
from Database import ml_model
from Database.roadmap import build_roadmap, required_subjects
from Database.careers_data import CAREER_SEEDS, SEED_VERSION
from Database import personality

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# The database path can be overridden (used by the automated tests).
DB_PATH = os.environ.get(
    "CAREER_DB_PATH", os.path.join(BASE_DIR, "Database", "career_counseling.db")
)


def load_secret_key():
    """Secret key from the SECRET_KEY environment variable, or a random key
    generated once and kept in instance/secret_key (never in the code)."""
    if os.environ.get("SECRET_KEY"):
        return os.environ["SECRET_KEY"]
    path = os.path.join(BASE_DIR, "instance", "secret_key")
    try:
        with open(path, encoding="utf-8") as handle:
            key = handle.read().strip()
            if key:
                return key
    except OSError:
        pass
    key = secrets.token_hex(32)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(key)
    return key


app = Flask(__name__)
app.secret_key = load_secret_key()
app.config.update(
    PERMANENT_SESSION_LIFETIME=timedelta(minutes=30),   # SRS session timeout (30 minutes)
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    MAX_CONTENT_LENGTH=1 * 1024 * 1024,
)

# Login rate limiting: at most 5 failed attempts per email + IP in 10 minutes.
LOGIN_MAX_FAILURES = 5
LOGIN_WINDOW_SECONDS = 600
_failed_logins = {}

SECURITY_QUESTIONS = [
    "What was the name of your first school?",
    "In which city were you born?",
    "What is the name of your favourite teacher?",
    "What was the name of your first pet?",
    "What is your favourite book?",
]
RESET_LINK_HOURS = 1


def hash_secret(value):
    """Hash passwords and security answers with PBKDF2-SHA256 (SRS NFR-SEC-01).
    Hashes created earlier with another method still verify normally."""
    return generate_password_hash(value, method="pbkdf2:sha256:600000")


def too_many_attempts(key):
    """True when this key has had LOGIN_MAX_FAILURES failures recently."""
    now = time.time()
    recent = [t for t in _failed_logins.get(key, []) if now - t < LOGIN_WINDOW_SECONDS]
    _failed_logins[key] = recent
    return len(recent) >= LOGIN_MAX_FAILURES


def record_failure(key):
    _failed_logins.setdefault(key, []).append(time.time())


def normalise_answer(answer):
    """Answers are compared ignoring case and extra spaces."""
    return " ".join(str(answer or "").lower().split())


def token_digest(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

# Plausible age range for each education level (catches inputs like
# "Matric, age 70" before they reach the recommendation engine).
AGE_RANGE_BY_EDUCATION = {
    "matric": (12, 30),
    "o level": (12, 30),
    "intermediate": (14, 35),
    "a level": (14, 35),
    "bs": (17, 50),
    "ms": (21, 60),
}
MAX_SKILLS = 8
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_connection():
    connection = sqlite3.connect(DB_PATH)

    connection.row_factory = sqlite3.Row
    # SQLite leaves foreign keys off by default; enforce them (SRS DB-04)
    connection.execute("PRAGMA foreign_keys = ON")

    return connection



# =========================================================
# ACCOUNTS (SIGN UP / SIGN IN)
# =========================================================

def init_db():
    connection = get_connection()
    # A brand-new (or deleted) database has no career tables yet: build them
    # first; the newer careers and Holland codes are added further below.
    has_careers = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'Careers'"
    ).fetchone()
    if not has_careers:
        connection.close()
        from Database.create_database import build
        build(DB_PATH, verbose=False)
        connection = get_connection()
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS Accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL,
            age INTEGER,
            gender TEXT
        );
        CREATE TABLE IF NOT EXISTS Assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            inputs_json TEXT NOT NULL,
            top_career TEXT,
            FOREIGN KEY(account_id) REFERENCES Accounts(id)
        );
        CREATE TABLE IF NOT EXISTS Feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            assessment_id INTEGER NOT NULL UNIQUE,
            account_id INTEGER NOT NULL,
            helpful INTEGER NOT NULL,
            comment TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(assessment_id) REFERENCES Assessments(id),
            FOREIGN KEY(account_id) REFERENCES Accounts(id)
        );
        """
    )
    migrations = {
        "Accounts": (("age", "INTEGER"), ("gender", "TEXT"),
                     ("is_admin", "INTEGER NOT NULL DEFAULT 0"),
                     ("security_question", "TEXT"), ("security_answer_hash", "TEXT"),
                     ("reset_token_hash", "TEXT"), ("reset_token_expires", "TEXT")),
        "Assessments": (("results_json", "TEXT"),),
        "Careers": (("holland_code", "TEXT"),),
    }
    for table, columns in migrations.items():
        existing = {r[1] for r in connection.execute(f"PRAGMA table_info({table})")}
        for column, kind in columns:
            if column not in existing:
                connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {kind}")
    connection.commit()
    seed_careers(connection)
    # Holland personality code for every career that does not have one yet
    for row in connection.execute(
            "SELECT id, career_name, interest FROM Careers "
            "WHERE holland_code IS NULL OR holland_code = ''").fetchall():
        connection.execute("UPDATE Careers SET holland_code = ? WHERE id = ?",
                           (personality.code_for(dict(row)), row["id"]))
    # Indexes on frequently queried columns (SRS DB-08)
    connection.executescript(
        """
        CREATE INDEX IF NOT EXISTS idx_assessments_account ON Assessments(account_id);
        CREATE INDEX IF NOT EXISTS idx_feedback_account ON Feedback(account_id);
        CREATE INDEX IF NOT EXISTS idx_career_interests_career ON CareerInterests(career_id);
        CREATE INDEX IF NOT EXISTS idx_accounts_reset_token ON Accounts(reset_token_hash);
        """
    )
    connection.commit()
    connection.close()


def seed_careers(connection):
    """Add the extra careers once, keeping existing accounts and reports.

    A version number in the Meta table records that seeding has run, so a
    career that an admin later deletes is not added back."""
    connection.execute("CREATE TABLE IF NOT EXISTS Meta (key TEXT PRIMARY KEY, value TEXT)")
    row = connection.execute("SELECT value FROM Meta WHERE key = 'careers_seed'").fetchone()
    current = int(row["value"]) if row else 1
    if current >= SEED_VERSION:
        return
    interest_ids = {r["interest_name"]: r["id"] for r in connection.execute(
        "SELECT id, interest_name FROM Interests")}
    existing = {r["career_name"].lower() for r in connection.execute(
        "SELECT career_name FROM Careers")}
    new_careers = [career for version, careers in sorted(CAREER_SEEDS.items())
                   if version > current for career in careers]
    for (name, education, field, minimum, interest, related, description,
         skills, scope, salary, resources) in new_careers:
        if name.lower() in existing:
            continue
        cursor = connection.execute(
            "INSERT INTO Careers (career_name, education_required, field_required, "
            "minimum_percentage, interest, description, required_skills, future_scope, "
            "average_salary, learning_resources, holland_code) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (name, education, field, minimum, interest, description, skills, scope,
             salary, resources, personality.HOLLAND_CODES.get(name)))
        for interest_name in dict.fromkeys([interest] + related):
            if interest_name in interest_ids:
                connection.execute(
                    "INSERT INTO CareerInterests (career_id, interest_id) VALUES (?, ?)",
                    (cursor.lastrowid, interest_ids[interest_name]))
    connection.execute(
        "INSERT OR REPLACE INTO Meta (key, value) VALUES ('careers_seed', ?)",
        (str(SEED_VERSION),))
    connection.commit()


def all_skill_names():
    """Every skill required by any career, for the skill picker."""
    connection = get_connection()
    rows = connection.execute("SELECT required_skills FROM Careers").fetchall()
    connection.close()
    names = {}
    for row in rows:
        for skill in str(row["required_skills"] or "").split(","):
            skill = skill.strip()
            if skill:
                names.setdefault(skill.lower(), skill)
    return sorted(names.values(), key=str.lower)


def current_account():
    if "account_id" not in session:
        return None
    connection = get_connection()
    row = connection.execute(
        "SELECT * FROM Accounts WHERE id = ?", (session["account_id"],)
    ).fetchone()
    connection.close()
    return row


def valid_age_and_gender(age_text, gender):
    try:
        age = int(age_text)
    except (TypeError, ValueError):
        return None, "Age must be a whole number."
    if not 10 <= age <= 100:
        return None, "Age must be between 10 and 100."
    if gender not in ("Male", "Female"):
        return None, "Please select your gender."
    return age, None


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "account_id" not in session:
            flash("Please sign in to continue.", "info")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "account_id" not in session:
            flash("Please sign in with an administrator account.", "info")
            return redirect(url_for("admin_login"))
        account = current_account()
        if not account or not account["is_admin"]:
            abort(403)
        return view(*args, **kwargs)
    return wrapped


def csrf_token():
    if "_csrf" not in session:
        session["_csrf"] = secrets.token_urlsafe(32)
    return session["_csrf"]


app.jinja_env.globals["csrf_token"] = csrf_token


@app.before_request
def keep_session_alive():
    """Signed-in sessions expire after 30 minutes without activity."""
    if "account_id" in session:
        session.permanent = True


@app.before_request
def csrf_protect():
    """Reject any POST that does not carry this session's CSRF token."""
    if request.method != "POST":
        return None
    sent = request.form.get("_csrf") or request.headers.get("X-CSRF-Token", "")
    expected = session.get("_csrf", "")
    if expected and sent and secrets.compare_digest(sent, expected):
        return None
    message = "Your session has expired. Please reload the page and try again."
    if request.path.startswith("/api/") or request.path == "/feedback":
        return jsonify(ok=False, message=message), 400
    response = make_response(render_template("error.html", message=message), 400)
    response.headers["X-Error-Page"] = "1"
    return response


@app.after_request
def security_headers(response):
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    return response


@app.errorhandler(403)
def forbidden(_error):
    return render_template("error.html", message="You do not have permission to open this page."), 403


@app.errorhandler(404)
def not_found(_error):
    return render_template("error.html", message="This page does not exist."), 404


@app.context_processor
def inject_account():
    return {
        "account_name": session.get("account_name"),
        "is_admin": session.get("is_admin", False),
    }


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")
        age, age_error = valid_age_and_gender(
            request.form.get("age"), request.form.get("gender", "")
        )

        error = None
        if len(full_name) < 2:
            error = "Please enter your full name."
        elif age_error:
            error = age_error
        elif not EMAIL_PATTERN.match(email):
            error = "Please enter a valid email address."
        elif len(password) < 8:
            error = "Password must be at least 8 characters."
        elif password != confirm:
            error = "Passwords do not match."
        elif request.form.get("security_question") not in SECURITY_QUESTIONS:
            error = "Choose a security question for password recovery."
        elif len(normalise_answer(request.form.get("security_answer"))) < 2:
            error = "Enter an answer to your security question."

        if not error:
            connection = get_connection()
            try:
                cursor = connection.execute(
                    "INSERT INTO Accounts (full_name, email, password_hash, created_at, age, gender, "
                    "security_question, security_answer_hash) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (full_name, email, hash_secret(password),
                     datetime.now().isoformat(timespec="seconds"),
                     age, request.form.get("gender"),
                     request.form.get("security_question"),
                     hash_secret(normalise_answer(request.form.get("security_answer"))))
                )
                connection.commit()
                session.clear()
                session["account_id"] = cursor.lastrowid
                session["account_name"] = full_name
                return redirect(url_for("home"))
            except sqlite3.IntegrityError:
                error = "An account with this email already exists."
            finally:
                connection.close()

        flash(error, "error")
    return render_template("auth.html", mode="signup", form=request.form,
                           questions=SECURITY_QUESTIONS)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        key = ("login", request.remote_addr, email)
        if too_many_attempts(key):
            wait = LOGIN_WINDOW_SECONDS - (time.time() - _failed_logins[key][0])
            minutes = int(wait // 60) + 1
            flash(f"Too many failed attempts. Please try again in {minutes} minute"
                  f"{'s' if minutes != 1 else ''}, or reset your password.", "error")
            return render_template("auth.html", mode="login", form=request.form), 429

        connection = get_connection()
        account = connection.execute(
            "SELECT * FROM Accounts WHERE email = ?", (email,)
        ).fetchone()
        connection.close()

        if account and check_password_hash(account["password_hash"], password):
            _failed_logins.pop(key, None)
            session.clear()
            session["account_id"] = account["id"]
            session["account_name"] = account["full_name"]
            session["is_admin"] = bool(account["is_admin"])
            if account["is_admin"]:
                return redirect(url_for("admin_dashboard"))
            return redirect(url_for("home"))

        record_failure(key)
        flash("Incorrect email or password.", "error")
    return render_template("auth.html", mode="login", form=request.form)


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    account = current_account()
    if account is None:
        session.clear()
        return redirect(url_for("login"))
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        age, error = valid_age_and_gender(
            request.form.get("age"), request.form.get("gender", "")
        )
        if len(full_name) < 2:
            error = "Please enter your full name."
        if error:
            flash(error, "error")
        else:
            connection = get_connection()
            connection.execute(
                "UPDATE Accounts SET full_name = ?, age = ?, gender = ? WHERE id = ?",
                (full_name, age, request.form.get("gender"), account["id"])
            )
            connection.commit()
            connection.close()
            session["account_name"] = full_name
            flash("Your profile has been updated.", "success")
            return redirect(url_for("profile"))
    return render_template("profile.html", account=account, questions=SECURITY_QUESTIONS)


# =========================================================
# PASSWORD RECOVERY
# =========================================================

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    """Step 1: the student enters their email address."""
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        connection = get_connection()
        account = connection.execute(
            "SELECT id, security_question FROM Accounts WHERE email = ?", (email,)
        ).fetchone()
        connection.close()
        if account and account["security_question"]:
            session["reset_email"] = email
            return redirect(url_for("reset_with_question"))
        flash("We could not verify this account with a security question. "
              "Please ask the administrator for a password reset link.", "error")
    return render_template("recover.html", step="email", form=request.form)


@app.route("/forgot-password/verify", methods=["GET", "POST"])
def reset_with_question():
    """Step 2: answer the security question and choose a new password."""
    email = session.get("reset_email")
    if not email:
        return redirect(url_for("forgot_password"))
    connection = get_connection()
    account = connection.execute(
        "SELECT * FROM Accounts WHERE email = ?", (email,)
    ).fetchone()
    if account is None or not account["security_question"]:
        connection.close()
        session.pop("reset_email", None)
        return redirect(url_for("forgot_password"))

    if request.method == "POST":
        key = ("recover", request.remote_addr, email)
        new = request.form.get("new_password", "")
        confirm = request.form.get("confirm_password", "")
        error = None
        if too_many_attempts(key):
            error = "Too many wrong answers. Please try again in 10 minutes or ask the administrator for a reset link."
        elif not check_password_hash(account["security_answer_hash"],
                                     normalise_answer(request.form.get("answer"))):
            record_failure(key)
            error = "That answer does not match. Answers are not case-sensitive."
        elif len(new) < 8:
            error = "Your new password must be at least 8 characters."
        elif new != confirm:
            error = "The new passwords do not match."
        if error:
            flash(error, "error")
        else:
            connection.execute(
                "UPDATE Accounts SET password_hash = ?, reset_token_hash = NULL, "
                "reset_token_expires = NULL WHERE id = ?",
                (hash_secret(new), account["id"]))
            connection.commit()
            connection.close()
            session.pop("reset_email", None)
            _failed_logins.pop(("login", request.remote_addr, email), None)
            flash("Your password has been reset. Sign in with your new password.", "success")
            return redirect(url_for("login"))
    connection.close()
    return render_template("recover.html", step="question", email=email,
                           question=account["security_question"])


@app.route("/reset/<token>", methods=["GET", "POST"])
def reset_with_link(token):
    """One-time reset link generated by an administrator."""
    connection = get_connection()
    account = connection.execute(
        "SELECT * FROM Accounts WHERE reset_token_hash = ?", (token_digest(token),)
    ).fetchone()
    valid = (account is not None and account["reset_token_expires"]
             and datetime.fromisoformat(account["reset_token_expires"]) > datetime.now())
    if not valid:
        connection.close()
        return render_template("recover.html", step="expired"), 400

    if request.method == "POST":
        new = request.form.get("new_password", "")
        confirm = request.form.get("confirm_password", "")
        if len(new) < 8:
            flash("Your new password must be at least 8 characters.", "error")
        elif new != confirm:
            flash("The new passwords do not match.", "error")
        else:
            connection.execute(
                "UPDATE Accounts SET password_hash = ?, reset_token_hash = NULL, "
                "reset_token_expires = NULL WHERE id = ?",
                (hash_secret(new), account["id"]))
            connection.commit()
            connection.close()
            flash("Your password has been reset. Sign in with your new password.", "success")
            return redirect(url_for("login"))
    connection.close()
    return render_template("recover.html", step="link", email=account["email"])


@app.route("/profile/security", methods=["POST"])
@login_required
def update_security_question():
    account = current_account()
    question = request.form.get("security_question")
    answer = normalise_answer(request.form.get("security_answer"))
    if not check_password_hash(account["password_hash"], request.form.get("current_password", "")):
        flash("Your current password is incorrect.", "error")
    elif question not in SECURITY_QUESTIONS:
        flash("Choose a security question.", "error")
    elif len(answer) < 2:
        flash("Enter an answer to your security question.", "error")
    else:
        connection = get_connection()
        connection.execute(
            "UPDATE Accounts SET security_question = ?, security_answer_hash = ? WHERE id = ?",
            (question, hash_secret(answer), account["id"]))
        connection.commit()
        connection.close()
        flash("Your recovery question has been saved.", "success")
    return redirect(url_for("profile") + "#recovery")


@app.route("/admin/users/<int:account_id>/reset-link", methods=["POST"])
@admin_required
def admin_reset_link(account_id):
    token = secrets.token_urlsafe(32)
    expires = datetime.now() + timedelta(hours=RESET_LINK_HOURS)
    connection = get_connection()
    row = connection.execute("SELECT full_name FROM Accounts WHERE id = ?", (account_id,)).fetchone()
    if row:
        connection.execute(
            "UPDATE Accounts SET reset_token_hash = ?, reset_token_expires = ? WHERE id = ?",
            (token_digest(token), expires.isoformat(timespec="seconds"), account_id))
        connection.commit()
        session["reset_link"] = {
            "name": row["full_name"],
            "url": url_for("reset_with_link", token=token, _external=True),
            "expires": expires.strftime("%I:%M %p"),
        }
    connection.close()
    return redirect(url_for("admin_users"))


@app.route("/profile/password", methods=["POST"])
@login_required
def change_password():
    account = current_account()
    current = request.form.get("current_password", "")
    new = request.form.get("new_password", "")
    confirm = request.form.get("confirm_password", "")

    error = None
    if not check_password_hash(account["password_hash"], current):
        error = "Your current password is incorrect."
    elif len(new) < 8:
        error = "Your new password must be at least 8 characters."
    elif new != confirm:
        error = "The new passwords do not match."
    elif new == current:
        error = "Your new password must be different from the current one."

    if error:
        flash(error, "error")
    else:
        connection = get_connection()
        connection.execute(
            "UPDATE Accounts SET password_hash = ? WHERE id = ?",
            (hash_secret(new), account["id"])
        )
        connection.commit()
        connection.close()
        flash("Your password has been changed.", "success")
    return redirect(url_for("profile") + "#password")


@app.route("/feedback", methods=["POST"])
@login_required
def feedback():
    try:
        assessment_id = int(request.form.get("assessment_id", ""))
        helpful = int(request.form.get("helpful", ""))
    except ValueError:
        return jsonify(ok=False, message="Invalid feedback."), 400
    if helpful not in (0, 1):
        return jsonify(ok=False, message="Invalid feedback."), 400
    comment = request.form.get("comment", "").strip()[:500]

    connection = get_connection()
    owns = connection.execute(
        "SELECT 1 FROM Assessments WHERE id = ? AND account_id = ?",
        (assessment_id, session["account_id"])
    ).fetchone()
    if not owns:
        connection.close()
        return jsonify(ok=False, message="Assessment not found."), 404
    connection.execute(
        "INSERT OR REPLACE INTO Feedback (assessment_id, account_id, helpful, comment, created_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (assessment_id, session["account_id"], helpful, comment,
         datetime.now().isoformat(timespec="seconds"))
    )
    connection.commit()
    connection.close()
    return jsonify(ok=True)


@app.route("/model")
def model_info():
    metrics = ml_model.load_metrics()
    connection = get_connection()
    row = connection.execute(
        "SELECT COUNT(*) AS total, COALESCE(SUM(helpful), 0) AS helpful FROM Feedback"
    ).fetchone()
    assessments = connection.execute("SELECT COUNT(*) FROM Assessments").fetchone()[0]
    connection.close()
    satisfaction = round(row["helpful"] * 100 / row["total"]) if row["total"] else None
    return render_template(
        "model.html", metrics=metrics, feedback_total=row["total"],
        satisfaction=satisfaction, assessments=assessments,
        sklearn_ok=ml_model.SKLEARN_AVAILABLE
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


@app.route("/history")
@login_required
def history():
    connection = get_connection()
    rows = connection.execute(
        "SELECT * FROM Assessments WHERE account_id = ? ORDER BY id DESC",
        (session["account_id"],)
    ).fetchall()
    connection.close()

    items = []
    for row in rows:
        data = json.loads(row["inputs_json"])
        items.append({
            "id": row["id"],
            "has_report": bool(row["results_json"]),
            "date": datetime.fromisoformat(row["created_at"]).strftime("%d %b %Y, %I:%M %p"),
            "education": data.get("education"),
            "field": data.get("field"),
            "interest": data.get("interest"),
            "top_career": row["top_career"] or "No eligible career yet",
        })
    return render_template("history.html", items=items)


@app.after_request
def style_form_errors(response):
    """Show validation errors on a styled page instead of plain text."""
    if response.headers.get("X-Error-Page"):
        return response
    if (
        request.endpoint == "submit"
        and response.status_code in (400, 500)
        and response.mimetype == "text/html"
    ):
        if response.status_code == 500:
            message = "Something went wrong while processing your assessment. Please try again."
        else:
            message = response.get_data(as_text=True).replace("Error: ", "", 1)
        return make_response(
            render_template("error.html", message=message),
            response.status_code
        )
    return response


# =========================================================
# HOME PAGE
# =========================================================

@app.route("/welcome")
def landing():
    """Public landing page."""
    connection = get_connection()
    careers = connection.execute("SELECT COUNT(*) FROM Careers").fetchone()[0]
    grouped = {}
    for row in connection.execute(
            "SELECT id, career_name, interest FROM Careers ORDER BY career_name"):
        grouped.setdefault(row["interest"], []).append(
            {"id": row["id"], "name": row["career_name"]})
    areas = [{"interest": name, "n": len(items), "careers": items}
             for name, items in sorted(grouped.items(), key=lambda x: -len(x[1]))]
    assessments = connection.execute("SELECT COUNT(*) FROM Assessments").fetchone()[0]
    connection.close()
    metrics = ml_model.load_metrics() or {}
    return render_template(
        "landing.html", career_count=careers, areas=areas,
        assessments=assessments,
        model_count=len(metrics.get("results", [])) or 4
    )


def latest_inputs(account_id):
    """The student's answers from their latest assessment (SRS FR3).

    The assessment form is pre-filled with them, so a returning student
    only updates what has changed (education, results, skills, levels,
    interest and quiz answers) instead of typing everything again."""
    connection = get_connection()
    row = connection.execute(
        "SELECT inputs_json FROM Assessments WHERE account_id = ? ORDER BY id DESC LIMIT 1",
        (account_id,)
    ).fetchone()
    connection.close()
    if row is None:
        return None
    try:
        data = json.loads(row["inputs_json"])
    except (TypeError, ValueError):
        return None
    keys = ("education", "field", "interest", "about", "skills", "matric", "inter",
            "cgpa", "levels", "answers", "score_type", "marks")
    return {k: data.get(k) for k in keys}


@app.route("/")
def home():
    if "account_id" not in session:
        return landing()
    account = current_account()
    if account is None:
        session.clear()
        return redirect(url_for("login"))
    if not account["age"] or not account["gender"]:
        flash("Please complete your profile to start the assessment.", "info")
        return redirect(url_for("profile"))
    return render_template(
        "index.html", account=account, fields_by_level=FIELDS_BY_LEVEL,
        previous=latest_inputs(account["id"]),
        all_skills=all_skill_names(),
        questions=personality.QUESTIONS, answer_labels=personality.ANSWER_LABELS, max_skills=MAX_SKILLS
    )


# =========================================================
# ASSESSMENT PROFILE (shared by live preview and final submit)
# =========================================================

EDUCATION_OPTIONS = ["Matric", "O Level", "Intermediate", "A Level", "BS", "MS"]

_SCHOOL_FIELDS = [
    ("Medical", "Biology / Pre-Medical"),
    ("Engineering", "Maths / Pre-Engineering"),
    ("Computer Science", "Computer Science"),
    ("Commerce", "Commerce"),
    ("Arts", "Arts / Humanities"),
]
_COLLEGE_FIELDS = [
    ("Medical", "Pre-Medical (FSc)"),
    ("Engineering", "Pre-Engineering (FSc)"),
    ("Computer Science", "ICS (Computer Science)"),
    ("Commerce", "I.Com (Commerce)"),
    ("Arts", "FA / Humanities"),
]
_UNIVERSITY_FIELDS = [
    ("Computer Science", "Computer Science / IT / Software"),
    ("Engineering", "Engineering"),
    ("Medical", "Medical & Health Sciences"),
    ("Business", "Business / Management"),
    ("Commerce", "Commerce / Accounting / Economics"),
    ("Arts", "Arts / Media / Design"),
    ("Education", "Education"),
    ("Law", "Law"),
    ("Sciences", "Natural Sciences (Maths, Physics, Chemistry, Biology, Statistics)"),
]

# The field of study must belong to the selected education level.
FIELDS_BY_LEVEL = {
    "Matric": _SCHOOL_FIELDS,
    "O Level": _SCHOOL_FIELDS,
    "Intermediate": _COLLEGE_FIELDS,
    "A Level": _COLLEGE_FIELDS,
    "BS": _UNIVERSITY_FIELDS,
    "MS": _UNIVERSITY_FIELDS,
}


class Incomplete(ValueError):
    """The form is not filled in yet (not an error while typing)."""


def _percentage(form, key, label):
    raw = form.get(key, "").strip()
    if not raw:
        raise Incomplete(f"{label} is required.")
    try:
        value = float(raw)
    except ValueError:
        raise ValueError(f"{label} must be a number.")
    if not 0 <= value <= 100:
        raise ValueError(f"{label} must be between 0 and 100.")
    return value


def build_profile(form, account, require_quiz=True):
    """Validate the form and combine all academic scores into one."""
    education = form.get("education", "").strip()
    if education not in FIELDS_BY_LEVEL:
        raise Incomplete("Select your education level.")

    field = form.get("field", "").strip()
    if not field:
        raise Incomplete("Select your field of study.")
    if field not in {value for value, _ in FIELDS_BY_LEVEL[education]}:
        raise ValueError(
            "This field of study does not belong to your education level. "
            "Please select it again."
        )

    interest = form.get("interest", "").strip()
    if not interest:
        raise Incomplete("Select your main interest.")

    skills = list(dict.fromkeys(
        s.strip() for s in form.getlist("skills") if s.strip()
    ))
    # Self-assessed proficiency 1-5 for each selected skill (SRS FR6)
    levels = {}
    for skill in skills:
        try:
            level = int(form.get("level::" + skill, 3))
        except (TypeError, ValueError):
            level = 3
        levels[skill] = min(max(level, 1), 5)
    if not skills:
        raise Incomplete("Select at least one skill.")
    if len(skills) > MAX_SKILLS:
        raise ValueError(
            f"Please select at most {MAX_SKILLS} skills "
            f"(you selected {len(skills)}). Choose the ones you are "
            "genuinely good at."
        )

    age = account["age"]
    age_range = AGE_RANGE_BY_EDUCATION.get(education.lower())
    if age_range and not age_range[0] <= age <= age_range[1]:
        raise ValueError(
            f"The age in your profile ({age}) does not look right for "
            f"{education} (expected {age_range[0]}-{age_range[1]}). "
            "Please update your profile or your education level."
        )

    about = form.get("interest_description", "").strip()[:1200]

    matric = _percentage(form, "matric_percentage", "Matric / O Level percentage")
    inter = None
    degree_pct = None
    cgpa = None
    parts = [f"Matric {matric:g}%"]

    if education in ("Intermediate", "A Level", "BS", "MS"):
        inter = _percentage(form, "inter_percentage", "Intermediate / A Level percentage")
        parts.append(f"Inter {inter:g}%")

    if education in ("BS", "MS"):
        score_type = form.get("score_type", "").strip().lower()
        raw = form.get("marks", "").strip()
        if not raw:
            raise Incomplete("Enter your current degree score.")
        try:
            value = float(raw)
        except ValueError:
            raise ValueError("Degree score must be a number.")
        if score_type == "cgpa":
            if not 0 <= value <= 4:
                raise ValueError("CGPA must be between 0 and 4.")
            cgpa = value
            degree_pct = value / 4 * 100
            parts.append(f"CGPA {value:g}")
        elif score_type == "percentage":
            if not 0 <= value <= 100:
                raise ValueError("Degree percentage must be between 0 and 100.")
            degree_pct = value
            parts.append(f"Degree {value:g}%")
        else:
            raise ValueError("Invalid degree score type.")

    # Weighted overall academic score: the current level counts most.
    if degree_pct is not None:
        overall = 0.5 * degree_pct + 0.3 * inter + 0.2 * matric
    elif inter is not None:
        overall = 0.6 * inter + 0.4 * matric
    else:
        overall = matric

    return {
        "education": education, "field": field, "interest": interest,
        "skills": skills, "age": age, "gender": account["gender"],
        "name": account["full_name"], "about": about, "matric": matric, "inter": inter,
        "cgpa": cgpa, "overall": round(overall, 1),
        "levels": levels,
        "score_type": form.get("score_type", "").strip().lower() if degree_pct is not None else None,
        "marks": form.get("marks", "").strip() if degree_pct is not None else None,
        "personality": personality.score_answers(form, required=require_quiz),
        "answers": personality.answers_from(form),
        "display": " · ".join(parts) + f" → {overall:.1f}% overall",
    }


def suitability_label(score):
    if score >= 85:
        return "Excellent Fit"
    if score >= 75:
        return "Strong Fit"
    if score >= 60:
        return "Good Fit"
    if score >= 45:
        return "Moderate Fit"
    return "Low Fit"


def explore_links(career_name):
    """Live job searches (Pakistan) and course searches for a career."""
    from urllib.parse import quote, quote_plus
    slug = re.sub(r"[^a-z0-9]+", "-", career_name.lower()).strip("-")
    return {
        "jobs": [
            ("Rozee.pk", f"https://www.rozee.pk/EN/search/{slug}-jobs-in-pakistan"),
            ("LinkedIn", "https://www.linkedin.com/jobs/search/?keywords="
                         f"{quote(career_name)}&location=Pakistan"),
            ("Indeed Pakistan", f"https://pk.indeed.com/q-{slug}-jobs.html"),
        ],
        "learn": [
            ("Coursera", f"https://www.coursera.org/search?query={quote(career_name)}"),
            ("YouTube", "https://www.youtube.com/results?search_query="
                        f"{quote_plus(career_name + ' career roadmap')}"),
        ],
    }


def skill_gap(required_text, user_skills):
    """Split a career's required skills into ones the student has / lacks."""
    have_set = {s.strip().lower() for s in user_skills}
    required = [s.strip() for s in str(required_text or "").split(",") if s.strip()]
    have = [s for s in required if s.lower() in have_set]
    missing = [s for s in required if s.lower() not in have_set]
    return have, missing


def skill_profile(career, levels):
    """Skill gap with proficiency levels (SRS FR6, FR10).

    A required skill the student has counts level/5 (Expert = 1.0,
    Beginner = 0.2). Returns the lists for the report and a 0-100 match."""
    have_lookup = {s.strip().lower(): (s, lvl) for s, lvl in levels.items()}
    required = [s.strip() for s in str(career.get("required_skills") or "").split(",") if s.strip()]
    have, developing, missing, credit = [], [], [], 0.0
    for skill in required:
        found = have_lookup.get(skill.lower())
        if not found:
            missing.append(skill)
            continue
        level = found[1]
        credit += level / 5
        entry = {"name": skill, "level": level, "label": LEVEL_LABELS[level]}
        (have if level >= 3 else developing).append(entry)
    match = round(credit / len(required) * 100) if required else 0
    return have, developing, missing, match


LEVEL_LABELS = {1: "Beginner", 2: "Basic", 3: "Intermediate", 4: "Advanced", 5: "Expert"}


def run_engine(profile):
    """Hybrid AI recommendation.

    For every career:
      knowledge score  = rule-based scoring (field, interest, education, marks,
                         skills weighted by proficiency) + NLP description match
      ML score         = trained classifier probability relative to its top career
      personality score = cosine similarity (scikit-learn) between the student's
                         Holland RIASEC profile and the career's profile
    Final score = 70% knowledge + 15% ML + 15% personality.
    Without quiz answers (live preview before the quiz) the weights are
    80% knowledge + 20% ML. Careers are then split by education eligibility.
    """
    found = recommend_career(
        profile["education"], profile["field"], profile["overall"],
        profile["interest"], "percentage", profile["skills"], limit=500,
        description_text=profile["about"]
    )

    probabilities = ml_model.predict_probabilities(
        profile["education"], profile["field"], profile["interest"],
        profile["overall"], profile["skills"]
    )
    top_probability = max(probabilities.values(), default=0) or 1
    model_name = ml_model.model_name()
    personality_scores = profile.get("personality")
    fits = personality.personality_matches(personality_scores, found) if personality_scores else {}
    student_types = personality.top_types(personality_scores, 2) if personality_scores else []
    levels = profile.get("levels") or {s: 3 for s in profile["skills"]}

    for career in found:
        have, developing, missing, skill_match = skill_profile(career, levels)
        # Replace the plain skill points with proficiency-weighted points
        skill_points = career.get("score_breakdown", {}).get("skills", 0)
        knowledge = career["score"] - skill_points + skill_match / 100 * 15
        relative = (probabilities.get(career["career_name"], 0.0) / top_probability
                    if probabilities else None)
        fit = fits.get(career["career_name"])

        if fit is not None and relative is not None:
            score = 0.70 * knowledge + 15 * relative + 0.15 * fit
        elif relative is not None:
            score = 0.80 * knowledge + 20 * relative
        elif fit is not None:
            score = 0.85 * knowledge + 0.15 * fit
        else:
            score = knowledge
        career["score"] = round(min(score, 100), 2)
        career["suitability_label"] = suitability_label(career["score"])
        career["personality_match"] = fit
        career["holland_code"] = personality.code_for(career)
        career["holland_names"] = [personality.TYPE_INFO[t][0] for t in career["holland_code"]]

        reasons = list(career.get("reasons") or [])
        if relative is not None and relative >= 0.5:
            reasons.append(f"Our trained machine learning model ({model_name}) also "
                           "predicts this career for students with profiles like yours.")
        if fit is not None and fit >= 75 and student_types:
            reasons.append("Your personality type ("
                           + " and ".join(t["name"] for t in student_types)
                           + f") suits this career ({fit:.0f}% personality match).")
        career["skills_have"] = [s["name"] for s in have]
        career["skills_levels"] = have
        career["skills_developing"] = developing
        career["skills_missing"] = missing
        career["skill_match"] = skill_match
        career["links"] = explore_links(career["career_name"])
        career["roadmap"] = build_roadmap(
            career, profile["education"], profile["field"],
            missing + [s["name"] for s in developing]
        )
        career["reasons"] = sorted(
            dict.fromkeys(reasons),
            key=lambda r: (
                0 if "machine learning model" in r else
                1 if "personality" in r else
                2 if "description" in r else
                3 if "skill" in r else
                4 if "interest" in r or "field" in r else 5
            )
        )

    found.sort(key=lambda c: -c["score"])
    eligible = [c for c in found if c.get("education_eligible", True)]
    future = [c for c in found if not c.get("education_eligible", True)]
    return eligible[:5], future[:5]


@app.route("/api/preview", methods=["POST"])
@login_required
def api_preview():
    """Live recommendations while the user fills in the form."""
    account = current_account()
    if not account or not account["age"] or not account["gender"]:
        return jsonify(ok=False, message="Please complete your profile first.")
    try:
        profile = build_profile(request.form, account, require_quiz=False)
    except Incomplete:
        return jsonify(ok=False, message="Complete the form to see live matches.")
    except ValueError as error:
        return jsonify(ok=False, warn=True, message=str(error))

    eligible, future = run_engine(profile)
    detected = nlp_extract(profile["about"])
    suggestion = None
    if detected["interests"] and profile["interest"] not in detected["interests"]:
        suggestion = (
            f"Your description sounds like {detected['interests'][0]}, "
            f"but you selected {profile['interest']}."
        )
    return jsonify(
        ok=True,
        overall=profile["display"],
        personality=personality.top_types(profile["personality"], 3) if profile["personality"] else None,
        nlp={"interests": detected["interests"], "skills": detected["skills"],
             "suggestion": suggestion},
        careers=[
            {"name": c["career_name"], "score": c["score"],
             "label": c["suitability_label"]}
            for c in eligible[:3]
        ],
        pathway=[
            {"name": c["career_name"], "requires": c["required_education"]}
            for c in future[:3]
        ] if not eligible else []
    )


# =========================================================
# SUBMIT CAREER ASSESSMENT
# =========================================================

def attach_job_market(careers):
    """Optional live openings (Adzuna API). Fails quietly without API keys."""
    if not careers:
        return
    with ThreadPoolExecutor(max_workers=min(5, len(careers))) as executor:
        futures = {
            executor.submit(get_job_market_data, career["career_name"]): career
            for career in careers
        }
        for future in as_completed(futures):
            try:
                futures[future]["job_market"] = future.result()
            except Exception:
                futures[future]["job_market"] = {"available": False, "jobs": []}


@app.route("/submit", methods=["POST"])
@login_required
def submit():
    account = current_account()
    if not account or not account["age"] or not account["gender"]:
        return redirect(url_for("profile"))

    try:
        profile = build_profile(request.form, account)
    except ValueError as error:
        return f"Error: {error}", 400

    try:
        recommended, future = run_engine(profile)
        attach_job_market(recommended)
    except Exception:
        return "Error while processing your assessment.", 500

    created = datetime.now()
    # Snapshot of the complete report, so it can be reopened later exactly
    # as it was generated, even if the career database changes.
    snapshot = {
        "kind": "report" if recommended else "pathway",
        "name": profile["name"], "age": profile["age"], "gender": profile["gender"],
        "education": profile["education"], "field": profile["field"],
        "interest": profile["interest"], "skills": profile["skills"],
        "display": profile["display"],
        "levels": profile["levels"],
        "personality": personality.top_types(profile["personality"], 6) if profile["personality"] else None,
        "generated_on": created.strftime("%d %B %Y, %I:%M %p"),
        "careers": recommended, "future": future,
    }

    connection = get_connection()
    try:
        connection.execute(
            "INSERT INTO Users (name, age, gender, education_level, "
            "field_of_study, percentage, cgpa) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (profile["name"], profile["age"], profile["gender"],
             profile["education"], profile["field"], profile["overall"],
             profile["cgpa"])
        )
        cursor = connection.execute(
            "INSERT INTO Assessments (account_id, created_at, inputs_json, "
            "top_career, results_json) VALUES (?, ?, ?, ?, ?)",
            (account["id"], created.isoformat(timespec="seconds"),
             json.dumps({k: profile[k] for k in (
                 "education", "field", "interest", "about", "skills", "matric",
                 "inter", "cgpa", "overall", "levels", "personality", "answers",
                 "score_type", "marks")}),
             recommended[0]["career_name"] if recommended else None,
             json.dumps(snapshot, default=str))
        )
        assessment_id = cursor.lastrowid
        connection.commit()
    except Exception:
        connection.rollback()
        return "Error while saving your assessment.", 500
    finally:
        connection.close()

    return redirect(url_for("report", assessment_id=assessment_id))


@app.route("/report/<int:assessment_id>")
@login_required
def report(assessment_id):
    """Open a saved report. Students see their own; admins can see any."""
    connection = get_connection()
    row = connection.execute(
        "SELECT * FROM Assessments WHERE id = ?", (assessment_id,)
    ).fetchone()
    connection.close()
    if row is None:
        abort(404)
    if row["account_id"] != session["account_id"] and not session.get("is_admin"):
        abort(404)
    if not row["results_json"]:
        flash("This assessment was taken before reports were saved. "
              "Please take a new assessment to see a full report.", "info")
        return redirect(url_for("history"))

    data = json.loads(row["results_json"])
    for career in data.get("careers", []) + data.get("future", []):
        if "roadmap" not in career:
            career["roadmap"] = build_roadmap(
                career, data["education"], data["field"], career.get("skills_missing"))
    if data["kind"] == "pathway":
        return render_template(
            "pathway.html", education=data["education"], field=data["field"],
            interest=data["interest"], future=data["future"],
            generated_on=data.get("generated_on"),
            personality_profile=data.get("personality")
        )
    return render_template(
        "result.html",
        careers=data["careers"], name=data["name"], age=data["age"],
        gender=data["gender"], education=data["education"],
        field=data["field"], score_type="percentage",
        academic_score_display=data["display"], interest=data["interest"],
        skills=data["skills"], assessment_id=assessment_id,
        generated_on=data["generated_on"],
        own_report=row["account_id"] == session["account_id"],
        personality_profile=data.get("personality"),
    )


# =========================================================
# CAREER DETAILS (SRS FR9, UC-07)
# =========================================================

@app.route("/career/<int:career_id>")
def career_details(career_id):
    connection = get_connection()
    row = connection.execute("SELECT * FROM Careers WHERE id = ?", (career_id,)).fetchone()
    connection.close()
    if row is None:
        abort(404)
    career = dict(row)
    code = personality.code_for(career)
    roadmap = build_roadmap(career, "Matric", "", [])
    requirements = required_subjects(career)
    return render_template(
        "career.html", career=career, roadmap=roadmap, requirements=requirements,
        holland=[{"code": t, "name": personality.TYPE_INFO[t][0],
                  "about": personality.TYPE_INFO[t][1]} for t in code],
        skills=[s.strip() for s in str(career["required_skills"] or "").split(",") if s.strip()],
        links=explore_links(career["career_name"]),
    )


# =========================================================
# ADMIN PANEL
# =========================================================

ADMIN_EDUCATION = ["Matric", "Intermediate", "BS", "MS"]
ADMIN_FIELDS = ["Computer Science", "Engineering", "Medical", "Business",
                "Commerce", "Arts", "Education", "Law", "Sciences",
                "Public Administration", "Any"]
CAREER_TEXT_FIELDS = ["description", "required_skills", "future_scope",
                      "average_salary", "learning_resources"]


def _interest_names(connection):
    rows = connection.execute("SELECT interest_name FROM Interests ORDER BY id").fetchall()
    return [r["interest_name"] for r in rows]


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    """Separate sign-in page for administrators only."""
    if session.get("is_admin"):
        return redirect(url_for("admin_dashboard"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        key = ("login", request.remote_addr, email)
        if too_many_attempts(key):
            flash("Too many failed attempts. Please try again in 10 minutes.", "error")
            return render_template("auth.html", mode="admin", form=request.form), 429
        connection = get_connection()
        account = connection.execute(
            "SELECT * FROM Accounts WHERE email = ?", (email,)
        ).fetchone()
        connection.close()
        if account and check_password_hash(account["password_hash"], password):
            if not account["is_admin"]:
                flash("This account does not have administrator access. "
                      "Students should use the student sign-in.", "error")
                return render_template("auth.html", mode="admin", form=request.form), 403
            _failed_logins.pop(key, None)
            session.clear()
            session["account_id"] = account["id"]
            session["account_name"] = account["full_name"]
            session["is_admin"] = True
            return redirect(url_for("admin_dashboard"))
        record_failure(key)
        flash("Incorrect email or password.", "error")
    return render_template("auth.html", mode="admin", form=request.form)


@app.route("/admin")
@admin_required
def admin_dashboard():
    connection = get_connection()
    one = lambda sql, *args: connection.execute(sql, args).fetchone()[0]
    week_ago = (datetime.now().timestamp() - 7 * 86400)
    stats = {
        "students": one("SELECT COUNT(*) FROM Accounts WHERE is_admin = 0"),
        "assessments": one("SELECT COUNT(*) FROM Assessments"),
        "this_week": one(
            "SELECT COUNT(*) FROM Assessments WHERE created_at >= ?",
            datetime.fromtimestamp(week_ago).isoformat(timespec="seconds")),
        "careers": one("SELECT COUNT(*) FROM Careers"),
        "feedback": one("SELECT COUNT(*) FROM Feedback"),
        "helpful": one("SELECT COALESCE(SUM(helpful), 0) FROM Feedback"),
    }
    stats["satisfaction"] = (
        round(stats["helpful"] * 100 / stats["feedback"]) if stats["feedback"] else None
    )
    top_careers = connection.execute(
        "SELECT top_career AS name, COUNT(*) AS n FROM Assessments "
        "WHERE top_career IS NOT NULL GROUP BY top_career ORDER BY n DESC LIMIT 6"
    ).fetchall()
    levels = {}
    for row in connection.execute("SELECT inputs_json FROM Assessments"):
        level = json.loads(row["inputs_json"]).get("education", "Unknown")
        levels[level] = levels.get(level, 0) + 1
    recent = connection.execute(
        "SELECT a.id, a.created_at, a.top_career, a.inputs_json, a.results_json, "
        "c.full_name FROM Assessments a JOIN Accounts c ON c.id = a.account_id "
        "ORDER BY a.id DESC LIMIT 8"
    ).fetchall()
    connection.close()

    recent_rows = [{
        "id": r["id"], "name": r["full_name"],
        "date": datetime.fromisoformat(r["created_at"]).strftime("%d %b %Y, %I:%M %p"),
        "education": json.loads(r["inputs_json"]).get("education"),
        "top_career": r["top_career"] or "Next-step pathway",
        "has_report": bool(r["results_json"]),
    } for r in recent]
    max_top = max((r["n"] for r in top_careers), default=1)
    max_level = max(levels.values(), default=1)
    return render_template(
        "admin/dashboard.html", stats=stats, top_careers=top_careers,
        max_top=max_top, levels=sorted(levels.items(), key=lambda x: -x[1]),
        max_level=max_level, recent=recent_rows,
        metrics=ml_model.load_metrics(), active="dashboard"
    )


@app.route("/admin/careers")
@admin_required
def admin_careers():
    query = request.args.get("q", "").strip()
    connection = get_connection()
    if query:
        rows = connection.execute(
            "SELECT * FROM Careers WHERE career_name LIKE ? OR interest LIKE ? "
            "OR field_required LIKE ? ORDER BY career_name",
            (f"%{query}%",) * 3
        ).fetchall()
    else:
        rows = connection.execute("SELECT * FROM Careers ORDER BY career_name").fetchall()
    connection.close()
    return render_template("admin/careers.html", careers=rows, q=query, active="careers")


def _career_form_data(form, interests):
    data = {k: form.get(k, "").strip() for k in
            ["career_name", "education_required", "field_required", "interest"]
            + CAREER_TEXT_FIELDS}
    data["minimum_percentage"] = form.get("minimum_percentage", "").strip()
    data["holland_code"] = personality.clean_code("".join(form.getlist("holland_code")))
    data["related"] = [i for i in form.getlist("related") if i in interests]

    if len(data["career_name"]) < 2:
        return data, "Career name is required."
    if not data["education_required"]:
        return data, "Select the required education."
    if not data["field_required"]:
        return data, "Select the field of study."
    if data["interest"] not in interests:
        return data, "Select the main interest."
    try:
        minimum = float(data["minimum_percentage"])
    except ValueError:
        return data, "Minimum percentage must be a number."
    if not 0 <= minimum <= 100:
        return data, "Minimum percentage must be between 0 and 100."
    data["minimum_percentage"] = minimum
    if not data["required_skills"]:
        return data, "Enter at least one required skill (comma separated)."
    if not data["description"]:
        return data, "Enter a short description."
    if not data["holland_code"]:
        return data, "Choose at least one personality type (Holland code)."
    return data, None


def _save_career_interests(connection, career_id, data):
    names = list(dict.fromkeys([data["interest"]] + data["related"]))
    connection.execute("DELETE FROM CareerInterests WHERE career_id = ?", (career_id,))
    for name in names:
        row = connection.execute(
            "SELECT id FROM Interests WHERE interest_name = ?", (name,)).fetchone()
        if row:
            connection.execute(
                "INSERT INTO CareerInterests (career_id, interest_id) VALUES (?, ?)",
                (career_id, row["id"]))


@app.route("/admin/careers/new", methods=["GET", "POST"])
@app.route("/admin/careers/<int:career_id>/edit", methods=["GET", "POST"])
@admin_required
def admin_career_form(career_id=None):
    connection = get_connection()
    interests = _interest_names(connection)
    career = None
    if career_id is not None:
        career = connection.execute("SELECT * FROM Careers WHERE id = ?", (career_id,)).fetchone()
        if career is None:
            connection.close()
            abort(404)

    if request.method == "POST":
        data, error = _career_form_data(request.form, interests)
        if not error:
            clash = connection.execute(
                "SELECT id FROM Careers WHERE LOWER(career_name) = LOWER(?) AND id != ?",
                (data["career_name"], career_id or 0)).fetchone()
            if clash:
                error = "Another career already has this name."
        if error:
            flash(error, "error")
            values = data
        else:
            columns = ["career_name", "education_required", "field_required",
                       "minimum_percentage", "interest", "holland_code"] + CAREER_TEXT_FIELDS
            params = [data[c] for c in columns]
            if career_id is None:
                cursor = connection.execute(
                    f"INSERT INTO Careers ({', '.join(columns)}) "
                    f"VALUES ({', '.join('?' * len(columns))})", params)
                career_id = cursor.lastrowid
                message = f"Career “{data['career_name']}” added."
            else:
                connection.execute(
                    f"UPDATE Careers SET {', '.join(c + ' = ?' for c in columns)} WHERE id = ?",
                    params + [career_id])
                message = f"Career “{data['career_name']}” updated."
            _save_career_interests(connection, career_id, data)
            connection.commit()
            connection.close()
            ml_model.reset_model()
            flash(message + " Retrain the AI model from the dashboard to refresh its evaluation.", "success")
            return redirect(url_for("admin_careers"))
    else:
        if career:
            values = dict(career)
            values["related"] = [r["interest_name"] for r in connection.execute(
                "SELECT i.interest_name FROM CareerInterests ci JOIN Interests i "
                "ON i.id = ci.interest_id WHERE ci.career_id = ?", (career_id,))]
        else:
            values = {"related": [], "minimum_percentage": 50}
    connection.close()

    education_options = list(ADMIN_EDUCATION)
    if values.get("education_required") and values["education_required"] not in education_options:
        education_options.append(values["education_required"])
    field_options = list(ADMIN_FIELDS)
    if values.get("field_required") and values["field_required"] not in field_options:
        field_options.append(values["field_required"])
    return render_template(
        "admin/career_form.html", values=values, career_id=career_id,
        education_options=education_options, field_options=field_options,
        interests=interests, active="careers", holland_types=personality.TYPE_INFO
    )


@app.route("/admin/careers/<int:career_id>/delete", methods=["POST"])
@admin_required
def admin_career_delete(career_id):
    connection = get_connection()
    row = connection.execute("SELECT career_name FROM Careers WHERE id = ?", (career_id,)).fetchone()
    if row:
        connection.execute("DELETE FROM CareerInterests WHERE career_id = ?", (career_id,))
        connection.execute("DELETE FROM Careers WHERE id = ?", (career_id,))
        connection.commit()
        ml_model.reset_model()
        flash(f"Career “{row['career_name']}” deleted.", "success")
    connection.close()
    return redirect(url_for("admin_careers"))


@app.route("/admin/users")
@admin_required
def admin_users():
    connection = get_connection()
    rows = connection.execute(
        "SELECT c.*, COUNT(a.id) AS assessments, MAX(a.created_at) AS last_activity "
        "FROM Accounts c LEFT JOIN Assessments a ON a.account_id = c.id "
        "GROUP BY c.id ORDER BY c.id DESC"
    ).fetchall()
    connection.close()
    users = [{
        **dict(r),
        "joined": datetime.fromisoformat(r["created_at"]).strftime("%d %b %Y"),
        "last": (datetime.fromisoformat(r["last_activity"]).strftime("%d %b %Y")
                 if r["last_activity"] else "—"),
    } for r in rows]
    return render_template("admin/users.html", users=users, active="users",
                           reset_link=session.pop("reset_link", None))


@app.route("/admin/users/<int:account_id>/role", methods=["POST"])
@admin_required
def admin_toggle_role(account_id):
    if account_id == session["account_id"]:
        flash("You cannot change your own admin role.", "error")
        return redirect(url_for("admin_users"))
    connection = get_connection()
    row = connection.execute("SELECT full_name, is_admin FROM Accounts WHERE id = ?",
                             (account_id,)).fetchone()
    if row:
        connection.execute("UPDATE Accounts SET is_admin = ? WHERE id = ?",
                           (0 if row["is_admin"] else 1, account_id))
        connection.commit()
        flash(f"{row['full_name']} is {'no longer an admin' if row['is_admin'] else 'now an admin'}.",
              "success")
    connection.close()
    return redirect(url_for("admin_users"))


@app.route("/admin/feedback")
@admin_required
def admin_feedback():
    connection = get_connection()
    rows = connection.execute(
        "SELECT f.*, c.full_name, a.top_career FROM Feedback f "
        "JOIN Accounts c ON c.id = f.account_id "
        "JOIN Assessments a ON a.id = f.assessment_id ORDER BY f.id DESC"
    ).fetchall()
    connection.close()
    items = [{
        **dict(r),
        "date": datetime.fromisoformat(r["created_at"]).strftime("%d %b %Y, %I:%M %p"),
    } for r in rows]
    helpful = sum(1 for i in items if i["helpful"])
    return render_template("admin/feedback.html", items=items, helpful=helpful, active="feedback")


@app.route("/admin/retrain", methods=["POST"])
@admin_required
def admin_retrain():
    if not ml_model.SKLEARN_AVAILABLE:
        flash("scikit-learn is not installed, so the model cannot be trained.", "error")
        return redirect(url_for("admin_dashboard"))
    try:
        metrics = ml_model.train_and_save_metrics()
        ml_model.reset_model()
        best = metrics["results"][0]
        flash(f"AI model retrained on {metrics['dataset_size']:,} profiles for "
              f"{metrics['classes']} careers. Best model: {best['model']} "
              f"(accuracy {best['accuracy']}%, F1 {best['f1']:.3f}).", "success")
    except Exception as error:
        flash(f"Retraining failed: {error}", "error")
    return redirect(url_for("admin_dashboard"))


# =========================================================
# RUN APPLICATION
# =========================================================

init_db()

# Train the ML model in the background so the first request is fast.
threading.Thread(
    target=ml_model.predict_probabilities,
    args=("BS", "Computer Science", "Programming", 70, []),
    daemon=True
).start()

if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
