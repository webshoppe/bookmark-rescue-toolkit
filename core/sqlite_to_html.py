"""
sqlite_to_html.py - Bookmark Rescue Toolkit
============================================
Converts a Firefox-family places.sqlite database into a Netscape Bookmark
HTML file that can be imported by any modern browser.

Supported sources
-----------------
  Firefox, LibreWolf, Waterfox, Pale Moon, SeaMonkey,
  Mullvad Browser, Zen Browser, Tor Browser, and more.

Standalone usage
----------------
  python -m core.sqlite_to_html places.sqlite output.html
  python -m core.sqlite_to_html places.sqlite output.html --browser "LibreWolf"
"""

from __future__ import annotations

import os
import sqlite3
import sys
from html import escape
from pathlib import Path

from .utils import get_human_date


_REQUIRED_TABLES = frozenset({"moz_bookmarks", "moz_places"})

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _convert_firefox_time(pr_time) -> int:
    """Convert a Firefox PRTime (microseconds since Unix epoch) to seconds.

    Returns 0 for any value that cannot be parsed cleanly.
    """
    try:
        return int(pr_time) // 1_000_000
    except (ValueError, TypeError):
        return 0


def _validate_schema(cursor: sqlite3.Cursor) -> None:
    """Raise RuntimeError if the required Firefox tables are absent.

    This provides a clear error message when a SQLite file is passed that is
    not a Firefox places database (e.g. a Chrome History or Favicons database).
    """
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name IN (?, ?)",
        tuple(_REQUIRED_TABLES),
    )
    found   = {row[0] for row in cursor.fetchall()}
    missing = _REQUIRED_TABLES - found
    if missing:
        raise RuntimeError(
            f"Not a valid Firefox places.sqlite - "
            f"missing table(s): {', '.join(sorted(missing))}"
        )


