"""
admin/manage_questions.py - Complete Question Management Module
Allows adding, editing, deleting, searching, filtering, and activating/deactivating
questions, as well as importing/exporting questions in JSON format.
"""

import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

import database
from ui_common import THEME, FONTS, ModernButton


class ManageQuestionsView(tk.Frame):
    """Admin view for managing quiz questions in SQLite."""

    def __init__(self, parent, controller):
        super().__init__(parent, bg=THEME["bg_main"])
        self.controller = controller

        # Header Title Bar
        header = tk.Frame(self, bg=THEME["bg_main"], padx=20, pady=15)
        header.pack(fill="x")

        title_box = tk.Frame(header, bg=THEME["bg_main"])
        title_box.pack(side="left")

        lbl_title = tk.Label(title_box, text="Manage Questions", font=FONTS["hero"], bg=THEME["bg_main"], fg=THEME["text_primary"])
        lbl_title.pack(anchor="w")

        lbl_sub = tk.Label(title_box, text="Create, edit, filter, import, and organize multiple-choice quiz questions",
                           font=FONTS["body"], bg=THEME["bg_main"], fg=THEME["text_secondary"])
        lbl_sub.pack(anchor="w")

        # Top Action Buttons
        actions_bar = tk.Frame(header, bg=THEME["bg_main"])
        actions_bar.pack(side="right")

        btn_add = ModernButton(actions_bar, text="➕ Add Question", command=self.open_add_dialog,
                               bg=THEME["accent_primary"], hover_bg=THEME["accent_primary_hover"],
                               font=FONTS["button_sm"], padx=12, pady=6)
        btn_add.pack(side="left", padx=4)

        btn_import = ModernButton(actions_bar, text="📥 Import JSON", command=self.import_json,
                                  bg=THEME["btn_nav"], hover_bg=THEME["btn_nav_hover"],
                                  font=FONTS["button_sm"], padx=10, pady=6)
        btn_import.pack(side="left", padx=4)

        btn_export = ModernButton(actions_bar, text="📤 Export JSON", command=self.export_json,
                                  bg=THEME["btn_nav"], hover_bg=THEME["btn_nav_hover"],
                                  font=FONTS["button_sm"], padx=10, pady=6)
        btn_export.pack(side="left", padx=4)

        # ----------------------------------------------------
        # FILTER & SEARCH TOOLBAR
        # ----------------------------------------------------
        filter_bar = tk.Frame(self, bg=THEME["bg_card"], bd=1, relief="ridge", padx=16, pady=10)
        filter_bar.pack(fill="x", padx=20, pady=(0, 10))

        # Search Entry
        tk.Label(filter_bar, text="🔍 Search:", font=FONTS["body_bold"], bg=THEME["bg_card"], fg=THEME["text_primary"]).pack(side="left", padx=(0, 4))
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(filter_bar, textvariable=self.search_var, bg=THEME["bg_main"], fg=THEME["text_primary"],
                                     insertbackground=THEME["text_primary"], font=FONTS["body"], width=22, bd=1, relief="solid")
        self.search_entry.pack(side="left", padx=(0, 15))
        self.search_entry.bind("<KeyRelease>", lambda e: self.load_questions())

        # Category Filter
        tk.Label(filter_bar, text="Category:", font=FONTS["body_bold"], bg=THEME["bg_card"], fg=THEME["text_primary"]).pack(side="left", padx=(0, 4))
        self.cat_var = tk.StringVar(value="All")
        self.cat_combo = ttk.Combobox(filter_bar, textvariable=self.cat_var, state="readonly", width=18)
        self.cat_combo.pack(side="left", padx=(0, 15))
        self.cat_combo.bind("<<ComboboxSelected>>", lambda e: self.load_questions())

        # Difficulty Filter
        tk.Label(filter_bar, text="Difficulty:", font=FONTS["body_bold"], bg=THEME["bg_card"], fg=THEME["text_primary"]).pack(side="left", padx=(0, 4))
        self.diff_var = tk.StringVar(value="All")
        self.diff_combo = ttk.Combobox(filter_bar, textvariable=self.diff_var, values=["All", "Easy", "Medium", "Hard"], state="readonly", width=10)
        self.diff_combo.pack(side="left", padx=(0, 15))
        self.diff_combo.bind("<<ComboboxSelected>>", lambda e: self.load_questions())

        # Status Filter
        tk.Label(filter_bar, text="Status:", font=FONTS["body_bold"], bg=THEME["bg_card"], fg=THEME["text_primary"]).pack(side="left", padx=(0, 4))
        self.status_var = tk.StringVar(value="All")
        self.status_combo = ttk.Combobox(filter_bar, textvariable=self.status_var, values=["All", "Active", "Inactive"], state="readonly", width=10)
        self.status_combo.pack(side="left", padx=(0, 15))
        self.status_combo.bind("<<ComboboxSelected>>", lambda e: self.load_questions())

        # Reset Filter Button
        btn_reset = ModernButton(filter_bar, text="Reset", command=self.reset_filters,
                                 bg=THEME["bg_card_hover"], hover_bg=THEME["btn_nav_hover"],
                                 font=FONTS["button_sm"], padx=10, pady=3)
        btn_reset.pack(side="left")

        # Total Count Label
        self.lbl_count = tk.Label(filter_bar, text="", font=FONTS["meta"], bg=THEME["bg_card"], fg=THEME["text_accent"])
        self.lbl_count.pack(side="right")

        # ----------------------------------------------------
        # QUESTIONS TREEVIEW TABLE
        # ----------------------------------------------------
        table_frame = tk.Frame(self, bg=THEME["bg_main"], padx=20)
        table_frame.pack(fill="both", expand=True)

        cols = ("id", "question", "category", "difficulty", "correct", "marks", "status")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=14)

        self.tree.heading("id", text="ID")
        self.tree.heading("question", text="Question Text")
        self.tree.heading("category", text="Category")
        self.tree.heading("difficulty", text="Difficulty")
        self.tree.heading("correct", text="Ans")
        self.tree.heading("marks", text="Marks")
        self.tree.heading("status", text="Status")

        self.tree.column("id", width=50, anchor="center")
        self.tree.column("question", width=360, anchor="w")
        self.tree.column("category", width=140, anchor="w")
        self.tree.column("difficulty", width=90, anchor="center")
        self.tree.column("correct", width=60, anchor="center")
        self.tree.column("marks", width=60, anchor="center")
        self.tree.column("status", width=80, anchor="center")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind("<Double-1>", lambda e: self.open_edit_dialog())

        # ----------------------------------------------------
        # ACTION BUTTONS FOOTER
        # ----------------------------------------------------
        footer = tk.Frame(self, bg=THEME["bg_main"], padx=20, pady=12)
        footer.pack(fill="x")

        btn_edit = ModernButton(footer, text="✏️ Edit Selected", command=self.open_edit_dialog,
                                bg=THEME["accent_primary"], hover_bg=THEME["accent_primary_hover"],
                                font=FONTS["button_sm"], padx=12, pady=6)
        btn_edit.pack(side="left", padx=4)

        btn_toggle = ModernButton(footer, text="🔄 Toggle Active / Inactive", command=self.toggle_status,
                                  bg=THEME["btn_nav"], hover_bg=THEME["btn_nav_hover"],
                                  font=FONTS["button_sm"], padx=12, pady=6)
        btn_toggle.pack(side="left", padx=4)

        btn_delete = ModernButton(footer, text="🗑️ Delete Question", command=self.delete_selected,
                                  bg=THEME["danger"], hover_bg=THEME["danger_hover"],
                                  font=FONTS["button_sm"], padx=12, pady=6)
        btn_delete.pack(side="left", padx=4)

        lbl_hint = tk.Label(footer, text="Tip: Double-click any row to edit question details", font=FONTS["meta"],
                            bg=THEME["bg_main"], fg=THEME["text_secondary"])
        lbl_hint.pack(side="right")

        # Initial populate
        self.refresh_categories_dropdown()
        self.load_questions()

    def refresh_categories_dropdown(self):
        """Populates category combobox filter with database categories."""
        cats = database.get_categories()
        self.cat_lookup = {c["name"]: c["id"] for c in cats}
        combo_values = ["All"] + [c["name"] for c in cats]
        self.cat_combo["values"] = combo_values

    def reset_filters(self):
        """Clears all filters."""
        self.search_var.set("")
        self.cat_var.set("All")
        self.diff_var.set("All")
        self.status_var.set("All")
        self.load_questions()

    def load_questions(self):
        """Fetches and displays questions from SQLite based on current filters."""
        for row in self.tree.get_children():
            self.tree.delete(row)

        cat_name = self.cat_var.get()
        cat_id = self.cat_lookup.get(cat_name) if cat_name != "All" else None
        diff = self.diff_var.get()
        status_val = self.status_var.get()
        search = self.search_var.get()

        questions = database.get_questions(
            category_id=cat_id,
            difficulty=diff,
            status=status_val,
            search_query=search
        )

        for q in questions:
            status_text = "Active" if q["is_active"] == 1 else "Inactive"
            self.tree.insert("", "end", values=(
                q["id"],
                q["question_text"],
                q["category_name"],
                q["difficulty"],
                q["correct_answer"],
                q["marks"],
                status_text
            ))

        self.lbl_count.configure(text=f"Showing {len(questions)} question{'s' if len(questions) != 1 else ''}")

    def _get_selected_id(self):
        """Returns the ID of the currently selected row in Treeview."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select a question from the table first.")
            return None
        return int(self.tree.item(selected[0])["values"][0])

    def toggle_status(self):
        """Toggles active/inactive state of selected question."""
        qid = self._get_selected_id()
        if not qid:
            return
        new_status, err = database.toggle_question_status(qid)
        if err:
            messagebox.showerror("Error", f"Failed to toggle status: {err}")
        else:
            self.load_questions()

    def delete_selected(self):
        """Deletes selected question with confirmation."""
        qid = self._get_selected_id()
        if not qid:
            return

        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to permanently delete Question #{qid}?\n\nThis action cannot be undone.",
            icon="warning"
        )
        if not confirm:
            return

        success, err = database.delete_question(qid)
        if not success:
            messagebox.showerror("Delete Error", f"Could not delete question: {err}")
        else:
            messagebox.showinfo("Deleted", f"Question #{qid} was successfully deleted.")
            self.load_questions()

    # ----------------------------------------------------
    # ADD & EDIT QUESTION MODAL DIALOG
    # ----------------------------------------------------
    def open_add_dialog(self):
        self._show_question_form(question_id=None)

    def open_edit_dialog(self):
        qid = self._get_selected_id()
        if qid:
            self._show_question_form(question_id=qid)

    def _show_question_form(self, question_id=None):
        """Modal dialog for creating or updating a question."""
        is_edit = question_id is not None
        title_text = f"Edit Question #{question_id}" if is_edit else "Add New Question"

        cats = database.get_categories()
        if not cats:
            messagebox.showerror("No Categories", "Please create at least one category before adding questions.")
            return

        cat_names = [c["name"] for c in cats]
        cat_id_by_name = {c["name"]: c["id"] for c in cats}

        # Existing data if editing
        initial = {}
        if is_edit:
            initial = database.get_question_by_id(question_id)
            if not initial:
                messagebox.showerror("Error", "Question not found.")
                return

        dlg = tk.Toplevel(self)
        dlg.title(title_text)
        dlg.configure(bg=THEME["bg_main"])
        dlg.geometry("700x720")
        dlg.transient(self)
        dlg.grab_set()

        # Header
        h_frame = tk.Frame(dlg, bg=THEME["bg_card"], padx=20, pady=12)
        h_frame.pack(fill="x")
        tk.Label(h_frame, text=title_text, font=FONTS["h1"], bg=THEME["bg_card"], fg=THEME["text_primary"]).pack(anchor="w")

        body = tk.Frame(dlg, bg=THEME["bg_main"], padx=25, pady=15)
        body.pack(fill="both", expand=True)

        # Question Text
        tk.Label(body, text="Question Text *", font=FONTS["body_bold"], bg=THEME["bg_main"], fg=THEME["text_primary"]).pack(anchor="w", pady=(0, 2))
        txt_q = tk.Text(body, height=3, font=FONTS["body"], bg=THEME["bg_card"], fg=THEME["text_primary"],
                        insertbackground=THEME["text_primary"], bd=1, relief="solid", wrap="word")
        txt_q.pack(fill="x", pady=(0, 10))
        if is_edit:
            txt_q.insert("1.0", initial["question_text"])

        # Options A, B, C, D
        options_entries = {}
        opts_frame = tk.Frame(body, bg=THEME["bg_main"])
        opts_frame.pack(fill="x", pady=(0, 10))

        for opt_key, opt_label in [("A", "Option A *"), ("B", "Option B *"), ("C", "Option C *"), ("D", "Option D *")]:
            row_f = tk.Frame(opts_frame, bg=THEME["bg_main"])
            row_f.pack(fill="x", pady=2)

            tk.Label(row_f, text=opt_label, width=12, anchor="w", font=FONTS["body_bold"],
                     bg=THEME["bg_main"], fg=THEME["text_accent"]).pack(side="left")
            entry = tk.Entry(row_f, font=FONTS["body"], bg=THEME["bg_card"], fg=THEME["text_primary"],
                             insertbackground=THEME["text_primary"], bd=1, relief="solid")
            entry.pack(side="left", fill="x", expand=True)
            if is_edit:
                entry.insert(0, initial.get(f"option_{opt_key.lower()}", ""))
            options_entries[opt_key] = entry

        # Meta row 1: Correct Answer, Category, Difficulty
        meta_row1 = tk.Frame(body, bg=THEME["bg_main"])
        meta_row1.pack(fill="x", pady=6)

        # Correct Answer
        tk.Label(meta_row1, text="Correct Answer *", font=FONTS["body_bold"], bg=THEME["bg_main"], fg=THEME["text_primary"]).pack(side="left", padx=(0, 4))
        var_ans = tk.StringVar(value=initial.get("correct_answer", "A"))
        combo_ans = ttk.Combobox(meta_row1, textvariable=var_ans, values=["A", "B", "C", "D"], state="readonly", width=6)
        combo_ans.pack(side="left", padx=(0, 15))

        # Category
        tk.Label(meta_row1, text="Category *", font=FONTS["body_bold"], bg=THEME["bg_main"], fg=THEME["text_primary"]).pack(side="left", padx=(0, 4))
        var_cat = tk.StringVar(value=initial.get("category_name", cat_names[0]))
        combo_cat = ttk.Combobox(meta_row1, textvariable=var_cat, values=cat_names, state="readonly", width=18)
        combo_cat.pack(side="left", padx=(0, 15))

        # Difficulty
        tk.Label(meta_row1, text="Difficulty *", font=FONTS["body_bold"], bg=THEME["bg_main"], fg=THEME["text_primary"]).pack(side="left", padx=(0, 4))
        var_diff = tk.StringVar(value=initial.get("difficulty", "Medium"))
        combo_diff = ttk.Combobox(meta_row1, textvariable=var_diff, values=["Easy", "Medium", "Hard"], state="readonly", width=10)
        combo_diff.pack(side="left")

        # Meta row 2: Marks, Active Checkbox
        meta_row2 = tk.Frame(body, bg=THEME["bg_main"])
        meta_row2.pack(fill="x", pady=6)

        tk.Label(meta_row2, text="Marks (Points):", font=FONTS["body_bold"], bg=THEME["bg_main"], fg=THEME["text_primary"]).pack(side="left", padx=(0, 4))
        var_marks = tk.StringVar(value=str(initial.get("marks", 1)))
        entry_marks = tk.Entry(meta_row2, textvariable=var_marks, width=6, font=FONTS["body"], bg=THEME["bg_card"],
                               fg=THEME["text_primary"], insertbackground=THEME["text_primary"], bd=1, relief="solid")
        entry_marks.pack(side="left", padx=(0, 20))

        var_active = tk.BooleanVar(value=bool(initial.get("is_active", 1)))
        chk_active = tk.Checkbutton(meta_row2, text="Active (Visible in user quizzes)", variable=var_active,
                                    bg=THEME["bg_main"], fg=THEME["text_primary"], selectcolor=THEME["bg_card"],
                                    activebackground=THEME["bg_main"], font=FONTS["body"])
        chk_active.pack(side="left")

        # Explanation
        tk.Label(body, text="Explanation (shown to users in review mode):", font=FONTS["body_bold"],
                 bg=THEME["bg_main"], fg=THEME["text_secondary"]).pack(anchor="w", pady=(8, 2))
        txt_exp = tk.Text(body, height=3, font=FONTS["body"], bg=THEME["bg_card"], fg=THEME["text_primary"],
                          insertbackground=THEME["text_primary"], bd=1, relief="solid", wrap="word")
        txt_exp.pack(fill="x", pady=(0, 15))
        if is_edit:
            txt_exp.insert("1.0", initial.get("explanation", ""))

        # Dialog Buttons
        btn_bar = tk.Frame(body, bg=THEME["bg_main"])
        btn_bar.pack(fill="x", pady=(5, 0))

        def _save():
            q_text = txt_q.get("1.0", "end").strip()
            opt_a = options_entries["A"].get().strip()
            opt_b = options_entries["B"].get().strip()
            opt_c = options_entries["C"].get().strip()
            opt_d = options_entries["D"].get().strip()
            correct_ans = var_ans.get().strip().upper()
            cat_selected = var_cat.get().strip()
            diff_selected = var_diff.get().strip()
            exp_text = txt_exp.get("1.0", "end").strip()
            is_act = 1 if var_active.get() else 0

            # Validations
            if not q_text:
                messagebox.showwarning("Validation Error", "Question Text cannot be empty.", parent=dlg)
                return
            if not opt_a or not opt_b or not opt_c or not opt_d:
                messagebox.showwarning("Validation Error", "All four options (A, B, C, D) are required and cannot be empty.", parent=dlg)
                return
            if correct_ans not in ("A", "B", "C", "D"):
                messagebox.showwarning("Validation Error", "Please select a valid correct answer (A, B, C, or D).", parent=dlg)
                return

            cat_id = cat_id_by_name.get(cat_selected)
            if not cat_id:
                messagebox.showwarning("Validation Error", "Invalid category selected.", parent=dlg)
                return

            try:
                marks_val = int(var_marks.get().strip())
                if marks_val < 1:
                    raise ValueError
            except ValueError:
                messagebox.showwarning("Validation Error", "Marks must be a positive integer (e.g. 1, 2, 5).", parent=dlg)
                return

            # Execute Save
            if is_edit:
                success, err = database.update_question(
                    question_id=question_id,
                    category_id=cat_id,
                    question_text=q_text,
                    opt_a=opt_a,
                    opt_b=opt_b,
                    opt_c=opt_c,
                    opt_d=opt_d,
                    correct_answer=correct_ans,
                    difficulty=diff_selected,
                    marks=marks_val,
                    explanation=exp_text,
                    is_active=is_act
                )
            else:
                success, err = database.add_question(
                    category_id=cat_id,
                    question_text=q_text,
                    opt_a=opt_a,
                    opt_b=opt_b,
                    opt_c=opt_c,
                    opt_d=opt_d,
                    correct_answer=correct_ans,
                    difficulty=diff_selected,
                    marks=marks_val,
                    explanation=exp_text,
                    is_active=is_act
                )

            if err:
                messagebox.showerror("Save Error", f"Failed to save question: {err}", parent=dlg)
            else:
                messagebox.showinfo("Success", f"Question successfully {'updated' if is_edit else 'created'}!", parent=dlg)
                dlg.destroy()
                self.load_questions()

        btn_save = ModernButton(btn_bar, text="💾 Save Question", command=_save,
                                bg=THEME["success"], hover_bg=THEME["success_hover"],
                                font=FONTS["button_sm"], padx=16, pady=6)
        btn_save.pack(side="right", padx=(8, 0))

        btn_cancel = ModernButton(btn_bar, text="Cancel", command=dlg.destroy,
                                  bg=THEME["btn_nav"], hover_bg=THEME["btn_nav_hover"],
                                  font=FONTS["button_sm"], padx=14, pady=6)
        btn_cancel.pack(side="right")

    # ----------------------------------------------------
    # IMPORT & EXPORT JSON
    # ----------------------------------------------------
    def import_json(self):
        """Imports questions from a user-selected JSON file."""
        file_path = filedialog.askopenfilename(
            title="Import Questions from JSON",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
        )
        if not file_path:
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            messagebox.showerror("Import Error", f"Could not read JSON file:\n{e}")
            return

        if not isinstance(data, list) or len(data) == 0:
            messagebox.showwarning("Import Warning", "The selected JSON file does not contain a list of questions.")
            return

        # Prepare categories lookup
        cats = database.get_categories()
        cat_map = {c["name"].lower(): c["id"] for c in cats}
        imported_count = 0
        skipped_count = 0

        for item in data:
            if not isinstance(item, dict):
                skipped_count += 1
                continue

            q_text = item.get("question") or item.get("question_text")
            options = item.get("options")
            opt_a = item.get("option_a")
            opt_b = item.get("option_b")
            opt_c = item.get("option_c")
            opt_d = item.get("option_d")
            correct = item.get("correct_answer") or item.get("answer")
            cat_name = item.get("category") or item.get("category_name", "General Knowledge")
            difficulty = item.get("difficulty", "Medium")
            marks = item.get("marks", 1)
            explanation = item.get("explanation", "")

            # If options given as array of 4
            if isinstance(options, list) and len(options) == 4:
                opt_a, opt_b, opt_c, opt_d = options[0], options[1], options[2], options[3]
                # If answer given as option text
                if correct and correct not in ("A", "B", "C", "D"):
                    for idx, opt_str in enumerate(options):
                        if str(opt_str).strip() == str(correct).strip():
                            correct = chr(65 + idx)
                            break

            if not q_text or not opt_a or not opt_b or not opt_c or not opt_d or not correct:
                skipped_count += 1
                continue

            # Ensure category exists
            cat_id = cat_map.get(cat_name.lower())
            if not cat_id:
                new_cat_id, _ = database.add_category(cat_name)
                if new_cat_id:
                    cat_id = new_cat_id
                    cat_map[cat_name.lower()] = new_cat_id
                else:
                    cat_id = list(cat_map.values())[0] if cat_map else 1

            database.add_question(
                category_id=cat_id,
                question_text=str(q_text),
                opt_a=str(opt_a),
                opt_b=str(opt_b),
                opt_c=str(opt_c),
                opt_d=str(opt_d),
                correct_answer=str(correct).upper(),
                difficulty=str(difficulty).capitalize() if difficulty in ("Easy", "Medium", "Hard") else "Medium",
                marks=int(marks) if str(marks).isdigit() else 1,
                explanation=str(explanation),
                is_active=1
            )
            imported_count += 1

        self.refresh_categories_dropdown()
        self.load_questions()
        messagebox.showinfo(
            "Import Finished",
            f"Successfully imported {imported_count} questions into the database.\nSkipped: {skipped_count} invalid items."
        )

    def export_json(self):
        """Exports currently loaded questions to a JSON file."""
        questions = database.get_questions()
        if not questions:
            messagebox.showwarning("Export", "No questions available to export.")
            return

        file_path = filedialog.asksaveasfilename(
            title="Export Questions to JSON",
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json")]
        )
        if not file_path:
            return

        export_data = []
        for q in questions:
            export_data.append({
                "id": q["id"],
                "category": q["category_name"],
                "question": q["question_text"],
                "options": [q["option_a"], q["option_b"], q["option_c"], q["option_d"]],
                "correct_answer": q["correct_answer"],
                "difficulty": q["difficulty"],
                "marks": q["marks"],
                "explanation": q["explanation"],
                "is_active": q["is_active"]
            })

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("Export Successful", f"Exported {len(export_data)} questions to:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to write file:\n{e}")
