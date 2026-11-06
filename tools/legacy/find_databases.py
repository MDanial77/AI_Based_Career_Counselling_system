import os
import sqlite3

PROJECT_FOLDER = os.path.dirname(os.path.abspath(__file__))

print("=" * 70)
print("SEARCHING FOR ALL SQLITE DATABASE FILES")
print("=" * 70)

found = False

for root, dirs, files in os.walk(PROJECT_FOLDER):

    # Skip virtual environment
    if "venv" in root.split(os.sep):
        continue

    for filename in files:

        if filename.lower().endswith((".db", ".sqlite", ".sqlite3")):

            found = True

            path = os.path.join(root, filename)

            print("\n" + "-" * 70)
            print("Database file:")
            print(path)

            print("Size:")
            print(os.path.getsize(path), "bytes")

            try:
                connection = sqlite3.connect(path)
                cursor = connection.cursor()

                tables = cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()

                print("Tables:")

                if tables:
                    for table in tables:
                        print("  -", table[0])
                else:
                    print("  No tables found")

                if any(table[0] == "Careers" for table in tables):

                    count = cursor.execute(
                        "SELECT COUNT(*) FROM Careers"
                    ).fetchone()[0]

                    print("Careers records:", count)

                connection.close()

            except Exception as error:

                print("Could not inspect database:")
                print(error)


print("\n" + "=" * 70)

if found:
    print("DATABASE SEARCH COMPLETED")
else:
    print("NO DATABASE FILES FOUND")

print("=" * 70)