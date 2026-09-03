# Thunder Hill Elementary PTA Website

This repo is a static-site generator: `config/*.json` (data) +
`src/templates/*.tmpl` (structure) → `python3 src/build.py` →
`/pages/*.html`. GitHub Actions builds and deploys those pages straight
to **GitHub Pages**, served at the custom domain in `config/site.json`'s
`custom_domain` field (currently `www.thespta.org`) via a generated
`CNAME` file — self-hosted, no Google Sites embedding. A content change
is just a config edit + push.

**Staging**: `techmaster-thespta/thespta-prestage` is a separate repo
that mirrors this one for previewing changes before they hit production,
live at `https://techmaster-thespta.github.io/thespta-prestage/`. See
the `rebuild-now` skill's pattern for pushing this repo's current branch
there and redeploying.

## The one rule that matters most

**Content changes are config-only. Do not edit `src/` unless the user
explicitly asks for a structural or design change.**

Every routine addition (a board member, sponsor, flyer) has a matching
skill in `.claude/skills/` — use it. Those skills are deliberately scoped
to touching only `config/*.json`, because:

- `src/templates/` defines the visual system (the "thes" design language:
  navy/blue/yellow/teal/coral, Montserrat + Lato, card/grid patterns).
  Changing it changes the whole site's look, not just one piece of content.
- `src/build.py` is the assembly logic. It's had several rounds of
  deliberate simplification after real mobile-rendering bugs — see
  "Hard-won constraints" below before touching it.
- Config files are safe to edit freely: worst case, re-run the build and
  the site looks the same as before, or a section quietly doesn't render
  (sponsors/flyers with an empty list produce no section at all — this is
  intentional, not a bug).

**Events are the one exception to "config-only"**: they're synced
automatically from Google Calendar by `scripts/sync_calendar_events.py`
(GitHub Actions runs it hourly via `.github/workflows/sync-events.yml`,
and again on every push via `deploy.yml`) — `config/events.json` is
*generated*, like `pages/*.html`, never hand-edited. See
`.claude/skills/add-event/` and `docs/SOP.md` Task 4.

The **nav menu** is also config, not template: `config/site.json`'s
`nav` list drives the header — see "Adding a page to the nav" below.

If a task genuinely needs a template/build.py change (a new page, a new
section type nothing existing covers), say so explicitly and explain why a
config-only approach can't do it, rather than silently editing `src/`.

## Hard-won constraints (don't reintroduce these mistakes)

- **No page can omit the header — it's structural, not a template
  convention.** `build.py`'s `main()` inserts the header right after
  `<div class="thes">` opens, for every page, unconditionally — no page
  template includes a `{{HEADER}}` marker to remember. This exists
  because a real page (the newsletter page) shipped without a header
  once: it was written before this repo had a header concept, and a
  later merge didn't retroactively add a marker nothing enforced.
  Don't reintroduce a marker-based header; if the header needs to change,
  edit `src/templates/header.html.tmpl` or `build_header()`.
- **Every generated page needs its own `<!DOCTYPE html>`/`<head>`/viewport
  meta — these pages are opened directly, not embedded inside another
  page that supplies one.** `build.py`'s `main()` wraps every page in a
  real document shell for exactly this reason. Skipping the viewport meta
  specifically silently breaks every `@media` query meant for phones —
  without it, mobile browsers assume a fake ~980px desktop-width layout
  viewport regardless of the device's real width. This already caused a
  real bug (the mobile hamburger menu never triggered on an actual phone)
  before the fix.
- **The header/nav is the site's one piece of JS-driven UI** — the
  hamburger button and each dropdown nav item's caret are real
  `<button>`s that toggle a plain `.is-open` class via
  `addEventListener` (see the `<script>` in `header.html.tmpl`, appended
  right after the header markup by `build_header()` so it ships on every
  page the same way the header itself does). This replaced an earlier
  pure-CSS checkbox-hack version after that version shipped a real bug:
  a touch tap on a parent nav link (e.g. "Get Involved") could trigger
  `:focus-within` and pop its submenu open with no way to distinguish
  that from a deliberate caret tap, and a user reported the submenu
  showing "from the beginning" with the caret doing nothing. The rest of
  the site has no other JS, and there's no framework/bundler — if you add
  more interactive UI, keep it as plain inline `<script>` in the relevant
  template, following this same pattern.
