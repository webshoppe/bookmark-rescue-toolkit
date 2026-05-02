"""
vault_builder.py - Bookmark Rescue Toolkit
===========================================
Reads the output of the Retriever (preferring manifest.json when present,
otherwise walking the directory tree directly) and converts every bookmark
artifact into HTML, then generates a polished index.html dashboard.

Standalone usage
----------------
  python -m core.vault_builder "C:\\Bookmark_Rescue\\Raw" "C:\\Bookmark_Rescue\\Site"
"""

from __future__ import annotations

import json
import os
import sys
from html import escape
from pathlib import Path
from urllib.parse import quote

from .json_to_html   import convert_json_to_html
from .sqlite_to_html import convert_sqlite_to_html


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _convert_one(
    artifact_type: str,
    source_path: Path,
    out_html: Path,
    display_label: str,
) -> dict:
    """Dispatch to the appropriate converter and return its stats dict."""
    if artifact_type == "chromium_bookmarks_json":
        return convert_json_to_html(str(source_path), str(out_html),
                                    browser_label=display_label)
    elif artifact_type == "gecko_places_sqlite":
        return convert_sqlite_to_html(str(source_path), str(out_html),
                                      browser_label=display_label)
    else:
        raise ValueError(f"Unknown artifact type: {artifact_type!r}")


def _infer_artifact_type(filename: str) -> str | None:
    """Guess artifact type from filename (used in manifest-less fallback mode).

    Explicitly excludes .bak files - they are valid backup sources but would
    otherwise produce a redundant second HTML page alongside the primary one.
    """
    if filename == "places.sqlite":
        return "gecko_places_sqlite"
    if not filename.endswith(".bak") and (filename.endswith(".json") or "Bookmarks" in filename):
        return "chromium_bookmarks_json"
    return None


# ---------------------------------------------------------------------------
# Index page generator
# ---------------------------------------------------------------------------

