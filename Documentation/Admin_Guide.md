# Administrator Guide: AI Career Counselling System

This guide is for the person who runs the system: installing it, creating an administrator, managing careers and users, retraining the AI model and keeping backups.

## 1. Installing and starting

You need Python 3.10 or newer. Open a terminal in the project folder (the one that contains `app.py`):

```
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000. Keep the terminal open while the site is in use; press Ctrl+C to stop it.

On the first start with an older database, the system adds any new careers and Holland codes automatically. Accounts, reports and feedback are kept.

## 2. Creating an administrator

```
python create_admin.py
```

Enter an email, full name and password (at least 8 characters). If the email already belongs to a student account, that account is given admin rights instead, and keeps its own password.

To sign in, click **Administrator sign-in** in the footer, or open http://127.0.0.1:5000/admin/login. Student accounts are refused on this page.

## 3. Dashboard

The dashboard shows the number of students, assessments and careers, the percentage of feedback that found the recommendations helpful, assessments by education level, the most recommended careers and the latest assessments.

## 4. Managing careers

Open **Careers**. Use the search box to find a career, then **Edit** or **Delete** it, or click **Add career**.

| Field | Notes |
|---|---|
| Career name | Must be unique |
| Minimum education | The lowest level at which the career can be started (Intermediate, BS, MS, and so on) |
| Field of study | The field a student needs. Students in other fields get a lower match |
| Main interest | The interest this career is matched to |
| Minimum percentage | Students below it get a lower match |
| Related interests | Other interests that also fit |
| Required skills | Comma separated, for example `Python, SQL, Statistics`. New skills appear in the assessment form automatically |
| Personality type (Holland code) | Choose up to 3 types, most important first. For example a nurse is Social then Investigative (`SI`). Used for the personality match |
| Description, future scope, average salary, learning resources | Shown to students in the report and on the career details page |

The roadmap and the required subjects are chosen automatically from the career's name and field. A new career with an unusual name gets the general roadmap for its field.

After adding, editing or deleting careers, **retrain the AI model** (section 6) so the machine learning part knows about the change.

A deleted career is not added back when the application restarts. Reports that students already received keep their saved copy.

## 5. Managing users

Open **Users** to see every account, its number of assessments and its role.

- **Make admin / Remove admin**: give or remove admin rights. You cannot remove your own.
- **Reset link**: creates a one-time password reset link for a student who has forgotten both the password and the recovery answer. Click **Copy link** and give it to the student in person or by message. The link works once and expires after 1 hour.

## 6. Retraining the AI model

On the dashboard, under **AI model**, click **Retrain AI model**. This regenerates the training data from the current careers, compares Random Forest, K-Nearest Neighbours, Decision Tree and Support Vector Machine with 10-fold cross-validation, and uses the best one. It takes about 15–30 seconds.

The same can be done from the terminal:

```
python train_model.py
```

The results are shown on the public **How the AI works** page.

## 7. Feedback

Open **Feedback** to see each student's answer ("Yes" or "No"), their comment, and the top career they were given. The percentage at the top is the share who found the recommendations helpful (the SRS target is 75% or more).

## 8. Backups

All data is in one file: `Database/career_counseling.db`.

To back up, stop the website (Ctrl+C), copy that file to a safe place with the date in its name (for example `backups/career_counseling_2026-10-17.db`), then start the website again. Back up at least once a week, and always before editing many careers.

To restore, stop the website and copy the backup over `Database/career_counseling.db`.

`Database/create_database.py` rebuilds the career tables from scratch. It refuses to run on a database that has accounts unless you add `--force`. Make a backup first.

## 9. Security settings

| Setting | Value |
|---|---|
| Password storage | PBKDF2-SHA256, 600,000 iterations; never plain text |
| Session timeout | 30 minutes of inactivity |
| Failed sign-ins | 5 wrong passwords in 10 minutes pause sign-in for 10 minutes |
| CSRF protection | Every form and request carries a secret token |
| Secret key | The `SECRET_KEY` environment variable, or a random key created on first run in `instance/secret_key`. Do not share or commit the `instance` folder |

Optional environment variables:

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Fixed secret key for sessions |
| `FLASK_DEBUG=1` | Debug mode, for development only |
| `ADZUNA_APP_ID`, `ADZUNA_APP_KEY` | Show a few live job openings inside reports |
| `CAREER_DB_PATH` | Use a different database file (the automated tests use this) |

## 10. Checking that everything works

```
python -m unittest discover tests -v
```

The 36 automated tests run on a temporary copy of the database, so real data is never changed. All should pass.

## 11. Troubleshooting

| Problem | Fix |
|---|---|
| `can't open file 'app.py'` | The terminal is in the wrong folder. Use `cd` to go to the folder that contains `app.py` |
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| Port 5000 is already in use | Close the other program, or stop the earlier copy of the website |
| A student is locked out | Wait 10 minutes, or create a reset link for them |
| A new career is never recommended | Check its minimum education, field and percentage, then retrain the model |
