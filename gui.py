"""
gui.py - Bookmark Rescue Toolkit
==================================
Unified graphical front-end for the five-stage bookmark recovery workflow.

  Tab 1 · Extractor      Scan Windows.old → copy raw browser files
  Tab 2 · JSON Parser    Convert a single Chromium Bookmarks file → HTML
  Tab 3 · SQLite Parser  Convert a single Firefox places.sqlite → HTML
  Tab 4 · Vault Builder  Batch-convert all extracted files → Netscape HTML dashboard
  Tab 5 · Merger         Merge & deduplicate bookmarks from multiple sources;
                         export to CSV or JSON for Notion, Airtable, Excel, etc.

Header utilities:
  🔍 Search   - live search across all extracted sources
  View Docs   - tabbed in-app documentation viewer

Threading model
---------------
Long-running operations run on daemon threads so the GUI stays responsive.
All widget updates are posted to a Queue and drained by the main thread
via after() - the only safe pattern for Tkinter.

Persistence
-----------
Last-used paths are saved to config.json (next to gui.py) on close and
restored on launch.

Requirements
------------
  pip install customtkinter
"""

import json
import os
import queue
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from core.version         import __version__
from core.json_to_html    import convert_json_to_html
from core.retriever       import recover_bookmarks
from core.sqlite_to_html  import convert_sqlite_to_html
from core.vault_builder   import build_vault
from core.bookmark_merger import (
    merge_sources, export_to_csv, export_to_json,
    sources_from_manifest,
)
from core.search import search_bookmarks
from core.utils  import get_human_date

# ---------------------------------------------------------------------------
# Appearance defaults
# ---------------------------------------------------------------------------
ctk.set_appearance_mode("Dark")      # "System" | "Dark" | "Light" - overridden by config.json
ctk.set_default_color_theme("blue")  # "blue"   | "green" | "dark-blue"

def _get_base_path() -> Path:
    """Return the application base directory in both source and frozen (PyInstaller) builds.

    When running from source:       the folder containing gui.py.
    When running as a .exe bundle:  the folder containing the .exe.

    This keeps docs/, README.md, icons, and config.json next to the
    executable where the user can access them, not in a temp directory.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent


_HERE        = _get_base_path()
_CONFIG_PATH = _HERE / "config.json"
# BUILDING.md is only meaningful in the source repo -- it describes how to
# create this very executable. When running as a portable .exe it is excluded
# from the bundle and replaced with an inline message in the doc viewer.
_IS_FROZEN = getattr(sys, "frozen", False)

_DOC_FILES = [
    ("README",          _HERE / "README.md"),
    ("GUI Walkthrough", _HERE / "docs" / "GUI_WALKTHROUGH.md"),
    ("CLI Tools",       _HERE / "docs" / "MANUAL_TOOLS.md"),
    ("Customization",   _HERE / "docs" / "CUSTOMIZATION.md"),
    ("Building .exe",   _HERE / "BUILDING.md"),
]

_BUILDING_PORTABLE_MSG = """Building .exe

You are running the portable build of Bookmark Rescue Toolkit.

This tab covers how to build this executable from the Python source -- which
you have already done (or someone did it for you). There is nothing to build.

If you need the full build instructions -- for example, to create a new
release after modifying the source code -- find BUILDING.md in the GitHub
repository alongside the source code.

    https://github.com/YOUR_USERNAME/Bookmark-Rescue-Toolkit

