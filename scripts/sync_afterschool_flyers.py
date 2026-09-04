#!/usr/bin/env python3
"""
Thunder Hill Elementary PTA — Afterschool Programs flyer sync.

Reads the fixed Google Drive folder (config/site.json's
`afterschool_flyers_folder_id`) via the Drive API v3 `files.list`
endpoint, and reconciles config/afterschool-programs.json against
what's actually in that folder right now:

  - A file no longer in the folder -> its config entry is removed.
  - A file id not yet in config -> a placeholder entry is added (a
    readable name guessed from the filename, description flagged as
    needing review). Writing the program's *real* name/schedule/price
    is a vision/understanding task — reading what the flyer actually
    says — which this script can't do; that's a follow-up a human or
    an agent does by looking at the flyer, same as the first pass that
    built this file originally.
  - A file already in config whose content changed (Drive computes and
    exposes each file's md5Checksum itself, so this needs no download)
    -> flagged `needs_review: true` and its hash updated, but its old
    details are left in place rather than wiped, since stale-but-present
    beats blank.
  - Unchanged files are left untouched entirely.

Requires the GOOGLE_DRIVE_API_KEY environment variable — an API-key-only
(no OAuth) credential restricted to the Drive API. Since the folder is
shared as "anyone with the link," a bare API key is enough to read it;
Drive API keys without an attached OAuth identity can only ever see
already-public content, so a leaked key doesn't expose anything private.
See docs/SOP.md for how to create one.

Run by .github/workflows/sync-afterschool-flyers.yml (daily — this
folder changes far less often than the events calendar) and can be run
locally too:

    GOOGLE_DRIVE_API_KEY=xxx python3 scripts/sync_afterschool_flyers.py

No dependencies beyond the Python 3 standard library.
"""
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config"

DRIVE_API_KEY = os.environ.get("GOOGLE_DRIVE_API_KEY")
DRIVE_FILES_LIST_URL = "https://www.googleapis.com/drive/v3/files"


def load_json(name, default=None):
    path = CONFIG / name
    if not path.exists():
        return default
    return json.loads(path.read_text())


def list_folder_files(folder_id, api_key):
    """Every non-trashed file directly inside the folder, as
    {id, name, md5Checksum, mimeType}. One API call, no file downloads —
    Drive already computes the checksum server-side."""
    params = {
        "q": f"'{folder_id}' in parents and trashed = false",
        "fields": "files(id,name,md5Checksum,mimeType)",
        "key": api_key,
        "pageSize": "1000",
    }
    url = f"{DRIVE_FILES_LIST_URL}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=30) as resp:
        data = json.loads(resp.read())
    if "error" in data:
        raise SystemExit(f"Drive API error: {data['error'].get('message', data['error'])}")
    return data.get("files", [])


def guess_name(filename):
    """A readable fallback title for a brand-new flyer nobody's written
    up yet, e.g. "chess-club_flyer.jpg" -> "Chess Club Flyer"."""
    stem = Path(filename).stem
    words = stem.replace("_", " ").replace("-", " ").split()
    return " ".join(w.capitalize() for w in words) or filename


def blank_program(file_id, name):
    return {
        "name": guess_name(name),
        "provider": None,
        "description": "New flyer — needs review to fill in the real program details.",
        "day_time": None,
        "date_range": None,
        "grades": None,
        "price": None,
        "sessions": [],
        "show_date": None,
        "contact": None,
        "registration_href": None,
        "registration_note": None,
        "flyer_drive_file_id": file_id,
        "content_hash": None,
        "needs_review": True,
    }


def main():
    if not DRIVE_API_KEY:
        raise SystemExit("GOOGLE_DRIVE_API_KEY is not set — see docs/SOP.md for how to create one.")

    site = load_json("site.json", default={})
    folder_id = site.get("afterschool_flyers_folder_id")
    if not folder_id:
        raise SystemExit("config/site.json is missing afterschool_flyers_folder_id.")

    live_files = list_folder_files(folder_id, DRIVE_API_KEY)
    live_by_id = {f["id"]: f for f in live_files}

    programs = load_json("afterschool-programs.json", default=[])
    kept = []
    seen_ids = set()
    changed = False

    for program in programs:
        file_id = program.get("flyer_drive_file_id")
        live = live_by_id.get(file_id)
        if live is None:
            print(f"  - removed (no longer in folder): {program['name']}")
            changed = True
            continue
        seen_ids.add(file_id)
        if live.get("md5Checksum") != program.get("content_hash"):
            print(f"  ! flyer changed, flagging for review: {program['name']}")
            program = {**program, "content_hash": live.get("md5Checksum"), "needs_review": True}
            changed = True
        kept.append(program)

    for file_id, live in live_by_id.items():
        if file_id in seen_ids:
            continue
        print(f"  + new flyer, adding placeholder: {live['name']}")
        entry = blank_program(file_id, live["name"])
        entry["content_hash"] = live.get("md5Checksum")
        kept.append(entry)
        changed = True

    if not changed:
        print("No changes — folder matches config/afterschool-programs.json.")
        return

    (CONFIG / "afterschool-programs.json").write_text(json.dumps(kept, indent=2) + "\n")
    print(f"Wrote config/afterschool-programs.json ({len(kept)} programs).")


if __name__ == "__main__":
    main()
