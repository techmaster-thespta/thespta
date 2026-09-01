---
name: add-event
description: Add, edit, or remove a PTA event highlight (Home page preview + Events page quick-list). Config-only — never edit src/.
---

# Add / edit / remove an event highlight

Use this when the user asks to add an upcoming event, change an event's
date/time/details, or remove one from the site's short highlight lists.

**This is not the live Google Calendar.** If the user's request is really
"put this on the calendar," that's Task 5 in `docs/SOP.md` — done directly
in Google Calendar, no code involved, out of scope for this skill.

## File

`config/events.json` — a JSON array. Each entry:

```json
{ "day": "15", "month": "Sep", "title": "Back-to-School Picnic", "when": "5:30 – 7:00 PM · Courtyard", "featured": false }
```

Fields:
- `day` — two-digit-looking string, e.g. `"05"` or `"15"`.
- `month` — three-letter abbreviation, e.g. `"Sep"`.
- `title` — event name.
- `when` — time and/or location, one line, e.g. `"6:30 PM · School Library"`.
- `featured` — boolean. **Exactly one entry in the whole file must be `true`** — that one becomes the large navy "Featured Event" card on the Home page. All others must be `false`.
- `description` — **required on the featured entry only** (a one-sentence blurb; the featured card displays it). Optional/omit on non-featured entries.

The order of entries in the file is the display order everywhere.

## Steps

1. Read `config/events.json`.
2. **Adding**: append a new `{ }` entry in the right chronological position. If it should be the new featured event, set its `featured` to `true` and set every other entry's `featured` to `false` (there must be exactly one).
3. **Editing**: change the relevant fields in place.
4. **Removing**: delete the entry. If it was the featured one, set `featured: true` on a different entry (a file with zero featured entries falls back to the first entry, which is probably not what's intended — always leave exactly one explicit).
5. Run `python3 src/build.py`.
6. Run `python3 test/validate_build.py` — confirm it passes.
7. Report which generated files changed (`pages/home.html` and `pages/events.html` — this config feeds both) and remind the user to push (`docs/SOP.md` Task 7) — GitHub Actions rebuilds and redeploys automatically.

## Do not

- Do not edit `src/templates/featured-event.html.tmpl`, `more-event-row.html.tmpl`, `event-row.html.tmpl`, or `src/build.py` to accomplish this. If the requested change genuinely needs a new field or different layout, stop and tell the user that's a template change, not a config change, and ask before proceeding.
