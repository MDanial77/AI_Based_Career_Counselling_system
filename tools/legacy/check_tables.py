import sqlite3
import os

# Correct database filename
db_path = os.path.join(
    os.path.dirname(__file__),
    "career_counseling.db"
)

print("=" * 60)
print("DATABASE VERIFICATION")
print("=" * 60)

print("\nDatabase:")
print(os.path.abspath(db_path))

print("\nDatabase exists:")
print(os.path.exists(db_path))

print("\nDatabase size:")
print(os.path.getsize(db_path), "bytes")

connection = sqlite3.connect(db_path)
cursor = connection.cursor()

# ---------------------------------------------------------
# SHOW TABLES
# ---------------------------------------------------------

print("\nTables:")

tables = cursor.execute(
    "SELECT name FROM sqlite_master WHERE type='table'"
).fetchall()

for table in tables:
    print(" -", table[0])


# ---------------------------------------------------------
# CAREERS TABLE COLUMNS
# ---------------------------------------------------------

print("\nCareers Table Columns:")

try:

    columns = cursor.execute(
        "PRAGMA table_info(Careers)"
    ).fetchall()

    for column in columns:

        print(
            f" - {column[1]}"
            f" | Type: {column[2]}"
            f" | Primary Key: {column[5]}"
        )

except sqlite3.Error as error:

    print("Could not read Careers table.")
    print("Error:", error)


# ---------------------------------------------------------
# CAREER RECORDS
# ---------------------------------------------------------

print("\nCareer Records:")

try:

    careers = cursor.execute(
        "SELECT id, career_name FROM Careers"
    ).fetchall()

    for career in careers:

        print(
            f" - ID: {career[0]} | "
            f"Career: {career[1]}"
        )

    print("\nTotal Careers:", len(careers))

except sqlite3.Error as error:

    print("Could not read Careers table.")
    print("Error:", error)


connection.close()

print("\n" + "=" * 60)
print("DATABASE VERIFICATION COMPLETED")
print("=" * 60)