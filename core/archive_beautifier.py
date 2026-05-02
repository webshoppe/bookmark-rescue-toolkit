"""
archive_beautifier.py - Bookmark Rescue Toolkit
================================================
Reads the manifest.json from the Extractor and builds a modern, stylized
HTML5 archive designed for human reading and exploration.

This module produces a different output to vault_builder:
  vault_builder    → Netscape Bookmark HTML, optimised for browser import
  archive_beautifier → Responsive HTML5, optimised for reading in a browser

Features
--------
  • Sticky navigation header with folder jump-links per page
  • Dark / light theme toggle (persisted to localStorage)
  • Forensic metadata section showing original source path and artifact type
  • Bookmark and folder counts on the hub index cards
  • External style.css so the theme can be customised without touching HTML
  • Fully offline - no CDN, no web fonts, no external requests

Standalone usage
----------------
  python -m core.archive_beautifier "C:\\Bookmark_Rescue\\Raw" "C:\\Bookmark_Rescue\\Archive"
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
from html import escape
from pathlib import Path
from urllib.parse import quote

from .utils import get_human_date


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _convert_chrome_time(webkit_timestamp) -> int:
    """Convert a WebKit/Chromium microsecond timestamp to a Unix timestamp."""
    try:
        return int((int(webkit_timestamp) - 11_644_473_600_000_000) / 1_000_000)
    except (ValueError, TypeError):
        return 0


def _slugify(text: str) -> str:
    """Create a safe, lowercase anchor ID from arbitrary text."""
    safe = "".join(c if c.isalnum() else "-" for c in text.lower())
    return safe.strip("-") or "section"


def _validate_gecko_schema(cursor: sqlite3.Cursor) -> None:
    """Raise RuntimeError if the required Firefox tables are absent."""
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name IN (?, ?)",
        ("moz_bookmarks", "moz_places"),
    )
    found   = {row[0] for row in cursor.fetchall()}
    missing = {"moz_bookmarks", "moz_places"} - found
    if missing:
        raise RuntimeError(
            f"Not a valid Firefox places.sqlite - "
            f"missing table(s): {', '.join(sorted(missing))}"
        )


# ---------------------------------------------------------------------------
# CSS and theme generator
# ---------------------------------------------------------------------------

_CSS = """\
/* style.css - Bookmark Rescue Toolkit: Stylized Archive
   Edit this file to customise colours, fonts, and spacing.
   Dark theme is the default; light theme is toggled by adding
   the class "light" to the <html> element via the JS toggle button. */

/* ── Design tokens ───────────────────────────────────────────── */
:root {
    --bg-main:      #121212;
    --bg-surface:   #1e1e1e;
    --bg-card:      #2c2c2c;
    --bg-hover:     #383838;
    --text-primary: #e0e0e0;
    --text-secondary: #aaaaaa;
    --accent:       #4dabf7;
    --border:       #333333;
}

html.light {
    --bg-main:      #f5f5f5;
    --bg-surface:   #ffffff;
    --bg-card:      #e8e8e8;
    --bg-hover:     #d8d8d8;
    --text-primary: #1a1a1a;
    --text-secondary: #555555;
    --accent:       #1a6fb5;
    --border:       #cccccc;
}

/* ── Base ────────────────────────────────────────────────────── */
*, *::before, *::after { box-sizing: border-box; }

html { scroll-behavior: smooth; }

body {
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    background-color: var(--bg-main);
    color: var(--text-primary);
    margin: 0; padding: 0; line-height: 1.6;
    transition: background-color 0.25s, color 0.25s;
}

/* ── Sticky header ───────────────────────────────────────────── */
header {
    background-color: var(--bg-surface);
    border-bottom: 2px solid var(--border);
    padding: 12px 40px;
    position: sticky; top: 0; z-index: 1000;
    box-shadow: 0 4px 8px rgba(0,0,0,0.15);
}

.header-container {
    max-width: 1200px; margin: 0 auto;
    display: flex; justify-content: space-between;
    align-items: center; gap: 20px; flex-wrap: wrap;
}

