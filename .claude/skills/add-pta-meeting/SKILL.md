---
name: add-pta-meeting
description: Add, edit, or remove a PTA meeting record on the PTA Meetings archive page. Config-only — never edit src/.
---

# Add / edit / remove a PTA meeting record

Use this after a PTA meeting has happened and the user has a real
recap flyer, or real highlights/an agenda link, to report. Unlike
`config/events.json` (generated from Google Calendar, never
hand-edited), `config/pta-meetings.json` is normally kept up to date
the same way `config/afterschool-programs.json` and
`config/fundraisers.json` are: a "recap" flyer graphic dropped in
`assets/flyers/pta-meetings/` gets picked up automatically. Don't copy
the calendar invite's description in as `highlights` — that's a
different piece of writing with a different purpose (what the meeting
was *expected* to cover, not what actually happened), and typically
won't exist as real content until someone reads the recap flyer or
tells you what happened.

## This page is normally kept up to date automatically

`scripts/sync_pta_meeting_flyers.py` runs as a step in
`.github/workflows/deploy.yml` on every push and reconciles
`config/pta-meetings.json` against whatever's actually in
`assets/flyers/pta-meetings/`:

- A flyer removed from that folder → its record is removed.
- A brand-new flyer → a placeholder record appears with
  `"needs_review": true` and — deliberately — **no guessed date**
  (unlike the other flyer types, which guess a name): a wrong date
  would silently misfile the meeting into the wrong school year, so a
  dateless placeholder is left visibly incomplete instead. A dateless
  entry never becomes the page's "Latest Meeting" spotlight and never
  gets grouped into a school year — it shows up in a small "N new
  meeting flyers need review" notice instead.
- A changed flyer (same filename, different content) → flagged
  `"needs_review": true`, old details left in place.

**Reading the flyer to fill in the real date, title, and highlights is
not something this automation can do on its own** — that's a
vision/understanding task for a human or an agent
(`.claude/skills/review-pta-meeting-flyers/`). PTA meeting recap flyers
(like the one this feature launched with) typically state the
highlights directly — new board members welcomed, committees formed,
membership numbers — so this is usually a matter of reading the flyer
and transcribing what it already says, not writing new copy from
scratch.

### Adding a flyer without touching git directly

Anyone with repo access can drop a flyer in without using the command
line: on GitHub's website, go to
`https://github.com/techmaster-thespta/thespta/upload/main/assets/flyers/pta-meetings`,
drag the image in, and commit. The next push-triggered deploy picks it
up automatically and flags it for review.

## File

`config/pta-meetings.json` — a JSON array, one object per meeting:

```json
{
  "date": "2026-09-08",
  "title": "September PTA Meeting",
  "highlights": "The first PTA meeting of the 2026–2027 school year — welcomed new Executive Board members Ivan Torres-Negron (2nd Vice President of Fundraising) and Marianna Patterson (2nd PTACHC Representative), announced the formation of a new Beautification Committee, and celebrated reaching 84 PTA members on the way to a goal of 120.",
  "agenda_href": "https://docs.google.com/document/u/0/d/.../mobilebasic",
  "flyer_filename": "september-2026-pta-meeting-recap.png",
  "content_hash": "2c6c869cf685d8f364559763deaa9c417fac2913d55dd3c3a0612b7777952b0d",
  "needs_review": false
}
```

- `date` is ISO `YYYY-MM-DD` — used both to display the date and to
  group meetings into a school year (`compute_school_year()` in
  `src/build.py`: July onward starts a new school year, so a meeting in
  April groups with the September that started that same school year).
  **Never guess this** — leave it `null` (and `needs_review: true`) if
  it's genuinely unknown, rather than putting a wrong date in.
- `title` is short — "September PTA Meeting," not the flyer's full
  headline text.
- `highlights` is a real summary of what happened, 1–3 sentences —
  usually transcribed from the recap flyer itself. Ask the user (or
  read the flyer) rather than inventing it; if neither is available
  yet, leave the entry flagged `needs_review` rather than guessing.
- `agenda_href` is a real link (a Drive file, a Google Doc, a PDF) when
  one exists — `null` otherwise, which just omits the "View Agenda"
  button on that meeting's card. Don't invent one.
- `flyer_filename` is the bare filename of the recap flyer inside
  `assets/flyers/pta-meetings/` (e.g. `"september-2026-pta-meeting-recap.png"`,
  not a path or URL) — shown as a thumbnail inside the card, served
  from this repo. `content_hash` and `needs_review` are bookkeeping for
  the automated sync — **don't hand-edit `content_hash`** unless you're
  intentionally telling the sync "this is the current version," and
  clear `needs_review` to `false` once you've actually filled in a
  flagged entry's real details.

## How the page uses this

The single most recent *reviewed* meeting (by `date`) is spotlighted at
the top of `/pta-meetings` in a big navy card (reusing the Home page's
featured-event styling, including its flyer thumbnail and a "View
Agenda" button styled like the Events page's Sign Up/Join Google Meet
buttons). Every other reviewed meeting is grouped into a `<details>`
accordion by school year, most recent year open by default, older
years collapsed. An empty file (`[]`) shows a "no meetings recorded
yet" placeholder instead of an empty page.

## Steps for a manual add/edit/remove

Most of the time you won't need this — dropping a flyer in and running
`review-pta-meeting-flyers` (or waiting for the daily automation) is
the normal path. Use this for a correction, or a meeting with no flyer
at all.

1. Read `config/pta-meetings.json`.
2. **Adding**: append a new entry with the fields above (`flyer_filename`/
   `content_hash` can stay `null` if there's no flyer to attach). Since
   the *most recent* entry always becomes the spotlighted "Latest
   Meeting" automatically (sorted by `date`, not by array position),
   you don't need to worry about where in the array you add it.
3. **Editing**: change the relevant field(s) in place.
4. **Removing**: delete the entry. (Note: if its flyer is still in
   `assets/flyers/pta-meetings/`, the next push will re-add it as a
   fresh `needs_review` placeholder — delete the file too if it should
   stay gone for good.)
5. Run `python3 src/build.py` then `python3 test/validate_build.py`.
6. Report that `pages/pta-meetings.html` changed and remind the user to
   push (`docs/SOP.md` Task 7).

## Do not

- Do not create a new page, template, or URL for an individual meeting
  — they all live on the one `/pta-meetings` page.
- Do not edit `src/templates/pages/pta-meetings.html.tmpl`,
  `src/templates/pta-meeting-featured.html.tmpl`,
  `src/templates/card-pta-meeting.html.tmpl`,
  `src/templates/pta-meetings-empty.html.tmpl`, or
  `render_pta_meeting_card()`/`render_featured_pta_meeting()`/
  `build_pta_meetings_section()`/`compute_school_year()` in
  `src/build.py`. If the request needs a different card layout or a new
  field, stop and tell the user that's a template change, not a config
  change.
- Do not invent `highlights` from the calendar invite's description —
  that's what the meeting was *expected* to cover, not a record of what
  actually happened.
- Do not guess a `date`. Leave it `null` and flagged instead.
- Do not add a `config/pta-meetings.json` entry for a meeting that
  hasn't happened yet.
