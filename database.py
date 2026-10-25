"""
database.py - Database Layer for Python Quiz Management System
Handles SQLite connection, schema creation, migrations, seeding,
and all parameterized queries for admins, users, categories, questions,
settings, and quiz attempts.
"""

import os
import sys
import json
import sqlite3
import datetime
import hashlib
import secrets

DB_NAME = "quiz.db"


def get_db_path():
    """Returns absolute path to quiz.db in the application directory."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, DB_NAME)


def get_connection():
    """Creates a new SQLite connection with foreign keys enabled."""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def hash_password(password, salt=None):
    """Secure password hashing using PBKDF2-HMAC-SHA256."""
    if not salt:
        salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000).hex()
    return hashed, salt


def verify_password(password, stored_hash, salt):
    """Verifies a plaintext password against stored hash and salt."""
    computed_hash, _ = hash_password(password, salt)
    return secrets.compare_digest(computed_hash, stored_hash)


def init_database():
    """Initializes tables, default settings, demo admin, categories, and sample questions."""
    conn = get_connection()
    try:
        cursor = conn.cursor()

        # 1. Admins Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                full_name TEXT,
                created_at TEXT NOT NULL
            );
        """)

        # 2. Users Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                full_name TEXT,
                email TEXT,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL
            );
        """)

        # 3. Categories Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                created_at TEXT NOT NULL
            );
        """)

        # 4. Questions Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE RESTRICT,
                question_text TEXT NOT NULL,
                option_a TEXT NOT NULL,
                option_b TEXT NOT NULL,
                option_c TEXT NOT NULL,
                option_d TEXT NOT NULL,
                correct_answer TEXT NOT NULL, -- 'A', 'B', 'C', or 'D'
                difficulty TEXT NOT NULL DEFAULT 'Medium', -- 'Easy', 'Medium', 'Hard'
                marks INTEGER NOT NULL DEFAULT 1,
                explanation TEXT,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL
            );
        """)

        # 5. Quiz Attempts Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quiz_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
                category_name TEXT,
                difficulty TEXT NOT NULL DEFAULT 'All',
                total_questions INTEGER NOT NULL,
                correct_answers INTEGER NOT NULL,
                incorrect_answers INTEGER NOT NULL,
                unanswered INTEGER NOT NULL,
                score_marks INTEGER NOT NULL,
                max_marks INTEGER NOT NULL,
                percentage REAL NOT NULL,
                passed INTEGER NOT NULL, -- 1=Pass, 0=Fail
                time_taken_seconds INTEGER NOT NULL,
                created_at TEXT NOT NULL
            );
        """)

        # 6. Quiz Answers Snapshot Table (Preserves historical answers even if questions change)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quiz_answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                attempt_id INTEGER NOT NULL REFERENCES quiz_attempts(id) ON DELETE CASCADE,
                question_id INTEGER REFERENCES questions(id) ON DELETE SET NULL,
                question_text TEXT NOT NULL,
                option_a TEXT NOT NULL,
                option_b TEXT NOT NULL,
                option_c TEXT NOT NULL,
                option_d TEXT NOT NULL,
                correct_answer TEXT NOT NULL,
                user_answer TEXT, -- 'A', 'B', 'C', 'D' or None
                is_correct INTEGER NOT NULL,
                marks_awarded INTEGER NOT NULL,
                explanation TEXT
            );
        """)

        # 7. Settings Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
        """)

        conn.commit()

        # Seed Default Data
        _seed_default_settings(cursor)
        _seed_default_admin(cursor)
        _seed_default_user(cursor)
        _seed_default_categories(cursor)
        conn.commit()

        # Seed questions from questions.json if questions table is empty
        _seed_sample_questions(cursor)
        conn.commit()

    except sqlite3.Error as e:
        print(f"[Database Error during init]: {e}")
        raise
    finally:
        conn.close()


def _seed_default_settings(cursor):
    """Seed initial settings if not present."""
    default_settings = {
        "questions_per_quiz": "10",
        "timer_minutes": "10",
        "passing_percentage": "60",
        "randomize_questions": "true",
        "show_answers_after_submission": "true",
        "allow_retakes": "true"
    }
    for key, val in default_settings.items():
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?);", (key, val))


