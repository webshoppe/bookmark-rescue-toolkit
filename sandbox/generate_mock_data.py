"""
generate_mock_data.py
=====================
Creates a realistic mock Windows.old folder structure for screenshot
and demonstration purposes.

Users created:    Alex  (tech-focused bookmarks)
                  Jordan (general / lifestyle bookmarks)

Browsers per user:
  Alex   - Chrome (Default), Edge (Default), Firefox, Brave (Default)
  Jordan - Chrome (Default), Brave (Default), Firefox, Opera

Run from inside C:\\Bookmark_Rescue\\Sandbox\\ or any directory.
Output path is always C:\\Bookmark_Rescue\\Mock_Windows_Old\\
"""

import json
import os
import sqlite3
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
WORKSPACE   = Path(r"C:\Bookmark_Rescue")
OUTPUT_ROOT = WORKSPACE / "Windows.old" / "Users"

# ---------------------------------------------------------------------------
# Timestamp helpers
# ---------------------------------------------------------------------------
# WebKit epoch: microseconds since 1601-01-01
# To convert a Unix timestamp: unix_ts * 1_000_000 + 11_644_473_600_000_000

def _webkit(year: int, month: int, day: int) -> str:
    """Return a Chromium-style WebKit timestamp string for the given date."""
    import datetime
    dt = datetime.datetime(year, month, day, 12, 0, 0)
    unix_ts = int(dt.timestamp())
    webkit   = unix_ts * 1_000_000 + 11_644_473_600_000_000
    return str(webkit)


def _prtime(year: int, month: int, day: int) -> int:
    """Return a Firefox PRTime integer (microseconds since Unix epoch)."""
    import datetime
    dt = datetime.datetime(year, month, day, 12, 0, 0)
    return int(dt.timestamp()) * 1_000_000


# ---------------------------------------------------------------------------
# Chromium bookmark data
# ---------------------------------------------------------------------------

def _url_node(name: str, url: str, year: int, month: int, day: int) -> dict:
    return {
        "date_added": _webkit(year, month, day),
        "id":         "0",   # id collisions are fine in mock data
        "name":       name,
        "type":       "url",
        "url":        url,
    }


def _folder_node(name: str, children: list,
                 year: int = 2021, month: int = 1, day: int = 1) -> dict:
    return {
        "children":      children,
        "date_added":    _webkit(year, month, day),
        "date_modified": _webkit(year, month, day),
        "id":            "0",
        "name":          name,
        "type":          "folder",
    }


# ── Alex: tech-focused ────────────────────────────────────────────────────

ALEX_CHROME_BAR = _folder_node("Bookmarks bar", [
    _url_node("GitHub",         "https://github.com",              2020, 3, 15),
    _url_node("Stack Overflow", "https://stackoverflow.com",       2020, 4,  2),
    _url_node("MDN Web Docs",   "https://developer.mozilla.org",   2020, 5, 10),
    _url_node("Gmail",          "https://mail.google.com",         2019, 8, 22),
    _url_node("Google Drive",   "https://drive.google.com",        2019, 8, 22),
    _folder_node("Dev Tools", [
        _url_node("Chrome DevTools Docs",   "https://developer.chrome.com/docs/devtools/", 2021, 1, 5),
        _url_node("Postman",                "https://www.postman.com",                     2021, 2, 14),
        _url_node("JSON Formatter",         "https://jsonformatter.curiousconcept.com",    2021, 3, 8),
        _url_node("Regex101",               "https://regex101.com",                        2021, 4, 19),
        _url_node("Can I Use",              "https://caniuse.com",                         2021, 5, 27),
    ], 2021, 1, 5),
    _folder_node("Learning", [
        _url_node("freeCodeCamp",   "https://www.freecodecamp.org",  2020, 6, 3),
        _url_node("The Odin Project","https://www.theodinproject.com",2020, 7, 14),
        _url_node("CSS-Tricks",     "https://css-tricks.com",        2020, 8, 29),
        _url_node("Real Python",    "https://realpython.com",        2020, 9, 11),
        _url_node("Coursera",       "https://www.coursera.org",      2020, 10, 5),
    ], 2020, 6, 3),
], 2019, 8, 1)

