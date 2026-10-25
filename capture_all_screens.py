"""
capture_all_screens.py - Captures authentic original screenshots of all application views.
"""

import os
import ctypes
from ctypes import wintypes
import tkinter as tk
from PIL import Image

import main
import database
import auth


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ('biSize', wintypes.DWORD),
        ('biWidth', wintypes.LONG),
        ('biHeight', wintypes.LONG),
        ('biPlanes', wintypes.WORD),
        ('biBitCount', wintypes.WORD),
        ('biCompression', wintypes.DWORD),
        ('biSizeImage', wintypes.DWORD),
        ('biXPelsPerMeter', wintypes.LONG),
        ('biYPelsPerMeter', wintypes.LONG),
        ('biClrUsed', wintypes.DWORD),
        ('biClrImportant', wintypes.DWORD),
    ]


def capture_window(window, filepath):
    window.update_idletasks()
    window.update()
    hwnd = window.winfo_id()
    rect = wintypes.RECT()
    ctypes.windll.user32.GetClientRect(hwnd, ctypes.byref(rect))
    w = max(1, rect.right - rect.left)
    h = max(1, rect.bottom - rect.top)

    hwnd_dc = ctypes.windll.user32.GetDC(hwnd)
    mfc_dc = ctypes.windll.gdi32.CreateCompatibleDC(hwnd_dc)
    save_bmp = ctypes.windll.gdi32.CreateCompatibleBitmap(hwnd_dc, w, h)
    ctypes.windll.gdi32.SelectObject(mfc_dc, save_bmp)

    # 2 = PW_RENDERFULLCONTENT
    ctypes.windll.user32.PrintWindow(hwnd, mfc_dc, 2)

    bmi = BITMAPINFOHEADER()
    bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.biWidth = w
    bmi.biHeight = -h
    bmi.biPlanes = 1
    bmi.biBitCount = 32
    bmi.biCompression = 0

    buf = ctypes.create_string_buffer(w * h * 4)
    ctypes.windll.gdi32.GetDIBits(mfc_dc, save_bmp, 0, h, buf, ctypes.byref(bmi), 0)

    ctypes.windll.user32.ReleaseDC(hwnd, hwnd_dc)
    ctypes.windll.gdi32.DeleteDC(mfc_dc)
    ctypes.windll.gdi32.DeleteObject(save_bmp)

    img = Image.frombuffer('RGBA', (w, h), buf, 'raw', 'BGRA', 0, 1)
    img = img.convert('RGB')
    img.save(filepath)
    print(f"Captured: {filepath} ({w}x{h})")


def main_capture():
    os.makedirs('assets/screenshots', exist_ok=True)
    database.init_database()

    root = tk.Tk()
    app = main.QuizSystemApp(root)
    root.update()

    # 1. Login Screen
    capture_window(root, 'assets/screenshots/fig_11_1_login.png')

    # Authenticate Admin
    admin, _ = auth.authenticate_admin('admin', 'admin123')
    app.current_user = admin
    app.show_admin_portal()
    root.update()

    # 2. Admin Dashboard
    app.navigate_admin('dashboard')
    root.update()
    capture_window(root, 'assets/screenshots/fig_11_2_admin_dashboard.png')

    # 3. Manage Questions
    app.navigate_admin('questions')
    root.update()
    capture_window(root, 'assets/screenshots/fig_11_3_manage_questions.png')

    # 4. Manage Categories
    app.navigate_admin('categories')
    root.update()
    capture_window(root, 'assets/screenshots/fig_11_4_manage_categories.png')

    # 5. Manage Users
    app.navigate_admin('users')
    root.update()
    capture_window(root, 'assets/screenshots/fig_11_5_manage_users.png')

    # 6. View Results
    app.navigate_admin('results')
    root.update()
    capture_window(root, 'assets/screenshots/fig_11_6_view_results.png')

    # 7. Settings
    app.navigate_admin('settings')
    root.update()
    capture_window(root, 'assets/screenshots/fig_11_7_settings.png')

    # Authenticate Student
    student, _ = auth.authenticate_user('student', 'student123')
    app.current_user = student

    # 8. Student Home Dashboard
    app.show_user_home()
    root.update()
    capture_window(root, 'assets/screenshots/fig_11_8_student_dashboard.png')

    # 9. Live Quiz Screen
    qs = database.get_active_questions_for_quiz(limit=5)
    app.launch_quiz('All', 'All Categories', 'All', qs)
    root.update()
    # Select option B on question
    if hasattr(app.main_container.winfo_children()[0], 'select_option'):
        app.main_container.winfo_children()[0].select_option('B')
        root.update()
    capture_window(root, 'assets/screenshots/fig_11_9_take_quiz.png')

    # 10. Post-Quiz Performance Summary
    # Ensure there's at least one attempt in database
    attempts = database.get_user_attempts(student['id'])
    if not attempts:
        # Create sample attempt
        answers_snapshot = []
        for q in qs:
            answers_snapshot.append({
                "question_id": q["id"],
                "question_text": q["question_text"],
                "option_a": q["option_a"],
                "option_b": q["option_b"],
                "option_c": q["option_c"],
                "option_d": q["option_d"],
                "correct_answer": q["correct_answer"],
                "user_answer": q["correct_answer"],
                "is_correct": True,
                "marks_awarded": 1,
                "explanation": q.get("explanation", "")
            })
        att_id, _ = database.record_quiz_attempt(
            user_id=student["id"], category_id=None, category_name="All Categories",
            difficulty="All", total_q=len(qs), correct_q=len(qs), incorrect_q=0,
            unanswered_q=0, score_marks=len(qs), max_marks=len(qs), percentage=100.0,
            passed=True, time_taken_seconds=42, answers_snapshot=answers_snapshot
        )
    else:
        att_id = attempts[0]['id']

    app.show_quiz_results(att_id)
    root.update()
    capture_window(root, 'assets/screenshots/fig_11_10_quiz_results.png')

    # 11. Answer Review Screen
    current_view = app.main_container.winfo_children()[0]
    if hasattr(current_view, 'show_answer_review_screen'):
        current_view.show_answer_review_screen()
        root.update()
        capture_window(root, 'assets/screenshots/fig_11_11_review_answers.png')

    # 12. Student Personal History
    app.show_user_history()
    root.update()
    capture_window(root, 'assets/screenshots/fig_11_12_student_history.png')

    root.destroy()
    print("ALL SCREENSHOTS CAPTURED SUCCESSFULLY!")


if __name__ == '__main__':
    main_capture()