header h1 { margin: 0; font-size: 1.4rem; color: var(--accent); flex-shrink: 0; }

/* ── Navigation ──────────────────────────────────────────────── */
nav ul {
    list-style: none; margin: 0; padding: 0;
    display: flex; gap: 8px; flex-wrap: wrap;
}

nav a {
    color: var(--text-primary); text-decoration: none;
    font-weight: 600; font-size: 0.85rem;
    padding: 4px 10px; border-radius: 4px;
    transition: background-color 0.2s, outline 0.1s;
}

nav a:hover, nav a:focus {
    background-color: var(--bg-card);
    outline: 2px solid var(--accent);
    outline-offset: 1px;
}

/* ── Theme toggle button ─────────────────────────────────────── */
.theme-toggle {
    background: var(--bg-card); color: var(--text-primary);
    border: 1px solid var(--border); border-radius: 6px;
    padding: 5px 12px; cursor: pointer; font-size: 0.85rem;
    flex-shrink: 0; transition: background-color 0.2s;
}
.theme-toggle:hover { background: var(--bg-hover); }

/* ── Main content ────────────────────────────────────────────── */
main { max-width: 1200px; margin: 30px auto; padding: 0 40px 60px; }

section {
    background-color: var(--bg-surface); border-radius: 8px;
    padding: 25px; margin-bottom: 28px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.08);
    scroll-margin-top: 90px;
}

h2 {
    color: var(--text-primary); margin-top: 0;
    border-bottom: 1px solid var(--border);
    padding-bottom: 10px; font-size: 1.15rem;
}

/* ── Bookmark lists ──────────────────────────────────────────── */
dl { margin: 12px 0 0 0; padding-left: 8px; }

dt {
    background-color: var(--bg-card);
    margin-bottom: 6px; border-radius: 6px;
    transition: transform 0.15s, background-color 0.15s;
}

dt:hover { transform: translateX(4px); background-color: var(--bg-hover); }

dt a {
    display: block; padding: 10px 14px;
    color: var(--text-primary); text-decoration: none; font-weight: 500;
    word-break: break-word;
}

dt a:focus {
    outline: 2px solid var(--accent);
    outline-offset: -2px; border-radius: 6px;
}

/* Nested folder groups */
dl dl {
    margin-left: 18px;
    border-left: 2px solid var(--border);
    padding-left: 12px;
}

.folder-label {
    padding: 8px 14px; font-weight: 600;
    color: var(--text-secondary); font-size: 0.9rem;
    background: transparent;
}
.folder-label:hover { transform: none; background: transparent; }

/* ── Forensic metadata section ───────────────────────────────── */
#forensic-metadata dt {
    background-color: transparent; padding: 4px 0; margin-bottom: 4px;
}
#forensic-metadata dt:hover { transform: none; background-color: transparent; }

code {
    background-color: var(--bg-card); padding: 2px 6px; border-radius: 4px;
    font-family: 'Consolas', 'Courier New', monospace; font-size: 0.88em;
    color: var(--accent); word-break: break-all;
}

/* ── Hub index cards ─────────────────────────────────────────── */
.user-title { color: var(--accent); }
.browser-title {
    color: var(--text-secondary); font-size: 1.05em;
    margin: 18px 0 8px 0; font-weight: 600;
}
.hub-list { display: flex; flex-wrap: wrap; gap: 12px; padding-left: 0; }
.hub-list li { list-style: none; }
.hub-card {
    display: block; background-color: var(--bg-card);
    border-radius: 6px; text-decoration: none;
    transition: transform 0.2s, background-color 0.2s;
}
.hub-card:hover { transform: translateY(-2px); background-color: var(--bg-hover); }
.hub-card-label {
    display: block; padding: 11px 18px;
    color: var(--text-primary); font-weight: bold; font-size: 0.95rem;
}
.hub-card-meta {
    display: block; padding: 0 18px 10px;
    color: var(--text-secondary); font-size: 0.8rem;
}

