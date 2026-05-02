"""
bookmark_merger.py - Bookmark Rescue Toolkit
=============================================
Merge bookmarks from multiple browsers into one clean, deduplicated Netscape
HTML file ready to import into any browser.  Also exports to CSV and JSON for
use in Notion, Airtable, Excel, or custom databases.

Sources accepted
----------------
  • Netscape Bookmark HTML   our generated output, or native browser exports
  • Chromium Bookmarks JSON  the raw file extracted by the Retriever
  • Firefox places.sqlite    the raw database extracted by the Retriever
  • A raw extracted folder   reads manifest.json and processes everything at once

Standalone usage
----------------
  python -m core.bookmark_merger -s file1.html file2.html -o merged.html
  python -m core.bookmark_merger --raw "C:\\Raw" -o merged.html
  python -m core.bookmark_merger --raw "C:\\Raw" -o merged.html --no-dedup --no-group
  python -m core.bookmark_merger --raw "C:\\Raw" --export-csv bookmarks.csv
  python -m core.bookmark_merger --raw "C:\\Raw" --export-json bookmarks.json
"""

from __future__ import annotations

import csv
import json
import sqlite3
import sys
from dataclasses import dataclass, field
from html import escape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse, urlunparse

from .utils import get_human_date


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class BookmarkEntry:
    """One bookmark with its original folder path and source label."""
    url:          str
    title:        str
    add_date:     int   = 0
    folder_path:  tuple = field(default_factory=tuple)   # outermost → innermost
    source_label: str   = ""


# ---------------------------------------------------------------------------
# URL normalisation
# ---------------------------------------------------------------------------

def _normalize_url(url: str) -> str:
    """Return a scheme-agnostic canonical key for deduplication.

    ``http://example.com/page`` and ``https://example.com/page`` produce the
    same key so they are treated as the same bookmark.  The dedup logic in
    ``merge_sources`` separately decides which version to keep (preferring
    https when both are present).

    Query strings are preserved - ``/search?q=foo`` and ``/search?q=bar``
    are distinct pages.  Fragments (#anchor) are dropped.
    """
    url = url.strip()
    if not url:
        return ""
    try:
        p          = urlparse(url)
        clean_path = p.path.rstrip("/") or "/"
        key = p.netloc.lower() + clean_path
        if p.query:
            key += "?" + p.query
        return key
    except Exception:
        return url.lower()


def _is_https(url: str) -> bool:
    return url.startswith("https://")


# ---------------------------------------------------------------------------
# Input parsers
# ---------------------------------------------------------------------------

class _NetscapeParser(HTMLParser):
    """Parse a Netscape Bookmark HTML file into BookmarkEntry objects.

    Handles both our generated output and native browser exports from
    Chrome, Edge, Firefox, Safari, and most others.
    """

    def __init__(self, source_label: str = "") -> None:
        super().__init__(convert_charrefs=True)
        self.bookmarks:       list[BookmarkEntry] = []
        self._source_label    = source_label
        self._folder_stack:   list[str]  = []
        self._pending_folder: str | None = None
        self._current_tag:    str | None = None
        self._current_attrs:  dict       = {}
        self._buf:            str        = ""

    def handle_starttag(self, tag: str, attrs) -> None:
        tag        = tag.lower()
        attrs_dict = dict(attrs)
        if tag in ("a", "h3"):
            self._current_tag   = tag
            self._current_attrs = attrs_dict
            self._buf           = ""
        elif tag == "dl" and self._pending_folder is not None:
            self._folder_stack.append(self._pending_folder)
            self._pending_folder = None

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "a" and self._current_tag == "a":
            url   = self._current_attrs.get("href", "").strip()
            title = self._buf.strip() or "Unnamed"
            if url and not url.startswith(
                ("place:", "javascript:", "chrome://", "about:", "data:")
            ):
                self.bookmarks.append(BookmarkEntry(
                    url          = url,
                    title        = title,
                    add_date     = _safe_int(self._current_attrs.get("add_date", 0)),
                    folder_path  = tuple(self._folder_stack),
                    source_label = self._source_label,
                ))
            self._current_tag = None
            self._buf         = ""
        elif tag == "h3" and self._current_tag == "h3":
            self._pending_folder = self._buf.strip() or "Unnamed Folder"
            self._current_tag    = None
            self._buf            = ""
        elif tag == "dl":
            if self._folder_stack:
                self._folder_stack.pop()
            self._pending_folder = None

    def handle_data(self, data: str) -> None:
        if self._current_tag in ("a", "h3"):
            self._buf += data


