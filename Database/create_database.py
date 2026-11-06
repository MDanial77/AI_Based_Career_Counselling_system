import sqlite3
import os

# ==========================================================
# DATABASE PATH
# ==========================================================

import sys

db_path = os.path.join(os.path.dirname(__file__), "career_counseling.db")

# Safety guard: this script deletes and recreates the career tables.
# Refuse to run on a database that already has user accounts unless
# the user explicitly passes --force.
def build(db_path=db_path, verbose=True):
    """Create the career tables (Users, Careers, Interests, CareerInterests) with the
    original 40 careers. The application adds the newer careers (version 2 and 3,
    88 in total) and the Holland codes automatically the next time it starts."""
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    cursor.execute("PRAGMA foreign_keys = ON")

    # ==========================================================
    # DELETE OLD TABLES
    # ==========================================================

    cursor.execute("DROP TABLE IF EXISTS CareerInterests")
    cursor.execute("DROP TABLE IF EXISTS Interests")
    cursor.execute("DROP TABLE IF EXISTS Careers")
    cursor.execute("DROP TABLE IF EXISTS Users")

    # ==========================================================
    # USERS TABLE
    # ==========================================================

    cursor.execute("""
    CREATE TABLE Users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        age INTEGER,
        gender TEXT,
        education_level TEXT,
        field_of_study TEXT,
        percentage REAL,
        cgpa REAL
    )
    """)

    # ==========================================================
    # CAREERS TABLE
    # ==========================================================

    cursor.execute("""
    CREATE TABLE Careers(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        career_name TEXT,
        education_required TEXT,
        field_required TEXT,
        minimum_percentage REAL,
        interest TEXT,
        description TEXT,
        required_skills TEXT,
        future_scope TEXT,
        average_salary TEXT,
        learning_resources TEXT
    )
    """)

    # ==========================================================
    # INTERESTS TABLE
    # ==========================================================

    cursor.execute("""
    CREATE TABLE Interests(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        interest_name TEXT UNIQUE
    )
    """)

    # ==========================================================
    # CAREER INTERESTS TABLE
    # ==========================================================

    cursor.execute("""
    CREATE TABLE CareerInterests(
        career_id INTEGER,
        interest_id INTEGER,
        FOREIGN KEY(career_id) REFERENCES Careers(id),
        FOREIGN KEY(interest_id) REFERENCES Interests(id)
    )
    """)

    # ==========================================================
    # CAREER DATA
    # ==========================================================

    careers = [
        ("Software Engineer", "BS", "Computer Science", 60, "Programming",
         "Develops software applications.", "Python, C++, Problem Solving",
         "Excellent", "PKR 120,000/month", "CS50, freeCodeCamp, Python.org"),

        ("AI Engineer", "BS", "Computer Science", 70, "Programming",
         "Builds AI systems.", "Python, Machine Learning, Deep Learning",
         "Excellent", "PKR 180,000/month", "Coursera AI, Kaggle, TensorFlow"),

        ("Data Scientist", "BS", "Computer Science", 65, "Mathematics",
         "Analyzes data.", "Python, SQL, Statistics, Power BI",
         "Very High", "PKR 180,000 - 400,000/month",
         "Kaggle, Coursera, DataCamp"),

        ("Web Developer", "BS", "Computer Science", 55, "Programming",
         "Builds websites.", "HTML, CSS, JavaScript, Flask",
         "High", "PKR 120,000 - 250,000/month",
         "freeCodeCamp, MDN, W3Schools"),

        ("Cyber Security Analyst", "BS", "Computer Science", 65, "Technology",
         "Protects systems.", "Networking, Linux, Ethical Hacking",
         "Excellent", "PKR 180,000 - 400,000/month",
         "TryHackMe, Hack The Box"),

        ("Doctor", "Intermediate", "Medical", 85, "Biology",
         "Treats patients.", "Biology, Patient Care, Diagnosis",
         "Excellent", "PKR 200,000+/month", "PMC, Khan Academy"),

        ("Dentist", "Intermediate", "Medical", 80, "Biology",
         "Dental specialist.", "Dental Surgery, Patient Care",
         "High", "PKR 180,000+/month", "Dental Council Resources"),

        ("Pharmacist", "Intermediate", "Medical", 75, "Chemistry",
         "Medicine expert.", "Chemistry, Pharmacology",
         "High", "PKR 120,000 - 250,000/month", "Coursera Pharmacy"),

        ("Graphic Designer", "Intermediate", "Arts", 50, "Arts",
         "Creates graphics.", "Photoshop, Illustrator, Creativity",
         "High", "PKR 80,000 - 200,000/month",
         "Adobe Learn, Behance"),

        ("Animator", "BS", "Arts", 55, "Arts",
         "Creates animation.", "Blender, Maya, Creativity",
         "High", "PKR 120,000 - 250,000/month", "Blender Guru"),

        ("Accountant", "B.Com", "Commerce", 60, "Business",
         "Financial expert.", "Accounting, Excel, Taxation",
         "High", "PKR 100,000 - 220,000/month", "ACCA, Coursera"),

        ("Bank Manager", "MBA", "Commerce", 65, "Business",
         "Manages banks.", "Finance, Leadership",
         "High", "PKR 180,000+/month", "Bank Training Programs"),

        ("Marketing Manager", "MBA", "Business", 60, "Business",
         "Marketing specialist.", "Digital Marketing, SEO",
         "Very High", "PKR 180,000+/month",
         "Google Digital Garage"),

        ("Civil Engineer", "BS", "Engineering", 65, "Mathematics",
         "Designs buildings.", "AutoCAD, Structural Design",
         "High", "PKR 150,000+/month", "Autodesk Learn"),

        ("Mechanical Engineer", "BS", "Engineering", 65, "Mathematics",
         "Designs machines.", "CAD, Thermodynamics",
         "High", "PKR 150,000+/month", "NPTEL, Coursera"),

        ("Electrical Engineer", "BS", "Engineering", 65, "Physics",
         "Electrical systems.", "Circuit Design, PLC",
         "High", "PKR 150,000+/month", "Coursera Electrical"),

        ("Teacher", "BS", "Education", 50, "Teaching",
         "School teacher.", "Communication, Teaching",
         "Moderate", "PKR 70,000 - 120,000/month",
         "Coursera Education"),

        ("Lecturer", "MS", "Education", 65, "Teaching",
         "University lecturer.", "Research, Teaching",
         "High", "PKR 120,000+/month", "Higher Education Courses"),

        ("Lawyer", "LLB", "Law", 60, "Debate",
         "Legal professional.", "Legal Writing, Advocacy",
         "High", "PKR 150,000+/month", "Pakistan Bar Council"),

        ("CSS Officer", "Bachelor", "Any", 60, "Public Service",
         "Government Officer.", "Leadership, Administration",
         "Excellent", "PKR 180,000+/month", "FPSC, CSS Academy")
             ,

        ("AI Research Scientist", "MS", "Computer Science", 70, "Programming",
         "Researches advanced artificial intelligence methods.",
         "Python, Machine Learning, Mathematics, Research",
         "Excellent", "PKR 250,000 - 600,000/month",
         "Coursera, DeepLearning.AI, arXiv"),

        ("Machine Learning Engineer", "BS", "Computer Science", 65, "Programming",
         "Develops and deploys machine learning systems.",
         "Python, Machine Learning, TensorFlow, SQL",
         "Excellent", "PKR 180,000 - 450,000/month",
         "Kaggle, Coursera, TensorFlow"),

        ("Data Analyst", "BS", "Computer Science", 60, "Mathematics",
         "Analyzes business and organizational data.",
         "Excel, SQL, Python, Power BI, Statistics",
         "Very High", "PKR 120,000 - 300,000/month",
         "Microsoft Learn, Kaggle, Coursera"),

        ("Cloud Engineer", "BS", "Computer Science", 65, "Technology",
         "Designs and manages cloud computing infrastructure.",
         "AWS, Azure, Linux, Networking",
         "Excellent", "PKR 180,000 - 400,000/month",
         "AWS Training, Microsoft Learn"),

        ("DevOps Engineer", "BS", "Computer Science", 65, "Technology",
         "Automates software development and deployment processes.",
         "Linux, Docker, Git, Kubernetes, CI/CD",
         "Excellent", "PKR 180,000 - 450,000/month",
         "Docker Docs, Kubernetes, AWS"),

        ("Mobile App Developer", "BS", "Computer Science", 60, "Programming",
         "Develops applications for Android and iOS devices.",
         "Flutter, Dart, Kotlin, Java, UI Design",
         "Very High", "PKR 120,000 - 300,000/month",
         "Flutter, Android Developers"),

        ("Network Engineer", "BS", "Computer Science", 60, "Technology",
         "Designs and maintains computer networks.",
         "Networking, Cisco, Linux, Troubleshooting",
         "High", "PKR 120,000 - 300,000/month",
         "Cisco Networking Academy"),

        ("Database Administrator", "BS", "Computer Science", 60, "Technology",
         "Manages and maintains organizational databases.",
         "SQL, MySQL, PostgreSQL, Backup, Security",
         "High", "PKR 130,000 - 320,000/month",
         "Oracle Learning, SQLBolt"),

        ("UI/UX Designer", "BS", "Computer Science", 55, "Arts",
         "Designs user interfaces and user experiences.",
         "Figma, UI Design, UX Research, Creativity",
         "Very High", "PKR 100,000 - 280,000/month",
         "Figma Learn, Google UX Course"),

        ("Game Developer", "BS", "Computer Science", 55, "Programming",
         "Creates interactive computer and mobile games.",
         "Unity, C#, Blender, Game Design",
         "High", "PKR 120,000 - 350,000/month",
         "Unity Learn, Unreal Engine"),

        ("Biomedical Engineer", "BS", "Engineering", 65, "Biology",
         "Combines engineering principles with medical technology.",
         "Biology, Electronics, Biomedical Design",
         "Excellent", "PKR 130,000 - 300,000/month",
         "Coursera, MIT OpenCourseWare"),

        ("Chemical Engineer", "BS", "Engineering", 65, "Chemistry",
         "Designs industrial chemical processes and systems.",
         "Chemistry, Process Design, Thermodynamics",
         "High", "PKR 140,000 - 320,000/month",
         "NPTEL, Coursera"),

        ("Environmental Engineer", "BS", "Engineering", 60, "Biology",
         "Develops solutions for environmental and pollution problems.",
         "Environmental Science, Chemistry, Research",
         "Very High", "PKR 120,000 - 280,000/month",
         "Coursera, EPA Resources"),

        ("Economist", "BS", "Commerce", 65, "Mathematics",
         "Studies economic trends, markets, and financial systems.",
         "Economics, Statistics, Data Analysis",
         "High", "PKR 120,000 - 300,000/month",
         "Coursera, Khan Academy"),

        ("Financial Analyst", "BS", "Commerce", 65, "Business",
         "Analyzes financial information to support business decisions.",
         "Excel, Financial Analysis, Accounting, Statistics",
         "Very High", "PKR 130,000 - 350,000/month",
         "CFI, Coursera, Microsoft Learn"),

        ("Human Resources Manager", "MS", "Business", 60, "Business",
         "Manages recruitment, employees, and organizational policies.",
         "Communication, HR Management, Leadership",
         "High", "PKR 130,000 - 300,000/month",
         "Coursera HR, SHRM"),

        ("Content Writer", "BS", "Arts", 50, "Arts",
         "Creates written content for digital and traditional platforms.",
         "Writing, Research, Communication, SEO",
         "High", "PKR 70,000 - 220,000/month",
         "HubSpot Academy, Coursera"),

        ("Psychologist", "MS", "Medical", 60, "Biology",
         "Provides psychological assessment and support.",
         "Psychology, Communication, Counseling",
         "Very High", "PKR 100,000 - 300,000/month",
         "Coursera, APA Resources"),

        ("Journalist", "BS", "Arts", 50, "Debate",
         "Researches and reports news and current affairs.",
         "Writing, Research, Communication, Interviewing",
         "High", "PKR 70,000 - 220,000/month",
         "Reuters Training, Coursera"),

        ("Public Administration Officer", "MS", "Public Administration", 60, "Public Service",
         "Manages public-sector programs and administrative activities.",
         "Administration, Leadership, Communication",
         "High", "PKR 120,000 - 300,000/month",
         "Coursera, Public Administration Courses")
    ]

    cursor.executemany("""
    INSERT INTO Careers(
        career_name, education_required, field_required,
        minimum_percentage, interest, description, required_skills,
        future_scope, average_salary, learning_resources
    )
    VALUES(?,?,?,?,?,?,?,?,?,?)
    """, careers)

    # ==========================================================
    # INTEREST DATA
    # ==========================================================

    interests = [
        ("Programming",),
        ("Mathematics",),
        ("Biology",),
        ("Business",),
        ("Arts",),
        ("Teaching",),
        ("Technology",),
        ("Physics",),
        ("Chemistry",),
           ("Debate",),
        ("Public Service",),
        ("Public Administration",)
    ]

    cursor.executemany(
        "INSERT INTO Interests(interest_name) VALUES(?)",
        interests
    )

    # ==========================================================
    # CAREER-INTEREST RELATIONSHIPS
    # ==========================================================

    career_interests = [
        (1, 1), (1, 2),       # Software Engineer
        (2, 1), (2, 2),       # AI Engineer
        (3, 1), (3, 2),       # Data Scientist
        (4, 1),               # Web Developer
        (5, 7),               # Cyber Security Analyst
        (6, 3),               # Doctor
        (7, 3),               # Dentist
        (8, 9), (8, 3),       # Pharmacist
        (9, 5),               # Graphic Designer
        (10, 5),              # Animator
        (11, 4), (11, 2),     # Accountant
        (12, 4),              # Bank Manager
        (13, 4),              # Marketing Manager
        (14, 2),              # Civil Engineer
        (15, 2),              # Mechanical Engineer
        (16, 8),              # Electrical Engineer
        (17, 6),              # Teacher
        (18, 6),              # Lecturer
        (19, 10),             # Lawyer
               (20, 11),              # CSS Officer

        (21, 1),               # AI Research Scientist
        (22, 1),               # Machine Learning Engineer
        (23, 2),               # Data Analyst
        (24, 7),               # Cloud Engineer
        (25, 7),               # DevOps Engineer
        (26, 1),               # Mobile App Developer
        (27, 7),               # Network Engineer
        (28, 7),               # Database Administrator
        (29, 5),               # UI/UX Designer
        (30, 1),               # Game Developer
        (31, 3),               # Biomedical Engineer
        (32, 9),               # Chemical Engineer
        (33, 3),               # Environmental Engineer
        (34, 2),               # Economist
        (35, 4),               # Financial Analyst
        (36, 4),               # Human Resources Manager
        (37, 5),               # Content Writer
        (38, 3),               # Psychologist
        (39, 10),              # Journalist
        (40, 11)               # Public Administration Officer
    ]

    cursor.executemany(
        "INSERT INTO CareerInterests(career_id, interest_id) VALUES(?, ?)",
        career_interests
    )

    # ==========================================================
    # SAVE DATABASE
    # ==========================================================

    # Make the application seed the newer careers again on its next start
    has_meta = cursor.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='Meta'").fetchone()
    if has_meta:
        cursor.execute("DELETE FROM Meta WHERE key = 'careers_seed'")
    connection.commit()
    connection.close()

    if verbose:
        print("Database created successfully.")
    if verbose:
        print(f"Database location: {db_path}")
    if verbose:
        print(f"{len(careers)} careers inserted successfully.")
    if verbose:
        print("11 interests inserted successfully.")
    if verbose:
        print("Career-interest relationships inserted successfully.")


if __name__ == "__main__":
    if os.path.exists(db_path) and "--force" not in sys.argv:
        check = sqlite3.connect(db_path)
        has_table = check.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='Accounts'"
        ).fetchone()
        has_accounts = has_table and check.execute("SELECT 1 FROM Accounts LIMIT 1").fetchone()
        check.close()
        if has_accounts:
            sys.exit(
                "This database already contains user accounts and assessments.\n"
                "Running this script would reset the career tables.\n"
                "If you really want to do this, back up the database and run:\n"
                "    python Database/create_database.py --force"
            )

    build(db_path)
    print("Start the application (python app.py) to add the remaining careers (88 in total).")
