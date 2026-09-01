#!/usr/bin/env python3
"""
Pulls upcoming events from the PTA's Google Calendar and writes
config/events.json in the exact shape src/build.py expects — so the
"Upcoming Events" preview on the Home page and the quick-scan list on the
Events page stay in sync with the calendar automatically, with nobody
hand-editing config/events.json. A file attached to a calendar event (e.g.
a flyer PDF added via Google Drive in the Calendar UI) is picked up too —
confirmed empirically that Google's public .ics export includes ATTACH
properties, which isn't obviously true of a "basic" reduced feed — and
turned into a "Flyer" link on that event wherever it's shown. The Drive
file itself still needs "Anyone with the link" sharing for that link to
actually work for a visitor — attaching it to the event doesn't change its
Drive permissions.

A calendar shared as "public" (see docs/SOP.md Task 5) exposes a free,
no-auth .ics feed at a fixed URL — the same feed config/site.json's
CAL_ICS_URL already points visitors to for "Download .ics". This script
fetches that feed and parses just enough iCalendar (RFC 5545) syntax to
list what's coming up: VEVENT/SUMMARY/DTSTART/DTEND/LOCATION/DESCRIPTION,
plus RRULE recurrence (FREQ=DAILY/WEEKLY/MONTHLY/YEARLY, INTERVAL, COUNT,
UNTIL, BYDAY — including the "first Tuesday of the month" ordinal form
PTA meetings commonly use) and EXDATE. No third-party calendar library —
stdlib only, consistent with the rest of this build system.

Run manually any time you want the site to catch up with calendar changes
right now:

    python3 scripts/sync_calendar_events.py

GitHub Actions also runs this automatically before every build — on a
daily schedule and on every push (see .github/workflows/deploy.yml) — so
this normally never needs a human to run it. Add/edit/delete events in
Google Calendar directly; that's the only source of truth now.

If the calendar has zero upcoming events, this writes an empty `[]` and
the "Upcoming Events" / quick-scan sections disappear from the site
entirely (same empty-list-means-no-section pattern as sponsors/flyers) —
not a bug, and not this script's problem to paper over.
"""
import datetime as dt
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config"

LOOKAHEAD_DAYS = 180  # how far into the future to expand recurring events
MAX_EVENTS = 6        # how many upcoming events to keep as highlights

MONTH_ABBR = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
WEEKDAYS = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]


def load_json(name):
    return json.loads((CONFIG / name).read_text())


def fetch_ics(calendar_id):
    url = f"https://calendar.google.com/calendar/ical/{urllib.parse.quote(calendar_id, safe='')}/public/basic.ics"
    with urllib.request.urlopen(url, timeout=20) as resp:
        return resp.read().decode("utf-8", errors="replace")


def unfold(text):
    """RFC 5545 line folding: a line starting with a space/tab continues the previous line."""
    lines = text.replace("\r\n", "\n").split("\n")
    out = []
    for line in lines:
        if line.startswith((" ", "\t")) and out:
            out[-1] += line[1:]
        else:
            out.append(line)
    return out


def unescape_text(value):
    return (
        value.replace("\\n", " ").replace("\\N", " ")
        .replace("\\,", ",").replace("\\;", ";").replace("\\\\", "\\")
        .strip()
    )


def parse_property_line(line):
    """'NAME;PARAM=X:VALUE' -> ("NAME", {"PARAM": "X"}, "VALUE")."""
    head, _, value = line.partition(":")
    parts = head.split(";")
    params = {}
    for p in parts[1:]:
        if "=" in p:
            k, v = p.split("=", 1)
            if v.startswith('"') and v.endswith('"'):
                v = v[1:-1]
            params[k] = v
    return parts[0], params, value


def parse_ics_datetime(value, local_tz):
    """DTSTART/DTEND/EXDATE value -> (naive local datetime, is_all_day).
    A trailing "Z" means UTC — converted to the calendar's configured
    timezone. A bare TZID-qualified or floating value is treated as
    already being in that local timezone (true for a single-timezone PTA
    calendar, which is the only case this needs to handle)."""
    value = value.strip()
    if len(value) == 8:
        return dt.datetime.strptime(value, "%Y%m%d"), True
    if value.endswith("Z"):
        aware_utc = dt.datetime.strptime(value, "%Y%m%dT%H%M%SZ").replace(tzinfo=dt.timezone.utc)
        return aware_utc.astimezone(local_tz).replace(tzinfo=None), False
    return dt.datetime.strptime(value, "%Y%m%dT%H%M%S"), False


def parse_vevents(lines, local_tz):
    events = []
    cur = None
    for line in lines:
        if line == "BEGIN:VEVENT":
            cur = {}
        elif line == "END:VEVENT":
            if cur is not None and "DTSTART" in cur:
                events.append(cur)
            cur = None
        elif cur is not None and line.strip():
            name, params, value = parse_property_line(line)
            if name in ("DTSTART", "DTEND"):
                when, all_day = parse_ics_datetime(value, local_tz)
                cur[name] = when
                cur[name + "_ALLDAY"] = all_day
            elif name == "EXDATE":
                cur.setdefault("EXDATE", set())
                for v in value.split(","):
                    when, _ = parse_ics_datetime(v, local_tz)
                    cur["EXDATE"].add(when)
            elif name in ("SUMMARY", "LOCATION", "DESCRIPTION"):
                cur[name] = unescape_text(value)
            elif name == "RRULE":
                cur["RRULE"] = value
            elif name == "ATTACH":
                cur.setdefault("ATTACH", [])
                cur["ATTACH"].append({"title": params.get("FILENAME", "Flyer"), "href": value.strip()})
    return events


