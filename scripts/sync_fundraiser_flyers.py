#!/usr/bin/env python3
"""
Thunder Hill Elementary PTA — Fundraiser flyer sync.

Reconciles config/fundraisers.json against whatever's actually in
assets/flyers/fundraising/ right now. Same mechanism as
sync_afterschool_flyers.py (sha256 of the file bytes, no external
service involved at all), but fundraisers behave differently from
afterschool programs in one important way this script has to account
for:

An afterschool program's flyer basically *is* the program — no flyer,
no listing. A fundraiser is usually a standing campaign (Box Tops,
RaiseRight, Membership...) that exists independently of whether a
current flyer image happens to sit in the folder, and — this is the
part that actually bit us — a *new* flyer file is more often a reprint
of an existing campaign than a brand-new one (four flyers landed in
the old Drive folder once: three were obviously existing campaigns by
name, and the fourth, "buy-a-box.jpg", turned out to be the See's
Candies flyer under a name that shares no words with "See's Candies
Fundraiser" at all — only actually reading the image showed that).
So this script:

  - A file no longer in the folder, whose entry already has real
    content (a real cta_href/description, not the generic placeholder
    text) -> just detaches the flyer (`flyer_filename`/`content_hash`
    cleared). The campaign itself isn't flyer-dependent, so it stays
    on the page.
  - A file no longer in the folder, whose entry is *still* an
    unreviewed placeholder (nothing but the generic "New flyer..."
    text) -> removed outright, same as afterschool — there was never
    any real content to lose.
  - A file not yet attached to anything: tries a cheap, deliberately
    conservative filename-vs-campaign-name match first (see
    `guess_existing_match` — normalizes both to bare alnum strings and
    checks substring containment, so "Raise-Right.jpg" matches
    "RaiseRight Gift Cards" even though the config name has no space).
    A confident match just attaches the flyer to that existing entry
    and flags it `needs_review` so the review skill double-checks the
    guess and refreshes anything the new flyer changed. No match ->
    a blank placeholder card is added instead, exactly like
    afterschool — same reasoning: reading a flyer well enough to know
    it's "actually the See's Candies flyer" is a vision/understanding
    task this plain script can't do, so it leaves that call, clearly
    flagged, for `review-fundraiser-flyers`.
  - A file already attached whose content changed -> flagged
    `needs_review: true`, hash updated, old details left in place.
  - Unchanged files are left untouched entirely.

This originally read a shared Google Drive folder via the Drive API
(needing a GOOGLE_DRIVE_API_KEY secret and a personal Google account in
good standing to own the folder). That whole dependency was removed
after the owning account got flagged by Google and every file in it —
even ones served by a plain public link — started 403ing with "you
can't access this item, it violates our Terms of Service." Flyers now
just live in this repo (assets/flyers/fundraising/), uploaded via
GitHub's own web UI or a normal git push — no external account, no API
key, nothing for a third party to flag. This also means the mechanical
reconciliation can run on every push instead of polling on a schedule
(see .github/workflows/deploy.yml) — a file landing in the repo *is*
the event, there's no external state to poll for anymore.

Run as a step in .github/workflows/deploy.yml, and can be run locally
too:

    python3 scripts/sync_fundraiser_flyers.py

No dependencies beyond the Python 3 standard library.
"""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config"
FLYERS_DIR = ROOT / "assets" / "flyers" / "fundraising"

PLACEHOLDER_DESCRIPTION = "New flyer — needs review to fill in the real campaign details."


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


def normalize(text):
    """Bare-alnum, lowercased, no separators at all — deliberately more
    aggressive than splitting into words, so "RaiseRight" (one word in
    the config) and "Raise-Right" (two words in a filename) normalize
    to the identical string instead of failing a word-token match."""
    return re.sub(r"[^a-z0-9]", "", text.lower())


def guess_existing_match(filename, campaigns):
    """A confident (but conservative) guess that a new file is a
    reprint of an existing campaign, not a new one — a plain substring
    check on the normalized filename stem vs. each campaign's normalized
    name, only trusted when the shorter side is at least 5 characters
    (long enough to rule out coincidental matches on short words).
    Returns the matching campaign dict, or None if nothing's confident
    enough — None is the safe default; it just means a placeholder gets
    created for a human/agent to sort out instead, same as
    sync_afterschool_flyers.py does for everything."""
    stem = normalize(Path(filename).stem)
    if len(stem) < 5:
        return None
    best = None
    for campaign in campaigns:
        name = normalize(campaign["name"])
        if len(name) < 5:
            continue
        if stem in name or name in stem:
            if best is None or len(name) > len(normalize(best["name"])):
                best = campaign
    return best


def guess_display_name(filename):
    stem = Path(filename).stem
    words = stem.replace("_", " ").replace("-", " ").split()
    return " ".join(w.capitalize() for w in words) or filename


def blank_campaign(filename):
    return {
        "name": guess_display_name(filename),
        "category": "everyday",
        "description": PLACEHOLDER_DESCRIPTION,
        "how_to_join": None,
        "cta_label": None,
        "cta_href": None,
        "secondary_label": None,
        "secondary_href": None,
        "enrollment_code": None,
        "dates": [],
        "contact": None,
        "flyer_filename": filename,
        "content_hash": None,
        "needs_review": True,
    }


def main():
    live_files = list_flyer_files()

    campaigns = load_json("fundraisers.json", default=[])
    kept = []
    seen_filenames = set()
    changed = False

    for campaign in campaigns:
        filename = campaign.get("flyer_filename")
        if not filename:
            kept.append(campaign)
            continue
        if filename not in live_files:
            if campaign.get("description") == PLACEHOLDER_DESCRIPTION:
                print(f"  - removed (unreviewed placeholder, flyer gone): {campaign['name']}")
                changed = True
                continue
            print(f"  - flyer detached (file removed from folder, campaign kept): {campaign['name']}")
            campaign = {**campaign, "flyer_filename": None, "content_hash": None}
            changed = True
            kept.append(campaign)
            continue
        seen_filenames.add(filename)
        if live_files[filename] != campaign.get("content_hash"):
            print(f"  ! flyer changed, flagging for review: {campaign['name']}")
            campaign = {**campaign, "content_hash": live_files[filename], "needs_review": True}
            changed = True
        kept.append(campaign)

    for filename, file_hash in live_files.items():
        if filename in seen_filenames:
            continue
        match = guess_existing_match(filename, kept)
        if match is not None:
            print(f"  ~ new flyer {filename!r} looks like an existing campaign, attaching + flagging: {match['name']}")
            match["flyer_filename"] = filename
            match["content_hash"] = file_hash
            match["needs_review"] = True
            changed = True
            continue
        print(f"  + new flyer, adding placeholder: {filename}")
        entry = blank_campaign(filename)
        entry["content_hash"] = file_hash
        kept.append(entry)
        changed = True

    if not changed:
        print("No changes — folder matches config/fundraisers.json.")
        return

    (CONFIG / "fundraisers.json").write_text(json.dumps(kept, indent=2) + "\n")
    print(f"Wrote config/fundraisers.json ({len(kept)} campaigns).")


if __name__ == "__main__":
    main()
