from database import get_connection

connection = get_connection()
cursor = connection.cursor()

cursor.execute("SELECT career_name FROM Careers")

careers = cursor.fetchall()

print("Careers in Database:\n")

for career in careers:
    print(career["career_name"])

connection.close()