"""
admin/dashboard.py - Admin Overview Dashboard
Displays summary metric cards, Matplotlib analytics charts,
and a recent quiz activity table populated live from SQLite.
"""

import tkinter as tk
from tkinter import ttk
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import database
from ui_common import THEME, FONTS, ModernButton, StatCard, ScrollableFrame


class AdminDashboardView(tk.Frame):
    """Admin Overview Dashboard Frame with metrics and charts."""

    def __init__(self, parent, controller):
        super().__init__(parent, bg=THEME["bg_main"])
        self.controller = controller

        # Scrollable container
        self.scroll = ScrollableFrame(self, bg=THEME["bg_main"])
        self.scroll.pack(fill="both", expand=True)
        self.content = self.scroll.scrollable_content

        self.charts_canvases = []
        self.render_dashboard()

    def render_dashboard(self):
        """Fetches live SQLite statistics and draws the entire dashboard."""
        for widget in self.content.winfo_children():
            widget.destroy()
        self.charts_canvases.clear()

        # Fetch stats from SQLite
        stats = database.get_admin_dashboard_summary()

        # Header Bar
        header = tk.Frame(self.content, bg=THEME["bg_main"], padx=20, pady=15)
        header.pack(fill="x")

        title_box = tk.Frame(header, bg=THEME["bg_main"])
        title_box.pack(side="left")

        lbl_title = tk.Label(
            title_box,
            text="Admin Analytics & Overview",
            font=FONTS["hero"],
            bg=THEME["bg_main"],
            fg=THEME["text_primary"]
        )
        lbl_title.pack(anchor="w")

        lbl_sub = tk.Label(
            title_box,
            text="Real-time quiz management statistics, user performance, and category distribution",
            font=FONTS["body"],
            bg=THEME["bg_main"],
            fg=THEME["text_secondary"]
        )
        lbl_sub.pack(anchor="w")

        btn_refresh = ModernButton(
            header,
            text="🔄 Refresh Data",
            command=self.render_dashboard,
            bg=THEME["btn_nav"],
            hover_bg=THEME["btn_nav_hover"],
            font=FONTS["button_sm"],
            padx=12,
            pady=6
        )
        btn_refresh.pack(side="right")

        # ----------------------------------------------------
        # 1. KPI SUMMARY CARDS
        # ----------------------------------------------------
        cards_frame = tk.Frame(self.content, bg=THEME["bg_main"], padx=20, pady=5)
        cards_frame.pack(fill="x")
        cards_frame.columnconfigure((0, 1, 2, 3, 4, 5), weight=1)

        kpi_data = [
            ("Total Questions", f"{stats['total_questions']} ({stats['active_questions']} act)", "❓", THEME["text_accent"]),
            ("Categories", stats["total_categories"], "📂", THEME["warning"]),
            ("Registered Users", f"{stats['total_users']} ({stats['active_users']} act)", "👥", THEME["accent_primary"]),
            ("Total Attempts", stats["total_attempts"], "📝", THEME["text_primary"]),
            ("Average Score", f"{stats['avg_score']}%", "📈", THEME["success"] if stats['avg_score'] >= 60 else THEME["warning"]),
            ("System Pass Rate", f"{stats['pass_rate']}%", "🏆", THEME["success"] if stats['pass_rate'] >= 60 else THEME["danger"])
        ]

        for col, (title, val, icon, color) in enumerate(kpi_data):
            card = StatCard(cards_frame, title=title, value=val, icon=icon, color=color)
            card.grid(row=0, column=col, padx=6, pady=6, sticky="nsew")

        # ----------------------------------------------------
        # 2. CHARTS SECTION (MATPLOTLIB)
        # ----------------------------------------------------
        charts_frame = tk.Frame(self.content, bg=THEME["bg_main"], padx=20, pady=15)
        charts_frame.pack(fill="x")
        charts_frame.columnconfigure((0, 1), weight=1)

        # Chart 1: Category Distribution (Bar Chart)
        self._build_category_chart(charts_frame, stats["cat_counts"])

        # Chart 2: Pass vs Fail / Performance (Pie Chart)
        self._build_performance_chart(charts_frame, stats["pass_count"], stats["fail_count"])

        # ----------------------------------------------------
        # 3. RECENT QUIZ ACTIVITY TABLE
        # ----------------------------------------------------
        recent_frame = tk.Frame(self.content, bg=THEME["bg_card"], bd=1, relief="ridge", padx=16, pady=14)
        recent_frame.pack(fill="x", padx=20, pady=(5, 25))

        lbl_recent = tk.Label(
            recent_frame,
            text="⚡ Recent Quiz Attempts",
            font=FONTS["h2"],
            bg=THEME["bg_card"],
            fg=THEME["text_primary"]
        )
        lbl_recent.pack(anchor="w", pady=(0, 10))

        tree_frame = tk.Frame(recent_frame, bg=THEME["bg_card"])
        tree_frame.pack(fill="x", expand=True)

        cols = ("id", "user", "category", "score", "percentage", "status", "date")
        tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=6)

        tree.heading("id", text="ID")
        tree.heading("user", text="User")
        tree.heading("category", text="Category")
        tree.heading("score", text="Score")
        tree.heading("percentage", text="Percentage")
        tree.heading("status", text="Result")
        tree.heading("date", text="Date & Time")

        tree.column("id", width=40, anchor="center")
        tree.column("user", width=120, anchor="w")
        tree.column("category", width=150, anchor="w")
        tree.column("score", width=80, anchor="center")
        tree.column("percentage", width=90, anchor="center")
        tree.column("status", width=90, anchor="center")
        tree.column("date", width=140, anchor="center")

        tree.pack(fill="x")

        for act in stats["recent_activity"]:
            res_str = "Passed ✓" if act["passed"] else "Failed ✗"
            tree.insert("", "end", values=(
                f"#{act['id']}",
                act["username"],
                act["category_name"] or "All Categories",
                f"{act['score_marks']}/{act['max_marks']}",
                f"{act['percentage']}%",
                res_str,
                act["created_at"]
            ))

        if not stats["recent_activity"]:
            no_act_lbl = tk.Label(
                recent_frame,
                text="No quiz attempts recorded yet. As users take quizzes, real-time results will appear here.",
                font=FONTS["body"],
                bg=THEME["bg_card"],
                fg=THEME["text_secondary"]
            )
            no_act_lbl.pack(pady=10)

    def _build_category_chart(self, parent, cat_counts):
        """Renders category question counts bar chart using Matplotlib."""
        box = tk.Frame(parent, bg=THEME["bg_card"], bd=1, relief="ridge", padx=14, pady=12)
        box.grid(row=0, column=0, padx=6, sticky="nsew")

        lbl = tk.Label(box, text="📂 Active Questions per Category", font=FONTS["h3"], bg=THEME["bg_card"], fg=THEME["text_accent"])
        lbl.pack(anchor="w", pady=(0, 6))

        fig = Figure(figsize=(5.2, 3.2), dpi=100, facecolor=THEME["bg_card"])
        ax = fig.add_subplot(111)
        ax.set_facecolor(THEME["bg_card"])

        categories = [item[0] for item in cat_counts] if cat_counts else ["None"]
        counts = [item[1] for item in cat_counts] if cat_counts else [0]

        # Truncate long category names
        display_cats = [c[:12] + ".." if len(c) > 14 else c for c in categories]
        bars = ax.bar(display_cats, counts, color="#6366f1", width=0.55, edgecolor="#818cf8", linewidth=1)

        ax.tick_params(colors=THEME["text_secondary"], labelsize=8)
        ax.spines["bottom"].set_color(THEME["border"])
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color(THEME["border"])
        ax.yaxis.grid(True, linestyle="--", alpha=0.3, color=THEME["border"])

        # Label numbers on top of bars
        for bar in bars:
            height = bar.get_height()
            ax.annotate(f"{height}",
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3), textcoords="offset points",
                        ha="center", va="bottom", fontsize=8, color=THEME["text_primary"])

        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=box)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self.charts_canvases.append(canvas)

    def _build_performance_chart(self, parent, pass_count, fail_count):
        """Renders Pass vs Fail distribution pie chart."""
        box = tk.Frame(parent, bg=THEME["bg_card"], bd=1, relief="ridge", padx=14, pady=12)
        box.grid(row=0, column=1, padx=6, sticky="nsew")

        lbl = tk.Label(box, text="🎯 Overall Pass / Fail Ratio", font=FONTS["h3"], bg=THEME["bg_card"], fg=THEME["text_accent"])
        lbl.pack(anchor="w", pady=(0, 6))

        fig = Figure(figsize=(5.2, 3.2), dpi=100, facecolor=THEME["bg_card"])
        ax = fig.add_subplot(111)

        if pass_count == 0 and fail_count == 0:
            ax.text(0.5, 0.5, "No Quiz Attempts Yet", ha="center", va="center",
                    color=THEME["text_secondary"], fontsize=11)
            ax.axis("off")
        else:
            labels = ["Passed", "Failed"]
            sizes = [pass_count, fail_count]
            colors = [THEME["success"], THEME["danger"]]

            wedges, texts, autotexts = ax.pie(
                sizes,
                labels=labels,
                autopct="%1.1f%%",
                startangle=90,
                colors=colors,
                textprops=dict(color=THEME["text_primary"], fontsize=9),
                wedgeprops=dict(edgecolor=THEME["bg_card"], linewidth=2)
            )
            for at in autotexts:
                at.set_color("#ffffff")
                at.set_weight("bold")
            ax.axis("equal")

        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=box)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self.charts_canvases.append(canvas)
