"""Automated tests for the AI Career Counselling System.

Run from the project folder:
    python -m unittest discover tests -v

The tests use a temporary copy of the database, so your real accounts and
reports are never changed.
"""
import os
import re
import shutil
import sys
import tempfile
import unittest

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT)

_TEMP_DIR = tempfile.mkdtemp()
_TEMP_DB = os.path.join(_TEMP_DIR, "test.db")
shutil.copy(os.path.join(PROJECT, "Database", "career_counseling.db"), _TEMP_DB)
os.environ["CAREER_DB_PATH"] = _TEMP_DB
os.environ["SECRET_KEY"] = "test-secret-key"

import app as application  # noqa: E402  (must come after the environment is set)
from Database.nlp_engine import extract  # noqa: E402
from Database.roadmap import build_roadmap  # noqa: E402

QUESTION = "In which city were you born?"
BS_PROFILE = dict(education="BS", field="Computer Science", interest="Programming",
                  matric_percentage="82", inter_percentage="78", score_type="cgpa",
                  marks="3.4", skills=["Python", "SQL", "Machine Learning"])
MATRIC_PROFILE = dict(education="Matric", field="Medical", interest="Biology",
                      matric_percentage="90", skills=["Biology", "Patient Care"])
# A student who mostly likes helping people and investigating (Holland "SI")
QUIZ = {f"q{i}": "3" for i in range(1, 16)}
QUIZ.update(q4="4", q5="4", q9="5", q10="5", q11="5", q1="2", q13="2")
BS_PROFILE.update(QUIZ)
MATRIC_PROFILE.update(QUIZ)
_counter = [0]


def csrf(client, page="/login"):
    html = client.get(page).get_data(as_text=True)
    return re.search(r'name="_csrf" value="([^"]+)"', html).group(1)


def post(client, url, data, page="/login"):
    data = dict(data, _csrf=csrf(client, page))
    return client.post(url, data=data)


def new_student(age="22", password="secret123"):
    """Create and sign in a fresh student; returns (client, email)."""
    _counter[0] += 1
    email = f"student{_counter[0]}@test.com"
    client = application.app.test_client()
    post(client, "/signup", dict(full_name="Test Student", email=email, password=password,
                                 confirm=password, age=age, gender="Male",
                                 security_question=QUESTION, security_answer="Lahore"), "/signup")
    return client, email


def make_admin(email):
    connection = application.get_connection()
    connection.execute("UPDATE Accounts SET is_admin = 1 WHERE email = ?", (email,))
    connection.commit()
    connection.close()


class PublicPagesTest(unittest.TestCase):
    def test_public_pages_load(self):
        client = application.app.test_client()
        for url in ("/", "/login", "/signup", "/forgot-password", "/admin/login", "/model"):
            self.assertEqual(client.get(url).status_code, 200, url)

    def test_protected_pages_need_sign_in(self):
        client = application.app.test_client()
        for url in ("/history", "/profile"):
            self.assertEqual(client.get(url).status_code, 302, url)

    def test_unknown_page_returns_404(self):
        self.assertEqual(application.app.test_client().get("/no-such-page").status_code, 404)


class SecurityTest(unittest.TestCase):
    def test_post_without_csrf_token_is_rejected(self):
        client = application.app.test_client()
        response = client.post("/login", data=dict(email="a@b.com", password="x"))
        self.assertEqual(response.status_code, 400)

    def test_password_is_stored_as_hash(self):
        _, email = new_student()
        connection = application.get_connection()
        row = connection.execute("SELECT password_hash FROM Accounts WHERE email = ?", (email,)).fetchone()
        connection.close()
        self.assertNotIn("secret123", row["password_hash"])

    def test_repeated_wrong_passwords_are_blocked(self):
        _, email = new_student()
        client = application.app.test_client()
        codes = [post(client, "/login", dict(email=email, password="wrong")).status_code
                 for _ in range(6)]
        self.assertEqual(codes[-1], 429)

    def test_security_headers(self):
        response = application.app.test_client().get("/")
        self.assertEqual(response.headers.get("X-Frame-Options"), "DENY")
        self.assertEqual(response.headers.get("X-Content-Type-Options"), "nosniff")


class AccountTest(unittest.TestCase):
    def test_signup_requires_recovery_question(self):
        client = application.app.test_client()
        response = post(client, "/signup", dict(full_name="A B", email="noq@test.com",
                                                 password="secret123", confirm="secret123",
                                                 age="20", gender="Male"), "/signup")
        self.assertIn(b"security question", response.data)

    def test_change_password(self):
        client, email = new_student()
        post(client, "/profile/password", dict(current_password="secret123",
                                                new_password="changed123",
                                                confirm_password="changed123"), "/profile")
        other = application.app.test_client()
        self.assertEqual(post(other, "/login", dict(email=email, password="changed123")).status_code, 302)

    def test_forgot_password_with_security_question(self):
        _, email = new_student()
        client = application.app.test_client()
        post(client, "/forgot-password", dict(email=email), "/forgot-password")
        wrong = post(client, "/forgot-password/verify",
                     dict(answer="Karachi", new_password="reset1234", confirm_password="reset1234"),
                     "/forgot-password/verify")
        self.assertIn(b"does not match", wrong.data)
        right = post(client, "/forgot-password/verify",
                     dict(answer="  LAHORE ", new_password="reset1234", confirm_password="reset1234"),
                     "/forgot-password/verify")
        self.assertEqual(right.status_code, 302)
        fresh = application.app.test_client()
        self.assertEqual(post(fresh, "/login", dict(email=email, password="reset1234")).status_code, 302)


