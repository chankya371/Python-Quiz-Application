"""
admin/manage_users.py - User Account Management Module
Allows the admin to view registered users, search accounts, monitor quiz attempt
statistics, and toggle user account activation status without exposing passwords.
"""

import tkinter as tk
from tkinter import ttk, messagebox

import database
from ui_common import THEME, FONTS, ModernButton


class ManageUsersView(tk.Frame):
    """Admin view for managing registered student/user accounts."""

    def __init__(self, parent, controller):
        super().__init__(parent, bg=THEME["bg_main"])
        self.controller = controller

        # Header Title Bar
        header = tk.Frame(self, bg=THEME["bg_main"], padx=20, pady=15)
        header.pack(fill="x")

        title_box = tk.Frame(header, bg=THEME["bg_main"])
        title_box.pack(side="left")

        lbl_title = tk.Label(title_box, text="Manage Users", font=FONTS["hero"], bg=THEME["bg_main"], fg=THEME["text_primary"])
        lbl_title.pack(anchor="w")

        lbl_sub = tk.Label(title_box, text="View user profiles, attempt activity, and manage account access status",
                           font=FONTS["body"], bg=THEME["bg_main"], fg=THEME["text_secondary"])
        lbl_sub.pack(anchor="w")

        # Search Bar
        search_bar = tk.Frame(self, bg=THEME["bg_card"], bd=1, relief="ridge", padx=16, pady=10)
        search_bar.pack(fill="x", padx=20, pady=(0, 10))

        tk.Label(search_bar, text="🔍 Search Users:", font=FONTS["body_bold"], bg=THEME["bg_card"], fg=THEME["text_primary"]).pack(side="left", padx=(0, 6))
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(search_bar, textvariable=self.search_var, bg=THEME["bg_main"], fg=THEME["text_primary"],
                                     insertbackground=THEME["text_primary"], font=FONTS["body"], width=28, bd=1, relief="solid")
        self.search_entry.pack(side="left", padx=(0, 10))
        self.search_entry.bind("<KeyRelease>", lambda e: self.load_users())

        btn_clear = ModernButton(search_bar, text="Clear", command=self.clear_search,
                                 bg=THEME["bg_card_hover"], hover_bg=THEME["btn_nav_hover"],
                                 font=FONTS["button_sm"], padx=10, pady=3)
        btn_clear.pack(side="left")

        self.lbl_stats = tk.Label(search_bar, text="", font=FONTS["meta"], bg=THEME["bg_card"], fg=THEME["text_accent"])
        self.lbl_stats.pack(side="right")

        # Users Table
        table_frame = tk.Frame(self, bg=THEME["bg_main"], padx=20)
        table_frame.pack(fill="both", expand=True)

        cols = ("id", "username", "full_name", "email", "registered", "attempts", "avg_score", "status")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=15)

        self.tree.heading("id", text="ID")
        self.tree.heading("username", text="Username")
        self.tree.heading("full_name", text="Full Name")
        self.tree.heading("email", text="Email")
        self.tree.heading("registered", text="Registered On")
        self.tree.heading("attempts", text="Quizzes")
        self.tree.heading("avg_score", text="Avg Score")
        self.tree.heading("status", text="Account Status")

        self.tree.column("id", width=45, anchor="center")
        self.tree.column("username", width=120, anchor="w")
        self.tree.column("full_name", width=150, anchor="w")
        self.tree.column("email", width=180, anchor="w")
        self.tree.column("registered", width=140, anchor="center")
        self.tree.column("attempts", width=70, anchor="center")
        self.tree.column("avg_score", width=80, anchor="center")
        self.tree.column("status", width=110, anchor="center")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Footer Actions
        footer = tk.Frame(self, bg=THEME["bg_main"], padx=20, pady=12)
        footer.pack(fill="x")

        btn_toggle = ModernButton(footer, text="🔄 Toggle Active / Inactive Status", command=self.toggle_user_status,
                                  bg=THEME["accent_primary"], hover_bg=THEME["accent_primary_hover"],
                                  font=FONTS["button_sm"], padx=14, pady=6)
        btn_toggle.pack(side="left", padx=4)

        lbl_sec = tk.Label(footer, text="🔒 Passwords are cryptographically salted and hashed. Sensitive credentials are never exposed.",
                           font=FONTS["meta"], bg=THEME["bg_main"], fg=THEME["text_secondary"])
        lbl_sec.pack(side="right")

        self.load_users()

    def clear_search(self):
        self.search_var.set("")
        self.load_users()

    def load_users(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        search = self.search_var.get().strip()
        users = database.get_all_users(search_query=search)

        for u in users:
            status_text = "Active ✓" if u["is_active"] == 1 else "Inactive (Disabled) ✗"
            avg_str = f"{round(u['avg_score'], 1)}%" if u["attempts_count"] > 0 else "N/A"
            self.tree.insert("", "end", values=(
                u["id"],
                u["username"],
                u["full_name"] or "N/A",
                u["email"] or "N/A",
                u["created_at"],
                u["attempts_count"],
                avg_str,
                status_text
            ))

        self.lbl_stats.configure(text=f"Total Users: {len(users)}")

    def toggle_user_status(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select a user from the table first.")
            return

        values = self.tree.item(selected[0])["values"]
        user_id = int(values[0])
        username = values[1]
        current_status = values[7]

        action_name = "deactivate" if "Active" in current_status else "activate"
        confirm = messagebox.askyesno(
            "Confirm Status Change",
            f"Are you sure you want to {action_name} user '{username}'?\n\n"
            f"{'Deactivated users will not be able to log in or take quizzes.' if action_name == 'deactivate' else 'User will be able to log in normally.'}"
        )
        if not confirm:
            return

        new_status, err = database.toggle_user_status(user_id)
        if err:
            messagebox.showerror("Error", f"Failed to change status: {err}")
        else:
            messagebox.showinfo("Status Updated", f"User '{username}' is now {'Active' if new_status == 1 else 'Inactive'}.")
            self.load_users()
