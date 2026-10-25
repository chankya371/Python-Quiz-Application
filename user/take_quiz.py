"""
user/take_quiz.py - Live Quiz Taking Screen
Presents questions one-by-one with 4 interactive options, Next/Previous navigation,
answer preservation, real-time countdown timer with auto-submit, and secure score calculation.
"""

import tkinter as tk
from tkinter import ttk, messagebox

import database
from ui_common import THEME, FONTS, ModernButton


class OptionChoiceCard(tk.Frame):
    """Interactive multiple-choice option card."""

    def __init__(self, parent, letter, text, on_click_callback):
        super().__init__(parent, bg=THEME["bg_card"], bd=1, relief="ridge", cursor="hand2")
        self.letter = letter
        self.text = text
        self.on_click = on_click_callback
        self.is_selected = False

        self.inner = tk.Frame(self, bg=THEME["bg_card"], padx=14, pady=12)
        self.inner.pack(fill="both", expand=True)

        # Badge: A, B, C, D
        self.badge = tk.Label(
            self.inner,
            text=f" {letter} ",
            font=FONTS["body_bold"],
            bg=THEME["bg_card_hover"],
            fg=THEME["text_accent"],
            padx=6,
            pady=3
        )
        self.badge.pack(side="left", padx=(0, 12))

        # Text
        self.label = tk.Label(
            self.inner,
            text=text,
            font=FONTS["body"],
            bg=THEME["bg_card"],
            fg=THEME["text_primary"],
            anchor="w",
            justify="left",
            wraplength=640
        )
        self.label.pack(side="left", fill="both", expand=True)

        # Radio indicator
        self.indicator = tk.Label(
            self.inner,
            text="○",
            font=(FONTS["body"][0], 14),
            bg=THEME["bg_card"],
            fg=THEME["text_secondary"]
        )
        self.indicator.pack(side="right", padx=(8, 4))

        for w in (self, self.inner, self.badge, self.label, self.indicator):
            w.bind("<Button-1>", lambda e: self.on_click(self.letter))
            w.bind("<Enter>", self._on_enter)
            w.bind("<Leave>", self._on_leave)

    def _on_enter(self, _):
        if not self.is_selected:
            self._apply_style(bg=THEME["bg_card_hover"], border=THEME["bg_card_hover"], badge_bg=THEME["accent_primary"])

    def _on_leave(self, _):
        if not self.is_selected:
            self._apply_style(bg=THEME["bg_card"], border=THEME["bg_card"], badge_bg=THEME["bg_card_hover"])

    def set_selected(self, selected=True):
        self.is_selected = selected
        if selected:
            self._apply_style(
                bg=THEME["bg_selected"],
                border=THEME["border_selected"],
                badge_bg=THEME["accent_primary"],
                indicator_text="●",
                indicator_fg=THEME["border_selected"]
            )
        else:
            self._apply_style(
                bg=THEME["bg_card"],
                border=THEME["bg_card"],
                badge_bg=THEME["bg_card_hover"],
                indicator_text="○",
                indicator_fg=THEME["text_secondary"]
            )

    def _apply_style(self, bg, border, badge_bg, indicator_text=None, indicator_fg=None):
        self.configure(bg=border)
        self.inner.configure(bg=bg)
        self.label.configure(bg=bg)
        self.indicator.configure(bg=bg)
        self.badge.configure(bg=badge_bg)
        if indicator_text is not None:
            self.indicator.configure(text=indicator_text)
        if indicator_fg is not None:
            self.indicator.configure(fg=indicator_fg)


