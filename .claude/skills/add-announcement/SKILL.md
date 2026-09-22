---
name: add-announcement
description: Add, edit, or remove an announcement in the rotating banner shown under the header on every page. Config-only — never edit src/.
---

# Add / edit / remove an announcement

Use this when the user asks to add, change, or remove a message in the
horizontal announcements banner shown just below the header on every page
of the site.

## File

`config/announcements.json` — a JSON array, empty (`[]`) by default. Each
entry:

```json
{ "text": "Fall Fest & Trunk or Treat is October 30 — get your tickets now!", "href": "https://example.com" }
```

or, to link to a page on this site instead of an external URL:

```json
{ "text": "New sponsorship levels are open!", "page_url": "become_sponsor" }
```

Use `page_url` (a key from `config/site.json`'s `page_urls`) for an internal
page, or `href` for an external link — never both on the same entry. `text`
is the whole clickable message; keep it short (one line, no line breaks) since
it has to fit the banner at every screen width. **Never use emoji in `text`**
— the PTA wants this professional, not casual; every text announcement
already gets a small built-in speaker icon automatically, so no icon of any
kind needs to be typed into the message itself.

For a real image icon instead of the built-in speaker icon, add
`icon_filename` — a small image file already in `assets/images/` (same place
hero/board photos live):

```json
{ "text": "New sponsorship levels are open!", "page_url": "become_sponsor", "icon_filename": "megaphone.png" }
```

If the PTA already has a **designed flyer graphic** for this announcement,
use `flyer_filename` instead — the whole banner becomes that flyer image
(no icon/text/arrow), clickable through to `href`/`page_url` same as any
other entry. The file goes in `assets/flyers/announcements/` (same pattern
as `assets/flyers/before-after-school/`, `assets/flyers/fundraising/`, etc.):

```json
{ "text": "Fall Fest flyer", "page_url": "events", "flyer_filename": "fall-fest-2026.jpg" }
```

`text` is still required even with `flyer_filename` — it becomes the
image's `alt` text for anyone who can't see it. Never combine
`icon_filename` and `flyer_filename` on the same entry (flyer wins, icon is
ignored) — pick one.

**Important behavior to know**: when this file is `[]`, the entire banner is
omitted from every page — not shown as an empty bar. Adding the first entry
makes it appear everywhere automatically; removing the last entry makes it
disappear everywhere automatically. This is by design — don't "fix" it by
editing templates.

**Rotation and dismissal**: with more than one entry, the banner
auto-rotates between them every few seconds with a smooth fade. A visitor
who dismisses the banner (the × button) won't see it again on that browser
*for the same set of announcements* — changing this file's content
(adding, removing, or editing any entry) automatically un-dismisses the
banner for everyone, since dismissal is remembered against a hash of the
current content, not "the banner" in general. You don't need to do
anything special to make an edit "count" as new — any change to this file
does.

## Steps

1. Read `config/announcements.json`.
2. **Adding**: append a new `{ }` entry. Ask for the exact message text and where it should link (an internal page, or an external URL) if not given.
3. **Editing**: change the relevant field(s) in place.
4. **Removing**: delete the entry.
5. Run `python3 src/build.py`.
6. Run `python3 test/validate_build.py` — confirm it passes.
7. Report that every page changed (mention explicitly if the banner just appeared or disappeared for the first time, and that any edit re-shows the banner to visitors who'd previously dismissed the old version) and remind the user to push (`docs/SOP.md` Task 7) — GitHub Actions rebuilds and redeploys automatically.

## Do not

- Do not edit `src/templates/announcement-banner.html.tmpl`, the
  `build_announcement_banner` function in `src/build.py`, or the
  `.thes__announce*` CSS rules in `src/templates/tokens.html.tmpl`. If the
  request needs different rotation timing, a different color, per-page
  targeting, or anything else the config can't express, stop and tell the
  user that's a template change, not a config change, and ask before
  proceeding.
