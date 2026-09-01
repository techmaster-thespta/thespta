# Thunder Hill Elementary PTA Website

This repo generates the HTML pasted into a **Google Sites** site (which has
no code editor of its own — content goes in via "Insert → Embed → Embed
code" blocks). It is a static-site generator: `config/*.json` (data) +
`src/templates/*.tmpl` (structure) → `python3 src/build.py` → `/pages/*.html`
(what actually gets pasted).

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
- **Images are Drive-hosted, not embedded as base64**, except when a user
  explicitly asks for a fully self-contained embed. Drive links use
  `https://lh3.googleusercontent.com/d/{FILE_ID}` (more reliable for
  hotlinking than `drive.google.com/uc?export=view`). The Drive folder
  they live in must stay shared "Anyone with the link" — see
  `docs/drive-cicd-setup.md`.
- **`page_urls.*` in `config/site.json` are the only correct way to link
  between pages.** Never hardcode a relative path like `/events` — Google
  Sites' actual published URL structure doesn't reliably support that.

## Commands

```bash
python3 src/build.py            # regenerate /pages from /config
python3 test/validate_build.py  # validate the output (also runs in CI)
scripts/build.sh                # same as the first command, path-independent
```

## Where things are documented

- `docs/SOP.md` — day-to-day content-editing tasks (the thing to read first for "how do I change X")
- `docs/website-setup.md` — one-time Google Sites setup
- `docs/drive-cicd-setup.md` — one-time GitHub Actions → Google Drive setup
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