class AssessmentTest(unittest.TestCase):
    def test_supervisor_case_matric_age_70_is_rejected(self):
        client, _ = new_student(age="70")
        response = post(client, "/submit", dict(MATRIC_PROFILE, field="Computer Science",
                                                 interest="Programming"), "/")
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"does not look right", response.data)

    def test_more_than_eight_skills_is_rejected(self):
        client, _ = new_student()
        skills = ["Python", "SQL", "Git", "Debugging", "Programming", "HTML", "CSS", "Linux", "Excel"]
        response = post(client, "/submit", dict(BS_PROFILE, skills=skills), "/")
        self.assertIn(b"at most 8", response.data)

    def test_field_must_match_education_level(self):
        client, _ = new_student(age="15")
        response = post(client, "/submit", dict(MATRIC_PROFILE, field="Law"), "/")
        self.assertIn(b"does not belong", response.data)

    def test_bs_student_gets_saved_report_with_roadmap(self):
        client, _ = new_student()
        response = post(client, "/submit", BS_PROFILE, "/")
        self.assertEqual(response.status_code, 302)
        report = client.get(response.headers["Location"]).get_data(as_text=True)
        self.assertIn("Your roadmap to", report)
        self.assertIn("rozee.pk", report)
        self.assertIn("View report", client.get("/history").get_data(as_text=True))

    def test_matric_student_gets_roadmap_not_jobs(self):
        client, _ = new_student(age="15")
        response = post(client, "/submit", MATRIC_PROFILE, "/")
        page = client.get(response.headers["Location"]).get_data(as_text=True)
        self.assertIn("Your roadmap from Matric", page)
        self.assertIn("MDCAT", page)

    def test_students_cannot_open_each_others_reports(self):
        owner, _ = new_student()
        location = post(owner, "/submit", BS_PROFILE, "/").headers["Location"]
        stranger, _ = new_student()
        self.assertEqual(stranger.get(location).status_code, 404)

    def test_live_preview(self):
        client, _ = new_student()
        data = post(client, "/api/preview", dict(BS_PROFILE, interest_description="I love building AI models"), "/").get_json()
        self.assertTrue(data["ok"])
        self.assertTrue(data["careers"])


class SRSRequirementsTest(unittest.TestCase):
    def test_quiz_is_required_on_submit(self):
        client, _ = new_student()
        profile = {k: v for k, v in BS_PROFILE.items() if k != "q7"}
        response = post(client, "/submit", profile, "/")
        self.assertEqual(response.status_code, 400)
        self.assertIn("personality", response.get_data(as_text=True))

    def test_personality_match_uses_cosine_similarity(self):
        from Database import personality
        careers = [{"career_name": "Nurse", "holland_code": "SI"},
                   {"career_name": "Civil Engineer", "holland_code": "RC"}]
        scores = personality.score_answers(QUIZ)
        match = personality.personality_matches(scores, careers)
        self.assertGreater(match["Nurse"], match["Civil Engineer"])
        self.assertEqual(personality.top_types(scores, 1)[0]["code"], "S")

    def test_report_shows_personality_and_skill_levels(self):
        client, _ = new_student()
        profile = dict(BS_PROFILE, **{"level::Python": "5", "level::SQL": "1"})
        location = post(client, "/submit", profile, "/").headers["Location"]
        html = client.get(location).get_data(as_text=True)
        self.assertIn("Your personality type", html)
        self.assertIn("Skill match", html)
        self.assertIn("Python · 5/5", html)

    def test_skill_level_changes_skill_match(self):
        career = {"required_skills": "Python, SQL"}
        strong = application.skill_profile(career, {"Python": 5, "SQL": 5})[3]
        weak = application.skill_profile(career, {"Python": 1, "SQL": 1})[3]
        self.assertGreater(strong, weak)

    def test_session_times_out_after_30_minutes(self):
        self.assertEqual(application.app.config["PERMANENT_SESSION_LIFETIME"].total_seconds(), 1800)

    def test_returning_student_form_is_prefilled(self):
        client, _ = new_student()
        post(client, "/submit", dict(BS_PROFILE, **{"level::Python": "4"}), "/")
        html = client.get("/").get_data(as_text=True)
        self.assertIn('"education": "BS"', html)
        self.assertIn('"Python": 4', html)
        self.assertIn('"score_type": "cgpa"', html)

    def test_foreign_keys_are_enforced(self):
        import sqlite3
        connection = application.get_connection()
        with self.assertRaises(sqlite3.IntegrityError):
            connection.execute("INSERT INTO Assessments (account_id, created_at, inputs_json) "
                               "VALUES (999999, 'x', '{}')")
        connection.close()

    def test_passwords_use_pbkdf2(self):
        _, email = new_student()
        connection = application.get_connection()
        row = connection.execute("SELECT password_hash FROM Accounts WHERE email = ?", (email,)).fetchone()
        connection.close()
        self.assertTrue(row["password_hash"].startswith("pbkdf2:sha256"))