def _build_tree(
    cursor: sqlite3.Cursor,
    parent_id: int,
    html_output: list,
    stats: dict,
    browser_name: str = "Firefox",
    indent_level: int = 1,
) -> None:
    """Recursively walk the Firefox bookmark tree, appending HTML lines.

    moz_bookmarks item types:
      1 = URL bookmark
      2 = Folder
      3 = Separator (skipped)
    """
    indent = "    " * indent_level
    cursor.execute(
        """
        SELECT b.id, b.type, b.title, p.url, b.dateAdded
        FROM   moz_bookmarks b
        LEFT   JOIN moz_places p ON b.fk = p.id
        WHERE  b.parent = ?
        ORDER  BY b.position
        """,
        (parent_id,),
    )

    for item_id, item_type, title, url, date_added in cursor.fetchall():
        safe_title    = escape(title or "Unnamed", quote=True)
        add_date_unix = _convert_firefox_time(date_added)
        human_date    = get_human_date(add_date_unix)

        if item_type == 2:  # folder
            stats["folders"] += 1
            html_output.append(
                f'{indent}<DT><H3 ADD_DATE="{add_date_unix}">{safe_title}</H3>'
            )
            html_output.append(f"{indent}<DL><p>")
            _build_tree(cursor, item_id, html_output, stats, browser_name, indent_level + 1)
            html_output.append(f"{indent}</DL><p>")

        elif item_type == 1 and url:  # bookmark with a URL
            stats["bookmarks"] += 1
            safe_url     = escape(url, quote=True)
            meta_string  = escape(f"Browser: {browser_name} | Added: {human_date}", quote=True)
            safe_browser = escape(browser_name, quote=True)
            html_output.append(
                f'{indent}<DT><A HREF="{safe_url}" ADD_DATE="{add_date_unix}"'
                f' TITLE="{meta_string}" aria-label="{safe_title}. {meta_string}"'
                f' data-browser="{safe_browser}">{safe_title}</A>'
            )

        elif item_type not in (1, 3):
            # Type 3 is a separator - silently skip. Anything else is unexpected.
            stats["warnings"].append(
                f"Skipped item type {item_type} (id={item_id}) under parent {parent_id}"
            )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def convert_sqlite_to_html(
    sqlite_path: str,
    output_html_path: str,
    browser_label: str = "Firefox",
) -> dict:
    """Convert a Firefox places.sqlite to a Netscape Bookmark HTML file.

    The database is opened in read-only mode via SQLite's URI interface so
    that this tool cannot accidentally modify a live or recovered profile.

    A warning is surfaced if a WAL journal file is detected alongside the
    database, because an unclean browser shutdown can leave uncommitted
    transactions in the WAL - meaning some recently added bookmarks may not
    appear in the output.

    Parameters
    ----------
    sqlite_path:
        Path to a Firefox-family ``places.sqlite`` file.
    output_html_path:
        Destination path for the generated HTML file.
    browser_label:
        Human-readable browser name used in the HTML ``<TITLE>`` and as the
        ``data-browser`` attribute on every anchor tag.

    Returns
    -------
    dict with keys:
        status, bookmarks, folders, warnings, source, output, browser

    Raises
    ------
    FileNotFoundError
        If *sqlite_path* does not exist.
    RuntimeError
        If the file is not a valid Firefox places database.
    """
    if not os.path.exists(sqlite_path):
        raise FileNotFoundError(f"Source file not found: {sqlite_path}")

    stats: dict = {
        "status":    "ok",
        "bookmarks": 0,
        "folders":   0,
        "warnings":  [],
        "source":    sqlite_path,
        "output":    output_html_path,
        "browser":   browser_label,
    }

    # Detect a WAL journal - indicates an unclean shutdown and potentially
    # incomplete data even though the database itself will still open fine.
    wal_path = Path(sqlite_path).with_suffix(".sqlite-wal")
    if wal_path.exists():
        stats["warnings"].append(
            "A WAL journal file was detected alongside this database. "
            "The browser may have shut down uncleanly - "
            "some recently added bookmarks could be missing from the output."
        )

    conn = sqlite3.connect(f"file:{sqlite_path}?mode=ro", uri=True)
    try:
        cursor = conn.cursor()
        _validate_schema(cursor)

        safe_label = escape(browser_label, quote=True)
        html_lines = [
            "<!DOCTYPE NETSCAPE-Bookmark-file-1>",
            "",
            '<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">',
            f"<TITLE>Recovered Bookmarks \u2014 {safe_label}</TITLE>",
            f"<H1>Recovered Bookmarks ({safe_label})</H1>",
            "<DL><p>",
        ]

        # Firefox uses well-known root IDs: 1=root, 2=menu, 3=toolbar, 4=tags, 5=unfiled
        # Querying for children of root (parent=1) returns those named top-level folders.
        cursor.execute(
            "SELECT id, title FROM moz_bookmarks "
            "WHERE parent = 1 AND type = 2 ORDER BY position"
        )
        roots = cursor.fetchall()

        if not roots:
            stats["warnings"].append("No root bookmark folders found in moz_bookmarks.")

        for root_id, title in roots:
            safe_title = escape(title or "Root", quote=True)
            html_lines.append(f"    <DT><H3>{safe_title}</H3>")
            html_lines.append("    <DL><p>")
            _build_tree(cursor, root_id, html_lines, stats, browser_label, indent_level=2)
            html_lines.append("    </DL><p>")

        html_lines.append("</DL><p>")

        with open(output_html_path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(html_lines))

    finally:
        # Always close - even if _validate_schema or _build_tree raises.
        conn.close()

    return stats


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        prog="python -m core.sqlite_to_html",
        description="Convert a Firefox places.sqlite to Netscape Bookmark HTML.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  python -m core.sqlite_to_html places.sqlite output.html
  python -m core.sqlite_to_html places.sqlite output.html --browser "LibreWolf"
  python -m core.sqlite_to_html places.sqlite output.html --browser "Tor Browser"
        """,
    )
    parser.add_argument("source",
                        help="Path to the Firefox places.sqlite file")
    parser.add_argument("output",
                        help="Path for the output HTML file (e.g. bookmarks.html)")
    parser.add_argument("--browser", default="Firefox",
                        help='Browser label used in the HTML title (default: "Firefox")')
    args = parser.parse_args()

    try:
        stats = convert_sqlite_to_html(args.source, args.output, browser_label=args.browser)
    except (FileNotFoundError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Converted : {stats['bookmarks']} bookmarks, {stats['folders']} folders")
    if stats["warnings"]:
        for w in stats["warnings"]:
            print(f"  [!] {w}")
    print(f"Output    : {args.output}")
