import sqlite3

DB_NAME = "users.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
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
            grad_year TEXT
        )
    """)
    conn.commit()
    conn.close()
    create_notifications_table()
    create_resumes_table()
    create_learn_tables()
    migrate_notifications_schema()
    migrate_users_schema()
    create_roadmaps_table()

def create_learn_tables():
    """Creates tables for the LEARN feature."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Courses Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            topic TEXT NOT NULL,
            syllabus_json TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_email) REFERENCES users(email)
        )
    """)

    # Course Progress Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS course_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            course_id INTEGER NOT NULL,
            current_week INTEGER DEFAULT 1,
            current_day INTEGER DEFAULT 1,
            completed_days_json TEXT DEFAULT '[]',
            is_completed BOOLEAN DEFAULT 0,
            FOREIGN KEY(user_email) REFERENCES users(email),
            FOREIGN KEY(course_id) REFERENCES courses(id)
        )
    """)

    # Assessments Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER NOT NULL,
            week_number INTEGER NOT NULL,
            is_final_exam BOOLEAN DEFAULT 0,
            questions_json TEXT NOT NULL,
            score INTEGER,
            passed BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(course_id) REFERENCES courses(id)
        )
    """)

    # Course Content Cache (to avoid re-generating same day content)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS course_content (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER NOT NULL,
            week_number INTEGER NOT NULL,
            day_number INTEGER NOT NULL,
            content_markdown TEXT NOT NULL,
            FOREIGN KEY(course_id) REFERENCES courses(id)
        )
    """)

    conn.commit()
    conn.close()

def add_user(full_name, email, password):
    """Adds a new user to the database. Returns True if successful, False if email exists."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (full_name, email, password) VALUES (?, ?, ?)", (full_name, email, password))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def get_user(email, password):
    """Retrieves a user by email and password."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT full_name, email FROM users WHERE email = ? AND password = ?", (email, password))
    user = cursor.fetchone()
    conn.close()
    return user

def update_user_profile(email, phone, location, bio, linkedin, github, skills, experience_years, degree, university, grad_year, resume_path=None, resume_text=None):
    """Updates the user's profile details."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # Dynamic query construction to handle optional resume updates
        query = """
            UPDATE users 
            SET phone=?, location=?, bio=?, linkedin=?, github=?, skills=?, experience_years=?, degree=?, university=?, grad_year=?
        """
        params = [phone, location, bio, linkedin, github, skills, experience_years, degree, university, grad_year]
        
        if resume_path:
            query += ", resume_path=?"
            params.append(resume_path)
        if resume_text:
            query += ", resume_text=?"
            params.append(resume_text)
            
        query += " WHERE email=?"
        params.append(email)
        
        cursor.execute(query, tuple(params))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"DB Error: {e}")
        return False

def migrate_users_schema():
    """Migrates users table to include resume columns."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("ALTER TABLE users ADD COLUMN resume_path TEXT")
        cursor.execute("ALTER TABLE users ADD COLUMN resume_text TEXT")
        conn.commit()
        conn.close()
    except:
        pass # Columns likely exist

def get_user_profile(email):
    """Retrieves full user profile by email."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # Allows accessing columns by name
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()
    return user

def create_notifications_table():
    """Creates the notifications table if it doesn't exist."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            job_title TEXT NOT NULL,
            company TEXT NOT NULL,
            match_score INTEGER,
            reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_read BOOLEAN DEFAULT 0,
            apply_link TEXT,
            FOREIGN KEY(user_email) REFERENCES users(email)
        )
    """)
    conn.commit()
    conn.close()

def create_resumes_table():
    """Creates the resumes table if it doesn't exist."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS resumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            resume_text TEXT,
            is_active BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_email) REFERENCES users(email)
        )
    """)
    conn.commit()
    conn.close()

# --- Resume Management Functions ---

def add_resume(user_email, filename, file_path, resume_text, is_active=False):
    """Adds a new resume. If is_active is True, deactivates others."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        if is_active:
            # Deactivate all other resumes for this user
            cursor.execute("UPDATE resumes SET is_active=0 WHERE user_email=?", (user_email,))
            
        cursor.execute("""
            INSERT INTO resumes (user_email, filename, file_path, resume_text, is_active)
            VALUES (?, ?, ?, ?, ?)
        """, (user_email, filename, file_path, resume_text, is_active))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"DB Error (add_resume): {e}")
        return False

def get_user_resumes(user_email):
    """Retrieves all resumes for a user."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM resumes WHERE user_email=? ORDER BY created_at DESC", (user_email,))
    resumes = cursor.fetchall()
    conn.close()
    return resumes

def delete_resume(resume_id, user_email):
    """Deletes a resume by ID."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM resumes WHERE id=? AND user_email=?", (resume_id, user_email))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"DB Error (delete_resume): {e}")
        return False

