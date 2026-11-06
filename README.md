# AI-Based Career Counselling System

Final Year Design Project (FYDP), BS Computer Science, Session 2022–2026
Department of Computer Science & IT, University of Southern Punjab, Multan

| Student | Registration no. |
|---|---|
| Ahmad Jamal | BSCS-023A22-16 |
| M. Danial Mazhar | BSCS-023R22-39 |
| M. Hamza Zayan | BSCS-023R22-100 |

**Supervisor:** Sir Imran Ali

---

## 1. Project title and brief description

**AI-Based Career Counselling System** is a web application that recommends suitable careers to students in Pakistan, from Matric and O Level to BS and MS, and explains each recommendation.

The student enters their education level, field of study, Matric, Intermediate and degree results, main interest, a short description in their own words, up to 8 skills with a level from 1 to 5, and answers a 15-question Holland (RIASEC) personality quiz. A hybrid AI engine then ranks 88 careers by combining:

- **knowledge-based scoring** of field, interest, education, marks and skills;
- **natural language processing** of the student's description (tokenising, stemming, TF-IDF and cosine similarity);
- a **machine learning model** chosen from Random Forest, Support Vector Machine, K-Nearest Neighbours and Decision Tree by 10-fold cross-validation (Random Forest, 92.7% accuracy);
- a **personality match** between the student's quiz answers and each career's Holland code, using cosine similarity.

Each report shows the top 5 careers with reasons, personality type, skill gap, a step-by-step roadmap (Intermediate group, entry test, degree, licence, first job), and links to live jobs (Rozee.pk, LinkedIn, Indeed) and free courses. Careers a student cannot enter yet are shown as a next-step pathway instead of a false match. Reports are saved, can be downloaded as PDF and rated. An admin panel manages careers, users and feedback and retrains the AI model.

---

## 2. Tools, technologies and software used

| Category | Technology | Version tested |
|---|---|---|
| Programming language | Python | 3.13 (3.10 or newer supported) |
| Web framework | Flask, with Jinja2 templates and Werkzeug | Flask 3.1.3, Jinja2 3.1.6, Werkzeug 3.1.8 |
| Database | SQLite 3 (built into Python) | — |
| Machine learning | scikit-learn, NumPy | scikit-learn 1.9.1, NumPy 2.5.3 |
| HTTP client | requests (optional live job openings) | 2.34.2 |
| Front end | HTML5, CSS3, JavaScript | — |
| Security | PBKDF2-SHA256 password hashing (Werkzeug), CSRF tokens, rate limiting | — |
| Testing | Python `unittest` with Flask's test client | — |
| Development tools | Visual Studio Code, Git, Google Chrome | — |

---

## 3. System requirements and prerequisites

**Hardware**

- Processor: dual-core or better
- Memory: 4 GB RAM (minimum)
- Disk: 1 GB of free space
- Students only need a computer, tablet or phone with a modern browser

**Software**

- Operating system: Windows 10/11, macOS or Linux
- **Python 3.10 or newer**, with `pip` (on Windows, tick **"Add Python to PATH"** during installation)
- A web browser: Chrome, Firefox or Edge
- Internet connection only for installing packages; the system itself runs offline (job and course links open external sites)

Check Python is installed:

```
python --version
```

---

## 4. Step-by-step installation and configuration

1. **Unzip** `Career-System-FINAL.zip` to a folder, for example `D:\Career-System`.
2. **Open a terminal in the project folder**, the folder that contains `app.py`:
   - Windows: open the folder in File Explorer, type `cmd` in the address bar and press Enter (or open the folder in VS Code and use *Terminal → New Terminal*).
   - macOS/Linux: `cd` into the folder.
3. *(Optional, recommended)* **Create a virtual environment**:
   ```
   python -m venv venv
   venv\Scripts\activate          (Windows)
   source venv/bin/activate       (macOS/Linux)
   ```
4. **Install the dependencies** (see section 5):
   ```
   pip install -r requirements.txt
   ```
5. **Create an administrator account**:
   ```
   python create_admin.py
   ```
   Enter an e-mail address, a full name and a password (at least 8 characters).

**Configuration (optional).** The system works without any configuration. These environment variables can be set if needed:

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Fixed secret key for sessions. If not set, a random key is created on the first run and stored in `instance/secret_key` (keep this folder private) |
| `ADZUNA_APP_ID`, `ADZUNA_APP_KEY` | Show a few live job openings inside reports (free key from developer.adzuna.com) |
| `CAREER_DB_PATH` | Use a different database file |
| `FLASK_DEBUG=1` | Debug mode, for development only |

Set one on Windows with `set SECRET_KEY=your-long-random-text`, or on macOS/Linux with `export SECRET_KEY=your-long-random-text`, before running the application.

---

## 5. Required dependencies and how to install them

All dependencies are listed in `requirements.txt`:

| Package | Why it is needed |
|---|---|
| `Flask` | Web framework: pages, forms, sessions (installs Jinja2 and Werkzeug) |
| `scikit-learn` | Machine learning models, cross-validation, cosine similarity |
| `numpy` | Numerical arrays used by the ML and personality modules |
| `requests` | Optional live job openings from the Adzuna API |

