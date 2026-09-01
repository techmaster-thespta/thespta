# Thunder Hill Elementary PTA — Website

The Thunder Hill Elementary PTA site is hosted on **Google Sites**, which
has no code editor of its own — pages are built by pasting a block of HTML
into an "Embed code" widget. This repo is the tool that generates those
HTML blocks from plain config files, so the site's content, colors, and
structure can all change without hand-editing HTML.

```
config/*.json          ← edit these: site info, theme, events, board, sponsors, flyers
src/                    ← the generator (templates + build script) — rarely touched
        ↓  python3 src/build.py
pages/*.html            ← generated output, paste into Google Sites
```

## Quickstart

```bash
python3 src/build.py          # regenerate /pages from /config
python3 test/validate_build.py  # check the output is sound
```

No dependencies beyond Python 3 — nothing to install.

On every push to `main`, GitHub Actions does both of those automatically,
then pushes `/pages` and `/assets/images` to a shared Google Drive folder
(see `docs/drive-cicd-setup.md`).

## Making a content change

Almost everything is a config edit — see **`docs/SOP.md`** for the full
task-by-task guide (site info, colors/fonts, board members, events,
sponsors, flyers, images, publishing).

If you're an AI agent, use **`.claude/skills/`** — there's one skill per
kind of addition, each scoped to config-only edits.

## First-time setup

- **`docs/website-setup.md`** — creating the Google Site and getting the 4 pages live
- **`docs/drive-cicd-setup.md`** — wiring GitHub Actions to push to Google Drive

## Repo layout

| Path | What's in it |
|---|---|
| `config/` | All editable site content and settings |
| `src/build.py` | The generator script |
| `src/templates/` | Page structure and reusable component templates |
| `pages/` | Generated HTML — what you paste into Google Sites |
| `assets/images/` | Source images kept in the repo (also pushed to Drive by CI) |
| `scripts/` | `build.sh` (rebuild) and `push_to_drive.py` (used by CI) |
| `test/` | Build validation |
| `docs/` | All setup and maintenance documentation |
| `.github/workflows/` | The build → validate → push-to-Drive CI pipeline |
| `.claude/` | Instructions and skills for AI agents working in this repo |
| `.mcp.json` | GitHub MCP server declaration (token via env var, not committed) — see `docs/github-agent-setup.md` |