ALEX_CHROME_OTHER = _folder_node("Other bookmarks", [
    _url_node("Reddit",          "https://www.reddit.com",         2019, 9, 4),
    _url_node("YouTube",         "https://www.youtube.com",        2019, 9, 4),
    _url_node("Hacker News",     "https://news.ycombinator.com",   2020, 1, 15),
    _url_node("Python Docs",     "https://docs.python.org/3/",     2020, 2, 28),
    _url_node("PyPI",            "https://pypi.org",               2020, 3, 7),
    _url_node("VS Code Docs",    "https://code.visualstudio.com/docs", 2020, 4, 2),
    _url_node("Docker Hub",      "https://hub.docker.com",         2021, 6, 18),
    _url_node("Netlify",         "https://www.netlify.com",        2021, 7, 22),
    _url_node("Cloudflare",      "https://www.cloudflare.com",     2021, 8, 9),
    _url_node("DigitalOcean",    "https://www.digitalocean.com",   2021, 9, 3),
], 2019, 9, 1)

# Alex's Edge has partial overlap (shared bookmarks) plus work-specific ones
ALEX_EDGE_BAR = _folder_node("Favorites bar", [
    _url_node("GitHub",          "https://github.com",             2021, 1, 3),
    _url_node("Outlook",         "https://outlook.office365.com",  2021, 1, 3),
    _url_node("Teams",           "https://teams.microsoft.com",    2021, 1, 3),
    _url_node("Azure Portal",    "https://portal.azure.com",       2021, 2, 11),
    _folder_node("Work", [
        _url_node("SharePoint",  "https://sharepoint.com",         2021, 3, 15),
        _url_node("Confluence",  "https://www.atlassian.com/software/confluence", 2021, 3, 15),
        _url_node("Jira",        "https://www.atlassian.com/software/jira",       2021, 4, 7),
        _url_node("Figma",       "https://www.figma.com",          2021, 5, 22),
    ], 2021, 3, 15),
    _folder_node("Reference", [
        _url_node("MDN Web Docs","https://developer.mozilla.org",  2021, 1, 8),
        _url_node("W3Schools",   "https://www.w3schools.com",      2021, 1, 8),
        _url_node("Stack Overflow","https://stackoverflow.com",    2021, 1, 8),
    ], 2021, 1, 8),
], 2021, 1, 3)

# Alex's Brave is privacy/security focused
ALEX_BRAVE_BAR = _folder_node("Bookmarks bar", [
    _url_node("ProtonMail",        "https://proton.me/mail",         2022, 3, 10),
    _url_node("Bitwarden",         "https://vault.bitwarden.com",    2022, 3, 10),
    _url_node("Mullvad VPN",       "https://mullvad.net",            2022, 4, 5),
    _url_node("DuckDuckGo",        "https://duckduckgo.com",         2022, 4, 5),
    _folder_node("Privacy Tools", [
        _url_node("Privacy Guides",    "https://www.privacyguides.org",     2022, 5, 12),
        _url_node("EFF",               "https://www.eff.org",               2022, 5, 12),
        _url_node("Have I Been Pwned", "https://haveibeenpwned.com",        2022, 6, 3),
        _url_node("Shodan",            "https://www.shodan.io",             2022, 7, 19),
    ], 2022, 5, 12),
    _folder_node("Open Source", [
        _url_node("GitHub",        "https://github.com",             2022, 3, 15),
        _url_node("GitLab",        "https://gitlab.com",             2022, 3, 15),
        _url_node("Codeberg",      "https://codeberg.org",           2022, 8, 4),
        _url_node("SourceHut",     "https://sourcehut.org",          2022, 9, 11),
    ], 2022, 3, 15),
], 2022, 3, 10)

# ── Jordan: general/lifestyle focused ─────────────────────────────────────

