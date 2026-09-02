---
name: release
description: Verify main is deployable, bump VERSION, write a board-friendly CHANGELOG.md entry, and cut a tagged GitHub Release. Use when the user asks to "cut a release," "make a release," or wants something shareable summarizing recent site changes for the PTA board.
---

# Cut a release

Produces a tagged, versioned snapshot of the site with a plain-language
changelog entry the user can hand to PTA board members — distinct from
`rebuild-now`, which just forces a deploy without any of that record-keeping.

Only run this when the user actually asks for a release. Don't run it
automatically after every change — that would produce noisy, meaningless
releases. It's fine (expected, even) for several unrelated changes to
land on `main` between releases; that's exactly what one release entry
should summarize.

## Steps

### 1. Verify `main` is actually deployable

Same discipline used for every push this whole project:

```bash
git checkout main
git status --short              # must be clean — stop and ask if not
git fetch origin main -q
git log HEAD..origin/main --oneline   # must be empty — pull/rebase first if not
python3 src/build.py
python3 test/validate_build.py  # must pass
```

If anything here fails, fix it before proceeding — never tag a release
on top of a build that doesn't validate.

### 2. Figure out what actually changed since the last release

```bash
git log $(git describe --tags --abbrev=0 2>/dev/null || echo "")..HEAD --oneline
```

(If this is the very first release, there's no previous tag — just
summarize everything notable in the repo so far, like the `0.0.1` entry
already in `CHANGELOG.md` does.)

Read the commits, not just the subject lines, for the real content —
then translate that into 3-8 plain-language bullets a non-technical PTA
board member would understand: what changed for *them*, not what changed
in the code. "The Events page now updates itself from the calendar
automatically" — not "wired scripts/sync_calendar_events.py into a new
GitHub Actions workflow." Group under `### Added` / `### Changed` /
`### Fixed` (skip any group with nothing in it), matching the existing
`CHANGELOG.md` entries' tone and level of detail.

### 3. Decide the version bump

Read the current version from `VERSION` (bare `X.Y.Z`, no `v` prefix, no
trailing content). Default to a **patch** bump (`0.0.1` → `0.0.2`) for
routine content/fixes. Bump **minor** (`0.1.0` → `0.2.0`, reset patch to
0) if this release includes a structural or new-capability change (a new
page, a new automation, a new content type). Only bump **major** if the
user explicitly asks for it — this project is pre-1.0, so breaking
changes aren't really a concept here yet.

### 4. Update `VERSION` and `CHANGELOG.md`

- Overwrite `VERSION` with the new bare version number (plus trailing
  newline).
- Insert a new `## [X.Y.Z] - YYYY-MM-DD` section at the top of
  `CHANGELOG.md` (right below the intro paragraph, above the previous
  newest entry) with today's actual date and the bullets from step 2.

### 5. Commit, tag, and push

```bash
git add VERSION CHANGELOG.md
git commit -m "chore: release vX.Y.Z"
git tag vX.Y.Z
git push origin main
git push origin vX.Y.Z
```

### 6. Create the GitHub Release

```bash
gh release create vX.Y.Z --title "vX.Y.Z" --notes-file <(sed -n '/^## \[X.Y.Z\]/,/^## \[/{/^## \[X.Y.Z\]/d;/^## \[/!p}' CHANGELOG.md)
```

(That `sed` pulls just the new section's body out of `CHANGELOG.md` so
the release notes aren't the whole changelog file — adjust the version
in both `## [...]` patterns to match. If that's fiddly in practice, it's
fine to just paste the section's bullets into `--notes` directly instead.)

### 7. Confirm and report back

```bash
gh release view vX.Y.Z
```

Tell the user the release is live, give them the release URL
(`https://github.com/techmaster-thespta/thespta/releases/tag/vX.Y.Z`),
and mention that's the link to share with the board.

## Do not

- Do not tag/release on top of a dirty working tree, a build that
  doesn't validate, or a `main` that's behind `origin/main`.
- Do not write changelog entries in commit-message/technical language —
  the whole point is that a board member with no technical background
  can read it and understand what's new on the website.
- Do not bump the version without also updating `CHANGELOG.md` in the
  same commit, or vice versa — they always move together.