def parse_rrule(rrule):
    out = {}
    for chunk in rrule.split(";"):
        k, _, v = chunk.partition("=")
        out[k] = v
    return out


def matches_monthly_byday(d, byday):
    m = re.match(r"(-?\d*)([A-Z]{2})", byday)
    ordinal_str, weekday_code = m.groups()
    if WEEKDAYS.index(weekday_code) != d.weekday():
        return False
    if not ordinal_str:
        return True
    ordinal = int(ordinal_str)
    if ordinal > 0:
        return (d.day - 1) // 7 + 1 == ordinal
    next_month = (d.replace(day=28) + dt.timedelta(days=4)).replace(day=1)
    last_day_of_month = (next_month - dt.timedelta(days=1)).day
    return (last_day_of_month - d.day) // 7 == (-ordinal - 1)


def advance(cur, freq, interval, byday):
    if freq == "DAILY":
        return cur + dt.timedelta(days=interval)
    if freq == "WEEKLY":
        return cur + dt.timedelta(weeks=interval)
    if freq == "MONTHLY":
        if byday:
            return cur + dt.timedelta(days=1)  # scanned day-by-day; see expand_occurrences
        month_index = cur.month - 1 + interval
        year = cur.year + month_index // 12
        month = month_index % 12 + 1
        day = min(cur.day, 28)
        return cur.replace(year=year, month=month, day=day)
    if freq == "YEARLY":
        try:
            return cur.replace(year=cur.year + interval)
        except ValueError:
            return cur.replace(year=cur.year + interval, day=28)
    return None


def expand_occurrences(event, window_start, window_end):
    """Yield each occurrence's start datetime within [window_start, window_end]."""
    start = event["DTSTART"]
    rrule = event.get("RRULE")
    if not rrule:
        if window_start <= start <= window_end:
            yield start
        return

    rule = parse_rrule(rrule)
    freq = rule.get("FREQ")
    interval = int(rule.get("INTERVAL", "1"))
    count = int(rule["COUNT"]) if "COUNT" in rule else None
    until = parse_ics_datetime(rule["UNTIL"], dt.timezone.utc)[0] if "UNTIL" in rule else None
    byday = rule.get("BYDAY") if freq == "MONTHLY" else None
    exdates = event.get("EXDATE", set())

    cur = start
    produced = 0
    for _ in range(3000):  # defensive cap — a malformed rule can't loop forever
        if cur is None or cur > window_end or (until and cur > until) or (count is not None and produced >= count):
            break
        matches = matches_monthly_byday(cur, byday) if byday else True
        if matches:
            if cur not in exdates and cur >= window_start:
                yield cur
            produced += 1
        cur = advance(cur, freq, interval, byday)


def format_time(d):
    return d.strftime("%-I:%M %p")


def format_when(start, end, all_day, location):
    if all_day:
        parts = ["All Day"]
    elif end and end != start:
        start_s, end_s = format_time(start), format_time(end)
        same_period = start_s[-2:] == end_s[-2:]
        parts = [f"{start_s[:-3] if same_period else start_s} – {end_s}"]
    else:
        parts = [format_time(start)]
    if location:
        parts.append(location)
    return " · ".join(parts)


def build_events_json(vevents, window_start, window_end):
    occurrences = []
    for event in vevents:
        title = event.get("SUMMARY", "Untitled Event")
        start_time = event["DTSTART"]
        end_time = event.get("DTEND")
        all_day = event.get("DTSTART_ALLDAY", False)
        duration = (end_time - start_time) if end_time else None
        for occ_start in expand_occurrences(event, window_start, window_end):
            occ_end = occ_start + duration if duration else None
            occurrences.append({
                "start": occ_start,
                "title": title,
                "when": format_when(occ_start, occ_end, all_day, event.get("LOCATION")),
                "description": event.get("DESCRIPTION"),
                "attachments": event.get("ATTACH", []),
            })

    occurrences.sort(key=lambda o: o["start"])
    occurrences = occurrences[:MAX_EVENTS]

    out = []
    for i, occ in enumerate(occurrences):
        entry = {
            "day": f"{occ['start'].day:02d}",
            "month": MONTH_ABBR[occ["start"].month - 1],
            "title": occ["title"],
            "when": occ["when"],
            "featured": i == 0,
        }
        if occ["attachments"]:
            entry["attachments"] = occ["attachments"]
        if i == 0:
            # The featured card always shows a description slot, so it
            # always gets one, even a generic one if the calendar didn't
            # set a real Description.
            entry["description"] = (occ["description"] or f"Join us for {occ['title']} — see the full calendar for details.")[:200]
        elif occ["description"]:
            # Every other event on the quick-scan list shows its own
            # calendar Description too, if it set one — otherwise the
            # row just stays compact (day/time/title), no filler text.
            entry["description"] = occ["description"][:200]
        out.append(entry)
    return out


def main():
    site = load_json("site.json")
    calendar_id = site["calendar"]["calendar_id"]
    local_tz = ZoneInfo(site["calendar"]["timezone"])

    try:
        raw = fetch_ics(calendar_id)
    except (urllib.error.URLError, TimeoutError) as e:
        print(f"  ! Could not fetch the calendar feed ({e}) — leaving config/events.json unchanged.")
        return

    vevents = parse_vevents(unfold(raw), local_tz)
    window_start = dt.datetime.combine(dt.date.today(), dt.time.min)
    window_end = window_start + dt.timedelta(days=LOOKAHEAD_DAYS)
    events = build_events_json(vevents, window_start, window_end)

    (CONFIG / "events.json").write_text(json.dumps(events, indent=2) + "\n")
    print(f"  synced {len(events)} upcoming event(s) from the calendar into config/events.json")


if __name__ == "__main__":
    main()