def _seed_default_admin(cursor):
    """Seed demo admin: admin / admin123"""
    cursor.execute("SELECT id FROM admins WHERE username = 'admin';")
    if not cursor.fetchone():
        hashed, salt = hash_password("admin123")
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO admins (username, password_hash, salt, full_name, created_at)
            VALUES (?, ?, ?, ?, ?);
        """, ("admin", hashed, salt, "System Administrator", now))


def _seed_default_user(cursor):
    """Seed demo user: student / student123"""
    cursor.execute("SELECT id FROM users WHERE username = 'student';")
    if not cursor.fetchone():
        hashed, salt = hash_password("student123")
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO users (username, password_hash, salt, full_name, email, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, 1, ?);
        """, ("student", hashed, salt, "Demo Student", "student@example.com", now))


def _seed_default_categories(cursor):
    """Seed standard categories."""
    default_categories = [
        ("Python", "Python programming language concepts, data structures, and syntax"),
        ("Computer Basics", "Fundamental concepts of computer hardware, input/output, and storage"),
        ("General Knowledge", "General science, geography, physics, and history trivia"),
        ("Computer Science", "Algorithms, binary math, data structures, and theory"),
        ("Mathematics", "Arithmetic, algebra, and logical reasoning"),
        ("Networking", "Computer networks, protocols, IP addressing, and the web")
    ]
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for name, desc in default_categories:
        cursor.execute("""
            INSERT OR IGNORE INTO categories (name, description, created_at)
            VALUES (?, ?, ?);
        """, (name, desc, now))


def _seed_sample_questions(cursor):
    """Seeds questions from questions.json into SQLite questions table if empty."""
    cursor.execute("SELECT COUNT(*) AS cnt FROM questions;")
    row = cursor.fetchone()
    if row and row["cnt"] > 0:
        return  # Questions already present

    json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "questions.json")
    if not os.path.exists(json_path):
        return

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"[Seed Warning] Could not load questions.json: {e}")
        return

    # Map category names to IDs
    cursor.execute("SELECT id, name FROM categories;")
    cat_map = {r["name"].lower(): r["id"] for r in cursor.fetchall()}
    default_cat_id = cat_map.get("computer basics") or list(cat_map.values())[0]

    # Pre-defined explanations for seed questions
    explanations = {
        "What does CPU stand for in computer hardware?": "CPU stands for Central Processing Unit, the primary component that executes instructions.",
        "Which keyword is used to define a function in Python?": "The 'def' keyword is used in Python to define custom functions.",
        "What type of computer memory is volatile and loses data when powered off?": "RAM (Random Access Memory) requires continuous electrical power to retain data.",
        "Which protocol provides encrypted, secure communication over the World Wide Web?": "HTTPS (Hypertext Transfer Protocol Secure) encrypts HTTP traffic via TLS/SSL.",
        "What does HTML stand for?": "HTML stands for HyperText Markup Language, the standard language for web documents.",
        "Who created the Python programming language?": "Guido van Rossum released the first version of Python in 1991.",
        "What does SSD stand for in modern storage drives?": "SSD stands for Solid State Drive, utilizing flash memory rather than spinning magnetic platters.",
        "Which Python built-in data type is immutable?": "Tuples cannot be modified after creation, making them immutable in Python.",
        "Which of the following is an open-source operating system kernel?": "Linux is a free and open-source Unix-like operating system kernel created by Linus Torvalds.",
        "What does GUI stand for in software applications?": "GUI stands for Graphical User Interface, allowing users to interact through visual elements."
    }

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    difficulties = ["Easy", "Medium", "Hard"]

    for idx, item in enumerate(data):
        cat_name = item.get("category", "Computer Basics").lower()
        cat_id = cat_map.get(cat_name, default_cat_id)
        q_text = item.get("question", "").strip()
        opts = item.get("options", [])
        ans_text = item.get("answer", "").strip()

        if len(opts) != 4 or not q_text or not ans_text:
            continue

        # Find letter for answer
        correct_letter = "A"
        for letter_idx, opt_str in enumerate(opts):
            if opt_str.strip() == ans_text:
                correct_letter = chr(65 + letter_idx)
                break

        difficulty = difficulties[idx % 3]
        explanation = explanations.get(q_text, f"The correct answer is {ans_text}.")

        cursor.execute("""
            INSERT INTO questions 
            (category_id, question_text, option_a, option_b, option_c, option_d, correct_answer, difficulty, marks, explanation, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?);
        """, (cat_id, q_text, opts[0], opts[1], opts[2], opts[3], correct_letter, difficulty, 1, explanation, now))


