import os
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.environ.get("DATABASE_URL")

SQLITE_DB_NAME = "users.db"

def get_db_connection():
    if DATABASE_URL:
        try:
            conn = psycopg2.connect(DATABASE_URL, sslmode='require')
            return conn
        except Exception as e:
            print(f"[DB] PostgreSQL Connection Error: {e}")
            return None
    else:
        conn = sqlite3.connect(SQLITE_DB_NAME)
        conn.row_factory = sqlite3.Row 
        return conn

def execute_query(sql, params=(), fetch_mode=None, commit=False):
    conn = get_db_connection()
    if not conn:
        return None

    try:
        if DATABASE_URL:
            sql = sql.replace("?", "%s")
            sql = sql.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
            cursor = conn.cursor(cursor_factory=RealDictCursor)
        else:
            cursor = conn.cursor()

        cursor.execute(sql, params)

        result = None
        if fetch_mode == 'one':
            result = cursor.fetchone()
        elif fetch_mode == 'all':
            result = cursor.fetchall()
        
        if commit:
            conn.commit()
            if DATABASE_URL and sql.strip().upper().startswith("INSERT"):
                 pass 
            elif not DATABASE_URL and sql.strip().upper().startswith("INSERT"):
                 result = cursor.lastrowid 

        return result
    except Exception as e:
        print(f"[DB] Query Error: {e}\nQuery: {sql}")
        return None
    finally:
        conn.close()

def execute_insert_returning_id(sql, params=()):
    conn = get_db_connection()
    if not conn: return None
    
    try:
        is_postgres = bool(DATABASE_URL)
        if is_postgres:
            sql = sql.replace("?", "%s")
            sql += " RETURNING id" if "RETURNING" not in sql.upper() else ""
            cursor = conn.cursor()
            cursor.execute(sql, params)
            new_id = cursor.fetchone()[0]
            conn.commit()
            return new_id
        else:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            conn.commit()
            return cursor.lastrowid
    except Exception as e:
        print(f"[DB] Insert Error: {e}")
        return None
    finally:
        conn.close()

def init_db():
    print(f"[DB] Initializing database... (Mode: {'PostgreSQL' if DATABASE_URL else 'SQLite'})")
    
    users_table = """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            phone TEXT,
            location TEXT,
            bio TEXT,
            linkedin TEXT,
            github TEXT,
            skills TEXT,
            experience_years TEXT,
            degree TEXT,
            university TEXT,
            grad_year TEXT,
            resume_path TEXT,
            resume_text TEXT
        )
    """
    execute_query(users_table, commit=True)
    
    create_notifications_table()
    create_resumes_table()
    create_learn_tables()
    create_roadmaps_table()
    
    migrate_columns()
    
    print("[DB] Database initialized successfully.")

def create_learn_tables():
    courses_sql = """
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            topic TEXT NOT NULL,
            syllabus_json TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    execute_query(courses_sql, commit=True)

    progress_sql = """
        CREATE TABLE IF NOT EXISTS course_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            course_id INTEGER NOT NULL,
            current_week INTEGER DEFAULT 1,
            current_day INTEGER DEFAULT 1,
            completed_days_json TEXT DEFAULT '[]',
            is_completed BOOLEAN DEFAULT 0
        )
    """
    execute_query(progress_sql, commit=True)

    content_sql = """
        CREATE TABLE IF NOT EXISTS course_content (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER NOT NULL,
            week_number INTEGER NOT NULL,
            day_number INTEGER NOT NULL,
            content_markdown TEXT NOT NULL
        )
    """
    execute_query(content_sql, commit=True)
    
    assessments_sql = """
        CREATE TABLE IF NOT EXISTS assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER NOT NULL,
            week_number INTEGER NOT NULL,
            is_final_exam BOOLEAN DEFAULT 0,
            questions_json TEXT NOT NULL,
            score INTEGER,
            passed BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    execute_query(assessments_sql, commit=True)

def create_notifications_table():
    sql = """
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            job_title TEXT NOT NULL,
            company TEXT NOT NULL,
            match_score INTEGER,
            reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_read BOOLEAN DEFAULT 0,
            apply_link TEXT
        )
    """
    execute_query(sql, commit=True)

