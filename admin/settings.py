"""
admin/settings.py - Global Quiz Configuration Settings Module
Allows the admin to configure quiz length, timer duration, passing score percentage,
randomized ordering, answer review permissions, and quiz retake permissions.
"""

import tkinter as tk
from tkinter import ttk, messagebox

import database
from ui_common import THEME, FONTS, ModernButton


class SettingsView(tk.Frame):
    """Admin view for configuring global quiz rules and runtime parameters."""

    def __init__(self, parent, controller):
        super().__init__(parent, bg=THEME["bg_main"])
        self.controller = controller

        # Header Title Bar
        header = tk.Frame(self, bg=THEME["bg_main"], padx=20, pady=15)
        header.pack(fill="x")

        title_box = tk.Frame(header, bg=THEME["bg_main"])
        title_box.pack(side="left")

        lbl_title = tk.Label(title_box, text="Quiz Settings & Configuration", font=FONTS["hero"], bg=THEME["bg_main"], fg=THEME["text_primary"])
        lbl_title.pack(anchor="w")

        lbl_sub = tk.Label(title_box, text="Configure global rules, timers, scoring thresholds, and quiz permissions",
                           font=FONTS["body"], bg=THEME["bg_main"], fg=THEME["text_secondary"])
        lbl_sub.pack(anchor="w")

        # Main Card Container
        card = tk.Frame(self, bg=THEME["bg_card"], bd=1, relief="ridge", padx=30, pady=25)
        card.pack(fill="x", padx=20, pady=10)

        # Load current settings from SQLite
        curr_settings = database.get_settings()

        # 1. Questions per Quiz
        r1 = tk.Frame(card, bg=THEME["bg_card"])
        r1.pack(fill="x", pady=8)
        tk.Label(r1, text="Number of Questions per Quiz:", width=30, anchor="w", font=FONTS["body_bold"],
                 bg=THEME["bg_card"], fg=THEME["text_primary"]).pack(side="left")
        self.var_q_count = tk.StringVar(value=curr_settings.get("questions_per_quiz", "10"))
        spin_q = tk.Spinbox(r1, from_=5, to=100, textvariable=self.var_q_count, width=8, font=FONTS["body"],
                            bg=THEME["bg_main"], fg=THEME["text_primary"], insertbackground=THEME["text_primary"], bd=1, relief="solid")
        spin_q.pack(side="left")
        tk.Label(r1, text=" questions (questions loaded per quiz attempt)", font=FONTS["meta"],
                 bg=THEME["bg_card"], fg=THEME["text_secondary"]).pack(side="left", padx=10)

        # 2. Timer Duration
        r2 = tk.Frame(card, bg=THEME["bg_card"])
        r2.pack(fill="x", pady=8)
        tk.Label(r2, text="Quiz Timer Duration (Minutes):", width=30, anchor="w", font=FONTS["body_bold"],
                 bg=THEME["bg_card"], fg=THEME["text_primary"]).pack(side="left")
        self.var_timer = tk.StringVar(value=curr_settings.get("timer_minutes", "10"))
        spin_timer = tk.Spinbox(r2, from_=1, to=180, textvariable=self.var_timer, width=8, font=FONTS["body"],
                                bg=THEME["bg_main"], fg=THEME["text_primary"], insertbackground=THEME["text_primary"], bd=1, relief="solid")
        spin_timer.pack(side="left")
        tk.Label(r2, text=" minutes (quiz automatically submits when time expires)", font=FONTS["meta"],
                 bg=THEME["bg_card"], fg=THEME["text_secondary"]).pack(side="left", padx=10)

        # 3. Passing Percentage
        r3 = tk.Frame(card, bg=THEME["bg_card"])
        r3.pack(fill="x", pady=8)
        tk.Label(r3, text="Passing Score Threshold (%):", width=30, anchor="w", font=FONTS["body_bold"],
                 bg=THEME["bg_card"], fg=THEME["text_primary"]).pack(side="left")
        self.var_pass = tk.StringVar(value=curr_settings.get("passing_percentage", "60"))
        spin_pass = tk.Spinbox(r3, from_=10, to=100, textvariable=self.var_pass, width=8, font=FONTS["body"],
                               bg=THEME["bg_main"], fg=THEME["text_primary"], insertbackground=THEME["text_primary"], bd=1, relief="solid")
        spin_pass.pack(side="left")
        tk.Label(r3, text=" % required to earn a passing result", font=FONTS["meta"],
                 bg=THEME["bg_card"], fg=THEME["text_secondary"]).pack(side="left", padx=10)

        # Divider
        tk.Frame(card, bg=THEME["border"], height=1).pack(fill="x", pady=15)

        # 4. Checkbox: Randomize Question Order
        self.var_random = tk.BooleanVar(value=curr_settings.get("randomize_questions", "true").lower() == "true")
        chk_random = tk.Checkbutton(
            card,
            text="Randomize Question Order (Shuffles questions randomly for every quiz attempt)",
            variable=self.var_random,
            bg=THEME["bg_card"],
            fg=THEME["text_primary"],
            selectcolor=THEME["bg_main"],
            activebackground=THEME["bg_card"],
            font=FONTS["body"]
        )
        chk_random.pack(anchor="w", pady=4)

        # 5. Checkbox: Show Correct Answers after Submission
        self.var_show_ans = tk.BooleanVar(value=curr_settings.get("show_answers_after_submission", "true").lower() == "true")
        chk_ans = tk.Checkbutton(
            card,
            text="Display Correct Answers & Explanations to users in post-quiz review mode",
            variable=self.var_show_ans,
            bg=THEME["bg_card"],
            fg=THEME["text_primary"],
            selectcolor=THEME["bg_main"],
            activebackground=THEME["bg_card"],
            font=FONTS["body"]
        )
        chk_ans.pack(anchor="w", pady=4)

        # 6. Checkbox: Allow Quiz Retakes
        self.var_retakes = tk.BooleanVar(value=curr_settings.get("allow_retakes", "true").lower() == "true")
        chk_retakes = tk.Checkbutton(
            card,
            text="Allow Users to Retake Quizzes (Enables the 'Retake Quiz' button on results screen)",
            variable=self.var_retakes,
            bg=THEME["bg_card"],
            fg=THEME["text_primary"],
            selectcolor=THEME["bg_main"],
            activebackground=THEME["bg_card"],
            font=FONTS["body"]
        )
        chk_retakes.pack(anchor="w", pady=4)

        # Save Button
        tk.Frame(card, bg=THEME["border"], height=1).pack(fill="x", pady=15)

        btn_save = ModernButton(
            card,
            text="💾 Save All Settings",
            command=self.save_settings,
            bg=THEME["success"],
            hover_bg=THEME["success_hover"],
            font=FONTS["button"],
            padx=20,
            pady=8
        )
        btn_save.pack(anchor="w")

    def save_settings(self):
        """Validates and saves settings into SQLite."""
        try:
            q_count = int(self.var_q_count.get().strip())
            if q_count < 1:
                raise ValueError("Questions per quiz must be at least 1.")
        except ValueError:
            messagebox.showwarning("Validation Error", "Questions per quiz must be a valid positive number.")
            return

        try:
            timer_val = int(self.var_timer.get().strip())
            if timer_val < 1:
                raise ValueError("Timer duration must be at least 1 minute.")
        except ValueError:
            messagebox.showwarning("Validation Error", "Timer duration must be a valid positive number.")
            return

        try:
            pass_val = int(self.var_pass.get().strip())
            if not (1 <= pass_val <= 100):
                raise ValueError("Passing percentage must be between 1 and 100.")
        except ValueError:
            messagebox.showwarning("Validation Error", "Passing percentage must be between 1 and 100.")
            return

        new_settings = {
            "questions_per_quiz": str(q_count),
            "timer_minutes": str(timer_val),
            "passing_percentage": str(pass_val),
            "randomize_questions": "true" if self.var_random.get() else "false",
            "show_answers_after_submission": "true" if self.var_show_ans.get() else "false",
            "allow_retakes": "true" if self.var_retakes.get() else "false"
        }

        database.update_settings(new_settings)
        messagebox.showinfo("Settings Saved", "Quiz settings have been successfully updated and saved to SQLite!")