/* ── Back link ───────────────────────────────────────────────── */
.back-link {
    display: inline-block; margin-bottom: 20px;
    color: var(--accent); text-decoration: none; font-size: 0.9rem;
}
.back-link:hover { text-decoration: underline; }

/* ── Responsive ──────────────────────────────────────────────── */
@media (max-width: 600px) {
    header { padding: 10px 16px; }
    main   { padding: 0 16px 40px; }
    .hub-list { flex-direction: column; }
}
"""

# Small self-contained JS - no external dependencies.
# Reads/writes a "theme" key in localStorage so the choice persists.
_THEME_JS = """\
<script>
(function(){
    var html = document.documentElement;
    var btn  = document.getElementById('theme-btn');
    var stored = localStorage.getItem('brt-theme');
    if (stored === 'light') { html.classList.add('light'); }
    if (btn) {
        btn.textContent = html.classList.contains('light') ? '☀ Light' : '🌙 Dark';
        btn.addEventListener('click', function(){
            html.classList.toggle('light');
            var isLight = html.classList.contains('light');
            localStorage.setItem('brt-theme', isLight ? 'light' : 'dark');
            btn.textContent = isLight ? '☀ Light' : '🌙 Dark';
        });
    }
})();
</script>"""


def _write_css(site_dir: Path) -> None:
    (site_dir / "style.css").write_text(_CSS, encoding="utf-8")


# ---------------------------------------------------------------------------
# Hub index page
# ---------------------------------------------------------------------------

def _write_hub_index(site_dir: Path, site_map: dict) -> None:
    """Build the main index.html dashboard for the archive.

    site_map structure
    ------------------
    {
      username: {
        browser: [ (profile, rel_link, bm_count, folder_count), … ]
      }
    }
    """
    lines = [
        "<!DOCTYPE html>",
        "<html lang='en'>",
        "<head>",
        '    <meta charset="UTF-8">',
        '    <meta name="viewport" content="width=device-width, initial-scale=1.0">',
        "    <title>Stylized Bookmark Archive</title>",
        '    <link rel="stylesheet" href="style.css">',
        "</head>",
        "<body>",
        "    <header>",
        "        <div class='header-container'>",
        "            <h1>&#128214; Stylized Bookmark Archive</h1>",
        "            <button class='theme-toggle' id='theme-btn' aria-label='Toggle colour theme'>&#127769; Dark</button>",
        "        </div>",
        "    </header>",
        "    <main>",
    ]

    if not site_map:
        lines.append("        <section><p>No recovered bookmarks found to display.</p></section>")
    else:
        for username, browsers in sorted(site_map.items()):
            safe_user = escape(username)
            lines += [
                "        <section>",
                f"            <h2 class='user-title'>&#128100; User: {safe_user}</h2>",
            ]
            for browser_name, profiles in sorted(browsers.items()):
                safe_browser = escape(browser_name)
                lines += [
                    f"            <div class='browser-title'>&#128193; {safe_browser}</div>",
                    "            <ul class='hub-list'>",
                ]
                for profile_name, link, bm_count, folder_count in sorted(profiles):
                    safe_profile = escape(profile_name)
                    safe_link    = quote(link, safe="/")
                    lines += [
                        "                <li>",
                        f"                    <a class='hub-card' href='{safe_link}'>",
                        f"                        <span class='hub-card-label'>{safe_profile}</span>",
                        f"                        <span class='hub-card-meta'>{bm_count} bookmarks &middot; {folder_count} folders</span>",
                        "                    </a>",
                        "                </li>",
                    ]
                lines.append("            </ul>")
            lines.append("        </section>")

    lines += ["    </main>", _THEME_JS, "</body>", "</html>"]

    (site_dir / "index.html").write_text("\n".join(lines), encoding="utf-8")


# ---------------------------------------------------------------------------
# Per-profile page writer
# ---------------------------------------------------------------------------

def _write_archive_page(
    out_path: Path,
    browser_label: str,
    source_path: str,
    artifact_type: str,
    nav_links: list,
    sections_html: list,
    back_depth: int = 3,
) -> None:
    """Assemble and write one per-profile HTML5 archive page.

    back_depth controls how many `../` steps to reach the archive root
    (default 3 = user/browser/profile).
    """
    css_rel  = "../" * back_depth + "style.css"
    back_rel = "../" * back_depth + "index.html"

    html = [
        "<!DOCTYPE html>",
        "<html lang='en'>",
        "<head>",
        '    <meta charset="UTF-8">',
        '    <meta name="viewport" content="width=device-width, initial-scale=1.0">',
        f"    <title>Archive: {escape(browser_label)}</title>",
        f"    <link rel='stylesheet' href='{css_rel}'>",
        "</head>",
        "<body>",
        "    <header>",
        "        <div class='header-container'>",
        f"            <h1>{escape(browser_label)}</h1>",
        "            <nav aria-label='Jump to folder'>",
        "                <ul>",
    ]

    for slug, name in nav_links:
        html.append(
            f"                    <li><a href='#{slug}'>{escape(name)}</a></li>"
        )

    html += [
        "                </ul>",
        "            </nav>",
        "            <button class='theme-toggle' id='theme-btn' aria-label='Toggle colour theme'>&#127769; Dark</button>",
        "        </div>",
        "    </header>",
        "    <main>",
        f"        <a class='back-link' href='{back_rel}'>&#8592; Back to Archive Index</a>",
        "        <section id='forensic-metadata' aria-labelledby='heading-metadata'>",
        "            <h2 id='heading-metadata'>Forensic Metadata</h2>",
        "            <dl>",
        "                <dt><strong>Source Path:</strong> "
        f"<code>{escape(source_path)}</code></dt>",
        "                <dt><strong>Artifact Type:</strong> "
        f"<code>{escape(artifact_type)}</code></dt>",
        "            </dl>",
        "        </section>",
    ]

    html.extend(sections_html)
    html += ["    </main>", _THEME_JS, "</body>", "</html>"]

    out_path.write_text("\n".join(html), encoding="utf-8")


# ---------------------------------------------------------------------------
# Chromium JSON parser
# ---------------------------------------------------------------------------

def _parse_json(
    json_path: str,
    out_path: Path,
    browser_label: str,
    source_path: str,
    artifact_type: str,
) -> tuple[int, int]:
    """Parse a Chromium Bookmarks file and write one archive page.

    Returns (bookmark_count, folder_count).
    """
    with open(json_path, "r", encoding="utf-8") as fh:
        try:
            data = json.load(fh)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Not valid JSON: {exc}") from exc

    if not isinstance(data, dict) or "roots" not in data:
        raise ValueError("Missing 'roots' key - not a Chromium Bookmarks file.")

    stats      = [0, 0]   # [bookmarks, folders]
    nav_links  = []
    sections   = []

    def _walk(node: dict, html_out: list, depth: int = 0) -> None:
        node_type = node.get("type")

        if node_type == "folder":
            stats[1] += 1
            name = escape(node.get("name", "Unnamed Folder"))

            if depth == 0:
                # Top-level root → full section with heading + nav link
                slug = f"folder-{_slugify(node.get('name', 'folder'))}"
                nav_links.append((slug, node.get("name", "Unnamed Folder")))
                html_out.append(
                    f"        <section id='{slug}' aria-labelledby='h-{slug}'>"
                )
                html_out.append(
                    f"            <h2 id='h-{slug}'>{name}</h2>"
                )
                html_out.append("            <dl>")
                for child in node.get("children", []):
                    _walk(child, html_out, depth + 1)
                html_out.append("            </dl>")
                html_out.append("        </section>")
            else:
                # Nested folder → labelled sub-list
                html_out.append(
                    f"            <dt class='folder-label'>&#128193; {name}</dt>"
                )
                html_out.append("            <dl>")
                for child in node.get("children", []):
                    _walk(child, html_out, depth + 1)
                html_out.append("            </dl>")

        elif node_type == "url":
            stats[0] += 1
            raw_name    = node.get("name", "Unnamed Bookmark")
            raw_url     = node.get("url", "")
            safe_name   = escape(raw_name)
            safe_url    = escape(raw_url, quote=True)
            unix_time   = _convert_chrome_time(node.get("date_added", 0))
            human_date  = get_human_date(unix_time)
            aria        = escape(f"{raw_name}. Added: {human_date}")

            html_out.append("            <dt>")
            html_out.append(
                f"                <a href='{safe_url}' aria-label='{aria}'>"
                f"{safe_name}</a>"
            )
            html_out.append("            </dt>")

    roots = data.get("roots", {})
    for key in ("bookmark_bar", "other", "synced"):
        root_node = roots.get(key)
        if root_node:
            _walk(root_node, sections, depth=0)

    _write_archive_page(out_path, browser_label, source_path, artifact_type,
                        nav_links, sections)
    return stats[0], stats[1]


# ---------------------------------------------------------------------------
# Firefox SQLite parser
# ---------------------------------------------------------------------------

def _parse_sqlite(
    sqlite_path: str,
    out_path: Path,
    browser_label: str,
    source_path: str,
    artifact_type: str,
) -> tuple[int, int]:
    """Parse a Firefox places.sqlite and write one archive page.

    Returns (bookmark_count, folder_count).
    """
    conn = sqlite3.connect(f"file:{sqlite_path}?mode=ro", uri=True)
    try:
        cursor = conn.cursor()
        _validate_gecko_schema(cursor)

        stats     = [0, 0]   # [bookmarks, folders]
        nav_links = []
        sections  = []

        def _walk(parent_id: int, html_out: list, depth: int = 0,
                  top_name: str = "") -> None:
            if depth == 0:
                # Top-level root folder → open a named section
                slug = f"folder-{_slugify(top_name)}"
                nav_links.append((slug, top_name))
                html_out.append(
                    f"        <section id='{slug}' aria-labelledby='h-{slug}'>"
                )
                html_out.append(
                    f"            <h2 id='h-{slug}'>{escape(top_name)}</h2>"
                )
                html_out.append("            <dl>")

            cursor.execute(
                "SELECT b.id, b.type, b.title, p.url, b.dateAdded "
                "FROM moz_bookmarks b "
                "LEFT JOIN moz_places p ON b.fk = p.id "
                "WHERE b.parent = ? ORDER BY b.position",
                (parent_id,),
            )
            for item_id, item_type, title, url, date_added in cursor.fetchall():
                name = title or "Unnamed"

                if item_type == 2:   # folder
                    stats[1] += 1
                    html_out.append(
                        f"            <dt class='folder-label'>"
                        f"&#128193; {escape(name)}</dt>"
                    )
                    html_out.append("            <dl>")
                    _walk(item_id, html_out, depth + 1)
                    html_out.append("            </dl>")

                elif item_type == 1 and url:   # bookmark
                    stats[0] += 1
                    safe_name  = escape(name)
                    safe_url   = escape(url, quote=True)
                    unix_time  = int(date_added) // 1_000_000 if date_added else 0
                    human_date = get_human_date(unix_time)
                    aria       = escape(f"{name}. Added: {human_date}")

                    html_out.append("            <dt>")
                    html_out.append(
                        f"                <a href='{safe_url}' aria-label='{aria}'>"
                        f"{safe_name}</a>"
                    )
                    html_out.append("            </dt>")

            if depth == 0:
                html_out.append("            </dl>")
                html_out.append("        </section>")

        cursor.execute(
            "SELECT id, title FROM moz_bookmarks "
            "WHERE parent = 1 AND type = 2 ORDER BY position"
        )
        for root_id, root_title in cursor.fetchall():
            _walk(root_id, sections, depth=0, top_name=root_title or "Root")

        _write_archive_page(out_path, browser_label, source_path, artifact_type,
                            nav_links, sections)
        return stats[0], stats[1]

    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_archive(raw_dir_path: str, archive_dir_path: str) -> dict:
    """Read manifest.json from *raw_dir_path* and build a styled HTML5 archive.

    Parameters
    ----------
    raw_dir_path:
        Folder produced by the Retriever - must contain ``manifest.json``.
    archive_dir_path:
        Destination for the archive site.  Created if it does not exist.

    Returns
    -------
    dict with keys:
        status, converted, bookmarks, folders, warnings

    Raises
    ------
    FileNotFoundError
        If *raw_dir_path* or its manifest.json cannot be found.
    """
    raw_dir     = Path(raw_dir_path)
    archive_dir = Path(archive_dir_path)

    if not raw_dir.exists():
        raise FileNotFoundError(f"Raw directory not found: {raw_dir}")

    manifest_path = raw_dir / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(
            "A manifest.json file is required but was not found.\n"
            "Run the Extractor (Tab 1) first to generate it."
        )

    archive_dir.mkdir(parents=True, exist_ok=True)
    _write_css(archive_dir)

    result: dict = {
        "status":    "ok",
        "converted": 0,
        "bookmarks": 0,
        "folders":   0,
        "warnings":  [],
    }
    site_map: dict = {}
    seen: set = set()

    with open(manifest_path, "r", encoding="utf-8") as fh:
        manifest = json.load(fh)

    for artifact in manifest.get("artifacts", []):
        if artifact.get("status") != "copied":
            continue

        artifact_type = artifact.get("artifact_type")
        if artifact_type not in {"chromium_bookmarks_json", "gecko_places_sqlite"}:
            continue

        copied_path = Path(artifact.get("copied_path", ""))
        if not copied_path.exists():
            result["warnings"].append(f"Missing artifact file: {copied_path}")
            continue

        username    = artifact.get("username", "UnknownUser")
        browser     = artifact.get("browser",  "UnknownBrowser")
        profile     = artifact.get("profile",  "UnknownProfile")
        source_path = artifact.get("source_path", "Unknown Source")

        dedup_key = (username, browser, profile, artifact_type)
        if dedup_key in seen:
            result["warnings"].append(
                f"Duplicate skipped: {username}/{browser}/{profile}"
            )
            continue
        seen.add(dedup_key)

        out_folder    = archive_dir / username / browser / profile
        out_folder.mkdir(parents=True, exist_ok=True)
        out_html      = out_folder / "bookmarks.html"
        rel_link      = f"{username}/{browser}/{profile}/bookmarks.html"
        display_label = f"{browser} ({profile})"

        try:
            if artifact_type == "chromium_bookmarks_json":
                bm, fo = _parse_json(
                    str(copied_path), out_html, display_label, source_path, artifact_type
                )
            else:
                bm, fo = _parse_sqlite(
                    str(copied_path), out_html, display_label, source_path, artifact_type
                )

            site_map.setdefault(username, {}).setdefault(browser, []).append(
                (profile, rel_link, bm, fo)
            )
            result["converted"] += 1
            result["bookmarks"] += bm
            result["folders"]   += fo

        except Exception as exc:
            result["warnings"].append(f"Failed to style {copied_path}: {exc}")

    _write_hub_index(archive_dir, site_map)
    return result


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        prog="python -m core.archive_beautifier",
        description="Build a styled HTML5 archive from extracted bookmark artifacts.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  python -m core.archive_beautifier "C:\\Bookmark_Rescue\\Raw" "C:\\Bookmark_Rescue\\Archive"
  python -m core.archive_beautifier ./raw_output ./stylized_archive
        """,
    )
    parser.add_argument("source", help="Raw Extractor folder (must contain manifest.json)")
    parser.add_argument("output", help="Destination folder for the styled archive")
    args = parser.parse_args()

    print(f"Raw data : {args.source}")
    print(f"Archive  : {args.output}")
    print()

    try:
        res = build_archive(args.source, args.output)
    except (FileNotFoundError, PermissionError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Converted : {res['converted']} page(s)")
    print(f"Bookmarks : {res['bookmarks']}")
    print(f"Folders   : {res['folders']}")
    if res["warnings"]:
        print(f"\nWarnings ({len(res['warnings'])}):")
        for w in res["warnings"]:
            print(f"  [!] {w}")
    print(f"\nArchive ready: {Path(args.output) / 'index.html'}")