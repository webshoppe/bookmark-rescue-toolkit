"""
json_to_html.py - Bookmark Rescue Toolkit
==========================================
Converts a Chromium-style Bookmarks JSON file into a Netscape Bookmark HTML
file that can be imported by any modern browser.

Supported sources (any Chromium-family browser)
------------------------------------------------
  Google Chrome, Microsoft Edge, Brave, Vivaldi, Opera, Arc,
  DuckDuckGo, Comet, Ungoogled Chromium, and more.

Standalone usage
----------------
  python -m core.json_to_html Bookmarks output.html
  python -m core.json_to_html Bookmarks output.html --browser "Brave"
"""

from __future__ import annotations

import json
import os
import sys
from html import escape

from .utils import get_human_date


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _convert_chrome_time(webkit_timestamp) -> int:
    """Convert a WebKit/Chromium microsecond timestamp to a Unix timestamp.

    Chromium stores dates as microseconds since 1601-01-01.  Subtracting the
    delta to the Unix epoch (1970-01-01) gives a standard Unix timestamp.
    Returns 0 for any value that cannot be parsed.
    """
    try:
        unix_time = (int(webkit_timestamp) - 11_644_473_600_000_000) / 1_000_000
        return int(unix_time)
    except (ValueError, TypeError):
        return 0


def _parse_node(
    node: dict,
    html_output: list,
    stats: dict,
    browser_name: str = "Chromium",
    indent_level: int = 1,
) -> None:
    """Recursively walk the Chromium bookmark tree, appending HTML lines.

    html.escape(..., quote=True) is used for every user-supplied string that
    lands inside an HTML attribute so that characters such as &, <, >, and
    quotes cannot break the output structure.
    """
    indent    = "    " * indent_level
    node_type = node.get("type")

    if node_type == "folder":
        stats["folders"] += 1
        folder_name = escape(node.get("name", "Unnamed Folder"), quote=True)
        add_date    = _convert_chrome_time(node.get("date_added", 0))

        html_output.append(f'{indent}<DT><H3 ADD_DATE="{add_date}">{folder_name}</H3>')
        html_output.append(f"{indent}<DL><p>")
        for child in node.get("children", []):
            _parse_node(child, html_output, stats, browser_name, indent_level + 1)
        html_output.append(f"{indent}</DL><p>")

    elif node_type == "url":
        stats["bookmarks"] += 1
        name          = escape(node.get("name", "Unnamed Bookmark"), quote=True)
        url           = escape(node.get("url",  ""),                  quote=True)
        add_date_unix = _convert_chrome_time(node.get("date_added", 0))
        human_date    = get_human_date(add_date_unix)
        meta_string   = escape(f"Browser: {browser_name} | Added: {human_date}", quote=True)
        safe_browser  = escape(browser_name, quote=True)

        html_output.append(
            f'{indent}<DT><A HREF="{url}" ADD_DATE="{add_date_unix}"'
            f' TITLE="{meta_string}" aria-label="{name}. {meta_string}"'
            f' data-browser="{safe_browser}">{name}</A>'
        )

    elif node_type is not None:
        stats["warnings"].append(f"Skipped unknown node type: {node_type!r}")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def convert_json_to_html(
    json_file_path: str,
    output_html_path: str,
    browser_label: str = "Chromium",
) -> dict:
    """Convert *json_file_path* to a Netscape Bookmark HTML file.

    Parameters
    ----------
    json_file_path:
        Path to a Chromium ``Bookmarks`` file (with or without ``.json``
        extension - Chromium uses no extension by default).
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
        If *json_file_path* does not exist.
    ValueError
        If the file is not valid JSON, or is JSON but not a Chromium Bookmarks
        file (i.e. missing the ``roots`` key).
    """
    if not os.path.exists(json_file_path):
        raise FileNotFoundError(f"Source file not found: {json_file_path}")

    with open(json_file_path, "r", encoding="utf-8") as fh:
        try:
            data = json.load(fh)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"File is not valid JSON ({json_file_path}): {exc}"
            ) from exc

    if not isinstance(data, dict) or "roots" not in data:
        raise ValueError(
            f"File does not appear to be a Chromium Bookmarks file "
            f"(missing 'roots' key): {json_file_path}"
        )

    stats: dict = {
        "status":    "ok",
        "bookmarks": 0,
        "folders":   0,
        "warnings":  [],
        "source":    json_file_path,
        "output":    output_html_path,
        "browser":   browser_label,
    }

    safe_label = escape(browser_label, quote=True)
    html_lines = [
        "<!DOCTYPE NETSCAPE-Bookmark-file-1>",
        "",
        '<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">',
        f"<TITLE>Recovered Bookmarks \u2014 {safe_label}</TITLE>",
        f"<H1>Recovered Bookmarks ({safe_label})</H1>",
        "<DL><p>",
    ]

    roots_found = False
    for root_key in ("bookmark_bar", "other", "synced"):
        root_node = data["roots"].get(root_key)
        if root_node:
            roots_found = True
            _parse_node(root_node, html_lines, stats, browser_label)

    if not roots_found:
        stats["warnings"].append(
            "No standard Chromium root keys found "
            "(expected: bookmark_bar, other, or synced)."
        )

    html_lines.append("</DL><p>")

    with open(output_html_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(html_lines))

    return stats


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        prog="python -m core.json_to_html",
        description="Convert a Chromium Bookmarks JSON file to Netscape Bookmark HTML.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  python -m core.json_to_html Bookmarks output.html
  python -m core.json_to_html Chrome_Bookmarks.json output.html --browser "Google Chrome"
  python -m core.json_to_html Bookmarks output.html --browser "Brave"
        """,
    )
    parser.add_argument("source",
                        help="Path to the Chromium Bookmarks file (JSON, no extension is fine)")
    parser.add_argument("output",
                        help="Path for the output HTML file (e.g. bookmarks.html)")
    parser.add_argument("--browser", default="Chromium",
                        help='Browser label used in the HTML title (default: "Chromium")')
    args = parser.parse_args()

    try:
        stats = convert_json_to_html(args.source, args.output, browser_label=args.browser)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Converted : {stats['bookmarks']} bookmarks, {stats['folders']} folders")
    if stats["warnings"]:
        for w in stats["warnings"]:
            print(f"  [!] {w}")
    print(f"Output    : {args.output}")
