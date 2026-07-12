"""
FL Studio Project Name Manager
GUI components — Tkinter/TTK widgets and main application window.
"""

import os
import sys
import json
import threading
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# ── DPI Awareness (Windows) ──────────────────────────────────────────────────
if sys.platform.startswith("win"):
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

from fl_project_scanner import FLProject, scan_directory, scan_directory_recursive
from excel_exporter import export_to_excel



# ── Color palette ────────────────────────────────────────────────────────────
BG_DARK       = "#0F0F1A"
BG_CARD       = "#1A1A2E"
BG_CARD_HOVER = "#222240"
ACCENT        = "#6C63FF"
ACCENT_HOVER  = "#5A52D5"
ACCENT_LIGHT  = "#A29BFE"
SUCCESS       = "#00C9A7"
WARNING       = "#FFB347"
DANGER        = "#FF6B6B"
TEXT_PRIMARY   = "#EAEAEA"
TEXT_SECONDARY = "#8D8DA0"
BORDER_SUBTLE  = "#2A2A42"

SETTINGS_FILE = Path.home() / ".fl_project_manager_settings.json"


class ScrollableFrame(tk.Frame):
    """A standard Tkinter frame with a scrollbar, mimicking CTkScrollableFrame."""
    
    def __init__(self, container, bg=BG_DARK, *args, **kwargs):
        super().__init__(container, bg=bg, *args, **kwargs)
        
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self, bg=bg)
        
        self.scrollable_frame_id = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        self.scrollable_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.canvas.bind("<Enter>", self._bind_mousewheel)
        self.canvas.bind("<Leave>", self._unbind_mousewheel)
        self.scrollable_frame.bind("<Enter>", self._bind_mousewheel)
        self.scrollable_frame.bind("<Leave>", self._unbind_mousewheel)

    def _on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        # Stretch inner frame to match canvas width
        self.canvas.itemconfig(self.scrollable_frame_id, width=event.width)

    def _bind_mousewheel(self, event):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbind_mousewheel(self, event):
        self.canvas.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


class FilterToggleBar(tk.Frame):
    """A row of mutually-exclusive toggle buttons for filtering."""

    def __init__(self, master, labels, variable, command=None, **kwargs):
        super().__init__(master, bg=BG_DARK, **kwargs)
        self.variable = variable
        self.command = command
        self.buttons: dict[str, tk.Label] = {}

        for label in labels:
            btn = tk.Label(
                self,
                text=label,
                font=("Segoe UI", 11),
                fg=TEXT_SECONDARY,
                bg=BG_DARK,
                padx=14,
                pady=5,
                cursor="hand2",
            )
            btn.pack(side="left", padx=(0, 4))
            btn.bind("<Button-1>", lambda e, l=label: self._select(l))
            btn.bind("<Enter>", lambda e, b=btn, l=label: self._on_enter(b, l))
            btn.bind("<Leave>", lambda e, b=btn, l=label: self._on_leave(b, l))
            self.buttons[label] = btn

        # Highlight the initial selection
        self._highlight(variable.get())

    def _select(self, label):
        self.variable.set(label)
        self._highlight(label)
        if self.command:
            self.command()

    def _highlight(self, active_label):
        for label, btn in self.buttons.items():
            if label == active_label:
                btn.configure(bg=ACCENT, fg=TEXT_PRIMARY)
            else:
                btn.configure(bg=BG_DARK, fg=TEXT_SECONDARY)

    def _on_enter(self, btn, label):
        if self.variable.get() != label:
            btn.configure(bg=BORDER_SUBTLE)

    def _on_leave(self, btn, label):
        if self.variable.get() != label:
            btn.configure(bg=BG_DARK)


