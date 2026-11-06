"""Create an admin account, or give admin rights to an existing account.

Usage:
    python create_admin.py
You will be asked for a name, email and password.
"""
import getpass
import sys
from datetime import datetime

import app as application


def main():
    print("Create an admin account for AI Career Counselling\n")
    email = input("Email: ").strip().lower()
    if not application.EMAIL_PATTERN.match(email):
        sys.exit("That is not a valid email address.")

    connection = application.get_connection()
    existing = connection.execute(
        "SELECT id, full_name FROM Accounts WHERE email = ?", (email,)
    ).fetchone()

    if existing:
        connection.execute("UPDATE Accounts SET is_admin = 1 WHERE id = ?", (existing["id"],))
        connection.commit()
        connection.close()
        print(f"\n{existing['full_name']} ({email}) is now an admin. Sign in with their usual password.")
        return

    name = input("Full name: ").strip()
    if len(name) < 2:
        sys.exit("Please enter a full name.")
    password = getpass.getpass("Password (at least 8 characters, hidden): ")
    if len(password) < 8:
        sys.exit("The password must be at least 8 characters.")
    if password != getpass.getpass("Confirm password: "):
        sys.exit("The passwords do not match.")

    connection.execute(
        "INSERT INTO Accounts (full_name, email, password_hash, created_at, is_admin) "
        "VALUES (?, ?, ?, ?, 1)",
        (name, email, application.hash_secret(password),
         datetime.now().isoformat(timespec="seconds"))
    )
    connection.commit()
    connection.close()
    print(f"\nAdmin account created for {email}. Run `python app.py` and sign in.")


if __name__ == "__main__":
    main()
