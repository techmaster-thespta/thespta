# Thunder Hill PTA Website — Standard Operating Procedures

This is the reference doc for **ongoing content edits** — written so a
future board member with no coding background can follow it. For the
one-time initial setup, see `docs/github-pages-setup.md` (GitHub Pages +
the custom domain).

The site is fully self-hosted on **GitHub Pages** at the custom domain
`www.thespta.org` — no Google Sites in the chain anymore. A content
change is just: edit a config file, push, done.

## How the system fits together

```
Google Calendar         ← the PTA's shared calendar (events only — see Task 4)
        ↓  scripts/sync_calendar_events.py (GitHub Actions runs this hourly via sync-events.yml, + on every push via deploy.yml)
config/events.json      ← generated — don't hand-edit
config/*.json           ← everything else you DO edit (colors, text, board, sponsors, flyers, nav)
src/templates/*.tmpl    ← page structure (rarely touched)
        ↓  python3 src/build.py   (or: scripts/build.sh)
pages/*.html            ← generated output (including pages/CNAME for the custom domain)
        ↓  git push → GitHub Actions
https://www.thespta.org/*.html   ← the live site
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
| `newsletter_href` | Footer "Subscribe" link, and the "Subscribe for Future Issues" button on the THES Happenings page — the real Smore newsletter URL |
| `newsletter_embed_src` | The Smore URL actually embedded as an iframe on the THES Happenings page (same newsletter, with `?embedded` appended) — update both together if the Smore newsletter's URL ever changes |
| `custom_domain` | The site's real domain (`www.thespta.org`) — `src/build.py` generates the `CNAME` file GitHub Pages needs from this value on every build. Only touch this if the domain itself changes; see `docs/github-pages-setup.md` for the DNS side. |
| `page_urls.*` | The filename-minus-`.html` slug for each page (e.g. `"index"` for Home, `"get-involved"`) — every internal link resolves as a plain relative filename (`index.html`, `get-involved.html`), which works identically whether the page is reached via the custom domain or the raw `*.github.io` URL. Home is named `index.html` on purpose, so it loads automatically at the domain root — the `page_urls` *key* is still `home` (used throughout templates as `{{page_urls.home}}`), only the underlying filename/value is `index`. |
| `nav` | The header menu's contents, in display order — see Task 5 |
| `copyright_year` | Footer copyright line |

Rebuild + push: `python3 src/build.py` then `git push` (or just push — see Task 7).

---

## Task 2 — Change colors or fonts

**File:** `config/theme.json`

Every color on the site is one named role in `theme.json`'s `colors`
block — change a hex value once here, it updates everywhere that role is
used, on every page, the next time you rebuild. There's no other place
colors live: templates only ever reference a role by name (e.g.
`var(--teal)`), never a hardcoded hex, so this file is genuinely the one
place to edit.

| Role | Default | Where it shows up |
|---|---|---|
| `navy` | `#073B68` | Headings, footer, featured event card, event-date badges, step numbers |
| `yellow` | `#FFD719` | Small cheerful accents only — icon circles, and highlights on the navy featured-event card. Deliberately *not* used for big surfaces or primary buttons. |
| `yellow_text` | `#8A6C00` | Text color paired with a yellow icon-circle background (needs to stay dark for contrast) |
| `teal` | `#159C9C` | Links, eyebrow labels, hover states, and every primary "join in" CTA button (Explore Our Committees, Join the PTA, Volunteer with \_\_\_, etc.) |
| `teal_tint` | `#E1F3F3` | "Members Welcome" committee status badge |
| `coral` | `#F2645A` | One of the "who benefits" icon colors; "Chair Needed" committee status badge |
| `coral_tint` | `#FDE7E5` | "Chair Needed" committee status badge background |
| `bg_tint` | `#EAF6F1` | The alternating section background (a warm light teal) used sitewide for visual rhythm between white and tinted sections — never applied to hero/banner photos |
| `text` / `text_muted` | `#172B3D` / `#566878` | Body text / secondary text |
| `border` | `#DCE5EA` | Card borders (light blue-gray) |