class HoverButton(tk.Button):
    """A flat styled tk.Button with hover effects."""
    
    def __init__(self, master, text, bg, active_bg, fg=TEXT_PRIMARY, font=("Segoe UI", 11, "bold"), command=None, **kwargs):
        super().__init__(
            master,
            text=text,
            bg=bg,
            fg=fg,
            activebackground=active_bg,
            activeforeground=fg,
            font=font,
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            command=command,
            cursor="hand2",
            **kwargs
        )
        self.default_bg = bg
        self.active_bg = active_bg
        self.disabled_bg = "#2D2D3F"
        self.disabled_fg = "#6D6D7F"
        
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _on_enter(self, event):
        if self["state"] == "normal":
            try:
                self.configure(bg=self.active_bg)
            except tk.TclError:
                pass

    def _on_leave(self, event):
        if self["state"] == "normal":
            try:
                self.configure(bg=self.default_bg)
            except tk.TclError:
                pass
            
    def configure(self, **kwargs):
        if "state" in kwargs:
            state = kwargs["state"]
            if state == "disabled":
                kwargs["bg"] = self.disabled_bg
                kwargs["fg"] = self.disabled_fg
            elif state == "normal":
                kwargs["bg"] = self.default_bg
                kwargs["fg"] = TEXT_PRIMARY
        super().configure(**kwargs)


class PlaceholderEntry(tk.Entry):
    """A styled tk.Entry inside a custom Frame to get inner padding and borders."""
    
    def __init__(self, master, placeholder_text="", font=("Segoe UI", 11), bg=BG_CARD, fg=TEXT_PRIMARY, border_color=BORDER_SUBTLE, **kwargs):
        self.frame = tk.Frame(master, bg=bg, highlightthickness=1, highlightbackground=border_color, highlightcolor=ACCENT)
        
        super().__init__(
            self.frame,
            font=font,
            bg=bg,
            fg=fg,
            insertbackground=fg,
            relief="flat",
            bd=0,
            **kwargs
        )
        super().pack(fill="both", expand=True, padx=10, pady=8)
        
        self.placeholder_text = placeholder_text
        self.placeholder_color = TEXT_SECONDARY
        self.default_color = fg
        self._showing_placeholder = False
        
        self.bind("<FocusIn>", self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)
        
        self.bind("<FocusIn>", lambda e: [self._on_focus_in(e), self.frame.configure(highlightbackground=ACCENT)], add="+")
        self.bind("<FocusOut>", lambda e: [self._on_focus_out(e), self.frame.configure(highlightbackground=border_color)], add="+")
        
        self._show_placeholder()
        
    def _show_placeholder(self):
        if not super().get() and self.placeholder_text:
            self._showing_placeholder = True
            self.configure(fg=self.placeholder_color)
            self.insert(0, self.placeholder_text)
            
    def _on_focus_in(self, event):
        if self._showing_placeholder:
            self._showing_placeholder = False
            self.delete(0, tk.END)
            self.configure(fg=self.default_color)
            
    def _on_focus_out(self, event):
        if not super().get():
            self._show_placeholder()

    def get(self):
        if self._showing_placeholder:
            return ""
        return super().get()

    def set_text(self, text):
        self._showing_placeholder = False
        self.delete(0, tk.END)
        self.configure(fg=self.default_color)
        self.insert(0, text)
        if not text:
            self._show_placeholder()

    def pack(self, **kwargs):
        self.frame.pack(**kwargs)
        
    def grid(self, **kwargs):
        self.frame.grid(**kwargs)
        
    def place(self, **kwargs):
        self.frame.place(**kwargs)