- **Mobile-safety**: every grid uses `auto-fit`/`minmax(...)`, never a
  fixed multi-breakpoint layout. Avoid `position: absolute` outside the
  three already-vetted uses (the header dropdown submenu, the page-header
  fade overlay, the calendar iframe's aspect-ratio box). Avoid fixed pixel
  widths on containers. A from-scratch redesign broke on mobile once
  already from ignoring this.
- **Images live in `assets/images/` and are served directly by GitHub
  Pages** (`config/site.json` → `hero_image_filename` /
  `page_header_image_filename`, resolved to a relative `images/<file>`
  URL by `src/build.py`). This replaced an earlier Google-Drive-hosted
  approach — don't reintroduce Drive for images or page hosting. A
  service-account-based Drive push was tried and abandoned: service
  accounts have zero storage quota on a plain Gmail "My Drive," so every
  upload failed with `storageQuotaExceeded` regardless of folder sharing.
  An OAuth-as-the-user variant was made to work, but GitHub Pages is
  simpler and was chosen instead — don't re-add either Drive approach.
- **`page_urls.*` in `config/site.json` are the only correct way to link
  between pages** — each value is a *slug* (e.g. `"get-involved"`, or
  `"get-involved/committees"` for a nested page), not a full URL.
  `src/build.py` appends `.html` and, for a page that itself lives below
  the site root, prefixes the right number of `../` so the link still
  resolves correctly from that depth (see "Nested pages" below). Never
  hardcode an absolute path (`/events.html`) or a full URL into
  `page_urls.*` — an absolute path breaks the moment a site is served
  from a URL subpath instead of a domain root, which is exactly how the
  `thespta-prestage` staging repo is hosted
  (`techmaster-thespta.github.io/thespta-prestage/`).
- **Nested pages (a page below the site root, e.g.
  `pages/get-involved/committees.html`) need relative links built with
  the right `../` depth — this is what `build_context(depth)` in
  `build.py` is for.** `main()` discovers page templates recursively
  (`(TEMPLATES / "pages").rglob("*.html.tmpl")`), computes each one's
  `depth` from how many directories deep it lives under
  `src/templates/pages/`, and calls `build_context(depth)` (memoized per
  depth, since header/footer/nav links depend on it but content like
  board/event/committee cards don't) — that's what prefixes every
  `page_urls.*` value and the hero/page-header image URLs with the right
  number of `"../"`. If you add another nested page, it gets this for
  free just by living in a subdirectory of `src/templates/pages/`; you
  don't need to touch `build_context` or `main()`. This was built
  because root-absolute paths (`/get-involved.html`) would have been
  simpler but silently broken on the staging repo's subpath hosting —
  relative paths work at both.
  Two real bugs already got caught by this depth change and are worth
  knowing about if you touch page discovery or deployment again:
  `test/validate_build.py` used to glob `pages/*.html` (flat) and would
  silently skip any nested page during validation; and
  `deploy.yml`/`sync-events.yml`'s "Assemble the deployed site" step used
  to `cp pages/*.html site/` (also flat), which would have silently
  **failed to deploy** a nested page even though it built and validated
  fine locally. Both are now recursive (`glob(..., recursive=True)` and
  `cp -r pages/. site/` respectively) — if you ever see a nested page
  validate locally but 404 live, a flat glob/cp regression is the first
  thing to check.
- **Any new colored link/button variant must combine classes, not rely on
  a single one for color** — `.thes a { color: inherit; }` in
  `tokens.html.tmpl` has specificity (0,1,1), which beats a single-class
  selector like `.thes__btn--green { color: ... }` (0,1,0) regardless of
  source order. This exact bug shipped once already: `.thes__btn--navy`
  buttons rendered near-black inherited text instead of white. The fix in
  place is `.thes__btn.thes__btn--navy { ... }` (two classes, specificity
  0,2,0) — follow that pattern for any new button/link color rule.
- **A GitHub-Actions-bot push never triggers another workflow's `push`
  trigger** — this is deliberate loop-prevention baked into `GITHUB_TOKEN`
  (see [GitHub's docs](https://docs.github.com/en/actions/concepts/security/github_token)),
  not a bug to work around with a PAT. This is why
  `.github/workflows/sync-events.yml` does its own full build+validate+deploy
  instead of just committing `config/events.json` and counting on
  `deploy.yml`'s push trigger to pick it up — that handoff would silently
  never fire. Keep this in mind before adding any other bot-committing
  workflow that's meant to cascade into another one.
- **`config/site.json`'s `custom_domain` generates the `CNAME` file
  GitHub Pages needs for the custom domain to work** — `build.py` writes
  `pages/CNAME` from it, and `deploy.yml`/`sync-events.yml` both copy that
  into the deployed `site/`. If the domain ever changes, update
  `custom_domain` and the DNS record pointing at GitHub Pages — don't
  hand-maintain a separate CNAME file, it'll drift.

## Commands

```bash
python3 src/build.py            # regenerate /pages from /config
python3 test/validate_build.py  # validate the output (also runs in CI)
scripts/build.sh                # same as the first command, path-independent
```

## Adding a page to the nav

Edit `config/site.json`'s `nav` list — each item is
`{"label": "...", "page_url": "<a page_urls.* key>"}`. Any item can carry
a `"children": [...]` list (same shape) to become a dropdown/subpage menu
— desktop shows it on hover, mobile lists it indented inside the already-
open mobile menu. This is data, not a template change: adding a subpage
never requires touching `header.html.tmpl` or `build.py`.

## Where things are documented

- `docs/SOP.md` — day-to-day content-editing tasks (the thing to read first for "how do I change X")
- `docs/github-pages-setup.md` — one-time: turning on GitHub Pages and the custom domain for this repo
- `.claude/skills/` — one skill per addable content type (`add-event`,
  `add-board-member`, `add-sponsor`, `add-flyer`, `add-committee`), the GitHub issue
  workflow (`create-issue` to plan a change and file it, `from-issue` to
  pull an issue by number, implement it, open a PR), `rebuild-now`
  (push pending changes + force an immediate rebuild/redeploy, for
  last-minute changes the user wants live right away rather than waiting
  on the hourly sync or normal push pipeline), and `release` (verify
  `main`, bump `VERSION`, write a board-friendly `CHANGELOG.md` entry,
  cut a tagged GitHub Release — only when the user actually asks for one,
  not automatically on every change).
- `VERSION` / `CHANGELOG.md` — the site's version number and a
  plain-language changelog meant to be shared with the PTA board, not
  just developers. Both only ever move together, via the `release` skill
  — don't hand-edit either mid-change.
- `scripts/sync_calendar_events.py` — generates `config/events.json` from
  the public Google Calendar `.ics` feed (stdlib-only RRULE expansion, no
  API key), including any file attached to an event (rendered as a
  clickable photo preview — confirmed empirically that Google's public
  feed includes `ATTACH` properties). Run by
  `.github/workflows/sync-events.yml` (hourly) and by `deploy.yml` (every
  push/manual run). See `docs/SOP.md` Task 4.
- `docs/github-agent-setup.md` — GitHub access setup for agents: `gh` CLI
  (shell-capable agents) or the GitHub MCP server declared in `.mcp.json`
  (any MCP-compatible agent). Use whichever this session actually has —
  the skills describe `gh` commands as the reference implementation; an
  MCP-only agent should translate the same intent into MCP tool calls.

## Adding a new modular content type

Sponsors and flyers (`config/sponsors.json`, `config/flyers.json`) are the
reference pattern for "a list of things that may be empty." If asked to add
another one (e.g. a photo gallery, a testimonials section):

1. Add `config/<name>.json` defaulting to `[]`.
2. Add `src/templates/card-<name>.html.tmpl` (one item).
3. Add `src/templates/<name>-section.html.tmpl` (the section wrapper, taking a `{{<NAME>_CARDS}}` marker).
4. Wire it into `build_optional_section(...)` in `src/build.py` and add the `{{<NAME>_SECTION}}` marker to whichever page template it belongs on.
5. Confirm an empty config produces no section (not an empty heading) — this is the pattern's whole point.
6. Add a matching skill under `.claude/skills/add-<name>/SKILL.md`.

This is itself a `src/` change — get explicit user sign-off before doing it,
per the rule above.
