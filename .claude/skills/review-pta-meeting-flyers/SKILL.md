---
name: review-pta-meeting-flyers
description: Check config/pta-meetings.json for entries flagged needs_review, read their actual flyer, and fill in the real date, title, and highlights. Used both interactively and by the headless daily automation in scripts/flyer-review/.
---

# Review flagged PTA meeting flyers

Use this when asked to "check for meeting flyers needing review," or
when running non-interactively via `scripts/flyer-review/run.sh`'s
scheduled systemd timer (see `docs/automation-service.md`) — this skill
is what that automation actually invokes for PTA meetings; it has no
separate instructions of its own.

`scripts/sync_pta_meeting_flyers.py` runs as a step in
`.github/workflows/deploy.yml` on every push and mechanically detects
new/removed/changed flyers in `assets/flyers/pta-meetings/`. A brand-new
flyer gets a placeholder with `"date": null` and `"needs_review": true`
— deliberately no guessed date (unlike the other flyer types' guessed
*name*), since a wrong date would silently misfile the meeting into the
wrong school year until someone caught it. A dateless entry never
becomes the page's "Latest Meeting" spotlight and never gets grouped
into a school year (see `build_pta_meetings_section()` in
`src/build.py`) — it just shows up in a small "N new meeting flyers
need review" notice instead, so an unreviewed placeholder can't
misrepresent itself as reviewed content. **This skill is what actually
resolves that**: reading the flyer to fill in the real `date`, `title`,
and `highlights` is a vision/understanding task the sync script can't
do.

If invoked non-interactively (no human present to answer questions or
approve actions): complete the task fully and exit, making the
reasonable call on anything ambiguous and noting it in the final
summary instead of asking.

## Steps

1. `git status` — if the working tree isn't clean, stop and do nothing
   further. Leave it for a human to look at; don't overwrite anything.
2. `git fetch origin main && git pull origin main` to get the latest.
3. Read `config/pta-meetings.json`. Find every entry with
   `"needs_review": true`.
4. If there are none, report "No PTA meeting flyers need review today"
   and stop — that's the normal, expected outcome most days, not an
   error.
5. For each flagged entry, open its flyer —
   `assets/flyers/pta-meetings/<flyer_filename>` (or ask an agent to) —
   and actually read it. These are typically a "recap" graphic (like
   the one this feature launched with — a "Thank You for joining our
   PTA Meeting!" flyer with a "Meeting Highlights" section), not an
   invitation, so the highlights are usually right there on the flyer
   itself:
   - `date`: the meeting's actual date, in `YYYY-MM-DD`. Don't guess —
     if the flyer genuinely doesn't state it, leave it `null` and note
     that in your summary; ask the user for it rather than leaving the
     entry stuck unreviewed indefinitely.
   - `title`: short, e.g. "September PTA Meeting" — not the flyer's
     full headline text.
   - `highlights`: 1–3 sentences, real content from the flyer (new
     board members welcomed, committees formed, membership numbers,
     decisions made) — not the calendar invite's description, which is
     a different piece of writing with a different purpose (what the
     meeting was expected to cover, not what actually happened).
   - `agenda_href`: only if the flyer itself shows/links one (some do,
     e.g. a "View the PTA Agenda" button) — otherwise leave whatever
     was already there, or `null`. Don't invent one.
   Set `"needs_review": false` once filled in.
6. Run `python3 src/build.py`, then `python3 test/validate_build.py`.
   If validation fails, fix the underlying issue and re-run rather than
   skipping it.
7. `git add config/pta-meetings.json pages/`, commit with a clear
   message (e.g. "chore: fill in reviewed PTA meeting flyer details"),
   and `git push origin main`. This is routine content fill, not a
   design change — push directly to `main`, no staging-first step
   needed (matches how the automated sync itself already commits
   directly to main).
8. Verify, don't just trust a green checkmark: `gh run list
   --workflow=deploy.yml --limit 1`, then `gh run watch <id>
   --exit-status` to confirm the push's deploy actually succeeded, then
   `curl` the live `https://www.thespta.org/pta-meetings.html` page to
   confirm the new content is actually there.
9. Report a short summary: how many entries were reviewed (name each
   one), or that there was nothing to do.

## Do not

- Do not touch the `thespta-prestage` (staging) repo — it runs its own
  independent copy of the same sync on its own pushes and may flag the
  same flyer separately; that's expected drift for routine content, not
  something to fix here.
- Do not hand-write `content_hash` — it's bookkeeping the mechanical
  sync owns; only `needs_review` and the actual content fields are
  yours to edit here.
- Do not guess a `date` — leave it `null` and flag it in your summary
  instead. A wrong date silently misfiles the meeting into the wrong
  school year; a `null` one is at least visibly incomplete.
- Do not copy the calendar event's invitation-style description in as
  `highlights` — write (or extract from the flyer) a real summary of
  what actually happened at the meeting.