def _safe_int(value) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _chrome_time(webkit_ts) -> int:
    try:
        return int((int(webkit_ts) - 11_644_473_600_000_000) / 1_000_000)
    except (TypeError, ValueError):
        return 0


def parse_netscape_html(path: str, source_label: str = "") -> list[BookmarkEntry]:
    """Parse a Netscape Bookmark HTML file.  Returns a list of BookmarkEntry."""
    label  = source_label or Path(path).stem
    parser = _NetscapeParser(source_label=label)
    parser.feed(Path(path).read_text(encoding="utf-8", errors="replace"))
    return parser.bookmarks


def parse_chromium_json(path: str, source_label: str = "") -> list[BookmarkEntry]:
    """Parse a Chromium Bookmarks JSON file.  Returns a list of BookmarkEntry."""
    label = source_label or Path(path).stem
    with open(path, "r", encoding="utf-8") as fh:
        try:
            data = json.load(fh)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Not valid JSON: {exc}") from exc

    if not isinstance(data, dict) or "roots" not in data:
        raise ValueError(f"Not a Chromium Bookmarks file (missing 'roots'): {path}")

    entries: list[BookmarkEntry] = []

    def _walk(node: dict, folder_stack: tuple) -> None:
        ntype = node.get("type")
        if ntype == "folder":
            name = node.get("name", "Unnamed Folder")
            for child in node.get("children", []):
                _walk(child, folder_stack + (name,))
        elif ntype == "url":
            url = node.get("url", "").strip()
            if url and not url.startswith(("javascript:", "data:", "chrome://")):
                entries.append(BookmarkEntry(
                    url          = url,
                    title        = node.get("name", "Unnamed"),
                    add_date     = _chrome_time(node.get("date_added", 0)),
                    folder_path  = folder_stack,
                    source_label = label,
                ))

    for key in ("bookmark_bar", "other", "synced"):
        root = data["roots"].get(key)
        if root:
            _walk(root, ())

    return entries


def parse_firefox_sqlite(path: str, source_label: str = "") -> list[BookmarkEntry]:
    """Parse a Firefox places.sqlite.  Returns a list of BookmarkEntry."""
    label   = source_label or Path(path).stem
    entries: list[BookmarkEntry] = []

    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name IN ('moz_bookmarks','moz_places')"
        )
        if len(cursor.fetchall()) < 2:
            raise RuntimeError(f"Not a valid Firefox places.sqlite: {path}")

        def _walk(parent_id: int, folder_stack: tuple) -> None:
            cursor.execute(
                "SELECT b.id, b.type, b.title, p.url, b.dateAdded "
                "FROM moz_bookmarks b "
                "LEFT JOIN moz_places p ON b.fk = p.id "
                "WHERE b.parent = ? ORDER BY b.position",
                (parent_id,),
            )
            for item_id, item_type, title, url, date_added in cursor.fetchall():
                if item_type == 2:
                    _walk(item_id, folder_stack + (title or "Unnamed Folder",))
                elif item_type == 1 and url:
                    if not url.startswith(("place:", "javascript:", "data:")):
                        entries.append(BookmarkEntry(
                            url          = url,
                            title        = title or "Unnamed",
                            add_date     = (int(date_added) // 1_000_000
                                            if date_added else 0),
                            folder_path  = folder_stack,
                            source_label = label,
                        ))

        cursor.execute(
            "SELECT id, title FROM moz_bookmarks "
            "WHERE parent = 1 AND type = 2 ORDER BY position"
        )
        for root_id, root_title in cursor.fetchall():
            _walk(root_id, ())

    finally:
        conn.close()

    return entries


# ---------------------------------------------------------------------------
# Tree builder and Netscape HTML writer
# ---------------------------------------------------------------------------

def _build_folder_tree(entries: list[BookmarkEntry]) -> dict:
    """Convert a flat entry list into a nested folder tree dict."""
    root: dict = {"_bookmarks": []}
    for entry in entries:
        node = root
        for folder in entry.folder_path:
            if folder not in node:
                node[folder] = {"_bookmarks": []}
            node = node[folder]
        node["_bookmarks"].append(entry)
    return root


