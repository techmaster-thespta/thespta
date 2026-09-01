# One-Time Setup: GitHub Access for AI Agents

The `create-issue` and `from-issue` skills (and anything else that files
issues, opens PRs, or pushes branches) need GitHub access. There are two
independent paths — set up whichever matches the agent you're using. Both
can coexist; an agent just uses whichever it has.

## Path 1 — `gh` CLI (Claude Code, or any agent with shell access)

1. Make sure `gh` is installed (`gh --version`). If not: download the
   matching release from [cli.github.com](https://cli.github.com/) — no
   sudo needed, it's a standalone binary you can drop in `~/.local/bin`.
2. Run `gh auth login` — **interactive**, run it yourself, not via an
   agent:
   - Choose **GitHub.com** → **SSH** (reuses the deploy key already set
     up for this repo) → **Login with a web browser** → it prints a
     one-time code and a URL (`github.com/login/device`) — open that on
     any device, enter the code, approve.
3. Verify: `gh auth status` should show you logged in.

This is what the skills use by default (`Bash` + `gh`).

## Path 2 — GitHub MCP server (any MCP-compatible agent)

For an agent that doesn't have shell/Bash access but does support MCP
tools, this repo ships a project-scoped `.mcp.json` declaring GitHub's
official MCP server. It's not hardwired to any token — you provide one via
an environment variable, so the config file itself is safe to commit (and
is already committed).

1. **Create a GitHub Personal Access Token**: GitHub → Settings →
   Developer settings → Personal access tokens → **Fine-grained tokens** →
   generate one scoped to just this repo (`techmaster-thespta/thespta`)
   with **Contents**, **Issues**, and **Pull requests** set to
   **Read and write**. Nothing broader than that.
2. **Set it as an environment variable** wherever the agent runs, e.g. in
   your shell profile or session:
   ```bash
   export GITHUB_PERSONAL_ACCESS_TOKEN="<the token>"
   ```
3. **Docker must be installed and running** — the MCP server runs as a
   container (`ghcr.io/github/github-mcp-server`), pulled automatically on
   first use.
4. Restart/reload the agent session so it picks up `.mcp.json`. Claude
   Code reads project-scoped `.mcp.json` files automatically on startup.

`.mcp.json` in this repo limits the server to the `repos`, `issues`, and
`pull_requests` toolsets — enough for the skills here, nothing wider.

## Which one is actually being used?

Doesn't matter functionally — both give equivalent GitHub access. The
skill files describe the `gh` CLI commands as the concrete reference
implementation; an agent using the MCP tools instead should translate the
same intent (read an issue, open a PR, etc.) into the equivalent MCP tool
calls.

## Security notes

- Never commit an actual token. `.mcp.json` only ever references
  `${GITHUB_PERSONAL_ACCESS_TOKEN}` — the real value lives in your shell
  environment, not in this repo.
- Prefer a fine-grained, repo-scoped token over a classic all-repos token.
- If a token is ever exposed, revoke it immediately at GitHub → Settings →
  Developer settings → Personal access tokens.
