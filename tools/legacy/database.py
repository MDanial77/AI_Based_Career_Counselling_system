import sqlite3

def get_connection():
    connection = sqlite3.connect("Database/career_counseling.db")
    connection.row_factory = sqlite3.Row
    return connection


