"""
user/home.py - User / Student Landing Dashboard
Displays personalized welcome banner, user performance metrics,
interactive category cards, difficulty selector, recent history, and real leaderboard.
"""

import tkinter as tk
from tkinter import ttk, messagebox

import database
from ui_common import THEME, FONTS, ModernButton, StatCard, ScrollableFrame


CATEGORY_ICONS = {
    "python": "🐍",
    "computer basics": "💻",
    "general knowledge": "🌍",
    "computer science": "⚙️",
    "mathematics": "🔢",
    "networking": "🌐"
}


class UserHomeView(tk.Frame):
    """Student / User Home Dashboard."""

    def __init__(self, parent, controller, user_info):
        super().__init__(parent, bg=THEME["bg_main"])
        self.controller = controller
        self.user_info = user_info

        self.selected_category_id = "All"
        self.selected_category_name = "All Categories"
        self.selected_difficulty = "All"
        self.category_card_widgets = []

        self.scroll = ScrollableFrame(self, bg=THEME["bg_main"])
        self.scroll.pack(fill="both", expand=True)
        self.content = self.scroll.scrollable_content

        self.render_dashboard()

    def render_dashboard(self):
        """Draws the complete user dashboard."""
        for widget in self.content.winfo_children():
            widget.destroy()
        self.category_card_widgets.clear()

        # Fetch stats from SQLite
        user_stats = database.get_user_dashboard_stats(self.user_info["id"])
        categories = database.get_categories(with_counts=True)
        settings = database.get_settings()

        # ----------------------------------------------------
        # TOP HERO BANNER
        # ----------------------------------------------------
        hero = tk.Frame(self.content, bg=THEME["bg_card"], bd=1, relief="ridge", padx=25, pady=20)
        hero.pack(fill="x", padx=20, pady=(15, 12))

        top_row = tk.Frame(hero, bg=THEME["bg_card"])
        top_row.pack(fill="x")

        welcome_box = tk.Frame(top_row, bg=THEME["bg_card"])
        welcome_box.pack(side="left")

        tk.Label(welcome_box, text=f"Welcome back, {self.user_info.get('full_name', 'Student')}! 👋",
                 font=FONTS["hero"], bg=THEME["bg_card"], fg=THEME["text_primary"]).pack(anchor="w")

        tk.Label(welcome_box, text=f"Logged in as @{self.user_info['username']} • Ready to test your skills today?",
                 font=FONTS["body"], bg=THEME["bg_card"], fg=THEME["text_secondary"]).pack(anchor="w", pady=(2, 0))

        # Logout button in top-right of hero
        btn_logout = ModernButton(top_row, text="🚪 Log Out", command=self.controller.logout,
                                  bg=THEME["btn_nav"], hover_bg=THEME["danger_hover"],
                                  font=FONTS["button_sm"], padx=12, pady=6)
        btn_logout.pack(side="right")

        # ----------------------------------------------------
        # USER STAT CARDS
        # ----------------------------------------------------
        stats_frame = tk.Frame(self.content, bg=THEME["bg_main"], padx=20, pady=5)
        stats_frame.pack(fill="x")
        stats_frame.columnconfigure((0, 1, 2, 3), weight=1)

        stat_items = [
            ("Quizzes Taken", user_stats["total_attempts"], "📝", THEME["text_accent"]),
            ("Best Score", f"{user_stats['best_score']}%", "🏆", THEME["warning"]),
            ("Average Score", f"{user_stats['avg_score']}%", "📊", THEME["accent_primary"]),
            ("Quizzes Passed", user_stats["quizzes_passed"], "✅", THEME["success"])
        ]

        for col, (label, val, icon, color) in enumerate(stat_items):
            card = StatCard(stats_frame, title=label, value=val, icon=icon, color=color)
            card.grid(row=0, column=col, padx=6, pady=4, sticky="nsew")

        # ----------------------------------------------------
        # QUIZ LAUNCHER: CATEGORY & DIFFICULTY SELECTOR
        # ----------------------------------------------------
        launcher_card = tk.Frame(self.content, bg=THEME["bg_card"], bd=1, relief="ridge", padx=25, pady=20)
        launcher_card.pack(fill="x", padx=20, pady=15)

        tk.Label(launcher_card, text="🚀 Choose a Quiz Category & Start", font=FONTS["h1"],
                 bg=THEME["bg_card"], fg=THEME["text_primary"]).pack(anchor="w")

        q_per_quiz = settings.get("questions_per_quiz", "10")
        timer_mins = settings.get("timer_minutes", "10")
        pass_pct = settings.get("passing_percentage", "60")

        tk.Label(launcher_card,
                 text=f"Standard format: {q_per_quiz} questions  •  {timer_mins} minutes countdown timer  •  Passing mark: {pass_pct}%",
                 font=FONTS["meta"], bg=THEME["bg_card"], fg=THEME["text_accent"]).pack(anchor="w", pady=(2, 14))

        # Category Cards Grid
        cat_grid = tk.Frame(launcher_card, bg=THEME["bg_card"])
        cat_grid.pack(fill="x", pady=(0, 15))
        cat_grid.columnconfigure((0, 1, 2, 3), weight=1)

        # "All Categories" card first
        total_active_all = sum(c.get("active_question_count", 0) or 0 for c in categories)
        self._create_category_card(cat_grid, row=0, col=0, cat_id="All",
                                  name="All Categories", count=total_active_all, icon="🎯")

        # Specific category cards
        for idx, c in enumerate(categories, start=1):
            row_idx = idx // 4
            col_idx = idx % 4
            c_icon = CATEGORY_ICONS.get(c["name"].lower(), "📂")
            self._create_category_card(cat_grid, row=row_idx, col=col_idx, cat_id=c["id"],
                                      name=c["name"], count=c.get("active_question_count", 0) or 0, icon=c_icon)

        # Difficulty & Start Row
        diff_row = tk.Frame(launcher_card, bg=THEME["bg_card"])
        diff_row.pack(fill="x", pady=(5, 0))

        tk.Label(diff_row, text="Difficulty Level:", font=FONTS["body_bold"],
                 bg=THEME["bg_card"], fg=THEME["text_primary"]).pack(side="left", padx=(0, 8))

        self.diff_var = tk.StringVar(value="All")
        for d in ("All", "Easy", "Medium", "Hard"):
            rb = tk.Radiobutton(diff_row, text=d, value=d, variable=self.diff_var,
                                font=FONTS["body"], bg=THEME["bg_card"], fg=THEME["text_primary"],
                                selectcolor=THEME["bg_main"], activebackground=THEME["bg_card"])
            rb.pack(side="left", padx=8)

        # Start Quiz Button
        btn_start = ModernButton(
            diff_row,
            text="🚀  Begin Quiz Now",
            command=self.start_quiz,
            bg=THEME["success"],
            hover_bg=THEME["success_hover"],
            font=FONTS["button"],
            padx=20,
            pady=8
        )
        btn_start.pack(side="right")

        # ----------------------------------------------------
        # BOTTOM TWO-COLUMN: RECENT ATTEMPTS & LEADERBOARD
        # ----------------------------------------------------
        bottom_frame = tk.Frame(self.content, bg=THEME["bg_main"], padx=20, pady=5)
        bottom_frame.pack(fill="both", expand=True, pady=(0, 25))
        bottom_frame.columnconfigure((0, 1), weight=1)

        # Left Column: Recent Attempts
        left_box = tk.Frame(bottom_frame, bg=THEME["bg_card"], bd=1, relief="ridge", padx=16, pady=14)
        left_box.grid(row=0, column=0, padx=(0, 8), sticky="nsew")

        lh_row = tk.Frame(left_box, bg=THEME["bg_card"])
        lh_row.pack(fill="x", pady=(0, 8))

        tk.Label(lh_row, text="📜 My Recent Quiz History", font=FONTS["h2"],
                 bg=THEME["bg_card"], fg=THEME["text_primary"]).pack(side="left")

        btn_all_hist = ModernButton(lh_row, text="View All History",
                                    command=lambda: self.controller.show_user_history(),
                                    bg=THEME["btn_nav"], hover_bg=THEME["btn_nav_hover"],
                                    font=FONTS["button_sm"], padx=10, pady=4)
        btn_all_hist.pack(side="right")

        # Treeview for user recent attempts
        my_attempts = database.get_user_attempts(self.user_info["id"], limit=5)
        t_left = ttk.Treeview(left_box, columns=("cat", "score", "pct", "res", "date"), show="headings", height=5)
        t_left.heading("cat", text="Category")
        t_left.heading("score", text="Score")
        t_left.heading("pct", text="%")
        t_left.heading("res", text="Result")
        t_left.heading("date", text="Date")

        t_left.column("cat", width=120, anchor="w")
        t_left.column("score", width=60, anchor="center")
        t_left.column("pct", width=55, anchor="center")
        t_left.column("res", width=70, anchor="center")
        t_left.column("date", width=110, anchor="center")
        t_left.pack(fill="both", expand=True)

        for a in my_attempts:
            t_left.insert("", "end", values=(
                a["category_name"] or "All",
                f"{a['score_marks']}/{a['max_marks']}",
                f"{a['percentage']}%",
                "Pass ✓" if a["passed"] else "Fail ✗",
                a["created_at"][:10]
            ))

        if not my_attempts:
            tk.Label(left_box, text="You have not completed any quizzes yet. Start one above!",
                     font=FONTS["body"], bg=THEME["bg_card"], fg=THEME["text_secondary"]).pack(pady=10)

        # Right Column: Leaderboard
        right_box = tk.Frame(bottom_frame, bg=THEME["bg_card"], bd=1, relief="ridge", padx=16, pady=14)
        right_box.grid(row=0, column=1, padx=(8, 0), sticky="nsew")

        tk.Label(right_box, text="🏆 Platform Leaderboard (Top Scorers)", font=FONTS["h2"],
                 bg=THEME["bg_card"], fg=THEME["text_accent"]).pack(anchor="w", pady=(0, 8))

        leaderboard = database.get_leaderboard(limit=5)
        t_lead = ttk.Treeview(right_box, columns=("rank", "user", "high", "avg", "quizzes"), show="headings", height=5)
        t_lead.heading("rank", text="Rank")
        t_lead.heading("user", text="User")
        t_lead.heading("high", text="High Score")
        t_lead.heading("avg", text="Avg Score")
        t_lead.heading("quizzes", text="Quizzes")

        t_lead.column("rank", width=45, anchor="center")
        t_lead.column("user", width=130, anchor="w")
        t_lead.column("high", width=80, anchor="center")
        t_lead.column("avg", width=80, anchor="center")
        t_lead.column("quizzes", width=65, anchor="center")
        t_lead.pack(fill="both", expand=True)

        medals = ["🥇", "🥈", "🥉", "4", "5"]
        for idx, row in enumerate(leaderboard):
            rank_str = medals[idx] if idx < len(medals) else str(idx + 1)
            t_lead.insert("", "end", values=(
                rank_str,
                row["username"],
                f"{row['high_score']}%",
                f"{row['avg_score']}%",
                row["attempts"]
            ))

        if not leaderboard:
            tk.Label(right_box, text="Leaderboard will populate as students complete quizzes.",
                     font=FONTS["body"], bg=THEME["bg_card"], fg=THEME["text_secondary"]).pack(pady=10)

    def _create_category_card(self, parent, row, col, cat_id, name, count, icon):
        """Creates an interactive selectable category card."""
        is_selected = (str(self.selected_category_id) == str(cat_id))
        border_col = THEME["border_selected"] if is_selected else THEME["border"]
        bg_col = THEME["bg_selected"] if is_selected else THEME["bg_main"]

        card = tk.Frame(parent, bg=bg_col, bd=2, relief="groove", cursor="hand2", padx=12, pady=10)
        card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")

        top_f = tk.Frame(card, bg=bg_col)
        top_f.pack(fill="x")

        lbl_icon = tk.Label(top_f, text=icon, font=(FONTS["h1"][0], 16), bg=bg_col, fg=THEME["text_accent"])
        lbl_icon.pack(side="left")

        lbl_count = tk.Label(top_f, text=f"{count} Qs", font=FONTS["meta"], bg=bg_col, fg=THEME["text_secondary"])
        lbl_count.pack(side="right")

        lbl_name = tk.Label(card, text=name, font=FONTS["body_bold"], bg=bg_col, fg=THEME["text_primary"],
                            wraplength=120, justify="left", anchor="w")
        lbl_name.pack(fill="x", pady=(4, 0))

        # Click handler
        def _on_click(_=None):
            self.selected_category_id = cat_id
            self.selected_category_name = name
            self._refresh_category_card_styles()

        for w in (card, top_f, lbl_icon, lbl_count, lbl_name):
            w.bind("<Button-1>", _on_click)

        self.category_card_widgets.append({
            "cat_id": str(cat_id),
            "card": card,
            "widgets": [card, top_f, lbl_icon, lbl_count, lbl_name]
        })

    def _refresh_category_card_styles(self):
        """Updates styling across all category cards when selection changes."""
        for item in self.category_card_widgets:
            is_sel = (item["cat_id"] == str(self.selected_category_id))
            bg_col = THEME["bg_selected"] if is_sel else THEME["bg_main"]
            border_col = THEME["border_selected"] if is_sel else THEME["border"]

            item["card"].configure(bg=border_col)
            for w in item["widgets"]:
                w.configure(bg=bg_col)

    def start_quiz(self):
        """Starts quiz after verifying question availability in SQLite."""
        settings = database.get_settings()
        limit = int(settings.get("questions_per_quiz", "10"))
        randomize = settings.get("randomize_questions", "true").lower() == "true"
        diff = self.diff_var.get()

        questions = database.get_active_questions_for_quiz(
            category_id=self.selected_category_id,
            difficulty=diff,
            limit=limit,
            randomize=randomize
        )

        if not questions:
            messagebox.showwarning(
                "No Questions Available",
                f"No active questions found for:\nCategory: {self.selected_category_name}\nDifficulty: {diff}\n\n"
                f"Please choose another category or difficulty, or ask an administrator to add questions."
            )
            return

        # Hand over to take_quiz view
        self.controller.launch_quiz(
            category_id=self.selected_category_id,
            category_name=self.selected_category_name,
            difficulty=diff,
            questions=questions
        )
