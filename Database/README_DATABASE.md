# Database and Dataset: Data Dictionary

AI-Based Career Counselling System, FYDP 2022–2026, University of Southern Punjab, Multan.

This folder contains the complete database and the machine learning dataset of the project.

## 1. Files

| File | Contents |
|---|---|
| `career_counseling.db` | Complete SQLite 3 database used by the application |
| `export/schema.sql` | `CREATE TABLE` and `CREATE INDEX` statements of every table |
| `export/careers.csv` | All 88 careers with every field (UTF-8, opens in Excel) |
| `export/interests.csv` | The 12 interests and the careers linked to each |
| `ml/training_dataset.csv` | Machine learning dataset: 5,280 labelled student profiles |
| `ml/model_metrics.json` | Results of the four models with 10-fold cross-validation |
| `careers_data.py` | Source data of the 48 careers added in versions 2 and 3 |
| `create_database.py` | Builds the career tables and the original 40 careers |

The database is ready to use. No server or setup is needed; the application opens it automatically. If the file is deleted, the application recreates it with all 88 careers on its next start. Regenerate the CSV and SQL exports with `python tools/export_database.py`.

## 2. Tables

### Careers (88 rows)

| Column | Type | Description |
|---|---|---|
| id | INTEGER, primary key | Career identifier |
| career_name | TEXT | Name, for example "Doctor" |
| education_required | TEXT | Minimum education to start the career: Intermediate, BS, MS, … |
| field_required | TEXT | Required field of study: Medical, Engineering, Computer Science, … |
| minimum_percentage | REAL | Minimum academic percentage (0–100) |
| interest | TEXT | Main interest the career matches, for example "Biology" |
| description | TEXT | Short description of the career |
| required_skills | TEXT | Comma-separated required skills |
| future_scope | TEXT | Future scope: Excellent, Very High, High, … |
| average_salary | TEXT | Indicative monthly salary in Pakistan |
| learning_resources | TEXT | Recommended learning resources |
| holland_code | TEXT | Holland (RIASEC) personality code, 1–3 letters, for example "IS" |

### Interests (12 rows) and CareerInterests

| Table | Column | Description |
|---|---|---|
| Interests | id, interest_name | The interests a student can choose |
| CareerInterests | career_id → Careers.id, interest_id → Interests.id | Which careers relate to each interest (many-to-many) |

### Accounts

| Column | Description |
|---|---|
| id | Account identifier (primary key) |
| full_name, email (unique), age, gender | Student or administrator details |
| password_hash | PBKDF2-SHA256 hash; passwords are never stored in plain text |
| is_admin | 1 for administrators, 0 for students |
| security_question, security_answer_hash | Recovery question and the hash of its answer |
| reset_token_hash, reset_token_expires | One-time password reset link created by an administrator (SHA-256 hash, 1-hour expiry) |
| created_at | Date and time the account was created |

### Assessments

| Column | Description |
|---|---|
| id | Report identifier (used in `/report/<id>`) |
| account_id → Accounts.id | Student who took the assessment |
| created_at | Date and time |
| inputs_json | The student's inputs as JSON: education, field, results, interest, description, skills, skill levels, quiz answers and personality scores |
| top_career | Best matching career |
| results_json | Complete snapshot of the report, so it always reopens exactly as it was |

### Feedback

| Column | Description |
|---|---|
| id | Feedback identifier |
| assessment_id → Assessments.id (unique) | The report being rated (one rating per report) |
| account_id → Accounts.id | Student who gave the rating |
| helpful | 1 = "Yes, helpful", 0 = "Not really" |
| comment, created_at | Optional comment and date |

### Users and Meta

| Table | Description |
|---|---|
| Users | Simple log of each assessment's profile (name, age, gender, education level, field, percentage, CGPA), kept from the first version |
| Meta | Settings used by migrations, for example `careers_seed` = data version |

The shipped database has **no accounts, reports or feedback**: they are created when students use the system. Foreign keys are enforced, and indexes exist on `Assessments(account_id)`, `Feedback(account_id)`, `CareerInterests(career_id)` and `Accounts(reset_token_hash)`.

## 3. Machine learning dataset (`ml/training_dataset.csv`)

No public dataset of Pakistani student profiles and career outcomes exists, so the dataset is generated from the career database by `train_model.py` (fixed random seed, so it is reproducible):

- 5,280 profiles: 60 for each of the 88 careers.
- Each profile starts from a career's real requirements and adds variation: about 15% have a different field, about 20% a different interest, marks vary around the career's minimum, and skills are a random subset of the required ones plus up to two unrelated skills.

| Column | Description |
|---|---|
| education_rank | 1 = Matric/O Level, 2 = Intermediate/A Level, 3 = BS, 4 = MS, 5 = PhD |
| field | Field of study (10 values) |
| interest | Main interest (11 values) |
| percentage | Overall academic percentage |
| skills | Skills separated by `\|` |
| career | Label: the career this profile belongs to (88 classes) |

The models encode each profile as a 175-feature vector: education level, percentage, field (one-hot), interest (one-hot) and skills (multi-hot).

## 4. Model results (`ml/model_metrics.json`)

Stratified 10-fold cross-validation, macro-averaged:

| Model | Accuracy | Precision | Recall | F1 |
|---|---|---|---|---|
| Random Forest (selected) | 92.7% ± 0.8 | 0.936 | 0.927 | 0.926 |
| Support Vector Machine | 92.4% ± 1.2 | 0.934 | 0.924 | 0.923 |
| K-Nearest Neighbours | 87.1% ± 1.2 | 0.889 | 0.871 | 0.868 |
| Decision Tree | 78.5% ± 1.8 | 0.810 | 0.785 | 0.784 |

Because the data is synthetic, these scores show how well each model learns the career requirements, not real-world career success. The Feedback table collects real ratings for later evaluation.