JORDAN_CHROME_BAR = _folder_node("Bookmarks bar", [
    _url_node("Gmail",           "https://mail.google.com",         2019, 5, 8),
    _url_node("Amazon",          "https://www.amazon.com",          2019, 5, 8),
    _url_node("YouTube",         "https://www.youtube.com",         2019, 5, 8),
    _url_node("Weather",         "https://weather.com",             2019, 6, 12),
    _folder_node("Shopping", [
        _url_node("Amazon",      "https://www.amazon.com",          2019, 7, 3),
        _url_node("eBay",        "https://www.ebay.com",            2019, 7, 3),
        _url_node("Etsy",        "https://www.etsy.com",            2019, 8, 14),
        _url_node("Best Buy",    "https://www.bestbuy.com",         2019, 9, 22),
        _url_node("Newegg",      "https://www.newegg.com",          2020, 1, 7),
        _url_node("B&H Photo",   "https://www.bhphotovideo.com",    2020, 2, 18),
    ], 2019, 7, 3),
    _folder_node("News", [
        _url_node("BBC",         "https://www.bbc.com",             2019, 10, 5),
        _url_node("Reuters",     "https://www.reuters.com",         2019, 10, 5),
        _url_node("AP News",     "https://apnews.com",              2019, 11, 12),
        _url_node("NPR",         "https://www.npr.org",             2020, 1, 22),
        _url_node("The Guardian","https://www.theguardian.com",     2020, 3, 8),
    ], 2019, 10, 5),
    _folder_node("Reading", [
        _url_node("Goodreads",      "https://www.goodreads.com",    2020, 4, 14),
        _url_node("Project Gutenberg","https://www.gutenberg.org",  2020, 5, 3),
        _url_node("Library Genesis","https://libgen.is",            2020, 6, 27),
        _url_node("Audible",        "https://www.audible.com",      2020, 7, 15),
    ], 2020, 4, 14),
], 2019, 5, 1)

JORDAN_CHROME_OTHER = _folder_node("Other bookmarks", [
    _url_node("Netflix",          "https://www.netflix.com",        2019, 6, 2),
    _url_node("Spotify",          "https://open.spotify.com",       2019, 6, 2),
    _url_node("Pinterest",        "https://www.pinterest.com",      2019, 7, 8),
    _url_node("Instagram",        "https://www.instagram.com",      2019, 8, 15),
    _url_node("Reddit",           "https://www.reddit.com",         2019, 9, 4),
    _url_node("Hulu",             "https://www.hulu.com",           2020, 2, 11),
    _url_node("Disney+",          "https://www.disneyplus.com",     2020, 11, 12),
    _url_node("Duolingo",         "https://www.duolingo.com",       2021, 1, 5),
    _url_node("AllRecipes",       "https://www.allrecipes.com",     2021, 3, 19),
    _url_node("Tasty",            "https://tasty.co",               2021, 4, 7),
    _url_node("Zillow",           "https://www.zillow.com",         2022, 8, 3),
    _url_node("Airbnb",           "https://www.airbnb.com",         2022, 9, 14),
], 2019, 6, 1)

JORDAN_BRAVE_BAR = _folder_node("Bookmarks bar", [
    _url_node("Gmail",            "https://mail.google.com",        2021, 4, 5),
    _url_node("Amazon",           "https://www.amazon.com",         2021, 4, 5),
    _url_node("YouTube",          "https://www.youtube.com",        2021, 4, 5),
    _folder_node("Finance", [
        _url_node("Mint",         "https://mint.intuit.com",        2021, 5, 20),
        _url_node("Credit Karma", "https://www.creditkarma.com",    2021, 5, 20),
        _url_node("Robinhood",    "https://robinhood.com",          2021, 6, 14),
        _url_node("NerdWallet",   "https://www.nerdwallet.com",     2021, 7, 8),
    ], 2021, 5, 20),
    _folder_node("Health", [
        _url_node("MyFitnessPal", "https://www.myfitnesspal.com",   2021, 8, 3),
        _url_node("Headspace",    "https://www.headspace.com",      2021, 9, 17),
        _url_node("WebMD",        "https://www.webmd.com",          2021, 10, 2),
    ], 2021, 8, 3),
], 2021, 4, 5)

