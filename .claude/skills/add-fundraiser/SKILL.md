---
name: add-fundraiser
description: Add, edit, remove, or review a flagged entry on the Ways to Give (fundraising) page. Config-only — never edit src/.
---

# Add / edit / remove a fundraising campaign

Use this when the user asks to add a fundraiser, update one's details,
remove one, or review something a daily sync flagged. Every campaign on
`/fundraising` funds Thunder Hill Elementary PTA programs, grants, and
events — unlike the afterschool-programs page, these are the PTA's own
campaigns, not third-party providers running something at the school.

## File

`config/fundraisers.json` — a JSON array. Each entry:

```json
{
  "name": "RaiseRight Gift Cards",
  "category": "everyday",
  "description": "Buy everyday gift cards at full value — groceries, gas, takeout, and more — and a percentage comes back to the PTA on every purchase.",
  "how_to_join": "Download the RaiseRight app or visit raiseright.com and use the enrollment code below to get started.",
  "cta_label": "Get Started at RaiseRight",
  "cta_href": "https://www.raiseright.com/",
  "secondary_label": null,
  "secondary_href": null,
  "enrollment_code": "J77AQSBNQDUP",
  "dates": [],
  "contact": null,
  "flyer_drive_file_id": "1kUjegU4PK3LJLb01QdS1a8CD53to4V4m",
  "content_hash": "b8d91f8be1d6d1c1c1d73122d2314bfe",
  "needs_review": false
}
```

- `category` is one of five values, and drives both the card's badge
  text and which section of the page it appears in
  (`FUNDRAISER_GROUPS`/`FUNDRAISER_CATEGORY_LABELS` in `src/build.py`):
  - `recurring` — a dated series held several times a year (Restaurant
    Nights).
  - `seasonal` — a limited-time storefront (Spirit Wear).
  - `annual` — the yearly membership drive.
  - `everyday` — an ongoing, no-deadline program (Box Tops, RaiseRight,
    Mabel's Labels, See's Candies, Givebacks Rewards).
  - `direct` — reserved for the one "Give Directly" donation entry,
    which renders as the page's opening full-width band, not a card in
    a grid. Don't add a second `direct` entry — there's nowhere on the
    page for a second one to go.
- `dates` is only for a `recurring`-style campaign with real scheduled
  instances — see the "Restaurant Nights" entry for the shape
  (`{"date", "venue", "time", "note"}` per instance, `note` nullable).
  Leave it `[]` for anything else.
- `cta_href`/`cta_label` are the primary action link+button; both or
  neither — don't set one without the other. `secondary_href`/
  `secondary_label` work the same way for a second button. A
  `secondary_href` of the literal form `"page_urls.xxx"` (e.g.
  `"page_urls.get_involved"`) is a sentinel meaning "link to that page
  on this site" — `render_fundraiser_card()` resolves it through the
  page's own context so the relative path/depth comes out right; any
  other value is treated as a literal external URL.
- `enrollment_code` is only for a campaign with an actual sign-up code
  (RaiseRight) — `null` otherwise.
- `flyer_drive_file_id` is the Google Drive file ID for that campaign's
  flyer image — the card shows it as a thumbnail inside its "Details"
  disclosure, hotlinked from Drive, never downloaded into this repo.
  Get the ID from the file's share link
  (`drive.google.com/file/d/<this-part>/view`).
- `content_hash` and `needs_review` are bookkeeping for the automated
  sync (see below) — **don't hand-edit `content_hash`** unless you're
  intentionally telling the sync "this is the current version," and
  clear `needs_review` to `false` once you've actually resolved a
  flagged entry.

## This page is normally kept in sync automatically

`.github/workflows/sync-fundraiser-flyers.yml` runs daily against the
fixed Drive folder in `config/site.json`'s `fundraiser_flyers_folder_id`
(same `GOOGLE_DRIVE_API_KEY` secret `sync-afterschool-flyers.yml`
already uses — see `docs/SOP.md` Task 5c). Unlike the afterschool sync,
a fundraiser's flyer isn't what defines its existence — a campaign like
Box Tops stays on the page even if its current flyer image is removed
from the folder (the flyer just gets detached). And because a *new*
flyer file is often a reprint of an existing campaign rather than a
genuinely new one, the sync script makes a conservative filename-vs-name
guess before creating a new placeholder — see
`scripts/sync_fundraiser_flyers.py` and
`.claude/skills/review-fundraiser-flyers/SKILL.md` for exactly how that
works and gets resolved. **Neither script can write real campaign
details or tell a reprint from a genuinely new flyer with full
confidence** — that requires actually looking at the flyer, which is
`review-fundraiser-flyers`'s job, not this skill's.

## Steps for a manual add/edit/remove

1. Read `config/fundraisers.json`.
2. **Adding**: append a new entry — ask for (or read from the flyer)
   the fields above rather than inventing any of them. Pick the
   `category` from the five above.
3. **Editing**: change the relevant field(s) in place.
4. **Removing**: delete the entry. (Note: if its flyer is still in the
   Drive folder, the next daily sync will re-add it as a fresh
   `needs_review` placeholder — remove the file from the folder too if
   it should stay gone for good.)
5. Run `python3 src/build.py` then `python3 test/validate_build.py`.
6. Report that `pages/fundraising.html` changed and remind the user to
   push (`docs/SOP.md` Task 7).

## Do not

- Do not create a new page, template, or URL for an individual
  campaign — they all live on the one `/fundraising` page.
- Do not edit `src/templates/pages/fundraising.html.tmpl`,
  `src/templates/fundraising-empty.html.tmpl`, or
  `render_fundraiser_card()`/`build_fundraising_section()` in
  `src/build.py`. If the request needs a different card layout, a new
  category, or a field nothing here covers, stop and tell the user
  that's a template change, not a config change.
- Do not download a flyer image into `assets/images/` or this repo —
  the whole point of `flyer_drive_file_id` is that Drive keeps hosting
  it, exactly like afterschool-program and event-attachment flyers.
- Do not add a second `direct`-category entry.