def _write_tree(node: dict, lines: list, indent: int = 1) -> None:
    """Recursively emit Netscape HTML from a folder tree node."""
    pad = "    " * indent
    for entry in node["_bookmarks"]:
        safe_url   = escape(entry.url, quote=True)
        safe_title = escape(entry.title, quote=True)
        human_date = get_human_date(entry.add_date)
        meta       = escape(
            f"Source: {entry.source_label} | Added: {human_date}", quote=True
        )
        lines.append(
            f'{pad}<DT><A HREF="{safe_url}" ADD_DATE="{entry.add_date}"'
            f' TITLE="{meta}" aria-label="{safe_title}. {meta}">'
            f'{safe_title}</A>'
        )
    for folder_name, child_node in node.items():
        if folder_name == "_bookmarks":
            continue
        lines.append(f'{pad}<DT><H3>{escape(folder_name, quote=True)}</H3>')
        lines.append(f'{pad}<DL><p>')
        _write_tree(child_node, lines, indent + 1)
        lines.append(f'{pad}</DL><p>')


def _write_netscape(
    sources: list[tuple[str, list[BookmarkEntry]]],
    output_path: str,
    group_by_source: bool = True,
) -> None:
    lines = [
        "<!DOCTYPE NETSCAPE-Bookmark-file-1>",
        "",
        '<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">',
        "<TITLE>Merged Bookmarks \u2014 Bookmark Rescue Toolkit</TITLE>",
        "<H1>Merged Bookmarks</H1>",
        "<DL><p>",
    ]
    if group_by_source:
        for label, entries in sources:
            if not entries:
                continue
            lines.append(f'    <DT><H3>{escape(label, quote=True)}</H3>')
            lines.append('    <DL><p>')
            _write_tree(_build_folder_tree(entries), lines, indent=2)
            lines.append('    </DL><p>')
    else:
        all_entries: list[BookmarkEntry] = []
        for _, entries in sources:
            all_entries.extend(entries)
        _write_tree(_build_folder_tree(all_entries), lines, indent=1)
    lines.append("</DL><p>")
    Path(output_path).write_text("\n".join(lines), encoding="utf-8")


# ---------------------------------------------------------------------------
# Shared source loader (used by all three export functions)
# ---------------------------------------------------------------------------

