#!/usr/bin/env python3
"""
Pulls the next few upcoming events from Howard County Public School
System's own Special Education Parent & Guardian Calendar — a county-
run calendar, not the PTA's — and writes
config/hcpss-family-events.json for the "Upcoming Events" list at the
top of the Special Education & Family Support page
(src/templates/pages/family-support-resources/special-education-family-support.html.tmpl),
above that page's live calendar embed.

Reuses the generic ICS-parsing/occurrence-expansion machinery already
built for the PTA's own calendar sync (scripts/sync_calendar_events.py)
rather than duplicating it — none of that (RFC 5545 line-folding, VEVENT
parsing, RRULE expansion, the Sign Up/Join Google Meet link-extraction
convention) is actually PTA-specific; only the calendar id, timezone,
output file, and event cap differ here. Confirmed empirically that this
calendar's public .ics feed is fetchable the same way the PTA's own is
(same public-calendar-sharing mechanism, different owner).

Run manually any time:

    python3 scripts/sync_hcpss_calendar.py

Run automatically by .github/workflows/deploy.yml on every push and by
sync-events.yml hourly, same as the PTA's own calendar sync — see that
workflow's comment for why the hourly one has to do its own full
build+validate+deploy rather than just committing this file.

If HCPSS's calendar has zero upcoming events, this writes an empty `[]`
and the "Upcoming Events" list disappears from the page entirely — same
empty-list-means-no-section pattern as the PTA's own calendar sync.
"""
import datetime as dt
import json
import re
import urllib.error
from pathlib import Path
from zoneinfo import ZoneInfo

from sync_calendar_events import build_events_json, fetch_ics, parse_vevents, unfold

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config"

CALENDAR_ID = "hcpss.org_b5ohk2do36a6h32jp8f2gureqc@group.calendar.google.com"
TIMEZONE = "America/New_York"
LOOKAHEAD_DAYS = 180  # same window as the PTA's own general highlights list
MAX_EVENTS = 3        # "next 3 events" — this calendar posts often enough not to need a longer lookahead

TAG_RE = re.compile(r"<[^>]+>")


def strip_html(text):
    """HCPSS's own calendar Descriptions contain literal HTML markup
    (<span>/<p>/<br> tags) — confirmed empirically, unlike the PTA's own
    calendar, which is plain text. render_event_description in
    src/build.py inserts a Description unescaped into a <p>, which
    would otherwise nest raw markup (sometimes literal <p> tags) inside
    that <p>, producing oddly-spaced, semantically broken output. Turned
    into plain text here, at the source, so every event description
    this site renders is plain text regardless of which calendar it
    came from."""
    return re.sub(r"\s+", " ", TAG_RE.sub(" ", text)).strip()


def main():
    try:
        raw = fetch_ics(CALENDAR_ID)
    except (urllib.error.URLError, TimeoutError) as e:
        print(f"  ! Could not fetch the HCPSS calendar feed ({e}) — leaving config/hcpss-family-events.json unchanged.")
        return

    local_tz = ZoneInfo(TIMEZONE)
    vevents = parse_vevents(unfold(raw), local_tz)
    for v in vevents:
        if v.get("DESCRIPTION"):
            v["DESCRIPTION"] = strip_html(v["DESCRIPTION"])
    window_start = dt.datetime.combine(dt.date.today(), dt.time.min)
    window_end = window_start + dt.timedelta(days=LOOKAHEAD_DAYS)
    events = build_events_json(vevents, window_start, window_end, max_events=MAX_EVENTS)

    (CONFIG / "hcpss-family-events.json").write_text(json.dumps(events, indent=2) + "\n")
    print(f"  synced {len(events)} upcoming event(s) from the HCPSS calendar into config/hcpss-family-events.json")


if __name__ == "__main__":
    main()