JORDAN_OPERA_BOOKMARKS = _folder_node("Bookmarks bar", [
    _url_node("Twitch",           "https://www.twitch.tv",          2022, 1, 8),
    _url_node("SoundCloud",       "https://soundcloud.com",         2022, 1, 8),
    _url_node("Bandcamp",         "https://bandcamp.com",           2022, 2, 14),
    _url_node("Last.fm",          "https://www.last.fm",            2022, 3, 5),
    _folder_node("Gaming", [
        _url_node("Steam",        "https://store.steampowered.com", 2022, 4, 12),
        _url_node("GOG",          "https://www.gog.com",            2022, 4, 12),
        _url_node("Itch.io",      "https://itch.io",                2022, 5, 3),
        _url_node("HowLongToBeat","https://howlongtobeat.com",      2022, 6, 19),
        _url_node("IGN",          "https://www.ign.com",            2022, 7, 8),
    ], 2022, 4, 12),
], 2022, 1, 8)


def _make_chromium_bookmarks(bar_node: dict, other_node: dict) -> dict:
    return {
        "checksum": "mockchecksum00000000000000000000",
        "roots": {
            "bookmark_bar": bar_node,
            "other":        other_node,
            "synced": {
                "children":      [],
                "date_added":    _webkit(2019, 1, 1),
                "date_modified": _webkit(2019, 1, 1),
                "id":            "0",
                "name":          "Mobile bookmarks",
                "type":          "folder",
            },
        },
        "version": 1,
    }


# ---------------------------------------------------------------------------
# Firefox SQLite helpers
# ---------------------------------------------------------------------------

def _create_firefox_db(db_path: Path, toolbar_bookmarks: list, menu_bookmarks: list) -> None:
    """Create a minimal but valid Firefox places.sqlite at db_path."""
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    cur  = conn.cursor()

    cur.executescript("""
        CREATE TABLE IF NOT EXISTS moz_places (
            id          INTEGER PRIMARY KEY,
            url         TEXT NOT NULL,
            title       TEXT,
            rev_host    TEXT,
            visit_count INTEGER DEFAULT 0,
            hidden      INTEGER DEFAULT 0,
            typed       INTEGER DEFAULT 0,
            frecency    INTEGER DEFAULT -1,
            last_visit_date INTEGER,
            guid        TEXT
        );

        CREATE TABLE IF NOT EXISTS moz_bookmarks (
            id            INTEGER PRIMARY KEY,
            type          INTEGER,
            fk            INTEGER DEFAULT NULL,
            parent        INTEGER,
            position      INTEGER,
            title         TEXT,
            keyword_id    INTEGER DEFAULT NULL,
            folder_type   TEXT,
            dateAdded     INTEGER,
            lastModified  INTEGER,
            guid          TEXT
        );
    """)

    # Root bookmark structure (mirrors a real Firefox install)
    root_rows = [
        # id, type, fk, parent, position, title, dateAdded
        (1,  2, None, 0,  0, "",                    _prtime(2019, 1, 1)),  # root
        (2,  2, None, 1,  0, "Bookmarks Menu",      _prtime(2019, 1, 1)),
        (3,  2, None, 1,  1, "Bookmarks Toolbar",   _prtime(2019, 1, 1)),
        (4,  2, None, 1,  2, "Tags",                _prtime(2019, 1, 1)),
        (5,  2, None, 1,  3, "Other Bookmarks",     _prtime(2019, 1, 1)),
        (6,  2, None, 1,  4, "Mobile Bookmarks",    _prtime(2019, 1, 1)),
    ]
    cur.executemany(
        "INSERT INTO moz_bookmarks (id,type,fk,parent,position,title,dateAdded) "
        "VALUES (?,?,?,?,?,?,?)",
        root_rows,
    )

    place_id   = 1
    bm_id      = 100

    def _insert_items(items: list, parent_id: int) -> None:
        nonlocal place_id, bm_id
        for pos, item in enumerate(items):
            if item["type"] == "url":
                cur.execute(
                    "INSERT INTO moz_places (id, url, title) VALUES (?, ?, ?)",
                    (place_id, item["url"], item["name"]),
                )
                cur.execute(
                    "INSERT INTO moz_bookmarks "
                    "(id, type, fk, parent, position, title, dateAdded) "
                    "VALUES (?, 1, ?, ?, ?, ?, ?)",
                    (bm_id, place_id, parent_id, pos, item["name"], item["date_added"]),
                )
                place_id += 1
                bm_id    += 1
            elif item["type"] == "folder":
                folder_date = int(item.get("date_added", _prtime(2020, 1, 1)))
                cur.execute(
                    "INSERT INTO moz_bookmarks "
                    "(id, type, fk, parent, position, title, dateAdded) "
                    "VALUES (?, 2, NULL, ?, ?, ?, ?)",
                    (bm_id, parent_id, pos, item["name"], folder_date),
                )
                folder_bm_id = bm_id
                bm_id += 1
                _insert_items(item.get("children", []), folder_bm_id)

    # Chromium _webkit timestamps are strings; Firefox wants int microseconds.
    # Patch items to use PRTime before inserting.
    def _patch_dates(items: list) -> list:
        import datetime, re
        out = []
        for item in items:
            item = dict(item)
            if "date_added" in item:
                try:
                    webkit = int(item["date_added"])
                    unix   = (webkit - 11_644_473_600_000_000) // 1_000_000
                    item["date_added"] = unix * 1_000_000
                except (ValueError, TypeError):
                    item["date_added"] = _prtime(2020, 1, 1)
            if "children" in item:
                item["children"] = _patch_dates(item["children"])
            out.append(item)
        return out

    _insert_items(_patch_dates(toolbar_bookmarks), parent_id=3)  # Toolbar
    _insert_items(_patch_dates(menu_bookmarks),    parent_id=2)  # Menu

    conn.commit()
    conn.close()