# ==========================================
# SETTINGS CRUD
# ==========================================
def get_settings():
    """Returns a dict of all configuration settings."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM settings;")
        rows = cursor.fetchall()
        return {r["key"]: r["value"] for r in rows}
    finally:
        conn.close()


def get_setting(key, default=None):
    """Returns a single setting value."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?;", (key,))
        row = cursor.fetchone()
        return row["value"] if row else default
    finally:
        conn.close()


def update_settings(settings_dict):
    """Updates multiple settings in SQLite."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        for k, v in settings_dict.items():
            cursor.execute("""
                INSERT INTO settings (key, value) VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value;
            """, (k, str(v)))
        conn.commit()
        return True
    finally:
        conn.close()


# ==========================================
# CATEGORIES CRUD
# ==========================================
def get_categories(with_counts=True):
    """
    Returns list of categories. If with_counts is True,
    includes 'question_count' for each category.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        if with_counts:
            cursor.execute("""
                SELECT c.id, c.name, c.description, c.created_at,
                       COUNT(q.id) AS question_count,
                       SUM(CASE WHEN q.is_active = 1 THEN 1 ELSE 0 END) AS active_question_count
                FROM categories c
                LEFT JOIN questions q ON c.id = q.category_id
                GROUP BY c.id
                ORDER BY c.name ASC;
            """)
        else:
            cursor.execute("SELECT id, name, description, created_at FROM categories ORDER BY name ASC;")
        return [dict(r) for r in cursor.fetchall()]
    finally:
        conn.close()


def add_category(name, description=""):
    """Adds a new category."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO categories (name, description, created_at)
            VALUES (?, ?, ?);
        """, (name.strip(), description.strip(), now))
        conn.commit()
        return cursor.lastrowid, None
    except sqlite3.IntegrityError:
        return None, f"Category '{name}' already exists."
    except Exception as e:
        return None, str(e)
    finally:
        conn.close()


def update_category(cat_id, name, description=""):
    """Renames or updates an existing category."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE categories SET name = ?, description = ?
            WHERE id = ?;
        """, (name.strip(), description.strip(), cat_id))
        conn.commit()
        return True, None
    except sqlite3.IntegrityError:
        return False, f"Category name '{name}' already exists."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def delete_category(cat_id):
    """
    Safely deletes a category.
    Prevents deletion if questions exist under it.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) AS cnt FROM questions WHERE category_id = ?;", (cat_id,))
        count = cursor.fetchone()["cnt"]
        if count > 0:
            return False, f"Cannot delete category: it still contains {count} question(s). Reassign or delete those questions first."

        cursor.execute("DELETE FROM categories WHERE id = ?;", (cat_id,))
        conn.commit()
        return True, None
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


# ==========================================
# QUESTIONS CRUD
# ==========================================
def get_questions(category_id=None, difficulty=None, status=None, search_query=None):
    """Retrieves questions with optional filtering and category names."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        query = """
            SELECT q.id, q.category_id, c.name AS category_name, q.question_text,
                   q.option_a, q.option_b, q.option_c, q.option_d,
                   q.correct_answer, q.difficulty, q.marks, q.explanation,
                   q.is_active, q.created_at
            FROM questions q
            JOIN categories c ON q.category_id = c.id
            WHERE 1=1
        """
        params = []

        if category_id and category_id != "All":
            query += " AND q.category_id = ?"
            params.append(int(category_id))

        if difficulty and difficulty != "All":
            query += " AND q.difficulty = ?"
            params.append(difficulty)

        if status is not None and status != "All":
            query += " AND q.is_active = ?"
            params.append(1 if status in (1, True, "Active") else 0)

        if search_query and search_query.strip():
            query += " AND (q.question_text LIKE ? OR q.explanation LIKE ?)"
            term = f"%{search_query.strip()}%"
            params.extend([term, term])

        query += " ORDER BY q.id DESC;"
        cursor.execute(query, params)
        return [dict(r) for r in cursor.fetchall()]
    finally:
        conn.close()


def get_question_by_id(question_id):
    """Fetches a single question by primary key."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT q.*, c.name AS category_name
            FROM questions q
            JOIN categories c ON q.category_id = c.id
            WHERE q.id = ?;
        """, (question_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def add_question(category_id, question_text, opt_a, opt_b, opt_c, opt_d,
                 correct_answer, difficulty="Medium", marks=1, explanation="", is_active=1):
    """Inserts a new question into SQLite."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO questions 
            (category_id, question_text, option_a, option_b, option_c, option_d,
             correct_answer, difficulty, marks, explanation, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (category_id, question_text.strip(), opt_a.strip(), opt_b.strip(), opt_c.strip(), opt_d.strip(),
              correct_answer.upper().strip(), difficulty.strip(), int(marks), explanation.strip(), int(is_active), now))
        conn.commit()
        return cursor.lastrowid, None
    except Exception as e:
        return None, str(e)
    finally:
        conn.close()


