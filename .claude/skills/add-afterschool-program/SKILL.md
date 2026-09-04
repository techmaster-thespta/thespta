---
name: add-afterschool-program
description: Add, edit, remove, or review a flagged entry on the Afterschool Programs page. Config-only — never edit src/.
---

# Add / edit / remove an afterschool program

Use this when the user asks to add a program, update one's details,
remove one, or review something a daily sync flagged. Every program on
`/afterschool-programs` is run by an **outside provider** (iCode,
KidzArt, a theatre company, etc.) — never the PTA or the school — the
page says so explicitly and every card should carry its own
registration link/contact info.

## File

`config/afterschool-programs.json` — a JSON array. Each entry:

```json
{
  "name": "Fall STEM Innovators: Robotics & 3D Design/Printing",
  "provider": "iCode Columbia",
  "description": "One or two sentences about what the program actually does.",
  "day_time": "3:55 – 5:00 PM",
  "date_range": "Sept 28 – Nov 2, 2026 (6 classes: 9/28, 10/5, 10/12, 10/19, 10/26, 11/2)",
  "grades": "K-5",
  "price": "$159",
  "sessions": [],
  "show_date": null,
  "contact": "410-454-9878 · columbia@icodeschool.com",
  "registration_href": null,
  "registration_note": "Scan the QR code on the flyer to register.",
  "flyer_drive_file_id": "1jYwU1sHU0ESSUFEOSCU3LUUlVIApi_sp",
  "content_hash": "59104f9ea3d65b77bc55afbe1673c28b",
  "needs_review": false
}
```

- `sessions` is only for a program that runs in multiple distinct blocks
  with their own dates/pricing (see KidzArt's entry for the pattern) —
  leave it `[]` for a program that's just one continuous run.
- `show_date` is only for something with a performance/showcase date
  (a theatre program) — `null` otherwise.
- `registration_href` is a real link when one exists; `registration_note`
  is free text for anything a link can't capture (e.g. "scan the QR code
  on the flyer" when there's no plain URL to link to). Either, both, or
  neither can be set.
- `flyer_drive_file_id` is the Google Drive file ID for that program's
  flyer image — the card shows it as a thumbnail exactly the way an
  event's calendar attachment already does (`drive_thumbnail_url()` in
  `src/build.py`), hotlinked from Drive, never downloaded into this
  repo. Get the ID from the file's share link
  (`drive.google.com/file/d/<this-part>/view`).
- `content_hash` and `needs_review` are bookkeeping for the automated
  sync (see below) — **don't hand-edit `content_hash`** unless you're
  intentionally telling the sync "this is the current version," and
  clear `needs_review` to `false` once you've actually updated a
  flagged entry's details.

## This page is normally kept in sync automatically

`.github/workflows/sync-afterschool-flyers.yml` runs daily against the
fixed Drive folder in `config/site.json`'s `afterschool_flyers_folder_id`
(see `docs/SOP.md` Task 5c for the one-time API key setup this needs).
It removes entries whose flyer disappeared from the folder, and adds a
placeholder (`needs_review: true`, name guessed from the filename) for
any brand-new flyer. **It cannot write the real program details** —
that requires actually looking at the flyer, which is a job for a human
or an agent, not the plain-Python sync script.

### Reviewing a flagged entry

1. Find entries with `"needs_review": true` in
   `config/afterschool-programs.json`.
2. Open `https://drive.google.com/file/d/<flyer_drive_file_id>/view` (or
   ask an agent to) and read the flyer.
3. Fill in `name`, `provider`, `description`, `day_time`, `date_range`
   (or `sessions`), `grades`, `price`, `contact`, and
   `registration_href`/`registration_note` from what the flyer actually
   says — don't invent details it doesn't show.
4. Set `"needs_review": false`.
5. Run `python3 src/build.py` then `python3 test/validate_build.py`.

## Steps for a manual add/edit/remove

1. Read `config/afterschool-programs.json`.
2. **Adding**: append a new entry — ask for (or read from the flyer)
   the fields above rather than inventing any of them.
3. **Editing**: change the relevant field(s) in place.
4. **Removing**: delete the entry. (Note: if its flyer is still in the
   Drive folder, the next daily sync will re-add it as a fresh
   `needs_review` placeholder — remove the file from the folder too if
   it should stay gone for good.)
5. Run `python3 src/build.py` then `python3 test/validate_build.py`.
6. Report that `pages/afterschool-programs.html` changed and remind the
   user to push (`docs/SOP.md` Task 7).

## Do not

- Do not create a new page, template, or URL for an individual program
  — they all live on the one `/afterschool-programs` page.
- Do not edit `src/templates/afterschool-programs-section.html.tmpl`,
  `src/templates/pages/afterschool-programs.html.tmpl`, or
  `render_afterschool_program_card()`/`build_afterschool_programs_section()`
  in `src/build.py`. If the request needs a different card layout or a
  new field, stop and tell the user that's a template change, not a
  config change.
- Do not download a flyer image into `assets/images/` or this repo —
  the whole point of `flyer_drive_file_id` is that Drive keeps hosting
  it, exactly like event attachments.
- Do not remove the "not sponsored or endorsed by the school" language
  from `afterschool-programs-section.html.tmpl`'s note — it's there on
  purpose since every program listed is run by a third party.
