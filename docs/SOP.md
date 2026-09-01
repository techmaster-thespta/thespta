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
config/*.json          ← you edit these (facts: colors, text, events, board, sponsors, flyers)
src/templates/*.tmpl   ← page structure (rarely touched)
        ↓  python3 src/build.py   (or: scripts/build.sh)
pages/*.html            ← generated output
        ↓  git push → GitHub Actions
https://techmaster-thespta.github.io/thespta/*.html   ← the live site, embedded by URL in Google Sites
```

**Golden rule: never hand-edit a file in `/pages`.** It gets silently
overwritten the next time anyone runs the build — including automatically,
by GitHub Actions, on every push to `main`. Every real change happens in
`/config` (data) or `/src/templates` (layout), followed by a rebuild —
and pushing to `main` is what actually makes it live, since GitHub Actions
does the rebuild-and-deploy for you.

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
| `page_urls.*` | The 4 pages' real GitHub Pages URLs — already correct out of the box; only touch this if the repo name or Pages domain ever changes |
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
About page.

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
needed) in `config/site.json` and push. The embed, the "Add to Google
Calendar" button, the Apple/Outlook subscribe link, and the `.ics`
download link are all built automatically from that one ID — you never
edit those URLs by hand.

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
see `docs/website-setup.md`.)

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
