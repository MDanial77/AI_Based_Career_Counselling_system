import sqlite3
import os

# =========================================================
# DATABASE PATH
# =========================================================

db_path = os.path.join(
    os.path.dirname(__file__),
    "career_counseling.db"
)

# =========================================================
# CONNECT TO DATABASE
# =========================================================

connection = sqlite3.connect(db_path)
connection.row_factory = sqlite3.Row
cursor = connection.cursor()

# =========================================================
# SHOW DATABASE PATH
# =========================================================

print("\n===== DATABASE =====")
print(db_path)

# =========================================================
# SHOW TABLES
# =========================================================

print("\n===== TABLES =====\n")

cursor.execute("""
    SELECT name
    FROM sqlite_master
    WHERE type='table'
    ORDER BY name
""")

tables = cursor.fetchall()

if not tables:
    print("No tables found in this database.")

else:
    for table in tables:
        print(table["name"])

# =========================================================
# CHECK CAREERS TABLE
# =========================================================

cursor.execute("""
    SELECT name
    FROM sqlite_master
    WHERE type='table'
    AND name='Careers'
""")

careers_table = cursor.fetchone()

if careers_table is None:

    print("\nERROR: Careers table does not exist.")
    print("The database file is not the correct/complete database.")

else:

    # =====================================================
    # CAREERS
    # =====================================================

    cursor.execute("SELECT * FROM Careers")

    careers = cursor.fetchall()

    print("\n===== CAREER DATABASE =====\n")

    for career in careers:

        print(f"ID: {career['id']}")
        print(f"Career Name: {career['career_name']}")

        if "category" in career.keys():
            print(f"Category: {career['category']}")

        if "description" in career.keys():
            print(f"Description: {career['description']}")

        if "required_skills" in career.keys():
            print(f"Required Skills: {career['required_skills']}")

        if "education_required" in career.keys():
            print(f"Education Required: {career['education_required']}")

        if "field_required" in career.keys():
            print(f"Field Required: {career['field_required']}")

        if "minimum_percentage" in career.keys():
            print(
                f"Minimum Percentage: "
                f"{career['minimum_percentage']}"
            )

        if "interest" in career.keys():
            print(f"Interest: {career['interest']}")

        if "future_scope" in career.keys():
            print(f"Future Scope: {career['future_scope']}")

        if "average_salary" in career.keys():
            print(f"Average Salary: {career['average_salary']}")

        if "learning_resources" in career.keys():
            print(
                f"Learning Resources: "
                f"{career['learning_resources']}"
            )

        print("-" * 60)

# =========================================================
# CLOSE DATABASE
# =========================================================

connection.close()

print("\nDatabase check completed successfully.")