class ProjectCard(tk.Frame):
    """A visual card representing one FL Studio project folder."""

    def __init__(self, master, project: FLProject, index: int, **kwargs):
        super().__init__(
            master,
            bg=BG_CARD,
            highlightthickness=1,
            highlightbackground=BORDER_SUBTLE,
            **kwargs,
        )
        self.project = project
        self.grid_columnconfigure(1, weight=1)

        # ── Index badge ──────────────────────────────────────────────────
        badge = tk.Label(
            self,
            text=f"#{index}",
            font=("Segoe UI", 12, "bold"),
            fg=ACCENT_LIGHT,
            bg=BG_CARD,
            width=5,
        )
        badge.grid(row=0, column=0, rowspan=2, padx=(14, 6), pady=12, sticky="n")

        # ── Project name ─────────────────────────────────────────────────
        name_label = tk.Label(
            self,
            text=project.primary_name,
            font=("Segoe UI", 15, "bold"),
            fg=TEXT_PRIMARY,
            bg=BG_CARD,
            anchor="w",
        )
        name_label.grid(row=0, column=1, padx=(4, 10), pady=(12, 0), sticky="ew")

        # ── Folder path (subtitle) ───────────────────────────────────────
        path_label = tk.Label(
            self,
            text=project.folder_path,
            font=("Segoe UI", 11),
            fg=TEXT_SECONDARY,
            bg=BG_CARD,
            anchor="w",
        )
        path_label.grid(row=1, column=1, padx=(4, 10), pady=(0, 2), sticky="ew")

        # ── Details row ──────────────────────────────────────────────────
        details_frame = tk.Frame(self, bg=BG_CARD)
        details_frame.grid(row=2, column=0, columnspan=3, padx=14, pady=(2, 4), sticky="ew")

        # FLP count
        flp_text = f"🎹 {project.project_count} FLP{'s' if project.project_count != 1 else ''}"
        tk.Label(
            details_frame,
            text=flp_text,
            font=("Segoe UI", 11),
            fg=TEXT_SECONDARY,
            bg=BG_CARD,
        ).pack(side="left", padx=(0, 16))

        # Separate audio vs MIDI counts
        midi_exts = {".mid", ".midi"}
        midi_files = [f for f in project.audio_files if Path(f).suffix.lower() in midi_exts]
        audio_only = [f for f in project.audio_files if Path(f).suffix.lower() not in midi_exts]

        if audio_only:
            tk.Label(
                details_frame,
                text=f"🔊 {len(audio_only)} audio",
                font=("Segoe UI", 11),
                fg=SUCCESS,
                bg=BG_CARD,
            ).pack(side="left", padx=(0, 12))

        if midi_files:
            tk.Label(
                details_frame,
                text=f"🎼 {len(midi_files)} MIDI",
                font=("Segoe UI", 11),
                fg="#00BCD4",
                bg=BG_CARD,
            ).pack(side="left", padx=(0, 12))

        # FLP file names (collapsed)
        flp_names = ", ".join(Path(f).stem for f in project.flp_files[:4])
        if len(project.flp_files) > 4:
            flp_names += f" (+{len(project.flp_files) - 4} more)"
        tk.Label(
            details_frame,
            text=flp_names,
            font=("Segoe UI", 11, "italic"),
            fg=TEXT_SECONDARY,
            bg=BG_CARD,
        ).pack(side="left", padx=(0, 10))

        # ── Exported file names (prominent) ──────────────────────────────
        if project.audio_files:
            self.export_frame = tk.Frame(self, bg="#1E1E38")
            self.export_frame.grid(row=3, column=0, columnspan=3, padx=14, pady=(0, 12), sticky="ew")

            tk.Label(
                self.export_frame,
                text="📦 Exports:",
                font=("Segoe UI", 11, "bold"),
                fg=ACCENT_LIGHT,
                bg="#1E1E38",
            ).pack(side="left", padx=(10, 6), pady=6)

            export_names = ", ".join(project.audio_files[:6])
            if len(project.audio_files) > 6:
                export_names += f"  (+{len(project.audio_files) - 6} more)"
            tk.Label(
                self.export_frame,
                text=export_names,
                font=("Segoe UI", 12, "bold"),
                fg=SUCCESS,
                bg="#1E1E38",
            ).pack(side="left", padx=(0, 10), pady=6)

        # ── Status badge ─────────────────────────────────────────────────
        if project.status == "Named ✓":
            status_color = SUCCESS
        elif project.status == "Unnamed":
            status_color = WARNING
        else:
            status_color = DANGER

        status_label = tk.Label(
            self,
            text=project.status,
            font=("Segoe UI", 12, "bold"),
            fg=status_color,
            bg=BG_CARD,
            anchor="e",
        )
        status_label.grid(row=0, column=2, rowspan=2, padx=(6, 16), pady=12, sticky="e")

        # ── Hover effect ─────────────────────────────────────────────────
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self._bind_hover_recursive(self)

    def _bind_hover_recursive(self, widget):
        widget.bind("<Enter>", self._on_enter, add="+")
        widget.bind("<Leave>", self._on_leave, add="+")
        for child in widget.winfo_children():
            self._bind_hover_recursive(child)

    def _on_enter(self, event):
        self.configure(bg=BG_CARD_HOVER, highlightbackground=ACCENT)
        self._update_colors(BG_CARD_HOVER)

    def _on_leave(self, event):
        self.configure(bg=BG_CARD, highlightbackground=BORDER_SUBTLE)
        self._update_colors(BG_CARD)

    def _update_colors(self, bg_color):
        export_fr = getattr(self, "export_frame", None)
        def recurse(w):
            if export_fr and (w == export_fr or self._is_descendant_of(w, export_fr)):
                return
            try:
                w.configure(bg=bg_color)
            except tk.TclError:
                pass
            for child in w.winfo_children():
                recurse(child)
        for child in self.winfo_children():
            recurse(child)

    def _is_descendant_of(self, widget, ancestor):
        curr = widget
        while curr:
            if curr == ancestor:
                return True
            parent_name = curr.winfo_parent()
            if not parent_name:
                break
            curr = curr.nametowidget(parent_name)
        return False