def _load_sources(
    sources: list[dict],
    deduplicate: bool,
) -> tuple[list[tuple[str, list[BookmarkEntry]]], dict]:
    """Parse and optionally deduplicate all sources.

    Returns (parsed_sources, partial_result_dict).

    Deduplication is scheme-agnostic: ``http://`` and ``https://`` with the
    same host+path are treated as the same bookmark.  When both exist, the
    ``https://`` version is kept in the output; all other fields (title,
    folder, date) come from the first-seen entry.
    """
    result: dict = {
        "total_input":        0,
        "duplicates_removed": 0,
        "total_output":       0,
        "sources_processed":  0,
        "warnings":           [],
    }
    parsed: list[tuple[str, list[BookmarkEntry]]] = []

    # norm_key → index into the current source's unique list
    # Shared across all sources so cross-source dedup works correctly.
    seen: dict[str, tuple[int, int]] = {}   # key → (source_idx, entry_idx)
    all_parsed: list[tuple[str, list]] = []

    for src in sources:
        src_type  = src.get("type", "html")
        src_path  = src.get("path", "")
        src_label = src.get("label", Path(src_path).stem)

        if not Path(src_path).exists():
            result["warnings"].append(f"File not found, skipped: {src_path}")
            continue

        try:
            if src_type == "json":
                entries = parse_chromium_json(src_path, source_label=src_label)
            elif src_type == "sqlite":
                entries = parse_firefox_sqlite(src_path, source_label=src_label)
            else:
                entries = parse_netscape_html(src_path, source_label=src_label)
        except Exception as exc:
            result["warnings"].append(f"Could not parse {src_path}: {exc}")
            continue

        result["total_input"]       += len(entries)
        result["sources_processed"] += 1
        all_parsed.append((src_label, entries))

    # Run deduplication across the combined pool
    deduped: list[tuple[str, list[BookmarkEntry]]] = []
    seen_key: dict[str, tuple[int, int]] = {}   # norm → (source_idx, entry_idx)

    for s_idx, (label, entries) in enumerate(all_parsed):
        unique: list[BookmarkEntry] = []
        for entry in entries:
            norm = _normalize_url(entry.url)
            if not norm:
                unique.append(entry)
                continue

            if not deduplicate or norm not in seen_key:
                seen_key[norm] = (s_idx, len(unique))
                unique.append(entry)
            else:
                # Upgrade http → https if the incoming entry is the secure version
                prev_si, prev_ei = seen_key[norm]
                prev_source_entries = deduped[prev_si][1] if prev_si < len(deduped) else unique
                if prev_si < len(deduped):
                    prev_entry = deduped[prev_si][1][prev_ei]
                    if _is_https(entry.url) and not _is_https(prev_entry.url):
                        deduped[prev_si][1][prev_ei] = BookmarkEntry(
                            url          = entry.url,
                            title        = prev_entry.title,
                            add_date     = prev_entry.add_date,
                            folder_path  = prev_entry.folder_path,
                            source_label = prev_entry.source_label,
                        )
                result["duplicates_removed"] += 1

        deduped.append((label, unique))

    result["total_output"] = sum(len(e) for _, e in deduped)
    return deduped, result


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def merge_sources(
    sources: list[dict],
    output_path: str,
    deduplicate:     bool = True,
    group_by_source: bool = True,
) -> dict:
    """Merge bookmark sources into one Netscape HTML file.

    Parameters
    ----------
    sources:
        List of source dicts with keys ``type`` ("html"/"json"/"sqlite"),
        ``path``, and ``label``.
    output_path:
        Destination ``.html`` file.
    deduplicate:
        Remove duplicate bookmarks by URL (scheme-agnostic; https preferred).
    group_by_source:
        Wrap each source's bookmarks in a named top-level folder.

    Returns
    -------
    dict with keys: status, total_input, duplicates_removed, total_output,
                    sources_processed, warnings
    """
    parsed, result = _load_sources(sources, deduplicate)
    result["status"] = "ok"

    if parsed and result["total_output"] > 0:
        _write_netscape(parsed, output_path, group_by_source=group_by_source)
    else:
        result["status"] = "empty"
        result["warnings"].append("No bookmarks were collected from the provided sources.")

    return result


def export_to_csv(
    sources: list[dict],
    output_path: str,
    deduplicate: bool = True,
) -> dict:
    """Export all bookmark sources to a flat CSV file.

    Columns: title, url, folder_path, source, date_added, date_human

    The folder path is written as a slash-separated string so it reads
    naturally in spreadsheet tools: ``Toolbar / Work / Dev Tools``

    Parameters and return dict are the same shape as ``merge_sources``.
    """
    parsed, result = _load_sources(sources, deduplicate)
    result["status"] = "ok"

    rows: list[dict] = []
    for _label, entries in parsed:
        for entry in entries:
            rows.append({
                "title":       entry.title,
                "url":         entry.url,
                "folder_path": " / ".join(entry.folder_path) if entry.folder_path else "",
                "source":      entry.source_label,
                "date_added":  entry.add_date,
                "date_human":  get_human_date(entry.add_date),
            })

    if not rows:
        result["status"] = "empty"
        result["warnings"].append("No bookmarks were collected from the provided sources.")
        return result

    with open(output_path, "w", newline="", encoding="utf-8-sig") as fh:
        # utf-8-sig adds the UTF-8 BOM that Excel requires to display Unicode correctly
        writer = csv.DictWriter(
            fh,
            fieldnames=["title", "url", "folder_path", "source", "date_added", "date_human"],
        )
        writer.writeheader()
        writer.writerows(rows)

    return result


def export_to_json(
    sources: list[dict],
    output_path: str,
    deduplicate: bool = True,
) -> dict:
    """Export all bookmark sources to a structured JSON file.

    Output is an array of objects:
    ``[{ "title", "url", "folder_path", "source", "date_added", "date_human" }, …]``

    The ``folder_path`` field is a list of strings (outermost → innermost)
    so consumers can reconstruct the hierarchy if needed.

    Parameters and return dict are the same shape as ``merge_sources``.
    """
    parsed, result = _load_sources(sources, deduplicate)
    result["status"] = "ok"

    records: list[dict] = []
    for _label, entries in parsed:
        for entry in entries:
            records.append({
                "title":       entry.title,
                "url":         entry.url,
                "folder_path": list(entry.folder_path),
                "source":      entry.source_label,
                "date_added":  entry.add_date,
                "date_human":  get_human_date(entry.add_date),
            })

    if not records:
        result["status"] = "empty"
        result["warnings"].append("No bookmarks were collected from the provided sources.")
        return result

    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(records, fh, indent=2, ensure_ascii=False)

    return result


