---
name: add-flyer
description: Add, edit, or remove a document/flyer link shown on the About page (bylaws, permission slips, PTA flyers, etc). Config-only — never edit src/.
---

# Add / edit / remove a document or flyer

Use this when the user asks to publish a downloadable document, form, or
flyer (PDF, etc.) — shown in the "Documents & Flyers" section of the About
page.

## File

`config/flyers.json` — a JSON array, empty (`[]`) by default. Each entry:

```json
{ "title": "2026–27 PTA Bylaws", "description": "Our current governing bylaws, last updated August 2026.", "href": "https://drive.google.com/file/d/FILE_ID/view" }
```

All three fields required. `href` must be a Google Drive share link the
file has already been uploaded to (this skill does not upload files) —
the file needs to be shared "Anyone with the link" or it'll be broken for
visitors (same requirement as any image; see `docs/SOP.md` Task 6).

**Important behavior to know**: when this file is `[]`, the entire
"Documents & Flyers" section is omitted from `pages/about.html` — not
shown as an empty heading. This is by design — don't "fix" it by editing
templates.

## Steps

1. Confirm the document is already uploaded to Drive and shared "Anyone with the link" — if not, tell the user to do that first (or do it yourself if you have Drive access in this session) and get the share link before proceeding.
2. Read `config/flyers.json`.
3. **Adding**: append a new `{ }` entry with title, one-sentence description, and the Drive link.
4. **Editing**: change the relevant field(s) in place.
5. **Removing**: delete the entry.
6. Run `python3 src/build.py`.
7. Run `python3 test/validate_build.py` — confirm it passes.
8. Report that `pages/about.html` changed (mention if the section just appeared or disappeared for the first time) and remind the user to push (`docs/SOP.md` Task 7) — GitHub Actions rebuilds and redeploys automatically.

## Do not

- Do not edit `src/templates/card-flyer.html.tmpl`, `flyers-section.html.tmpl`, or `src/build.py`. If the request needs categorization (e.g. separate "Forms" vs "Bylaws" groups), a dedicated Documents page, or file-type icons, stop and tell the user that's a template/structural change, not a config change, and ask before proceeding.
