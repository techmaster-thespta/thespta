---
name: add-family-support-resource
description: Add, edit, or remove a resource card on the Family Support Resources landing page. Config-only for a plain resource card — a resource that needs its own page (like the special-education calendar) is a template/build.py change instead.
---

# Add / edit / remove a family support resource

Use this for a Howard County or community resource worth pointing
Thunder Hill families to, that the PTA doesn't run itself — this is
what distinguishes this page from Events (PTA-run, synced from the
PTA's own calendar) and PTA Meetings (PTA-run, recap flyers after the
fact). "Family Support Resources" is a landing page of cards; each card
either links straight out to an external resource, or to a dedicated
page on this site for a resource substantial enough to need one (the
first example: the HCPSS Special Education Parent & Guardian Calendar).

## File

`config/family-support-resources.json` — a JSON array. Each entry:

```json
{ "title": "Special Education & Family Support", "description": "One sentence.", "page_url": "special_education_family_support" }
```

or, for a resource that's just an outbound link with no page of its own:

```json
{ "title": "Some County Program", "description": "One sentence.", "href": "https://example.com/program" }
```

- `title` / `description` are required — keep the description to one
  real sentence, describing what the resource actually is/does, not
  PTA marketing copy.
- Give the card **either** `page_url` (a key already present in
  `config/site.json`'s `page_urls`, for a resource with its own page on
  this site) **or** `href` (a full external URL, opens in a new tab) —
  not both. Don't invent a `page_url` that doesn't exist in `site.json`
  yet; that's a template change (see below).

Order in the file is display order (grid, left-to-right/top-to-bottom).

## Steps

1. Read `config/family-support-resources.json`.
2. **Adding an external-link card**: append `{ "title": ..., "description": ..., "href": ... }`. Don't guess a URL — ask the user or read the source page yourself, and verify it actually resolves (some HCPSS URLs redirect or get restructured) before using it.
3. **Editing**: change the relevant field(s) in place.
4. **Removing**: delete the entry.
5. Run `python3 src/build.py` then `python3 test/validate_build.py`.
6. Report that `pages/family-support-resources.html` changed and remind the user to push (`docs/SOP.md` Task 7).

## Adding a resource that needs its own page

The HCPSS Special Education Parent & Guardian Calendar
(`src/templates/pages/family-support-resources/special-education-family-support.html.tmpl`)
is the reference example: a resource substantial enough to deserve a
full page (a live calendar embed, reference links) rather than just a
card linking out. This is a `src/` change:

1. Add a nested page template under `src/templates/pages/family-support-resources/`.
2. Add its slug to `config/site.json`'s `page_urls` (e.g. `"special_education_family_support": "family-support-resources/special-education-family-support"`).
3. Add its title to `PAGE_TITLES` and a real description to `PAGE_DESCRIPTIONS` in `src/build.py`.
4. Add a `config/family-support-resources.json` entry with `"page_url"` pointing at that new `page_urls` key, so it gets a card on the landing page.
5. If it should also appear directly in the nav dropdown (not just as a card), add it to `config/site.json`'s `nav` — the "Family Support Resources" entry's `children` list, same pattern as "Get Involved" → "Committees".

Get explicit user sign-off before doing this, per `.claude/CLAUDE.md`'s
"Adding a new modular content type" rule — a plain resource card
(external link or linking to an *existing* page) doesn't need it, a new
page does.

## Do not

- Do not edit `src/templates/family-support-resources-section.html.tmpl`,
  `src/templates/card-family-support-resource.html.tmpl`, or
  `build_family_support_resources_section()` in `src/build.py` for a
  routine card add/edit/remove — that's all config.
- Do not invent a URL for an external resource. Ask, or verify the real
  one yourself — HCPSS in particular has restructured/redirected some
  of its own special-education pages before.
- Do not add a `page_url` to a card unless that page actually exists in
  `config/site.json`'s `page_urls` and has a built template — a card
  linking to a non-existent page is a broken link on the live site.
