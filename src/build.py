#!/usr/bin/env python3
"""
Thunder Hill Elementary PTA — Google Sites page builder.

Reads /config/*.json + src/templates/*.html.tmpl and writes one complete,
ready-to-paste HTML file per page into /pages. Run this after changing
anything in /config or /src/templates:

    python3 src/build.py        (or: scripts/build.sh)

No dependencies beyond the Python 3 standard library.

WHY THIS EXISTS: Google Sites' "Embed code" block is just a paste box with
no shared stylesheet, header, or footer of its own for content you embed —
whatever you paste is everything that block contains. This script is what
makes "change the color/text once, it updates everywhere" possible anyway:
it lives entirely in this repo, and its only job is to stamp out the final
files you copy-paste into each page's Embed code block. Google Sites never
sees /config, /src, or this script — only the finished files in /pages.

Pages: home, about, get-involved, events — see docs/SOP.md for the full
day-to-day editing guide, and docs/skills for how content additions
(events, board members, sponsors, flyers) are meant to be made — config
only, never this file — by an agent working from .claude/skills/.
"""
import json
import re
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config"
TEMPLATES = Path(__file__).resolve().parent / "templates"
PAGES_OUT = ROOT / "pages"

PLACEHOLDER = re.compile(r"\{\{\s*([\w.]+)\s*\}\}")


def flatten(d, prefix=""):
    """Turn nested dicts into dotted keys: {"a": {"b": 1}} -> {"a.b": 1}."""
    out = {}
    for k, v in d.items():
        key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            out.update(flatten(v, key))
        else:
            out[key] = str(v)
    return out


def render(text, context):
    """Replace {{key}} / {{a.b}} placeholders found in `context`; leave any
    placeholder not in `context` untouched (so markers like {{FOOTER}} can
    be substituted in a later pass without this function tripping on them)."""
    def sub(match):
        key = match.group(1)
        return context[key] if key in context else match.group(0)
    return PLACEHOLDER.sub(sub, text)


def indent(text, spaces=6):
    pad = " " * spaces
    return "\n".join(pad + line if line.strip() else line for line in text.splitlines())


def load_json(name, default=None):
    path = CONFIG / name
    if not path.exists():
        if default is not None:
            return default
        raise SystemExit(f"Missing required config file: config/{name}")
    return json.loads(path.read_text())


def build_context():
    site = load_json("site.json")
    theme = load_json("theme.json")

    context = flatten(site)
    context["font_display"] = theme["fonts"]["display"]
    context["font_body"] = theme["fonts"]["body"]
    context["google_fonts_url"] = theme["fonts"]["google_fonts_url"]
    context.update(flatten(theme["colors"], "colors"))

    context["HERO_IMAGE_URL"] = f'https://lh3.googleusercontent.com/d/{site["hero_image_drive_id"]}'
    context["PAGE_HEADER_IMAGE_URL"] = f'https://lh3.googleusercontent.com/d/{site["page_header_image_drive_id"]}'

    cal_id = site["calendar"]["calendar_id"]
    cal_id_q = urllib.parse.quote(cal_id, safe="")
    tz_q = urllib.parse.quote(site["calendar"]["timezone"], safe="")
    context["CAL_EMBED_SRC"] = (
        f"https://calendar.google.com/calendar/embed?src={cal_id_q}&ctz={tz_q}"
        "&showTitle=0&showPrint=0&showTabs=0&showCalendars=0&showNav=1&showDate=1"
    )
    context["CAL_WEBCAL_URL"] = f"webcal://calendar.google.com/calendar/ical/{cal_id_q}/public/basic.ics"
    context["CAL_GOOGLE_ADD_URL"] = f"https://calendar.google.com/calendar/render?cid={cal_id_q}"
    context["CAL_ICS_URL"] = f"https://calendar.google.com/calendar/ical/{cal_id_q}/public/basic.ics"

    return context


def build_tokens(context):
    return render((TEMPLATES / "tokens.html.tmpl").read_text(), context)


