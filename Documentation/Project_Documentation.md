# AI-Based Career Counselling System

## 1. Introduction

The AI-Based Career Counselling System is a web-based application developed to help users identify suitable career options according to their educational background, academic performance, interests, skills, and the student's own description.

The system analyzes the user's submitted information and provides ranked career recommendations using an AI-based weighted scoring mechanism.

## 2. Problem Statement

Students often face difficulty selecting a suitable career because they may not have sufficient guidance about which careers match their education, academic performance, interests, and skills.

The proposed system provides an automated career counselling solution that analyzes a user's profile and recommends suitable career paths.

## 3. Objectives

### 3.1 Main Objective

To develop a web-based AI career counselling system that recommends suitable careers according to a user's personal and educational profile.

### 3.2 Specific Objectives

1. Collect user personal information.
2. Collect educational information.
3. Collect academic performance.
4. Collect user interests.
5. Collect user skills.
6. Analyze the submitted profile.
7. Match the profile with available careers.
8. Rank careers according to compatibility.
9. Display career recommendations.
10. Provide career and job-market information where available.
11. Store assessment information in the database.

## 4. Technologies Used

- Python
- Flask
- SQLite
- HTML
- CSS
- JavaScript
- Requests
- Adzuna Job Search API

## 5. System Overview

The system consists of a web-based frontend, Flask backend, SQLite database, AI recommendation engine, and optional job-market integration.

The user first completes a career assessment form. The submitted information is processed by the Flask application and passed to the AI recommendation engine. The recommendation engine evaluates available careers and generates a ranked list of suitable careers.

## 6. Major System Modules

### 6.1 User Assessment Module

### 6.2 Database Module

### 6.3 AI Recommendation Module

### 6.4 Career Information Module

### 6.5 Job Market Module

### 6.6 Result Display Module

## 7. AI Recommendation System

The recommendation engine evaluates careers using multiple factors:

- Field compatibility
- Interest compatibility
- Education compatibility
- Academic performance
- Skills compatibility
- Description match (NLP similarity between the student's own words and the career)

Each factor contributes a weighted percentage to the final career compatibility score.

### 7.1 Weighted Scoring

The system calculates a compatibility score for every eligible career.

The scoring weights used by the recommendation engine are:

| Factor | Weight |
|---|---:|
| Field Compatibility | 25% |
| Interest Compatibility | 20% |
| Education Compatibility | 15% |
| Academic Performance | 15% |
| Skills Compatibility | 15% |
| Description Match (NLP) | 10% |
| **Total** | **100%** |

Each factor is evaluated independently and converted into its corresponding weighted points.

The final career score is calculated as:

**Knowledge-based score = Field + Interest + Education + Academic + Skills + Description match**

**Final score = 70% × knowledge-based score + 15% × machine learning score + 15% × personality match** (see Chapters 18 and 26). Before the personality quiz is answered (live preview) the blend is 80% knowledge-based and 20% machine learning.

The maximum possible score is 100%.

### 7.2 Career Eligibility

Before calculating the final ranking, the system checks whether a career is suitable for the user's profile.

The recommendation process considers:

- Education level
- Field of study
- Academic score
- Interest
- Skills
- Description match (NLP)

Careers that do not satisfy the required eligibility conditions can be excluded from the final recommendations.

### 7.3 Recommendation Ranking

After calculating the compatibility score for eligible careers, the system sorts the careers from highest score to lowest score.

The highest-scoring careers are displayed first as the user's recommended career options.

### 7.4 Special Case: Public Service

For users who select **Public Service** as their interest, the system gives special consideration to the **CSS Officer** career.

This prevents unrelated careers from being incorrectly recommended when the user's selected career direction is public service.

### 7.5 Example

For a Computer Science student with a Programming interest and relevant technical skills, careers such as AI Engineer, Software Engineer, Data Scientist, Web Developer, and Cyber Security Analyst can receive different compatibility scores.

The system ranks these careers according to their calculated scores.

## 8. Database

The system uses SQLite as its database management system. The database file is stored at:

`Database/career_counseling.db`

The database contains the following tables (`sqlite_sequence` is an SQLite internal table):

1. Users
2. Careers
3. Interests
4. CareerInterests
5. Accounts (sign-up / sign-in, with an admin flag)
6. Assessments (saved results history, including the full report snapshot)
7. Feedback (user ratings of recommendations)

### 8.1 Users Table

The `Users` table stores the information submitted by users during the career assessment.

The table contains user-related information such as:

- User ID
- Name
- Age
- Gender
- Education Level
- Field of Study
- Academic Percentage
- CGPA

The primary key is the user `id`.

### 8.2 Careers Table

The `Careers` table stores the career information used by the recommendation engine.

The table contains the following fields:

| Field | Data Type | Description |
|---|---|---|
| id | INTEGER | Unique career identifier |
| career_name | TEXT | Name of the career |
| education_required | TEXT | Required education level |
| field_required | TEXT | Required field of study |
| minimum_percentage | REAL | Minimum academic percentage |
| interest | TEXT | Related user interest |
| description | TEXT | Career description |
| required_skills | TEXT | Skills required for the career |
| future_scope | TEXT | Future scope of the career |
| average_salary | TEXT | Average salary information |
| learning_resources | TEXT | Recommended learning resources |

The system currently contains **88 career records** (40 original careers, 40 added in version 2 and the 8 remaining SRS sample careers added in version 3). Each career also has a `holland_code` column (for example `IS` for Doctor) used for personality matching.

### 8.3 Interests Table

The `Interests` table stores the interests that can be associated with career options.

Interests help the recommendation engine determine how closely a user's selected interest matches a career.

### 8.4 CareerInterests Table

The `CareerInterests` table connects careers with their corresponding interests.

This relationship allows the system to associate multiple career options with relevant user interests.

### 8.5 sqlite_sequence Table

The `sqlite_sequence` table is an SQLite system table automatically maintained for tables that use `AUTOINCREMENT`.

It keeps track of the next available identifier for automatically incremented primary keys.

### 8.6 Career Records

The original database contained the following 40 career options (the 40 careers added in version 2 are listed in Chapter 25):

| ID | Career |
|---:|---|
| 1 | Software Engineer |
| 2 | AI Engineer |
| 3 | Data Scientist |
| 4 | Web Developer |
| 5 | Cyber Security Analyst |
| 6 | Doctor |
| 7 | Dentist |
| 8 | Pharmacist |
| 9 | Graphic Designer |
| 10 | Animator |
| 11 | Accountant |
| 12 | Bank Manager |
| 13 | Marketing Manager |
| 14 | Civil Engineer |
| 15 | Mechanical Engineer |
| 16 | Electrical Engineer |
| 17 | Teacher |
| 18 | Lecturer |
| 19 | Lawyer |
| 20 | CSS Officer |
| 21 | AI Research Scientist |
| 22 | Machine Learning Engineer |
| 23 | Data Analyst |
| 24 | Cloud Engineer |
| 25 | DevOps Engineer |
| 26 | Mobile App Developer |
| 27 | Network Engineer |
| 28 | Database Administrator |
| 29 | UI/UX Designer |
| 30 | Game Developer |
| 31 | Biomedical Engineer |
| 32 | Chemical Engineer |
| 33 | Environmental Engineer |
| 34 | Economist |
| 35 | Financial Analyst |
| 36 | Human Resources Manager |
| 37 | Content Writer |
| 38 | Psychologist |
| 39 | Journalist |
| 40 | Public Administration Officer |
## 9. System Workflow and Architecture

The AI-Based Career Counselling System follows a sequence of connected modules. The user first enters personal, educational, academic, interest, and skill information through the web interface. The Flask backend validates and processes the submitted information.

The processed information is stored in the SQLite database and passed to the AI recommendation engine. The recommendation engine evaluates the user's profile against the available career records using the weighted scoring mechanism.

Eligible careers are scored and ranked according to compatibility. The highest-ranked careers are then displayed on the result page together with career information, explainable AI scoring details, and available live job-market information.

### 9.1 System Workflow

The overall workflow of the system is:

User
↓
Career Assessment Form
↓
Flask Web Application
↓
Input Validation
↓
SQLite Database
↓
AI Recommendation Engine
↓
Career Eligibility Filtering
↓
Weighted Compatibility Scoring
↓
Career Ranking
↓
Top Career Recommendations
↓
Career Information
↓
Live Job Market Information
↓
Final Results Page

### 9.2 System Architecture Components

The system consists of the following major architectural components:

#### Presentation Layer

The presentation layer is the web interface through which users enter their information and view career recommendations.

Technologies:
- HTML
- CSS
- JavaScript
- Jinja2 Templates

#### Application Layer

The application layer is responsible for receiving requests, validating data, storing user information, and coordinating the recommendation process.

Technology:
- Python Flask

#### AI Recommendation Layer

The AI recommendation layer evaluates user profiles against career records and calculates weighted compatibility scores.

Major factors include:
- Field of study
- Career interest
- Education
- Academic performance
- Skills
- Description match (NLP)

#### Database Layer

The database layer stores user information, career information, interests, and career-interest relationships.

Technology:
- SQLite

#### Job Market Layer

The optional job-market layer retrieves current employment information for supported careers and displays job counts, salary information, companies, and locations.

Technology:
- Adzuna Job Search API

### 9.3 Overall Data Flow

The user's assessment data flows through the system in the following order:

1. The user completes the career assessment form.
2. Flask receives the submitted information.
3. The application validates the submitted data.
4. User assessment information is stored in the SQLite database.
5. The AI recommendation engine retrieves suitable career records.
6. Career eligibility is evaluated.
7. Each eligible career receives a compatibility score.
8. Careers are sorted according to their final scores.
9. The top career matches are selected.
10. Additional career information is displayed.
11. Live job-market information is retrieved where available.
12. The final recommendations are presented to the user.

## 10. Use Case Diagram

The Use Case Diagram represents the interaction between the user and the AI-Based Career Counselling System.

The main actor of the system is the User. The user provides personal, educational, academic, interest, and skill information through the career assessment interface. After processing the submitted information, the system provides ranked career recommendations and supporting career information.

### 10.1 Main Actor

**User**

The user interacts with the system to provide assessment information and obtain personalized career recommendations.

### 10.2 Main Use Cases

| Use Case | Description |
|---|---|
| Enter Profile Information | User enters name, age, and gender. |
| Enter Education Information | User selects education level and field of study. |
| Enter Academic Score | User provides percentage or CGPA. |
| Select Career Interest | User selects the preferred career interest. |
| Select Skills | User selects relevant skills. |
| Submit Assessment | User submits the completed assessment. |
| Generate Recommendations | System analyzes the profile and ranks suitable careers. |
| View Reasons and Skill Gap | User views why each career was recommended, the personality match and the skills still to learn. |
| View Career Information | User views description, skills, salary, future scope, and resources. |
| View Job Market | User views available live job-market information. |
| Take Another Assessment | User can return to the assessment form. |

## 11. Data Flow Diagram (DFD) Level 0

The Level 0 Data Flow Diagram represents the AI-Based Career Counselling System as a single major process and shows the interaction between the external user and the system.

The user provides personal, educational, academic, interest, and skill information to the system. The system processes this information and returns career recommendations, AI scoring information, career details, and available job-market information.

### 11.1 External Entity

**User**

The user interacts directly with the AI-Based Career Counselling System.

### 11.2 Main System Process

**AI-Based Career Counselling System**

The system receives assessment information, processes the submitted profile, evaluates suitable careers, generates recommendations, and returns the final results.

### 11.3 Data Flows

#### User → System

The user provides:

- Personal information
- Education level
- Field of study
- Academic score
- Career interest
- Selected skills
- Description of interests (free text)

#### System → User

The system provides:

- Ranked career recommendations
- AI compatibility scores
- Reasons for each recommendation
- Step-by-step career roadmap
- Career descriptions
- Required skills
- Future scope
- Average salary
- Learning resources
- Available live job-market information

### 11.4 DFD Level 0 Flow

The overall Level 0 flow can be represented as:

User
↓
AI-Based Career Counselling System
↓
Career Recommendations and Supporting Information

The Level 0 diagram provides a high-level view of the system without showing its internal modules or database processes.

## 12. Data Flow Diagram (DFD) Level 1

The Level 1 Data Flow Diagram expands the main process shown in the Level 0 Context Diagram into the major internal processes of the AI-Based Career Counselling System.

It shows how assessment data is received, validated, stored, analyzed, scored, ranked, supplemented with job-market information, and finally presented to the user.

### 12.1 Main Processes

**1.0 User Assessment**

Receives personal, educational, academic, interest, skill, and the student's own description information from the user.

**2.0 Input Validation & Storage**

Validates the submitted information and stores the user's assessment data in the SQLite database.

**3.0 Career Eligibility Filtering**

Retrieves career records and checks whether careers satisfy the user's education, field, academic, and interest requirements.

**4.0 AI Compatibility Scoring**

Calculates a weighted compatibility score for each eligible career using field, interest, education, academic performance, skills, and the student's own description.

**5.0 Career Ranking & Recommendation**

Sorts eligible careers according to their final compatibility scores and selects the strongest career matches.

**6.0 Job Market Integration**

Retrieves available live job-market information for supported careers through the external job-market service.

**7.0 Results Generation**

Combines the recommendation scores, career information, explainable AI details, and available job-market information and presents the final results to the user.

### 12.2 Data Stores

| Data Store | Description |
|---|---|
| D1 — Users | Stores submitted user assessment information. |
| D2 — Careers | Stores career requirements and career information. |
| D3 — Interests | Stores available career interests. |
| D4 — CareerInterests | Stores relationships between careers and interests. |

### 12.3 Level 1 Data Flow

The detailed data flow is:

1. User submits assessment information.
2. User Assessment receives the information.
3. Input Validation checks the submitted values.
4. Valid user information is stored in the Users data store.
5. Career information and interest relationships are retrieved from the database.
6. Career Eligibility Filtering removes unsuitable careers.
7. AI Compatibility Scoring calculates the weighted score for eligible careers.
8. Career Ranking sorts careers according to final compatibility.
9. Top career recommendations are selected.
10. Job Market Integration retrieves live market information where available.
11. Results Generation prepares the final recommendation page.
12. The system returns recommendations and supporting career information to the user.

## 13. Entity Relationship Diagram (ERD)

The Entity Relationship Diagram represents the structure of the SQLite database used by the AI-Based Career Counselling System.

The database contains the following main entities:

### 13.1 Users

Stores information submitted by users during the career assessment.

Main attributes:

- id
- name
- age
- gender
- education_level
- field_of_study
- percentage
- cgpa

### 13.2 Careers

Stores information about available career options and their requirements.

Main attributes:

- id
- career_name
- education_required
- field_required
- minimum_percentage
- interest
- description
- required_skills
- future_scope
- average_salary
- learning_resources

### 13.3 Interests

Stores the available career interests used by the system.

### 13.4 CareerInterests

Stores relationships between careers and interests.

### 13.5 Relationships

The database uses `CareerInterests` to associate career records with relevant interests.

The main relationship is:

**Careers → CareerInterests ← Interests**

This allows a career to be associated with its relevant interest categories.

The `Users` table stores individual assessment information, while the `Careers` and interest-related tables provide the data used by the AI recommendation engine.
## 14. Testing

Testing was performed to verify that the database, AI recommendation engine, input processing, and result generation work correctly.

### 14.1 Database Testing

The SQLite database was verified using the database verification script.

The verification confirmed:

- Database exists successfully.
- Database is stored at `Database/career_counseling.db`.
- The database contains the required tables.
- The Careers table contains 88 career records.
- The Interests table contains 12 interests.
- Career-interest relationships were successfully inserted.

### 14.2 AI Recommendation Engine Testing

The recommendation engine was tested with different student profiles, including skill levels and personality quiz answers. The results below were produced by the final system (88 careers, Random Forest model).

#### Test Case 1: Computer Science Student

**Profile:** BS, Computer Science, CGPA 3.5 (Matric 85%, Intermediate 80%); interest Programming; skills Python (5), Machine Learning (4), SQL (3), Statistics (2); description "I enjoy building AI models and analysing data"; personality mainly Investigative and Conventional.

**Expected result:** careers in computing and data.

| Rank | Career | Score |
|---:|---|---:|
| 1 | Machine Learning Engineer | 86.95% |
| 2 | AI Engineer | 80.99% |
| 3 | Data Scientist | 80.15% |
| 4 | Data Engineer | 78.57% |
| 5 | Software Engineer | 71.55% |

**Status:** Passed

#### Test Case 2: Medical Student

**Profile:** Intermediate, Pre-Medical (Matric 91%, Intermediate 86%); interest Biology; skills Biology (5), Patient Care (3), Communication (2); description "I want to help patients and work in a hospital"; personality mainly Social and Investigative.

**Expected result:** medical and health careers.

| Rank | Career | Score |
|---:|---|---:|
| 1 | Doctor | 90.47% |
| 2 | Nurse | 88.89% |
| 3 | Physiotherapist | 74.50% |
| 4 | Nutritionist | 67.58% |
| 5 | Dentist | 66.56% |

**Status:** Passed

#### Test Case 3: Public Service Candidate

**Profile:** BS, Arts, CGPA 3.2; interest Public Service; skills Leadership (4), Communication (4), Public Speaking (3); description "I want to serve the country as a civil servant"; personality mainly Enterprising and Social.

**Expected result:** public service careers.

| Rank | Career | Score |
|---:|---|---:|
| 1 | Social Worker | 80.04% |
| 2 | CSS Officer | 68.85% |
| 3 | Army Officer | 64.81% |
| 4 | Civil Judge | 53.47% |
| 5 | Hotel Manager | 53.22% |

**Status:** Passed. The top four are public service, defence and law careers. Hotel Manager in fifth place is a weak match (53%), shown with a lower fit label.

#### Test Case 4: Supervisor's Test (Matric, Computer Science, age 70, every skill)

**Expected result:** the input is rejected.

**Actual result:** "The age in your profile (70) does not look right for Matric (expected 12-30). Please update your profile or your education level." No careers are recommended.

**Status:** Passed

### 14.3 Website Testing

The Flask web application was tested through the browser.

The test confirmed that:

- The assessment form loads successfully.
- User information can be submitted.
- Selected skills are received correctly.
- Career recommendations are displayed.
- Match percentages and the reasons for each career are displayed.
- The personality type, skill match and roadmap are displayed.
- Career information is displayed.
- Job-market information is displayed where available.
- The user can start another assessment.

**Status:** Passed

### 14.4 Score Calculation Verification

The scoring components were checked against the final compatibility score.

The weighted components are:

- Field of Study: 25%
- Career Interest: 20%
- Education: 15%
- Academic Performance: 15%
- Skills: 15%
- Description match (NLP): 10%

The component points correctly sum to the knowledge-based score, which is then blended with the machine learning score and the personality match (70% / 15% / 15%).

**Status:** Passed

### 14.5 Database Expansion Testing

The database was expanded from 20 to 40 careers, then to 80 (version 2) and finally to 88 (version 3, the remaining SRS sample careers). Each expansion was applied as a migration that keeps existing accounts and reports, and was verified.

The final verification confirmed:

**Total Careers: 88**

Automated tests confirm that every career has a Holland code and a specific roadmap, and that the new careers (for example Veterinary Doctor, Chartered Accountant and Army Officer) are recommended for matching profiles.

**Status:** Passed

### 14.x Automated test suite

In addition to the manual test cases above, the project includes 36 automated tests in `tests/test_app.py`, written with Python's built-in `unittest` framework and Flask's test client. They run against a temporary copy of the database, so real accounts and reports are never changed. Run them with:

`python -m unittest discover tests -v`

| Area | What is tested |
|---|---|
| Public pages | All public pages load; protected pages require sign-in; unknown addresses return 404 |
| Security | Requests without a CSRF token are rejected; passwords are stored as hashes; repeated wrong passwords are blocked; security headers are present |
| Accounts | Sign-up requires a recovery question; changing the password; resetting a forgotten password with the security question (wrong answer rejected, answer not case-sensitive) |
| Assessment | Matric with age 70 is rejected; more than 8 skills is rejected; field must match education level; BS student receives a saved report with roadmap and job links; Matric student receives a roadmap; students cannot open each other's reports; live preview |
| Admin | Students cannot open the admin panel; the administrator sign-in refuses students; admin pages load and a career can be added |
| AI components | NLP detects interests and skills; the roadmap for a Matric student aiming to become a doctor contains FSc Pre-Medical, MDCAT and MBBS and estimates 8 years |
| SRS requirements | The personality quiz is required on submit; personality matching uses cosine similarity and ranks a Social/Investigative student closer to Nurse than Civil Engineer; the report shows the personality type, skill match and skill levels; a higher skill level gives a higher skill match; sessions expire after 30 minutes; passwords use PBKDF2-SHA256; a returning student's form is pre-filled; foreign keys are enforced |
| Career database | At least 88 careers including the 8 SRS sample careers; every career has a Holland code; the career details page shows the required subjects; every career has a specific roadmap at every education level; new careers (Veterinary Doctor, Chartered Accountant, Army Officer) are recommended for matching profiles; seeding runs only once |

All 36 tests pass.

## 15. Limitations

Although the AI-Based Career Counselling System provides automated career recommendations, the current version has some limitations.

### 15.1 Limited Career Database

The current database contains 88 career options. Although these careers cover the major fields, the database does not represent every possible profession; administrators can add more careers from the admin panel.

### 15.2 Machine Learning Trained on Synthetic Data

The recommendation engine combines weighted knowledge-based scoring with a trained machine learning model (Random Forest, selected by 10-fold cross-validation) and a personality match. Because no public dataset of Pakistani student profiles and career outcomes exists, the model is trained on synthetic profiles generated from the career database. Its 92.7% accuracy therefore measures how well it learns the career requirements, not real-world career success.

### 15.3 Dependence on Database Information

The quality of recommendations depends on the accuracy and completeness of the career information stored in the database.

### 15.4 Job Market Availability

Live job-market information is available only when the external job-market service responds successfully and supports the requested career.

### 15.5 Internet Dependency for Live Market Data

The core career recommendation functionality uses the local database, while live job-market information requires an internet connection and a working external API configuration.

### 15.6 No Professional Human Counsellor

The system provides automated guidance and should not be considered a complete replacement for professional human career counselling.

### 15.7 Limited Personalization

The current version provides recommendations using the information collected through the assessment form. More advanced personalization could be achieved by incorporating additional behavioral, psychometric, academic, and career-history data.

## 16. Future Enhancements

The system can be further improved in future versions.

### 16.1 Training on Real Student Data

The machine learning module is currently trained on synthetic profiles. Data collected from real students (through the feedback module or surveys) could replace or extend it, giving a measure of real-world accuracy.

### 16.2 Larger Career Database

The system could be expanded with hundreds of careers from additional academic and professional fields.

### 16.3 Improved Psychometric Assessment

A more comprehensive psychometric assessment could be integrated to evaluate personality, aptitude, values, and behavioral characteristics.

### 16.4 Pakistan-Focused Job Market Integration

The job-market module could be extended to provide career opportunities specifically focused on Pakistan and other user-selected countries.

### 16.5 Hiding Weak Matches

When few careers are open at a student's level (for example a Commerce student at Intermediate level), weak matches can appear in the top five. A future version could hide matches below a threshold and suggest degree-level careers as next steps instead.

### 16.6 Comparing Assessments Over Time

User accounts and assessment history are implemented. A future version could show how a student's recommendations change between assessments as their marks and skills improve.

### 16.7 University and Scholarship Recommendations

The roadmap already shows the Intermediate group, entry test and degree for each career. A future version could also recommend specific universities, admission dates and scholarships for each step.

### 16.8 Mobile Application

A mobile version could be developed for Android and iOS devices to make the career counselling system more accessible.

### 16.9 Multilingual Support

The system could support multiple languages to make career counselling accessible to a wider range of users.

## 17. Accounts, Smart Form, NLP and Live Matches

### A. Sign Up and Sign In
Users create an account with name, email, age, gender and password. Passwords are stored as salted hashes (Werkzeug). The assessment, history and profile pages require sign-in. Age and gender are stored once in the profile, so the assessment form does not ask for them again. Each completed assessment is saved in the `Assessments` table and shown on the History page.

### B. Education-Aware Form
- The **field of study** is a dropdown that depends on the selected education level (Matric/O Level: school groups; Intermediate/A Level: FSc, ICS, I.Com, FA; BS/MS: university fields). The server rejects a mismatching combination.
- The form collects **Matric/O Level %**, **Intermediate/A Level %** (for Intermediate and above) and the **current degree score** (BS/MS, CGPA or percentage).
- The overall academic score is a weighted combination, with the current level counting most: Matric only = 100% Matric; Intermediate = 60% Intermediate + 40% Matric; BS/MS = 50% degree + 30% Intermediate + 20% Matric.

### C. Validation and Eligibility
- Age is checked against the education level (for example, Matric with age 70 is rejected).
- At most 8 skills can be selected (see Chapter 24).
- Careers whose education requirement is not met are not recommended as matches. If none are eligible, the user sees a **Next Step** page showing the careers they are working towards and the qualification each one needs.

### D. NLP Module (`Database/nlp_engine.py`)
The optional free-text description ("Describe what you enjoy") is processed in three steps:
1. **Pre-processing:** lower-casing, tokenisation, stop-word removal and stemming.
2. **Extraction:** a stemmed keyword/phrase lexicon detects interests and skills mentioned in the text. Detected skills (at most 5) are added to the skills used for scoring, and the interface warns when the text suggests a different interest from the one selected.
3. **TF-IDF similarity:** the text is compared with every career (name, description, required skills, interest, future scope) using TF-IDF vectors and cosine similarity. This similarity is the 10% *Description Match* component of the final score. When no text is entered, profile similarity is used instead.

### E. Live Career Matches
While the user fills the form, the browser sends the current values to `/api/preview` (JSON, debounced) and the top matches, the combined academic score and the NLP findings are updated instantly without reloading the page.

## 18. Machine Learning Module (`Database/ml_model.py`)

### Purpose
The recommendation engine is hybrid. Knowledge-based scoring and NLP are combined with a supervised machine learning classifier, so that recommendations are also learned from labelled data rather than produced by rules alone.

### Dataset
No public dataset of Pakistani student profiles and career outcomes is available, so a labelled training set is generated from the career database:

- 5,280 student profiles (60 per career, 88 careers).
- Each profile starts from a career's real requirements and adds random variation: about 15% have a different field, about 20% a different interest, marks are drawn around (and above) the career's minimum percentage, and each profile has a random subset of the required skills plus up to two unrelated skills.
- The dataset is saved to `Database/ml/training_dataset.csv`.

### Feature vector (175 features)
Education level (ordinal, normalised), overall academic percentage (normalised), field of study (one-hot), career interest (one-hot) and skills (multi-hot over all skills in the database).

### Models compared
Random Forest (200 trees), K-Nearest Neighbours (k = 7, standardised features, Euclidean distance), Decision Tree and Support Vector Machine (RBF kernel, C = 10). Each model is evaluated with stratified 10-fold cross-validation. Precision, recall and F1 are macro-averaged across the 88 careers.

| Model | Accuracy | Precision | Recall | F1 score |
|---|---|---|---|---|
| Random Forest (selected) | 92.7% ± 0.8 | 0.936 | 0.927 | 0.926 |
| Support Vector Machine | 92.4% ± 1.2 | 0.934 | 0.924 | 0.923 |
| K-Nearest Neighbours | 87.1% ± 1.2 | 0.889 | 0.871 | 0.868 |
| Decision Tree | 78.5% ± 1.8 | 0.810 | 0.785 | 0.784 |

The model with the highest F1 score (currently **Random Forest**) is selected automatically and trained on the full dataset when the application starts. Random Forest and Support Vector Machine are very close; whichever wins the cross-validation is used. When Support Vector Machine is selected, its probabilities are calibrated so they can be used as confidence values.

### Limitation
Because the data is synthetic, these scores measure how well each model learns the profile-to-career mapping encoded in the career database, not real-world career success. The feedback module (below) collects real user ratings so that the system can be evaluated, and the model retrained, on real data.

### Use in the final score
Final score = 70% (knowledge-based score including the 10% NLP description match) + 15% (ML score) + 15% (personality match, Chapter 26). Without quiz answers (live preview) it is 80% + 20%. The ML score is the model's probability for a career relative to its top prediction. When the model ranks a career highly, the explanation says so.

Run `python train_model.py` to regenerate the dataset and the comparison table.

## 19. Skill-Gap Analysis
Each recommended career shows two lists: the required skills the student already has and the skills still to develop, next to the learning resources stored in the database.

## 20. User Feedback Module
After each assessment the student can rate the recommendations as helpful or not, with an optional comment. Responses are stored in the `Feedback` table (one per assessment, linked to the account). The **AI Model** page reports the number of assessments, the number of feedback responses and the percentage that found the results helpful.

## 21. Downloadable Report
The results page has a **Download PDF report** button. It uses a print layout that hides navigation and interactive elements and adds the generation date, so the browser's "Save as PDF" produces a clean report.

## 22. Public Website, Career Report and Live Job Links

### Public landing page
Visitors who are not signed in see a public website: hero section, statistics taken from the database (careers, interest areas, education levels, ML models compared), features, a four-step "how it works" section, education levels, career areas generated from the `Careers` table, FAQ (including privacy), and a footer. Signed-in users go straight to the assessment page.

### Career report (results page)
The results page is presented as a personal career report: the best match with a match-score ring, salary, future scope and education check; then every recommended career with its reasons (most specific first, such as the ML model and the student's own description), a skill-gap view, salary, future scope and learning resources. The report can be downloaded as a PDF.

### Live jobs and courses
Each recommended career links to live job searches in Pakistan on Rozee.pk, LinkedIn and Indeed Pakistan, and to course searches on Coursera and YouTube. Because these open the sites' own current search results, the listings are always up to date and no API key is needed. If Adzuna API keys are configured, a few live openings are also shown inside the report.

## 23. Saved Reports, Account Settings, Admin Panel and Security

### Saved reports
When a student submits the assessment, the complete report (recommendations, reasons, skill gaps, profile and date) is saved as a snapshot in `Assessments.results_json`, and the browser is redirected to a permanent address, `/report/<id>`. This follows the Post/Redirect/Get pattern, so refreshing the page does not resubmit the form. The History page lists every report; each one can be reopened exactly as it was generated, even if the career database changes later. Students can open only their own reports; admins can open any report.

### Account settings
The profile page lets students update their name, age and gender and change their password (current password required, at least 8 characters, must differ from the old one).

### Admin panel
Accounts have an `is_admin` flag. The first admin is created with `python create_admin.py` (no default password is stored in the code). Admins are taken to the panel after signing in and see an Admin link in the navigation. Students who open an admin address receive a 403 page.

| Page | Purpose |
|---|---|
| Dashboard | Number of students, assessments (and in the last 7 days), careers, and the share of feedback rated helpful; most recommended careers; assessments by education level; recent assessments with links to each report; the ML model in use with a **Retrain AI model** button |
| Careers | Search, add, edit and delete careers, including required education, field, main and related interests, minimum percentage, skills, description, salary, future scope and learning resources. Input is validated (required fields, 0–100 percentage, unique name). Changes are used by the recommendation engine immediately |
| Users | Every account with age, join date, number of assessments and last activity; grant or remove admin rights (an admin cannot remove their own) |
| Feedback | Every feedback response with the student, top match, rating, comment and a link to the report |

Retraining regenerates the training dataset from the current careers, repeats the 10-fold comparison of the four models and selects the best one.

### Security measures

| Threat | Measure |
|---|---|
| Stolen passwords | Passwords and security answers are stored as salted hashes (Werkzeug); reset tokens are stored as SHA-256 hashes, expire after one hour and work once |
| Cross-site request forgery (CSRF) | Every form and AJAX request carries a per-session random token, checked on every POST request |
| Password guessing | After 5 failed sign-in attempts (or 5 wrong security answers) for the same email and IP address within 10 minutes, further attempts are blocked |
| Session theft | The session cookie is HttpOnly and SameSite=Lax; the session is cleared and recreated at sign-in |
| Hard-coded secret | The secret key comes from the `SECRET_KEY` environment variable or a random key generated on first run and stored outside the code (`instance/secret_key`) |
| SQL injection | All database queries use parameterised statements |
| Cross-site scripting | Jinja2 escapes all output automatically; the live preview builds the page with `textContent` |
| Clickjacking and content sniffing | `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff` and a strict referrer policy on every response |
| Access to other users' data | Reports and feedback are checked against the signed-in account; admin pages require the admin flag |

## 24. Career Roadmaps, Skill Limit, Password Recovery and Interface Improvements

### Career roadmap (`Database/roadmap.py`)
Every recommended career, and every future career shown to Matric and O Level students, includes a step-by-step roadmap from the student's current level to the first job:

1. **You are here:** current education level and field.
2. **Intermediate group** (Matric / O Level students only), for example FSc Pre-Medical for Doctor or ICS for Software Engineer, with a warning if the student's Matric group is not the usual route.
3. **Entry test**, for example MDCAT for MBBS and BDS, ECAT or NUST NET for engineering, HEC's LAT for LLB.
4. **Degree** and its duration, for example MBBS (5 years), Pharm-D (5 years), 5-year LLB, BS (4 years).
5. **Postgraduate study** when the career requires it (MS, MPhil, MBA).
6. **Licence or professional step**, for example house job and PMDC registration, PEC registration, Bar Council enrolment, CA / ACCA, B.Ed, or the CSS exam stages.
7. **Skills to build**, taken from the student's skill gap for that career.
8. **First job** and **career growth**.

The current step is highlighted as "Your next step", completed steps are ticked, and the roadmap estimates the years remaining to the first job. Each career belongs to a *track* (MBBS, BDS, Pharm-D, engineering, computing, accounting, law, CSS, and others). Careers added later by an admin fall back to a track chosen from their field of study, so every career always has a roadmap. Because admission rules, minimum marks and age limits change each year, the roadmap tells students to confirm them with the university or official body.

### Skill selection limit
Students can choose at most **8 skills**. The counter shows "n / 8 selected"; when the limit is reached, the remaining skills are locked and a message explains why. Suggested skills for the chosen interest appear first; other skills are collapsed and can be searched. The server enforces the same limit. Selecting every skill used to make every career look like a match; the limit keeps results meaningful.

### Password recovery
- **Security question (self-service):** at sign-up each student chooses a security question and answer. The answer is stored as a salted hash and compared without regard to case or extra spaces. On the "Forgot password?" page the student enters their email, answers the question and sets a new password. Wrong answers are rate-limited (5 attempts per 10 minutes).
- **Administrator reset link:** for students who cannot answer, an admin can create a one-time reset link from the Users page. Only a SHA-256 hash of the token is stored; the link expires after one hour and stops working once used.
- Students with older accounts can add a recovery question in Account settings.

### Navigation and administrator access
- Sign-in, sign-up and recovery pages have a **Back** button and a **Close (×)** button; pressing Escape also returns to the home page.
- A signed-in user has an **account menu** (initials avatar) with New assessment, My reports, Account settings, How the AI works and Sign out.
- Administrators see a distinct **Admin panel** button. A separate **Administrator sign-in** page (`/admin/login`, linked in the footer) accepts administrator accounts only; student accounts are refused without being signed in.

### Visual design
Cards use layered depth shadows; feature cards, the hero report and dashboard figures tilt slightly in 3D towards the mouse; primary buttons are raised and press down when clicked; the landing hero shows a perspective stack of report cards over a 3D grid. Motion is disabled automatically for users who have reduced motion turned on in their device settings, and on touch screens.

## 25. Career Database Version 2: 40 New Careers

The career database was expanded from 40 to **80 careers**. The new careers are stored in `Database/careers_data.py` and are added automatically the first time the application starts with an older database, so existing accounts, assessments and feedback are kept. A version number in a `Meta` table records that this has run, so a career that an administrator deletes later is not added back.

| Area | New careers |
|---|---|
| Health and allied health | Nurse, Physiotherapist, Medical Lab Technologist, Radiologic Technologist, Nutritionist, Veterinary Doctor, Public Health Specialist |
| Sciences and agriculture | Biotechnologist, Microbiologist, Chemist, Physicist, Geologist, Statistician, Actuary, Agriculture Officer |
| Computing | Full Stack Developer, Software QA Engineer, Data Engineer, Product Manager |
| Engineering and architecture | Aerospace Engineer, Mechatronics Engineer, Petroleum Engineer, Textile Engineer, Telecom Engineer, Architect, Urban Planner |
| Business and finance | Chartered Accountant, Banking Officer, Business Analyst, Digital Marketing Specialist, Supply Chain Manager, Hotel Manager |
| Public service, defence and law | Army Officer, Commercial Pilot, Civil Judge, Social Worker |
| Design, media and hospitality | Fashion Designer, Interior Designer, Video Editor, Chef |

### New field of study: Natural Sciences
BS and MS students can now choose **Natural Sciences (Maths, Physics, Chemistry, Biology, Statistics)** as their field. Previously these students had no matching field option.

### New roadmap tracks
Seventeen roadmap tracks were added, each describing the real route in Pakistan, for example:

| Career | Route in the roadmap |
|---|---|
| Nurse | FSc Pre-Medical, entry test, BSN (4 years), registration with the Pakistan Nursing and Midwifery Council (PNMC) |
| Physiotherapist | FSc Pre-Medical, DPT (5 years), registration with the Allied Health Professionals Council (AHPC) |
| Medical Lab / Radiologic Technologist, Nutritionist | FSc Pre-Medical, BS in the specialty (4 years), AHPC registration |
| Veterinary Doctor | FSc Pre-Medical, DVM (5 years), registration with the Pakistan Veterinary Medical Council (PVMC) |
| Architect | FSc Pre-Engineering, B.Arch (5 years, PCATP-accredited), PCATP registration |
| Chartered Accountant | Any Intermediate group, CA through ICAP (PRC, CAF, CFAP, final case study) with a training contract of about 2.5 to 4 years |
| Army Officer | FA/FSc (PMA Long Course has required at least 60%), initial tests and ISSB, two years at the Pakistan Military Academy, commission |
| Commercial Pilot | FSc Pre-Engineering, flying school entry test and Class 1 medical, CPL training, airline type rating |
| Civil Judge | 5-year LLB via LAT, practice as an advocate, Civil Judge competitive exam |

Roadmaps show non-degree stages as "Training" or "Qualification" (for example the PMA Long Course or the CA qualification). Admission rules, minimum marks and age limits change from year to year, so the roadmaps point students to the official body.

### Skills and NLP
- The skill picker now lists every skill required by any career, read from the database, so the skills of new careers (and of careers added later by an administrator) can be selected.
- The NLP engine recognises new interest and skill words, for example *animals*, *nursing*, *army*, *fly planes*, *fashion*, *cooking*, *audit* and *tax*.

### Model retrained
The machine learning models were retrained on 4,800 profiles for 80 careers (165 features). The selected model at that point was Support Vector Machine with 93.3% accuracy and an F1 score of 0.932. (After the 8 SRS careers were added in version 3, the models were retrained again; see Chapter 18 for the current results.)

Salaries for the new careers are indicative monthly ranges for Pakistan and vary by city, employer and experience.

## 26. Alignment with the Software Requirements Specification (SRS)

This chapter compares the final system with the SRS submitted to the department. It lists the features added to meet the SRS, then gives a traceability table for every requirement, and explains each place where the implementation differs from the SRS and why.

### 26.1 Features added to meet the SRS

**Holland (RIASEC) personality quiz (FR5).** The assessment page has a fourth section with 15 statements, two or three for each Holland type (Realistic, Investigative, Artistic, Social, Enterprising, Conventional), based on SRS Appendix 9.3. Each is answered on a 5-point scale from "Strongly disagree" to "Strongly agree". All 15 are required; the browser and the server both check this. Each type's score is the average of its answers, scaled to 0–100%.

**Cosine-similarity personality matching (FR7).** Every career has a Holland code (for example Doctor `IS`, Civil Engineer `RC`, Graphic Designer `AR`). The code is turned into a six-number profile: weight 1.0 for the first letter, 0.7 for the second, 0.4 for the third, and 0.1 for the others. The student's profile and every career profile are mean-centred, then compared with `sklearn.metrics.pairwise.cosine_similarity`. Mean-centring compares the *shape* of the profile, so a student who answers everything "Agree" does not get a falsely high match. The result (−1 to 1) is converted to a 0–100% personality match: `(similarity + 1) / 2 × 100`. A student whose answers are all identical gets a neutral 50% for every career. Code: `Database/personality.py`.

The final score is now:

**Final score = 70% × knowledge-based score + 15% × machine learning score + 15% × personality match**

The live preview, shown before the quiz is answered, uses 80% knowledge-based and 20% machine learning. A personality match of 75% or more is given as a reason in the report ("Your personality type (Social and Investigative) suits this career").

**Skill proficiency self-assessment (FR6).** After choosing skills, the student rates each one from 1 to 5 (Beginner, Basic, Intermediate, Advanced, Expert). A required skill now counts `level ÷ 5` instead of counting fully, so "Python, Expert" is worth more than "Python, Beginner".

**Skill match percentage and skill gap (FR10).** Each recommended career shows a skill-match bar (0–100%) and three groups of skills: skills the student has (level 3 or more), skills still developing (level 1–2) and skills to learn. Developing and missing skills are both added to the roadmap.

**Career details page (FR9, UC-07).** Every career has a page at `/career/<id>` with its description, salary, future scope, minimum education, the **required subjects** (Intermediate group, entry test, degree and licence), the Holland personality type, required skills, learning and job links, and a full roadmap from Matric. It is linked from every recommendation ("View details") and from the career areas on the home page.

**The 8 remaining SRS sample careers (DB-06).** Entrepreneur, Business Consultant, IT Project Manager, Photographer, Art Director, Music Producer, Industrial Engineer and Radiologist were added (version 3 of the career data), each with a specific roadmap. Together with the earlier careers, all 40 sample careers in SRS Appendix 9.2 are now covered, in a database of 88 careers. A few use the name common in Pakistan: Software Engineer (Software Developer), Cloud Engineer (Cloud Architect), Physiotherapist (Physical Therapist), Medical Lab Technologist (Lab Technician), Public Health Specialist (Public Health Officer), Human Resources Manager (HR Specialist) and Cyber Security Analyst (Cybersecurity Analyst).

**30-minute session timeout (SEC).** `PERMANENT_SESSION_LIFETIME` is 30 minutes. Each request from a signed-in user renews the session, so the student is signed out after 30 minutes of inactivity.

**PBKDF2 password hashing (SEC-01).** New passwords and security answers are hashed with PBKDF2-SHA256, 600,000 iterations (`werkzeug.security`), which the SRS lists as an accepted method. Existing hashes keep working, because the method is stored inside each hash.

**Updating the profile (FR3).** When a student returns, the assessment form is pre-filled from their latest assessment: education, field, results, degree score, interest, description, skills, skill levels and quiz answers. A note says so, the live matches appear straight away, and the student changes only what is different.

**Enforced foreign keys (DB-04).** SQLite does not enforce foreign keys unless asked. Every database connection now runs `PRAGMA foreign_keys = ON`.

**Indexes (DB-08).** Indexes on `Assessments(account_id)`, `Feedback(account_id)`, `CareerInterests(career_id)` and `Accounts(reset_token)` speed up the history page, the admin panel and password reset.

**Documentation (DOC).** `Documentation/User_Manual.md` (for students) and `Documentation/Admin_Guide.md` (for administrators) were added.

### 26.2 Functional requirements traceability

| ID | Requirement | Status | Where |
|---|---|---|---|
| FR1 | Register with email and password | Implemented | `/signup`, with recovery question |
| FR2 | Log in | Implemented | `/login`, rate-limited |
| FR3 | Update education, skills and interests | Implemented | The assessment form is pre-filled with the student's latest education, results, interest, skills, skill levels and quiz answers; the student changes what is different and submits. Name, age and gender are edited on the Profile page |
| FR4 | Admin panel to add, edit and delete careers | Implemented | `/admin/careers` (88 careers, including the Holland code) |
| FR5 | 15-question Holland quiz | Implemented | Assessment section 04 |
| FR6 | Skill self-assessment | Implemented | Skill levels 1–5 |
| FR7 | Cosine similarity matching | Implemented | Personality match (scikit-learn cosine similarity) and NLP description match (TF-IDF cosine similarity) |
| FR8 | Top 5 recommendations with match % | Implemented | Report page |
| FR9 | Career details: description, required subjects, salary | Implemented | `/career/<id>` |
| FR10 | Skill gap for the top career | Implemented, extended | Skill match % and the gap for every recommended career |
| FR11 | Free learning resources for missing skills | Implemented | YouTube and Coursera links, plus career-specific resources |
| FR12 | Responsive web interface | Implemented | Tested on desktop and mobile widths |
| FR13 | Store profiles, quiz answers and careers in SQLite | Implemented | Quiz answers are stored with each assessment |

### 26.3 Non-functional requirements traceability

| Requirement | Status | How |
|---|---|---|
| Response time under 3 seconds | Met | Under 0.1 s per recommendation (measured) after the model is trained at start-up |
| Passwords never stored in plain text | Met | PBKDF2-SHA256 |
| SQL injection prevention | Met | Parameterised queries everywhere |
| Session management with secure cookie | Met | HttpOnly, SameSite=Lax cookie; 30-minute timeout |
| Role-based access control | Met | `admin_required` decorator on every admin route |
| XSS prevention | Met | Jinja2 auto-escaping, plus security headers |
| CSRF protection | Met (different library) | See 26.5 |
| Secret key in environment | Met (different library) | See 26.5 |
| Assessment in 10 minutes; quiz in 5 minutes | Met | 15 one-click questions; the form remembers answers |
| Clear labels, validation, friendly errors | Met | Every field is validated in the browser and on the server |
| System does not crash on invalid input | Met | Tested, including age 70 with Matric and more than 8 skills |
| No data loss on restart | Met | SQLite; career updates are migrations that keep accounts |
| Career data editable without code changes | Met | Admin panel |
| Code and schema documented | Met | Docstrings, Chapter 13 (ERD), this document |
| Student satisfaction of 75% or more | Measured in use | The feedback module records "Yes, helpful" or "Not really" for each report; the admin panel shows the percentage |

### 26.4 Database requirements traceability

| ID | Requirement | Status |
|---|---|---|
| DB-01 | SQLite 3 | Met |
| DB-02 | 7 tables of SRS Section 7.3 | Met with a different layout; see 26.5 |
| DB-03 | Auto-increment integer primary keys | Met |
| DB-04 | Foreign keys enforced | Met (`PRAGMA foreign_keys = ON`) |
| DB-05 | Unique email | Met (`Accounts.email UNIQUE`) |
| DB-06 | 40 career records | Exceeded: 88 careers, including all 40 SRS samples |
| DB-07 | At least 100 students | Met; SQLite has no practical limit at this size |
| DB-08 | Indexes on frequently queried columns | Met |
| DB-09 | Backups by copying the .db file | Documented in the Admin Guide |
| DB-10 | Database file not in version control | `.gitignore` excludes local data (`instance/`, backups, `.env`). The career database itself is shipped, because it holds the 88 seeded careers |

### 26.5 Changes from the SRS and their justification

| SRS said | Implemented | Why |
|---|---|---|
| Bootstrap 5 | Custom CSS (`static/css`) | The supervisor asked for a more professional appearance. Custom styles gave full control over the 3D cards, report and roadmap layouts. The page needs no CDN, so it also works offline during the demonstration (SRS dependency D-: "Bootstrap CDN must be accessible" no longer applies) |
| Flask-WTF for CSRF | Built-in CSRF tokens | Same protection: a random token per session, checked on every POST, including AJAX requests (`X-CSRF-Token` header). It avoids an extra dependency and is covered by an automated test |
| python-dotenv for the secret key | `SECRET_KEY` environment variable, or a random key saved in `instance/secret_key` | Same goal (no secret in the code). It works without the student creating a `.env` file |
| bcrypt | PBKDF2-SHA256 (Werkzeug) | The SRS allows "bcrypt or werkzeug.security generate_password_hash" |
| Tables `users`, `student_profiles`, `quiz_results`, `careers` (with 6 Holland scores), `skills`, `student_skills`, `career_skills` | `Accounts`, `Assessments`, `Careers` (with `holland_code`), `Interests`, `CareerInterests`, `Feedback`, `Meta` | Same information, organised for how the system works: the student's profile is in `Accounts`; each assessment keeps its own inputs, quiz answers, skill levels and results as JSON, so old reports always reopen exactly as they were; required skills are a list on each career, editable in one field in the admin panel. One Holland code per career (for example `IS`) replaces six separate scores, and is converted to six numbers for cosine similarity |
| Cosine similarity as the whole matching method | Hybrid: knowledge-based scoring, personality cosine similarity, NLP (TF-IDF cosine similarity) and a machine learning classifier | Cosine similarity alone ignores eligibility. A hybrid engine lets the system refuse a career the student cannot enter yet (the supervisor's Matric, age 70 case) and explain every recommendation |
| Appendix 9.3 lists 17 quiz statements (three Artistic, three Enterprising, and two Conventional "distributed within 15") | 15 statements: three each for Realistic, Investigative and Social, two each for Artistic, Enterprising and Conventional | Keeps the quiz at the 15 questions required by FR5 while giving every Holland type at least two statements, so no type is decided by a single answer |
| 40 careers | 88 careers | More coverage of Pakistani careers (health, defence, aviation, CA, CSS) |
| Out of scope: real-time job feeds | Links to live searches on Rozee.pk, LinkedIn and Indeed; optional live openings with an Adzuna key | Added because the supervisor asked for the system to work on "real-time" data |
| Out of scope: email password reset | Security question, or a reset link from the administrator | Still no email is sent, as in the SRS; recovery works without a mail server |
| Not in SRS | Career roadmaps, PDF report, saved history, live preview, feedback, model retraining | Added after the supervisor's review to make the system practical |

## 27. Comparison with Related Systems

| Feature | Kumari et al. (IJIREM 2025) | Reddy et al. (Alliance University) | This project |
|---|---|---|---|
| Core technique | Random Forest, SVM, Decision Tree | KNN + Gemini LLM | Knowledge-based scoring + NLP + best of four ML classifiers |
| Model evaluation | Accuracy, precision, recall, F1, 10-fold CV | Not reported | Accuracy, precision, recall, F1, 10-fold CV, plus user feedback |
| NLP | Future work | Through an external LLM API | Built in (tokenisation, stemming, TF-IDF, cosine similarity), works offline |
| Education eligibility and next-step pathway | No | No | Yes |
| Live recommendations while filling the form | No | No | Yes |
| Explanation of each recommendation | Confidence score | AI-generated insights | Reasons for every career |
| Skill-gap analysis | Recommended skills | Yes | Yes |
| Sign-up / sign-in and history | In flowchart | Yes | Yes |
| Feedback collection | Future work | Yes | Yes |
| Local education system (Matric, FSc, O/A Level) | No | No | Yes |
| Resume / cover letter generation | No | Yes (LLM) | No (future work) |

## 28. Conclusion

The AI-Based Career Counselling System provides a web-based solution for helping users identify suitable career options according to their educational background, academic performance, interests, skills, and the student's own description.

The system combines a Flask web application, an SQLite database and a hybrid AI engine: knowledge-based scoring, a Holland (RIASEC) personality quiz matched with cosine similarity, natural language processing of the student's own description, and a machine learning classifier selected from four models by 10-fold cross-validation. Careers the student is not yet eligible for are shown as a next-step pathway instead of a false match.

The system currently contains 88 career options covering health and allied health, sciences, computer science, engineering, business and finance, arts and design, education, law, defence, aviation, hospitality and public service.

The final results provide ranked career recommendations together with plain-language explanations, a skill-gap analysis, career information, required skills, future scope, salary information, learning resources, and available live job-market information.

Overall, the project demonstrates how an automated and explainable AI-based approach can be used to provide structured career guidance through a simple web-based system.