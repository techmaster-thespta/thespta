#!/usr/bin/env python3
"""
Thunder Hill Elementary PTA — static site builder.

Reads /config/*.json + src/templates/*.html.tmpl and writes one complete
HTML file per page into /pages, self-hosted directly on GitHub Pages at
the custom domain in config/site.json's `custom_domain` — no third-party
site builder in the chain. Run this after changing anything in /config
or /src/templates:

    python3 src/build.py        (or: scripts/build.sh)

No dependencies beyond the Python 3 standard library.

WHY THIS EXISTS: this script is what makes "change the color/text once,
it updates everywhere" possible — it lives entirely in this repo, and its
only job is to stamp out the final static files that get deployed.

Pages: home, about, get-involved, events, newsletter — see docs/SOP.md
for the full day-to-day editing guide, and docs/skills for how content
additions (events, board members, sponsors, flyers) are meant to be made
— config only, never this file — by an agent working from .claude/skills/.
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


def build_context(depth=0):
    """`depth` is how many directory levels below the site root the page
    being built lives (0 for a top-level page like about.html, 1 for a
    page one directory down like get-involved/committees.html, etc.) —
    every relative path below is prefixed with the right number of "../"
    so a page can correctly link to any other page or asset regardless of
    how deep either one is nested. Deliberately relative rather than
    root-absolute (e.g. "/about.html"): this repo also gets pushed as-is
    to a staging repo served from a URL *subpath*
    (.../thespta-prestage/...), not the domain root, where root-absolute
    links would silently point at the wrong site."""
    site = load_json("site.json")
    theme = load_json("theme.json")

    context = flatten(site)
    context["font_display"] = theme["fonts"]["display"]
    context["font_body"] = theme["fonts"]["body"]
    context["google_fonts_url"] = theme["fonts"]["google_fonts_url"]
    context.update(flatten(theme["colors"], "colors"))

    prefix = "../" * depth

    # Served by GitHub Pages alongside the HTML — see .github/workflows/deploy.yml,
    # which copies assets/images/* into site/images/ next to pages/*.html.
    context["HERO_IMAGE_URL"] = f'{prefix}images/{site["hero_image_filename"]}'
    context["PAGE_HEADER_IMAGE_URL"] = f'{prefix}images/{site["page_header_image_filename"]}'

    # Same idea, for content-type flyers (afterschool programs,
    # fundraisers) — see .github/workflows/deploy.yml, which copies
    # assets/flyers/** into site/flyers/** next to pages/*.html. These
    # used to be Google Drive hotlinks; moved into the repo after the
    # Drive account got flagged and every file in it — even ones on a
    # plain public link — started 403ing.
    context["FLYER_BASE_URL"] = f"{prefix}flyers"

    # Internal links are plain relative filenames — `about`, `events`, etc.
    # become `about.html`, `events.html` (or `../about.html` etc. from one
    # directory down) — resolved relative to whatever domain serves
    # /pages directly (GitHub Pages' own URL, or the custom domain in
    # `custom_domain` via the generated CNAME file below).
    for key in list(context.keys()):
        if key.startswith("page_urls."):
            context[key] = f"{prefix}{context[key]}.html"

    cal_id = site["calendar"]["calendar_id"]
    cal_id_q = urllib.parse.quote(cal_id, safe="")
    tz_q = urllib.parse.quote(site["calendar"]["timezone"], safe="")
    # `color`: Google's embed defaults an unstyled calendar's events to a
    # pale/white block that barely shows up against the embed's white
    # background — passing our own navy brand color (confirmed Google
    # accepts arbitrary hex here, not just its built-in palette) makes a
    # day with something on it obvious at a glance. `mode=MONTH` makes
    # that explicit rather than relying on the embed's own default.
    color_q = urllib.parse.quote("#" + theme["colors"]["navy"].lstrip("#"), safe="")
    context["CAL_EMBED_SRC"] = (
        f"https://calendar.google.com/calendar/embed?src={cal_id_q}&ctz={tz_q}&color={color_q}&mode=MONTH"
        "&showTitle=0&showPrint=0&showTabs=0&showCalendars=0&showNav=1&showDate=1"
    )
    context["CAL_WEBCAL_URL"] = f"webcal://calendar.google.com/calendar/ical/{cal_id_q}/public/basic.ics"
    context["CAL_GOOGLE_ADD_URL"] = f"https://calendar.google.com/calendar/render?cid={cal_id_q}"
    context["CAL_ICS_URL"] = f"https://calendar.google.com/calendar/ical/{cal_id_q}/public/basic.ics"

    return context


def build_tokens(context):
    return render((TEMPLATES / "tokens.html.tmpl").read_text(), context)


def render_nav_items(items, context):
    """Render config/site.json's `nav` list into <li> menu items.

    Each item is {"label": ..., "page_url": <a page_urls.* key>} and may
    optionally have "children": [...same shape...] for a one-level
    dropdown submenu — this is the hook for a future page to gain
    subpages without touching this function again, just config. A parent
    with children and no page_url of its own (omit "page_url") renders as
    a non-link dropdown trigger rather than a page link.

    A parent item's caret is a real <button> wired to its submenu via
    aria-controls/id (not proximity in the DOM) and toggled by the
    script build_header() appends after the header markup. The JS sets
    the submenu's inline style.display directly rather than toggling a
    CSS class, so opening/closing it can't be silently defeated by a
    media query or selector mistake elsewhere in the stylesheet — an
    inline style always wins the cascade."""
    html = []
    for i, item in enumerate(items):
        label = item["label"]
        href = context[f"page_urls.{item['page_url']}"] if item.get("page_url") else None
        children = item.get("children")
        if children:
            submenu_id = f"thes-submenu-{i}"
            child_html = "".join(
                f'<li><a href="{context[f"page_urls.{c["page_url"]}"]}">{c["label"]}</a></li>'
                for c in children
            )
            trigger = f'<a href="{href}">{label}</a>' if href else f'<span class="thes__nav-trigger">{label}</span>'
            html.append(
                f'<li class="thes__nav-item thes__nav-item--parent">'
                f'<span class="thes__nav-item-row">{trigger}'
                f'<button type="button" class="thes__nav-caret" aria-label="Show {label} submenu" '
                f'aria-expanded="false" aria-controls="{submenu_id}"></button>'
                f'</span>'
                f'<ul class="thes__nav-submenu" id="{submenu_id}">{child_html}</ul></li>'
            )
        else:
            html.append(f'<li class="thes__nav-item"><a href="{href}">{label}</a></li>')
    return "\n".join(html)


def build_header(context):
    nav_items = render_nav_items(load_json("site.json").get("nav", []), context)
    return render((TEMPLATES / "header.html.tmpl").read_text(), {**context, "NAV_ITEMS": nav_items})


def build_footer(context):
    return render((TEMPLATES / "footer.html.tmpl").read_text(), context)


def render_board_photo(member):
    """A board member's headshot, served from assets/images/ like the
    hero/page-header images — or a neutral placeholder for a vacant seat
    (no `photo_filename` in config/board.json), so the grid stays visually
    aligned instead of some cards being taller than others."""
    filename = member.get("photo_filename")
    if filename:
        return f'<img class="thes__board-photo" src="images/{filename}" alt="{member["name"]}">'
    return (
        '<div class="thes__board-photo-placeholder" aria-hidden="true">'
        '<svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6">'
        '<circle cx="12" cy="8" r="4"/><path d="M4 21c0-4.5 4-7 8-7s8 2.5 8 7"/></svg>'
        "</div>"
    )


def render_board_email(member):
    """Omit the email line entirely rather than link to a blank/guessed
    address — not every real board member has a published email, and a
    vacant seat never does."""
    email = member.get("email")
    if not email:
        return ""
    return f'<a class="thes__board-email" href="mailto:{email}">{email}</a>'


def build_board_cards():
    board = load_json("board.json", default=[])
    card_tmpl = (TEMPLATES / "card-board-member.html.tmpl").read_text()
    cards = []
    for member in board:
        ctx = {**member, "PHOTO": render_board_photo(member), "EMAIL_LINK": render_board_email(member)}
        cards.append(indent(render(card_tmpl, ctx)))
    return "\n".join(cards)


DRIVE_FILE_ID = re.compile(r"/file/d/([\w-]+)|[?&]id=([\w-]+)")


def drive_thumbnail_url(href):
    """Drive's public thumbnail endpoint renders a preview image for a
    shared file regardless of type — a real image, or the first page of a
    PDF — confirmed working against a real file before relying on it.
    Returns None if `href` isn't a recognizable Drive share link, so
    non-Drive attachments just fall back to a plain text link."""
    m = DRIVE_FILE_ID.search(href)
    if not m:
        return None
    file_id = m.group(1) or m.group(2)
    return f"https://drive.google.com/thumbnail?id={file_id}&sz=w400"


ATTACHMENT_LINK_TEXT = "Click for more information"


def render_event_attachments(attachments):
    """A file attached to a calendar event (e.g. a flyer PDF or image —
    see scripts/sync_calendar_events.py) becomes a small clickable
    thumbnail preview, or a plain text link when there's no thumbnail to
    show. Returns "" if the event has none.

    The thumbnail is sized big enough that the picture itself is
    recognizable (not just a tiny icon) — that's what signals "there's
    more here," so no "Flyer:" label is needed alongside it, just the
    click-through text. The link text is always ATTACHMENT_LINK_TEXT, not
    the attachment's own filename — Calendar attachments commonly get an
    auto-generated filename (a photo upload UUID, a scan's default name),
    which reads as noise/clutter next to an event, not useful link text."""
    if not attachments:
        return ""
    items = []
    for a in attachments:
        thumb_url = drive_thumbnail_url(a["href"])
        if thumb_url:
            items.append(
                f'<a class="thes__flyer" href="{a["href"]}" target="_blank" rel="noopener">'
                f'<img src="{thumb_url}" alt="" width="160" loading="lazy">'
                f'<span>{ATTACHMENT_LINK_TEXT}</span></a>'
            )
        else:
            items.append(f'<a class="thes__flyer" href="{a["href"]}" target="_blank" rel="noopener"><span>{ATTACHMENT_LINK_TEXT}</span></a>')
    return f'<div class="thes__event-attachments">{"".join(items)}</div>'


def render_event_description(description):
    """An event's own calendar Description, shown as a short blurb under
    its row on the Events page's quick-scan list — "" if it doesn't have
    one (true of most non-featured events), so the row just stays compact
    instead of showing filler text. Separate from the raw `description`
    field the featured-event card template uses directly — that one
    always has a value (falling back to a generic line), this one is
    genuinely optional."""
    if not description:
        return ""
    return f'<p class="thes__event-description">{description}</p>'


def with_event_extras(event):
    return {
        **event,
        "ATTACHMENTS": render_event_attachments(event.get("attachments", [])),
        "DESCRIPTION_BLOCK": render_event_description(event.get("description")),
    }


def build_home_events_section(events, context):
    """Whole 'Upcoming Events' section on the Home page: one big featured
    event (first entry with "featured": true, or the first event) + the
    next two as a short list. Config/events.json is synced automatically
    from Google Calendar (see scripts/sync_calendar_events.py) and can
    genuinely be empty — same empty-list-means-no-section pattern as
    sponsors/flyers, rather than rendering an empty grid."""
    if not events:
        return ""
    featured_tmpl = (TEMPLATES / "featured-event.html.tmpl").read_text()
    more_tmpl = (TEMPLATES / "more-event-row.html.tmpl").read_text()
    section_tmpl = (TEMPLATES / "events-section.html.tmpl").read_text()

    featured = next((e for e in events if e.get("featured")), events[0])
    others = [e for e in events if e is not featured][:2]

    featured_html = indent(render(featured_tmpl, {**context, **with_event_extras(featured)}), 8)
    more_rows = "\n".join(indent(render(more_tmpl, {**context, **e}), 10) for e in others)
    return render(section_tmpl, {**context, "FEATURED_EVENT": featured_html, "MORE_EVENTS": more_rows})


EVENTS_PAGE_MAX = 4


def build_events_page_section(events, context):
    """Whole quick-scan highlights section on the Events page. Unlike the
    Home page teaser (which just disappears when there are no events —
    it's a preview, not the main feature), this section always renders:
    with zero synced events it shows a short "nothing posted yet" message
    instead of vanishing, since this list is the site's main date-sorted
    view of what's coming up and a visitor expects to see *something*
    here. The live calendar embed further down the page renders either
    way, regardless of this section.

    Capped at EVENTS_PAGE_MAX (4) events — config/events.json is already
    date-ascending (see scripts/sync_calendar_events.py), so this is
    simply the next 4 chronologically. No "view more" link is needed for
    anything beyond that: the live calendar embed further down this same
    page already shows everything."""
    section_tmpl = (TEMPLATES / "events-list-section.html.tmpl").read_text()
    if not events:
        empty_tmpl = (TEMPLATES / "events-list-empty.html.tmpl").read_text()
        return render(empty_tmpl, context)
    row_tmpl = (TEMPLATES / "event-row.html.tmpl").read_text()
    section_tmpl = (TEMPLATES / "events-list-section.html.tmpl").read_text()
    rows = "\n".join(indent(render(row_tmpl, {**context, **with_event_extras(e)}), 8) for e in events[:EVENTS_PAGE_MAX])
    return render(section_tmpl, {**context, "EVENTS_LIST": rows})


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


COMMITTEE_STATUS_LABELS = {
    "chair-needed": "Chair Needed",
    "members-welcome": "Members Welcome",
}


def build_volunteer_form_url(volunteer_form, value):
    """A Google Forms "prefilled response" URL — the same form for every
    committee, with the committee field pre-filled to `value`, so no
    per-committee page/link/form is ever needed (config/site.json's
    `volunteerForm` ships with placeholder baseUrl/committeeFieldId until
    a real Google Form exists — see docs/SOP.md for how to get the real
    values from one)."""
    base = volunteer_form["baseUrl"].rstrip("?")
    field = volunteer_form["committeeFieldId"]
    return f"{base}?{field}={urllib.parse.quote(value)}"


def render_committee_card(committee, volunteer_form):
    """One committee's card: status badge, one-line description, chair
    (if any), a volunteer button that deep-links into the single shared
    Google Form with this committee pre-selected, and a native <details>
    disclosure for the rest — no JS, no separate page per committee, no
    modal framework needed for "expand for more" to work on mobile."""
    status = committee["status"]
    chair = committee.get("chair")
    chair_line = f'<p class="thes__committee-chair">Chair: {chair}</p>' if chair else ""
    activities = "".join(f"<li>{a}</li>" for a in committee.get("activities", []))
    status_note = (
        "A chair is still needed for this committee — but you don't need to become chair to help."
        if status == "chair-needed"
        else "This committee already has a chair — members are always welcome."
    )
    form_url = build_volunteer_form_url(volunteer_form, committee["volunteerValue"])
    return (
        '<div class="thes__committee-card">'
        f'<span class="thes__badge thes__badge--{status}">{COMMITTEE_STATUS_LABELS[status]}</span>'
        f'<h3>{committee["name"]}</h3>'
        f'<p>{committee["description"]}</p>'
        f"{chair_line}"
        f'<a class="thes__btn thes__btn--teal" href="{form_url}" target="_blank" rel="noopener">Volunteer with {committee["name"]}</a>'
        '<details class="thes__committee-more"><summary>Learn More</summary>'
        '<div class="thes__committee-more-body">'
        f'<ul class="thes__checklist-plain">{activities}</ul>'
        f"<p>{status_note}</p>"
        "</div></details>"
        "</div>"
    )


def build_committees_section(committees, volunteer_form):
    """Whole committees page body: the two sections the spec calls for
    (chair-needed first, then members-welcome), each a card grid, plus a
    closing "not sure where to help" CTA into the same form with no
    committee — or rather a "help me choose" placeholder value —
    pre-selected. All 10 committees live on this one page; no per-
    committee URLs exist anywhere."""
    chair_needed = [c for c in committees if c["status"] == "chair-needed"]
    members_welcome = [c for c in committees if c["status"] == "members-welcome"]
    chair_needed_html = "\n".join(indent(render_committee_card(c, volunteer_form), 6) for c in chair_needed)
    members_welcome_html = "\n".join(indent(render_committee_card(c, volunteer_form), 6) for c in members_welcome)
    not_sure_url = build_volunteer_form_url(volunteer_form, "Not sure — help me choose.")
    section_tmpl = (TEMPLATES / "committees-section.html.tmpl").read_text()
    return render(section_tmpl, {
        "CHAIR_NEEDED_CARDS": chair_needed_html,
        "MEMBERS_WELCOME_CARDS": members_welcome_html,
        "NOT_SURE_FORM_URL": not_sure_url,
    })


def render_afterschool_program_card(program, context):
    """One afterschool program's card: a short always-visible summary
    (name, provider, one compact meta line, Register button) plus a
    native <details> "Details" disclosure for everything else —
    description, full schedule/sessions, contact, the flyer, fine print.
    Same zero-JS expand/collapse pattern committees already use
    (render_committee_card above); added because showing every field for
    all 10 programs at once on one page read as far too much text.

    Run by an outside provider (iCode, KidzArt, a theatre company,
    etc.), not the PTA — the flyer image is the source of truth, a
    plain file in assets/flyers/before-after-school/ (previously
    hotlinked from Google Drive; moved into the repo after the Drive
    account got flagged and every file in it started 403ing, even ones
    on a plain public link). `content_hash` on each config entry is
    bookkeeping only (lets a future refresh tell which flyers actually
    changed vs. which are untouched) and is never rendered."""
    summary = [f'<h3>{program["name"]}</h3>']
    if program.get("provider"):
        summary.append(f'<p class="thes__program-provider">{program["provider"]}</p>')
    if program.get("grades"):
        summary.append(f'<span class="thes__badge thes__badge--age">Grades {program["grades"]}</span>')

    meta_bits = [b for b in (program.get("day_time"), program.get("price")) if b]
    if meta_bits:
        summary.append(f'<p class="thes__program-meta">{" &middot; ".join(meta_bits)}</p>')

    if program.get("registration_href"):
        summary.append(
            f'<a class="thes__btn thes__btn--teal" href="{program["registration_href"]}" '
            f'target="_blank" rel="noopener">Register &rarr;</a>'
        )

    details = []
    if program.get("description"):
        details.append(f'<p>{program["description"]}</p>')
    if program.get("date_range"):
        details.append(f'<p>{program["date_range"]}</p>')
    if program.get("show_date"):
        details.append(f'<p>Show: {program["show_date"]}</p>')

    sessions = program.get("sessions") or []
    if sessions:
        rows = "".join(
            f'<li><strong>{s["label"]}:</strong> {s["dates"]} &mdash; {s.get("classes", "")}, {s.get("price", "")}</li>'
            for s in sessions
        )
        details.append(f'<ul class="thes__checklist-plain">{rows}</ul>')

    if program.get("contact"):
        details.append(f'<p>{program["contact"]}</p>')

    flyer_filename = program.get("flyer_filename")
    if flyer_filename:
        flyer_url = f'{context["FLYER_BASE_URL"]}/before-after-school/{flyer_filename}'
        details.append(
            f'<a class="thes__flyer" href="{flyer_url}" target="_blank" rel="noopener">'
            f'<img src="{flyer_url}" alt="" width="160" loading="lazy">'
            f'<span>{ATTACHMENT_LINK_TEXT}</span></a>'
        )

    if program.get("registration_note"):
        details.append(f'<p>{program["registration_note"]}</p>')

    details_html = ""
    if details:
        details_html = (
            '<details class="thes__program-more"><summary>Details</summary>'
            f'<div class="thes__program-more-body">{"".join(details)}</div></details>'
        )

    return f'<div class="thes__program-card">{"".join(summary)}{details_html}</div>'


def build_afterschool_programs_section(programs, context):
    """Whole Before & After School Programs page body (function/config
    names kept the shorter "afterschool" name for simplicity even after
    the page itself was retitled to explicitly cover before-school
    programs too). Same empty-means-no-content pattern as
    sponsors/flyers/events, except this page always exists (it's in the
    nav) so an empty config shows a short "nothing posted yet" message
    rather than the page vanishing."""
    if not programs:
        return (TEMPLATES / "afterschool-programs-empty.html.tmpl").read_text()
    cards = "\n".join(indent(render_afterschool_program_card(p, context), 6) for p in programs)
    section_tmpl = (TEMPLATES / "afterschool-programs-section.html.tmpl").read_text()
    return render(section_tmpl, {"AFTERSCHOOL_PROGRAM_CARDS": cards})


FUNDRAISER_CATEGORY_LABELS = {
    "recurring": "Recurring Fundraiser",
    "seasonal": "Seasonal Sale",
    "annual": "Annual Drive",
    "everyday": "Everyday Giving",
}

# (group key, categories folded into it, heading, blurb) — five raw
# categories collapse into two visible sections plus a "direct" closing
# band (handled separately below) so the page reads as three balanced
# groups instead of five sparse ones; each card still carries its own
# specific category badge (see FUNDRAISER_CATEGORY_LABELS) so nothing
# about that grouping is lost.
FUNDRAISER_GROUPS = [
    (
        ["recurring", "seasonal", "annual"],
        "Every Year",
        "Traditional Campaigns",
        "Dated and seasonal fundraisers the PTA runs every year — some are happening now, some are still to come.",
    ),
    (
        ["everyday"],
        "All Year Long",
        "Everyday Giving",
        "Set these up once and they keep giving all year long, at no extra cost to you.",
    ),
]


def render_fundraiser_card(campaign, context):
    """One fundraising campaign's card. Two shapes depending on the data:
    a dated campaign (Restaurant Nights) shows its date list directly in
    the always-visible summary — the dates *are* how a family joins, so
    unlike the afterschool-program card's <details> pattern, nothing
    essential is hidden behind a click here. An undated campaign (a
    storefront, an everyday-giving program) shows its "how to join" line
    and CTA button(s) instead. A flyer or contact, when present, still
    goes in a <details> "Details" disclosure — same reasoning as
    render_afterschool_program_card, for whichever field doesn't need to
    be seen immediately."""
    category = campaign["category"]
    parts = [
        f'<span class="thes__badge thes__badge--fund-{category}">{FUNDRAISER_CATEGORY_LABELS[category]}</span>',
        f'<h3>{campaign["name"]}</h3>',
        f'<p>{campaign["description"]}</p>',
    ]

    dates = campaign.get("dates") or []
    if dates:
        rows = []
        for d in dates:
            note = f'<p class="thes__fund-date-note">{d["note"]}</p>' if d.get("note") else ""
            rows.append(
                f'<li><strong>{d["date"]}</strong> — {d["venue"]}, {d["time"]}{note}</li>'
            )
        parts.append(f'<ul class="thes__fund-dates">{"".join(rows)}</ul>')

    if campaign.get("how_to_join"):
        parts.append(f'<p class="thes__fund-howto">{campaign["how_to_join"]}</p>')

    if campaign.get("enrollment_code"):
        parts.append(f'<p class="thes__fund-code">Enrollment code: <strong>{campaign["enrollment_code"]}</strong></p>')

    buttons = []
    if campaign.get("cta_href"):
        buttons.append(
            f'<a class="thes__btn thes__btn--teal" href="{campaign["cta_href"]}" target="_blank" rel="noopener">'
            f'{campaign["cta_label"]} &rarr;</a>'
        )
    secondary_href = campaign.get("secondary_href")
    if secondary_href:
        # A JSON value of "page_urls.xxx" is a sentinel meaning "resolve
        # this as an internal link" — context already holds it fully
        # resolved (relative filename, right "../" depth) under that
        # same dotted key, same as any {{page_urls.xxx}} used directly in
        # a template. Every other value is a literal external URL.
        if secondary_href.startswith("page_urls."):
            secondary_href = context[secondary_href]
            buttons.append(f'<a class="thes__btn thes__btn--navy" href="{secondary_href}">{campaign["secondary_label"]} &rarr;</a>')
        else:
            buttons.append(
                f'<a class="thes__btn thes__btn--navy" href="{secondary_href}" target="_blank" rel="noopener">'
                f'{campaign["secondary_label"]} &rarr;</a>'
            )
    if buttons:
        parts.append('<div class="thes__fund-actions">' + "".join(buttons) + "</div>")

    details = []
    flyer_filename = campaign.get("flyer_filename")
    if flyer_filename:
        flyer_url = f'{context["FLYER_BASE_URL"]}/fundraising/{flyer_filename}'
        details.append(
            f'<a class="thes__flyer" href="{flyer_url}" target="_blank" rel="noopener">'
            f'<img src="{flyer_url}" alt="" width="160" loading="lazy">'
            f'<span>{ATTACHMENT_LINK_TEXT}</span></a>'
        )
    if campaign.get("contact"):
        details.append(f'<p>{campaign["contact"]}</p>')

    details_html = ""
    if details:
        details_html = (
            '<details class="thes__program-more"><summary>Details</summary>'
            f'<div class="thes__program-more-body">{"".join(details)}</div></details>'
        )

    return f'<div class="thes__fund-card">{"".join(parts)}{details_html}</div>'


def build_fundraising_section(campaigns, context):
    """Whole Fundraising page body: campaigns grouped into a couple of
    visually-balanced sections (see FUNDRAISER_GROUPS) plus a closing
    full-width "Give Directly" band — a single-card grid for a one-entry
    category would read as sparse, so it gets the same treatment as
    committees.html's "Not Sure Where to Help?" closer instead. Same
    empty-means-a-placeholder-message pattern as the other always-in-nav
    pages (afterschool programs, events)."""
    if not campaigns:
        return (TEMPLATES / "fundraising-empty.html.tmpl").read_text()

    by_category = {}
    for c in campaigns:
        by_category.setdefault(c["category"], []).append(c)
    direct = by_category.pop("direct", [])

    sections = []
    tint = True

    # "Give Directly" leads the page — the most immediate, no-research-
    # needed way to help, ahead of the other campaigns that each take a
    # minute to read and act on.
    if direct:
        d = direct[0]
        sections.append(
            f'<section class="thes__section {"thes__section--tint" if tint else ""}">\n'
            '  <div class="thes__wrap">\n'
            '    <div class="thes__join">\n'
            f'      <h2>{d["name"]}</h2>\n'
            f'      <p>{d["description"]}</p>\n'
            f'      <a class="thes__btn thes__btn--navy" href="{d["cta_href"]}" target="_blank" rel="noopener">{d["cta_label"]} &rarr;</a>\n'
            "    </div>\n"
            "  </div>\n"
            "</section>"
        )
        tint = not tint

    for categories, eyebrow, heading, blurb in FUNDRAISER_GROUPS:
        group_campaigns = [c for cat in categories for c in by_category.get(cat, [])]
        if not group_campaigns:
            continue
        cards = "\n".join(indent(render_fundraiser_card(c, context), 6) for c in group_campaigns)
        section_class = "thes__section thes__section--tint" if tint else "thes__section"
        sections.append(
            f'<section class="{section_class}">\n'
            '  <div class="thes__wrap">\n'
            '    <div class="thes__section-head">\n'
            f'      <span class="thes__eyebrow">{eyebrow}</span>\n'
            f'      <h2>{heading}</h2>\n'
            f"      <p>{blurb}</p>\n"
            "    </div>\n"
            '    <div class="thes__fund-grid">\n'
            f"{cards}\n"
            "    </div>\n"
            "  </div>\n"
            "</section>"
        )
        tint = not tint

    return "\n\n".join(sections)


def build_analytics_snippet(ga_id):
    """Google Analytics 4's standard gtag.js snippet for config/site.json's
    `google_analytics_id`, placed immediately after <head> opens on every
    page (Google's own installation instructions specifically call out
    this exact position). Returns "" (nothing rendered, no third-party
    script at all) when it's blank — this ships with zero tracking until
    a real Measurement ID is configured. flatten() stringifies every
    context value, so this also guards against the literal string "None"
    a JSON `null` would otherwise produce here — use "" in config, not
    null, to turn this off."""
    if not ga_id or ga_id == "None":
        return ""
    return (
        "<!-- Google tag (gtag.js) -->\n"
        f'<script async src="https://www.googletagmanager.com/gtag/js?id={ga_id}"></script>\n'
        "<script>\n"
        "  window.dataLayer = window.dataLayer || [];\n"
        "  function gtag(){dataLayer.push(arguments);}\n"
        "  gtag('js', new Date());\n"
        f"  gtag('config', '{ga_id}');\n"
        "</script>\n"
    )


def colorize_title_words(text):
    """Alternate each word's color between the site's dark text tone and
    teal — the same two-tone treatment already used in the home hero
    image's headline ("Stronger Together." / "Better for Every Student.")
    — applied here to the live <h1> text on every other page's header."""
    classes = ["thes__title-a", "thes__title-b"]
    words = text.split(" ")
    return " ".join(f'<span class="{classes[i % 2]}">{w}</span>' for i, w in enumerate(words))


PAGE_TITLES = {
    "about.html": "Who We Are",
    "get-involved.html": "Join Us",
    "events.html": "Upcoming Events",
    "newsletter.html": "The Newsletter",
    "get-involved/committees.html": "Committees",
    "before-after-school-programs.html": "Before & After School Programs",
    "shop.html": "Shop",
    "fundraising.html": "Ways to Give",
}


def main():
    # These don't depend on page depth (no internal page_urls/image
    # links of their own), so they're built once and reused for whatever
    # page(s) actually reference them — same as before this file
    # supported nested pages at all.
    board_cards = build_board_cards()
    events = load_json("events.json", default=[])
    committees_section = build_committees_section(
        load_json("committees.json", default=[]), load_json("site.json")["volunteerForm"]
    )

    page_templates = sorted((TEMPLATES / "pages").rglob("*.html.tmpl"))
    if not page_templates:
        raise SystemExit("No page templates found in src/templates/pages/")

    PAGES_OUT.mkdir(exist_ok=True)
    context_by_depth = {}

    for tmpl_path in page_templates:
        rel = tmpl_path.relative_to(TEMPLATES / "pages")
        depth = len(rel.parts) - 1
        page_name = str(rel).removesuffix(".tmpl")

        # Everything that depends on page_urls.*/HERO_IMAGE_URL/etc has to
        # be rebuilt per depth — a page one directory down needs "../"
        # prefixes a top-level page doesn't. Cheap to just rebuild (this
        # site has a handful of pages total) and memoizing per depth
        # avoids redoing it once per page at the same depth.
        if depth not in context_by_depth:
            context_by_depth[depth] = build_context(depth)
        context = context_by_depth[depth]
        tokens = build_tokens(context)
        header = build_header(context)
        footer = build_footer(context)
        home_events_section = build_home_events_section(events, context)
        events_page_section = build_events_page_section(events, context)
        sponsors_section = build_optional_section(
            "sponsors.json", "card-sponsor.html.tmpl", "sponsors-section.html.tmpl", "SPONSOR_CARDS", context
        )
        flyers_section = build_optional_section(
            "flyers.json", "card-flyer.html.tmpl", "flyers-section.html.tmpl", "FLYER_CARDS", context
        )
        fundraising_section = build_fundraising_section(
            load_json("fundraisers.json", default=[]), context
        )
        afterschool_programs_section = build_afterschool_programs_section(
            load_json("afterschool-programs.json", default=[]), context
        )

        shared_markers = {
            "{{TOKENS}}": tokens,
            "{{FOOTER}}": footer,
            "{{BOARD_CARDS}}": board_cards,
            "{{EVENTS_SECTION}}": home_events_section,
            "{{EVENTS_LIST_SECTION}}": events_page_section,
            "{{SPONSORS_SECTION}}": sponsors_section,
            "{{FLYERS_SECTION}}": flyers_section,
            "{{COMMITTEES_SECTION}}": committees_section,
            "{{AFTERSCHOOL_PROGRAMS_SECTION}}": afterschool_programs_section,
            "{{FUNDRAISING_SECTIONS}}": fundraising_section,
        }

        page_context = context
        if page_name in PAGE_TITLES:
            page_context = {**context, "PAGE_TITLE": colorize_title_words(PAGE_TITLES[page_name])}
        text = tmpl_path.read_text()
        text = render(text, page_context)
        for marker, value in shared_markers.items():
            text = text.replace(marker, value)

        # Decoupled from each page template's own markup on purpose: the
        # header is inserted structurally right after `<div class="thes">`
        # opens, rather than relying on a `{{HEADER}}` marker every page
        # template has to remember to include. A real page once shipped
        # without one (copied from before this branch had a header at
        # all) because nothing enforced its presence — this makes it
        # impossible for any current or future page to omit it.
        text = text.replace('<div class="thes">', f'<div class="thes">\n{header}', 1)

        leftover = PLACEHOLDER.findall(text)
        if leftover:
            print(f"  ! {page_name}: unresolved placeholder(s): {sorted(set(leftover))}")

        # These pages are opened directly (no Google Sites parent page to
        # supply a <head>/viewport for them), so this is a real document
        # shell, not a fragment. Missing the viewport meta specifically
        # would silently break any @media query meant for phones — without
        # it, mobile browsers assume a fake ~980px desktop-width layout
        # viewport instead of the device's real width.
        # index.html is the home page (named that so it loads automatically
        # at the domain root) but should still say "Home" in the browser
        # tab, not the literal filename. For any other page, use just the
        # last path segment (Path.stem) as the title base, ignoring any
        # parent directories — "get-involved/committees.html" should say
        # "Committees", not "Get-Involved/Committees".
        page_title = "Home" if page_name == "index.html" else Path(page_name).stem.replace("-", " ").title()
        analytics_snippet = build_analytics_snippet(context.get("google_analytics_id", ""))
        text = (
            "<!DOCTYPE html>\n"
            '<html lang="en">\n<head>\n'
            f"{analytics_snippet}"
            '<meta charset="UTF-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            f"<title>{context.get('org_name', '')} — {page_title}</title>\n"
            f"</head>\n<body>\n{text}\n</body>\n</html>\n"
        )

        out_path = PAGES_OUT / page_name
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text)
        print(f"  built {out_path.relative_to(ROOT)}")

    # GitHub Pages' custom-domain feature reads a plain-text CNAME file
    # (just the domain, nothing else) from the deployed site's root.
    # Generated from config/site.json's `custom_domain` — the single
    # source of truth — rather than hand-maintained separately, so it
    # can never drift out of sync with what the site actually claims to
    # be. .github/workflows/deploy.yml copies this into site/ alongside
    # pages/*.html and assets/images/*.
    custom_domain = load_json("site.json").get("custom_domain")
    if custom_domain:
        (PAGES_OUT / "CNAME").write_text(custom_domain + "\n")
        print(f"  built {(PAGES_OUT / 'CNAME').relative_to(ROOT)} ({custom_domain})")

    print(f"\nDone — {len(page_templates)} pages written to /pages.")
    print("Push to main to deploy — GitHub Actions rebuilds, validates, and redeploys to GitHub Pages automatically.")


if __name__ == "__main__":
    main()