The repository also contains the complete source for all five core engines,
the GUI, and the build pipeline.
"""

_CONFIG_KEYS = ["ext_src", "ext_dest", "vault_src", "vault_dest", "merger_dest", "theme"]


# ---------------------------------------------------------------------------
# Cross-platform file / folder opener
# ---------------------------------------------------------------------------

def _open_path(path: str) -> None:
    if not path or not os.path.exists(path):
        return
    if sys.platform == "win32":
        os.startfile(path)              # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])


def _open_url(url: str) -> None:
    """Open a URL in the default browser (cross-platform)."""
    import webbrowser
    webbrowser.open(url)


# ---------------------------------------------------------------------------
# Minimal Markdown cleaner for the in-app doc viewer
# ---------------------------------------------------------------------------

def _clean_markdown(text: str) -> str:
    lines_out     = []
    in_code_block = False
    for raw in text.splitlines():
        line = raw
        if line.startswith("```"):
            in_code_block = not in_code_block
            lines_out.append("")
            continue
        if in_code_block:
            lines_out.append("    " + line)
            continue
        if line.startswith("######") or line.startswith("#####") or line.startswith("####"):
            lines_out.append("\n  ▸ " + line.lstrip("#").strip()); continue
        if line.startswith("###"):
            lines_out.append("\n▸ " + line.lstrip("#").strip()); continue
        if line.startswith("##"):
            lines_out.append("\n── " + line.lstrip("#").strip().upper() + " ──"); continue
        if line.startswith("#"):
            lines_out.append("\n══ " + line.lstrip("#").strip().upper() + " ══"); continue
        if line.strip() in ("---", "***", "___"):
            lines_out.append("  " + "─" * 62); continue
        for marker in ("**", "__", "*", "_"):
            while marker in line:
                s = line.find(marker)
                e = line.find(marker, s + len(marker))
                if e == -1: break
                line = line[:s] + line[s + len(marker):e] + line[e + len(marker):]
        while "`" in line:
            s = line.find("`"); e = line.find("`", s + 1)
            if e == -1: break
            line = line[:s] + line[s + 1:e] + line[e + 1:]
        if line.startswith("> "):
            line = "  │ " + line[2:]
        lines_out.append(line)
    return "\n".join(lines_out)


# ---------------------------------------------------------------------------
# ToolTip
# ---------------------------------------------------------------------------

class ToolTip:
    def __init__(self, widget: tk.Widget, text: str) -> None:
        self._widget = widget; self._text = text; self._tip_win = None
        widget.bind("<Enter>", self._show)
        widget.bind("<Leave>", self._hide)

    def _show(self, _event=None) -> None:
        if self._tip_win: return
        x = self._widget.winfo_rootx() + 22
        y = self._widget.winfo_rooty() + self._widget.winfo_height() + 6
        self._tip_win = win = tk.Toplevel(self._widget)
        win.wm_overrideredirect(True)
        win.wm_geometry(f"+{x}+{y}")
        tk.Label(win, text=self._text, justify="left",
                 background="#2c2c2c", foreground="#ffffff",
                 relief="solid", borderwidth=1,
                 font=("Arial", 10), padx=6, pady=4).pack()

    def _hide(self, _event=None) -> None:
        if self._tip_win:
            self._tip_win.destroy(); self._tip_win = None


# ---------------------------------------------------------------------------
# Main application
# ---------------------------------------------------------------------------

class BookmarkApp(ctk.CTk):

    _TAB_TIPS = {
        "1: Extractor":
            "Tip: Windows.old folders often need Administrator privileges. "
            "If the scan returns 0 files, right-click your terminal → Run as administrator.",
        "2: JSON Parser":
            "Tip: Extractor missed a custom install? "
            "Browse directly to any Chromium-style Bookmarks file here.",
        "3: SQLite Parser":
            "Tip: Extractor missed a portable browser? "
            "Browse directly to any places.sqlite file here.",
        "4: Vault Builder":
            "Tip: Point this at the folder from Tab 1 to batch-convert everything "
            "into a Netscape HTML dashboard ready for browser import.",
        "5: Merger":
            "Tip: Add sources, then merge into one importable HTML or export as CSV/JSON "
            "for Notion, Airtable, Excel, or any custom database.",
    }

    def __init__(self) -> None:
        super().__init__()
        self.title(f"Bookmark Rescue Toolkit v{__version__}")
        self.geometry("720x760")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._ui_queue:       queue.Queue  = queue.Queue()
        self._doc_win                      = None
        self._search_win                   = None
        self._merger_sources: list[dict]   = []

        # ── Active job tracking (graceful exit) ───────────────────────────
        self._active_jobs:    int           = 0
        self._active_names:   list[str]     = []   # human-readable job names
        self._jobs_lock:      threading.Lock = threading.Lock()

        self._load_icon()

        # ── StringVars ────────────────────────────────────────────────────
        self.ext_src      = ctk.StringVar()
        self.ext_dest     = ctk.StringVar()
        self.json_src     = ctk.StringVar()
        self.json_dest    = ctk.StringVar()
        self.json_browser = ctk.StringVar(value="Google Chrome")
        self.sql_src      = ctk.StringVar()
        self.sql_dest     = ctk.StringVar()
        self.sql_browser  = ctk.StringVar(value="Firefox")
        self.vault_src    = ctk.StringVar()
        self.vault_dest   = ctk.StringVar()
        self.merger_dest  = ctk.StringVar()

        self._merger_dedup = ctk.BooleanVar(value=True)
        self._merger_group = ctk.BooleanVar(value=True)

        self._build_ui()
        self._register_traces()
        self._load_config()
        self.after(100, self._poll_queue)

    # ── Config persistence ─────────────────────────────────────────────────

    def _load_config(self) -> None:
        try:
            data = json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
            for key in _CONFIG_KEYS:
                if key == "theme":
                    # Apply theme immediately if saved; must be called before
                    # widgets are rendered to take full effect.
                    saved_theme = data.get("theme", "")
                    if saved_theme in ("Dark", "Light", "System"):
                        ctk.set_appearance_mode(saved_theme)
                    continue
                var = getattr(self, key, None)
                if var and data.get(key):
                    var.set(data[key])
        except Exception:
            pass

    def _save_config(self) -> None:
        try:
            data = {}
            for key in _CONFIG_KEYS:
                if key == "theme":
                    data["theme"] = ctk.get_appearance_mode()
                else:
                    var = getattr(self, key, None)
                    if var:
                        data[key] = var.get()
            _CONFIG_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception:
            pass

    def _load_icon(self) -> None:
        """Load a custom window icon if one is present next to gui.py.

        Lookup order:
          1. icon.ico  on Windows via iconbitmap()  (native, best quality)
          2. icon.png  on any platform via iconphoto()  (cross-platform fallback)
          3. Default Tkinter icon if neither file exists or both fail to load.

        Each attempt is wrapped independently so a malformed .ico does not
        prevent the .png fallback from being tried.
        """
        ico = _HERE / "icon.ico"
        png = _HERE / "icon.png"

        if sys.platform == "win32" and ico.exists():
            try:
                self.iconbitmap(str(ico))
                return   # success -- no need to try PNG
            except Exception:
                pass     # malformed .ico -- fall through to PNG

        if png.exists():
            try:
                img = tk.PhotoImage(file=str(png))
                self.iconphoto(True, img)
                self._icon_ref = img   # keep reference - GC would blank the icon
            except Exception:
                pass     # malformed .png -- default Tkinter icon used silently

    def _apply_icon_to_toplevel(self, win) -> None:
        """Apply the app icon to a CTkToplevel window.

        CTkToplevel performs internal setup after __init__ that can override
        an immediate iconbitmap call, so the application is scheduled via
        after(). In frozen/sandbox environments mapped drives add latency, so
        we use a longer delay and retry once to ensure the icon sticks.
        wm_iconbitmap(default=...) is used alongside iconbitmap() because it
        persists more reliably on Toplevel windows in PyInstaller builds.
        """
        ico = _HERE / "icon.ico"
        png = _HERE / "icon.png"

        def _apply():
            if sys.platform == "win32" and ico.exists():
                try:
                    win.iconbitmap(str(ico))
                    win.wm_iconbitmap(default=str(ico))
                    return
                except Exception:
                    pass   # malformed .ico -- fall through to PNG
            if png.exists():
                try:
                    img = tk.PhotoImage(file=str(png))
                    win.iconphoto(True, img)
                    win._icon_ref = img
                except Exception:
                    pass   # malformed .png -- default icon used silently

        # Primary attempt at 300ms -- enough for CTkToplevel internal setup
        win.after(300, _apply)
        # Retry at 800ms -- covers mapped-drive / sandbox latency cases
        win.after(800, _apply)

    def _on_close(self) -> None:
        """Graceful exit: warn the user if any background operation is running."""
        with self._jobs_lock:
            count = self._active_jobs
            names = list(self._active_names)

        if count > 0:
            job_list = "\n".join(f"  • {n}" for n in names) if names else "  • An operation"
            proceed  = messagebox.askyesno(
                "Operation in Progress",
                f"The following operation{'s are' if count > 1 else ' is'} still running:\n\n"
                f"{job_list}\n\n"
                "Closing now may leave output files incomplete.\n"
                "Are you sure you want to quit?",
                icon="warning",
            )
            if not proceed:
                return

        self._save_config()
        self.destroy()

    def _job_start(self, name: str) -> None:
        """Record that a background job has started (call from main thread)."""
        with self._jobs_lock:
            self._active_jobs += 1
            self._active_names.append(name)

    def _job_done(self, name: str) -> None:
        """Record that a background job has finished (call from any thread)."""
        with self._jobs_lock:
            self._active_jobs = max(0, self._active_jobs - 1)
            try:
                self._active_names.remove(name)
            except ValueError:
                pass

    # ── Queue: thread-safe widget updates ─────────────────────────────────

    def _poll_queue(self) -> None:
        while not self._ui_queue.empty():
            msg    = self._ui_queue.get_nowait()
            action = msg.get("action")
            if action == "status":
                msg["label"].configure(text=msg["text"],
                                       text_color=msg.get("color", "gray"))
            elif action == "button":
                msg["button"].configure(state=msg["state"])
                if "command" in msg:
                    msg["button"].configure(command=msg["command"])
            elif action == "log":
                self._log_box.configure(state="normal")
                self._log_box.insert("end", msg["text"] + "\n")
                self._log_box.see("end")
                self._log_box.configure(state="disabled")
        self.after(100, self._poll_queue)

    def _q_status(self, label, text: str, color: str = "gray") -> None:
        self._ui_queue.put({"action": "status", "label": label,
                            "text": text, "color": color})

    def _q_button(self, button, state: str, command=None) -> None:
        msg: dict = {"action": "button", "button": button, "state": state}
        if command is not None:
            msg["command"] = command
        self._ui_queue.put(msg)

    def _q_log(self, text: str) -> None:
        self._ui_queue.put({"action": "log", "text": text})

    # ── Helpers ───────────────────────────────────────────────────────────

    def _register_traces(self) -> None:
        pairs = [
            (self.ext_src,   self.ext_dest,   lambda: self.ext_status),
            (self.json_src,  self.json_dest,  lambda: self.json_status),
            (self.sql_src,   self.sql_dest,   lambda: self.sql_status),
            (self.vault_src, self.vault_dest, lambda: self.vault_status),
        ]
        for v1, v2, lbl_fn in pairs:
            v1.trace_add("write", lambda *_, a=v1, b=v2, f=lbl_fn: self._check_ready(a, b, f()))
            v2.trace_add("write", lambda *_, a=v1, b=v2, f=lbl_fn: self._check_ready(a, b, f()))
        self.merger_dest.trace_add("write", lambda *_: self._check_merger_ready())

    def _check_ready(self, v1, v2, label) -> None:
        if v1.get() and v2.get():
            label.configure(text="Ready to process.", text_color="#2ecc71")
        else:
            label.configure(text="Waiting for selections\u2026", text_color="gray")

    def _check_merger_ready(self) -> None:
        if self._merger_sources and self.merger_dest.get():
            self.merger_status.configure(text="Ready to merge.", text_color="#2ecc71")
        else:
            self.merger_status.configure(
                text="Add at least one source and choose an output file.",
                text_color="gray",
            )

    def _browse_dir(self, var: ctk.StringVar) -> None:
        folder = filedialog.askdirectory(initialdir=var.get() or os.getcwd())
        if folder:
            var.set(folder)

    def _browse_file(self, var: ctk.StringVar, f_type: str) -> None:
        exts = ([("Chromium Bookmarks", "Bookmarks *.json"), ("All Files", "*.*")]
                if f_type == "JSON" else
                [("SQLite Files", "*.sqlite"), ("All Files", "*.*")])
        path = filedialog.askopenfilename(initialdir=os.getcwd(), filetypes=exts)
        if path:
            var.set(path)

    def _browse_save(self, var: ctk.StringVar, default_name: str = "bookmarks.html",
                     extra_types: list | None = None) -> None:
        types = extra_types or [("HTML Files", "*.html")]
        path  = filedialog.asksaveasfilename(
            initialdir=os.getcwd(), initialfile=default_name,
            defaultextension=Path(default_name).suffix,
            filetypes=types + [("All Files", "*.*")],
        )
        if path:
            var.set(path)

    # ── Search window ─────────────────────────────────────────────────────

    def _show_search(self) -> None:
        if self._search_win is not None and self._search_win.winfo_exists():
            self._search_win.lift()
            self._search_win.focus_force()
            return

        win = ctk.CTkToplevel(self)
        self._search_win = win
        win.title("Search Bookmarks")
        win.geometry("700x540")
        win.resizable(True, True)
        # Brief -topmost pulse: forces the window above the main app on Windows.
        # Released after 400ms so it doesn't permanently float above other apps.
        win.attributes("-topmost", True)
        win.after(400, lambda: win.attributes("-topmost", False))
        win.after(150, win.focus_force)
        self._apply_icon_to_toplevel(win)

        # ── Row 1: Source folder ──────────────────────────────────────────
        src_frame = ctk.CTkFrame(win, fg_color="transparent")
        src_frame.pack(fill="x", padx=16, pady=(14, 4))

        ctk.CTkLabel(src_frame, text="Search in:", width=80, anchor="w").pack(side="left")
        search_src_var = ctk.StringVar(value=self.ext_dest.get() or os.getcwd())
        src_entry = ctk.CTkEntry(src_frame, textvariable=search_src_var, width=490)
        src_entry.pack(side="left", padx=(6, 6))
        ToolTip(src_entry,
                "Folder produced by the Extractor (Tab 1) - must contain manifest.json.\n"
                "Pre-populated from your last extractor output path.")

        def _browse_search_src():
            folder = filedialog.askdirectory(initialdir=search_src_var.get())
            if folder:
                search_src_var.set(folder)
            # The folder dialog returns focus to the main window on Windows.
            # Re-raise the search window so it doesn't stay buried.
            win.lift()
            win.focus_force()

        ctk.CTkButton(src_frame, text="Browse", width=80,
                      command=_browse_search_src).pack(side="left")

        # ── Row 2: Query entry ────────────────────────────────────────────
        q_frame = ctk.CTkFrame(win, fg_color="transparent")
        q_frame.pack(fill="x", padx=16, pady=(4, 2))

        ctk.CTkLabel(q_frame, text="Query:", width=80, anchor="w").pack(side="left")
        query_var = ctk.StringVar()
        q_entry   = ctk.CTkEntry(
            q_frame, textvariable=query_var, width=590,
            placeholder_text='e.g.  python -video    or    github.com',
        )
        q_entry.pack(side="left", padx=(6, 0))
        q_entry.focus()

        # ── Row 3: Field selector + Search button ─────────────────────────
        # Kept on a separate row so neither element clips at any window width.
        ctrl_frame = ctk.CTkFrame(win, fg_color="transparent")
        ctrl_frame.pack(fill="x", padx=16, pady=(4, 2))

        ctk.CTkLabel(ctrl_frame, text="Search:", width=80, anchor="w").pack(side="left")

        field_var = ctk.StringVar(value="both")
        # CTkSegmentedButton child widgets intercept bind() and can cause a
        # silent TclError when ToolTip tries to attach -- no tooltip here.
        field_cb = ctk.CTkSegmentedButton(
            ctrl_frame,
            values=["both", "title", "url"],
            variable=field_var,
            width=200,
        )
        field_cb.pack(side="left", padx=(6, 16))

        run_btn = ctk.CTkButton(
            ctrl_frame, text="Search", width=120,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#2ecc71", hover_color="#27ae60", text_color="#000000",
        )
        run_btn.pack(side="left")
        ToolTip(run_btn, "Run the search.  You can also press Enter in the Query field.")

        # ── Hint ──────────────────────────────────────────────────────────
        ctk.CTkLabel(
            win,
            text="All words must match. Prefix a word with - to exclude it."
                 "  |  Double-click a result to open it.",
            text_color="gray",
            font=ctk.CTkFont(size=11, slant="italic"),
        ).pack(pady=(2, 4))

        # ── Results listbox ───────────────────────────────────────────────
        results_frame = ctk.CTkFrame(win)
        results_frame.pack(fill="both", expand=True, padx=16, pady=(0, 4))

        results_lb = tk.Listbox(
            results_frame,
            bg="#1e1e1e", fg="#e0e0e0",
            selectbackground="#4dabf7", selectforeground="#000000",
            font=("Consolas", 10), activestyle="none",
            borderwidth=0, highlightthickness=0,
        )
        scrollbar = tk.Scrollbar(results_frame, command=results_lb.yview)
        results_lb.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        results_lb.pack(fill="both", expand=True, padx=4, pady=4)

        # ── Status label ──────────────────────────────────────────────────
        status_lbl = ctk.CTkLabel(
            win, text="", text_color="gray", font=ctk.CTkFont(size=11)
        )
        status_lbl.pack(pady=(0, 2))

        # ── Bottom action buttons ─────────────────────────────────────────
        act_frame = ctk.CTkFrame(win, fg_color="transparent")
        act_frame.pack(pady=(0, 12))

        open_btn = ctk.CTkButton(
            act_frame, text="Open URL", width=120, state="disabled"
        )
        open_btn.pack(side="left", padx=6)
        ToolTip(open_btn, "Open the selected bookmark in your default browser.")

        copy_btn = ctk.CTkButton(
            act_frame, text="Copy URL", width=120, state="disabled"
        )
        copy_btn.pack(side="left", padx=6)
        ToolTip(copy_btn, "Copy the selected bookmark URL to the clipboard.")

        # ── Internal state ────────────────────────────────────────────────
        _results: list = []

        def _populate(found: list) -> None:
            """Update the results listbox from the main thread."""
            results_lb.delete(0, "end")
            _results.clear()
            _results.extend(found)
            if not found:
                status_lbl.configure(text="No results found.", text_color="gray")
                open_btn.configure(state="disabled")
                copy_btn.configure(state="disabled")
                return
            for entry in found:
                title_col = entry.title[:54].ljust(55)
                url_col   = entry.url[:62]
                results_lb.insert("end", f"  {title_col}  {url_col}")
            cap = " (capped at 500)" if len(found) == 500 else ""
            status_lbl.configure(
                text=f"{len(found)} result(s) found{cap}",
                text_color="#2ecc71",
            )
            open_btn.configure(state="normal")
            copy_btn.configure(state="normal")

        def _run_search_thread(raw_folder: str, query: str, field: str) -> None:
            """Background thread: parse sources and search, post results via queue."""
            try:
                sources = sources_from_manifest(raw_folder)
                found   = search_bookmarks(sources, query, field=field, limit=500)
                # Schedule UI update on the main thread
                win.after(0, lambda: _populate(found))
                win.after(0, lambda: run_btn.configure(state="normal"))
            except Exception as exc:
                win.after(0, lambda e=exc: status_lbl.configure(
                    text=f"Error: {e}", text_color="red"
                ))
                win.after(0, lambda: run_btn.configure(state="normal"))

        def _do_search(*_) -> None:
            raw_folder = search_src_var.get().strip()
            query      = query_var.get().strip()

            if not query:
                status_lbl.configure(text="Enter a search query.", text_color="gray")
                return
            if not raw_folder or not (Path(raw_folder) / "manifest.json").exists():
                status_lbl.configure(
                    text="Select a valid extraction folder (must contain manifest.json).",
                    text_color="red",
                )
                return

            # Clear previous results and disable button while running
            results_lb.delete(0, "end")
            _results.clear()
            open_btn.configure(state="disabled")
            copy_btn.configure(state="disabled")
            status_lbl.configure(text="Searching...", text_color="orange")
            run_btn.configure(state="disabled")

            threading.Thread(
                target=_run_search_thread,
                args=(raw_folder, query, field_var.get()),
                daemon=True,
            ).start()

        def _on_open() -> None:
            sel = results_lb.curselection()
            if sel and _results:
                _open_url(_results[sel[0]].url)

        def _on_copy() -> None:
            sel = results_lb.curselection()
            if sel and _results:
                win.clipboard_clear()
                win.clipboard_append(_results[sel[0]].url)

        run_btn.configure(command=_do_search)
        open_btn.configure(command=_on_open)
        copy_btn.configure(command=_on_copy)
        q_entry.bind("<Return>", _do_search)
        results_lb.bind("<Double-Button-1>", lambda _e: _on_open())

    # ── Documentation window ──────────────────────────────────────────────

    def _show_docs(self) -> None:
        if self._doc_win is not None and self._doc_win.winfo_exists():
            self._doc_win.lift()
            self._doc_win.focus_force()
            return
        self._doc_win = win = ctk.CTkToplevel(self)
        win.title("Documentation & Help")
        win.geometry("780x680")
        win.resizable(True, True)
        # Brief -topmost pulse: forces the window above the main app on Windows.
        # Released after 400ms so it doesn't permanently float above other apps.
        win.attributes("-topmost", True)
        win.after(400, lambda: win.attributes("-topmost", False))
        win.after(150, win.focus_force)
        self._apply_icon_to_toplevel(win)
        tabs = ctk.CTkTabview(win)
        tabs.pack(fill="both", expand=True, padx=15, pady=15)
        for tab_label, filepath in _DOC_FILES:
            tabs.add(tab_label)
            txt = ctk.CTkTextbox(tabs.tab(tab_label), wrap="word",
                                  font=ctk.CTkFont(family="Consolas", size=12))
            txt.pack(fill="both", expand=True)
            if tab_label == "Building .exe" and _IS_FROZEN:
                # Portable build: swap in a helpful inline message instead of
                # "file not found" since BUILDING.md is intentionally excluded.
                txt.insert("end", _BUILDING_PORTABLE_MSG.strip())
            elif filepath.exists():
                txt.insert("end", _clean_markdown(filepath.read_text(encoding="utf-8")))
            else:
                txt.insert("end",
                           f"File not found:\n  {filepath}\n\n"
                           "Make sure the docs/ folder and README.md are present\n"
                           "in the same directory as gui.py.")
            txt.configure(state="disabled")

    # ── UI construction ───────────────────────────────────────────────────

    def _build_ui(self) -> None:
        # ── Header ────────────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(15, 2))

        ctk.CTkLabel(header, text="Bookmark Rescue Toolkit",
                     font=ctk.CTkFont(size=24, weight="bold")).pack(side="left")

        docs_btn = ctk.CTkButton(
            header, text="View Docs", width=90, height=28,
            fg_color="#4dabf7", hover_color="#3b8fd6", text_color="#000000",
            font=ctk.CTkFont(weight="bold"), command=self._show_docs,
        )
        docs_btn.pack(side="right", padx=(6, 0))
        ToolTip(docs_btn, "Open the README and all documentation in a tabbed viewer.")

        search_btn = ctk.CTkButton(
            header, text="\U0001f50d Search", width=90, height=28,
            fg_color="#2ecc71", hover_color="#27ae60", text_color="#000000",
            font=ctk.CTkFont(weight="bold"), command=self._show_search,
        )
        search_btn.pack(side="right", padx=(0, 6))
        ToolTip(search_btn,
                "Search bookmarks by title or URL across all extracted sources.\n"
                "Requires a completed extraction (Tab 1) with a manifest.json.")

        ctk.CTkLabel(
            self,
            text="Recover \u00b7 Convert \u00b7 Merge \u00b7 Import  |  30+ browsers supported",
            text_color="gray", font=ctk.CTkFont(size=12), anchor="w",
        ).pack(fill="x", padx=20, pady=(0, 8))

        # ── Tabs ──────────────────────────────────────────────────────────
        self._tabs = ctk.CTkTabview(self, width=680, height=460, command=self._update_tip)
        self._tabs.pack(padx=20, pady=4)
        for name in ("1: Extractor", "2: JSON Parser", "3: SQLite Parser",
                     "4: Vault Builder", "5: Merger"):
            self._tabs.add(name)

        self._build_extractor_tab()
        self._build_converter_tab("2: JSON Parser",   self.json_src, self.json_dest,
                                   self.json_browser, "JSON")
        self._build_converter_tab("3: SQLite Parser", self.sql_src,  self.sql_dest,
                                   self.sql_browser,  "SQLite")
        self._build_vault_tab()
        self._build_merger_tab()

        # ── Tip line ──────────────────────────────────────────────────────
        self._tip_label = ctk.CTkLabel(
            self, text="", text_color="gray",
            font=ctk.CTkFont(size=11, slant="italic"), wraplength=680,
        )
        self._tip_label.pack(pady=(2, 2))
        self._update_tip()

        # ── Log area ──────────────────────────────────────────────────────
        log_frame = ctk.CTkFrame(self, fg_color="transparent")
        log_frame.pack(fill="x", padx=20, pady=(2, 12))

        self._log_box = ctk.CTkTextbox(log_frame, width=560, height=110, state="disabled")
        self._log_box.pack(side="left", fill="both", expand=True)

        btn_col = ctk.CTkFrame(log_frame, fg_color="transparent")
        btn_col.pack(side="left", padx=(6, 0))
        for text, cmd, tip in [
            ("Clear\nLog",  self._clear_log,  "Clear the activity log display."),
            ("Export\nLog", self._export_log, "Save the activity log to a .txt file."),
        ]:
            b = ctk.CTkButton(btn_col, text=text, width=56, height=52,
                               fg_color="#2c2c2c", hover_color="#444",
                               font=ctk.CTkFont(size=11), command=cmd)
            b.pack(pady=(0, 4))
            ToolTip(b, tip)

    def _clear_log(self) -> None:
        self._log_box.configure(state="normal")
        self._log_box.delete("1.0", "end")
        self._log_box.configure(state="disabled")

    def _export_log(self) -> None:
        self._log_box.configure(state="normal")
        content = self._log_box.get("1.0", "end")
        self._log_box.configure(state="disabled")
        if not content.strip():
            return
        path = filedialog.asksaveasfilename(
            initialfile="bookmark_rescue_log.txt", defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
        )
        if path:
            try:
                Path(path).write_text(content, encoding="utf-8")
            except OSError as exc:
                messagebox.showerror("Export Failed", str(exc))

    def _field_row(self, parent, label_text: str, var, browse_cmd, label_width: int = 140):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=15, pady=5)
        ctk.CTkLabel(frame, text=label_text, width=label_width, anchor="w").pack(side="left")
        entry = ctk.CTkEntry(frame, textvariable=var, width=370)
        entry.pack(side="left", padx=(8, 8))
        btn = ctk.CTkButton(frame, text="Browse", width=80, command=browse_cmd)
        btn.pack(side="left")
        return entry, btn

    def _action_buttons(self, parent, run_text: str, run_cmd, open_text: str):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(pady=5)
        run_btn = ctk.CTkButton(frame, text=run_text,
                                 font=ctk.CTkFont(size=14, weight="bold"),
                                 height=38, command=run_cmd)
        run_btn.pack(side="left", padx=5)
        open_btn = ctk.CTkButton(frame, text=open_text,
                                  font=ctk.CTkFont(size=13),
                                  height=38, width=160, state="disabled")
        open_btn.pack(side="left", padx=5)
        return run_btn, open_btn

    # ── Tab builders ──────────────────────────────────────────────────────

    def _build_extractor_tab(self) -> None:
        tab = self._tabs.tab("1: Extractor")
        ctk.CTkLabel(
            tab,
            text="Scan a Windows.old backup and extract raw browser data from 30+ browsers "
                 "into organised folders.",
            text_color="gray", wraplength=600,
        ).pack(pady=(10, 6))
        src_e,  src_b  = self._field_row(tab, "Windows.old Path:", self.ext_src,
                                          lambda: self._browse_dir(self.ext_src))
        dest_e, dest_b = self._field_row(tab, "Output Directory:", self.ext_dest,
                                          lambda: self._browse_dir(self.ext_dest))
        ToolTip(src_e,  "Root of the Windows.old folder, or any drive root (e.g. D:\\).")
        ToolTip(src_b,  "Browse for the Windows.old or drive root directory.")
        ToolTip(dest_e, "Empty folder where extracted browser files will be saved.")
        ToolTip(dest_b, "Browse for the output directory.")
        self.ext_status = ctk.CTkLabel(tab, text="Waiting for selections\u2026",
                                        text_color="gray")
        self.ext_status.pack(pady=(14, 4))
        self.ext_run_btn, self.ext_open_btn = self._action_buttons(
            tab, "Run Extraction", self._start_extraction, "Open Output Folder"
        )
        ToolTip(self.ext_run_btn,
                "Scan the drive and copy bookmark files.\n"
                "Also writes manifest.json used by Tabs 4, 5, and Search.")
        ToolTip(self.ext_open_btn,
                "Open the output folder in your file manager.\n"
                "Available after a successful extraction.")

    def _build_converter_tab(self, tab_name, var_src, var_dest, var_browser, file_type):
        tab     = self._tabs.tab(tab_name)
        is_json = file_type == "JSON"
        ctk.CTkLabel(
            tab,
            text=("Convert a Chromium-style Bookmarks JSON file into a universal importable HTML."
                  if is_json else
                  "Convert a Firefox-style places.sqlite database into a universal importable HTML."),
            text_color="gray", wraplength=600,
        ).pack(pady=(10, 6))
        src_e, src_b = self._field_row(
            tab, f"{file_type} Source File:", var_src,
            lambda: self._browse_file(var_src, file_type),
        )
        ToolTip(src_e, f"Select the {file_type} bookmark file to convert.")
        ToolTip(src_b, f"Browse for the source {file_type} file.")

        bf = ctk.CTkFrame(tab, fg_color="transparent")
        bf.pack(fill="x", padx=15, pady=5)
        ctk.CTkLabel(bf, text="Browser Label:", width=140, anchor="w").pack(side="left")
        json_browsers = [
            "Google Chrome", "Chrome Beta", "Chrome Dev", "Chrome Canary",
            "Microsoft Edge", "Edge Beta", "Edge Dev", "Edge Canary",
            "Brave", "Brave Beta", "Brave Nightly",
            "Opera", "Opera GX", "Opera Beta", "Opera Developer",
            "Vivaldi", "Arc", "DuckDuckGo", "Comet", "Ungoogled Chromium",
        ]
        sqlite_browsers = [
            "Firefox", "Firefox Beta", "Firefox Developer Edition",
            "Firefox Nightly", "Firefox ESR",
            "LibreWolf", "Waterfox", "Pale Moon", "SeaMonkey",
            "Mullvad", "Zen", "Zen Beta", "Tor", "Tor Alpha",
        ]
        combo = ctk.CTkComboBox(bf, variable=var_browser,
                                 values=json_browsers if is_json else sqlite_browsers,
                                 width=370)
        combo.pack(side="left", padx=(8, 8))
        ToolTip(combo, "Select from the list or type a custom name.\n"
                       "This label appears in the HTML title and link metadata.")

        dest_e, dest_b = self._field_row(
            tab, "Save HTML As:", var_dest,
            lambda: self._browse_save(
                var_dest,
                default_name=f"{var_browser.get().replace(' ', '_')}_Bookmarks.html",
            ),
        )
        ToolTip(dest_e, "Choose a path and filename for the output HTML file.")
        ToolTip(dest_b, "Browse for the save location.")

        if is_json:
            self.json_status = ctk.CTkLabel(tab, text="Waiting for selections\u2026",
                                             text_color="gray")
            self.json_status.pack(pady=(14, 4))
            self.json_run_btn, self.json_open_btn = self._action_buttons(
                tab, "Convert to HTML", self._start_json_conversion, "View HTML File"
            )
            ToolTip(self.json_run_btn,  "Generate a Netscape HTML file from the JSON source.")
            ToolTip(self.json_open_btn, "Open the converted file in your default browser.")
        else:
            self.sql_status = ctk.CTkLabel(tab, text="Waiting for selections\u2026",
                                            text_color="gray")
            self.sql_status.pack(pady=(14, 4))
            self.sql_run_btn, self.sql_open_btn = self._action_buttons(
                tab, "Convert to HTML", self._start_sql_conversion, "View HTML File"
            )
            ToolTip(self.sql_run_btn,  "Generate a Netscape HTML file from the SQLite source.")
            ToolTip(self.sql_open_btn, "Open the converted file in your default browser.")

    def _build_vault_tab(self) -> None:
        tab = self._tabs.tab("4: Vault Builder")
        ctk.CTkLabel(
            tab,
            text="Batch-convert all extracted files and build a Netscape HTML dashboard "
                 "ready for browser import.",
            text_color="gray", wraplength=600,
        ).pack(pady=(10, 6))
        src_e,  src_b  = self._field_row(tab, "Raw Data Folder:", self.vault_src,
                                          lambda: self._browse_dir(self.vault_src))
        dest_e, dest_b = self._field_row(tab, "Site Output Folder:", self.vault_dest,
                                          lambda: self._browse_dir(self.vault_dest))
        ToolTip(src_e,  "The folder created by Tab 1 (Extractor).")
        ToolTip(src_b,  "Browse for the raw data directory.")
        ToolTip(dest_e, "Empty folder where the HTML vault will be created.")
        ToolTip(dest_b, "Browse for the site output directory.")
        self.vault_status = ctk.CTkLabel(tab, text="Waiting for selections\u2026",
                                          text_color="gray")
        self.vault_status.pack(pady=(14, 4))
        self.vault_run_btn, self.vault_open_btn = self._action_buttons(
            tab, "Generate Vault Site", self._start_vault_build, "Open Vault Dashboard"
        )
        ToolTip(self.vault_run_btn,
                "Convert every artifact and build the index.html dashboard.\n"
                "Uses manifest.json from Tab 1 when available.")
        ToolTip(self.vault_open_btn, "Open the index.html dashboard in your default browser.")

    def _build_merger_tab(self) -> None:
        tab = self._tabs.tab("5: Merger")
        ctk.CTkLabel(
            tab,
            text="Combine bookmarks from multiple browsers into one file. "
                 "Merge to HTML for import, or export to CSV/JSON for Notion, Airtable, or Excel.",
            text_color="gray", wraplength=600,
        ).pack(pady=(8, 4))

        # ── Source list ───────────────────────────────────────────────────
        list_frame = ctk.CTkFrame(tab)
        list_frame.pack(fill="x", padx=15, pady=(2, 0))
        self._merger_listbox = tk.Listbox(
            list_frame,
            bg="#2c2c2c", fg="#e0e0e0",
            selectbackground="#4dabf7", selectforeground="#000000",
            font=("Consolas", 10), activestyle="none",
            borderwidth=0, highlightthickness=1, highlightcolor="#4dabf7",
            height=4,
        )
        self._merger_listbox.pack(fill="x", padx=6, pady=6)

        # ── Source buttons ────────────────────────────────────────────────
        sb = ctk.CTkFrame(tab, fg_color="transparent")
        sb.pack(fill="x", padx=15, pady=(2, 2))
        for text, cmd, tip in [
            ("+ Add HTML Files",     self._merger_add_html,
             "Add Netscape HTML files - our output OR native browser exports."),
            ("+ Add from Raw Folder", self._merger_add_raw,
             "Load all browsers from a manifest.json extraction folder."),
            ("Remove Selected",      self._merger_remove_selected,
             "Remove the selected source from the list."),
            ("Clear All",            self._merger_clear_all,
             "Remove all sources."),
        ]:
            kw = ({"fg_color": "#8b0000", "hover_color": "#a00000"}
                  if text == "Remove Selected" else
                  {"fg_color": "#2c2c2c", "hover_color": "#444"} if text == "Clear All" else {})
            b = ctk.CTkButton(sb, text=text, width=130 if len(text) < 15 else 150,
                               height=28, command=cmd, **kw)
            b.pack(side="left", padx=(0, 5))
            ToolTip(b, tip)

        # ── Options ───────────────────────────────────────────────────────
        of = ctk.CTkFrame(tab, fg_color="transparent")
        of.pack(fill="x", padx=15, pady=(2, 2))
        dedup_cb = ctk.CTkCheckBox(of, text="Deduplicate by URL",
                                    variable=self._merger_dedup, width=180)
        dedup_cb.pack(side="left", padx=(0, 20))
        ToolTip(dedup_cb,
                "Remove URLs already seen in an earlier source.\n"
                "http:// and https:// for the same page are treated as duplicates;\n"
                "the https:// version is always kept.")
        group_cb = ctk.CTkCheckBox(of, text="Group by source browser",
                                    variable=self._merger_group, width=200)
        group_cb.pack(side="left")
        ToolTip(group_cb,
                "Wrap each browser's bookmarks in a named top-level folder.\n"
                "Uncheck for a single flat merged structure.")

        # ── Output path ───────────────────────────────────────────────────
        dest_e, dest_b = self._field_row(
            tab, "Save Merged File As:", self.merger_dest,
            lambda: self._browse_save(self.merger_dest,
                                      default_name="Merged_Bookmarks.html"),
        )
        ToolTip(dest_e, "Path for the merged Netscape HTML output file.")
        ToolTip(dest_b, "Browse for the output file location.")

        # ── Status + Merge button row ──────────────────────────────────────
        self.merger_status = ctk.CTkLabel(
            tab, text="Add at least one source and choose an output file.",
            text_color="gray",
        )
        self.merger_status.pack(pady=(6, 2))

        self.merger_run_btn, self.merger_open_btn = self._action_buttons(
            tab, "Merge Bookmarks", self._start_merge, "View Merged File"
        )
        ToolTip(self.merger_run_btn,
                "Merge all listed sources into one Netscape HTML file.\n"
                "The result is ready to import into any browser.")
        ToolTip(self.merger_open_btn,
                "Open the merged HTML file in your default browser.")

        # ── Export divider ────────────────────────────────────────────────
        ctk.CTkLabel(
            tab,
            text="── Export to CSV or JSON (uses the same sources above) ──",
            text_color="#888888", font=ctk.CTkFont(size=11),
        ).pack(pady=(4, 2))

        exp_frame = ctk.CTkFrame(tab, fg_color="transparent")
        exp_frame.pack()
        csv_btn = ctk.CTkButton(
            exp_frame, text="Export CSV", width=140, height=34,
            fg_color="#2c6e49", hover_color="#1f5038",
            command=self._export_csv,
        )
        csv_btn.pack(side="left", padx=8)
        ToolTip(csv_btn,
                "Export all sources as a flat CSV spreadsheet.\n"
                "Columns: title, url, folder_path, source, date_added, date_human\n"
                "UTF-8 BOM is added so Excel opens it correctly.")

        json_btn = ctk.CTkButton(
            exp_frame, text="Export JSON", width=140, height=34,
            fg_color="#1a4a6e", hover_color="#153d5c",
            command=self._export_json,
        )
        json_btn.pack(side="left", padx=8)
        ToolTip(json_btn,
                "Export all sources as a JSON array.\n"
                "Each record includes title, url, folder_path (list), source, dates.\n"
                "Compatible with Notion, Airtable, and custom databases.")

    def _update_tip(self) -> None:
        self._tip_label.configure(text=self._TAB_TIPS.get(self._tabs.get(), ""))

    # ── Merger source list management ─────────────────────────────────────

    def _merger_add_html(self) -> None:
        paths = filedialog.askopenfilenames(
            title="Select Netscape Bookmark HTML files", initialdir=os.getcwd(),
            filetypes=[("HTML Files", "*.html"), ("All Files", "*.*")],
        )
        for path in paths:
            label = Path(path).stem
            self._merger_sources.append({"type": "html", "path": path, "label": label})
            self._merger_listbox.insert("end", f"  {label:<32}  {Path(path).name}")
        self._check_merger_ready()

    def _merger_add_raw(self) -> None:
        folder = filedialog.askdirectory(
            title="Select Raw Extracted Data Folder (must contain manifest.json)",
            initialdir=os.getcwd(),
        )
        if not folder:
            return
        manifest_path = Path(folder) / "manifest.json"
        if not manifest_path.exists():
            messagebox.showwarning(
                "No Manifest Found",
                f"manifest.json not found in:\n{folder}\n\n"
                "Run Tab 1 (Extractor) first to generate it.",
            )
            return
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception as exc:
            messagebox.showerror("Read Error", f"Could not read manifest.json:\n{exc}")
            return

        added = 0
        for artifact in manifest.get("artifacts", []):
            if artifact.get("status") != "copied":
                continue
            atype = artifact.get("artifact_type", "")
            if atype not in ("chromium_bookmarks_json", "gecko_places_sqlite"):
                continue
            src_type = "json" if "json" in atype else "sqlite"
            label    = f"{artifact.get('browser','')} ({artifact.get('profile','')})"
            path     = artifact.get("copied_path", "")
            self._merger_sources.append({"type": src_type, "path": path, "label": label})
            self._merger_listbox.insert("end", f"  {label:<40}  {Path(path).name}")
            added += 1

        if added == 0:
            messagebox.showwarning(
                "Nothing Found",
                "No bookmark artifacts of type chromium_bookmarks_json or\n"
                "gecko_places_sqlite were found in manifest.json.\n\n"
                "This usually means the Extractor (Tab 1) found no browsers\n"
                "on the scanned drive, or the manifest is from an older run.\n\n"
                "Try re-running Tab 1 against your source folder.",
            )
        else:
            self._q_log(f"[Merger] Added {added} source(s) from {folder}")
        self._check_merger_ready()

    def _merger_remove_selected(self) -> None:
        for idx in reversed(self._merger_listbox.curselection()):
            self._merger_listbox.delete(idx)
            self._merger_sources.pop(idx)
        self._check_merger_ready()

    def _merger_clear_all(self) -> None:
        self._merger_listbox.delete(0, "end")
        self._merger_sources.clear()
        self._check_merger_ready()

    # ── Background runners ────────────────────────────────────────────────

    def _start_extraction(self) -> None:
        if not self.ext_src.get() or not self.ext_dest.get():
            return
        self.ext_status.configure(text="Extracting\u2026 please wait.", text_color="orange")
        self.ext_run_btn.configure(state="disabled")
        self.ext_open_btn.configure(state="disabled")
        self._q_log(f"[Extractor] Starting \u2192 {self.ext_src.get()}")
        self._job_start("Extractor")
        threading.Thread(target=self._run_extraction, daemon=True).start()

    def _run_extraction(self) -> None:
        try:
            result = recover_bookmarks(self.ext_src.get(), self.ext_dest.get())
            n = result.get("copied_files", 0)
            w = len(result.get("warnings", []))
            self._q_status(self.ext_status,
                           f"Done - {n} file(s) copied." + (f"  ({w} warning(s))" if w else ""),
                           "#2ecc71")
            self._q_log(f"[Extractor] Finished. {n} file(s) copied, {w} warning(s).")
            for warning in result.get("warnings", []):
                self._q_log(f"  [!] {warning}")
            dest = self.ext_dest.get()
            self._q_button(self.ext_open_btn, "normal",
                           command=lambda p=dest: _open_path(p))
        except Exception as exc:
            self._q_status(self.ext_status, f"Error: {exc}", "red")
            self._q_log(f"[Extractor] Error: {exc}")
        finally:
            self._job_done("Extractor")
            self._q_button(self.ext_run_btn, "normal")

    def _start_json_conversion(self) -> None:
        if not self.json_src.get() or not self.json_dest.get():
            return
        self.json_status.configure(text="Converting\u2026", text_color="orange")
        self.json_run_btn.configure(state="disabled")
        self.json_open_btn.configure(state="disabled")
        self._q_log(f"[JSON] Converting \u2192 {self.json_src.get()}")
        self._job_start("JSON Parser")
        threading.Thread(target=self._run_json, daemon=True).start()

    def _run_json(self) -> None:
        try:
            label = self.json_browser.get().strip() or "Chromium"
            stats = convert_json_to_html(self.json_src.get(), self.json_dest.get(),
                                         browser_label=label)
            bm, fo = stats.get("bookmarks", 0), stats.get("folders", 0)
            self._q_status(self.json_status,
                           f"Done - {bm} bookmarks, {fo} folders.", "#2ecc71")
            self._q_log(f"[JSON] Done. {bm} bookmarks, {fo} folders \u2192 {self.json_dest.get()}")
            for w in stats.get("warnings", []):
                self._q_log(f"  [!] {w}")
            dest = self.json_dest.get()
            self._q_button(self.json_open_btn, "normal",
                           command=lambda p=dest: _open_path(p))
        except Exception as exc:
            self._q_status(self.json_status, f"Error: {exc}", "red")
            self._q_log(f"[JSON] Error: {exc}")
        finally:
            self._job_done("JSON Parser")
            self._q_button(self.json_run_btn, "normal")

    def _start_sql_conversion(self) -> None:
        if not self.sql_src.get() or not self.sql_dest.get():
            return
        self.sql_status.configure(text="Converting\u2026", text_color="orange")
        self.sql_run_btn.configure(state="disabled")
        self.sql_open_btn.configure(state="disabled")
        self._q_log(f"[SQLite] Converting \u2192 {self.sql_src.get()}")
        self._job_start("SQLite Parser")
        threading.Thread(target=self._run_sql, daemon=True).start()

    def _run_sql(self) -> None:
        try:
            label = self.sql_browser.get().strip() or "Firefox"
            stats = convert_sqlite_to_html(self.sql_src.get(), self.sql_dest.get(),
                                           browser_label=label)
            bm, fo = stats.get("bookmarks", 0), stats.get("folders", 0)
            self._q_status(self.sql_status,
                           f"Done - {bm} bookmarks, {fo} folders.", "#2ecc71")
            self._q_log(f"[SQLite] Done. {bm} bookmarks, {fo} folders \u2192 {self.sql_dest.get()}")
            for w in stats.get("warnings", []):
                self._q_log(f"  [!] {w}")
            dest = self.sql_dest.get()
            self._q_button(self.sql_open_btn, "normal",
                           command=lambda p=dest: _open_path(p))
        except Exception as exc:
            self._q_status(self.sql_status, f"Error: {exc}", "red")
            self._q_log(f"[SQLite] Error: {exc}")
        finally:
            self._job_done("SQLite Parser")
            self._q_button(self.sql_run_btn, "normal")

    def _start_vault_build(self) -> None:
        if not self.vault_src.get() or not self.vault_dest.get():
            return
        self.vault_status.configure(text="Building vault\u2026 please wait.", text_color="orange")
        self.vault_run_btn.configure(state="disabled")
        self.vault_open_btn.configure(state="disabled")
        self._q_log(f"[Vault] Building from \u2192 {self.vault_src.get()}")
        self._job_start("Vault Builder")
        threading.Thread(target=self._run_vault, daemon=True).start()

    def _run_vault(self) -> None:
        try:
            result = build_vault(self.vault_src.get(), self.vault_dest.get())
            n = result.get("converted", 0)
            w = len(result.get("warnings", []))
            index = Path(self.vault_dest.get()) / "index.html"
            self._q_status(self.vault_status,
                           f"Done - {n} page(s) generated." + (f"  ({w} warning(s))" if w else ""),
                           "#2ecc71")
            self._q_log(f"[Vault] Done. {n} page(s) converted, {w} warning(s).")
            self._q_log(f"[Vault] Dashboard \u2192 {index}")
            for warning in result.get("warnings", []):
                self._q_log(f"  [!] {warning}")
            self._q_button(self.vault_open_btn, "normal",
                           command=lambda p=str(index): _open_path(p))
        except Exception as exc:
            self._q_status(self.vault_status, f"Error: {exc}", "red")
            self._q_log(f"[Vault] Error: {exc}")
        finally:
            self._job_done("Vault Builder")
            self._q_button(self.vault_run_btn, "normal")

    def _start_merge(self) -> None:
        if not self._merger_sources or not self.merger_dest.get():
            return
        self.merger_status.configure(text="Merging\u2026 please wait.", text_color="orange")
        self.merger_run_btn.configure(state="disabled")
        self.merger_open_btn.configure(state="disabled")
        self._q_log(f"[Merger] Starting \u2014 {len(self._merger_sources)} source(s)")
        self._job_start("Merger")
        threading.Thread(target=self._run_merge, daemon=True).start()

    def _run_merge(self) -> None:
        try:
            result = merge_sources(
                list(self._merger_sources),
                self.merger_dest.get(),
                deduplicate    = self._merger_dedup.get(),
                group_by_source= self._merger_group.get(),
            )
            inp  = result.get("total_input", 0)
            dupl = result.get("duplicates_removed", 0)
            out  = result.get("total_output", 0)
            w    = len(result.get("warnings", []))
            self._q_status(self.merger_status,
                           f"Done - {out} bookmarks ({dupl} duplicates removed).",
                           "#2ecc71")
            self._q_log(f"[Merger] Done. {inp} in \u2192 {out} out "
                        f"({dupl} duplicates removed, {w} warning(s)).")
            for warning in result.get("warnings", []):
                self._q_log(f"  [!] {warning}")
            dest = self.merger_dest.get()
            self._q_button(self.merger_open_btn, "normal",
                           command=lambda p=dest: _open_path(p))
        except Exception as exc:
            self._q_status(self.merger_status, f"Error: {exc}", "red")
            self._q_log(f"[Merger] Error: {exc}")
        finally:
            self._job_done("Merger")
            self._q_button(self.merger_run_btn, "normal")

    def _export_csv(self) -> None:
        if not self._merger_sources:
            messagebox.showinfo("No Sources", "Add at least one source to the list first.")
            return
        path = filedialog.asksaveasfilename(
            initialfile="Bookmarks_Export.csv", defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
        )
        if not path:
            return
        self._q_log(f"[Export CSV] Starting \u2192 {path}")
        self._job_start("Export CSV")
        threading.Thread(
            target=self._run_export,
            args=(export_to_csv, path, "CSV"),
            daemon=True,
        ).start()

    def _export_json(self) -> None:
        if not self._merger_sources:
            messagebox.showinfo("No Sources", "Add at least one source to the list first.")
            return
        path = filedialog.asksaveasfilename(
            initialfile="Bookmarks_Export.json", defaultextension=".json",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
        )
        if not path:
            return
        self._q_log(f"[Export JSON] Starting \u2192 {path}")
        self._job_start("Export JSON")
        threading.Thread(
            target=self._run_export,
            args=(export_to_json, path, "JSON"),
            daemon=True,
        ).start()

    def _run_export(self, fn, path: str, label: str) -> None:
        try:
            result = fn(
                list(self._merger_sources),
                path,
                deduplicate=self._merger_dedup.get(),
            )
            out = result.get("total_output", 0)
            w   = len(result.get("warnings", []))
            self._q_log(f"[Export {label}] Done. {out} bookmark(s) exported, {w} warning(s).")
            self._q_log(f"[Export {label}] File \u2192 {path}")
            for warning in result.get("warnings", []):
                self._q_log(f"  [!] {warning}")
        except Exception as exc:
            self._q_log(f"[Export {label}] Error: {exc}")
        finally:
            self._job_done(f"Export {label}")


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app = BookmarkApp()
    app.mainloop()