class App(tk.Tk):
    """Main application window."""

    def __init__(self):
        super().__init__()

        self.title("FL Studio Project Name Manager")
        
        # Calculate dynamic window resolution based on screen dimensions
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        width = int(screen_width * 0.6)
        height = int(screen_height * 0.7)
        # Ensure sizes remain in reasonable bounds
        width = max(1000, min(width, 1400))
        height = max(650, min(height, 900))
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.minsize(820, 520)
        self.configure(bg=BG_DARK)

        # Apply dark theme styling to TTK scrollbars using clam
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Vertical.TScrollbar",
            troughcolor=BG_DARK,
            background=BORDER_SUBTLE,
            arrowcolor=TEXT_SECONDARY,
            bordercolor=BG_DARK,
            gripcount=0
        )
        style.map(
            "Vertical.TScrollbar",
            background=[("active", ACCENT), ("pressed", ACCENT_HOVER)]
        )

        self.projects: list[FLProject] = []
        self._search_timer = None
        self._build_ui()
        self._apply_settings()

    # ── UI construction ──────────────────────────────────────────────────
    def _build_ui(self):
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # ── Header ───────────────────────────────────────────────────────
        header = tk.Frame(self, bg=BG_CARD, height=70)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(1, weight=1)

        tk.Label(
            header,
            text="🎛️  FL Studio Project Name Manager",
            font=("Segoe UI", 22, "bold"),
            fg=TEXT_PRIMARY,
            bg=BG_CARD,
        ).grid(row=0, column=0, padx=24, pady=18, sticky="w")

        self.settings_btn = HoverButton(
            header,
            text="⚙️",
            bg=BG_CARD,
            active_bg=BG_CARD_HOVER,
            font=("Segoe UI", 18),
            fg=TEXT_SECONDARY,
            command=self._open_settings,
        )
        self.settings_btn.grid(row=0, column=1, padx=(0, 24), pady=18, sticky="e")

        # ── Toolbar ──────────────────────────────────────────────────────
        toolbar = tk.Frame(self, bg=BG_DARK, height=52)
        toolbar.grid(row=1, column=0, sticky="ew", padx=20, pady=(14, 0))
        toolbar.grid_columnconfigure(1, weight=1)

        # Folder path entry
        self.path_entry = PlaceholderEntry(
            toolbar,
            placeholder_text="Select your FL Studio projects folder…",
            font=("Segoe UI", 12),
        )
        self.path_entry.grid(row=0, column=0, columnspan=2, sticky="ew", padx=(0, 10))

        # Browse button
        self.browse_btn = HoverButton(
            toolbar,
            text="📂  Browse",
            bg=ACCENT,
            active_bg=ACCENT_HOVER,
            command=self._browse_folder,
        )
        self.browse_btn.grid(row=0, column=2, padx=(0, 8), ipady=5, ipadx=10)

        # Scan button
        self.scan_btn = HoverButton(
            toolbar,
            text="🔍  Scan",
            bg=ACCENT,
            active_bg=ACCENT_HOVER,
            command=self._start_scan,
        )
        self.scan_btn.grid(row=0, column=3, padx=(0, 8), ipady=5, ipadx=10)

        # Refresh button
        self.refresh_btn = HoverButton(
            toolbar,
            text="🔄  Refresh",
            bg="#FF8C00",
            active_bg="#CC7000",
            command=self._refresh_scan,
            state="disabled",
        )
        self.refresh_btn.grid(row=0, column=4, padx=(0, 8), ipady=5, ipadx=10)

        # Recursive toggle
        self.recursive_var = tk.BooleanVar(value=False)
        self.recursive_cb = tk.Checkbutton(
            toolbar,
            text="Deep scan",
            font=("Segoe UI", 11),
            variable=self.recursive_var,
            fg=TEXT_SECONDARY,
            bg=BG_DARK,
            activeforeground=TEXT_PRIMARY,
            activebackground=BG_DARK,
            selectcolor=BG_CARD,
            relief="flat",
            bd=0,
            highlightthickness=0,
            cursor="hand2"
        )
        self.recursive_cb.grid(row=0, column=5, padx=(6, 8))

        # Bind F5 to refresh
        self.bind("<F5>", lambda e: self._refresh_scan())

        # Export button
        self.export_btn = HoverButton(
            toolbar,
            text="📊  Export Excel",
            bg="#2E7D32",
            active_bg="#1B5E20",
            command=self._export_excel,
            state="disabled",
        )
        self.export_btn.grid(row=0, column=6, ipady=5, ipadx=10)

        # ── Stats bar ────────────────────────────────────────────────────
        self.stats_frame = tk.Frame(self, bg=BG_DARK, height=32)
        self.stats_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=(6, 4))

        self.stats_label = tk.Label(
            self.stats_frame,
            text="No projects scanned yet.  Select a folder and press Scan.",
            font=("Segoe UI", 12),
            fg=TEXT_SECONDARY,
            bg=BG_DARK,
        )
        self.stats_label.pack(side="left")

        # ── Filter bar ───────────────────────────────────────────────────
        filter_bar = tk.Frame(self, bg=BG_DARK, height=36)
        filter_bar.grid(row=4, column=0, sticky="ew", padx=20, pady=(0, 6))

        self.filter_var = tk.StringVar(value="All")
        self.filter_toggle = FilterToggleBar(
            filter_bar,
            labels=("All", "Named ✓", "Unnamed", "Empty"),
            variable=self.filter_var,
            command=self._apply_filter,
        )
        self.filter_toggle.pack(side="left")

        # Search
        self.search_entry = PlaceholderEntry(
            filter_bar,
            placeholder_text="🔎  Search projects…",
            font=("Segoe UI", 11),
        )
        self.search_entry.pack(side="right")
        self.search_entry.bind("<KeyRelease>", self._on_search_change)

        # ── Scrollable results area ──────────────────────────────────────
        self.scroll_frame = ScrollableFrame(self)
        self.scroll_frame.grid(row=2, column=0, sticky="nsew", padx=16, pady=(10, 0))
        self.scroll_frame.scrollable_frame.grid_columnconfigure(0, weight=1)

        # Welcome placeholder
        self._show_welcome()

    def _on_search_change(self, event=None):
        if self._search_timer is not None:
            self.after_cancel(self._search_timer)
        self._search_timer = self.after(300, self._apply_filter)

    # ── Welcome screen ───────────────────────────────────────────────────
    def _show_welcome(self):
        for widget in self.scroll_frame.scrollable_frame.winfo_children():
            widget.destroy()

        welcome = tk.Frame(self.scroll_frame.scrollable_frame, bg=BG_DARK)
        welcome.grid(row=0, column=0, pady=80, sticky="n")

        tk.Label(
            welcome,
            text="🎹",
            font=("Segoe UI", 64),
            fg=TEXT_PRIMARY,
            bg=BG_DARK
        ).pack()
        tk.Label(
            welcome,
            text="Welcome to FL Studio Project Name Manager",
            font=("Segoe UI", 20, "bold"),
            fg=TEXT_PRIMARY,
            bg=BG_DARK
        ).pack(pady=(10, 4))
        tk.Label(
            welcome,
            text="Select your FL Studio projects folder and click Scan to get started.",
            font=("Segoe UI", 14),
            fg=TEXT_SECONDARY,
            bg=BG_DARK
        ).pack()

    # ── Actions ──────────────────────────────────────────────────────────
    def _browse_folder(self):
        folder = filedialog.askdirectory(title="Select FL Studio Projects Folder")
        if folder:
            self.path_entry.set_text(folder)

    def _refresh_scan(self):
        """Re-scan the same folder (shortcut: F5)."""
        path = self.path_entry.get().strip()
        if path and os.path.isdir(path):
            self._start_scan()

    def _start_scan(self):
        path = self.path_entry.get().strip()
        if not path or not os.path.isdir(path):
            messagebox.showwarning("Invalid Path", "Please select a valid directory first.")
            return

        # Disable controls during scan
        self.scan_btn.configure(state="disabled")
        self.scan_btn.configure(text="⏳ Scanning…")
        self.refresh_btn.configure(state="disabled")
        self.browse_btn.configure(state="disabled")
        self.export_btn.configure(state="disabled")

        # Clear current results
        for widget in self.scroll_frame.scrollable_frame.winfo_children():
            widget.destroy()

        # Run scan in a thread to keep the UI responsive
        threading.Thread(target=self._do_scan, args=(path,), daemon=True).start()

    def _do_scan(self, path: str):
        try:
            if self.recursive_var.get():
                results = scan_directory_recursive(path)
            else:
                results = scan_directory(path, depth=1)
                root_result = scan_directory(path, depth=0)
                results = root_result + results
            self.projects = results
            self.after(0, self._display_results)
        except Exception as e:
            self.after(0, lambda em=str(e): self._on_scan_error(em))

    def _on_scan_error(self, error_msg: str):
        self.scan_btn.configure(state="normal")
        self.scan_btn.configure(text="🔍  Scan")
        self.refresh_btn.configure(state="normal")
        self.browse_btn.configure(state="normal")
        messagebox.showerror("Scan Error", f"An error occurred while scanning:\n{error_msg}")

    def _display_results(self):
        self.scan_btn.configure(state="normal")
        self.scan_btn.configure(text="🔍  Scan")
        self.refresh_btn.configure(state="normal")
        self.browse_btn.configure(state="normal")

        if self.projects:
            self.export_btn.configure(state="normal")

        # Store original index so it persists through search/filter
        for i, project in enumerate(self.projects, start=1):
            project._original_index = i

        self._apply_filter()

    def _apply_filter(self):
        """Rebuild the card list based on the current filter and search query."""
        for widget in self.scroll_frame.scrollable_frame.winfo_children():
            widget.destroy()

        filter_val = self.filter_var.get()
        search_q = self.search_entry.get().strip().lower()

        filtered = []
        for p in self.projects:
            # Status filter
            if filter_val != "All" and p.status != filter_val:
                continue
            # Search filter
            if search_q:
                haystack = f"{p.folder_name} {p.primary_name} {' '.join(p.flp_files)}".lower()
                if search_q not in haystack:
                    continue
            filtered.append(p)

        if not filtered and not self.projects:
            self._show_welcome()
            return

        if not filtered:
            tk.Label(
                self.scroll_frame.scrollable_frame,
                text="No projects match the current filter.",
                font=("Segoe UI", 14),
                fg=TEXT_SECONDARY,
                bg=BG_DARK
            ).grid(row=0, column=0, pady=60, sticky="n")
        else:
            for i, project in enumerate(filtered, start=1):
                card = ProjectCard(self.scroll_frame.scrollable_frame, project, project._original_index)
                card.grid(row=i, column=0, sticky="ew", padx=4, pady=4)

        # Stats
        total = len(self.projects)
        named = sum(1 for p in self.projects if p.status == "Named ✓")
        unnamed = sum(1 for p in self.projects if p.status == "Unnamed")
        self.stats_label.configure(
            text=f"📁 {total} projects  •  ✅ {named} named  •  ⚠️ {unnamed} unnamed  •  Showing {len(filtered)}"
        )
        self.update_idletasks()

    def _export_excel(self):
        if not self.projects:
            messagebox.showinfo("Nothing to export", "Scan a folder first.")
            return

        save_path = filedialog.asksaveasfilename(
            title="Save Excel Report",
            defaultextension=".xlsx",
            filetypes=[("Excel Workbook", "*.xlsx")],
            initialfile="fl_studio_projects.xlsx",
        )
        if not save_path:
            return

        try:
            result_path = export_to_excel(self.projects, save_path)
            messagebox.showinfo(
                "Export Complete ✅",
                f"Excel report saved to:\n{result_path}"
            )
        except Exception as e:
            messagebox.showerror("Export Error", f"Could not save Excel file:\n{e}")

    def _load_settings(self):
        try:
            with open(SETTINGS_FILE, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save_settings(self, data):
        with open(SETTINGS_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def _apply_settings(self):
        settings = self._load_settings()
        default_path = settings.get("default_workspace", "")
        if default_path and os.path.isdir(default_path):
            self.path_entry.set_text(default_path)

    def _open_settings(self):
        SettingsDialog(self)


class SettingsDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

        self.title("Settings")
        self.configure(bg=BG_DARK)
        self.resizable(False, False)

        width, height = 600, 200
        px = parent.winfo_rootx() + (parent.winfo_width() - width) // 2
        py = parent.winfo_rooty() + (parent.winfo_height() - height) // 2
        self.geometry(f"{width}x{height}+{px}+{py}")
        self.transient(parent)
        self.grab_set()

        self.grid_columnconfigure(1, weight=1)

        header_label = tk.Label(
            self,
            text="⚙️  Settings",
            font=("Segoe UI", 16, "bold"),
            fg=TEXT_PRIMARY,
            bg=BG_DARK,
        )
        header_label.grid(row=0, column=0, columnspan=4, padx=20, pady=(16, 8), sticky="w")

        tk.Label(
            self,
            text="Default workspace:",
            font=("Segoe UI", 11),
            fg=TEXT_SECONDARY,
            bg=BG_DARK,
        ).grid(row=1, column=0, padx=(20, 8), pady=6, sticky="w")

        self.path_var = tk.StringVar(value="None")
        self.path_label = tk.Label(
            self,
            textvariable=self.path_var,
            font=("Segoe UI", 11),
            fg=TEXT_SECONDARY,
            bg=BG_DARK,
            anchor="w",
        )
        self.path_label.grid(row=1, column=1, padx=(0, 6), pady=6, sticky="ew")

        browse_btn = HoverButton(
            self,
            text="📂",
            bg=ACCENT,
            active_bg=ACCENT_HOVER,
            font=("Segoe UI", 12),
            fg=TEXT_PRIMARY,
            command=self._browse_workspace,
        )
        browse_btn.grid(row=1, column=2, padx=(0, 4), pady=6, ipady=3, ipadx=6)

        clear_btn = HoverButton(
            self,
            text="✕",
            bg=DANGER,
            active_bg="#CC5555",
            font=("Segoe UI", 12, "bold"),
            fg=TEXT_PRIMARY,
            command=self._clear_workspace,
        )
        clear_btn.grid(row=1, column=3, padx=(0, 4), pady=6, ipady=3, ipadx=8)

        close_btn = HoverButton(
            self,
            text="Close",
            bg=ACCENT,
            active_bg=ACCENT_HOVER,
            font=("Segoe UI", 11),
            fg=TEXT_PRIMARY,
            command=self.destroy,
        )
        close_btn.grid(row=2, column=0, columnspan=4, padx=20, pady=(12, 16), sticky="e", ipady=5, ipadx=14)

        self._refresh_path_display()

    def _refresh_path_display(self):
        settings = self.parent._load_settings()
        default_path = settings.get("default_workspace", "")
        if default_path and os.path.isdir(default_path):
            self.path_var.set(default_path)
            self.path_label.configure(fg=TEXT_PRIMARY)
        else:
            self.path_var.set("None")
            self.path_label.configure(fg=TEXT_SECONDARY)

    def _browse_workspace(self):
        folder = filedialog.askdirectory(title="Select Default Workspace Folder")
        if folder:
            settings = self.parent._load_settings()
            settings["default_workspace"] = folder
            self.parent._save_settings(settings)
            self.parent.path_entry.set_text(folder)
            self._refresh_path_display()

    def _clear_workspace(self):
        settings = self.parent._load_settings()
        settings.pop("default_workspace", None)
        self.parent._save_settings(settings)
        self.parent.path_entry.set_text("")
        self._refresh_path_display()
