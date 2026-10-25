"""
ui_common.py - Shared UI Theme, Widgets, and Styling Utilities
Provides consistent colors, fonts, styled buttons, metric cards,
scrollable containers, and ttk styles across the entire application.
"""

import sys
import tkinter as tk
from tkinter import ttk

# Enable High-DPI scaling on Windows
try:
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

FONT_FAMILY = "Segoe UI" if sys.platform.startswith("win") else "Helvetica"

THEME = {
    "bg_main": "#0f172a",          # Deep slate background
    "bg_card": "#1e293b",          # Container cards
    "bg_card_hover": "#334155",    # Card hover
    "bg_sidebar": "#090d16",       # Dark sidebar
    "bg_sidebar_active": "#1e293b",# Active sidebar tab
    "text_primary": "#f8fafc",     # Bright white
    "text_secondary": "#94a3b8",   # Muted slate
    "text_accent": "#38bdf8",      # Cyan / sky blue
    "accent_primary": "#6366f1",   # Indigo 500
    "accent_primary_hover": "#4f46e5",
    "success": "#10b981",          # Emerald
    "success_hover": "#059669",
    "danger": "#ef4444",           # Rose
    "danger_hover": "#dc2626",
    "warning": "#f59e0b",          # Amber
    "btn_nav": "#334155",          # Secondary buttons
    "btn_nav_hover": "#475569",
    "border": "#334155",
    "bg_selected": "#3730a3",      # Indigo selection background
    "border_selected": "#818cf8"   # Bright indigo border
}

FONTS = {
    "hero": (FONT_FAMILY, 22, "bold"),
    "h1": (FONT_FAMILY, 18, "bold"),
    "h2": (FONT_FAMILY, 14, "bold"),
    "h3": (FONT_FAMILY, 12, "bold"),
    "body": (FONT_FAMILY, 11),
    "body_bold": (FONT_FAMILY, 11, "bold"),
    "meta": (FONT_FAMILY, 9),
    "button": (FONT_FAMILY, 11, "bold"),
    "button_sm": (FONT_FAMILY, 10, "bold"),
    "stat_num": (FONT_FAMILY, 24, "bold"),
    "stat_lbl": (FONT_FAMILY, 10)
}


def setup_ttk_styles():
    """Configures global ttk widget styles to match modern dark theme."""
    style = ttk.Style()
    style.theme_use("clam")

    # Treeview Styles
    style.configure(
        "Treeview",
        background=THEME["bg_card"],
        foreground=THEME["text_primary"],
        fieldbackground=THEME["bg_card"],
        rowheight=32,
        font=(FONT_FAMILY, 10),
        borderwidth=0
    )
    style.configure(
        "Treeview.Heading",
        background=THEME["bg_card_hover"],
        foreground=THEME["text_accent"],
        font=(FONT_FAMILY, 10, "bold"),
        borderwidth=1,
        relief="flat"
    )
    style.map(
        "Treeview",
        background=[("selected", THEME["accent_primary"])],
        foreground=[("selected", "#ffffff")]
    )

    # Progressbar Style
    style.configure(
        "Modern.Horizontal.TProgressbar",
        troughcolor=THEME["bg_card"],
        background=THEME["accent_primary"],
        thickness=8,
        borderwidth=0
    )

    # Combobox Style
    style.configure(
        "TCombobox",
        fieldbackground=THEME["bg_card"],
        background=THEME["bg_card_hover"],
        foreground=THEME["text_primary"],
        arrowcolor=THEME["text_accent"],
        borderwidth=1,
        relief="flat"
    )


class ModernButton(tk.Button):
    """Custom flat styled button with smooth hover states and customizable color schemes."""

    def __init__(self, parent, text, command=None, bg=THEME["accent_primary"],
                 hover_bg=THEME["accent_primary_hover"], fg=THEME["text_primary"],
                 font=FONTS["button"], padx=16, pady=8, width=None, **kwargs):
        self.normal_bg = bg
        self.hover_bg = hover_bg

        btn_kwargs = {
            "text": text,
            "command": command,
            "bg": bg,
            "fg": fg,
            "activebackground": hover_bg,
            "activeforeground": fg,
            "font": font,
            "bd": 0,
            "relief": "flat",
            "cursor": "hand2",
            "padx": padx,
            "pady": pady,
            **kwargs
        }
        if width:
            btn_kwargs["width"] = width

        super().__init__(parent, **btn_kwargs)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _on_enter(self, _):
        if self["state"] != tk.DISABLED:
            self.configure(bg=self.hover_bg)

    def _on_leave(self, _):
        if self["state"] != tk.DISABLED:
            self.configure(bg=self.normal_bg)

    def set_colors(self, bg, hover_bg):
        self.normal_bg = bg
        self.hover_bg = hover_bg
        self.configure(bg=bg, activebackground=hover_bg)


class StatCard(tk.Frame):
    """A polished KPI summary card displaying icon/badge, metric value, and label."""

    def __init__(self, parent, title, value, icon="📊", color=THEME["text_accent"], **kwargs):
        super().__init__(parent, bg=THEME["bg_card"], bd=1, relief="ridge", padx=16, pady=14, **kwargs)

        header_frame = tk.Frame(self, bg=THEME["bg_card"])
        header_frame.pack(fill="x")

        lbl_icon = tk.Label(header_frame, text=icon, font=(FONT_FAMILY, 14), bg=THEME["bg_card"], fg=color)
        lbl_icon.pack(side="left")

        lbl_title = tk.Label(header_frame, text=f" {title}", font=FONTS["stat_lbl"], bg=THEME["bg_card"], fg=THEME["text_secondary"])
        lbl_title.pack(side="left")

        self.lbl_value = tk.Label(self, text=str(value), font=FONTS["stat_num"], bg=THEME["bg_card"], fg=color)
        self.lbl_value.pack(anchor="w", pady=(6, 0))

    def update_value(self, new_value):
        self.lbl_value.configure(text=str(new_value))


class ScrollableFrame(tk.Frame):
    """Reusable scrollable frame container using Canvas & Scrollbar."""

    def __init__(self, parent, bg=THEME["bg_main"], **kwargs):
        super().__init__(parent, bg=bg, **kwargs)

        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_content = tk.Frame(self.canvas, bg=bg)

        self.scrollable_content.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_content, anchor="nw")

        def _on_canvas_configure(e):
            self.canvas.itemconfig(self.canvas_window, width=e.width)

        self.canvas.bind("<Configure>", _on_canvas_configure)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Mouse wheel support
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)
