# Thunder Hill Elementary PTA — Website

The live site is fully self-hosted on **GitHub Pages** at
`www.thespta.org` — a content change is just a config edit + push. This
repo is the generator: plain config files in, complete static HTML pages
out.

```
Google Calendar         ← events — edit here, not in this repo (see docs/SOP.md Task 4)
        ↓  scripts/sync_calendar_events.py (hourly + on push)
config/*.json           ← edit the rest of these: site info, theme, board, sponsors, flyers, nav
src/                    ← the generator (templates + build script) — rarely touched
        ↓  python3 src/build.py
pages/*.html            ← generated output (including pages/CNAME for the custom domain)
        ↓  git push → GitHub Actions
https://www.thespta.org/*.html   ← the live site
```

## Quickstart

```bash
python3 src/build.py            # regenerate /pages from /config
python3 test/validate_build.py  # check the output is sound
```

No dependencies beyond Python 3 — nothing to install.

On every push to `main`, GitHub Actions does both of those automatically,
then deploys the result to GitHub Pages (see `docs/github-pages-setup.md`).

**Staging**: `techmaster-thespta/thespta-prestage` is a separate repo
that mirrors this one for previewing changes before they hit production,
live at `https://techmaster-thespta.github.io/thespta-prestage/`.

## Making a content change

Almost everything is a config edit — see **`docs/SOP.md`** for the full
task-by-task guide (site info, colors/fonts, board members, events,
sponsors, flyers, images, publishing).

If you're an AI agent, use **`.claude/skills/`** — there's one skill per
kind of addition, each scoped to config-only edits.

## First-time setup

- **`docs/github-pages-setup.md`** — turning on GitHub Pages and pointing the custom domain at it

## Repo layout

| Path | What's in it |
|---|---|
| `config/` | All editable site content and settings |
| `src/build.py` | The generator script |
| `src/templates/` | Page structure and reusable component templates |
| `pages/` | Generated HTML — deployed to GitHub Pages by CI |
| `assets/images/` | Source images, served directly by GitHub Pages |
| `scripts/` | `build.sh` (rebuild locally), `sync_calendar_events.py` (pull events from Google Calendar into `config/events.json`) |
| `test/` | Build validation |
| `docs/` | All setup and maintenance documentation |
| `.github/workflows/` | `deploy.yml` (build → validate → deploy-to-Pages, on push), `sync-events.yml` (hourly calendar sync) |
| `.claude/` | Instructions and skills for AI agents working in this repo |
| `.mcp.json` | GitHub MCP server declaration (token via env var, not committed) — see `docs/github-agent-setup.md` |
| `VERSION` / `CHANGELOG.md` | The site's version and a plain-language changelog, shareable with the PTA board — see the `release` skill |