def merge_from_raw(
    raw_dir_path: str,
    output_path:  str,
    deduplicate:     bool = True,
    group_by_source: bool = True,
) -> dict:
    """Convenience: read manifest.json and merge all primary artifacts."""
    return merge_sources(
        _sources_from_manifest(raw_dir_path),
        output_path,
        deduplicate=deduplicate,
        group_by_source=group_by_source,
    )


def sources_from_manifest(raw_dir_path: str) -> list[dict]:
    manifest_path = Path(raw_dir_path) / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(
            f"manifest.json not found in {raw_dir_path}. "
            "Run the Extractor (Tab 1) first to generate it."
        )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    sources: list[dict] = []
    for artifact in manifest.get("artifacts", []):
        if artifact.get("status") != "copied":
            continue
        atype = artifact.get("artifact_type", "")
        if atype not in ("chromium_bookmarks_json", "gecko_places_sqlite"):
            continue
        sources.append({
            "type":  "json" if "json" in atype else "sqlite",
            "path":  artifact.get("copied_path", ""),
            "label": f"{artifact.get('browser','')} ({artifact.get('profile','')})",
        })
    return sources


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        prog="python -m core.bookmark_merger",
        description="Merge and export bookmarks from multiple sources.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  python -m core.bookmark_merger -s chrome.html firefox.html -o merged.html
  python -m core.bookmark_merger --raw "C:\\Raw" -o merged.html
  python -m core.bookmark_merger --raw "C:\\Raw" --export-csv bookmarks.csv
  python -m core.bookmark_merger --raw "C:\\Raw" --export-json bookmarks.json
  python -m core.bookmark_merger --raw "C:\\Raw" -o merged.html --no-dedup --no-group
        """,
    )
    g = parser.add_mutually_exclusive_group(required=True)
    g.add_argument("-s", "--sources", nargs="+", metavar="FILE",
                   help="One or more Netscape HTML, JSON, or SQLite files")
    g.add_argument("--raw", metavar="FOLDER",
                   help="Raw extracted folder (reads manifest.json automatically)")

    parser.add_argument("-o", "--output",       metavar="FILE", help="Output HTML file")
    parser.add_argument("--export-csv",         metavar="FILE", help="Export to CSV file")
    parser.add_argument("--export-json",        metavar="FILE", help="Export to JSON file")
    parser.add_argument("--no-dedup",  action="store_true", help="Disable URL deduplication")
    parser.add_argument("--no-group",  action="store_true", help="Disable source grouping in HTML")
    args = parser.parse_args()

    if not any([args.output, args.export_csv, args.export_json]):
        parser.error("Specify at least one output: --output, --export-csv, or --export-json")

    dedup = not args.no_dedup
    group = not args.no_group

    if args.raw:
        try:
            src_list = sources_from_manifest(args.raw)
        except FileNotFoundError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)
    else:
        src_list = []
        for p in args.sources:
            ext = Path(p).suffix.lower()
            t   = "sqlite" if ext == ".sqlite" else ("json" if ext == ".json" else "html")
            src_list.append({"type": t, "path": p, "label": Path(p).stem})

    res = None
    if args.output:
        res = merge_sources(src_list, args.output, deduplicate=dedup, group_by_source=group)
        print(f"Merged HTML   : {args.output}")
    if args.export_csv:
        res = export_to_csv(src_list, args.export_csv, deduplicate=dedup)
        print(f"Exported CSV  : {args.export_csv}")
    if args.export_json:
        res = export_to_json(src_list, args.export_json, deduplicate=dedup)
        print(f"Exported JSON : {args.export_json}")

    if res:
        print(f"\nSources processed : {res['sources_processed']}")
        print(f"Input bookmarks   : {res['total_input']}")
        print(f"Duplicates removed: {res['duplicates_removed']}")
        print(f"Output bookmarks  : {res['total_output']}")
        if res["warnings"]:
            print(f"\nWarnings ({len(res['warnings'])}):")
            for w in res["warnings"]:
                print(f"  [!] {w}")
