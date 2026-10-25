"""
user/results.py - Post-Quiz Results & Answer Review
Displays score card, pass/fail status, marks obtained, percentage,
time taken, and comprehensive question-by-question review with explanations.
"""

import tkinter as tk
from tkinter import ttk, messagebox

import database
from ui_common import THEME, FONTS, ModernButton, ScrollableFrame


class QuizResultView(tk.Frame):
    """Post-quiz performance breakdown and answer review view."""

    def __init__(self, parent, controller, attempt_id):
        super().__init__(parent, bg=THEME["bg_main"])
        self.controller = controller
        self.attempt_id = attempt_id

        self.attempt, self.answers = database.get_attempt_details(attempt_id)
        self.settings = database.get_settings()

        self.render_result_screen()

    def render_result_screen(self):
        for widget in self.winfo_children():
            widget.destroy()

        if not self.attempt:
            tk.Label(self, text="Error: Could not retrieve quiz attempt record.",
                     font=FONTS["h1"], bg=THEME["bg_main"], fg=THEME["danger"]).pack(pady=40)
            return

        frame = tk.Frame(self, bg=THEME["bg_main"], padx=35, pady=20)
        frame.pack(fill="both", expand=True)

        # Result Banner / Grade
        is_pass = bool(self.attempt["passed"])
        status_color = THEME["success"] if is_pass else THEME["danger"]
        status_text = "🎉 Congratulations, You Passed!" if is_pass else "📚 Quiz Not Passed - Keep Practicing!"

        badge = tk.Label(
            frame,
            text=f"  {status_text}  ",
            font=FONTS["h1"],
            bg=THEME["bg_card"],
            fg=status_color,
            bd=1,
            relief="ridge",
            padx=16,
            pady=6
        )
        badge.pack(pady=(0, 15))

        # Main Score Hero Card
        hero = tk.Frame(frame, bg=THEME["bg_card"], bd=1, relief="ridge", padx=30, pady=20)
        hero.pack(fill="x", padx=40, pady=(0, 15))

        score_lbl = tk.Label(
            hero,
            text=f"{self.attempt['percentage']}%",
            font=(FONTS["hero"][0], 46, "bold"),
            bg=THEME["bg_card"],
            fg=status_color
        )
        score_lbl.pack()

        time_str = f"{self.attempt['time_taken_seconds'] // 60}m {self.attempt['time_taken_seconds'] % 60}s"
        sub_text = (
            f"Marks Obtained: {self.attempt['score_marks']} / {self.attempt['max_marks']} Points  •  "
            f"Time Taken: {time_str}  •  Passing Threshold: {self.settings.get('passing_percentage', '60')}%"
        )
        tk.Label(hero, text=sub_text, font=FONTS["body"], bg=THEME["bg_card"], fg=THEME["text_primary"]).pack(pady=(4, 0))

        # 4 Stat Breakdown Cards
        stats_frame = tk.Frame(frame, bg=THEME["bg_main"])
        stats_frame.pack(fill="x", padx=40, pady=(0, 20))
        stats_frame.columnconfigure((0, 1, 2, 3), weight=1)

        breakdown_items = [
            ("Total Questions", str(self.attempt["total_questions"]), THEME["text_primary"]),
            ("Correct Answers", str(self.attempt["correct_answers"]), THEME["success"]),
            ("Incorrect Answers", str(self.attempt["incorrect_answers"]), THEME["danger"]),
            ("Unanswered", str(self.attempt["unanswered"]), THEME["warning"])
        ]

        for col, (label, val, color) in enumerate(breakdown_items):
            box = tk.Frame(stats_frame, bg=THEME["bg_card"], padx=14, pady=12, bd=1, relief="groove")
            box.grid(row=0, column=col, padx=6, sticky="nsew")

            tk.Label(box, text=val, font=FONTS["stat_num"], bg=THEME["bg_card"], fg=color).pack()
            tk.Label(box, text=label, font=FONTS["stat_lbl"], bg=THEME["bg_card"], fg=THEME["text_secondary"]).pack()

        # Action Buttons
        btn_box = tk.Frame(frame, bg=THEME["bg_main"])
        btn_box.pack(pady=10)

        # Allow Retakes setting check
        allow_retakes = self.settings.get("allow_retakes", "true").lower() == "true"
        if allow_retakes:
            btn_retake = ModernButton(
                btn_box,
                text="🔄  Retake Quiz",
                command=self.retake_quiz,
                bg=THEME["accent_primary"],
                hover_bg=THEME["accent_primary_hover"],
                width=16
            )
            btn_retake.pack(side="left", padx=8)

        # Show Answers setting check
        show_review = self.settings.get("show_answers_after_submission", "true").lower() == "true"
        if show_review:
            btn_review = ModernButton(
                btn_box,
                text="🔍  Review Answers",
                command=self.show_answer_review_screen,
                bg=THEME["btn_nav"],
                hover_bg=THEME["btn_nav_hover"],
                width=16
            )
            btn_review.pack(side="left", padx=8)

        btn_home = ModernButton(
            btn_box,
            text="🏠  Dashboard",
            command=self.controller.show_user_home,
            bg=THEME["btn_nav"],
            hover_bg=THEME["btn_nav_hover"],
            width=16
        )
        btn_home.pack(side="left", padx=8)

    def retake_quiz(self):
        """Launches a fresh quiz with the same category and difficulty settings."""
        cat_id = self.attempt["category_id"] or "All"
        cat_name = self.attempt["category_name"] or "All Categories"
        diff = self.attempt["difficulty"] or "All"

        settings = database.get_settings()
        limit = int(settings.get("questions_per_quiz", "10"))
        randomize = settings.get("randomize_questions", "true").lower() == "true"

        questions = database.get_active_questions_for_quiz(
            category_id=cat_id,
            difficulty=diff,
            limit=limit,
            randomize=randomize
        )

        if not questions:
            messagebox.showwarning("Error", "Could not load questions for retake.")
            return

        self.controller.launch_quiz(
            category_id=cat_id,
            category_name=cat_name,
            difficulty=diff,
            questions=questions
        )

    def show_answer_review_screen(self):
        """Displays full scrollable answer-by-answer review view."""
        for widget in self.winfo_children():
            widget.destroy()

        outer = tk.Frame(self, bg=THEME["bg_main"], padx=25, pady=15)
        outer.pack(fill="both", expand=True)

        top_bar = tk.Frame(outer, bg=THEME["bg_main"])
        top_bar.pack(fill="x", pady=(0, 12))

        tk.Label(top_bar, text="Question Review & Explanations", font=FONTS["hero"],
                 bg=THEME["bg_main"], fg=THEME["text_primary"]).pack(side="left")

        btn_back = ModernButton(top_bar, text="◀ Back to Score Summary", command=self.render_result_screen,
                                bg=THEME["btn_nav"], hover_bg=THEME["btn_nav_hover"],
                                font=FONTS["button_sm"], padx=12, pady=5)
        btn_back.pack(side="right")

        scroll = ScrollableFrame(outer, bg=THEME["bg_main"])
        scroll.pack(fill="both", expand=True)
        content = scroll.scrollable_content

        for idx, ans in enumerate(self.answers, start=1):
            is_corr = ans["is_correct"] == 1
            has_ans = bool(ans["user_answer"])

            box = tk.Frame(content, bg=THEME["bg_card"], bd=1, relief="ridge", padx=18, pady=14)
            box.pack(fill="x", pady=6, padx=10)

            ch = tk.Frame(box, bg=THEME["bg_card"])
            ch.pack(fill="x", pady=(0, 6))

            tk.Label(ch, text=f"Q{idx}. {ans['question_text']}", font=FONTS["h3"],
                     bg=THEME["bg_card"], fg=THEME["text_primary"], wraplength=580, justify="left").pack(side="left")

            res_col = THEME["success"] if is_corr else (THEME["warning"] if not has_ans else THEME["danger"])
            res_txt = "✓ Correct" if is_corr else ("⚠️ Unanswered" if not has_ans else "✗ Incorrect")
            tk.Label(ch, text=res_txt, font=FONTS["body_bold"], bg=THEME["bg_card"], fg=res_col).pack(side="right")

            # Option list
            opts_box = tk.Frame(box, bg=THEME["bg_card"])
            opts_box.pack(fill="x", pady=(4, 4))

            for letter in ("A", "B", "C", "D"):
                opt_val = ans[f"option_{letter.lower()}"]
                fg_col = THEME["text_secondary"]
                prefix = f"  {letter}. "

                if ans["correct_answer"] == letter:
                    fg_col = THEME["success"]
                    prefix = f"  {letter}. [CORRECT ANSWER] "
                if ans["user_answer"] == letter and not is_corr:
                    fg_col = THEME["danger"]
                    prefix = f"  {letter}. [YOUR ANSWER] "

                tk.Label(opts_box, text=f"{prefix}{opt_val}", font=FONTS["body"], bg=THEME["bg_card"], fg=fg_col).pack(anchor="w")

            if ans.get("explanation"):
                tk.Label(box, text=f"💡 Explanation: {ans['explanation']}", font=FONTS["meta"],
                         bg=THEME["bg_card"], fg=THEME["text_accent"], wraplength=660, justify="left").pack(anchor="w", pady=(6, 0))
