# Archive

Expired announcements and featured event pages, kept for future
reference. Nothing in this folder is published on the website.

`scripts/archive_expired.py` moves entries here automatically (on every
push and every hourly calendar sync) once they're past their `expires`
date:

- `announcements.json` — from `config/announcements.json`
- `event-pages.json` — from `config/event-pages.json`
- `flyers/` — their flyer images, moved out of `assets/flyers/`

Each archived entry gets an `archived_on` date. To bring one back (say, an
annual event), copy its entry back into the live config file with new
dates and a new `expires`, and move its flyer back into `assets/flyers/`.