def update_question(question_id, category_id, question_text, opt_a, opt_b, opt_c, opt_d,
                    correct_answer, difficulty="Medium", marks=1, explanation="", is_active=1):
    """Updates an existing question."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE questions SET
                category_id = ?,
                question_text = ?,
                option_a = ?,
                option_b = ?,
                option_c = ?,
                option_d = ?,
                correct_answer = ?,
                difficulty = ?,
                marks = ?,
                explanation = ?,
                is_active = ?
            WHERE id = ?;
        """, (category_id, question_text.strip(), opt_a.strip(), opt_b.strip(), opt_c.strip(), opt_d.strip(),
              correct_answer.upper().strip(), difficulty.strip(), int(marks), explanation.strip(), int(is_active), question_id))
        conn.commit()
        return True, None
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def delete_question(question_id):
    """Deletes a question by ID."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM questions WHERE id = ?;", (question_id,))
        conn.commit()
        return True, None
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def toggle_question_status(question_id):
    """Toggles active/inactive state of a question."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE questions SET is_active = CASE WHEN is_active = 1 THEN 0 ELSE 1 END WHERE id = ?;", (question_id,))
        conn.commit()
        cursor.execute("SELECT is_active FROM questions WHERE id = ?;", (question_id,))
        row = cursor.fetchone()
        return (row["is_active"] if row else None), None
    except Exception as e:
        return None, str(e)
    finally:
        conn.close()


