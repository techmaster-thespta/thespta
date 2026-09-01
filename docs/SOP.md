# Thunder Hill PTA Website — Standard Operating Procedures

This is the reference doc for **ongoing content edits** — written so a
future board member with no coding background can follow it. For the
one-time initial setup, see `docs/github-pages-setup.md` (GitHub Pages)
and `docs/website-setup.md` (wiring it into Google Sites).

The live site is hosted on **GitHub Pages**; Google Sites embeds each page
**by URL** (not by pasted code) — so once initial setup is done, a content
change is just: edit a config file, push, done. Nothing to re-paste,
nothing to touch in Google Sites again.

## How the system fits together

```
Google Calendar         ← the PTA's shared calendar (events only — see Task 4)
        ↓  scripts/sync_calendar_events.py (GitHub Actions runs this hourly via sync-events.yml, + on every push via deploy.yml)
config/events.json      ← generated — don't hand-edit
config/*.json           ← everything else you DO edit (colors, text, board, sponsors, flyers)
src/templates/*.tmpl    ← page structure (rarely touched)
        ↓  python3 src/build.py   (or: scripts/build.sh)
pages/*.html            ← generated output
        ↓  git push → GitHub Actions
https://techmaster-thespta.github.io/thespta/*.html   ← the live site, embedded by URL in Google Sites
```

**Golden rule: never hand-edit a file in `/pages` or `config/events.json`.**
Both get silently overwritten the next time anyone runs the build/sync —
including automatically, by GitHub Actions, hourly and on every push to
`main`. Every real change happens in Google Calendar (for events), the
rest of `/config` (other data), or `/src/templates` (layout), followed by
a rebuild — and pushing to `main` is what actually makes it live, since
GitHub Actions does the rebuild-and-deploy for you.

**If you're an AI agent (Claude or otherwise) making a content change**:
check `.claude/skills/` first — there's a dedicated skill for each kind of
addition (board member, sponsor, flyer/document). Events are the one
exception: they're calendar-driven now, not a config edit — see
`.claude/skills/add-event/` and Task 4 below. Skills are scoped to
**config-only edits** and are the preferred path. Only touch `src/` if the
user explicitly asks for a structural/design change.

Requires only Python 3 — no npm, no installs, nothing to configure.

---

## Task 1 — Change site info (name, address, contact, links)

**File:** `config/site.json`

| Field | Controls |
|---|---|
| `org_name`, `school_name`, `school_short_name` | Name shown throughout the site |
| `mascot_name` | "Home of the ___" text on the banner |
| `address_line1` / `address_line2` | Footer address |
| `email` | Footer contact link |
| `meeting_schedule`, `membership_cost` | Text on About / Get Involved |
| `donate_href` | Where the "Donate" buttons point (Support THES card). Currently the Givebacks shop pre-filtered to donation items: `https://1thes.givebacks.com/shop?search=Donation` |
| `membership_portal_href` | Where "Join PTA" / "Become a Member" buttons point. Currently the Givebacks shop pre-filtered to membership items: `https://1thes.givebacks.com/shop?search=Membership` — the shop lists each membership tier (student, individual, faculty/staff, business, etc.) as a separately named product, and this one search catches all of them. If a tier ever needs its own dedicated link instead, add a new `*_membership_href` field per tier and wire it in wherever that tier should link. |
| `shop_href` | The Givebacks shop's own landing page (`https://1thes.givebacks.com/shop`) — linked from the footer's Quick Links as "Shop" |
| `social.facebook_href`, `social.instagram_href` | Footer social links |
| `newsletter_href` | Footer "Subscribe" link |
| `google_sites_base_url` | The Google Site's base URL (e.g. `https://sites.google.com/view/thesptademo`) — only touch this if the site ever moves to a different Google Sites URL |
| `page_urls.*` | The **slug** of each page's Google Sites sub-page (e.g. `"home"`, `"get-involved"`) — every internal link (nav cards, buttons) is built as `google_sites_base_url` + `/` + this slug, so clicking a link keeps the visitor inside Google Sites' own nav/header/footer instead of dropping them onto a bare embedded page |
| `copyright_year` | Footer copyright line |

Rebuild + push: `python3 src/build.py` then `git push` (or just push — see Task 7).

---

## Task 2 — Change colors or fonts

**File:** `config/theme.json`

Every color on the site is one of six named roles — change the hex value once, it updates on all 4 pages the next time you rebuild:

| Role | Default | Where it shows up |
|---|---|---|
| `navy` | `#073B68` | Page headers, footer, featured event card |
| `blue` | `#0874B9` | Links, icon circles |
| `yellow` | `#FFD719` | Primary buttons (Donate, Join the PTA) |
| `teal` | `#159C9C` | Accent 1 (Support THES icon, etc.) |
| `coral` | `#F2645A` | Accent 2 (Join Us icon, etc.) |
| `bg_tint` | `#EFF7FA` | Alternating light section backgrounds |

Fonts are set under `fonts.display` (headings — Montserrat) and
`fonts.body` (paragraphs — Lato). To change either, you need a font name
Google Fonts actually has, and you must update `google_fonts_url` to match
(go to [fonts.google.com](https://fonts.google.com), pick the font, copy
the `<link>` URL it gives you).

---

## Task 3 — Add, remove, or edit a board member

**File:** `config/board.json` · **Skill:** `.claude/skills/add-board-member/`

Each entry is `{ "role": "...", "name": "...", "email": "..." }`. Add a new
`{ }` entry (comma-separated) for a new board member, delete one to remove
someone, or edit the text directly. This list appears once, on the About
page.

---

## Task 4 — Add, remove, or edit an event

**There is exactly one place to do this: Google Calendar.** Both the
"Upcoming Events" preview on the Home page and the quick-scan list on the
Events page are synced automatically from the PTA's Google Calendar —
nothing to edit in this repo for a routine event change.

1. Go to [calendar.google.com](https://calendar.google.com), find the
   PTA's shared calendar in the left sidebar (matches the `calendar_id` in
   `config/site.json` under `calendar`).
2. Add/edit/delete events as normal — a one-time event, or a recurring one
   (e.g. "First Tuesday of every month" for board meetings) both work.
3. **To attach a flyer to an event** (so it shows as a "Flyer" link next
   to that event on the website): open the event → **Add attachment** →
   pick or upload the file in Google Drive. The Drive file itself still
   needs to be shared **"Anyone with the link"** — attaching it to the
   event doesn't change its Drive sharing, and a visitor clicking a
   flyer link they can't open is the most likely thing to go wrong here.
4. The live calendar embed on the Events page updates within minutes,
   automatically, no rebuild needed.
5. The Home/Events highlight lists (and any flyer link) catch up on the
   next sync — automatically, within the hour
   (`.github/workflows/sync-events.yml`), and again on every push to
   `main`. To pull the change in immediately instead of waiting:
   **Actions** tab → "Sync events from Google Calendar" → **Run
   workflow**.

**`config/events.json` is now generated, like `pages/*.html`  — don't
hand-edit it,** it'll be overwritten by the next sync. `scripts/sync_calendar_events.py`
reads the calendar's public `.ics` feed and picks up to 6 of the soonest
upcoming events (further out ones just don't make the short-list — the
full calendar embed always has everything regardless), auto-marking the
very next one as "featured" for the big navy card on the Home page. A
`description` for the featured card comes from that event's own
Description field in Google Calendar if you set one, otherwise a generic
line is used. A file attached to an event in Google Calendar (step 3
above) comes through the same way, as a "Flyer" (or "Flyers", if more
than one) link on that event wherever it appears on the site.

**Heads up:** a recurring event (e.g. a monthly meeting) produces one
highlight-list entry per occurrence, so it can crowd out one-off events
further out if there are more than 6 items competing for the list. If
that becomes a real problem, the fix is changing `MAX_EVENTS` in
`scripts/sync_calendar_events.py` (a `src/`-adjacent change — get sign-off
first, per `.claude/CLAUDE.md`) or splitting recurring meetings onto a
separate calendar not included in the sync.

If the calendar has zero upcoming events, both highlight sections
disappear from the site entirely (same empty-list-means-no-section
pattern as sponsors/flyers) — the site never shows an empty "Upcoming
Events" box.

**If the PTA ever switches to a different Google Calendar** (new
account, etc.): update `calendar.calendar_id` (and `calendar.timezone` if
needed) in `config/site.json` and push. The embed, the sync script, the
"Add to Google Calendar" button, the Apple/Outlook subscribe link, and the
`.ics` download link are all built from that one ID — you never edit those
URLs by hand.

---

## Task 4b — Add, remove, or edit a sponsor

**File:** `config/sponsors.json` · **Skill:** `.claude/skills/add-sponsor/`

Each entry is `{ "name": "...", "href": "..." }`. This list is empty by
default (`[]`) — **when it's empty, the whole "Our Sponsors" section on
the Home page doesn't appear at all**, not even as an empty heading. Add
your first entry and the section appears automatically; delete the last
one and it disappears again.

---

## Task 4c — Add, remove, or edit a flyer / document

**File:** `config/flyers.json` · **Skill:** `.claude/skills/add-flyer/`

Each entry is `{ "title": "...", "description": "...", "href": "..." }` —
`href` can be a Google Drive share link (upload the PDF/doc to Drive,
share it "Anyone with the link", copy the link) since this is a normal
read-only share, not an automated upload. Same empty-list-means-no-section
behavior as sponsors — this powers the "Documents & Flyers" section on the
About page, for standing documents (bylaws, handbooks) not tied to a
specific date.

**A flyer for a specific event doesn't go here** — attach it to that
event in Google Calendar instead (Task 4, step 3) so it shows up linked
from that event directly, wherever the event appears.

---

## Task 6 — Change the banner photo, page header photo, or add a logo

Images live in `assets/images/` in this repo and are served directly by
GitHub Pages alongside the HTML — no external hosting, no sharing settings
to manage.

1. Drop the new image file into `assets/images/`.
2. Update `config/site.json` — `hero_image_filename` (Home banner) or `page_header_image_filename` (About/Get Involved/Events header) to that filename.
3. Push. GitHub Actions rebuilds, copies it into the deployed site's `images/` folder, and it's live.

There's no logo yet (`thes__icon-circle` fallbacks and text stand in for
one). When there's a real Thunderbird logo file, it can be added the same
way.

