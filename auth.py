"""
auth.py - Authentication & Authorization Layer
Handles user and admin login verification, registration,
password hashing, and role-based session validation.
"""

import sqlite3
import re
from database import get_connection, hash_password, verify_password


def authenticate_admin(username, password):
    """
    Authenticates admin credentials against the 'admins' table.
    Returns: (admin_dict, error_message)
    """
    username = username.strip()
    if not username or not password:
        return None, "Please enter both username and password."

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, password_hash, salt, full_name FROM admins WHERE username = ?;", (username,))
        row = cursor.fetchone()
        if not row:
            return None, "Invalid admin username or password."

        if not verify_password(password, row["password_hash"], row["salt"]):
            return None, "Invalid admin username or password."

        return {
            "id": row["id"],
            "username": row["username"],
            "full_name": row["full_name"],
            "role": "admin"
        }, None
    except Exception as e:
        return None, f"Authentication error: {e}"
    finally:
        conn.close()


def authenticate_user(username, password):
    """
    Authenticates standard user credentials against the 'users' table.
    Checks that the user's account is active.
    Returns: (user_dict, error_message)
    """
    username = username.strip()
    if not username or not password:
        return None, "Please enter both username and password."

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, password_hash, salt, full_name, email, is_active FROM users WHERE username = ?;", (username,))
        row = cursor.fetchone()
        if not row:
            return None, "Invalid username or password."

        if not verify_password(password, row["password_hash"], row["salt"]):
            return None, "Invalid username or password."

        if row["is_active"] != 1:
            return None, "Your account has been deactivated by an administrator."

        return {
            "id": row["id"],
            "username": row["username"],
            "full_name": row["full_name"],
            "email": row["email"],
            "role": "user"
        }, None
    except Exception as e:
        return None, f"Authentication error: {e}"
    finally:
        conn.close()


def register_user(username, password, full_name, email):
    """
    Validates and registers a new standard user account.
    Returns: (success_bool, error_message)
    """
    username = username.strip()
    full_name = full_name.strip()
    email = email.strip()

    if not username:
        return False, "Username is required."
    if len(username) < 3:
        return False, "Username must be at least 3 characters long."
    if not re.match(r"^[a-zA-Z0-9_.-]+$", username):
        return False, "Username can only contain letters, numbers, dots, and underscores."

    if not password:
        return False, "Password is required."
    if len(password) < 4:
        return False, "Password must be at least 4 characters long."

    if not full_name:
        return False, "Full Name is required."

    if email and not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return False, "Please enter a valid email address."

    hashed_pw, salt = hash_password(password)
    import datetime
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (username, password_hash, salt, full_name, email, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, 1, ?);
        """, (username, hashed_pw, salt, full_name, email, now))
        conn.commit()
        return True, None
    except sqlite3.IntegrityError:
        return False, f"Username '{username}' is already taken. Please choose another."
    except Exception as e:
        return False, f"Registration failed: {e}"
    finally:
        conn.close()
