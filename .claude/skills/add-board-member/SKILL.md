---
name: add-board-member
description: Add, edit, or remove a PTA board member (About page roster). Config-only — never edit src/.
---

# Add / edit / remove a board member

Use this when the user asks to add a new officer, change a board member's
name/role/email, or remove someone from the roster on the About page.

## File

`config/board.json` — a JSON array. Each entry:

```json
{ "role": "Treasurer", "name": "Daniel Osei", "email": "treasurer@thunderhillpta.org", "photo_filename": "board-daniel-osei.jpg" }
```

`role` and `name` are required. `email` and `photo_filename` are both
**optional** — omit `email` rather than guess one, and omit
`photo_filename` for a vacant seat (`"name": "Vacant"`) or anyone who
hasn't supplied a headshot yet; the card falls back to a neutral
placeholder icon so the grid stays visually aligned. A photo file goes in
`assets/images/` (flat, no subfolder — see that folder's own README) same
as the hero/page-header images, named however you like as long as
`photo_filename` matches exactly.

Order in the file is display order (grid, left-to-right/top-to-bottom).

## Steps

1. Read `config/board.json`.
2. **Adding**: append a new `{ }` entry. Ask the user for role and name if either wasn't given — don't invent a person. Leave `email`/`photo_filename` out entirely if not supplied; don't guess an email domain or fabricate a photo.
3. **Editing**: change the relevant field(s) in place.
4. **Removing**: delete the entry — or, if the seat is now vacant rather than eliminated, keep the `role` and set `"name": "Vacant"`, dropping `email`/`photo_filename`.
5. If a new headshot was supplied, save it into `assets/images/` (crop/save as needed) and set `photo_filename` to that filename.
6. Run `python3 src/build.py`.
7. Run `python3 test/validate_build.py` — confirm it passes.
8. Report that `pages/about.html` changed and remind the user to push (`docs/SOP.md` Task 7) — GitHub Actions rebuilds and redeploys automatically.

## Do not

- Do not edit `src/templates/card-board-member.html.tmpl` or `src/build.py`. If the request needs something the current card doesn't support (a bio field, a different layout), stop and tell the user that's a template change, not a config change, and ask before proceeding.