Install them all with one command from the project folder:

```
pip install -r requirements.txt
```

If `pip` is not recognised, use `python -m pip install -r requirements.txt`.

Everything else (SQLite, `unittest`, `csv`, `hashlib`, …) is part of Python's standard library and needs no installation.

---

## 6. Database setup and configuration

The project uses **SQLite**, so there is **no database server to install**. The complete database is included:

```
Database/career_counseling.db
```

It already contains all **88 careers** (with Holland codes, required skills, salaries, future scope and learning resources), 12 interests and their career links, and empty tables for accounts, reports and feedback. **No setup is needed**: the application uses it automatically.

What happens automatically when the application starts:

- if the database file is missing, it is created with all tables and all 88 careers;
- newer columns, careers, Holland codes and indexes are added to an older database without deleting existing accounts or reports;
- foreign keys are enforced on every connection.

**Database and dataset files**

| File | Contents |
|---|---|
| `Database/career_counseling.db` | The complete SQLite database used by the application |
| `Database/export/schema.sql` | `CREATE TABLE` and `CREATE INDEX` statements for every table |
| `Database/export/careers.csv` | All 88 careers with every field (opens in Excel) |
| `Database/export/interests.csv` | The 12 interests and the careers linked to each |
| `Database/ml/training_dataset.csv` | Machine learning dataset: 5,280 labelled student profiles (60 per career) |
| `Database/ml/model_metrics.json` | Accuracy, precision, recall and F1 of the four models (10-fold cross-validation) |
| `Database/careers_data.py` | Source data of the careers added in versions 2 and 3 |
| `Database/README_DATABASE.md` | Data dictionary: every table, column and dataset field explained |

**Useful database commands**

| Command | What it does |
|---|---|
| `python tools/export_database.py` | Re-export `schema.sql`, `careers.csv` and `interests.csv` from the database |
| `python train_model.py` | Regenerate the training dataset and compare the four ML models again |
| `python Database/create_database.py --force` | Rebuild the career tables from scratch (back up the database first); the next start adds all 88 careers back |

**Backup:** stop the application and copy `Database/career_counseling.db` to a safe place. To restore, copy it back.

To view the database, open `career_counseling.db` in the free tool *DB Browser for SQLite*.

---

## 7. Step-by-step instructions for running the project

1. Open a terminal in the project folder (and activate the virtual environment if you created one).
2. Start the application:
   ```
   python app.py
   ```
3. Wait for the message `Running on http://127.0.0.1:5000`. The AI model trains in the background during the first few seconds, so the very first recommendation may take a moment longer.
4. Open **http://127.0.0.1:5000** in your browser.
5. **As a student:** click **Create account**, fill in your details and a recovery question, then complete the assessment (education, interest, skills with levels, and the 15 personality questions) and click **Get AI Career Recommendation**. Your report opens with your top careers, personality type, skill gap, roadmap and job links. Use **View details**, **Download PDF report** and **My reports**.
6. **As an administrator:** click **Administrator sign-in** in the footer (or open http://127.0.0.1:5000/admin/login) and sign in with the account created by `create_admin.py`. Manage **Careers**, **Users** and **Feedback**, and click **Retrain AI model** after changing careers.
7. To stop the application, press **Ctrl + C** in the terminal.

**Run the automated tests** (36 tests; they use a temporary copy of the database, so real data is never changed):

```
python -m unittest discover tests -v
```

**Troubleshooting**

| Problem | Solution |
|---|---|
| `can't open file 'app.py'` | The terminal is in the wrong folder; `cd` to the folder that contains `app.py` |
| `'python' is not recognized` | Reinstall Python and tick "Add Python to PATH", or use `py` instead of `python` |
| `ModuleNotFoundError: No module named 'flask'` | Run `pip install -r requirements.txt` (inside the virtual environment if you use one) |
| Port 5000 already in use | Close the other program or the earlier copy of the application |
| Sign-in is blocked | Wait 10 minutes after 5 wrong passwords, or use **Forgot password?** |

---

## Project structure

```
app.py                     Web application: routes, validation, accounts, security, reports, admin panel
create_admin.py            Create an administrator account
train_model.py             Generate the dataset and compare the four ML models
requirements.txt           Python dependencies
Database/
  career_counseling.db     SQLite database (88 careers)
  create_database.py       Builds the career tables from scratch
  careers_data.py          Careers added in versions 2 and 3
  ai_engine.py             Eligibility filter and knowledge-based scoring
  nlp_engine.py            NLP: tokenising, stemming, keyword extraction, TF-IDF
  ml_model.py              Dataset generation, model comparison, prediction
  personality.py           Holland (RIASEC) quiz and cosine-similarity personality match
  roadmap.py               Career roadmaps and required subjects
  job_market.py            Optional live job openings (Adzuna API)
  ml/                      Training dataset and model results
  export/                  Schema and CSV exports of the database
  README_DATABASE.md       Data dictionary
templates/                 HTML pages (Jinja2)
static/                    CSS and JavaScript
tests/                     36 automated tests
tools/                     Database export script and early development scripts
Documentation/             Project documentation, User Manual and Admin Guide
```
