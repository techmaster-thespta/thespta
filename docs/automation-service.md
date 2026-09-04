# Afterschool-flyer review: local automation service

A `systemd --user` timer that runs daily and asks headless Claude Code
to check `config/afterschool-programs.json` for anything flagged
`"needs_review": true`, read the actual flyer, and fill in the real
program details — see
`.claude/skills/review-afterschool-flyers/SKILL.md` for exactly what it
does; this doc is just the one-time host setup.

This replaced an earlier version built with Claude Code's session-only
`CronCreate` scheduler: that approach only exists for the lifetime of
one Claude Code session (gone the moment the terminal closes) and
auto-expires after 7 days regardless. This systemd version survives
both, since it's a real OS-level service tied to your user account, not
a running conversation.

## What actually runs

`scripts/afterschool-review/run.sh` calls:

```bash
claude -p "/review-afterschool-flyers" --permission-mode bypassPermissions --output-format text
```

**`bypassPermissions` is required, not just convenient.** This runs
with no TTY and no human present — any normal permission prompt would
hang forever waiting for input that can never come. The safety boundary
for this job is the narrow, version-controlled, human-reviewed skill
content it runs (`.claude/skills/review-afterschool-flyers/SKILL.md`),
not runtime permission gating. Know what that skill does before
enabling this service; treat editing it with the same care as editing
any other script that runs unattended with your credentials.

The skill itself pushes directly to `main` on success (this is treated
as routine content fill, not a design change — see the skill file for
why) and verifies the live site afterward before finishing.

## Prerequisites

- `claude` CLI installed and already logged in as yourself (this service
  runs as your own user account and reuses your existing Claude Code
  credentials — nothing extra to configure for auth).
- `gh` CLI authenticated (used by the skill to watch the deploy).
- The repo cloned at `~/devel/pta` (the unit files below assume this
  path via `%h/devel/pta`; edit both `.service` and `.timer`'s
  `WorkingDirectory`/`ExecStart` lines if your clone lives elsewhere).
- `systemd --user` available and lingering enabled for your account, so
  the timer still fires when you're not actively logged in:

  ```bash
  loginctl enable-linger "$(whoami)"
  ```

## One-time install

```bash
mkdir -p ~/.config/systemd/user
ln -s ~/devel/pta/scripts/afterschool-review/afterschool-review.service ~/.config/systemd/user/
ln -s ~/devel/pta/scripts/afterschool-review/afterschool-review.timer ~/.config/systemd/user/

systemctl --user daemon-reload
systemctl --user enable --now afterschool-review.timer
```

Symlinking (rather than copying) means editing the unit files in the
repo and running `systemctl --user daemon-reload` is enough to pick up
changes — no need to re-copy anything.

## Checking on it

```bash
systemctl --user status afterschool-review.timer     # is it scheduled?
systemctl --user list-timers afterschool-review.timer # when's the next run?
systemctl --user start afterschool-review.service     # run it right now, on demand
journalctl --user -u afterschool-review.service -f    # systemd-level log (start/stop/exit code)
```

The actual Claude Code transcript for each run is a separate log file,
since that's much longer than what belongs in the systemd journal:

```bash
ls ~/.local/state/thespta-afterschool-review/
```

## Uninstalling

```bash
systemctl --user disable --now afterschool-review.timer
rm ~/.config/systemd/user/afterschool-review.service ~/.config/systemd/user/afterschool-review.timer
systemctl --user daemon-reload
```

(This only removes the schedule — the skill, the script, and the unit
file templates all stay in the repo either way.)
