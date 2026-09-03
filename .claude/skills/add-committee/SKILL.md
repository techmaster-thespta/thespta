---
name: add-committee
description: Add, edit, or remove a PTA committee shown on the Get Involved > Committees page. Config-only — never edit src/.
---

# Add / edit / remove a committee

Use this when the user asks to add a new committee, change a chair,
change a committee's status, or remove one — all 10 (or however many)
committees live on **one** page (`/get-involved/committees`), each as its
own card. There is no per-committee page or URL — never create one.

## File

`config/committees.json` — a JSON array. Each entry:

```json
{
  "name": "Hospitality",
  "slug": "hospitality",
  "status": "chair-needed",
  "chair": null,
  "description": "One sentence describing what this committee does.",
  "activities": ["A few", "concrete examples", "of what it actually does"],
  "audiences": ["staff"],
  "volunteerValue": "Hospitality"
}
```

- `status` is exactly `"chair-needed"` or `"members-welcome"` — this
  controls both the badge shown and which of the two sections on the
  page the card appears in.
- `chair` is `null` for a `chair-needed` committee, or the chair's name
  (string) for a `members-welcome` one. The card only shows a "Chair:"
  line when this is set.
- `activities` is a short list (2-5 items) shown in the card's "Learn
  More" expandable detail — keep them concrete and grounded in the
  `description`, don't invent activities not implied by it.
- `audiences` is any subset of `["students", "families", "staff"]` —
  informational for now (not yet rendered anywhere), but keep it
  reasonably accurate to the committee's actual focus.
- `volunteerValue` is the exact text pre-filled into the shared Google
  Form's committee field when someone clicks that card's volunteer
  button — normally just the committee's `name`, but kept separate in
  case the form field expects different wording than the display name.
- `slug` is a unique, URL-safe-looking identifier (not currently used as
  a real URL — there are no per-committee URLs — but keep it unique and
  stable in case that changes later).

## Steps

1. Read `config/committees.json`.
2. **Adding**: append a new `{ }` entry. Ask for the fields above if not
   given — don't invent a chair's name, a description, or activities not
   actually stated.
3. **Editing**: change the relevant field(s) in place. Moving a committee
   from "chair-needed" to "members-welcome" (or back) just means changing
   `status` (and setting/clearing `chair`) — it automatically moves
   between the two sections on the page, no other change needed.
4. **Removing**: delete the entry.
5. Run `python3 src/build.py`.
6. Run `python3 test/validate_build.py` — confirm it passes (note: this
   validates every page recursively, including the nested
   `pages/get-involved/committees.html` — don't be surprised it's not at
   the top level of `/pages`).
7. Report that `pages/get-involved/committees.html` changed and remind
   the user to push (`docs/SOP.md` Task 7) — GitHub Actions rebuilds and
   redeploys automatically.

## Do not

- Do not create a new page, template, or URL for an individual committee
  — the whole point of this structure is one reusable page for all of
  them. If asked to do this, stop and explain why (per the user's own
  explicit spec for this feature) rather than doing it.
- Do not edit `src/templates/committees-section.html.tmpl`,
  `src/templates/pages/get-involved/committees.html.tmpl`, or
  `render_committee_card`/`build_committees_section` in `src/build.py`.
  If the request needs a different card layout or a new field, stop and
  tell the user that's a template change, not a config change.
- Do not touch `config/site.json`'s `volunteerForm` block for a routine
  committee edit — that's the shared Google Form config, unrelated to
  any individual committee (see `docs/SOP.md` for what it controls and
  how to set the real values once a form exists).