def build_footer(context):
    return render((TEMPLATES / "footer.html.tmpl").read_text(), context)


def build_board_cards():
    board = load_json("board.json", default=[])
    card_tmpl = (TEMPLATES / "card-board-member.html.tmpl").read_text()
    return "\n".join(indent(render(card_tmpl, member)) for member in board)


def build_home_events_blocks(events, context):
    """One big featured event (first entry with "featured": true, or the
    first event) + the next two as a short list."""
    featured_tmpl = (TEMPLATES / "featured-event.html.tmpl").read_text()
    more_tmpl = (TEMPLATES / "more-event-row.html.tmpl").read_text()

    featured = next((e for e in events if e.get("featured")), events[0])
    others = [e for e in events if e is not featured][:2]

    featured_html = indent(render(featured_tmpl, {**context, **featured}))
    more_rows = "\n".join(indent(render(more_tmpl, {**context, **e}), 8) for e in others)
    return featured_html, more_rows


def build_events_page_list(events, context):
    """Full-ish list of event rows for the dedicated Events page, shown
    above the live calendar as a quick-scan highlight list."""
    row_tmpl = (TEMPLATES / "event-row.html.tmpl").read_text()
    return "\n".join(indent(render(row_tmpl, {**context, **e})) for e in events)


def build_optional_section(config_name, card_template_name, section_template_name, cards_key, context):
    """Generic builder for content types that may have zero entries
    (sponsors, flyers, and any future one like it): renders one card per
    config entry into a section template, or returns "" entirely — so an
    empty config file means the section doesn't appear on the page at all,
    rather than showing an empty heading.
    """
    items = load_json(config_name, default=[])
    if not items:
        return ""
    card_tmpl = (TEMPLATES / card_template_name).read_text()
    cards = "\n".join(indent(render(card_tmpl, item), 8) for item in items)
    section_tmpl = (TEMPLATES / section_template_name).read_text()
    return render(section_tmpl, {**context, cards_key: cards})


def main():
    context = build_context()
    tokens = build_tokens(context)
    footer = build_footer(context)
    board_cards = build_board_cards()

    events = load_json("events.json")
    featured_event, more_events = build_home_events_blocks(events, context)
    events_list = build_events_page_list(events, context)

    sponsors_section = build_optional_section(
        "sponsors.json", "card-sponsor.html.tmpl", "sponsors-section.html.tmpl", "SPONSOR_CARDS", context
    )
    flyers_section = build_optional_section(
        "flyers.json", "card-flyer.html.tmpl", "flyers-section.html.tmpl", "FLYER_CARDS", context
    )

    shared_markers = {
        "{{TOKENS}}": tokens,
        "{{FOOTER}}": footer,
        "{{BOARD_CARDS}}": board_cards,
        "{{FEATURED_EVENT}}": featured_event,
        "{{MORE_EVENTS}}": more_events,
        "{{EVENTS_LIST}}": events_list,
        "{{SPONSORS_SECTION}}": sponsors_section,
        "{{FLYERS_SECTION}}": flyers_section,
    }

    page_templates = sorted((TEMPLATES / "pages").glob("*.html.tmpl"))
    if not page_templates:
        raise SystemExit("No page templates found in src/templates/pages/")

    PAGES_OUT.mkdir(exist_ok=True)

    for tmpl_path in page_templates:
        page_name = tmpl_path.name.removesuffix(".tmpl")
        text = tmpl_path.read_text()
        text = render(text, context)
        for marker, value in shared_markers.items():
            text = text.replace(marker, value)

        leftover = PLACEHOLDER.findall(text)
        if leftover:
            print(f"  ! {page_name}: unresolved placeholder(s): {sorted(set(leftover))}")

        out_path = PAGES_OUT / page_name
        out_path.write_text(text)
        print(f"  built {out_path.relative_to(ROOT)}")

    print(f"\nDone — {len(page_templates)} pages written to /pages.")
    print("Paste each file's full contents into that page's Insert > Embed > Embed code block in Google Sites.")


if __name__ == "__main__":
    main()
