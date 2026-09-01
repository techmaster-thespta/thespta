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
{ "role": "Treasurer", "name": "Daniel Osei", "email": "treasurer@thunderhillpta.org" }
```

All three fields are required. Order in the file is display order (grid,
left-to-right/top-to-bottom).

## Steps

1. Read `config/board.json`.
2. **Adding**: append a new `{ }` entry. Ask the user for role, name, and email if any weren't given — don't invent a person or guess an email domain.
3. **Editing**: change the relevant field(s) in place.
4. **Removing**: delete the entry.
5. Run `python3 src/build.py`.
6. Run `python3 test/validate_build.py` — confirm it passes.
7. Report that `pages/about.html` changed and remind the user to re-paste it into Google Sites (`docs/SOP.md` Task 8).

## Do not

- Do not edit `src/templates/card-board-member.html.tmpl` or `src/build.py`. If the request needs a new field (e.g. a photo per board member) or a different card layout, stop and tell the user that's a template change, not a config change, and ask before proceeding.
