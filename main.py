"""
FL Studio Project Name Manager
Main GUI application — built with CustomTkinter.
"""

import os
import sys
import threading
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from fl_project_scanner import FLProject, scan_directory, scan_directory_recursive
from excel_exporter import export_to_excel


# ── Appearance ───────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

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


class ProjectCard(ctk.CTkFrame):
    """A visual card representing one FL Studio project folder."""

    def __init__(self, master, project: FLProject, index: int, **kwargs):
        super().__init__(
            master,
            fg_color=BG_CARD,
            corner_radius=12,
            border_width=1,
            border_color=BORDER_SUBTLE,
            **kwargs,
        )
        self.project = project
        self.grid_columnconfigure(1, weight=1)

        # ── Index badge ──────────────────────────────────────────────────
        badge = ctk.CTkLabel(
            self,
            text=f"#{index}",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=ACCENT_LIGHT,
            width=42,
        )
        badge.grid(row=0, column=0, rowspan=2, padx=(14, 6), pady=12, sticky="n")

        # ── Project name ─────────────────────────────────────────────────
        name_label = ctk.CTkLabel(
            self,
            text=project.primary_name,
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color=TEXT_PRIMARY,
            anchor="w",
        )
        name_label.grid(row=0, column=1, padx=(4, 10), pady=(12, 0), sticky="ew")

        # ── Folder path (subtitle) ───────────────────────────────────────
        path_label = ctk.CTkLabel(
            self,
            text=project.folder_path,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=TEXT_SECONDARY,
            anchor="w",
        )
        path_label.grid(row=1, column=1, padx=(4, 10), pady=(0, 2), sticky="ew")

        # ── Details row ──────────────────────────────────────────────────
        details_frame = ctk.CTkFrame(self, fg_color="transparent")
        details_frame.grid(row=2, column=0, columnspan=3, padx=14, pady=(2, 4), sticky="ew")

        # FLP count
        flp_text = f"🎹 {project.project_count} FLP{'s' if project.project_count != 1 else ''}"
        ctk.CTkLabel(
            details_frame,
            text=flp_text,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=TEXT_SECONDARY,
        ).pack(side="left", padx=(0, 16))

        # Separate audio vs MIDI counts
        midi_exts = {".mid", ".midi"}
        midi_files = [f for f in project.audio_files if Path(f).suffix.lower() in midi_exts]
        audio_only = [f for f in project.audio_files if Path(f).suffix.lower() not in midi_exts]

        if audio_only:
            ctk.CTkLabel(
                details_frame,
                text=f"🔊 {len(audio_only)} audio",
                font=ctk.CTkFont(family="Segoe UI", size=11),
                text_color=SUCCESS,
            ).pack(side="left", padx=(0, 12))

        if midi_files:
            ctk.CTkLabel(
                details_frame,
                text=f"🎼 {len(midi_files)} MIDI",
                font=ctk.CTkFont(family="Segoe UI", size=11),
                text_color="#00BCD4",
            ).pack(side="left", padx=(0, 12))

        # FLP file names (collapsed)
        flp_names = ", ".join(Path(f).stem for f in project.flp_files[:4])
        if len(project.flp_files) > 4:
            flp_names += f" (+{len(project.flp_files) - 4} more)"
        ctk.CTkLabel(
            details_frame,
            text=flp_names,
            font=ctk.CTkFont(family="Segoe UI", size=11, slant="italic"),
            text_color=TEXT_SECONDARY,
        ).pack(side="left", padx=(0, 10))

        # ── Exported file names (prominent) ──────────────────────────────
        if project.audio_files:
            export_frame = ctk.CTkFrame(self, fg_color="#1E1E38", corner_radius=8)
            export_frame.grid(row=3, column=0, columnspan=3, padx=14, pady=(0, 12), sticky="ew")

            ctk.CTkLabel(
                export_frame,
                text="📦 Exports:",
                font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                text_color=ACCENT_LIGHT,
            ).pack(side="left", padx=(10, 6), pady=6)

            export_names = ", ".join(project.audio_files[:6])
            if len(project.audio_files) > 6:
                export_names += f"  (+{len(project.audio_files) - 6} more)"
            ctk.CTkLabel(
                export_frame,
                text=export_names,
                font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                text_color=SUCCESS,
            ).pack(side="left", padx=(0, 10), pady=6)

        # ── Status badge ─────────────────────────────────────────────────
        if project.status == "Named ✓":
            status_color = SUCCESS
        elif project.status == "Unnamed":
            status_color = WARNING
        else:
            status_color = DANGER

        status_label = ctk.CTkLabel(
            self,
            text=project.status,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=status_color,
            width=90,
        )
        status_label.grid(row=0, column=2, rowspan=2, padx=(6, 16), pady=12, sticky="e")

        # ── Hover effect ─────────────────────────────────────────────────
        self.bind("<Enter>", lambda e: self.configure(fg_color=BG_CARD_HOVER, border_color=ACCENT))
        self.bind("<Leave>", lambda e: self.configure(fg_color=BG_CARD, border_color=BORDER_SUBTLE))


