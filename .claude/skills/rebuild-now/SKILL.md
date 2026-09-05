---
name: rebuild-now
description: Push any pending local changes and force an immediate rebuild/redeploy, instead of waiting for the next scheduled sync or push. Use for last-minute changes the user wants live right away.
---

# Rebuild and deploy right now

Use this when the user wants their latest change on the live site
immediately — a last-minute content edit before an event, a calendar
change they don't want to wait up to an hour for, or just "can you push
this live now" — rather than waiting for the hourly calendar sync
(`.github/workflows/sync-events.yml`), the daily afterschool-flyer sync
(`.github/workflows/sync-afterschool-flyers.yml` and
`scripts/afterschool-review/`), or the normal push-triggered pipeline
(`.github/workflows/deploy.yml`) to get to it on their own.

## Steps

1. **Sync with the Drive folder and pick up the latest afterschool-program
   flyer info first — don't wait for either daily schedule.** Two
   automations normally handle this once a day each; force both to run
   now instead:

   a. **Trigger the mechanical Drive-diff sync right now:**
      ```bash
      gh workflow run sync-afterschool-flyers.yml
      run_id=$(gh run list --workflow=sync-afterschool-flyers.yml --limit 1 --json databaseId --jq '.[0].databaseId')
      gh run watch "$run_id" --exit-status
      ```
      This actually lists the shared Drive folder (`config/site.json`'s
      `afterschool_flyers_folder_id`, via the `GOOGLE_DRIVE_API_KEY`
      secret) and reconciles `config/afterschool-programs.json` against
      it — adds a `needs_review` placeholder for any brand-new flyer,
      removes any that disappeared, flags any changed one (see
      `scripts/sync_afterschool_flyers.py`). It's self-contained like
      `sync-events.yml` — if it finds a change, it commits, rebuilds, and
      deploys on its own already. Pull that down before continuing:
      ```bash
      git pull origin main
      ```

   b. **Run the `review-afterschool-flyers` skill** (checks
      `config/afterschool-programs.json` for anything flagged
      `needs_review` — either just added by step (a) or already flagged
      from before — reads the actual flyer, and fills in the real
      details; see that skill for the full process).

   If either step finds nothing to do, that's a normal, silent no-op —
   move on to step 2. Anything either step changes becomes part of the
   "local changes" step 2 picks up and pushes.

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