---

## Task 7 — Publish a change

Because Google Sites embeds each page **by URL**, publishing a content
change is just:

```bash
python3 src/build.py     # optional — CI does this too, but good to check locally
git add -A
git commit -m "describe the change"
git push
```

GitHub Actions takes it from there: rebuilds, validates, commits
regenerated `pages/` back if needed, and redeploys to GitHub Pages. The
Google Sites embed shows the update automatically — nothing to touch in
Google Sites itself, ever, for a routine content change.

(The only time you touch Google Sites again is adding a brand-new page —
see `docs/website-setup.md` → "Adding a new page later.")

---

## Verification checklist (before/after pushing)

- [ ] `python3 test/validate_build.py` passes with no failures (or the GitHub Actions run for your commit is green — check the **Actions** tab).
- [ ] Visit the live URL directly (e.g. `https://techmaster-thespta.github.io/thespta/home.html`) to confirm the change is really there.
- [ ] If you changed `theme.json`, spot-checked all 4 pages, not just one — colors are shared.

---

## Yearly board handoff

- This GitHub repo (`techmaster-thespta/thespta`) is the source of truth — hand off repo access (or add the incoming board's GitHub account as a collaborator) along with this doc.
- Nobody needs to know Python to use it — just edit the `.json` files listed above and push; GitHub Actions rebuilds and redeploys automatically.
- The Google account used for Google Sites and Google Calendar should be a shared PTA/"webmaster" account, not a personal one, so ownership doesn't leave with a board member. Google Sites also supports adding co-owners/editors via its own **Share** button if a transition to a shared account hasn't happened yet.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Banner or header image is broken | Filename in `config/site.json` doesn't match a real file in `assets/images/` | Check spelling/extension match exactly, rebuild |
| Calendar embed shows blank/error | Calendar's own sharing isn't public, or wrong `calendar_id` | In Google Calendar → calendar settings → **Access permissions** → "Make available to public" |
| Google Sites shows an old version | The embed is "By URL," which should always be live | Try removing and re-adding the Embed-by-URL block; also hard-refresh the live GitHub Pages URL directly to rule out browser caching |
| `python3 src/build.py` prints `unresolved placeholder(s)` | A config file is missing a field a template expects | Read the warning — it names the exact `{{key}}` — add that field to the relevant `config/*.json` |
| Layout looks broken/overlapping on phone | Usually a hand-edited style with a fixed pixel width or `position: absolute` added outside the existing patterns | Stick to the existing CSS classes in `src/templates/tokens.html.tmpl` rather than adding new inline styles with fixed widths |
| GitHub Actions run failed | See `docs/github-pages-setup.md` → "If something breaks" | |
