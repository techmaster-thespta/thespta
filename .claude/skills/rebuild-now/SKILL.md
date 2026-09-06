---
name: rebuild-now
description: Push any pending local changes and force an immediate rebuild/redeploy, instead of waiting for the next scheduled sync or push. Use for last-minute changes the user wants live right away.
---

# Rebuild and deploy right now

Use this when the user wants their latest change on the live site
immediately — a last-minute content edit before an event, a calendar
change they don't want to wait up to an hour for, or just "can you push
this live now" — rather than waiting for the hourly calendar sync
(`.github/workflows/sync-events.yml`), the daily flyer syncs
(`.github/workflows/sync-afterschool-flyers.yml`,
`.github/workflows/sync-fundraiser-flyers.yml`, and
`scripts/flyer-review/`), or the normal push-triggered pipeline
(`.github/workflows/deploy.yml`) to get to it on their own.

## Steps

1. **Sync with both Drive folders and pick up the latest flyer info
   first — don't wait for the daily schedule.** Two flyer-backed content
   types exist (afterschool programs, fundraisers), each with its own
   mechanical Drive-diff sync workflow and its own review skill; force
   all four to run now instead of waiting:

   a. **Trigger both mechanical Drive-diff syncs right now:**
      ```bash
      gh workflow run sync-afterschool-flyers.yml
      gh workflow run sync-fundraiser-flyers.yml
      run_id_a=$(gh run list --workflow=sync-afterschool-flyers.yml --limit 1 --json databaseId --jq '.[0].databaseId')
      run_id_f=$(gh run list --workflow=sync-fundraiser-flyers.yml --limit 1 --json databaseId --jq '.[0].databaseId')
      gh run watch "$run_id_a" --exit-status
      gh run watch "$run_id_f" --exit-status
      ```
      Each actually lists its shared Drive folder (`config/site.json`'s
      `afterschool_flyers_folder_id` / `fundraiser_flyers_folder_id`,
      via the `GOOGLE_DRIVE_API_KEY` secret) and reconciles its config
      file against what's really there — adds a `needs_review`
      placeholder for a brand-new flyer, flags a changed one, and
      removes/detaches one that disappeared (see
      `scripts/sync_afterschool_flyers.py` and
      `scripts/sync_fundraiser_flyers.py` — the two differ in one real
      way: a fundraiser campaign isn't flyer-dependent the way an
      afterschool program is, and a new fundraiser flyer is often a
      reprint of an existing campaign rather than a new one, so that
      script also makes a conservative filename match before creating a
      placeholder). Both are self-contained like `sync-events.yml` — if
      either finds a change, it commits, rebuilds, and deploys on its
      own already. Pull that down before continuing:
      ```bash
      git pull origin main
      ```

   b. **Run the `review-afterschool-flyers` and `review-fundraiser-flyers`
      skills** (each checks its own config file for anything flagged
      `needs_review` — either just added by step (a) or already flagged
      from before — reads the actual flyer, and fills in the real
      details, merging a reprinted fundraiser flyer into its existing
      campaign rather than duplicating it; see each skill for its full
      process).

   If a step finds nothing to do, that's a normal, silent no-op — move
   on to step 2. Anything any step changes becomes part of the "local
   changes" step 2 picks up and pushes.

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
