import sqlite3

connection = sqlite3.connect("career_counseling.db")
cursor = connection.cursor()

cursor.execute("SELECT * FROM Skills")

skills = cursor.fetchall()

print("===== Skills =====\n")

for skill in skills:
    print(f"{skill[0]}. {skill[1]}")

connection.close()