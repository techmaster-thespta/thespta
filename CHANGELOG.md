# Changelog

Notable changes to the Thunder Hill Elementary PTA website, in plain language — meant to be shareable with the board, not just developers. Each release is also published as a [GitHub Release](https://github.com/techmaster-thespta/thespta/releases).

## [0.0.1] - 2026-09-02

First tracked release — a snapshot of everything the site does today.

### Added
- Custom domain (`www.thespta.org`) wired up for the live site.
- The Events page now syncs automatically from the PTA's shared Google Calendar, including recurring events like monthly meetings — no manual updates needed. Runs on its own every hour.
- A flyer or photo attached to a calendar event now shows as a clickable picture preview right next to that event, on both the Home and Events pages.
- Real 2026-2027 board roster with photos, sourced from the board's own announcement graphic. Vacant seats are clearly marked as vacant rather than left blank or faked.
- New "THES Happenings" page embedding the PTA's Smore newsletter directly on the site.
- Real Facebook and Instagram links with icons in the footer.
- The live Google Calendar view now visually highlights which days actually have something on them.

### Changed
- Corrected the school's address (was wrong).
- Updated membership pricing to $16/year, noting the student, individual, faculty/staff, and business tiers.
- Donate and membership buttons now point at the real Givebacks shop instead of placeholder links.
- Rewrote the Get Involved page to lead with membership and make clear, up front, that joining never requires attending meetings or volunteering — that stays entirely optional.
- Board member emails are now shown only for the President, per board preference.

### Fixed
- A mobile navigation bug where clicking a footer link (e.g. "Home") from certain pages could show a browser security error instead of navigating.

---

Format loosely follows [Keep a Changelog](https://keepachangelog.com/). Version numbers follow [Semantic Versioning](https://semver.org/): `MAJOR.MINOR.PATCH`, currently pre-1.0 so anything may still change.
