"""
admin/view_results.py - Quiz Results, Detailed Review, and CSV Export
Allows the admin to review all student attempts, search/filter, inspect
question-by-question breakdown, and export audit reports to CSV.
"""

import csv
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

import database
from ui_common import THEME, FONTS, ModernButton, ScrollableFrame


class ViewResultsView(tk.Frame):
    """Admin view for inspecting quiz results and exporting to CSV."""

    def __init__(self, parent, controller):
        super().__init__(parent, bg=THEME["bg_main"])
        self.controller = controller

        # Header Title Bar
        header = tk.Frame(self, bg=THEME["bg_main"], padx=20, pady=15)
        header.pack(fill="x")

        title_box = tk.Frame(header, bg=THEME["bg_main"])
        title_box.pack(side="left")

        lbl_title = tk.Label(title_box, text="Quiz Results & Audit Reports", font=FONTS["hero"], bg=THEME["bg_main"], fg=THEME["text_primary"])
        lbl_title.pack(anchor="w")

        lbl_sub = tk.Label(title_box, text="Review attempt performance, inspect answer breakdowns, and export to CSV",
                           font=FONTS["body"], bg=THEME["bg_main"], fg=THEME["text_secondary"])
        lbl_sub.pack(anchor="w")

        btn_export = ModernButton(header, text="📊 Export to CSV", command=self.export_csv,
                                  bg=THEME["success"], hover_bg=THEME["success_hover"],
                                  font=FONTS["button_sm"], padx=14, pady=6)
        btn_export.pack(side="right")

        # Toolbar Filter
        filter_bar = tk.Frame(self, bg=THEME["bg_card"], bd=1, relief="ridge", padx=16, pady=10)
        filter_bar.pack(fill="x", padx=20, pady=(0, 10))

        # Search User
        tk.Label(filter_bar, text="🔍 Search User:", font=FONTS["body_bold"], bg=THEME["bg_card"], fg=THEME["text_primary"]).pack(side="left", padx=(0, 4))
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(filter_bar, textvariable=self.search_var, bg=THEME["bg_main"], fg=THEME["text_primary"],
                                     insertbackground=THEME["text_primary"], font=FONTS["body"], width=18, bd=1, relief="solid")
        self.search_entry.pack(side="left", padx=(0, 15))
        self.search_entry.bind("<KeyRelease>", lambda e: self.load_results())

        # Category Filter
        tk.Label(filter_bar, text="Category:", font=FONTS["body_bold"], bg=THEME["bg_card"], fg=THEME["text_primary"]).pack(side="left", padx=(0, 4))
        self.cat_var = tk.StringVar(value="All")
        self.cat_combo = ttk.Combobox(filter_bar, textvariable=self.cat_var, state="readonly", width=16)
        self.cat_combo.pack(side="left", padx=(0, 15))
        self.cat_combo.bind("<<ComboboxSelected>>", lambda e: self.load_results())

        # Sort By
        tk.Label(filter_bar, text="Sort By:", font=FONTS["body_bold"], bg=THEME["bg_card"], fg=THEME["text_primary"]).pack(side="left", padx=(0, 4))
        self.sort_var = tk.StringVar(value="Date (Newest First)")
        self.sort_map = {
            "Date (Newest First)": "date_desc",
            "Score (Highest First)": "score_desc",
            "Score (Lowest First)": "score_asc",
            "Username (A-Z)": "user_asc"
        }
        self.sort_combo = ttk.Combobox(filter_bar, textvariable=self.sort_var, values=list(self.sort_map.keys()), state="readonly", width=18)
        self.sort_combo.pack(side="left", padx=(0, 15))
        self.sort_combo.bind("<<ComboboxSelected>>", lambda e: self.load_results())

        # Reset Filter
        btn_reset = ModernButton(filter_bar, text="Reset", command=self.reset_filters,
                                 bg=THEME["bg_card_hover"], hover_bg=THEME["btn_nav_hover"],
                                 font=FONTS["button_sm"], padx=10, pady=3)
        btn_reset.pack(side="left")

        self.lbl_count = tk.Label(filter_bar, text="", font=FONTS["meta"], bg=THEME["bg_card"], fg=THEME["text_accent"])
        self.lbl_count.pack(side="right")

        # Table
        table_frame = tk.Frame(self, bg=THEME["bg_main"], padx=20)
        table_frame.pack(fill="both", expand=True)

        cols = ("id", "username", "category", "difficulty", "score", "percentage", "status", "time", "date")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=14)

        self.tree.heading("id", text="Attempt ID")
        self.tree.heading("username", text="Username")
        self.tree.heading("category", text="Category")
        self.tree.heading("difficulty", text="Difficulty")
        self.tree.heading("score", text="Score (Marks)")
        self.tree.heading("percentage", text="Percentage")
        self.tree.heading("status", text="Result")
        self.tree.heading("time", text="Time Taken")
        self.tree.heading("date", text="Attempt Date")

        self.tree.column("id", width=70, anchor="center")
        self.tree.column("username", width=120, anchor="w")
        self.tree.column("category", width=140, anchor="w")
        self.tree.column("difficulty", width=80, anchor="center")
        self.tree.column("score", width=90, anchor="center")
        self.tree.column("percentage", width=85, anchor="center")
        self.tree.column("status", width=80, anchor="center")
        self.tree.column("time", width=85, anchor="center")
        self.tree.column("date", width=140, anchor="center")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind("<Double-1>", lambda e: self.view_details())

        # Footer Actions
        footer = tk.Frame(self, bg=THEME["bg_main"], padx=20, pady=12)
        footer.pack(fill="x")

        btn_view = ModernButton(footer, text="🔍 View Attempt Details", command=self.view_details,
                                bg=THEME["accent_primary"], hover_bg=THEME["accent_primary_hover"],
                                font=FONTS["button_sm"], padx=14, pady=6)
        btn_view.pack(side="left", padx=4)

        lbl_hint = tk.Label(footer, text="Tip: Double-click any attempt row to view question-by-question student answers",
                            font=FONTS["meta"], bg=THEME["bg_main"], fg=THEME["text_secondary"])
        lbl_hint.pack(side="right")

        self.refresh_categories_dropdown()
        self.load_results()

    def refresh_categories_dropdown(self):
        cats = database.get_categories()
        self.cat_lookup = {c["name"]: c["id"] for c in cats}
        self.cat_combo["values"] = ["All"] + [c["name"] for c in cats]

    def reset_filters(self):
        self.search_var.set("")
        self.cat_var.set("All")
        self.sort_var.set("Date (Newest First)")
        self.load_results()

    def load_results(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        cat_name = self.cat_var.get()
        cat_id = self.cat_lookup.get(cat_name) if cat_name != "All" else None
        search = self.search_var.get().strip()
        sort_key = self.sort_map.get(self.sort_var.get(), "date_desc")

        attempts = database.get_all_attempts(category_id=cat_id, search_user=search, sort_by=sort_key)

        for a in attempts:
            status_text = "Passed ✓" if a["passed"] == 1 else "Failed ✗"
            time_str = f"{a['time_taken_seconds'] // 60}m {a['time_taken_seconds'] % 60}s"
            self.tree.insert("", "end", values=(
                f"#{a['id']}",
                a["username"],
                a["category_name"] or "All Categories",
                a["difficulty"],
                f"{a['score_marks']}/{a['max_marks']}",
                f"{a['percentage']}%",
                status_text,
                time_str,
                a["created_at"]
            ))

        self.lbl_count.configure(text=f"Total Records: {len(attempts)}")

    def view_details(self):
        """Displays question-by-question modal review of the selected attempt."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select an attempt row to view details.")
            return

        values = self.tree.item(selected[0])["values"]
        attempt_id = int(str(values[0]).replace("#", ""))

        attempt, answers = database.get_attempt_details(attempt_id)
        if not attempt:
            messagebox.showerror("Error", "Attempt details not found.")
            return

        dlg = tk.Toplevel(self)
        dlg.title(f"Quiz Attempt Breakdown - Attempt #{attempt_id} ({attempt['username']})")
        dlg.configure(bg=THEME["bg_main"])
        dlg.geometry("780x680")
        dlg.transient(self)
        dlg.grab_set()

        # Header Summary
        h_frame = tk.Frame(dlg, bg=THEME["bg_card"], padx=20, pady=12, bd=1, relief="ridge")
        h_frame.pack(fill="x")

        tk.Label(h_frame, text=f"Attempt #{attempt_id} — {attempt['full_name']} (@{attempt['username']})",
                 font=FONTS["h2"], bg=THEME["bg_card"], fg=THEME["text_primary"]).pack(anchor="w")

        meta_text = (
            f"Category: {attempt['category_name'] or 'All'}  |  Difficulty: {attempt['difficulty']}  |  "
            f"Score: {attempt['score_marks']}/{attempt['max_marks']} ({attempt['percentage']}%)  |  "
            f"Result: {'Passed ✓' if attempt['passed'] else 'Failed ✗'}  |  Date: {attempt['created_at']}"
        )
        tk.Label(h_frame, text=meta_text, font=FONTS["meta"], bg=THEME["bg_card"], fg=THEME["text_accent"]).pack(anchor="w", pady=(4, 0))

        # Scrollable Question Breakdown
        scroll = ScrollableFrame(dlg, bg=THEME["bg_main"])
        scroll.pack(fill="both", expand=True, padx=15, pady=10)
        content = scroll.scrollable_content

        for idx, ans in enumerate(answers, start=1):
            box = tk.Frame(content, bg=THEME["bg_card"], bd=1, relief="ridge", padx=14, pady=10)
            box.pack(fill="x", pady=6)

            top_row = tk.Frame(box, bg=THEME["bg_card"])
            top_row.pack(fill="x")

            tk.Label(top_row, text=f"Q{idx}. {ans['question_text']}", font=FONTS["body_bold"],
                     bg=THEME["bg_card"], fg=THEME["text_primary"], wraplength=580, justify="left").pack(side="left")

            is_corr = ans["is_correct"] == 1
            res_color = THEME["success"] if is_corr else (THEME["warning"] if not ans["user_answer"] else THEME["danger"])
            res_label = "✓ Correct" if is_corr else ("⚠️ Unanswered" if not ans["user_answer"] else "✗ Incorrect")

            tk.Label(top_row, text=res_label, font=FONTS["body_bold"], bg=THEME["bg_card"], fg=res_color).pack(side="right")

            # Answer options
            opts_box = tk.Frame(box, bg=THEME["bg_card"])
            opts_box.pack(fill="x", pady=(6, 2))

            for letter in ("A", "B", "C", "D"):
                opt_val = ans[f"option_{letter.lower()}"]
                fg_col = THEME["text_secondary"]
                prefix = f"  {letter}. "

                if ans["correct_answer"] == letter:
                    fg_col = THEME["success"]
                    prefix = f"  {letter}. [CORRECT] "
                if ans["user_answer"] == letter:
                    if not is_corr:
                        fg_col = THEME["danger"]
                        prefix = f"  {letter}. [STUDENT PICKED] "

                tk.Label(opts_box, text=f"{prefix}{opt_val}", font=FONTS["body"], bg=THEME["bg_card"], fg=fg_col).pack(anchor="w")

            if ans.get("explanation"):
                tk.Label(box, text=f"Explanation: {ans['explanation']}", font=FONTS["meta"],
                         bg=THEME["bg_card"], fg=THEME["text_accent"], wraplength=650, justify="left").pack(anchor="w", pady=(6, 0))

        # Close Button
        btn_close = ModernButton(dlg, text="Close", command=dlg.destroy, bg=THEME["btn_nav"], hover_bg=THEME["btn_nav_hover"],
                                 font=FONTS["button_sm"], padx=14, pady=6)
        btn_close.pack(pady=10)

    def export_csv(self):
        """Exports all recorded quiz attempts to a CSV file."""
        attempts = database.get_all_attempts(limit=5000)
        if not attempts:
            messagebox.showwarning("Export Warning", "No quiz attempts recorded yet to export.")
            return

        file_path = filedialog.asksaveasfilename(
            title="Export Quiz Results to CSV",
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")]
        )
        if not file_path:
            return

        try:
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Attempt ID", "User ID", "Username", "Full Name",
                    "Category", "Difficulty", "Total Questions",
                    "Correct Answers", "Incorrect Answers", "Unanswered",
                    "Score Marks", "Max Marks", "Percentage", "Passed (1/0)",
                    "Time Taken Seconds", "Attempt Date"
                ])
                for a in attempts:
                    writer.writerow([
                        a["id"], a["user_id"], a["username"], a["full_name"],
                        a["category_name"] or "All Categories", a["difficulty"],
                        a["total_questions"], a["correct_answers"], a["incorrect_answers"],
                        a["unanswered"], a["score_marks"], a["max_marks"],
                        a["percentage"], a["passed"], a["time_taken_seconds"], a["created_at"]
                    ])

            messagebox.showinfo("Export Successful", f"Exported {len(attempts)} attempt records to:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Export Failed", f"Could not write CSV file:\n{e}")