class TakeQuizView(tk.Frame):
    """Full screen quiz runner with countdown timer and navigation."""

    def __init__(self, parent, controller, user_info, category_id, category_name, difficulty, questions):
        super().__init__(parent, bg=THEME["bg_main"])
        self.controller = controller
        self.user_info = user_info
        self.category_id = category_id
        self.category_name = category_name
        self.difficulty = difficulty
        self.questions = questions

        self.current_idx = 0
        self.user_answers = {}  # {question_index: 'A' | 'B' | 'C' | 'D'}
        self.is_submitted = False
        self.option_cards = []

        # Timer setup
        settings = database.get_settings()
        self.duration_seconds = int(settings.get("timer_minutes", "10")) * 60
        self.remaining_seconds = self.duration_seconds
        self.timer_job = None

        # Build UI
        self.render_quiz_screen()

        # Start timer tick
        self._start_timer()

    def _start_timer(self):
        """Ticks down every second."""
        if self.is_submitted:
            return

        if self.remaining_seconds <= 0:
            self.lbl_timer.configure(text="⏱️ 00:00 - TIME EXPIRED", fg=THEME["danger"])
            messagebox.showinfo("Time's Up!", "Your quiz time has expired. Submitting your answers automatically now...")
            self.submit_quiz(auto_submitted=True)
            return

        mins = self.remaining_seconds // 60
        secs = self.remaining_seconds % 60
        timer_str = f"⏱️ {mins:02d}:{secs:02d}"

        # Color warning when under 1 minute
        fg_col = THEME["danger"] if self.remaining_seconds < 60 else (THEME["warning"] if self.remaining_seconds < 180 else THEME["text_primary"])
        self.lbl_timer.configure(text=timer_str, fg=fg_col)

        self.remaining_seconds -= 1
        self.timer_job = self.after(1000, self._start_timer)

    def _cancel_timer(self):
        if self.timer_job:
            self.after_cancel(self.timer_job)
            self.timer_job = None

    def destroy(self):
        self._cancel_timer()
        super().destroy()

    def render_quiz_screen(self):
        """Draws current question, options, progress, and nav buttons."""
        for widget in self.winfo_children():
            widget.destroy()

        q_data = self.questions[self.current_idx]
        total_q = len(self.questions)
        q_num = self.current_idx + 1

        outer = tk.Frame(self, bg=THEME["bg_main"], padx=35, pady=20)
        outer.pack(fill="both", expand=True)

        # Header Bar: Question Counter, Category, Timer
        h_row = tk.Frame(outer, bg=THEME["bg_main"])
        h_row.pack(fill="x", pady=(0, 6))

        tk.Label(h_row, text=f"Question {q_num} of {total_q}", font=FONTS["h1"],
                 bg=THEME["bg_main"], fg=THEME["text_primary"]).pack(side="left")

        # Category Badge
        tk.Label(h_row, text=f" {q_data.get('category_name', self.category_name)} • {q_data.get('difficulty', 'Medium')} ",
                 font=FONTS["meta"], bg=THEME["bg_card"], fg=THEME["text_accent"],
                 bd=1, relief="ridge", padx=8, pady=3).pack(side="left", padx=15)

        # Timer Display
        mins = self.remaining_seconds // 60
        secs = self.remaining_seconds % 60
        self.lbl_timer = tk.Label(h_row, text=f"⏱️ {mins:02d}:{secs:02d}", font=FONTS["h2"],
                                  bg=THEME["bg_main"], fg=THEME["text_primary"])
        self.lbl_timer.pack(side="right")

        # Answered counter
        ans_count = len(self.user_answers)
        tk.Label(h_row, text=f"Answered: {ans_count}/{total_q}", font=FONTS["body_bold"],
                 bg=THEME["bg_main"], fg=THEME["text_secondary"]).pack(side="right", padx=15)

        # Progress Bar
        progress_val = (q_num / total_q) * 100
        pb = ttk.Progressbar(outer, orient="horizontal", style="Modern.Horizontal.TProgressbar", value=progress_val)
        pb.pack(fill="x", pady=(8, 15))

        # Question Card Box
        q_box = tk.Frame(outer, bg=THEME["bg_card"], bd=1, relief="ridge", padx=22, pady=18)
        q_box.pack(fill="x", pady=(0, 15))

        top_q_f = tk.Frame(q_box, bg=THEME["bg_card"])
        top_q_f.pack(fill="x", pady=(0, 6))

        tk.Label(top_q_f, text=f"Points: {q_data.get('marks', 1)} Mark(s)", font=FONTS["meta"],
                 bg=THEME["bg_card_hover"], fg=THEME["text_accent"], padx=6, pady=2).pack(side="right")

        tk.Label(q_box, text=q_data["question_text"], font=FONTS["h2"], bg=THEME["bg_card"],
                 fg=THEME["text_primary"], wraplength=760, justify="left", anchor="w").pack(fill="x")

        # Options Container
        opts_frame = tk.Frame(outer, bg=THEME["bg_main"])
        opts_frame.pack(fill="both", expand=True)

        self.option_cards = []
        selected_letter = self.user_answers.get(self.current_idx)

        options_map = [
            ("A", q_data["option_a"]),
            ("B", q_data["option_b"]),
            ("C", q_data["option_c"]),
            ("D", q_data["option_d"])
        ]

        for letter, text in options_map:
            card = OptionChoiceCard(
                opts_frame,
                letter=letter,
                text=text,
                on_click_callback=self.select_option
            )
            card.pack(fill="x", pady=5)
            if selected_letter == letter:
                card.set_selected(True)
            self.option_cards.append(card)

        # Navigation Footer
        nav_frame = tk.Frame(outer, bg=THEME["bg_main"], pady=12)
        nav_frame.pack(fill="x")

        # Previous Button
        btn_prev = ModernButton(nav_frame, text="◀  Previous", command=self.prev_question,
                                bg=THEME["btn_nav"], hover_bg=THEME["btn_nav_hover"], width=13)
        btn_prev.pack(side="left")
        if self.current_idx == 0:
            btn_prev.configure(state=tk.DISABLED, bg="#1e293b", fg="#475569", cursor="arrow")

        # Next Button (or Submit if last question)
        if self.current_idx < total_q - 1:
            btn_next = ModernButton(nav_frame, text="Next  ▶", command=self.next_question,
                                    bg=THEME["accent_primary"], hover_bg=THEME["accent_primary_hover"], width=13)
            btn_next.pack(side="right")

            # Early Finish Button
            btn_submit_early = ModernButton(nav_frame, text="Submit Quiz 🏁", command=self.confirm_and_submit,
                                            bg=THEME["bg_card"], hover_bg=THEME["bg_card_hover"],
                                            fg=THEME["text_secondary"], font=FONTS["button_sm"], width=14)
            btn_submit_early.pack(side="right", padx=10)
        else:
            btn_submit = ModernButton(nav_frame, text="Finish & Submit Quiz 🏁", command=self.confirm_and_submit,
                                      bg=THEME["success"], hover_bg=THEME["success_hover"], width=20)
            btn_submit.pack(side="right")

        # Abandon Quiz Button
        btn_abandon = ModernButton(nav_frame, text="❌ Leave Quiz", command=self.confirm_abandon,
                                   bg=THEME["bg_card"], hover_bg=THEME["danger_hover"],
                                   fg=THEME["text_secondary"], font=FONTS["button_sm"], width=12)
        btn_abandon.pack(side="left", padx=12)

    def select_option(self, letter):
        """User clicked an option card."""
        self.user_answers[self.current_idx] = letter
        for card in self.option_cards:
            card.set_selected(card.letter == letter)

    def next_question(self):
        if self.current_idx < len(self.questions) - 1:
            self.current_idx += 1
            self.render_quiz_screen()

    def prev_question(self):
        if self.current_idx > 0:
            self.current_idx -= 1
            self.render_quiz_screen()

    def confirm_abandon(self):
        confirm = messagebox.askyesno(
            "Quit Quiz?",
            "Are you sure you want to exit? Your progress in this quiz session will be discarded.",
            icon="warning"
        )
        if confirm:
            self._cancel_timer()
            self.controller.show_user_home()

    def confirm_and_submit(self):
        """Confirms submission with warning if unanswered questions remain."""
        if self.is_submitted:
            return

        total_q = len(self.questions)
        unanswered = total_q - len(self.user_answers)

        if unanswered > 0:
            msg = (
                f"You have {unanswered} unanswered question{'s' if unanswered != 1 else ''} "
                f"out of {total_q}.\n\n"
                f"Are you sure you want to finish and submit your quiz now?"
            )
            proceed = messagebox.askyesno("Incomplete Quiz", msg, icon="warning")
            if not proceed:
                return

        self.submit_quiz(auto_submitted=False)

    def submit_quiz(self, auto_submitted=False):
        """Calculates final score and commits attempt record and answer snapshots to SQLite."""
        if self.is_submitted:
            return
        self.is_submitted = True
        self._cancel_timer()

        time_taken = self.duration_seconds - max(0, self.remaining_seconds)
        total_q = len(self.questions)
        correct_count = 0
        incorrect_count = 0
        unanswered_count = 0
        score_marks = 0
        max_marks = 0

        settings = database.get_settings()
        pass_threshold = float(settings.get("passing_percentage", "60"))

        answers_snapshot = []

        for idx, q_data in enumerate(self.questions):
            marks_weight = int(q_data.get("marks", 1))
            max_marks += marks_weight
            user_choice = self.user_answers.get(idx)
            correct_choice = q_data["correct_answer"].strip().upper()

            is_correct = False
            awarded = 0

            if user_choice is None:
                unanswered_count += 1
            elif user_choice.strip().upper() == correct_choice:
                correct_count += 1
                is_correct = True
                awarded = marks_weight
                score_marks += marks_weight
            else:
                incorrect_count += 1

            answers_snapshot.append({
                "question_id": q_data.get("id"),
                "question_text": q_data["question_text"],
                "option_a": q_data["option_a"],
                "option_b": q_data["option_b"],
                "option_c": q_data["option_c"],
                "option_d": q_data["option_d"],
                "correct_answer": correct_choice,
                "user_answer": user_choice,
                "is_correct": is_correct,
                "marks_awarded": awarded,
                "explanation": q_data.get("explanation", "")
            })

        percentage = round((score_marks / max_marks * 100), 1) if max_marks > 0 else 0.0
        passed = percentage >= pass_threshold

        cat_id_val = None if self.category_id == "All" else int(self.category_id)

        # Save to SQLite
        attempt_id, err = database.record_quiz_attempt(
            user_id=self.user_info["id"],
            category_id=cat_id_val,
            category_name=self.category_name,
            difficulty=self.difficulty,
            total_q=total_q,
            correct_q=correct_count,
            incorrect_q=incorrect_count,
            unanswered_q=unanswered_count,
            score_marks=score_marks,
            max_marks=max_marks,
            percentage=percentage,
            passed=passed,
            time_taken_seconds=time_taken,
            answers_snapshot=answers_snapshot
        )

        if err:
            messagebox.showerror("Save Error", f"Could not record quiz attempt: {err}")

        # Transition to Result View
        self.controller.show_quiz_results(attempt_id=attempt_id)
