---
name: review-fundraiser-flyers
description: Check config/fundraisers.json for entries flagged needs_review, read their actual flyer, and either fill in a brand-new campaign's details or merge a reprinted flyer into the existing campaign it actually belongs to. Used both interactively and by the headless daily automation in scripts/flyer-review/.
---

# Review flagged fundraiser flyers

Use this when asked to "check for fundraiser flyers needing review," or
when running non-interactively via `scripts/flyer-review/run.sh`'s
scheduled systemd timer (see `docs/automation-service.md`) — this skill
is what that automation actually invokes for the fundraising side; it
has no separate instructions of its own.

`scripts/sync_fundraiser_flyers.py` runs as a step in
`.github/workflows/deploy.yml` on every push and mechanically detects
new/removed/changed flyers in `assets/flyers/fundraising/`. It does one extra thing
`sync_afterschool_flyers.py` doesn't: a cheap filename-vs-campaign-name
guess, so an obviously-matching reprint (e.g. "Raise-Right.jpg" against
the existing "RaiseRight Gift Cards" card) gets attached automatically
instead of creating a duplicate. That guess is deliberately
conservative — a plain substring check, nothing that requires actually
looking at the image — so it under-matches rather than over-matches.
**This skill is what resolves the cases it couldn't**, and it's a real
possibility here in a way it mostly isn't for afterschool programs: a
new flyer in this folder is *often* a reprint of a campaign that
already exists on the page, not a new one. (This actually happened: a
flyer named "buy-a-box.jpg" turned out to be the See's Candies flyer —
nothing in the filename says so, only the image itself does.)

If invoked non-interactively (no human present to answer questions or
approve actions): complete the task fully and exit, making the
reasonable call on anything ambiguous and noting it in the final
summary instead of asking.

## Steps

1. `git status` — if the working tree isn't clean, stop and do nothing
   further. Leave it for a human to look at; don't overwrite anything.
2. `git fetch origin main && git pull origin main` to get the latest.
3. Read `config/fundraisers.json`. Find every entry with
   `"needs_review": true`.
4. If there are none, report "No fundraiser flyers need review today"
   and stop — that's the normal, expected outcome most days, not an
   error.
5. For each flagged entry, open its flyer —
   `assets/flyers/fundraising/<flyer_filename>` (or ask an agent to) —
   and actually look at it. Two cases:

   - **The flyer is for a campaign that's already a different entry in
     this file** (the sync script's placeholder name is a generic
     filename guess like "Buy A Box" but the flyer is obviously, say,
     the See's Candies fundraiser that already has its own card): move
     `flyer_filename` and `content_hash` onto the *existing* real
     entry, set that entry's `needs_review` to `false`, and delete the
     placeholder entry the sync script added — don't leave a duplicate
     card around. If the flyer also updates that campaign's real
     details (a new price, a new link), update the existing entry's
     fields too rather than the placeholder's.
   - **The flyer really is for a new campaign** (the sync script's
     conservative guess correctly found nothing, and looking at the
     flyer confirms it): fill in the placeholder's real values —
     `name`, `category` (one of `recurring`, `seasonal`, `annual`,
     `everyday`, or `direct` — see `.claude/skills/add-fundraiser/SKILL.md`
     for what each means), `description`, `how_to_join`, `cta_label`/
     `cta_href` (or `dates` for a Restaurant-Nights-style recurring
     series with real dates/venues — see that entry in the same file
     for the shape), `secondary_label`/`secondary_href`,
     `enrollment_code`, and `contact` as applicable. Do not invent
     details the flyer doesn't actually show — leave a field `null` if
     it's genuinely not on the flyer. Set `"needs_review": false`.

   Either way, an entry flagged `needs_review` purely because its
   *existing* flyer image changed (not a new file) just needs its
   current details double-checked against the updated flyer and
   `needs_review` cleared — nothing to merge or create.
6. Run `python3 src/build.py`, then `python3 test/validate_build.py`.
   If validation fails, fix the underlying issue and re-run rather than
   skipping it.
7. `git add config/fundraisers.json pages/`, commit with a clear message
   (e.g. "chore: fill in reviewed fundraiser flyer details" or "chore:
   merge reprinted flyer into existing fundraiser campaign"), and
   `git push origin main`. This is routine content fill, not a design
   change — push directly to `main`, no staging-first step needed
   (matches how the automated sync itself already commits directly to
   main).
8. Verify, don't just trust a green checkmark: `gh run list
   --workflow=deploy.yml --limit 1`, then `gh run watch <id>
   --exit-status` to confirm the push's deploy actually succeeded, then
   `curl` the live `https://www.thespta.org/fundraising.html` page to
   confirm the new/updated content is actually there.
9. Report a short summary: how many entries were reviewed (name each
   one, and say whether it was a new campaign or a merged reprint), or
   that there was nothing to do.

## Do not

- Do not touch the `thespta-prestage` (staging) repo — it runs its own
  independent copy of the same sync on its own pushes and may flag the
  same flyer separately; that's expected drift for routine content, not
  something to fix here.
- Do not hand-write `content_hash` — it's bookkeeping the mechanical
  sync owns; only `needs_review` and the actual content fields are
  yours to edit here.
- Do not leave a duplicate card on the page when a flyer turns out to
  be a reprint of an existing campaign — merge it, don't just fill in
  the placeholder alongside the real entry.
