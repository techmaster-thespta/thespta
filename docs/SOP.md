# Thunder Hill PTA Website — Standard Operating Procedures

This is the reference doc for **ongoing content edits** — written so a
future board member with no coding background can follow it. For the
one-time initial setup, see `docs/website-setup.md` (Google Sites) and
`docs/drive-cicd-setup.md` (GitHub Actions → Google Drive).

The site itself lives on **Google Sites**; this repo (`config/`, `src/`) is
the tool that generates the HTML you paste into it.

## How the system fits together

```
config/*.json          ← you edit these (facts: colors, text, events, board, sponsors, flyers)
src/templates/*.tmpl   ← page structure (rarely touched)
        ↓  python3 src/build.py   (or: scripts/build.sh)
pages/*.html            ← generated output — paste these into Google Sites
```

**Golden rule: never hand-edit a file in `/pages`.** It gets silently
overwritten the next time anyone runs the build — including automatically,
by GitHub Actions, on every push to `main`. Every real change happens in
`/config` (data) or `/src/templates` (layout), followed by a rebuild.

**If you're an AI agent (Claude or otherwise) making a content change**:
check `.claude/skills/` first — there's a dedicated skill for each kind of
addition (event, board member, sponsor, flyer/document). Those skills are
scoped to **config-only edits** and are the preferred path. Only touch
`src/` if the user explicitly asks for a structural/design change.

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
| `donate_href` | Where the "Donate" buttons point (Support THES card) |
| `membership_portal_href` | Where "Join PTA" / "Become a Member" buttons point |
| `social.facebook_href`, `social.instagram_href` | Footer social links |
| `newsletter_href` | Footer "Subscribe" link |
| `page_urls.*` | **Fill these in once each page is published** (see Task 7) — every internal button/footer link on the site points here |
| `copyright_year` | Footer copyright line |

Rebuild: `python3 src/build.py`, then re-paste the affected page(s) into Google Sites (Task 8).

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

Rebuild after any change: `python3 src/build.py`.

---

## Task 3 — Add, remove, or edit a board member

**File:** `config/board.json` · **Skill:** `.claude/skills/add-board-member/`

Each entry is `{ "role": "...", "name": "...", "email": "..." }`. Add a new
`{ }` entry (comma-separated) for a new board member, delete one to remove
someone, or edit the text directly. This list appears once, on the About
page.

Rebuild: `python3 src/build.py`, then re-paste `pages/about.html` into Google Sites.

---

## Task 4 — Add, remove, or edit an event (the static highlights)

**File:** `config/events.json` · **Skill:** `.claude/skills/add-event/`

This powers two things: the "Upcoming Events" preview on the Home page
(one big featured event + a short list), and the quick-scan list at the
top of the Events page. **It is separate from the live Google Calendar**
embedded further down the Events page (see Task 5) — this file is for
short, hand-picked highlights; the calendar is the full, always-current
schedule.

Each entry looks like:
```json
{ "day": "15", "month": "Sep", "title": "Back-to-School Picnic", "when": "5:30 – 7:00 PM · Courtyard", "featured": false }
```

- Exactly **one** entry should have `"featured": true` — that one becomes the big navy card on the Home page. Give it a `"description"` field too (a one-sentence blurb) — the featured card shows it, others don't need it.
- The order in this file is the order events appear everywhere.
- To remove an event, delete its `{ }` block. To add one, copy an existing block and edit it.

Rebuild: `python3 src/build.py`, then re-paste `pages/home.html` and `pages/events.html`.

---

## Task 4b — Add, remove, or edit a sponsor

**File:** `config/sponsors.json` · **Skill:** `.claude/skills/add-sponsor/`

Each entry is `{ "name": "...", "href": "..." }`. This list is empty by
default (`[]`) — **when it's empty, the whole "Our Sponsors" section on
the Home page doesn't appear at all**, not even as an empty heading. Add
your first entry and the section appears automatically; delete the last
one and it disappears again.

Rebuild: `python3 src/build.py`, then re-paste `pages/home.html`.

---

## Task 4c — Add, remove, or edit a flyer / document

**File:** `config/flyers.json` · **Skill:** `.claude/skills/add-flyer/`

Each entry is `{ "title": "...", "description": "...", "href": "..." }` —
`href` should be a Google Drive share link (upload the PDF/doc to Drive
first, share it "Anyone with the link", copy the link). Same
empty-list-means-no-section behavior as sponsors — this powers the
"Documents & Flyers" section on the About page.

Rebuild: `python3 src/build.py`, then re-paste `pages/about.html`.

---

## Task 5 — Update the actual event schedule (live calendar)

The Events page embeds a real Google Calendar, which is **not** part of
this build system — it updates itself the moment you add/edit/delete an
event in Google Calendar directly. No rebuild needed for this.

1. Go to [calendar.google.com](https://calendar.google.com), find the
   PTA's shared calendar in the left sidebar (matches the `calendar_id` in
   `config/site.json` under `calendar`).
2. Add/edit/delete events as normal.
3. Changes appear on the website within a few minutes automatically.