# Firefox bookmark data (mapped from the Chromium sets above but slightly different)

ALEX_FF_TOOLBAR = [
    {"name": "GitHub",        "url": "https://github.com",             "type": "url", "date_added": _webkit(2020, 4, 10)},
    {"name": "Stack Overflow","url": "https://stackoverflow.com",      "type": "url", "date_added": _webkit(2020, 4, 10)},
    {"name": "Python Docs",   "url": "https://docs.python.org/3/",     "type": "url", "date_added": _webkit(2020, 5, 7)},
    {"name": "MDN Web Docs",  "url": "https://developer.mozilla.org",  "type": "url", "date_added": _webkit(2020, 6, 14)},
    _folder_node("Bookmarks Toolbar", [
        {"name": "PyPI",          "url": "https://pypi.org",                 "type": "url", "date_added": _webkit(2021, 1, 3)},
        {"name": "Read the Docs", "url": "https://readthedocs.org",          "type": "url", "date_added": _webkit(2021, 2, 17)},
        {"name": "Awesome Python","url": "https://awesome-python.com",       "type": "url", "date_added": _webkit(2021, 3, 8)},
    ], 2021, 1, 3),
]

ALEX_FF_MENU = [
    {"name": "Hacker News",   "url": "https://news.ycombinator.com",   "type": "url", "date_added": _webkit(2020, 7, 22)},
    {"name": "Lobste.rs",     "url": "https://lobste.rs",              "type": "url", "date_added": _webkit(2020, 8, 5)},
    {"name": "Reddit",        "url": "https://www.reddit.com",         "type": "url", "date_added": _webkit(2020, 9, 1)},
    {"name": "YouTube",       "url": "https://www.youtube.com",        "type": "url", "date_added": _webkit(2020, 9, 18)},
    {"name": "Bandcamp",      "url": "https://bandcamp.com",           "type": "url", "date_added": _webkit(2021, 5, 7)},
]

JORDAN_FF_TOOLBAR = [
    {"name": "Gmail",         "url": "https://mail.google.com",        "type": "url", "date_added": _webkit(2019, 9, 3)},
    {"name": "Amazon",        "url": "https://www.amazon.com",         "type": "url", "date_added": _webkit(2019, 9, 3)},
    {"name": "Netflix",       "url": "https://www.netflix.com",        "type": "url", "date_added": _webkit(2019, 10, 12)},
    _folder_node("Daily", [
        {"name": "BBC News",  "url": "https://www.bbc.com/news",       "type": "url", "date_added": _webkit(2020, 1, 5)},
        {"name": "Weather",   "url": "https://weather.com",            "type": "url", "date_added": _webkit(2020, 1, 5)},
        {"name": "Reddit",    "url": "https://www.reddit.com",         "type": "url", "date_added": _webkit(2020, 2, 14)},
    ], 2020, 1, 5),
]