def generate_index_page(site_dir: Path, site_map: dict) -> None:
    """Build the master index.html dashboard for the offline vault.

    site_map structure
    ------------------
    {
      username: {
        browser: [ (profile_name, rel_link, bookmark_count, folder_count), … ]
      }
    }

    Every user-supplied string (username, browser, profile) is passed through
    html.escape() before being written into the HTML document.
    """
    css = (
        "        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;\n"
        "               background-color: #121212; color: #e0e0e0;\n"
        "               margin: 0; padding: 40px; }\n"
        "        h1   { text-align: center; color: #ffffff; margin-bottom: 40px;\n"
        "               border-bottom: 2px solid #333; padding-bottom: 20px; }\n"
        "        .user-container { background-color: #1e1e1e; border-radius: 8px;\n"
        "                          padding: 25px; margin-bottom: 30px;\n"
        "                          box-shadow: 0 4px 6px rgba(0,0,0,0.3); }\n"
        "        .user-title  { color: #4dabf7; margin-top: 0;\n"
        "                       border-bottom: 1px solid #333; padding-bottom: 10px; }\n"
        "        .browser-section { margin-top: 20px; }\n"
        "        .browser-title   { color: #aaaaaa; font-size: 1.1em; margin-bottom: 10px; }\n"
        "        ul   { list-style-type: none; padding-left: 0;\n"
        "               display: flex; flex-wrap: wrap; gap: 15px; }\n"
        "        li   { background-color: #2c2c2c; border-radius: 6px;\n"
        "               transition: transform 0.2s; }\n"
        "        li:hover { transform: translateY(-2px); background-color: #383838; }\n"
        "        a    { display: block; padding: 12px 20px; color: #ffffff;\n"
        "               text-decoration: none; font-weight: bold; }\n"
        "        .meta{ display: block; font-size: 0.85em; color: #b0b0b0;\n"
        "               padding: 0 20px 12px; }"
    )

    lines = [
        "<!DOCTYPE html>",
        "<html lang='en'>",
        "<head>",
        '    <meta charset="UTF-8">',
        '    <meta name="viewport" content="width=device-width, initial-scale=1.0">',
        "    <title>Offline Bookmark Vault</title>",
        "    <style>",
        css,
        "    </style>",
        "</head>",
        "<body>",
        "    <h1>&#128214; Offline Bookmark Vault</h1>",
    ]

    if not site_map:
        lines.append(
            "    <p style='text-align:center; color:#888;'>"
            "No recovered bookmarks found to display.</p>"
        )

    for username, browsers in sorted(site_map.items()):
        safe_user = escape(username)
        lines += [
            "    <div class='user-container'>",
            f"        <h2 class='user-title'>&#128100; User: {safe_user}</h2>",
        ]
        for browser_name, profiles in sorted(browsers.items()):
            safe_browser = escape(browser_name)
            lines += [
                "        <div class='browser-section'>",
                f"            <div class='browser-title'>&#128193; {safe_browser}</div>",
                "            <ul>",
            ]
            for profile_name, link, bm_count, folder_count in sorted(profiles):
                safe_profile = escape(profile_name)
                safe_link    = quote(link, safe="/")
                lines += [
                    "                <li>",
                    f"                    <a href='{safe_link}' target='_blank'>{safe_profile}</a>",
                    f"                    <span class='meta'>"
                    f"{bm_count} bookmarks &middot; {folder_count} folders</span>",
                    "                </li>",
                ]
            lines += ["            </ul>", "        </div>"]
        lines.append("    </div>")

    lines += ["</body>", "</html>"]

    with open(site_dir / "index.html", "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_vault(raw_dir_path: str, site_dir_path: str) -> dict:
    """Convert all bookmark artifacts under *raw_dir_path* and write an HTML vault.

    When a ``manifest.json`` written by the Retriever is found, it drives
    conversion with full metadata (artifact type, username, browser, profile).
    Otherwise, the directory tree is walked and artifact types are inferred
    from filenames - this fallback handles folders created manually or by
    earlier versions of the toolkit.

    Parameters
    ----------
    raw_dir_path:
        Folder produced by the Retriever (should contain ``manifest.json``).
    site_dir_path:
        Destination for the HTML vault.  Created if it does not exist.

    Returns
    -------
    dict with keys:
        status, converted, warnings, entries, used_manifest

    Raises
    ------
    FileNotFoundError
        If *raw_dir_path* does not exist.
    """
    raw_dir  = Path(raw_dir_path)
    site_dir = Path(site_dir_path)

    if not raw_dir.exists():
        raise FileNotFoundError(f"Raw directory not found: {raw_dir}")

    site_dir.mkdir(parents=True, exist_ok=True)

    result: dict = {
        "status":        "ok",
        "raw_dir":       str(raw_dir),
        "site_dir":      str(site_dir),
        "converted":     0,
        "warnings":      [],
        "entries":       [],
        "used_manifest": False,
    }
    # site_map: { username: { browser: [(profile, rel_link, bm_count, folder_count)] } }
    site_map: dict = {}

    def _register(username, browser, profile, out_html, rel_link, stats):
        site_map.setdefault(username, {}).setdefault(browser, []).append(
            (profile, rel_link, stats.get("bookmarks", 0), stats.get("folders", 0))
        )
        result["converted"] += 1
        result["entries"].append({
            "username":  username,
            "browser":   browser,
            "profile":   profile,
            "html":      str(out_html),
            "bookmarks": stats.get("bookmarks", 0),
            "folders":   stats.get("folders", 0),
            "warnings":  stats.get("warnings", []),
        })

    # ------------------------------------------------------------------
    # Preferred path: manifest-driven conversion
    # ------------------------------------------------------------------
    manifest_path = raw_dir / "manifest.json"
    if manifest_path.exists():
        result["used_manifest"] = True
        with open(manifest_path, "r", encoding="utf-8") as fh:
            manifest = json.load(fh)

        # Guard against duplicate username/browser/profile/type combos that
        # could arise from retried runs or manifest corruption.
        seen: set = set()

        for artifact in manifest.get("artifacts", []):
            if artifact.get("status") != "copied":
                continue
            artifact_type = artifact.get("artifact_type")
            if artifact_type not in {"chromium_bookmarks_json", "gecko_places_sqlite"}:
                continue  # skip backups, WAL files, favicons, etc.

            copied_path = Path(artifact.get("copied_path", ""))
            if not copied_path.exists():
                result["warnings"].append(f"Missing artifact file: {copied_path}")
                continue

            username = artifact.get("username", "UnknownUser")
            browser  = artifact.get("browser",  "UnknownBrowser")
            profile  = artifact.get("profile",  "UnknownProfile")

            dedup_key = (username, browser, profile, artifact_type)
            if dedup_key in seen:
                result["warnings"].append(
                    f"Duplicate artifact skipped: {username}/{browser}/{profile}"
                )
                continue
            seen.add(dedup_key)

            out_folder    = site_dir / username / browser / profile
            out_folder.mkdir(parents=True, exist_ok=True)
            out_html      = out_folder / "bookmarks.html"
            rel_link      = f"{username}/{browser}/{profile}/bookmarks.html"
            display_label = f"{browser} ({profile})"

            try:
                stats = _convert_one(artifact_type, copied_path, out_html, display_label)
                _register(username, browser, profile, out_html, rel_link, stats)
            except Exception as exc:
                result["warnings"].append(f"Failed to convert {copied_path}: {exc}")

    # ------------------------------------------------------------------
    # Fallback: walk the directory tree without a manifest
    # ------------------------------------------------------------------
    else:
        for root, _dirs, files in os.walk(raw_dir):
            for filename in files:
                artifact_type = _infer_artifact_type(filename)
                if artifact_type is None:
                    continue

                file_path = Path(root) / filename
                try:
                    rel_path = file_path.relative_to(raw_dir)
                except ValueError:
                    continue

                parts = rel_path.parts
                if len(parts) < 3:
                    continue  # too shallow to have username/browser/profile

                username, browser, profile = parts[0], parts[1], parts[2]
                out_folder    = site_dir / username / browser / profile
                out_folder.mkdir(parents=True, exist_ok=True)
                out_html      = out_folder / "bookmarks.html"
                rel_link      = f"{username}/{browser}/{profile}/bookmarks.html"
                display_label = f"{browser} ({profile})"

                try:
                    stats = _convert_one(artifact_type, file_path, out_html, display_label)
                    _register(username, browser, profile, out_html, rel_link, stats)
                except Exception as exc:
                    result["warnings"].append(f"Failed to convert {file_path}: {exc}")

    generate_index_page(site_dir, site_map)
    return result


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        prog="python -m core.vault_builder",
        description="Convert extracted bookmark artifacts into a static offline HTML vault.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  python -m core.vault_builder "C:\\Bookmark_Rescue\\Raw" "C:\\Bookmark_Rescue\\Site"
  python -m core.vault_builder ./raw_output ./vault_site
        """,
    )
    parser.add_argument("source",
                        help="Folder produced by the Retriever (contains manifest.json)")
    parser.add_argument("output",
                        help="Empty folder where the HTML vault will be written")
    args = parser.parse_args()

    print(f"Raw data : {args.source}")
    print(f"Site out : {args.output}")
    print()

    try:
        res = build_vault(args.source, args.output)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    mode = "manifest" if res["used_manifest"] else "directory walk (no manifest found)"
    print(f"Mode      : {mode}")
    print(f"Converted : {res['converted']} page(s)")
    if res["warnings"]:
        print(f"\nWarnings ({len(res['warnings'])}):")
        for w in res["warnings"]:
            print(f"  [!] {w}")
    print(f"\nVault ready: {Path(args.output) / 'index.html'}")
