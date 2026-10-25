"""
admin/manage_categories.py - Category Management Module
Allows adding, renaming, viewing, and safely deleting quiz categories.
Prevents unsafe deletion of categories that are still assigned to questions.
"""

import tkinter as tk
from tkinter import ttk, messagebox

import database
from ui_common import THEME, FONTS, ModernButton


class ManageCategoriesView(tk.Frame):
    """Admin view for managing quiz categories."""

    def __init__(self, parent, controller):
        super().__init__(parent, bg=THEME["bg_main"])
        self.controller = controller

        # Header Title Bar
        header = tk.Frame(self, bg=THEME["bg_main"], padx=20, pady=15)
        header.pack(fill="x")

        title_box = tk.Frame(header, bg=THEME["bg_main"])
        title_box.pack(side="left")

        lbl_title = tk.Label(title_box, text="Manage Categories", font=FONTS["hero"], bg=THEME["bg_main"], fg=THEME["text_primary"])
        lbl_title.pack(anchor="w")

        lbl_sub = tk.Label(title_box, text="Organize questions into subject categories with safe deletion protection",
                           font=FONTS["body"], bg=THEME["bg_main"], fg=THEME["text_secondary"])
        lbl_sub.pack(anchor="w")

        btn_add = ModernButton(header, text="➕ Add Category", command=self.open_add_dialog,
                               bg=THEME["accent_primary"], hover_bg=THEME["accent_primary_hover"],
                               font=FONTS["button_sm"], padx=14, pady=6)
        btn_add.pack(side="right")

        # Table Container
        table_frame = tk.Frame(self, bg=THEME["bg_main"], padx=20, pady=5)
        table_frame.pack(fill="both", expand=True)

        cols = ("id", "name", "description", "total_q", "active_q", "created_at")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=15)

        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="Category Name")
        self.tree.heading("description", text="Description")
        self.tree.heading("total_q", text="Total Qs")
        self.tree.heading("active_q", text="Active Qs")
        self.tree.heading("created_at", text="Created On")

        self.tree.column("id", width=50, anchor="center")
        self.tree.column("name", width=180, anchor="w")
        self.tree.column("description", width=340, anchor="w")
        self.tree.column("total_q", width=90, anchor="center")
        self.tree.column("active_q", width=90, anchor="center")
        self.tree.column("created_at", width=140, anchor="center")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind("<Double-1>", lambda e: self.open_edit_dialog())

        # Footer Actions
        footer = tk.Frame(self, bg=THEME["bg_main"], padx=20, pady=12)
        footer.pack(fill="x")

        btn_edit = ModernButton(footer, text="✏️ Rename / Edit", command=self.open_edit_dialog,
                                bg=THEME["accent_primary"], hover_bg=THEME["accent_primary_hover"],
                                font=FONTS["button_sm"], padx=12, pady=6)
        btn_edit.pack(side="left", padx=4)

        btn_delete = ModernButton(footer, text="🗑️ Delete Category", command=self.delete_selected,
                                  bg=THEME["danger"], hover_bg=THEME["danger_hover"],
                                  font=FONTS["button_sm"], padx=12, pady=6)
        btn_delete.pack(side="left", padx=4)

        lbl_note = tk.Label(footer, text="* Categories containing questions cannot be deleted until questions are moved or deleted.",
                            font=FONTS["meta"], bg=THEME["bg_main"], fg=THEME["text_secondary"])
        lbl_note.pack(side="right")

        self.load_categories()

    def load_categories(self):
        """Loads categories and question counts from SQLite."""
        for row in self.tree.get_children():
            self.tree.delete(row)

        cats = database.get_categories(with_counts=True)
        for c in cats:
            self.tree.insert("", "end", values=(
                c["id"],
                c["name"],
                c.get("description", "") or "No description provided",
                c.get("question_count", 0),
                c.get("active_question_count", 0) or 0,
                c.get("created_at", "")
            ))

    def _get_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select a category from the table first.")
            return None
        values = self.tree.item(selected[0])["values"]
        return {
            "id": int(values[0]),
            "name": str(values[1]),
            "description": str(values[2]),
            "total_q": int(values[3])
        }

    def open_add_dialog(self):
        self._show_form(cat=None)

    def open_edit_dialog(self):
        cat = self._get_selected()
        if cat:
            self._show_form(cat=cat)

    def _show_form(self, cat=None):
        is_edit = cat is not None
        title_text = f"Edit Category: {cat['name']}" if is_edit else "Create New Category"

        dlg = tk.Toplevel(self)
        dlg.title(title_text)
        dlg.configure(bg=THEME["bg_main"])
        dlg.geometry("500x320")
        dlg.transient(self)
        dlg.grab_set()

        # Header
        h_frame = tk.Frame(dlg, bg=THEME["bg_card"], padx=20, pady=12)
        h_frame.pack(fill="x")
        tk.Label(h_frame, text=title_text, font=FONTS["h2"], bg=THEME["bg_card"], fg=THEME["text_primary"]).pack(anchor="w")

        body = tk.Frame(dlg, bg=THEME["bg_main"], padx=20, pady=15)
        body.pack(fill="both", expand=True)

        tk.Label(body, text="Category Name *", font=FONTS["body_bold"], bg=THEME["bg_main"], fg=THEME["text_primary"]).pack(anchor="w")
        entry_name = tk.Entry(body, font=FONTS["body"], bg=THEME["bg_card"], fg=THEME["text_primary"],
                              insertbackground=THEME["text_primary"], bd=1, relief="solid")
        entry_name.pack(fill="x", pady=(2, 10))
        if is_edit:
            entry_name.insert(0, cat["name"])

        tk.Label(body, text="Description", font=FONTS["body_bold"], bg=THEME["bg_main"], fg=THEME["text_secondary"]).pack(anchor="w")
        entry_desc = tk.Entry(body, font=FONTS["body"], bg=THEME["bg_card"], fg=THEME["text_primary"],
                              insertbackground=THEME["text_primary"], bd=1, relief="solid")
        entry_desc.pack(fill="x", pady=(2, 15))
        if is_edit and cat["description"] != "No description provided":
            entry_desc.insert(0, cat["description"])

        btn_bar = tk.Frame(body, bg=THEME["bg_main"])
        btn_bar.pack(fill="x", pady=(10, 0))

        def _save():
            name = entry_name.get().strip()
            desc = entry_desc.get().strip()
            if not name:
                messagebox.showwarning("Validation Error", "Category Name cannot be empty.", parent=dlg)
                return

            if is_edit:
                success, err = database.update_category(cat["id"], name, desc)
            else:
                success, err = database.add_category(name, desc)

            if err:
                messagebox.showerror("Error", err, parent=dlg)
            else:
                messagebox.showinfo("Success", f"Category '{name}' {'updated' if is_edit else 'created'} successfully!", parent=dlg)
                dlg.destroy()
                self.load_categories()

        btn_save = ModernButton(btn_bar, text="💾 Save", command=_save,
                                bg=THEME["success"], hover_bg=THEME["success_hover"],
                                font=FONTS["button_sm"], padx=16, pady=5)
        btn_save.pack(side="right", padx=(8, 0))

        btn_cancel = ModernButton(btn_bar, text="Cancel", command=dlg.destroy,
                                  bg=THEME["btn_nav"], hover_bg=THEME["btn_nav_hover"],
                                  font=FONTS["button_sm"], padx=12, pady=5)
        btn_cancel.pack(side="right")

    def delete_selected(self):
        cat = self._get_selected()
        if not cat:
            return

        # Check questions count first
        if cat["total_q"] > 0:
            messagebox.showwarning(
                "Safe Deletion Protected",
                f"Cannot delete '{cat['name']}': this category currently contains {cat['total_q']} questions.\n\n"
                f"Please delete or reassign those questions before deleting this category."
            )
            return

        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete category '{cat['name']}'?",
            icon="warning"
        )
        if not confirm:
            return

        success, err = database.delete_category(cat["id"])
        if not success:
            messagebox.showerror("Delete Failed", err)
        else:
            messagebox.showinfo("Deleted", f"Category '{cat['name']}' has been removed.")
            self.load_categories()
