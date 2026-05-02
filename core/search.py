"""
search.py - Bookmark Rescue Toolkit
=====================================
Search bookmarks by title or URL across all source types without converting
them first.  Reads directly from the Retriever's manifest, or accepts
individual Netscape HTML, Chromium JSON, and Firefox SQLite files.

Standalone usage
----------------
  python -m core.search --raw "C:\\Raw" "github"
  python -m core.search -s bookmarks.html places.sqlite -q "python tutorial"
  python -m core.search --raw "C:\\Raw" "youtube" --field url
  python -m core.search --raw "C:\\Raw" "recipe" --limit 50
"""

from __future__ import annotations

import sys
from pathlib import Path

from .bookmark_merger import (
    BookmarkEntry,
    sources_from_manifest,
    parse_chromium_json,
    parse_firefox_sqlite,
    parse_netscape_html,
)
from .utils import get_human_date


# ---------------------------------------------------------------------------
# Core search
# ---------------------------------------------------------------------------

def search_bookmarks(
    sources: list[dict],
    query: str,
    field: str = "both",
    limit: int = 0,
    case_sensitive: bool = False,
) -> list[BookmarkEntry]:
    """Search bookmarks across multiple sources.

    Parameters
    ----------
    sources:
        List of source dicts (same format as bookmark_merger) - each with
        keys ``type`` ("html"/"json"/"sqlite"), ``path``, and ``label``.
    query:
        Search term.  Supports multiple words (all must appear, order doesn't
        matter) and a leading ``-`` to exclude a term, e.g.
        ``"python -tutorial"`` finds entries with "python" but not "tutorial".
    field:
        ``"title"``  - search only the bookmark title.
        ``"url"``    - search only the URL.
        ``"both"``   - search title and URL (default).
    limit:
        Maximum number of results (0 = no limit).
    case_sensitive:
        Default False.

    Returns
    -------
    List of matching BookmarkEntry objects, deduplication is NOT applied
    so users see all occurrences across browsers.
    """
    if not query.strip():
        return []

    # Parse query into required terms and excluded terms
    terms_raw    = query.strip().split()
    must_have    = [t.lower()  for t in terms_raw if not t.startswith("-")]
    must_not     = [t[1:].lower() for t in terms_raw if t.startswith("-") and len(t) > 1]

    def _matches(entry: BookmarkEntry) -> bool:
        title = entry.title if case_sensitive else entry.title.lower()
        url   = entry.url   if case_sensitive else entry.url.lower()

        haystack = ""
        if field in ("both", "title"):
            haystack += " " + title
        if field in ("both", "url"):
            haystack += " " + url

        for term in must_have:
            t = term if case_sensitive else term.lower()
            if t not in haystack:
                return False
        for term in must_not:
            t = term if case_sensitive else term.lower()
            if t in haystack:
                return False
        return True

    results: list[BookmarkEntry] = []
    for src in sources:
        src_type  = src.get("type", "html")
        src_path  = src.get("path", "")
        src_label = src.get("label", Path(src_path).stem)

        if not Path(src_path).exists():
            continue

        try:
            if src_type == "json":
                entries = parse_chromium_json(src_path, source_label=src_label)
            elif src_type == "sqlite":
                entries = parse_firefox_sqlite(src_path, source_label=src_label)
            else:
                entries = parse_netscape_html(src_path, source_label=src_label)
        except Exception:
            continue

        for entry in entries:
            if _matches(entry):
                results.append(entry)
                if limit and len(results) >= limit:
                    return results

    return results


def search_from_raw(
    raw_dir_path: str,
    query: str,
    field: str = "both",
    limit: int = 0,
    case_sensitive: bool = False,
) -> list[BookmarkEntry]:
    """Search directly from a Retriever output folder's manifest.json.

    Raises FileNotFoundError if manifest.json is absent.
    """
    return search_bookmarks(
        sources_from_manifest(raw_dir_path),
        query,
        field=field,
        limit=limit,
        case_sensitive=case_sensitive,
    )


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        prog="python -m core.search",
        description="Search bookmarks by title or URL across multiple sources.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
query syntax:
  Words are ANDed - all must match.
  Prefix a word with - to exclude it.

  "python tutorial"        → title or URL contains both "python" and "tutorial"
  "python -video"          → contains "python" but not "video"
  "github.com"             → matches that domain in the URL

examples:
  python -m core.search --raw "C:\\Raw" "github"
  python -m core.search --raw "C:\\Raw" "recipe -video" --field title
  python -m core.search -s bookmarks.html places.sqlite -q "youtube"
  python -m core.search --raw "C:\\Raw" "python" --limit 20 --field url
        """,
    )
    g = parser.add_mutually_exclusive_group(required=True)
    g.add_argument("--raw", metavar="FOLDER",
                   help="Raw extracted folder (reads manifest.json)")
    g.add_argument("-s", "--sources", nargs="+", metavar="FILE",
                   help="One or more Netscape HTML, JSON, or SQLite files")

    parser.add_argument("query", nargs="?",
                        help="Search query (words ANDed; prefix with - to exclude)")
    parser.add_argument("-q", "--query-flag", metavar="QUERY",
                        help="Alternative way to pass the query (useful in scripts)")
    parser.add_argument("--field", choices=["both", "title", "url"], default="both",
                        help="Which field to search (default: both)")
    parser.add_argument("--limit", type=int, default=0,
                        help="Maximum number of results (default: 0 = unlimited)")
    parser.add_argument("--case-sensitive", action="store_true",
                        help="Make the search case-sensitive")
    args = parser.parse_args()

    query_str = args.query_flag or args.query or ""
    if not query_str.strip():
        parser.error("Provide a search query as a positional argument or via -q.")

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

    results = search_bookmarks(
        src_list, query_str,
        field=args.field,
        limit=args.limit,
        case_sensitive=args.case_sensitive,
    )

    if not results:
        print(f"No bookmarks matched: {query_str!r}")
        sys.exit(0)

    print(f"Found {len(results)} result(s) for {query_str!r}:\n")
    for i, entry in enumerate(results, 1):
        folder = " / ".join(entry.folder_path) if entry.folder_path else "(root)"
        print(f"  {i:>4}.  {entry.title}")
        print(f"         {entry.url}")
        print(f"         Source: {entry.source_label}  |  Folder: {folder}")
        print(f"         Added:  {get_human_date(entry.add_date)}")
        print()