class AdminTest(unittest.TestCase):
    def test_student_cannot_open_admin_panel(self):
        client, _ = new_student()
        self.assertEqual(client.get("/admin").status_code, 403)

    def test_admin_sign_in_refuses_students(self):
        _, email = new_student()
        client = application.app.test_client()
        response = post(client, "/admin/login", dict(email=email, password="secret123"), "/admin/login")
        self.assertEqual(response.status_code, 403)

    def test_admin_pages_and_add_career(self):
        _, email = new_student()
        make_admin(email)
        client = application.app.test_client()
        post(client, "/admin/login", dict(email=email, password="secret123"), "/admin/login")
        for url in ("/admin", "/admin/careers", "/admin/careers/new", "/admin/users", "/admin/feedback"):
            self.assertEqual(client.get(url).status_code, 200, url)
        response = post(client, "/admin/careers/new", dict(
            career_name="Test Career", education_required="BS", field_required="Computer Science",
            interest="Technology", minimum_percentage="60", required_skills="Python, SQL",
            holland_code="I", description="A test career."), "/admin/careers/new")
        self.assertEqual(response.status_code, 302)


class AIComponentsTest(unittest.TestCase):
    def test_nlp_detects_interests_and_skills(self):
        result = extract("I want to help patients and work in a hospital")
        self.assertIn("Biology", result["interests"])
        self.assertIn("Patient Care", result["skills"])

    def test_roadmap_for_matric_student_aiming_for_doctor(self):
        roadmap = build_roadmap({"career_name": "Doctor", "education_required": "Intermediate",
                                 "field_required": "Medical"}, "Matric", "Medical", [])
        titles = " ".join(step["title"] for step in roadmap["steps"])
        self.assertIn("FSc Pre-Medical", titles)
        self.assertIn("MDCAT", titles)
        self.assertIn("MBBS", titles)
        self.assertEqual(roadmap["years"], 8)


class CareerDatabaseTest(unittest.TestCase):
    def careers(self):
        connection = application.get_connection()
        rows = [dict(r) for r in connection.execute("SELECT * FROM Careers")]
        connection.close()
        return rows

    def test_database_has_88_careers_including_srs_samples(self):
        names = {c["career_name"] for c in self.careers()}
        self.assertGreaterEqual(len(names), 88)
        for name in ("Entrepreneur", "Business Consultant", "IT Project Manager", "Photographer",
                     "Art Director", "Music Producer", "Industrial Engineer", "Radiologist"):
            self.assertIn(name, names)

    def test_every_career_has_a_holland_code(self):
        from Database import personality
        for career in self.careers():
            self.assertTrue(personality.clean_code(career["holland_code"]), career["career_name"])

    def test_career_details_page(self):
        career = next(c for c in self.careers() if c["career_name"] == "Doctor")
        html = application.app.test_client().get(f"/career/{career['id']}").get_data(as_text=True)
        self.assertIn("Required subjects", html)
        self.assertIn("FSc Pre-Medical", html)
        self.assertIn("MDCAT", html)
        self.assertEqual(application.app.test_client().get("/career/999999").status_code, 404)

    def test_every_career_has_a_specific_roadmap(self):
        from Database.roadmap import _track_for
        for career in self.careers():
            self.assertNotEqual(_track_for(career), "general", career["career_name"])
            for level, field in (("Matric", "Medical"), ("Intermediate", "Engineering"), ("BS", "Sciences")):
                roadmap = build_roadmap(career, level, field, [])
                self.assertTrue(roadmap["steps"], career["career_name"])

    def test_new_careers_are_recommended(self):
        client, _ = new_student(age="18")
        cases = [
            (dict(education="Intermediate", field="Medical", interest="Biology", matric_percentage="85",
                  inter_percentage="80", skills=["Biology", "Animal Care"],
                  interest_description="I love animals and want to treat sick pets"), "Veterinary Doctor"),
            (dict(education="Intermediate", field="Commerce", interest="Business", matric_percentage="80",
                  inter_percentage="75", skills=["Accounting", "Taxation", "Auditing"]), "Chartered Accountant"),
            (dict(education="Intermediate", field="Arts", interest="Public Service", matric_percentage="78",
                  inter_percentage="72", skills=["Leadership", "Physical Fitness", "Discipline"]), "Army Officer"),
        ]
        for profile, expected in cases:
            data = post(client, "/api/preview", profile, "/").get_json()
            self.assertEqual(data["careers"][0]["name"], expected)

    def test_seeding_runs_only_once(self):
        before = len(self.careers())
        connection = application.get_connection()
        application.seed_careers(connection)
        connection.close()
        self.assertEqual(len(self.careers()), before)


def tearDownModule():
    shutil.rmtree(_TEMP_DIR, ignore_errors=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