To recolor the site's teal accent everywhere at once, change `teal` (the
saturated version, used for links/buttons/text) and `bg_tint` (its very
light background counterpart) — those two together are what create the
white/teal alternating look. Secondary/utility buttons (calendar
subscribe, newsletter subscribe, membership portal) intentionally stay
navy rather than teal, for visual hierarchy against the primary teal
CTAs — see `src/templates/tokens.html.tmpl`'s `.thes__btn--navy` /
`.thes__btn--teal` if you ever want to change which buttons use which.

Fonts are set under `fonts.display` (headings — Montserrat) and
`fonts.body` (paragraphs — Lato). To change either, you need a font name
Google Fonts actually has, and you must update `google_fonts_url` to match
(go to [fonts.google.com](https://fonts.google.com), pick the font, copy
the `<link>` URL it gives you).

---

## Task 3 — Add, remove, or edit a board member

**File:** `config/board.json` · **Skill:** `.claude/skills/add-board-member/`

Each entry is `{ "role": "...", "name": "...", "email": "...", "photo_filename": "..." }`.
`role` and `name` are required; `email` and `photo_filename` are both
optional — a seat with no photo gets a neutral placeholder icon instead
of a broken image, and a vacant seat (`"name": "Vacant"`) should have
neither. Photo files go in `assets/images/` (flat, no subfolder), same as
the hero/page-header images. Add a new `{ }` entry (comma-separated) for
a new board member, delete one to remove someone (or set its name to
`"Vacant"` if the seat still exists but is unfilled), or edit the text
directly. This list appears once, on the About page.

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
line is used. Every other event on the quick-scan list shows its own
Description too, if it has one — otherwise that row just stays compact
(date/time/title only), no filler text. A file attached to an event in
Google Calendar (step 3 above) comes through the same way, as a "Flyer"
(or "Flyers", if more than one) link on that event wherever it appears on
the site — shown as a small clickable thumbnail preview, not just plain
text, if the attachment is a Drive link (true of anything attached via
the Calendar UI's own "Add attachment" picker). Drive can generate a
preview thumbnail for a PDF as well as an actual image file, so either
kind of flyer shows a picture, not just a link.

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

## Task 5 — Add, remove, or reorder a nav menu item

**File:** `config/site.json` → `nav`

Each entry is `{ "label": "...", "page_url": "<a page_urls.* key>" }`.
Order in the list is left-to-right display order in the header. To add
an existing page to the menu, add an entry pointing at its `page_urls`
key; to remove one from the menu (without deleting the page itself),
delete its entry.

An entry can also carry a `"children"` list (same shape) to become a
dropdown — desktop shows it on hover, mobile lists it indented inside
the already-open mobile menu:

```json
{ "label": "Resources", "page_url": "resources", "children": [
  { "label": "Bylaws", "page_url": "bylaws" },
  { "label": "Committees", "page_url": "committees" }
] }
```

Omit `"page_url"` on a parent entry to make it a dropdown-only label with
no page of its own. **Adding a genuinely new page** (not just adding an
existing one to the nav) is a bigger step — new template, new
`page_urls` entry — that's a `src/` change; ask before doing it, per
`.claude/CLAUDE.md`.

---

## Task 5b — Add, remove, or edit a committee

**File:** `config/committees.json` · **Skill:** `.claude/skills/add-committee/`

All committees live on **one** page, `/get-involved/committees` — there's
no per-committee page or URL, by design (so adding a committee is a
one-line config change, not a new page). Each entry:

```json
{ "name": "Hospitality", "slug": "hospitality", "status": "chair-needed", "chair": null,
  "description": "...", "activities": ["...", "..."], "audiences": ["staff"],
  "volunteerValue": "Hospitality" }
```

`status` (`"chair-needed"` or `"members-welcome"`) controls which of the
page's two sections the card appears in and which badge it shows —
moving a committee between them is just changing this one field (and
`chair`, to match). See the skill for the full field reference.

### One-time setup: the shared volunteer Google Form

Every committee's "Volunteer with ___" button opens the **same** Google
Form, with the committee name pre-filled via a
[prefilled-link URL](https://support.google.com/docs/answer/9308501) —
`config/site.json`'s `volunteerForm` block controls this for every
committee at once:

```json
"volunteerForm": {
  "baseUrl": "https://docs.google.com/forms/d/e/REPLACE_WITH_REAL_FORM_ID/viewform",
  "committeeFieldId": "entry.REPLACE_WITH_REAL_ENTRY_ID"
}
```

**This ships with placeholder values that don't go anywhere real yet.**
To wire up the actual form:

1. Create the Google Form (one "Committee" short-answer or dropdown
   field, plus whatever else you want to collect).
2. In the form editor, click the **⋮** menu → **Get pre-filled link**.
3. Fill in the Committee field with any sample value, fill in nothing
   else that should stay blank, then click **Get link**.
4. Copy the generated URL — it looks like
   `https://docs.google.com/forms/d/e/1FAI.../viewform?usp=pp_url&entry.123456789=Sample`.
   Split it into the two config values:
   - `baseUrl`: everything up to (not including) the `?` —
     `https://docs.google.com/forms/d/e/1FAI.../viewform`
   - `committeeFieldId`: the `entry.XXXXXXXXX` part right before `=Sample`
     (drop `usp=pp_url` and the `=Sample` value — the site builds that
     part itself per committee).
5. Update both values in `config/site.json`, rebuild, and check a few
   "Volunteer with ___" buttons on the live Committees page actually land
   on the form with the right committee pre-filled.

---

## Task 5c — Add, remove, or edit an afterschool program

**File:** `config/afterschool-programs.json` · **Skill:** `.claude/skills/add-afterschool-program/`

Every program on `/afterschool-programs` is run by an outside provider
(iCode, KidzArt, a theatre company, etc.) — **not** the PTA or the
school — so the page says so explicitly, and every card is expected to
carry its own registration link/contact info. Each entry's flyer is a
Google Drive file, shown as a thumbnail exactly the way an event's
calendar attachment already is — no image is ever downloaded into this
repo.

### This page is normally kept up to date automatically

`.github/workflows/sync-afterschool-flyers.yml` runs daily and
reconciles `config/afterschool-programs.json` against whatever's
actually in the shared Drive folder
(`config/site.json`'s `afterschool_flyers_folder_id`):

- A flyer removed from the folder → its card disappears.
- A brand-new flyer → a placeholder card appears (name guessed from the
  filename, flagged `"needs_review": true`) until someone fills in the
  real program details.
- A changed flyer (same file, different content) → flagged
  `"needs_review": true`, old details left in place rather than wiped.

**Reading what a flyer actually says (writing the real name, schedule,
price, description) is not something this automation can do on its
own** — that's the same kind of visual-understanding task the first
version of this page was built with. Whenever an entry is flagged
`needs_review`, open its `flyer_drive_file_id` in Drive (or ask an agent
to), read the flyer, and update the entry by hand — then clear the flag.

### One-time setup: the Drive API key

The daily sync needs a `GOOGLE_DRIVE_API_KEY` repo secret to actually
list the folder (unlike the events calendar, Drive has no equivalent
public, unauthenticated feed for "list a folder's files" — this is the
one piece of afterschool-programs automation that genuinely needs a
credential). Until this secret exists, the workflow no-ops harmlessly
(no daily failure emails) — the page just doesn't auto-update until it's
set up.

1. In [Google Cloud Console](https://console.cloud.google.com/), create
   or pick a project, then **APIs & Services → Library**, and enable the
   **Google Drive API**.
2. **APIs & Services → Credentials → Create Credentials → API key.**
3. Click into the new key and, under **API restrictions**, restrict it
   to **Google Drive API** only (defense in depth — an API key alone,
   with no OAuth identity attached, can only ever read files that are
   already public, so a leaked key can't expose anything private
   regardless, but restricting it limits what it's good for if leaked).
4. Copy the key. In this GitHub repo: **Settings → Secrets and
   variables → Actions → New repository secret**, name it
   `GOOGLE_DRIVE_API_KEY`, paste the value.
5. Trigger the workflow once by hand (`gh workflow run
   sync-afterschool-flyers.yml` or the Actions tab's "Run workflow"
   button) and watch it succeed.

If the shared folder itself ever needs to change, update
`afterschool_flyers_folder_id` in `config/site.json` — it's the last
segment of the folder's URL
(`drive.google.com/drive/folders/<this-part>`).

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

The site is served directly from what's in this repo, so publishing a
content change is just:

```bash
python3 src/build.py     # optional — CI does this too, but good to check locally
git add -A
git commit -m "describe the change"
git push
```

GitHub Actions takes it from there: rebuilds, validates, commits
regenerated `pages/` back if needed, and redeploys to GitHub Pages —
`https://www.thespta.org` shows the update automatically.

**Want it live immediately** instead of waiting on the push-triggered
pipeline or the hourly calendar sync? Trigger a rebuild directly:
**Actions** tab → "Build, validate, and deploy to GitHub Pages" → **Run
workflow**. If you're asking an AI agent to do this, it's the
`rebuild-now` skill (`.claude/skills/rebuild-now/`).

**Want a shareable summary of what's new** — e.g. to send the board an
update? That's a release, not just a push: ask an AI agent to use the
`release` skill (`.claude/skills/release/`), which bumps `VERSION`,
writes a plain-language entry in `CHANGELOG.md`, and cuts a tagged
GitHub Release at
`https://github.com/techmaster-thespta/thespta/releases`. Only do this
when you actually want a shareable snapshot — not after every small
change.

---

## Verification checklist (before/after pushing)

- [ ] `python3 test/validate_build.py` passes with no failures (or the GitHub Actions run for your commit is green — check the **Actions** tab).
- [ ] Visit the live URL directly (e.g. `https://www.thespta.org/`) to confirm the change is really there.
- [ ] If you changed `theme.json`, spot-checked every page, not just one — colors are shared.

---

## Yearly board handoff

- This GitHub repo (`techmaster-thespta/thespta`) is the source of truth — hand off repo access (or add the incoming board's GitHub account as a collaborator) along with this doc.
- Nobody needs to know Python to use it — just edit the `.json` files listed above and push; GitHub Actions rebuilds and redeploys automatically.
- The Google account used for Google Calendar should be a shared PTA/"webmaster" account, not a personal one, so ownership doesn't leave with a board member.
- Whoever manages `thespta.org`'s DNS (domain registrar access) needs to be someone with institutional continuity too — that's a separate credential from GitHub/Google and only needed if the domain itself ever moves (see `docs/github-pages-setup.md`).

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Banner or header image is broken | Filename in `config/site.json` doesn't match a real file in `assets/images/` | Check spelling/extension match exactly, rebuild |
| Calendar embed shows blank/error | Calendar's own sharing isn't public, or wrong `calendar_id` | In Google Calendar → calendar settings → **Access permissions** → "Make available to public" |
| `www.thespta.org` shows an old version | Should always be live within a minute or two of a successful deploy | Hard-refresh to rule out browser caching; check the **Actions** tab for a recent green run |
| `python3 src/build.py` prints `unresolved placeholder(s)` | A config file is missing a field a template expects | Read the warning — it names the exact `{{key}}` — add that field to the relevant `config/*.json` |
| Layout looks broken/overlapping on phone | Usually a hand-edited style with a fixed pixel width or `position: absolute` added outside the existing patterns | Stick to the existing CSS classes in `src/templates/tokens.html.tmpl` rather than adding new inline styles with fixed widths |
| GitHub Actions run failed | See `docs/github-pages-setup.md` → "If something breaks" | |
| Custom domain broken (SSL warning, wrong content, "domain not verified") | DNS or GitHub Pages custom-domain config issue, not a code problem | See `docs/github-pages-setup.md` → "Point the custom domain at GitHub Pages" |