def create_resumes_table():
    sql = """
        CREATE TABLE IF NOT EXISTS resumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            resume_text TEXT,
            is_active BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    execute_query(sql, commit=True)

def create_roadmaps_table():
    sql = """
        CREATE TABLE IF NOT EXISTS roadmaps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            domain TEXT NOT NULL,
            roadmap_json TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    execute_query(sql, commit=True)

def migrate_columns():
    
    migrations = [
        ("users", "resume_path", "TEXT"),
        ("users", "resume_text", "TEXT"),
        ("notifications", "apply_link", "TEXT")
    ]
    
    for table, col, type_def in migrations:
        try:
            execute_query(f"SELECT {col} FROM {table} LIMIT 1")
        except:
            print(f"[DB] Migrating {table}: Adding {col}")
            try:
                execute_query(f"ALTER TABLE {table} ADD COLUMN {col} {type_def}", commit=True)
            except Exception as e:
                print(f"[DB] Migration Error ({table}.{col}): {e}")

def add_user(full_name, email, password):
    sql = "INSERT INTO users (full_name, email, password) VALUES (?, ?, ?)"
    try:
        execute_query(sql, (full_name, email, password), commit=True)
        print(f"[DB] User added: {email}")
        return True
    except Exception as e:
        print(f"[DB] Add User Error (likely exists): {e}")
        return False

def get_user(email, password):
    sql = "SELECT full_name, email FROM users WHERE email = ? AND password = ?"
    
    result = execute_query(sql, (email, password), fetch_mode='one')
    if result:
        return (result['full_name'], result['email'])
    return None

def get_user_profile(email):
    sql = "SELECT * FROM users WHERE email = ?"
    return execute_query(sql, (email,), fetch_mode='one')

def update_user_profile(email, phone, location, bio, linkedin, github, skills, experience_years, degree, university, grad_year, resume_path=None, resume_text=None):
    sql = """
        UPDATE users 
        SET phone=?, location=?, bio=?, linkedin=?, github=?, skills=?, experience_years=?, degree=?, university=?, grad_year=?
    """
    params = [phone, location, bio, linkedin, github, skills, experience_years, degree, university, grad_year]
    
    if resume_path:
        sql += ", resume_path=?"
        params.append(resume_path)
    if resume_text:
        sql += ", resume_text=?"
        params.append(resume_text)
        
    sql += " WHERE email=?"
    params.append(email)
    
    try:
        execute_query(sql, tuple(params), commit=True)
        return True
    except:
        return False

def add_notification(user_email, job_title, company, match_score, reason, apply_link="#"):
    sql = """
        INSERT INTO notifications (user_email, job_title, company, match_score, reason, apply_link)
        VALUES (?, ?, ?, ?, ?, ?)
    """
    try:
        execute_query(sql, (user_email, job_title, company, match_score, reason, apply_link), commit=True)
        return True
    except:
        return False

def get_notifications(user_email, limit=20):
    sql = """
        SELECT * FROM notifications 
        WHERE user_email = ? 
        ORDER BY created_at DESC 
        LIMIT ?
    """
    res = execute_query(sql, (user_email, limit), fetch_mode='all')
    return res if res else []

def mark_notifications_read(user_email):
    sql = "UPDATE notifications SET is_read = 1 WHERE user_email = ?"
    execute_query(sql, (user_email,), commit=True)

def delete_notification(notif_id, user_email):
    sql = "DELETE FROM notifications WHERE id=? AND user_email=?"
    try:
        execute_query(sql, (notif_id, user_email), commit=True)
        return True
    except:
        return False

def add_resume(user_email, filename, file_path, resume_text, is_active=False):
    try:
        if is_active:
            execute_query("UPDATE resumes SET is_active=0 WHERE user_email=?", (user_email,), commit=True)
        
        sql = """
            INSERT INTO resumes (user_email, filename, file_path, resume_text, is_active)
            VALUES (?, ?, ?, ?, ?)
        """
        execute_query(sql, (user_email, filename, file_path, resume_text, is_active), commit=True)
        return True
    except Exception as e:
        print(f"Add Resume Error: {e}")
        return False

