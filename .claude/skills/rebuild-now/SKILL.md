---
name: rebuild-now
description: Push any pending local changes and force an immediate rebuild/redeploy, instead of waiting for the next scheduled sync or push. Use for last-minute changes the user wants live right away.
---

# Rebuild and deploy right now

Use this when the user wants their latest change on the live site
immediately — a last-minute content edit before an event, a calendar
change they don't want to wait up to an hour for, or just "can you push
this live now" — rather than waiting for the hourly calendar sync
(`.github/workflows/sync-events.yml`), the daily flyer-review service
(`scripts/flyer-review/`), or the normal push-triggered pipeline
(`.github/workflows/deploy.yml`) to get to it on their own.

Note: the flyer *mechanical* sync itself (detecting a new/changed/
removed file in `assets/flyers/before-after-school/` or
`assets/flyers/fundraising/`) is no longer something to force — it runs
as a step inside `deploy.yml` on every push already, immediate by
construction, not on a daily poll (these used to be Drive-hosted and
polled daily; moved into the repo after the Drive account got flagged).
What's still worth forcing is the *review* step — reading a flagged
flyer and writing its real details — since that's a judgment call that
only happens when this skill or the daily service runs it.

## Steps

1. **Run the `review-afterschool-flyers` and `review-fundraiser-flyers`
   skills first, before pushing anything else — don't wait for the
   daily service.** Each checks its own config file for anything
   flagged `needs_review` (from a flyer uploaded since the last review
   ran), reads the actual flyer, and fills in the real details — merging
   a reprinted fundraiser flyer into its existing campaign rather than
   duplicating it; see each skill for its full process. If a skill finds
   nothing to do, that's a normal, silent no-op — move on to step 2.
   Anything either skill changes becomes part of the "local changes"
   step 2 picks up and pushes.

2. **Check for local changes:**
   ```bash
   git status --short
   ```
   - If there are uncommitted changes the user wants included, stage,
     commit, and push them (see `docs/SOP.md` Task 7). A push to `main`
     triggers `deploy.yml` on its own — most of the time that's all this
     skill needs to do.
   - If everything is already pushed and the user just wants to force a
     fresh rebuild/redeploy right now (e.g. to pick up a calendar change
     immediately instead of waiting for the hourly sync), skip straight
     to step 3.

3. **Trigger the workflow manually:**
   ```bash
   gh workflow run deploy.yml
   ```
   This re-runs the full pipeline (sync calendar → build → validate →
   deploy) against whatever is currently on `main`, regardless of whether
   anything actually changed.

4. **Watch it to completion — don't just fire and report success:**
   ```bash
   run_id=$(gh run list --workflow=deploy.yml --limit 1 --json databaseId --jq '.[0].databaseId')
   gh run watch "$run_id" --exit-status
   ```
   If it fails, read the failing step's log (`gh run view "$run_id" --log-failed`)
   and fix the underlying issue rather than re-running blindly.

5. **Verify it's actually live**, don't just trust the green checkmark —
   this repo has a history of GitHub Pages reporting a successful deploy
   while still serving stale/broken content (see
   `docs/github-pages-setup.md` → "Workflow is green but the live URL
   404s"). Spot-check with curl against the specific thing that changed,
   e.g.:
   ```bash
   curl -s https://techmaster-thespta.github.io/thespta/events.html | grep "whatever changed"
   ```

## Do not

- Do not use this to make the actual content change — that's whichever
  other skill fits (`add-board-member`, `add-sponsor`, `add-flyer`,
  `add-event`) or a direct `config/*.json` edit. This skill is purely
  about forcing the publish step to happen now instead of later.
- Do not skip step 5. A workflow run reporting success is not the same as
  confirming the live site changed — verify with an actual request
  against the live URL.