**If the PTA ever switches to a different Google Calendar** (new
account, etc.): update `calendar.calendar_id` (and `calendar.timezone` if
needed) in `config/site.json`, rebuild, and re-paste `pages/events.html`.
The embed, the "Add to Google Calendar" button, the Apple/Outlook
subscribe link, and the `.ics` download link are all built automatically
from that one ID — you never edit those URLs by hand.

---

## Task 6 — Change the banner photo, page header photo, or add a logo

Images are hosted on Google Drive, not embedded in the HTML directly —
this keeps the pasted code small and images easy to swap.

1. Upload the new photo to Google Drive.
2. Right-click it → **Share** → set to **Anyone with the link** (Viewer). Required, or the image shows broken to visitors. (If it's uploaded straight into the CI-managed "PTA Website" Drive folder, this is already handled — see `docs/drive-cicd-setup.md`.)
3. Copy the file's share link, pull out the ID (the long string between `/d/` and `/view`).
4. Paste that ID into `config/site.json` — `hero_image_drive_id` (Home banner) or `page_header_image_drive_id` (About/Get Involved/Events header).
5. Rebuild: `python3 src/build.py`, re-paste the affected page(s).

There's no logo yet (`thes__icon-circle` fallbacks and text stand in for
one). When there's a real Thunderbird logo file, it can be added the same
way — a Drive-hosted image slot in the templates.

---

## Task 7 — Fill in real page links (do this once, right after publishing)

Every internal link on the site (footer nav, "Get Involved" buttons, "View
Events" links, etc.) currently points at `#` via `config/site.json` →
`page_urls`. Once each page is published in Google Sites and has a real
URL (e.g. `https://sites.google.com/view/thunderhillpta/events`):

1. Open `config/site.json`, find `page_urls`.
2. Replace each `"#"` with that page's real published URL.
3. Rebuild: `python3 src/build.py`.
4. Re-paste **all 4 pages** into Google Sites (every page's footer links to every other page, so all 4 files change).

---

## Task 8 — Publish a change to Google Sites

After any rebuild:

1. Open the relevant file in `/pages` (e.g. `pages/home.html`), select all, copy. (Or grab it from the Drive `pages/` folder — GitHub Actions keeps that in sync automatically on every push to `main`.)
2. In the Google Sites editor, go to that page.
3. **If the Embed block already exists:** click directly on it (the embedded content, not the page background) → a toolbar appears → click the **pencil/edit icon** → it reopens the code box → select all the old code, paste the new version, click **Update**.
4. **If there's no Embed block yet:** click where you want it → **Insert → Embed → Embed code** → paste → **Insert**.
5. Click **Publish** (top-right) to push the change live. Editing a page doesn't go live until you publish.

---

## Verification checklist (before publishing anything)

- [ ] `python3 test/validate_build.py` passes with no failures (or the GitHub Actions run for your commit is green).
- [ ] Opened the page in Google Sites' **Preview** (eye icon), checked both desktop and the mobile toggle inside preview.
- [ ] Clicked every button/link on the page you changed — nothing points at a stray `#` you forgot to fill in (Task 7).
- [ ] If you changed `theme.json`, spot-checked all 4 pages, not just one — colors are shared.

---

## Yearly board handoff

- This GitHub repo (`techmaster-thespta/thespta`) is the source of truth — hand off repo access (or add the incoming board's GitHub account as a collaborator) along with this doc.
- Nobody needs to know Python to use it — just edit the `.json` files listed above; GitHub Actions rebuilds and pushes to Drive automatically on every push to `main`.
- The Google account used for Google Sites, Google Calendar, and Drive should be a shared PTA/"webmaster" account, not a personal one, so ownership doesn't leave with a board member. Google Sites also supports adding co-owners/editors via its own **Share** button if a transition to a shared account hasn't happened yet.
- If GitHub Actions' Drive credentials (the OAuth refresh token) ever need rotating — e.g. a departing board member set them up — see `docs/drive-cicd-setup.md`.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Banner or header image shows a broken image icon | Drive file's sharing was changed or the file was moved/deleted | Re-check Task 6, step 2 — must stay "Anyone with the link" |
| Calendar embed shows blank/error | Calendar's own sharing isn't public, or wrong `calendar_id` | In Google Calendar → calendar settings → **Access permissions** → "Make available to public" |
| A page's colors look wrong after a theme edit | Old page wasn't re-pasted after rebuild | Re-copy that page's file from `/pages` into Google Sites again |
| `python3 src/build.py` prints `unresolved placeholder(s)` | A config file is missing a field a template expects | Read the warning — it names the exact `{{key}}` — add that field to the relevant `config/*.json` |
| Layout looks broken/overlapping on phone | Usually a hand-edited style with a fixed pixel width or `position: absolute` added outside the existing patterns | Stick to the existing CSS classes in `src/templates/tokens.html.tmpl` rather than adding new inline styles with fixed widths |
| GitHub Actions run failed | See `docs/drive-cicd-setup.md` → "If something breaks" | |
