# Thunder Hill Elementary PTA Website

This repo is a static-site generator: `config/*.json` (data) +
`src/templates/*.tmpl` (structure) → `python3 src/build.py` →
`/pages/*.html`. GitHub Actions deploys those pages to **GitHub Pages**
(`https://techmaster-thespta.github.io/thespta/`), and **Google Sites**
embeds each page **by URL** (`Insert → Embed → By URL`) rather than by
pasted code — so a content change is just a config edit + push; nothing
gets re-pasted into Google Sites ever again after initial setup.

## The one rule that matters most

**Content changes are config-only. Do not edit `src/` unless the user
explicitly asks for a structural or design change.**

Every routine addition (a new event, board member, sponsor, flyer) has a
matching skill in `.claude/skills/` — use it. Those skills are deliberately
scoped to touching only `config/*.json`, because:

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

If a task genuinely needs a template/build.py change (a new page, a new
section type nothing existing covers), say so explicitly and explain why a
config-only approach can't do it, rather than silently editing `src/`.

## Hard-won constraints (don't reintroduce these mistakes)

- **No custom header/nav/footer duplicating Google Sites' own** — except
  the footer, which Sites has no native equivalent for, so we build one
  (`src/templates/footer.html.tmpl`). Never add a second nav bar.
- **Mobile-safety**: every grid uses `auto-fit`/`minmax(...)`, never a
  fixed multi-breakpoint layout. Avoid `position: absolute` outside the
  two already-vetted uses (the banner/header fade overlay, the calendar
  iframe's aspect-ratio box). Avoid fixed pixel widths on containers. A
  from-scratch redesign broke on mobile once already from ignoring this.
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
  between pages** — each value is a *slug* (e.g. `"get-involved"`), not a
  full URL. `src/build.py` prefixes `google_sites_base_url` onto it, so
  links point at the page's Google Sites sub-page rather than the raw
  GitHub Pages URL — this keeps a visitor inside Google Sites' own
  nav/header/footer shell after clicking. The convention: a Google Sites
  sub-page's name always matches its generated HTML file's name (minus
  `.html`). See `docs/website-setup.md` → "Two different URLs, two
  different jobs" before changing any of this. Never hardcode a relative
  path like `/events`, and never point `page_urls.*` at a GitHub Pages URL
  directly.

## Commands

```bash
python3 src/build.py            # regenerate /pages from /config
python3 test/validate_build.py  # validate the output (also runs in CI)
scripts/build.sh                # same as the first command, path-independent
```

## Where things are documented

- `docs/SOP.md` — day-to-day content-editing tasks (the thing to read first for "how do I change X")
- `docs/github-pages-setup.md` — one-time: turning on GitHub Pages for this repo
- `docs/website-setup.md` — one-time: creating the Google Site, embedding
  the 4 pages by URL, and the slug convention for adding a new page later
- `.claude/skills/` — one skill per addable content type (`add-event`,
  `add-board-member`, `add-sponsor`, `add-flyer`), plus the GitHub
  issue workflow: `create-issue` (plan a change collaboratively, file it)
  and `from-issue` (pull an issue by number, implement it, open a PR).
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