class App(ctk.CTk):
    """Main application window."""

    def __init__(self):
        super().__init__()

        self.title("FL Studio Project Name Manager")
        self.geometry("1060x720")
        self.minsize(820, 520)
        self.configure(fg_color=BG_DARK)

        self.projects: list[FLProject] = []
        self._build_ui()

    # ── UI construction ──────────────────────────────────────────────────
    def _build_ui(self):
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # ── Header ───────────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=0, height=70)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            header,
            text="🎛️  FL Studio Project Name Manager",
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).grid(row=0, column=0, padx=24, pady=18, sticky="w")

        # ── Toolbar ──────────────────────────────────────────────────────
        toolbar = ctk.CTkFrame(self, fg_color=BG_DARK, height=52)
        toolbar.grid(row=1, column=0, sticky="ew", padx=20, pady=(14, 0))
        toolbar.grid_columnconfigure(1, weight=1)

        # Folder path entry
        self.path_var = ctk.StringVar()
        self.path_entry = ctk.CTkEntry(
            toolbar,
            textvariable=self.path_var,
            placeholder_text="Select your FL Studio projects folder…",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            height=40,
            corner_radius=10,
            border_color=BORDER_SUBTLE,
            fg_color=BG_CARD,
            text_color=TEXT_PRIMARY,
        )
        self.path_entry.grid(row=0, column=0, columnspan=2, sticky="ew", padx=(0, 10))

        # Browse button
        self.browse_btn = ctk.CTkButton(
            toolbar,
            text="📂  Browse",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            width=120,
            height=40,
            corner_radius=10,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            command=self._browse_folder,
        )
        self.browse_btn.grid(row=0, column=2, padx=(0, 8))

        # Scan button
        self.scan_btn = ctk.CTkButton(
            toolbar,
            text="🔍  Scan",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            width=110,
            height=40,
            corner_radius=10,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            command=self._start_scan,
        )
        self.scan_btn.grid(row=0, column=3, padx=(0, 8))

        # Refresh button
        self.refresh_btn = ctk.CTkButton(
            toolbar,
            text="🔄  Refresh",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            width=120,
            height=40,
            corner_radius=10,
            fg_color="#FF8C00",
            hover_color="#CC7000",
            command=self._refresh_scan,
            state="disabled",
        )
        self.refresh_btn.grid(row=0, column=4, padx=(0, 8))

        # Recursive toggle
        self.recursive_var = ctk.BooleanVar(value=False)
        self.recursive_cb = ctk.CTkCheckBox(
            toolbar,
            text="Deep scan",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            variable=self.recursive_var,
            text_color=TEXT_SECONDARY,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            corner_radius=6,
        )
        self.recursive_cb.grid(row=0, column=5, padx=(6, 8))

        # Bind F5 to refresh
        self.bind("<F5>", lambda e: self._refresh_scan())

        # Export button
        self.export_btn = ctk.CTkButton(
            toolbar,
            text="📊  Export Excel",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            width=140,
            height=40,
            corner_radius=10,
            fg_color="#2E7D32",
            hover_color="#1B5E20",
            command=self._export_excel,
            state="disabled",
        )
        self.export_btn.grid(row=0, column=6)

        # ── Stats bar ────────────────────────────────────────────────────
        self.stats_frame = ctk.CTkFrame(self, fg_color=BG_DARK, height=32)
        self.stats_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=(6, 4))

        self.stats_label = ctk.CTkLabel(
            self.stats_frame,
            text="No projects scanned yet.  Select a folder and press Scan.",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=TEXT_SECONDARY,
        )
        self.stats_label.pack(side="left")

        # ── Filter bar ───────────────────────────────────────────────────
        filter_bar = ctk.CTkFrame(self, fg_color=BG_DARK, height=36)
        filter_bar.grid(row=4, column=0, sticky="ew", padx=20, pady=(0, 6))

        self.filter_var = ctk.StringVar(value="All")
        for label in ("All", "Named ✓", "Unnamed", "Empty"):
            ctk.CTkRadioButton(
                filter_bar,
                text=label,
                variable=self.filter_var,
                value=label,
                font=ctk.CTkFont(family="Segoe UI", size=12),
                text_color=TEXT_SECONDARY,
                fg_color=ACCENT,
                hover_color=ACCENT_HOVER,
                command=self._apply_filter,
            ).pack(side="left", padx=(0, 18))

        # Search
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._apply_filter())
        search_entry = ctk.CTkEntry(
            filter_bar,
            textvariable=self.search_var,
            placeholder_text="🔎  Search projects…",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            height=32,
            width=220,
            corner_radius=8,
            border_color=BORDER_SUBTLE,
            fg_color=BG_CARD,
            text_color=TEXT_PRIMARY,
        )
        search_entry.pack(side="right")

        # ── Scrollable results area ──────────────────────────────────────
        self.scroll_frame = ctk.CTkScrollableFrame(
            self,
            fg_color=BG_DARK,
            corner_radius=0,
            scrollbar_button_color=BORDER_SUBTLE,
            scrollbar_button_hover_color=ACCENT,
        )
        self.scroll_frame.grid(row=2, column=0, sticky="nsew", padx=16, pady=(10, 0))
        self.scroll_frame.grid_columnconfigure(0, weight=1)

        # Welcome placeholder
        self._show_welcome()

    # ── Welcome screen ───────────────────────────────────────────────────
    def _show_welcome(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        welcome = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        welcome.grid(row=0, column=0, pady=80)

        ctk.CTkLabel(
            welcome,
            text="🎹",
            font=ctk.CTkFont(size=64),
        ).pack()
        ctk.CTkLabel(
            welcome,
            text="Welcome to FL Studio Project Name Manager",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).pack(pady=(10, 4))
        ctk.CTkLabel(
            welcome,
            text="Select your FL Studio projects folder and click Scan to get started.",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            text_color=TEXT_SECONDARY,
        ).pack()

    # ── Actions ──────────────────────────────────────────────────────────
    def _browse_folder(self):
        folder = filedialog.askdirectory(title="Select FL Studio Projects Folder")
        if folder:
            self.path_var.set(folder)

    def _refresh_scan(self):
        """Re-scan the same folder (shortcut: F5)."""
        path = self.path_var.get().strip()
        if path and os.path.isdir(path):
            self._start_scan()

    def _start_scan(self):
        path = self.path_var.get().strip()
        if not path or not os.path.isdir(path):
            messagebox.showwarning("Invalid Path", "Please select a valid directory first.")
            return

        # Disable controls during scan
        self.scan_btn.configure(state="disabled", text="⏳ Scanning…")
        self.refresh_btn.configure(state="disabled")
        self.browse_btn.configure(state="disabled")
        self.export_btn.configure(state="disabled")

        # Clear current results
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        # Run scan in a thread to keep the UI responsive
        threading.Thread(target=self._do_scan, args=(path,), daemon=True).start()

    def _do_scan(self, path: str):
        if self.recursive_var.get():
            results = scan_directory_recursive(path)
        else:
            results = scan_directory(path, depth=1)

        self.projects = results
        # Update UI on the main thread
        self.after(0, self._display_results)

    def _display_results(self):
        self.scan_btn.configure(state="normal", text="🔍  Scan")
        self.refresh_btn.configure(state="normal")
        self.browse_btn.configure(state="normal")

        if self.projects:
            self.export_btn.configure(state="normal")

        self._apply_filter()

    def _apply_filter(self):
        """Rebuild the card list based on the current filter and search query."""
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        filter_val = self.filter_var.get()
        search_q = self.search_var.get().strip().lower()

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
            ctk.CTkLabel(
                self.scroll_frame,
                text="No projects match the current filter.",
                font=ctk.CTkFont(family="Segoe UI", size=14),
                text_color=TEXT_SECONDARY,
            ).grid(row=0, column=0, pady=60)
        else:
            for i, project in enumerate(filtered, start=1):
                card = ProjectCard(self.scroll_frame, project, i)
                card.grid(row=i, column=0, sticky="ew", padx=4, pady=4)

        # Stats
        total = len(self.projects)
        named = sum(1 for p in self.projects if p.status == "Named ✓")
        unnamed = sum(1 for p in self.projects if p.status == "Unnamed")
        self.stats_label.configure(
            text=f"📁 {total} projects  •  ✅ {named} named  •  ⚠️ {unnamed} unnamed  •  Showing {len(filtered)}"
        )

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


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
