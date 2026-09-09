#!/usr/bin/env python3
"""
Thunder Hill Elementary PTA — PTA Meeting flyer sync.

Reconciles config/pta-meetings.json against whatever's actually in
assets/flyers/pta-meetings/ right now — same mechanism as
sync_afterschool_flyers.py, and the same reasoning applies: a meeting's
flyer (a recap graphic the president drops in after the meeting happens)
basically *is* the record, so a missing flyer means a removed record,
not just a detached one the way a fundraiser's flyer can be.

  - A file no longer in the folder -> its config entry is removed.
  - A file not yet in config -> a placeholder entry is added, with
    `needs_review: true` and no `date` — deliberately no guessed date
    (unlike the other flyer types' guessed *name*), since a wrong date
    would silently misfile the meeting into the wrong school year until
    someone corrects it. A dateless entry never becomes the "Latest
    Meeting" spotlight and never gets grouped into a school year — see
    build_pta_meetings_section() in src/build.py — so an unreviewed
    placeholder can't misrepresent itself as reviewed content.
  - A file already in config whose content changed (sha256 of the file
    bytes differs from the stored content_hash) -> flagged
    `needs_review: true` and its hash updated, old details left in
    place.
  - Unchanged files are left untouched entirely.

Reading what the flyer actually says (the real date, title, and
highlights — a recap graphic's whole point) is a vision/understanding
task this script can't do; that's `.claude/skills/review-pta-meeting-
flyers/`'s job.

Run as a step in .github/workflows/deploy.yml, and can be run locally
too:

    python3 scripts/sync_pta_meeting_flyers.py

No dependencies beyond the Python 3 standard library.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config"
FLYERS_DIR = ROOT / "assets" / "flyers" / "pta-meetings"

PLACEHOLDER_HIGHLIGHTS = "New meeting flyer — needs review to fill in the real date, title, and highlights."


def load_json(name, default=None):
    path = CONFIG / name
    if not path.exists():
        return default
    return json.loads(path.read_text())


def list_flyer_files():
    """Every real file directly inside the flyers folder, as
    {filename: sha256_hex}. .gitkeep and any dotfile are ignored."""
    if not FLYERS_DIR.exists():
        return {}
    return {
        f.name: hashlib.sha256(f.read_bytes()).hexdigest()
        for f in FLYERS_DIR.iterdir()
        if f.is_file() and not f.name.startswith(".")
    }


def blank_meeting(filename):
    return {
        "date": None,
        "title": "New PTA Meeting Flyer",
        "highlights": PLACEHOLDER_HIGHLIGHTS,
        "agenda_href": None,
        "flyer_filename": filename,
        "content_hash": None,
        "needs_review": True,
    }


def main():
    live_files = list_flyer_files()

    meetings = load_json("pta-meetings.json", default=[])
    kept = []
    seen_filenames = set()
    changed = False

    for meeting in meetings:
        filename = meeting.get("flyer_filename")
        if filename is None or filename not in live_files:
            if filename is not None:
                print(f"  - removed (no longer in folder): {meeting.get('title')}")
                changed = True
                continue
            kept.append(meeting)
            continue
        seen_filenames.add(filename)
        if live_files[filename] != meeting.get("content_hash"):
            print(f"  ! flyer changed, flagging for review: {meeting.get('title')}")
            meeting = {**meeting, "content_hash": live_files[filename], "needs_review": True}
            changed = True
        kept.append(meeting)

    for filename, file_hash in live_files.items():
        if filename in seen_filenames:
            continue
        print(f"  + new flyer, adding placeholder: {filename}")
        entry = blank_meeting(filename)
        entry["content_hash"] = file_hash
        kept.append(entry)
        changed = True

    if not changed:
        print("No changes — folder matches config/pta-meetings.json.")
        return

    (CONFIG / "pta-meetings.json").write_text(json.dumps(kept, indent=2) + "\n")
    print(f"Wrote config/pta-meetings.json ({len(kept)} meetings).")


if __name__ == "__main__":
    main()
