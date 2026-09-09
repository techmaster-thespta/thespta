# Flyer review: local automation service

A `systemd --user` timer that runs daily and asks headless Claude Code
to check `config/afterschool-programs.json`, `config/fundraisers.json`,
and `config/pta-meetings.json` for anything flagged
`"needs_review": true`, read the actual flyer, and fill in the real
details — see `.claude/skills/review-afterschool-flyers/SKILL.md`,
`.claude/skills/review-fundraiser-flyers/SKILL.md`, and
`.claude/skills/review-pta-meeting-flyers/SKILL.md` for exactly what
each one does; this doc is just the one-time host setup.

This replaced an earlier version built with Claude Code's session-only
`CronCreate` scheduler: that approach only exists for the lifetime of
one Claude Code session (gone the moment the terminal closes) and
auto-expires after 7 days regardless. This systemd version survives
both, since it's a real OS-level service tied to your user account, not
a running conversation.

It also replaced an even earlier version of itself: one systemd
timer/service per content type (`scripts/afterschool-review/`, before
`config/fundraisers.json` and its own review skill existed). Each flyer
type's actual review logic is genuinely different — different config
schemas; the fundraiser side has to tell a reprinted flyer of an
existing campaign apart from a genuinely new one; the PTA meeting side
has to never guess a date — so each kept its own skill file. But the
systemd plumbing around them (timer, service, install/uninstall) was
identical boilerplate either way, so that layer is merged into one
`scripts/flyer-review/` service that runs all three skills
back-to-back. A fourth flyer-backed content type means one more line in
`run.sh` — already proven twice — not a whole new
service/timer/install.sh trio.

## What actually runs

`scripts/flyer-review/run.sh` calls, one after another in the same run:

```bash
claude -p "/review-afterschool-flyers" --permission-mode bypassPermissions --output-format text
claude -p "/review-fundraiser-flyers" --permission-mode bypassPermissions --output-format text
claude -p "/review-pta-meeting-flyers" --permission-mode bypassPermissions --output-format text
```

**`bypassPermissions` is required, not just convenient.** This runs
with no TTY and no human present — any normal permission prompt would
hang forever waiting for input that can never come. The safety boundary
for this job is the narrow, version-controlled, human-reviewed skill
content it runs (`.claude/skills/review-afterschool-flyers/SKILL.md`,
`.claude/skills/review-fundraiser-flyers/SKILL.md`, and
`.claude/skills/review-pta-meeting-flyers/SKILL.md`), not runtime
permission gating. Know what those skills do before enabling this
service; treat editing any of them with the same care as editing any
other script that runs unattended with your credentials.

Each skill pushes directly to `main` on success (this is treated as
routine content fill, not a design change — see the skill files for
why) and verifies the live site afterward before finishing.

## Prerequisites

- `claude` CLI installed and already logged in as yourself (this service
  runs as your own user account and reuses your existing Claude Code
  credentials — nothing extra to configure for auth).
- `gh` CLI authenticated (used by the skills to watch the deploy).
- The repo cloned at `~/devel/pta` (the unit files below assume this
  path via `%h/devel/pta`; edit both `.service` and `.timer`'s
  `WorkingDirectory`/`ExecStart` lines if your clone lives elsewhere).
- `systemd --user` available. Lingering (so the timer still fires when
  you're not actively logged in) is enabled automatically by
  `install.sh` below if it isn't already on.

## One-time install

If you previously installed the old, afterschool-only
`afterschool-review` service (from before the fundraising page
existed), remove it first — its directory no longer exists in this
repo, so its uninstall script is gone too:

```bash
systemctl --user disable --now afterschool-review.timer
rm -f ~/.config/systemd/user/afterschool-review.service ~/.config/systemd/user/afterschool-review.timer
systemctl --user daemon-reload
```

Then install the current merged service:

```bash
bash scripts/flyer-review/install.sh
```

This symlinks (not copies) the unit files into
`~/.config/systemd/user/`, enables lingering if it isn't already on,
and runs `daemon-reload` + `enable --now`. Symlinking means editing the
unit files in the repo and re-running `systemctl --user daemon-reload`
is enough to pick up changes — no need to re-install. `run.sh` itself
needs even less than that: the `.service` file's `ExecStart` runs it
straight from its path in the repo, so an edit to `run.sh` (like adding
a fourth `run_skill` line) takes effect on the very next scheduled or
manual run, no reload or reinstall at all — this is exactly how the PTA
meetings skill got added to an already-installed service.

To uninstall:

```bash
bash scripts/flyer-review/uninstall.sh
```

This only removes the schedule — the skills, the scripts, and the unit
file templates all stay in the repo either way; re-running `install.sh`
brings it back.

## Checking on it

```bash
systemctl --user status flyer-review.timer     # is it scheduled?
systemctl --user list-timers flyer-review.timer # when's the next run?
systemctl --user start flyer-review.service     # run it right now, on demand
journalctl --user -u flyer-review.service -f    # systemd-level log (start/stop/exit code)
```

The actual Claude Code transcript for each run is a separate log file,
since that's much longer than what belongs in the systemd journal —
both skills' output land in the same file, one after another:

```bash
ls ~/.local/state/thespta-flyer-review/
```
