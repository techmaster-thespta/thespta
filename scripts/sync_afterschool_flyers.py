#!/usr/bin/env python3
"""
Thunder Hill Elementary PTA — Afterschool Programs flyer sync.

Reconciles config/afterschool-programs.json against whatever's actually
in assets/flyers/before-after-school/ right now:

  - A file no longer in the folder -> its config entry is removed.
  - A file not yet in config -> a placeholder entry is added (a
    readable name guessed from the filename, description flagged as
    needing review). Writing the program's *real* name/schedule/price
    is a vision/understanding task — reading what the flyer actually
    says — which this script can't do; that's a follow-up a human or
    an agent does by looking at the flyer.
  - A file already in config whose content changed (sha256 of the file
    bytes differs from the stored content_hash) -> flagged
    `needs_review: true` and its hash updated, but its old details are
    left in place rather than wiped, since stale-but-present beats
    blank.
  - Unchanged files are left untouched entirely.

This originally read a shared Google Drive folder via the Drive API
(needing a GOOGLE_DRIVE_API_KEY secret and a personal Google account in
good standing to own the folder). That whole dependency was removed
after the owning account got flagged by Google and every file in it —
even ones served by a plain public link — started 403ing with "you
can't access this item, it violates our Terms of Service." Flyers now
just live in this repo (assets/flyers/before-after-school/), uploaded
via GitHub's own web UI or a normal git push — no external account, no
API key, nothing for a third party to flag. This also means the
mechanical reconciliation can run on every push instead of polling on a
schedule (see .github/workflows/deploy.yml) — a file landing in the
repo *is* the event, there's no external state to poll for anymore.

Run as a step in .github/workflows/deploy.yml, and can be run locally
too:

    python3 scripts/sync_afterschool_flyers.py

No dependencies beyond the Python 3 standard library.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config"
FLYERS_DIR = ROOT / "assets" / "flyers" / "before-after-school"


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


def guess_name(filename):
    """A readable fallback title for a brand-new flyer nobody's written
    up yet, e.g. "chess-club_flyer.jpg" -> "Chess Club Flyer"."""
    stem = Path(filename).stem
    words = stem.replace("_", " ").replace("-", " ").split()
    return " ".join(w.capitalize() for w in words) or filename


def blank_program(filename):
    return {
        "name": guess_name(filename),
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
        "flyer_filename": filename,
        "content_hash": None,
        "needs_review": True,
    }


def main():
    live_files = list_flyer_files()

    programs = load_json("afterschool-programs.json", default=[])
    kept = []
    seen_filenames = set()
    changed = False

    for program in programs:
        filename = program.get("flyer_filename")
        if filename is None or filename not in live_files:
            if filename is not None:
                print(f"  - removed (no longer in folder): {program['name']}")
                changed = True
                continue
            kept.append(program)
            continue
        seen_filenames.add(filename)
        if live_files[filename] != program.get("content_hash"):
            print(f"  ! flyer changed, flagging for review: {program['name']}")
            program = {**program, "content_hash": live_files[filename], "needs_review": True}
            changed = True
        kept.append(program)

    for filename, file_hash in live_files.items():
        if filename in seen_filenames:
            continue
        print(f"  + new flyer, adding placeholder: {filename}")
        entry = blank_program(filename)
        entry["content_hash"] = file_hash
        kept.append(entry)
        changed = True

    if not changed:
        print("No changes — folder matches config/afterschool-programs.json.")
        return

    (CONFIG / "afterschool-programs.json").write_text(json.dumps(kept, indent=2) + "\n")
    print(f"Wrote config/afterschool-programs.json ({len(kept)} programs).")


if __name__ == "__main__":
    main()