def get_user_resumes(user_email):
    sql = "SELECT * FROM resumes WHERE user_email=? ORDER BY created_at DESC"
    res = execute_query(sql, (user_email,), fetch_mode='all')
    return res if res else []

def delete_resume(resume_id, user_email):
    sql = "DELETE FROM resumes WHERE id=? AND user_email=?"
    try:
        execute_query(sql, (resume_id, user_email), commit=True)
        return True
    except:
        return False

def set_active_resume(resume_id, user_email):
    try:
        execute_query("UPDATE resumes SET is_active=0 WHERE user_email=?", (user_email,), commit=True)
        execute_query("UPDATE resumes SET is_active=1 WHERE id=? AND user_email=?", (resume_id, user_email), commit=True)
        return True
    except:
        return False

def get_active_resume_text(user_email):
    sql = "SELECT resume_text FROM resumes WHERE user_email=? AND is_active=1"
    res = execute_query(sql, (user_email,), fetch_mode='one')
    if res:
        return res['resume_text']
    return ""

def create_course(user_email, topic, syllabus_json):
    sql = "INSERT INTO courses (user_email, topic, syllabus_json) VALUES (?, ?, ?)"
    try:
        course_id = execute_insert_returning_id(sql, (user_email, topic, syllabus_json))
        
        if course_id:
            execute_query("INSERT INTO course_progress (user_email, course_id) VALUES (?, ?)", (user_email, course_id), commit=True)
            return course_id
        return None
    except Exception as e:
        print(f"Create Course Error: {e}")
        return None

def get_user_courses(user_email):
    sql = """
        SELECT c.id, c.topic, c.syllabus_json, c.created_at, 
               p.current_week, p.current_day, p.is_completed 
        FROM courses c 
        JOIN course_progress p ON c.id = p.course_id 
        WHERE c.user_email = ? 
        ORDER BY c.created_at DESC
    """
    res = execute_query(sql, (user_email,), fetch_mode='all')
    return res if res else []

def get_course_details(course_id):
    sql = """
        SELECT c.*, p.current_week, p.current_day, p.completed_days_json, p.is_completed 
        FROM courses c 
        JOIN course_progress p ON c.id = p.course_id 
        WHERE c.id = ?
    """
    return execute_query(sql, (course_id,), fetch_mode='one')

def save_day_content(course_id, week, day, content):
    sql = "INSERT INTO course_content (course_id, week_number, day_number, content_markdown) VALUES (?, ?, ?, ?)"
    execute_query(sql, (course_id, week, day, content), commit=True)

def get_day_content(course_id, week, day):
    sql = "SELECT content_markdown FROM course_content WHERE course_id=? AND week_number=? AND day_number=?"
    res = execute_query(sql, (course_id, week, day), fetch_mode='one')
    return res['content_markdown'] if res else None

def update_course_progress(course_id, week, day, completed_days):
    sql = "UPDATE course_progress SET current_week=?, current_day=?, completed_days_json=? WHERE course_id=?"
    execute_query(sql, (week, day, completed_days, course_id), commit=True)

def save_roadmap(user_email, domain, roadmap_json):
    try:
        execute_query("DELETE FROM roadmaps WHERE user_email=?", (user_email,), commit=True)
        sql = "INSERT INTO roadmaps (user_email, domain, roadmap_json) VALUES (?, ?, ?)"
        execute_query(sql, (user_email, domain, roadmap_json), commit=True)
        return True
    except:
        return False

def get_user_roadmap(user_email):
    sql = "SELECT * FROM roadmaps WHERE user_email=? ORDER BY created_at DESC"
    res = execute_query(sql, (user_email,), fetch_mode='one')
    return res

def delete_roadmap(user_email):
    sql = "DELETE FROM roadmaps WHERE user_email=?"
    try:
        execute_query(sql, (user_email,), commit=True)
        return True
    except:
        return False

def migrate_notifications_schema():
    migrate_columns()
def migrate_users_schema():
    migrate_columns()
