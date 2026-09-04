---
name: review-afterschool-flyers
description: Check config/afterschool-programs.json for entries flagged needs_review, read their actual flyer, and fill in the real program details. Used both interactively and by the headless daily automation in scripts/afterschool-review/.
---

# Review flagged afterschool-program flyers

Use this when asked to "check for flyers needing review," "review the
afterschool programs," or when running non-interactively via
`scripts/afterschool-review/run.sh`'s scheduled systemd timer (see
`docs/automation-service.md`) — this skill is what that automation
actually invokes; it has no separate instructions of its own.

`.github/workflows/sync-afterschool-flyers.yml` runs daily and
mechanically detects new/removed/changed flyers in the shared Drive
folder — see `.claude/skills/add-afterschool-program/`. What it *can't*
do is read a flyer to write its real program details; that's this
skill's whole job.

If invoked non-interactively (no human present to answer questions or
approve actions): complete the task fully and exit, making the
reasonable call on anything ambiguous and noting it in the final
summary instead of asking.

## Steps

1. `git status` — if the working tree isn't clean, stop and do nothing
   further. Leave it for a human to look at; don't overwrite anything.
2. `git fetch origin main && git pull origin main` to get the latest.
3. Read `config/afterschool-programs.json`. Find every entry with
   `"needs_review": true`.
4. If there are none, report "No flyers need review today" and stop —
   that's the normal, expected outcome most days, not an error.
5. For each flagged entry, open its flyer — either
   `https://drive.google.com/file/d/<flyer_drive_file_id>/view` or the
   thumbnail `https://drive.google.com/thumbnail?id=<flyer_drive_file_id>&sz=w1200`
   — and actually read what it says. Fill in real values for `name`,
   `provider`, `description`, `day_time`, `date_range` (or `sessions`
   for a multi-session program — see the KidzArt entry in the same file
   for that shape), `grades`, `price`, `contact`, `registration_href`,
   and/or `registration_note`, matching the field reference in
   `.claude/skills/add-afterschool-program/SKILL.md`. Do not invent
   details the flyer doesn't actually show — leave a field `null` if
   it's genuinely not on the flyer. Set `"needs_review": false`.
6. Run `python3 src/build.py`, then `python3 test/validate_build.py`.
   If validation fails, fix the underlying issue and re-run rather than
   skipping it.
7. `git add config/afterschool-programs.json pages/`, commit with a
   clear message (e.g. "chore: fill in reviewed afterschool program
   flyer details"), and `git push origin main`. This is routine content
   fill, not a design change — push directly to `main`, no staging-first
   step needed (matches how the automated Drive-diff sync itself already
   commits directly to main).
8. Verify, don't just trust a green checkmark: `gh run list
   --workflow=deploy.yml --limit 1`, then `gh run watch <id>
   --exit-status` to confirm the push's deploy actually succeeded, then
   `curl` the live `https://www.thespta.org/afterschool-programs.html`
   page to confirm the new content is actually there.
9. Report a short summary: how many entries were reviewed/filled in
   (name each one), or that there was nothing to do.

## Do not

- Do not touch the `thespta-prestage` (staging) repo — it has its own
  independent daily Drive sync and may flag the same flyer separately;
  that's expected drift for routine content, not something to fix here.
- Do not hand-write `content_hash` — it's bookkeeping the mechanical
  sync owns; only `needs_review` and the actual content fields are
  yours to edit here.
