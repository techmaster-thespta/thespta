---
name: add-sponsor
description: Add, edit, or remove a business sponsor listed on the Home page. Config-only — never edit src/.
---

# Add / edit / remove a sponsor

Use this when the user asks to add, change, or remove a business/community
sponsor shown in the "Our Sponsors" section of the Home page.

## File

`config/sponsors.json` — a JSON array, empty (`[]`) by default. Each entry:

```json
{ "name": "Columbia Family Dentistry", "href": "https://example.com" }
```

Both fields required. `href` should be the sponsor's actual website; use
`"#"` only if the user genuinely doesn't have one yet and says so.

**Important behavior to know**: when this file is `[]`, the entire "Our
Sponsors" section is omitted from `pages/home.html` — not shown as an empty
heading. Adding the first entry makes the section appear automatically;
removing the last entry makes it disappear automatically. This is by
design — don't "fix" it by editing templates.

## Steps

1. Read `config/sponsors.json`.
2. **Adding**: append a new `{ }` entry. Ask for the sponsor's name and website URL if not given.
3. **Editing**: change the relevant field(s) in place.
4. **Removing**: delete the entry.
5. Run `python3 src/build.py`.
6. Run `python3 test/validate_build.py` — confirm it passes.
7. Report that `pages/home.html` changed (mention explicitly if the section just appeared or disappeared for the first time) and remind the user to re-paste it into Google Sites (`docs/SOP.md` Task 8).

## Do not

- Do not edit `src/templates/card-sponsor.html.tmpl`, `sponsors-section.html.tmpl`, or `src/build.py`. If the request needs a sponsor logo image, a tier system (Gold/Silver/Bronze), or different placement, stop and tell the user that's a template change, not a config change, and ask before proceeding.