JORDAN_FF_MENU = [
    {"name": "Allrecipes",    "url": "https://www.allrecipes.com",     "type": "url", "date_added": _webkit(2021, 6, 8)},
    {"name": "Tasty",         "url": "https://tasty.co",               "type": "url", "date_added": _webkit(2021, 6, 8)},
    {"name": "Pinterest",     "url": "https://www.pinterest.com",      "type": "url", "date_added": _webkit(2021, 7, 22)},
    {"name": "Spotify",       "url": "https://open.spotify.com",       "type": "url", "date_added": _webkit(2021, 8, 3)},
    {"name": "Goodreads",     "url": "https://www.goodreads.com",      "type": "url", "date_added": _webkit(2021, 9, 14)},
]


# ---------------------------------------------------------------------------
# File writer helpers
# ---------------------------------------------------------------------------

def _write_chromium(path: Path, bar: dict, other: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(_make_chromium_bookmarks(bar, other), fh, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Main builder
# ---------------------------------------------------------------------------

def build_mock_windows_old() -> None:
    print(f"Building mock Windows.old at: {OUTPUT_ROOT.parent}")
    print()

    # ── Alex ──────────────────────────────────────────────────────────────
    alex = OUTPUT_ROOT / "Alex"
    print("Creating user: Alex")

    _write_chromium(
        alex / r"AppData\Local\Google\Chrome\User Data\Default\Bookmarks",
        ALEX_CHROME_BAR, ALEX_CHROME_OTHER,
    )
    print("  Chrome          OK")

    _write_chromium(
        alex / r"AppData\Local\Microsoft\Edge\User Data\Default\Bookmarks",
        ALEX_EDGE_BAR,
        _folder_node("Other bookmarks", []),
    )
    print("  Edge            OK")

    _write_chromium(
        alex / r"AppData\Local\BraveSoftware\Brave-Browser\User Data\Default\Bookmarks",
        ALEX_BRAVE_BAR,
        _folder_node("Other bookmarks", []),
    )
    print("  Brave           OK")

    _create_firefox_db(
        alex / r"AppData\Roaming\Mozilla\Firefox\Profiles\alex4k2m.default-release\places.sqlite",
        ALEX_FF_TOOLBAR,
        ALEX_FF_MENU,
    )
    print("  Firefox         OK")
    print()

    # ── Jordan ────────────────────────────────────────────────────────────
    jordan = OUTPUT_ROOT / "Jordan"
    print("Creating user: Jordan")

    _write_chromium(
        jordan / r"AppData\Local\Google\Chrome\User Data\Default\Bookmarks",
        JORDAN_CHROME_BAR, JORDAN_CHROME_OTHER,
    )
    print("  Chrome          OK")

    _write_chromium(
        jordan / r"AppData\Local\BraveSoftware\Brave-Browser\User Data\Default\Bookmarks",
        JORDAN_BRAVE_BAR,
        _folder_node("Other bookmarks", []),
    )
    print("  Brave           OK")

    _create_firefox_db(
        jordan / r"AppData\Roaming\Mozilla\Firefox\Profiles\jrd9x1c.default-release\places.sqlite",
        JORDAN_FF_TOOLBAR,
        JORDAN_FF_MENU,
    )
    print("  Firefox         OK")

    # Jordan's Opera (single Bookmarks file at root of Opera path)
    opera_bm = jordan / r"AppData\Roaming\Opera Software\Opera Stable\Bookmarks"
    opera_bm.parent.mkdir(parents=True, exist_ok=True)
    with open(opera_bm, "w", encoding="utf-8") as fh:
        json.dump(
            _make_chromium_bookmarks(
                JORDAN_OPERA_BOOKMARKS,
                _folder_node("Other bookmarks", []),
            ),
            fh, indent=2, ensure_ascii=False,
        )
    print("  Opera           OK")
    print()

    total_files = sum(1 for _ in OUTPUT_ROOT.parent.rglob("*") if _.is_file())
    print(f"Mock data ready. {total_files} file(s) created.")
    print(f"Path: {OUTPUT_ROOT.parent}")


if __name__ == "__main__":
    build_mock_windows_old()
