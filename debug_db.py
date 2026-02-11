import sqlite3
import json

DB_NAME = "users.db"

def check_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    print("--- COURSES ---")
    cursor.execute("SELECT id, user_email, topic FROM courses")
    courses = cursor.fetchall()
    for c in courses:
        print(f"ID: {c[0]}, User: {c[1]}, Topic: {c[2]}")
        
    print("\n--- COURSE PROGRESS ---")
    cursor.execute("SELECT user_email, course_id, current_week, current_day FROM course_progress")
    progress = cursor.fetchall()
    for p in progress:
        print(f"User: {p[0]}, CourseID: {p[1]}, Week: {p[2]}, Day: {p[3]}")
        
    print("\n--- JOINED RESULTS (What API sees) ---")
    cursor.execute("""
        SELECT c.id, c.topic, p.current_week 
        FROM courses c 
        JOIN course_progress p ON c.id = p.course_id 
    """)
    joined = cursor.fetchall()
    for j in joined:
        print(f"ID: {j[0]}, Topic: {j[1]}, Week: {j[2]}")

    conn.close()

if __name__ == "__main__":
    try:
        check_db()
    except Exception as e:
        print(f"Error: {e}")
