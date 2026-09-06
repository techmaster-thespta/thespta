#!/usr/bin/env python3
"""
Thunder Hill Elementary PTA — Fundraiser flyer sync.

Reads the fixed Google Drive folder (config/site.json's
`fundraiser_flyers_folder_id`) via the Drive API v3 `files.list`
endpoint, and reconciles config/fundraisers.json against what's
actually in that folder right now. Same mechanism as
sync_afterschool_flyers.py (Drive-computed md5Checksum, no downloads),
but fundraisers behave differently from afterschool programs in one
important way this script has to account for:

An afterschool program's flyer basically *is* the program — no flyer,
no listing. A fundraiser is usually a standing campaign (Box Tops,
RaiseRight, Membership...) that exists independently of whether a
current flyer image happens to sit in the folder, and — this is the
part that actually bit us — a *new* flyer file is more often a reprint
of an existing campaign than a brand-new one (four flyers landed in
this folder once: three were obviously existing campaigns by name,
and the fourth, "buy-a-box.jpg", turned out to be the See's Candies
flyer under a name that shares no words with "See's Candies
Fundraiser" at all — only actually reading the image showed that).
So this script:

  - A file no longer in the folder, whose entry already has real
    content (a real cta_href/description, not the generic placeholder
    text) -> just detaches the flyer (`flyer_drive_file_id`/
    `content_hash` cleared). The campaign itself isn't flyer-dependent,
    so it stays on the page.
  - A file no longer in the folder, whose entry is *still* an
    unreviewed placeholder (nothing but the generic "New flyer..."
    text) -> removed outright, same as afterschool — there was never
    any real content to lose.
  - A file id not yet attached to anything: tries a cheap, deliberately
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

Requires the GOOGLE_DRIVE_API_KEY environment variable — see
docs/SOP.md for how to create one (the same key already used for
sync_afterschool_flyers.py works here too; it's just a Drive-API-scoped
key, not tied to one folder).

Run by .github/workflows/sync-fundraiser-flyers.yml (daily) and can be
run locally too:

    GOOGLE_DRIVE_API_KEY=xxx python3 scripts/sync_fundraiser_flyers.py

No dependencies beyond the Python 3 standard library.
"""
import json
import os
import re
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config"

DRIVE_API_KEY = os.environ.get("GOOGLE_DRIVE_API_KEY")
DRIVE_FILES_LIST_URL = "https://www.googleapis.com/drive/v3/files"

PLACEHOLDER_DESCRIPTION = "New flyer — needs review to fill in the real campaign details."


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


def blank_campaign(file_id, filename):
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
        "flyer_drive_file_id": file_id,
        "content_hash": None,
        "needs_review": True,
    }


def main():
    if not DRIVE_API_KEY:
        raise SystemExit("GOOGLE_DRIVE_API_KEY is not set — see docs/SOP.md for how to create one.")

    site = load_json("site.json", default={})
    folder_id = site.get("fundraiser_flyers_folder_id")
    if not folder_id:
        raise SystemExit("config/site.json is missing fundraiser_flyers_folder_id.")

    live_files = list_folder_files(folder_id, DRIVE_API_KEY)
    live_by_id = {f["id"]: f for f in live_files}

    campaigns = load_json("fundraisers.json", default=[])
    kept = []
    seen_ids = set()
    changed = False

    for campaign in campaigns:
        file_id = campaign.get("flyer_drive_file_id")
        if not file_id:
            kept.append(campaign)
            continue
        live = live_by_id.get(file_id)
        if live is None:
            if campaign.get("description") == PLACEHOLDER_DESCRIPTION:
                print(f"  - removed (unreviewed placeholder, flyer gone): {campaign['name']}")
                changed = True
                continue
            print(f"  - flyer detached (file removed from folder, campaign kept): {campaign['name']}")
            campaign = {**campaign, "flyer_drive_file_id": None, "content_hash": None}
            changed = True
            kept.append(campaign)
            continue
        seen_ids.add(file_id)
        if live.get("md5Checksum") != campaign.get("content_hash"):
            print(f"  ! flyer changed, flagging for review: {campaign['name']}")
            campaign = {**campaign, "content_hash": live.get("md5Checksum"), "needs_review": True}
            changed = True
        kept.append(campaign)

    for file_id, live in live_by_id.items():
        if file_id in seen_ids:
            continue
        match = guess_existing_match(live["name"], kept)
        if match is not None:
            print(f"  ~ new flyer {live['name']!r} looks like an existing campaign, attaching + flagging: {match['name']}")
            match["flyer_drive_file_id"] = file_id
            match["content_hash"] = live.get("md5Checksum")
            match["needs_review"] = True
            changed = True
            continue
        print(f"  + new flyer, adding placeholder: {live['name']}")
        entry = blank_campaign(file_id, live["name"])
        entry["content_hash"] = live.get("md5Checksum")
        kept.append(entry)
        changed = True

    if not changed:
        print("No changes — folder matches config/fundraisers.json.")
        return

    (CONFIG / "fundraisers.json").write_text(json.dumps(kept, indent=2) + "\n")
    print(f"Wrote config/fundraisers.json ({len(kept)} campaigns).")


if __name__ == "__main__":
    main()
