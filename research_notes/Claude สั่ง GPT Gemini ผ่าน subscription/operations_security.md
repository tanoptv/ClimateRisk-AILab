# Operations and Security of a Claude-led multi-vendor agent pipeline (Claude -> Codex CLI + Gemini CLI) run unattended on a home computer via Claude Code Remote Control (as of 2026-11-03)

Research limitations: in this session the hosts developers.openai.com, google-gemini.github.io and geminicli.com did not resolve (blocked by the session network allowlist). Official Codex and Gemini pages could therefore NOT be fetched directly. Codex/Gemini claims below come from WebSearch result summaries (which paraphrase the official pages and third-party blogs) and are marked [unverified-secondary] unless quoted from a page I fetched. Claude Code claims are quoted from fetched code.claude.com pages.

## 1. Remote Control constraints (computer on, process running, ANTHROPIC_BASE_URL) - confirm from docs

### Takeaway
Confirmed from the official page: the computer must stay on, the `claude` process must keep running, subscription login is required (no API keys), and a non-default `ANTHROPIC_BASE_URL` disables Remote Control. Server mode gives up after about 10 minutes of network outage and exits; use tmux/screen and a service supervisor.

### Cited Findings
- "The web and mobile interfaces are a window into that local session, so your computer has to stay on and the `claude` process has to keep running." — [Remote Control](https://code.claude.com/docs/en/remote-control)
- "Subscription: available on Pro, Max, Ultra, Team, and Enterprise plans. API keys are not supported." — [Remote Control](https://code.claude.com/docs/en/remote-control)
- API endpoint: not available if "You point `ANTHROPIC_BASE_URL` at a host other than `api.anthropic.com`, such as an LLM gateway or proxy. Unset the variable to use Remote Control." Also unavailable on Bedrock, Google Cloud Agent Platform, Microsoft Foundry, or an enterprise Claude apps gateway. — [Remote Control](https://code.claude.com/docs/en/remote-control)
- Auth error text: "Remote Control requires claude.ai subscription auth." followed by the credential in use, e.g. "ANTHROPIC_API_KEY is set, so this session is using API-key auth"; `apiKeyHelper` and `ANTHROPIC_AUTH_TOKEN` are named the same way. — [Remote Control](https://code.claude.com/docs/en/remote-control)
- "Local process must keep running: ... If you close the terminal, quit the Desktop app or VS Code ... or otherwise stop the `claude` process, the session goes offline until you bring it back. If you run `claude` from a terminal on a remote machine, start it inside `tmux` or `screen`..." — [Remote Control](https://code.claude.com/docs/en/remote-control)
- Sleep/network: "if your laptop sleeps or your network drops, Claude Code reconnects automatically when your machine comes back online." But a sleeping machine cannot run the pipeline. — [Remote Control](https://code.claude.com/docs/en/remote-control)
- Extended outage: "Server mode: Claude Code gives up after roughly 10 minutes and the `claude remote-control` process exits. Run `claude remote-control` again..." Interactive session: "retries for as long as the outage lasts and reconnects on its own." — [Remote Control](https://code.claude.com/docs/en/remote-control)
- Server mode flags: `--capacity <N>` (default 32 concurrent sessions), `--permission-mode <mode>` sets starting mode for the server's sessions, `--spawn worktree|same-dir` (worktree gives on-demand sessions isolated git worktrees; requires a git repo or WorktreeCreate hook), `--continue`/`--session-id` to resume (v2.1.200+). — [Remote Control](https://code.claude.com/docs/en/remote-control)
- Data flow: "While Remote Control is connected, the session transcript, including your messages, Claude's responses, and tool activity, is stored on Anthropic servers." Execution stays local. Anything Codex/Gemini returns into Claude's context therefore also lands in that transcript. — [Remote Control](https://code.claude.com/docs/en/remote-control)
- Trusted Devices (off by default on Pro/Max/Ultra) "requires a verified device before you can view or steer Remote Control sessions" - recommended since the phone is the control surface. — [Remote Control](https://code.claude.com/docs/en/remote-control)
- 403 handling: connected interactive sessions retry up to three minutes on HTTP 403 (VPN/proxy changes), then disconnect. — [Remote Control](https://code.claude.com/docs/en/remote-control)
- Remote Control security model: "All code execution and file access stays local ... No cloud VMs or sandboxing are involved." — [Security](https://code.claude.com/docs/en/security)

### Inferences
- Recommended supervisor: run `claude remote-control --spawn worktree --permission-mode <restricted mode>` under tmux or a systemd user service with auto-restart and OS sleep disabled; because server mode exits after about 10 minutes offline, a supervisor restart loop is needed.
- Because there is no sandbox around a Remote Control session by default, any isolation (container/VM/sandbox runtime) must be added by you.
- Do not set `ANTHROPIC_BASE_URL` or `ANTHROPIC_API_KEY` in the shell that starts Claude; a cost-saving gateway or API-key fallback is incompatible with Remote Control.

### Gaps
- Not verified: whether `claude remote-control` survives OS-level token expiry for weeks unattended (no doc passage found on refresh of claude.ai login for long-running servers).

## 2. Combined quota behavior, latency/timeouts, capping runs

### Takeaway
Three independent quota pools (Anthropic subscription, ChatGPT/Codex, Google) are not shared, so a fan-out drains each separately; the Claude pool is the one that also pays for the orchestration and summarization tokens. Limits are opaque and change often; cap fan-out by count and wall-clock in your own wrapper.

### Cited Findings
- Claude: subagents, terminal Claude Code, chat and cloud sessions draw from one subscription pool with a rolling 5-hour window plus a separate weekly cap; Anthropic does not publish prompt counts (community estimates only). — secondary summary via [WebSearch result: multiple blogs, e.g. alexcloudstar.com](https://alexcloudstar.com/blog/claude-code-usage-limits-2026/) [unverified-secondary]
- Claude: one October 2026 article reports weekly Claude Code limits were raised 25% from Sept 14. — [WebSearch summary, third-party] [unverified]
- Codex: Plus has a 5-hour window plus weekly cap again (5-hour limit removed 2026-07-12, scheduled to return 2026-08-25); $100/$200 Pro tiers reported exempt from 5-hour limit with weekly cap only; Oct 29, 2026 reported doubling of limits for Pro 100/200/500. Metering is reportedly credits/tokens since 2026-04-02 rather than per-message. — [Pillitteri](https://pasqualepillitteri.it/en/news/12697/openai-codex-chatgpt-work-5-hour-limit-plus), [Notebookcheck](https://www.notebookcheck.net/OpenAI-abruptly-restores-harsh-5-hour-Codex-and-Work-limits-for-ChatGPT-Plus.1378377.0.html), [aiidelist](https://aiidelist.com/blog/codex-5-hour-limit-plus-pro) [unverified-secondary; sources conflict on details]
- Gemini CLI (Google login): per-user daily request caps - Code Assist Individual 1,000, Google AI Pro 1,500, AI Ultra 2,000; Gemini API free key 250/day Flash only. "Agent mode and the CLI share one quota pool, and one prompt might result in multiple model requests." — [Gemini CLI quotas and pricing](https://geminicli.com/docs/resources/quota-and-pricing/) (via search snippet; page not fetched)
- Gemini: a May 2026 third-party post claims a move to compute-based quotas, conflicting with the flat numbers above. — [taxheal.com](https://www.taxheal.com/?p=132163) [unverified]
- Gemini: forum report of an AI Pro user stuck at 250/day because the cached auth token predated the upgrade; fix suggested was re-authenticating. — [Google AI forum](https://discuss.ai.google.dev/t/pro-plan-cli-quota-stuck-at-250-provisioning-issue/113645) [community report]
- Remote Control server mode default capacity is 32 concurrent sessions; lower it with `--capacity`. — [Remote Control](https://code.claude.com/docs/en/remote-control)

### Inferences
- A single user request that fans out to Codex + Gemini consumes: Claude tokens (prompt, tool results, summary), one Codex task, and one-to-many Gemini requests (agent loop multiplies requests). Gemini is the least predictable per-task cost.
- Cap runs with: `timeout` on each external call, a per-task max of one call per vendor, a daily counter file/db that refuses fan-out beyond N, `--capacity 1-2`, and a kill switch. Headless calls into agentic CLIs can run many minutes; no official latency figures were found.
- Failure symptoms to detect and surface to Claude: non-zero exit, 429/quota errors, empty output; have the wrapper return a structured "vendor unavailable" result rather than retrying.

### Gaps
- No official numbers for headless latency or hard timeouts of `codex exec` / `gemini -p`; could not fetch headless docs (blocked hosts).
- Current official Claude Pro limits not retrieved (Anthropic publishes none as prompt counts).

## 3. Unattended auth persistence (Codex, Gemini) and failure symptoms

### Takeaway
Codex caches ChatGPT login in `~/.codex/auth.json` (or OS keyring) with automatic refresh while in use; headless setup uses device-code login or copying auth.json. Gemini caches OAuth creds under `~/.gemini/` and refreshes via refresh token, but browser OAuth is awkward headless; API key or Vertex is the vendor-recommended unattended route. Subscription logins in unattended automation may violate vendor expectations (unverified).

### Cited Findings
- Codex: "Codex caches login details locally in a plaintext file at `~/.codex/auth.json` or in your OS-specific credential store"; backend set by `cli_auth_credentials_store` = file | keyring | auto. — [Codex auth](https://developers.openai.com/codex/auth) (via search summary) [unverified-secondary]
- Codex headless: `codex login --device-auth` (beta; must be enabled in ChatGPT security settings or workspace permissions; otherwise falls back to browser flow). Fallback: log in on a browser machine and copy `auth.json`. — [Codex auth](https://developers.openai.com/codex/auth), [danielvaughan.com guide](https://codex.danielvaughan.com/2026/04/01/codex-cli-authentication-flows-credential-management/) [unverified-secondary]
- Codex refresh: access token refreshes automatically during active use; concurrent jobs sharing one auth.json can race on refresh; official page says API keys remain the recommended default for automation. — same sources [unverified-secondary]
- Gemini: credentials cached in `~/.gemini/oauth_creds.json`; refresh token used to get new access tokens; if refresh token expires you must re-run auth. — [Roo Code doc](https://docs.roocode.com/providers/gemini-cli), [aguidetocloud](https://claw.aguidetocloud.com/google/gemini-cli/auth/) [unverified-secondary]
- Gemini in CI: one guide says OAuth needs a browser and recommends Gemini API key or Vertex service account for CI. — [aguidetocloud](https://claw.aguidetocloud.com/google/gemini-cli/auth/) [unverified-secondary]

### Inferences
- Failure symptoms (not documented; expected): Codex "not logged in"/401 on exec after refresh token revocation or concurrent-refresh race; Gemini prompting for interactive OAuth in headless mode (hang) - so always wrap with a timeout and stdin closed (`< /dev/null`).
- Serialize Codex calls (mutex) to avoid refresh races; run a daily cheap health-check call and alert via Remote Control/phone push when it fails.
- Using subscription logins for automated fan-out may conflict with vendor ToS/quota expectations - not verified; check each vendor's terms.

### Gaps
- No primary-source confirmation of Codex/Gemini refresh-token lifetime or behavior on a machine idle for weeks.
- Could not confirm whether Gemini official docs support device-flow/headless OAuth.

## 4. Permission and sandbox settings for unattended external CLIs, and what NOT to enable

### Takeaway
Run Codex in `workspace-write` (or `read-only` for pure advice) with network off and prefer no escalation; run Gemini in its sandbox (`-s`/`GEMINI_SANDBOX`) and avoid `--yolo`; for Claude use `acceptEdits`/`dontAsk` with explicit allow rules or auto mode, never `bypassPermissions` on the host.

### Cited Findings
- Codex: network off by default; in workspace-write it stays off unless `network_access = true` under `sandbox_workspace_write`; approvals can be disabled with `--ask-for-approval never` / `-a never`; `workspace-write` + `on-request` is the lower-risk preset, whereas `danger-full-access` + `never` is the risky pairing. — [Codex sandbox](https://developers.openai.com/codex/sandbox) (via search summary) [unverified-secondary]
- Codex: protected paths `.git/`, `.agents/`, `.codex/` stay read-only in workspace-write — third-party only. — [danielvaughan.com](https://codex.danielvaughan.com/2026/03/26/codex-cli-approval-modes-sandbox-security) [unverified]
- Gemini sandbox methods: macOS Seatbelt, Docker/Podman, Windows native, gVisor/runsc ("Strongest isolation available"), LXC. Enable with "`-s` or `--sandbox`" or "`GEMINI_SANDBOX=true|docker|podman|sandbox-exec|runsc|lxc`". — [Gemini CLI sandbox docs (raw GitHub)](https://raw.githubusercontent.com/google-gemini/gemini-cli/main/docs/cli/sandbox.md)
- Gemini `--yolo`: forum guidance advises against it unless you know what the command does. — [Google AI forum](https://discuss.ai.google.dev/t/pro-plan-cli-quota-stuck-at-250-provisioning-issue/113645) [community, weak]
- Claude auto mode: "A separate classifier model reviews actions before they run, blocking anything that escalates beyond your request, targets unrecognized infrastructure, or appears driven by hostile content Claude read." and "Auto mode reduces permission prompts but does not guarantee safety." — [Permission modes](https://code.claude.com/docs/en/permission-modes)
- Auto mode pauses and prompts again "if the classifier blocks an action 3 times in a row or 20 times total" - in an unattended phone-driven run this means a stall awaiting approval. — [Permission modes](https://code.claude.com/docs/en/permission-modes)
- Classifier input: "Tool results are stripped from those requests, so hostile content in a file or web page can't manipulate the classifier directly." — [Permission modes](https://code.claude.com/docs/en/permission-modes)
- Auto mode needs model support: Opus 4.6+/Sonnet 4.6+/Haiku 5.5/Fable on Anthropic API; available on all plans. — [Permission modes](https://code.claude.com/docs/en/permission-modes)
- `bypassPermissions`: "disables permission prompts and safety checks ... Only use this mode in isolated environments like containers, VMs, or dev containers without internet access" and "offers no protection against prompt injection or unintended actions." Refuses to start as root/sudo. — [Permission modes](https://code.claude.com/docs/en/permission-modes)
- `dontAsk`: "auto-denies every tool call that would otherwise prompt you ... Use this mode for CI pipelines or restricted environments where you pre-define what Claude may do." — [Permission modes](https://code.claude.com/docs/en/permission-modes)
- `acceptEdits`: auto-approves edits and `mkdir, touch, rm, rmdir, mv, cp, sed` only inside the working directory; other Bash still prompts. — [Permission modes](https://code.claude.com/docs/en/permission-modes)
- Allow-rule caveat: "A Bash command you approve can still write anywhere your user account can"; use sandboxing for OS-level restriction. — [Security](https://code.claude.com/docs/en/security)

### Inferences
- Do NOT enable: Codex `--dangerously-bypass-approvals-and-sandbox`/`danger-full-access` + `never`; Codex `network_access = true` without need; Gemini `--yolo` on the host without sandbox; Claude `bypassPermissions` on the host; `Bash(codex *)`/`Bash(gemini *)` blanket allow without wrapper script constraints.
- Prefer a single allow rule for a wrapper script (e.g. `Bash(./bin/ask-codex.sh *)`) that hard-codes sandbox flags, timeouts, cwd and read-only mode, so Claude cannot loosen flags; combine with `dontAsk` so unattended sessions never wait on a prompt.
- Use read-only/advisory invocations for Codex and Gemini (review, second opinion) and let only Claude write; this avoids three agents editing one tree.

### Gaps
- Exact current flag names for Gemini approval modes (`--approval-mode`, `--yolo`) and `codex exec` sandbox flags not verified from primary docs.

## 5. Security: prompt injection, credential exposure, least privilege, worktrees, audit logging

### Takeaway
The main risk is injection chaining: untrusted text read by one agent flows back through Claude, which has the broadest permissions. Mitigate with least-privilege wrappers, isolated worktrees/containers, stripped environments, and logging of every call.

### Cited Findings
- Anthropic best practices for untrusted content: "Review suggested commands before approval; Avoid piping untrusted content directly to Claude; Verify proposed changes to critical files; Use virtual machines (VMs) to run scripts and make tool calls, especially when interacting with external web services". — [Security](https://code.claude.com/docs/en/security)
- "No system is completely immune to all attacks." — [Security](https://code.claude.com/docs/en/security)
- Extra isolation: "run the whole Claude Code (local mode) process inside the sandbox runtime or a dev container"; sandboxing provides filesystem and network isolation for Bash. — [Security](https://code.claude.com/docs/en/security)
- `-p` sessions skip the workspace-trust and `.mcp.json` approval prompts. — [Security](https://code.claude.com/docs/en/security)
- Credential storage: macOS Keychain; on Linux "a file with mode `0600`". Codex stores plaintext `~/.codex/auth.json` (or keyring); Gemini `~/.gemini/oauth_creds.json`. — [Security](https://code.claude.com/docs/en/security); [Codex auth](https://developers.openai.com/codex/auth) [secondary]
- Audit: `ConfigChange` hooks can audit/block settings changes; OpenTelemetry metrics for usage monitoring. — [Security](https://code.claude.com/docs/en/security)
- Worktrees: Remote Control `--spawn worktree` gives on-demand sessions isolated git worktrees. — [Remote Control](https://code.claude.com/docs/en/remote-control)

### Inferences
- Credential exposure: any agent run as your user can read other CLIs' token files (`~/.codex`, `~/.gemini`, `~/.claude`). Run Codex/Gemini as separate OS users or in containers with only their own credential dir mounted; never put `.env` files (e.g. this repo's LINE/Anthropic keys) in a directory visible to them (AGENTS.md forbids committing secrets).
- Give each external call a throwaway worktree/copy of the repo with no `.env`, no `.git` remotes with push credentials, and no network (Codex default); collect results as text, never as executed code.
- Treat external-CLI output as untrusted data: instruct Claude (wrapper wraps output in delimiters) not to follow instructions inside it; keep Claude's own tools narrow (deny `curl`, `wget`, push).
- Log: wrapper writes timestamped JSONL (vendor, prompt hash/text, cwd, exit code, duration, output) to an append-only file outside the working tree; enable Claude OTel if wanted.

### Gaps
- No vendor guidance found specifically about multi-agent injection chains between Claude, Codex and Gemini.
- Codex/Gemini security pages not fetched directly.

## 6. Cheaper simpler alternatives and when they win

### Takeaway
Fewer vendors usually wins: one external CLI, or Claude subagents on a small model, avoids two extra auth/quota/attack surfaces. The multi-vendor pipeline is justified only when diversity of model opinion is itself the product.

### Cited Findings
- Auto mode lists Haiku 5.5 as a supported model, so a cheap model can serve as an unattended subagent under classifier protection. — [Permission modes](https://code.claude.com/docs/en/permission-modes)
- Subagent usage counts against the same Claude subscription pool (so subagents save tokens only if they use a cheaper model, not a different quota). — [WebSearch summary of third-party blogs] [unverified-secondary]
- Remote Control already supports progress of subagents and dynamic workflows staying in sync across devices. — [Remote Control](https://code.claude.com/docs/en/remote-control)
- Cloud sessions (Claude Code on the web) run in isolated Anthropic VMs with limited network by default and audit logging, avoiding the keep-the-computer-on requirement. — [Security](https://code.claude.com/docs/en/security)

### Inferences
- Option A (usually best): Claude only, with Haiku-model read-only subagents for review/second-opinion. Wins on cost, simplicity, and no extra credentials; use when the goal is parallelism or cheap checking.
- Option B: Claude + one external CLI (Codex preferred for independent code review; its sandbox model is better documented than Gemini's yolo/headless behavior in the sources found). Wins when a genuinely different model's critique is wanted and quota is at stake only on one extra vendor.
- Option C (full fan-out): justified for high-stakes decisions where cross-model disagreement matters; budget for serialized calls, daily caps, and monitoring.
- Option D: Move the whole pipeline to a cloud session / self-hosted runner so the home PC need not stay on (trade-off: external CLI subscription logins in a cloud VM are unverified and likely awkward).
- Option E: use API keys (Codex/Gemini) for the external vendors rather than subscription logins for predictable, documented unattended auth (billed per use) while keeping Claude on the subscription (required for Remote Control).

### Gaps
- No benchmark or cost comparison between Haiku subagents and Codex/Gemini review quality was found.
- No source quantifying how often multi-vendor review catches issues a single vendor misses.
