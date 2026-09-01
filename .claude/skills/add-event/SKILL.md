---
name: add-event
description: Add, edit, or remove a PTA event. Events are calendar-driven, not a config edit — this skill points to Google Calendar and (optionally) forces an immediate re-sync.
---

# Add / edit / remove an event

**There is no config file to edit for this anymore.** Both the "Upcoming
Events" preview on the Home page and the quick-scan list on the Events
page are synced automatically from the PTA's Google Calendar by
`scripts/sync_calendar_events.py`, which GitHub Actions runs hourly (via .github/workflows/sync-events.yml) and on
every push. `config/events.json` is *generated* by that script — treat it
like `pages/*.html`: never hand-edit it, it'll just be overwritten.

If the user asks to "add an event," "change an event's time," or "remove
an event from the website," the actual action is in Google Calendar, not
this repo.

## Steps

1. Tell the user (or do it yourself if you have calendar access) to
   add/edit/delete the event directly in Google Calendar — the shared
   calendar matching `calendar.calendar_id` in `config/site.json`. A
   recurring event (e.g. "first Tuesday of every month") works fine; the
   sync script expands common RRULE patterns.
2. **If the user wants a flyer linked from an event**: that's also done
   in Google Calendar, not this repo — open the event → **Add
   attachment** → attach the Drive file. Remind them the Drive file needs
   "Anyone with the link" sharing, since attaching it to the event doesn't
   change its Drive permissions; a flyer link a visitor can't open is the
   likely failure mode. The sync script picks up any attachment
   automatically and renders it as a "Flyer" link on that event.
3. The live calendar embed on the Events page picks this up within
   minutes on its own — nothing to do for that part.
4. The Home/Events highlight lists (and any flyer link) catch up on the
   next scheduled sync (hourly, via `.github/workflows/sync-events.yml`)
   or the next push. To make it show up immediately instead:
   ```bash
   python3 scripts/sync_calendar_events.py
   python3 src/build.py
   python3 test/validate_build.py
   ```
   then push (`docs/SOP.md` Task 7) — or, without local access, trigger
   the **Actions** tab → "Sync events from Google Calendar" → **Run
   workflow** button, which does the same thing in CI.
5. The "featured" event (big navy card on the Home page) is chosen
   automatically — always the soonest upcoming one. There's no manual
   "mark as featured" step anymore.

## Do not

- Do not hand-edit `config/events.json` — it's regenerated from the
  calendar and any manual edit will be silently overwritten on the next
  sync (hourly, at latest).
- Do not edit `scripts/sync_calendar_events.py`, `src/templates/featured-event.html.tmpl`,
  `more-event-row.html.tmpl`, `event-row.html.tmpl`, `events-section.html.tmpl`,
  `events-list-section.html.tmpl`, `src/build.py`, or
  `.github/workflows/{deploy,sync-events}.yml` to accomplish a routine
  event change. If the request genuinely needs different behavior (e.g.
  showing more than 6 upcoming events, changing which one gets featured,
  showing flyer links on the compact Home page rows too), stop and tell
  the user that's a script/template change, not a config change — see
  `docs/SOP.md` Task 4 for the tradeoffs already documented there, and
  get sign-off before touching `src/` per `.claude/CLAUDE.md`.