def set_active_resume(resume_id, user_email):
    """Sets a resume as active and deactivates others."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # Deactivate all
        cursor.execute("UPDATE resumes SET is_active=0 WHERE user_email=?", (user_email,))
        
        # Activate specific one
        cursor.execute("UPDATE resumes SET is_active=1 WHERE id=? AND user_email=?", (resume_id, user_email))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"DB Error (set_active_resume): {e}")
        return False

def get_active_resume_text(user_email):
    """Gets the text of the active resume."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT resume_text FROM resumes WHERE user_email=? AND is_active=1 LIMIT 1", (user_email,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else ""
    except Exception as e:
        print(f"DB Error (get_active_resume_text): {e}")
        return ""

def migrate_notifications_schema():
    """Migrates notifications table to include apply_link."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("ALTER TABLE notifications ADD COLUMN apply_link TEXT")
        conn.commit()
        conn.close()
    except:
        pass # Column likely exists

def add_notification(user_email, job_title, company, match_score, reason, apply_link="#"):
    """Adds a new notification."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO notifications (user_email, job_title, company, match_score, reason, apply_link)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_email, job_title, company, match_score, reason, apply_link))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"DB Error (add_notification): {e}")
        return False

def get_notifications(user_email, limit=5):
    """Retrieves recent notifications for a user."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM notifications 
        WHERE user_email = ? 
        ORDER BY created_at DESC 
        LIMIT ?
    """, (user_email, limit))
    notifications = cursor.fetchall()
    conn.close()
    return notifications

def mark_notifications_read(user_email):
    """Marks all notifications as read for a user."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE notifications SET is_read = 1 WHERE user_email = ?", (user_email,))
    conn.commit()
    conn.close()

# --- LEARN Feature Functions ---

def create_course(user_email, topic, syllabus_json):
    """Creates a new course."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO courses (user_email, topic, syllabus_json) VALUES (?, ?, ?)", (user_email, topic, syllabus_json))
        course_id = cursor.lastrowid
        
        # Initialize Progress
        cursor.execute("INSERT INTO course_progress (user_email, course_id) VALUES (?, ?)", (user_email, course_id))
        
        conn.commit()
        conn.close()
        return course_id
    except Exception as e:
        print(f"DB Error (create_course): {e}")
        return None

def get_user_courses(user_email):
    """Retrieves all courses for a user."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.*, p.current_week, p.current_day, p.is_completed 
        FROM courses c 
        JOIN course_progress p ON c.id = p.course_id 
        WHERE c.user_email = ? 
        ORDER BY c.created_at DESC
    """, (user_email,))
    courses = cursor.fetchall()
    conn.close()
    return courses

def get_course_details(course_id):
    """Retrieves course details and progress."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.*, p.current_week, p.current_day, p.completed_days_json, p.is_completed 
        FROM courses c 
        JOIN course_progress p ON c.id = p.course_id 
        WHERE c.id = ?
    """, (course_id,))
    course = cursor.fetchone()
    conn.close()
    return course

def save_day_content(course_id, week, day, content):
    """Caches generated content."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO course_content (course_id, week_number, day_number, content_markdown) VALUES (?, ?, ?, ?)", (course_id, week, day, content))
    conn.commit()
    conn.close()

def get_day_content(course_id, week, day):
    """Retrieves cached content."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT content_markdown FROM course_content WHERE course_id=? AND week_number=? AND day_number=?", (course_id, week, day))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def update_course_progress(course_id, week, day, completed_days):
    """Updates user progress."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE course_progress SET current_week=?, current_day=?, completed_days_json=? WHERE course_id=?", (week, day, completed_days, course_id))
    conn.commit()
    conn.close()

def create_roadmaps_table():
    """Creates the roadmaps table if it doesn't exist."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS roadmaps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            domain TEXT NOT NULL,
            roadmap_json TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_email) REFERENCES users(email)
        )
    """)
    conn.commit()
    conn.close()

def save_roadmap(user_email, domain, roadmap_json):
    """Saves a generated roadmap for a user. Replaces existing if same domain or updates?"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # Delete old roadmap for this user to keep it 1:1 for the "Career Architect" feature context
        cursor.execute("DELETE FROM roadmaps WHERE user_email=?", (user_email,))
        
        cursor.execute("INSERT INTO roadmaps (user_email, domain, roadmap_json) VALUES (?, ?, ?)", (user_email, domain, roadmap_json))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"DB Error (save_roadmap): {e}")
        return False

def get_user_roadmap(user_email):
    """Retrieves the user's saved roadmap."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM roadmaps WHERE user_email=? ORDER BY created_at DESC LIMIT 1", (user_email,))
    row = cursor.fetchone()
    conn.close()
    return row

def delete_roadmap(user_email):
    """Deletes the roadmap for a user."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM roadmaps WHERE user_email=?", (user_email,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"DB Error (delete_roadmap): {e}")
        return False
