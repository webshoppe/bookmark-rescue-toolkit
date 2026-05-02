"""
retriever.py - Bookmark Rescue Toolkit
========================================
Scans a Windows.old directory tree and copies bookmark-related artifacts
from 30+ browsers into a normalised, structured output folder.

Artifact types collected
------------------------
  Chromium-family  Bookmarks (JSON) and Bookmarks.bak
  Gecko-family     places.sqlite, places.sqlite-wal, favicons.sqlite,
                   and the bookmarkbackups/ folder
  Packaged apps    Arc (MSIX), DuckDuckGo (WebView2)
  Portable         Tor Browser, Mullvad Browser

Output layout
-------------
  output_dir/
      manifest.json              ← structured index consumed by vault_builder
      <username>/
          <browser>/
              <profile>/
                  <files …>

Standalone usage
----------------
  python -m core.retriever "C:\\Windows.old" "C:\\Bookmark_Rescue\\Raw"
  python -m core.retriever D:\\ output_folder --verbose
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _safe_copy(
    src: Path,
    dest: Path,
    result: dict,
    artifact_type: str,
    username: str,
    browser: str,
    profile: str,
) -> None:
    """Copy *src* → *dest* and record the outcome in *result*.

    Permission errors and OS errors are captured as warnings rather than
    crashing the scan, which is important because Windows.old folders
    routinely have NTFS ACL restrictions on old user profile data.
    """
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
    except PermissionError as exc:
        result["warnings"].append(f"Permission denied copying {src}: {exc}")
        return
    except OSError as exc:
        result["warnings"].append(f"OS error copying {src}: {exc}")
        return

    result["copied_files"] += 1
    result["artifacts"].append({
        "username":      username,
        "browser":       browser,
        "profile":       profile,
        "artifact_type": artifact_type,
        "source_path":   str(src),
        "copied_path":   str(dest),
        "status":        "copied",
    })


def _iter_gecko_profiles(path_obj: Path):
    """Yield Gecko/Firefox profile directories from *path_obj*.

    Handles two layouts:
      • A direct profile folder (contains places.sqlite at the top level).
        Used by Tor's profile.default, for example.
      • A Profiles/ parent folder containing multiple sub-profiles.
        Used by all standard Firefox-family installs.
    """
    if not path_obj.exists():
        return

    if (path_obj / "places.sqlite").exists():
        yield path_obj
        return

    try:
        children = list(path_obj.iterdir())
    except PermissionError:
        return

    for child in children:
        if child.is_dir() and (child / "places.sqlite").exists():
            yield child


def _copy_gecko_profile(
    profile_dir: Path,
    dest_folder: Path,
    result: dict,
    username: str,
    browser_name: str,
    profile_name: str,
) -> None:
    """Copy all recoverable artifacts from one Gecko profile directory."""
    for filename, artifact_type in (
        ("places.sqlite",     "gecko_places_sqlite"),
        ("places.sqlite-wal", "gecko_places_sqlite_wal"),
        ("favicons.sqlite",   "gecko_favicons_sqlite"),
    ):
        src = profile_dir / filename
        if src.exists():
            _safe_copy(src, dest_folder / filename,
                       result, artifact_type, username, browser_name, profile_name)

    backup_dir = profile_dir / "bookmarkbackups"
    if backup_dir.is_dir():
        try:
            for backup_file in backup_dir.iterdir():
                if backup_file.is_file():
                    _safe_copy(
                        backup_file,
                        dest_folder / "bookmarkbackups" / backup_file.name,
                        result, "gecko_bookmark_backup",
                        username, browser_name, profile_name,
                    )
        except PermissionError as exc:
            result["warnings"].append(
                f"Permission denied reading bookmarkbackups in {profile_dir}: {exc}"
            )


def _scan_chromium_user_data(
    user_data_dir: Path,
    dest_root: Path,
    result: dict,
    username: str,
    browser_name: str,
) -> None:
    """Scan a Chromium 'User Data' directory for Default / Profile N folders."""
    try:
        entries = list(user_data_dir.iterdir())
    except PermissionError as exc:
        result["warnings"].append(
            f"Permission denied scanning {user_data_dir}: {exc}"
        )
        return

    for profile_dir in entries:
        if not profile_dir.is_dir():
            continue
        if not ("Default" in profile_dir.name or "Profile" in profile_dir.name):
            continue

        dest = dest_root / profile_dir.name

        bookmarks = profile_dir / "Bookmarks"
        if bookmarks.exists():
            _safe_copy(
                bookmarks,
                dest / f"{browser_name}_Bookmarks.json",
                result, "chromium_bookmarks_json",
                username, browser_name, profile_dir.name,
            )

        backup = profile_dir / "Bookmarks.bak"
        if backup.exists():
            _safe_copy(
                backup,
                dest / f"{browser_name}_Bookmarks.bak",
                result, "chromium_bookmarks_backup",
                username, browser_name, profile_dir.name,
            )


# ---------------------------------------------------------------------------
# Browser path registries
# ---------------------------------------------------------------------------
# All paths use forward slashes - pathlib handles the separator on every OS,
# and single-backslash raw strings inside Windows path strings are tricky.

_CHROMIUM_PATHS: dict[str, str] = {
    "Google Chrome":      "AppData/Local/Google/Chrome/User Data",
    "Chrome Beta":        "AppData/Local/Google/Chrome Beta/User Data",
    "Chrome Dev":         "AppData/Local/Google/Chrome Dev/User Data",
    "Chrome Canary":      "AppData/Local/Google/Chrome SxS/User Data",
    "Microsoft Edge":     "AppData/Local/Microsoft/Edge/User Data",
    "Edge Beta":          "AppData/Local/Microsoft/Edge Beta/User Data",
    "Edge Dev":           "AppData/Local/Microsoft/Edge Dev/User Data",
    "Edge Canary":        "AppData/Local/Microsoft/Edge SxS/User Data",
    "Brave":              "AppData/Local/BraveSoftware/Brave-Browser/User Data",
    "Brave Beta":         "AppData/Local/BraveSoftware/Brave-Browser-Beta/User Data",
    "Brave Nightly":      "AppData/Local/BraveSoftware/Brave-Browser-Nightly/User Data",
    "Vivaldi":            "AppData/Local/Vivaldi/User Data",
    "Ungoogled Chromium": "AppData/Local/Chromium/User Data",
    "Comet":              "AppData/Local/Perplexity/Comet/User Data",
}

# Opera stores its data one level higher than standard Chromium builds.
# The root of the path itself may contain a Bookmarks file, *and* sub-profiles
# may also exist - so both locations are checked.
_OPERA_PATHS: dict[str, str] = {
    "Opera":           "AppData/Roaming/Opera Software/Opera Stable",
    "Opera GX":        "AppData/Roaming/Opera Software/Opera GX Stable",
    "Opera Beta":      "AppData/Roaming/Opera Software/Opera Beta",
    "Opera Developer": "AppData/Roaming/Opera Software/Opera Developer",
}

_GECKO_PATHS: dict[str, str] = {
    "Firefox":         "AppData/Roaming/Mozilla/Firefox/Profiles",
    "Waterfox":        "AppData/Roaming/Waterfox/Profiles",
    "LibreWolf":       "AppData/Roaming/librewolf/Profiles",
    "Pale Moon":       "AppData/Roaming/Moonchild Productions/Pale Moon/Profiles",
    "SeaMonkey":       "AppData/Roaming/Mozilla/SeaMonkey/Profiles",
    # Mullvad may install to either Roaming or Local depending on version
    "Mullvad":         "AppData/Roaming/Mullvad/MullvadBrowser/Profiles",
    "Mullvad (Local)": "AppData/Local/Mullvad/MullvadBrowser/Profiles",
    # Both Zen registry keys are intentionally mapped to display name "Zen"
    # so their profiles merge under one output folder rather than splitting.
    "Zen":             "AppData/Roaming/zen/Profiles",
    "Zen (Alt)":       "AppData/Roaming/ZenBrowser/Profiles",
    "Tor":             "AppData/Local/TorBrowser/Data/Browser/profile.default",
}

_SKIP_USERNAMES = {"public", "default", "default user"}
_PORTABLE_NAMES = ["Tor Browser", "Mullvad Browser"]

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def recover_bookmarks(windows_old_path: str, output_dir: str) -> dict:
    """Scan *windows_old_path* and copy bookmark artifacts to *output_dir*.

    Parameters
    ----------
    windows_old_path:
        Root of the Windows.old folder, or any drive root (e.g. ``D:\\``).
    output_dir:
        Destination folder.  Created if it does not exist.

    Returns
    -------
    dict with keys:
        status, source_root, output_root, copied_files, users_scanned,
        artifacts, warnings
    Raises FileNotFoundError if the Users subdirectory cannot be found.
    """
    win_old   = Path(windows_old_path)
    users_dir = win_old / "Users"
    out_dir   = Path(output_dir)

    if not users_dir.exists():
        raise FileNotFoundError(
            f"Could not find a Users directory at {users_dir}. "
            "Make sure the path points to the root of a Windows installation "
            "(e.g. C:\\Windows.old or D:\\)."
        )

    out_dir.mkdir(parents=True, exist_ok=True)

    result: dict = {
        "status":        "ok",
        "source_root":   str(win_old),
        "output_root":   str(out_dir),
        "copied_files":  0,
        "users_scanned": 0,
        "artifacts":     [],
        "warnings":      [],
    }

    # Collect top-level user folders - guard against permission errors on
    # locked system directories that live alongside real user folders.
    try:
        user_folders = [f for f in users_dir.iterdir() if f.is_dir()]
    except PermissionError as exc:
        raise PermissionError(f"Cannot read the Users directory: {exc}") from exc

    for user_folder in user_folders:
        if user_folder.name.lower() in _SKIP_USERNAMES:
            continue

        result["users_scanned"] += 1
        username = user_folder.name

        # ── Standard Chromium-family ──────────────────────────────────
        for browser_name, rel_path in _CHROMIUM_PATHS.items():
            user_data_dir = user_folder / rel_path
            if user_data_dir.exists():
                _scan_chromium_user_data(
                    user_data_dir,
                    out_dir / username / browser_name,
                    result, username, browser_name,
                )

        # ── Opera-family ──────────────────────────────────────────────
        for browser_name, rel_path in _OPERA_PATHS.items():
            opera_dir = user_folder / rel_path
            if not opera_dir.exists():
                continue
            # Root-level Bookmarks (single-profile Opera layout)
            root_bm = opera_dir / "Bookmarks"
            if root_bm.exists():
                _safe_copy(
                    root_bm,
                    out_dir / username / browser_name / "Default" / f"{browser_name}_Bookmarks.json",
                    result, "chromium_bookmarks_json",
                    username, browser_name, "Default",
                )
            # Sub-profiles (multi-profile Opera layout)
            _scan_chromium_user_data(
                opera_dir,
                out_dir / username / browser_name,
                result, username, browser_name,
            )

        # ── Gecko-family ──────────────────────────────────────────────
        for browser_name, rel_path in _GECKO_PATHS.items():
            profiles_root = user_folder / rel_path
            # Merge "Zen" and "Zen (Alt)" into one output directory so that
            # duplicate profiles from different registry paths don't split.
            display_name = "Zen" if "Zen" in browser_name else browser_name
            for profile_dir in _iter_gecko_profiles(profiles_root):
                dest_folder = out_dir / username / display_name / profile_dir.name
                _copy_gecko_profile(
                    profile_dir, dest_folder, result,
                    username, display_name, profile_dir.name,
                )

        # ── Packaged / MSIX apps ──────────────────────────────────────
        packages_dir = user_folder / "AppData/Local/Packages"
        if packages_dir.exists():
            try:
                packages = list(packages_dir.iterdir())
            except PermissionError as exc:
                result["warnings"].append(
                    f"Permission denied reading Packages for {username}: {exc}"
                )
                packages = []

            for package in packages:
                if package.name.startswith("TheBrowserCompany.Arc_"):
                    arc_data = package / "LocalCache/Local/Arc/User Data"
                    if arc_data.exists():
                        _scan_chromium_user_data(
                            arc_data, out_dir / username / "Arc",
                            result, username, "Arc",
                        )

                elif package.name.startswith("DuckDuckGo.DesktopBrowser_"):
                    ddg_data = package / "LocalState/EBWebView"
                    if ddg_data.exists():
                        _scan_chromium_user_data(
                            ddg_data, out_dir / username / "DuckDuckGo",
                            result, username, "DuckDuckGo",
                        )

        # ── Portable installs ─────────────────────────────────────────
        for search_root in (user_folder, user_folder / "Desktop"):
            if not search_root.exists():
                continue
            for p_name in _PORTABLE_NAMES:
                portable_dir = search_root / p_name
                if not portable_dir.exists():
                    continue
                try:
                    for places_db in portable_dir.rglob("places.sqlite"):
                        # Tag the destination with both the search root name and
                        # the profile sub-folder so collisions are impossible.
                        location_tag = f"{search_root.name}_{places_db.parent.name}"
                        dest_folder  = out_dir / username / p_name / location_tag
                        _copy_gecko_profile(
                            places_db.parent, dest_folder, result,
                            username, p_name, location_tag,
                        )
                except PermissionError as exc:
                    result["warnings"].append(
                        f"Permission denied scanning portable {p_name}: {exc}"
                    )

    # Write manifest so vault_builder can consume structured artifact data
    # rather than guessing from filenames alone.
    manifest_path = out_dir / "manifest.json"
    try:
        with open(manifest_path, "w", encoding="utf-8") as fh:
            json.dump(result, fh, indent=2)
    except OSError as exc:
        result["warnings"].append(f"Could not write manifest.json: {exc}")

    return result


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        prog="python -m core.retriever",
        description="Scan a Windows.old directory and extract browser bookmark artifacts.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  python -m core.retriever "C:\\Windows.old" "C:\\Bookmark_Rescue\\Raw"
  python -m core.retriever D:\\ output_folder
  python -m core.retriever D:\\ output_folder --verbose
        """,
    )
    parser.add_argument("source",
                        help="Path to the Windows.old root, or any drive root (e.g. D:\\)")
    parser.add_argument("output",
                        help="Directory where extracted files will be saved")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Print each copied file as it is processed")
    args = parser.parse_args()

    print(f"Scanning : {args.source}")
    print(f"Output   : {args.output}")
    print()

    try:
        res = recover_bookmarks(args.source, args.output)
    except (FileNotFoundError, PermissionError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.verbose:
        for artifact in res["artifacts"]:
            print(f"  [+] {artifact['browser']:20s} {artifact['artifact_type']:30s} "
                  f"→ {artifact['copied_path']}")

    print(f"\nScan complete.")
    print(f"  Users scanned : {res['users_scanned']}")
    print(f"  Files copied  : {res['copied_files']}")
    if res["warnings"]:
        print(f"\nWarnings ({len(res['warnings'])}):")
        for w in res["warnings"]:
            print(f"  [!] {w}")
    print(f"\nManifest  : {Path(args.output) / 'manifest.json'}")
