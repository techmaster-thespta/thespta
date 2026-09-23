---
name: add-event-page
description: Give one specific event its own searchable page (e.g. the Holiday Market) — with Google event structured data — or edit/remove one. Opt-in only; config-only — never edit src/.
---

# Add / edit / remove an event page

Use this when the user wants a particular event to be findable on Google
(e.g. "I want the Holiday Market to show up when people search for it").
This is **opt-in**: routine calendar events stay calendar-only (see the
`add-event` skill). Only events the user explicitly names get a page.

Each entry in `config/event-pages.json` becomes
`pages/events/<slug>.html` with:

- a full page (date/time, location, contact, flyer, detail sections,
  "Add to Google Calendar" button),
- schema.org `Event` JSON-LD in `<head>` (what Google reads to show it
  as an event in search results),
- a `<meta name="description">` from `summary`, a canonical URL, and a
  `sitemap.xml` entry,
- a card in the "Featured Events" section at the top of the Events page
  while the event is still upcoming (the page itself stays up afterward,
  so shared links don't break).

## File

`config/event-pages.json` — a JSON array, `[]` means no event pages and
no "Featured Events" section. Each entry:

```json
{
  "slug": "holiday-market",
  "title": "THES PTA Holiday Market 2026",
  "eyebrow": "Save the Date",
  "tagline": "One sentence shown under the title and on the Events page card.",
  "summary": "1–2 sentences naming the event, full date, time, and place — becomes the Google search snippet and the JSON-LD description.",
  "start": "2026-11-21T11:00",
  "end": "2026-11-21T15:00",
  "location_name": "Thunder Hill Elementary School",
  "flyer_filename": "events/holiday-market-2026.png",
  "flyer_alt": "Text version of what the flyer says.",
  "about": ["Paragraph.", "Paragraph."],
  "sections": [
    { "heading": "What You'll Find", "items": ["Bullet", "Bullet"], "note": "Optional line under the list." }
  ],
  "register_href": "",
  "contact_name": "Natalie Miskimins",
  "contact_email": "president.thespta@gmail.com"
}
```

Required: `slug`, `title`, `summary`, `start`. Everything else is
optional. `start`/`end` are local time in `config/site.json`'s
`calendar.timezone` (no offset — the build adds the right EST/EDT one).
Location defaults to the school's address from `config/site.json`;
override with `address_line1`/`address_line2` for an off-site event.
`register_href`, when set, adds a "Register as a Vendor" button.

## Steps

1. Get the details from the user or their flyer. **Never guess** a date,
   time, price, or link — ask. Check `config/events.json` / the calendar
   for the same event and make sure the date matches.
2. Save the flyer image into `assets/flyers/events/` (this repo, not a
   Drive link — see the "images" constraint in `.claude/CLAUDE.md`) and
   set `flyer_filename` to `events/<file>`.
3. Add/edit/remove the entry in `config/event-pages.json`. Put the
   event's name, town ("Columbia, MD"), and full date in `summary` —
   that's the text people see in search results.
4. Run `python3 src/build.py` and `python3 test/validate_build.py`.
5. Push (`docs/SOP.md` Task 7). Then remind the user to use Google
   Search Console → URL Inspection → "Request indexing" on the new page
   URL, and to share that link (social, newsletter, community calendars)
   — Google ranks pages other sites link to.

**Removing**: when an event is long past and no one will look for it,
delete its entry and its flyer file. Changing a `slug` changes the URL —
avoid that once a page has been shared.

## Do not

- Do not create a page for an event the user didn't ask for.
- Do not edit `src/templates/event-page.html.tmpl` or `src/build.py` for
  a content change — layout changes are a structural change; ask first.
