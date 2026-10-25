"""
user/history.py - Student Personal Quiz History
Allows a logged-in student to review their historical attempts, scores, and breakdowns.
Ensures users only see their own records.
"""

import tkinter as tk
from tkinter import ttk, messagebox

import database
from ui_common import THEME, FONTS, ModernButton, ScrollableFrame


class UserHistoryView(tk.Frame):
    """Personal quiz attempt history for the logged-in user."""

    def __init__(self, parent, controller, user_info):
        super().__init__(parent, bg=THEME["bg_main"])
        self.controller = controller
        self.user_info = user_info

        # Header Title Bar
        header = tk.Frame(self, bg=THEME["bg_main"], padx=20, pady=15)
        header.pack(fill="x")

        title_box = tk.Frame(header, bg=THEME["bg_main"])
        title_box.pack(side="left")

        lbl_title = tk.Label(title_box, text="My Quiz History", font=FONTS["hero"], bg=THEME["bg_main"], fg=THEME["text_primary"])
        lbl_title.pack(anchor="w")

        lbl_sub = tk.Label(title_box, text=f"Review your historical quiz attempts and progress (@{user_info['username']})",
                           font=FONTS["body"], bg=THEME["bg_main"], fg=THEME["text_secondary"])
        lbl_sub.pack(anchor="w")

        btn_back = ModernButton(header, text="🏠 Back to Dashboard", command=self.controller.show_user_home,
                                bg=THEME["btn_nav"], hover_bg=THEME["btn_nav_hover"],
                                font=FONTS["button_sm"], padx=14, pady=6)
        btn_back.pack(side="right")

        # Table
        table_frame = tk.Frame(self, bg=THEME["bg_main"], padx=20)
        table_frame.pack(fill="both", expand=True)

        cols = ("id", "category", "difficulty", "score", "percentage", "status", "time", "date")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=15)

        self.tree.heading("id", text="Attempt ID")
        self.tree.heading("category", text="Category")
        self.tree.heading("difficulty", text="Difficulty")
        self.tree.heading("score", text="Score (Marks)")
        self.tree.heading("percentage", text="Percentage")
        self.tree.heading("status", text="Result")
        self.tree.heading("time", text="Time Taken")
        self.tree.heading("date", text="Attempt Date")

        self.tree.column("id", width=70, anchor="center")
        self.tree.column("category", width=160, anchor="w")
        self.tree.column("difficulty", width=90, anchor="center")
        self.tree.column("score", width=90, anchor="center")
        self.tree.column("percentage", width=90, anchor="center")
        self.tree.column("status", width=90, anchor="center")
        self.tree.column("time", width=90, anchor="center")
        self.tree.column("date", width=140, anchor="center")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind("<Double-1>", lambda e: self.view_details())

        # Footer Actions
        footer = tk.Frame(self, bg=THEME["bg_main"], padx=20, pady=12)
        footer.pack(fill="x")

        btn_view = ModernButton(footer, text="🔍 View Details & Answer Key", command=self.view_details,
                                bg=THEME["accent_primary"], hover_bg=THEME["accent_primary_hover"],
                                font=FONTS["button_sm"], padx=14, pady=6)
        btn_view.pack(side="left", padx=4)

        self.lbl_count = tk.Label(footer, text="", font=FONTS["meta"], bg=THEME["bg_main"], fg=THEME["text_accent"])
        self.lbl_count.pack(side="right")

        self.load_history()

    def load_history(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        attempts = database.get_user_attempts(self.user_info["id"], limit=100)
        for a in attempts:
            status_text = "Passed ✓" if a["passed"] == 1 else "Failed ✗"
            time_str = f"{a['time_taken_seconds'] // 60}m {a['time_taken_seconds'] % 60}s"
            self.tree.insert("", "end", values=(
                f"#{a['id']}",
                a["category_name"] or "All Categories",
                a["difficulty"],
                f"{a['score_marks']}/{a['max_marks']}",
                f"{a['percentage']}%",
                status_text,
                time_str,
                a["created_at"]
            ))

        self.lbl_count.configure(text=f"Total Completed Attempts: {len(attempts)}")

    def view_details(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select an attempt row to view details.")
            return

        values = self.tree.item(selected[0])["values"]
        attempt_id = int(str(values[0]).replace("#", ""))

        settings = database.get_settings()
        show_review = settings.get("show_answers_after_submission", "true").lower() == "true"
        if not show_review:
            messagebox.showinfo("Review Disabled", "The administrator has disabled detailed answer key reviews.")
            return

        self.controller.show_quiz_results(attempt_id=attempt_id)
