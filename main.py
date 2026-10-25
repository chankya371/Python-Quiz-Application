"""
main.py - Main Desktop Application Controller
Python Quiz Management System with Admin Dashboard & Student Portal
Features:
  - Role-based access control (Admin & Student panels)
  - Dedicated Admin Dashboard with sidebar navigation & Matplotlib analytics
  - Question CRUD, category management with safe deletion, user management
  - Global quiz settings configuration
  - Interactive quiz engine with real-time countdown timer & auto-submission
  - Question-by-question answer review with explanations
  - JSON question import/export and CSV result reporting
  - Permanent local SQLite storage (quiz.db)
"""

import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox

import database
import auth
from ui_common import THEME, FONTS, ModernButton, setup_ttk_styles
from admin.dashboard import AdminDashboardView
from admin.manage_questions import ManageQuestionsView
from admin.manage_categories import ManageCategoriesView
from admin.manage_users import ManageUsersView
from admin.view_results import ViewResultsView
from admin.settings import SettingsView
from user.home import UserHomeView
from user.take_quiz import TakeQuizView
from user.results import QuizResultView
from user.history import UserHistoryView


class QuizSystemApp:
    """The central application window and navigation controller."""

    def __init__(self, root):
        self.root = root
        self.root.title("Python Quiz Management System")
        self.root.configure(bg=THEME["bg_main"])
        self.root.minsize(1050, 720)

        # Initialize SQLite database schema and seed defaults
        database.init_database()

        # Global ttk styles
        setup_ttk_styles()

        # Session state
        self.current_user = None  # None or dict {id, username, full_name, role, ...}

        # Center window
        self._center_window(1100, 750)

        # Root layout container
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)

        self.main_container = tk.Frame(self.root, bg=THEME["bg_main"])
        self.main_container.grid(row=0, column=0, sticky="nsew")
        self.main_container.rowconfigure(0, weight=1)
        self.main_container.columnconfigure(0, weight=1)

        # Show initial login page
        self.show_login_view()

    def _center_window(self, width, height):
        self.root.update_idletasks()
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        x = max(0, (screen_w - width) // 2)
        y = max(0, (screen_h - height) // 2 - 25)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def _clear_container(self):
        for widget in self.main_container.winfo_children():
            widget.destroy()

    # ====================================================
    # 1. LOGIN & REGISTRATION CONTROLLERS
    # ====================================================
    def show_login_view(self):
        """Displays user/admin login interface with toggle tabs."""
        self._clear_container()
        self.current_user = None

        center_box = tk.Frame(self.main_container, bg=THEME["bg_main"])
        center_box.place(relx=0.5, rely=0.5, anchor="center")

        # App Brand Header
        brand_frame = tk.Frame(center_box, bg=THEME["bg_main"])
        brand_frame.pack(pady=(0, 20))

        tk.Label(brand_frame, text="🧠 Python Quiz System", font=FONTS["hero"],
                 bg=THEME["bg_main"], fg=THEME["text_primary"]).pack()
        tk.Label(brand_frame, text="Professional Quiz Management & Student Assessment Platform",
                 font=FONTS["body"], bg=THEME["bg_main"], fg=THEME["text_secondary"]).pack(pady=(4, 0))

        # Login Card Container
        card = tk.Frame(center_box, bg=THEME["bg_card"], bd=1, relief="ridge", padx=35, pady=25, width=460)
        card.pack(fill="x")

        # Tab Toggle Buttons: User Login vs. Admin Login
        tab_bar = tk.Frame(card, bg=THEME["bg_card"])
        tab_bar.pack(fill="x", pady=(0, 20))
        tab_bar.columnconfigure((0, 1), weight=1)

        self.login_mode = "user"  # "user" or "admin"

        def _switch_tab(mode):
            self.login_mode = mode
            if mode == "user":
                btn_tab_user.configure(bg=THEME["accent_primary"], fg="#ffffff")
                btn_tab_admin.configure(bg=THEME["bg_card_hover"], fg=THEME["text_secondary"])
                lbl_role_desc.configure(text="Sign in to take quizzes, track progress, and view leaderboards.")
                demo_note.configure(text="Demo Student: student / student123")
                reg_box.pack(fill="x", pady=(15, 0))
            else:
                btn_tab_admin.configure(bg=THEME["accent_primary"], fg="#ffffff")
                btn_tab_user.configure(bg=THEME["bg_card_hover"], fg=THEME["text_secondary"])
                lbl_role_desc.configure(text="Sign in to access admin analytics, question bank, and system settings.")
                demo_note.configure(text="Demo Admin: admin / admin123")
                reg_box.pack_forget()

        btn_tab_user = ModernButton(
            tab_bar, text="👤 Student Login",
            command=lambda: _switch_tab("user"),
            bg=THEME["accent_primary"], hover_bg=THEME["accent_primary_hover"],
            font=FONTS["button_sm"], padx=10, pady=8
        )
        btn_tab_user.grid(row=0, column=0, padx=(0, 4), sticky="nsew")

        btn_tab_admin = ModernButton(
            tab_bar, text="🛡️ Admin Portal",
            command=lambda: _switch_tab("admin"),
            bg=THEME["bg_card_hover"], hover_bg=THEME["accent_primary_hover"],
            font=FONTS["button_sm"], padx=10, pady=8
        )
        btn_tab_admin.grid(row=0, column=1, padx=(4, 0), sticky="nsew")

        lbl_role_desc = tk.Label(
            card, text="Sign in to take quizzes, track progress, and view leaderboards.",
            font=FONTS["meta"], bg=THEME["bg_card"], fg=THEME["text_accent"], wraplength=380, justify="center"
        )
        lbl_role_desc.pack(pady=(0, 15))

        # Username Field
        tk.Label(card, text="Username", font=FONTS["body_bold"], bg=THEME["bg_card"], fg=THEME["text_primary"]).pack(anchor="w")
        entry_user = tk.Entry(card, font=FONTS["body"], bg=THEME["bg_main"], fg=THEME["text_primary"],
                              insertbackground=THEME["text_primary"], bd=1, relief="solid", width=34)
        entry_user.pack(fill="x", pady=(2, 12))
        entry_user.focus_set()

        # Password Field
        tk.Label(card, text="Password", font=FONTS["body_bold"], bg=THEME["bg_card"], fg=THEME["text_primary"]).pack(anchor="w")
        entry_pass = tk.Entry(card, show="●", font=FONTS["body"], bg=THEME["bg_main"], fg=THEME["text_primary"],
                              insertbackground=THEME["text_primary"], bd=1, relief="solid", width=34)
        entry_pass.pack(fill="x", pady=(2, 18))

        def _handle_login():
            uname = entry_user.get().strip()
            pword = entry_pass.get().strip()

            if self.login_mode == "admin":
                admin_data, err = auth.authenticate_admin(uname, pword)
                if err:
                    messagebox.showerror("Admin Login Failed", err)
                else:
                    self.current_user = admin_data
                    self.show_admin_portal()
            else:
                user_data, err = auth.authenticate_user(uname, pword)
                if err:
                    messagebox.showerror("User Login Failed", err)
                else:
                    self.current_user = user_data
                    self.show_user_home()

        # Enter key triggers login
        entry_user.bind("<Return>", lambda e: _handle_login())
        entry_pass.bind("<Return>", lambda e: _handle_login())

        # Sign In Button
        btn_login = ModernButton(
            card, text="🔐 Sign In", command=_handle_login,
            bg=THEME["accent_primary"], hover_bg=THEME["accent_primary_hover"],
            font=FONTS["button"], pady=9
        )
        btn_login.pack(fill="x")

        # Demo Credentials Note
        demo_note = tk.Label(
            card, text="Demo Student: student / student123",
            font=FONTS["meta"], bg=THEME["bg_card"], fg=THEME["text_secondary"]
        )
        demo_note.pack(pady=(12, 0))

        # Register Link (for users)
        reg_box = tk.Frame(card, bg=THEME["bg_card"])
        reg_box.pack(fill="x", pady=(15, 0))

        tk.Label(reg_box, text="Don't have a student account? ", font=FONTS["meta"],
                 bg=THEME["bg_card"], fg=THEME["text_secondary"]).pack(side="left")

        lbl_reg_link = tk.Label(reg_box, text="Create Account", font=FONTS["body_bold"],
                                bg=THEME["bg_card"], fg=THEME["text_accent"], cursor="hand2")
        lbl_reg_link.pack(side="left")
        lbl_reg_link.bind("<Button-1>", lambda e: self.open_registration_modal())

    def open_registration_modal(self):
        """Modal dialog for new user account registration."""
        dlg = tk.Toplevel(self.root)
        dlg.title("Register Student Account")
        dlg.configure(bg=THEME["bg_main"])
        dlg.geometry("450x480")
        dlg.transient(self.root)
        dlg.grab_set()

        h_frame = tk.Frame(dlg, bg=THEME["bg_card"], padx=20, pady=12)
        h_frame.pack(fill="x")
        tk.Label(h_frame, text="Create Student Account", font=FONTS["h2"], bg=THEME["bg_card"], fg=THEME["text_primary"]).pack(anchor="w")
        tk.Label(h_frame, text="Register now to participate in quizzes and track your achievements",
                 font=FONTS["meta"], bg=THEME["bg_card"], fg=THEME["text_secondary"]).pack(anchor="w")

        body = tk.Frame(dlg, bg=THEME["bg_main"], padx=25, pady=15)
        body.pack(fill="both", expand=True)

        fields = {}
        for key, label in [("full_name", "Full Name *"), ("email", "Email Address"),
                           ("username", "Desired Username *"), ("password", "Password *")]:
            tk.Label(body, text=label, font=FONTS["body_bold"], bg=THEME["bg_main"], fg=THEME["text_primary"]).pack(anchor="w", pady=(4, 1))
            show_char = "●" if key == "password" else ""
            ent = tk.Entry(body, show=show_char, font=FONTS["body"], bg=THEME["bg_card"], fg=THEME["text_primary"],
                           insertbackground=THEME["text_primary"], bd=1, relief="solid")
            ent.pack(fill="x", pady=(0, 6))
            fields[key] = ent

        btn_bar = tk.Frame(body, bg=THEME["bg_main"])
        btn_bar.pack(fill="x", pady=(15, 0))

        def _do_register():
            fn = fields["full_name"].get().strip()
            em = fields["email"].get().strip()
            un = fields["username"].get().strip()
            pw = fields["password"].get().strip()

            success, err = auth.register_user(un, pw, fn, em)
            if not success:
                messagebox.showerror("Registration Error", err, parent=dlg)
            else:
                messagebox.showinfo("Account Created", "Your account has been successfully created! You may now sign in.", parent=dlg)
                dlg.destroy()

        btn_submit = ModernButton(btn_bar, text="Register Now", command=_do_register,
                                  bg=THEME["success"], hover_bg=THEME["success_hover"], font=FONTS["button_sm"], pady=7)
        btn_submit.pack(fill="x")

    def logout(self):
        """Logs out the active user or admin and returns to login screen."""
        if messagebox.askyesno("Confirm Logout", "Are you sure you want to log out?"):
            self.current_user = None
            self.show_login_view()

    # ====================================================
    # 2. ADMIN PORTAL (SIDEBAR + MAIN CONTENT AREA)
    # ====================================================
    def show_admin_portal(self):
        """Renders modern sidebar + content area for administrative management."""
        if not self.current_user or self.current_user.get("role") != "admin":
            self.show_login_view()
            return

        self._clear_container()

        admin_layout = tk.Frame(self.main_container, bg=THEME["bg_main"])
        admin_layout.pack(fill="both", expand=True)

        # ----------------------------------------------------
        # LEFT SIDEBAR
        # ----------------------------------------------------
        sidebar = tk.Frame(admin_layout, bg=THEME["bg_sidebar"], width=230)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        # Sidebar Header
        sb_header = tk.Frame(sidebar, bg=THEME["bg_sidebar"], padx=15, pady=18)
        sb_header.pack(fill="x")

        tk.Label(sb_header, text="🛡️ Admin Panel", font=FONTS["h2"],
                 bg=THEME["bg_sidebar"], fg=THEME["text_primary"]).pack(anchor="w")

        tk.Label(sb_header, text=f"Admin: @{self.current_user['username']}", font=FONTS["meta"],
                 bg=THEME["bg_sidebar"], fg=THEME["text_accent"]).pack(anchor="w", pady=(2, 0))

        tk.Frame(sidebar, bg=THEME["border"], height=1).pack(fill="x", padx=10, pady=(0, 10))

        # Content Area (Right)
        self.admin_content_area = tk.Frame(admin_layout, bg=THEME["bg_main"])
        self.admin_content_area.pack(side="left", fill="both", expand=True)

        # Navigation Menu Items
        self.sidebar_buttons = {}
        nav_items = [
            ("dashboard", "📊  Dashboard"),
            ("questions", "❓  Manage Questions"),
            ("categories", "📂  Manage Categories"),
            ("users", "👥  Manage Users"),
            ("results", "📝  Quiz Results"),
            ("settings", "⚙️  Quiz Settings")
        ]

        for view_key, label in nav_items:
            btn = tk.Button(
                sidebar,
                text=label,
                anchor="w",
                padx=16,
                pady=11,
                font=FONTS["body_bold"],
                bg=THEME["bg_sidebar"],
                fg=THEME["text_secondary"],
                activebackground=THEME["bg_sidebar_active"],
                activeforeground=THEME["text_primary"],
                bd=0,
                relief="flat",
                cursor="hand2",
                command=lambda k=view_key: self.navigate_admin(k)
            )
            btn.pack(fill="x")
            self.sidebar_buttons[view_key] = btn

        # Logout Button in bottom of sidebar
        tk.Frame(sidebar, bg=THEME["border"], height=1).pack(side="bottom", fill="x", padx=10, pady=(0, 10))

        btn_sb_logout = tk.Button(
            sidebar,
            text="🚪  Log Out",
            anchor="w",
            padx=16,
            pady=11,
            font=FONTS["body_bold"],
            bg=THEME["bg_sidebar"],
            fg=THEME["danger"],
            activebackground=THEME["danger_hover"],
            activeforeground="#ffffff",
            bd=0,
            relief="flat",
            cursor="hand2",
            command=self.logout
        )
        btn_sb_logout.pack(side="bottom", fill="x")

        # Initial view
        self.navigate_admin("dashboard")

    def navigate_admin(self, view_key):
        """Swaps the view inside admin_content_area and highlights sidebar button."""
        # Highlight active button
        for k, btn in self.sidebar_buttons.items():
            if k == view_key:
                btn.configure(bg=THEME["accent_primary"], fg="#ffffff")
            else:
                btn.configure(bg=THEME["bg_sidebar"], fg=THEME["text_secondary"])

        # Clear content area
        for widget in self.admin_content_area.winfo_children():
            widget.destroy()

        if view_key == "dashboard":
            view = AdminDashboardView(self.admin_content_area, self)
        elif view_key == "questions":
            view = ManageQuestionsView(self.admin_content_area, self)
        elif view_key == "categories":
            view = ManageCategoriesView(self.admin_content_area, self)
        elif view_key == "users":
            view = ManageUsersView(self.admin_content_area, self)
        elif view_key == "results":
            view = ViewResultsView(self.admin_content_area, self)
        elif view_key == "settings":
            view = SettingsView(self.admin_content_area, self)
        else:
            view = AdminDashboardView(self.admin_content_area, self)

        view.pack(fill="both", expand=True)

    # ====================================================
    # 3. STUDENT / USER PORTAL
    # ====================================================
    def show_user_home(self):
        """Displays user home dashboard."""
        if not self.current_user or self.current_user.get("role") != "user":
            self.show_login_view()
            return

        self._clear_container()
        view = UserHomeView(self.main_container, self, self.current_user)
        view.pack(fill="both", expand=True)

    def launch_quiz(self, category_id, category_name, difficulty, questions):
        """Launches a live quiz screen."""
        self._clear_container()
        view = TakeQuizView(self.main_container, self, self.current_user,
                            category_id, category_name, difficulty, questions)
        view.pack(fill="both", expand=True)

    def show_quiz_results(self, attempt_id):
        """Displays post-quiz results screen."""
        self._clear_container()
        view = QuizResultView(self.main_container, self, attempt_id)
        view.pack(fill="both", expand=True)

    def show_user_history(self):
        """Displays complete personal history for the logged in user."""
        self._clear_container()
        view = UserHistoryView(self.main_container, self, self.current_user)
        view.pack(fill="both", expand=True)


def main():
    root = tk.Tk()
    app = QuizSystemApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