def get_active_questions_for_quiz(category_id=None, difficulty=None, limit=10, randomize=True):
    """Fetches active questions configured for a user quiz session."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        query = """
            SELECT q.id, q.category_id, c.name AS category_name, q.question_text,
                   q.option_a, q.option_b, q.option_c, q.option_d,
                   q.correct_answer, q.difficulty, q.marks, q.explanation
            FROM questions q
            JOIN categories c ON q.category_id = c.id
            WHERE q.is_active = 1
        """
        params = []
        if category_id and category_id != "All":
            query += " AND q.category_id = ?"
            params.append(int(category_id))

        if difficulty and difficulty != "All":
            query += " AND q.difficulty = ?"
            params.append(difficulty)

        if randomize:
            query += " ORDER BY RANDOM()"
        else:
            query += " ORDER BY q.id ASC"

        if limit and limit > 0:
            query += " LIMIT ?"
            params.append(int(limit))

        cursor.execute(query, params)
        return [dict(r) for r in cursor.fetchall()]
    finally:
        conn.close()


# ==========================================
# USERS CRUD & STATS
# ==========================================
def get_all_users(search_query=None):
    """Retrieves all registered users with their attempt counts and average scores."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        query = """
            SELECT u.id, u.username, u.full_name, u.email, u.is_active, u.created_at,
                   COUNT(qa.id) AS attempts_count,
                   COALESCE(AVG(qa.percentage), 0) AS avg_score,
                   COALESCE(MAX(qa.percentage), 0) AS best_score
            FROM users u
            LEFT JOIN quiz_attempts qa ON u.id = qa.user_id
            WHERE 1=1
        """
        params = []
        if search_query and search_query.strip():
            query += " AND (u.username LIKE ? OR u.full_name LIKE ? OR u.email LIKE ?)"
            term = f"%{search_query.strip()}%"
            params.extend([term, term, term])

        query += " GROUP BY u.id ORDER BY u.created_at DESC;"
        cursor.execute(query, params)
        return [dict(r) for r in cursor.fetchall()]
    finally:
        conn.close()


def get_user_by_id(user_id):
    """Fetches user record by ID."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, full_name, email, is_active, created_at FROM users WHERE id = ?;", (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def toggle_user_status(user_id):
    """Activates or deactivates a user account."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET is_active = CASE WHEN is_active = 1 THEN 0 ELSE 1 END WHERE id = ?;", (user_id,))
        conn.commit()
        cursor.execute("SELECT is_active FROM users WHERE id = ?;", (user_id,))
        row = cursor.fetchone()
        return (row["is_active"] if row else None), None
    except Exception as e:
        return None, str(e)
    finally:
        conn.close()


def get_user_dashboard_stats(user_id):
    """Calculates summary statistics for the user dashboard."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                COUNT(*) AS total_attempts,
                COALESCE(AVG(percentage), 0) AS avg_score,
                COALESCE(MAX(percentage), 0) AS best_score,
                SUM(CASE WHEN passed = 1 THEN 1 ELSE 0 END) AS quizzes_passed
            FROM quiz_attempts
            WHERE user_id = ?;
        """, (user_id,))
        row = cursor.fetchone()
        stats = dict(row) if row else {
            "total_attempts": 0, "avg_score": 0.0, "best_score": 0.0, "quizzes_passed": 0
        }
        stats["avg_score"] = round(stats["avg_score"], 1)
        stats["best_score"] = round(stats["best_score"], 1)
        return stats
    finally:
        conn.close()


# ==========================================
# QUIZ ATTEMPTS & ANSWERS
# ==========================================
def record_quiz_attempt(user_id, category_id, category_name, difficulty,
                        total_q, correct_q, incorrect_q, unanswered_q,
                        score_marks, max_marks, percentage, passed,
                        time_taken_seconds, answers_snapshot):
    """
    Saves a completed quiz attempt and its detailed question snapshots
    into SQLite in a single transaction.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
            INSERT INTO quiz_attempts
            (user_id, category_id, category_name, difficulty, total_questions,
             correct_answers, incorrect_answers, unanswered, score_marks, max_marks,
             percentage, passed, time_taken_seconds, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (user_id, category_id, category_name, difficulty, total_q,
              correct_q, incorrect_q, unanswered_q, score_marks, max_marks,
              round(percentage, 1), 1 if passed else 0, time_taken_seconds, now))

        attempt_id = cursor.lastrowid

        # Insert question-by-question snapshot
        for ans in answers_snapshot:
            cursor.execute("""
                INSERT INTO quiz_answers
                (attempt_id, question_id, question_text, option_a, option_b, option_c, option_d,
                 correct_answer, user_answer, is_correct, marks_awarded, explanation)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (attempt_id, ans.get("question_id"), ans["question_text"],
                  ans["option_a"], ans["option_b"], ans["option_c"], ans["option_d"],
                  ans["correct_answer"], ans.get("user_answer"), 1 if ans.get("is_correct") else 0,
                  ans.get("marks_awarded", 0), ans.get("explanation", "")))

        conn.commit()
        return attempt_id, None
    except Exception as e:
        conn.rollback()
        return None, str(e)
    finally:
        conn.close()


def get_user_attempts(user_id, limit=50):
    """Retrieves quiz history for a specific user."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, category_name, difficulty, total_questions,
                   correct_answers, incorrect_answers, unanswered,
                   score_marks, max_marks, percentage, passed,
                   time_taken_seconds, created_at
            FROM quiz_attempts
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?;
        """, (user_id, limit))
        return [dict(r) for r in cursor.fetchall()]
    finally:
        conn.close()


def get_all_attempts(category_id=None, search_user=None, sort_by="date_desc", limit=200):
    """Retrieves all quiz attempts across all users for admin reports."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        query = """
            SELECT qa.id, qa.user_id, u.username, u.full_name,
                   qa.category_name, qa.difficulty, qa.total_questions,
                   qa.correct_answers, qa.incorrect_answers, qa.unanswered,
                   qa.score_marks, qa.max_marks, qa.percentage, qa.passed,
                   qa.time_taken_seconds, qa.created_at
            FROM quiz_attempts qa
            JOIN users u ON qa.user_id = u.id
            WHERE 1=1
        """
        params = []
        if category_id and category_id != "All":
            query += " AND qa.category_id = ?"
            params.append(int(category_id))

        if search_user and search_user.strip():
            query += " AND (u.username LIKE ? OR u.full_name LIKE ?)"
            term = f"%{search_user.strip()}%"
            params.extend([term, term])

        # Sorting
        if sort_by == "score_desc":
            query += " ORDER BY qa.percentage DESC, qa.id DESC"
        elif sort_by == "score_asc":
            query += " ORDER BY qa.percentage ASC, qa.id DESC"
        elif sort_by == "user_asc":
            query += " ORDER BY u.username ASC, qa.id DESC"
        else:
            query += " ORDER BY qa.id DESC"

        query += " LIMIT ?;"
        params.append(int(limit))

        cursor.execute(query, params)
        return [dict(r) for r in cursor.fetchall()]
    finally:
        conn.close()


def get_attempt_details(attempt_id):
    """Retrieves header and question-level breakdown for a specific attempt."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT qa.*, u.username, u.full_name, u.email
            FROM quiz_attempts qa
            JOIN users u ON qa.user_id = u.id
            WHERE qa.id = ?;
        """, (attempt_id,))
        attempt_row = cursor.fetchone()
        if not attempt_row:
            return None, []

        cursor.execute("""
            SELECT id, question_id, question_text, option_a, option_b, option_c, option_d,
                   correct_answer, user_answer, is_correct, marks_awarded, explanation
            FROM quiz_answers
            WHERE attempt_id = ?
            ORDER BY id ASC;
        """, (attempt_id,))
        answers = [dict(r) for r in cursor.fetchall()]

        return dict(attempt_row), answers
    finally:
        conn.close()


def get_leaderboard(limit=10):
    """
    Calculates leaderboard rankings based on highest score,
    average score, and total attempts.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.username, u.full_name,
                   COUNT(qa.id) AS attempts,
                   MAX(qa.percentage) AS high_score,
                   ROUND(AVG(qa.percentage), 1) AS avg_score,
                   SUM(CASE WHEN qa.passed = 1 THEN 1 ELSE 0 END) AS passes
            FROM users u
            JOIN quiz_attempts qa ON u.id = qa.user_id
            WHERE u.is_active = 1
            GROUP BY u.id
            ORDER BY high_score DESC, avg_score DESC, attempts DESC
            LIMIT ?;
        """, (limit,))
        return [dict(r) for r in cursor.fetchall()]
    finally:
        conn.close()


# ==========================================
# ADMIN DASHBOARD STATS
# ==========================================
def get_admin_dashboard_summary():
    """Compiles statistics for the admin dashboard cards and charts."""
    conn = get_connection()
    try:
        cursor = conn.cursor()

        # Questions
        cursor.execute("SELECT COUNT(*) AS total, SUM(CASE WHEN is_active=1 THEN 1 ELSE 0 END) AS active FROM questions;")
        q_row = cursor.fetchone()
        total_questions = q_row["total"] or 0
        active_questions = q_row["active"] or 0

        # Categories
        cursor.execute("SELECT COUNT(*) AS total FROM categories;")
        total_categories = cursor.fetchone()["total"] or 0

        # Users
        cursor.execute("SELECT COUNT(*) AS total, SUM(CASE WHEN is_active=1 THEN 1 ELSE 0 END) AS active FROM users;")
        u_row = cursor.fetchone()
        total_users = u_row["total"] or 0
        active_users = u_row["active"] or 0

        # Quiz Attempts
        cursor.execute("""
            SELECT COUNT(*) AS total,
                   COALESCE(AVG(percentage), 0) AS avg_score,
                   SUM(CASE WHEN passed = 1 THEN 1 ELSE 0 END) AS pass_count
            FROM quiz_attempts;
        """)
        att_row = cursor.fetchone()
        total_attempts = att_row["total"] or 0
        avg_score = round(att_row["avg_score"] or 0.0, 1)
        pass_count = att_row["pass_count"] or 0
        fail_count = total_attempts - pass_count
        pass_rate = round((pass_count / total_attempts * 100), 1) if total_attempts > 0 else 0.0

        # Category question counts for chart
        cursor.execute("""
            SELECT c.name, COUNT(q.id) AS question_count
            FROM categories c
            LEFT JOIN questions q ON c.id = q.category_id AND q.is_active = 1
            GROUP BY c.id
            ORDER BY question_count DESC;
        """)
        cat_counts = [(r["name"], r["question_count"]) for r in cursor.fetchall()]

        # Recent Activity (last 6 quiz attempts)
        cursor.execute("""
            SELECT qa.id, u.username, qa.category_name, qa.score_marks, qa.max_marks,
                   qa.percentage, qa.passed, qa.created_at
            FROM quiz_attempts qa
            JOIN users u ON qa.user_id = u.id
            ORDER BY qa.id DESC
            LIMIT 6;
        """)
        recent_activity = [dict(r) for r in cursor.fetchall()]

        return {
            "total_questions": total_questions,
            "active_questions": active_questions,
            "total_categories": total_categories,
            "total_users": total_users,
            "active_users": active_users,
            "total_attempts": total_attempts,
            "avg_score": avg_score,
            "pass_count": pass_count,
            "fail_count": fail_count,
            "pass_rate": pass_rate,
            "cat_counts": cat_counts,
            "recent_activity": recent_activity
        }
    finally:
        conn.close()
