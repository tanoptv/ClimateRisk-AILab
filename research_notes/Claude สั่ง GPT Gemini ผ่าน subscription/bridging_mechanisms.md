# Claude Code -> Codex CLI / Gemini CLI delegation mechanisms (as of 2026-11-03)

Research limits: ~15 tool calls. Network blocked geminicli.com and developers.openai.com (official Gemini headless docs and Codex noninteractive docs NOT fetched directly; their content below comes from search-engine summaries and is marked unverified). Last-commit dates and release dates could not be obtained from GitHub pages (not shown in fetched output).

## 1. CLI-through-Bash vs MCP wrappers: what exists, maintenance, auth

### Takeaway
Calling `codex exec` / `gemini -p` via Bash is the simplest, officially supported route and can use subscription login (ChatGPT plan for Codex; Gemini subscription route is now changed, see below). MCP wrappers exist (native `codex mcp-server`, PAL/zen `clink`, `claude-code-mcp`), but I could not verify last-commit dates or subscription-vs-API-key behaviour for most; PAL's own README snippet mentions API keys only.

### Cited Findings
- Codex README mirror: Codex runs non-interactively with `codex exec PROMPT` (prompt may come via stdin); `codex mcp-server` runs Codex as an MCP server; `codex mcp` manages MCP launchers in config.toml. (via search summary of a mirror, UNVERIFIED against OpenAI docs; sources disagreed on `codex mcp` vs `codex mcp-server` naming) — [mirror README](https://forge.lthn.ai/core/core-agent-ide/src/branch/dev/codex-rs/README.md)
- Codex repo: 132.9k stars; "Run `codex` and select **Sign in with ChatGPT**" lets you use Codex as part of "your Plus, Pro, Business, Edu, or Enterprise plan." Repo page did not show release version/date or mention MCP. — [openai/codex](https://github.com/openai/codex)
- Codex docs/exec.md in repo only points to official page "https://developers.openai.com/codex/noninteractive" (not fetched, host blocked). — [exec.md](https://raw.githubusercontent.com/openai/codex/main/docs/exec.md)
- Gemini CLI repo: 108.7k stars; headless is `gemini -p "..."`, with `--output-format json` and `--output-format stream-json`. — [google-gemini/gemini-cli](https://github.com/google-gemini/gemini-cli)
- Gemini CLI repo notice: "Free individual access and Google AI Pro / Ultra (Google One) moved to Antigravity CLI on June 18, 2026." and the CLI is "Designed for Gemini Code Assist Standard / Enterprise" licenses; other auth: Gemini API key, Vertex AI. This means Google-account/subscription login for Gemini CLI is no longer the free/consumer path as of Nov 2026. — [google-gemini/gemini-cli](https://github.com/google-gemini/gemini-cli)
- Gemini headless docs (search summary, UNVERIFIED details): `-p/--prompt` bypasses interactive UI and also triggers in non-TTY; `--output-format json` returns one JSON object with response and stats (read `.response` with jq); `--yolo`/`--approval-mode` exist. — [geminicli.com headless](https://www.geminicli.com/docs/cli/headless)
- PAL MCP (formerly Zen MCP), BeehiveInnovations/pal-mcp-server: 11.8k stars, 1.0k forks, 1,150 commits; `clink` "connects external AI CLIs directly into your workflow" (Gemini CLI, Codex CLI, Claude Code) and can launch isolated CLI subagents. Page says "PAL activates any provider that has credentials in your .env" (API keys); page did not state whether clink uses the CLI's own subscription login. Last commit date not shown. License listed NOASSERTION on one directory (UNVERIFIED). — [repo](https://github.com/BeehiveInnovations/pal-mcp-server)
- steipete/claude-code-mcp: thin MCP wrapper around local Claude Code CLI, one-shot, skips permissions by default, "not an OS-level sandbox"; recommends native `claude mcp serve` instead. Star count/last commit not found. (search summary, UNVERIFIED) — [repo](https://github.com/steipete/claude-code-mcp)
- kunihiros/claude-code-mcp: ~31 stars at an aggregator snapshot, ~9 months stale (UNVERIFIED) — [listing](https://awesome.ecosyste.ms/projects/github.com%2Fkunihiros%2Fclaude-code-mcp)

### Inferences
- For a Thai-province bot dev workflow, the lowest-risk path is Bash + `codex exec` (ChatGPT login) and `gemini -p` (API key or Code Assist license, not consumer Google One after 2026-06-18 per repo notice).
- PAL/clink is the most popular multi-CLI bridge found, but treat subscription-compatibility as unverified.

### Gaps
- No last-commit dates, release dates, or star counts for most MCP wrappers; Codex-specific community MCP wrappers (e.g. "consult"-style) not found at all.
- Official Codex noninteractive docs and Gemini headless docs not read directly (blocked hosts; ask user to allow developers.openai.com and geminicli.com).
- Whether Antigravity CLI has a headless mode: not researched.

## 2. Claude Code glue: subagents, hooks, skills, agent teams, Agent SDK

### Takeaway
Claude Code has an official, experimental "agent teams" feature, but it coordinates Claude sessions only. Cross-vendor delegation still needs a subagent/skill/slash-command that shells out to the other CLI.

### Cited Findings
- "Agent teams are experimental and disabled by default. Enable them by setting `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`." "Coordinate multiple Claude Code instances working together as a team, with shared tasks, inter-agent messaging, and centralized management." — [Agent teams docs](https://code.claude.com/docs/en/agent-teams)
- Teammates are "Separate Claude Code instances"; each mailbox "is a JSON file at `~/.claude/teams/{team-name}/inboxes/{agent-name}.json`" (so Anthropic itself uses a file-mailbox design). — [Agent teams docs](https://code.claude.com/docs/en/agent-teams)
- "In non-interactive mode with the `-p` flag, including Agent SDK sessions, Claude doesn't spawn teammates." — [Agent teams docs](https://code.claude.com/docs/en/agent-teams)
- Docs point to lighter options: subagents ("Return a result to the caller") and "cross-session messaging" between sessions the user runs. — [Agent teams docs](https://code.claude.com/docs/en/agent-teams)
- Hooks `TeammateIdle`, `TaskCreated`, `TaskCompleted` can exit code 2 to block/feedback. — [Agent teams docs](https://code.claude.com/docs/en/agent-teams)
- Native `claude mcp serve` exposes Claude Code to other MCP clients (secondary guide) — [ksred guide](https://www.ksred.com/claude-code-as-an-mcp-server-an-interesting-capability-worth-understanding/)

### Inferences
- A custom subagent or skill whose body runs `codex exec ... </dev/null` via Bash returns the answer as a normal tool result, the cleanest "automatic return" with no markdown handoff.

### Gaps
- Did not read sub-agents, hooks, headless, or Agent SDK pages individually; cross-session-messaging page not fetched.
- No evidence found that agent teams accept non-Claude teammates.

## 3. File-based mailbox vs direct process calls

### Takeaway
Direct process calls give synchronous results but risk hangs/timeouts; file mailboxes decouple and persist but need watchers and add race/injection surface. Anthropic's own team feature uses file mailboxes with file locking.

### Cited Findings
- "Task claiming uses file locking to prevent race conditions"; mailbox entries are validated and malformed ones removed. — [Agent teams docs](https://code.claude.com/docs/en/agent-teams)
- Claude Code reports a message sent only when the mailbox file write succeeds. — [Agent teams docs](https://code.claude.com/docs/en/agent-teams)

### Inferences
- Mailbox pros: auditable, async, survives crashes. Cons: needs a watcher process, no built-in auth, stale/partial file races. (my judgement, no external source)

### Gaps
- No engineering blog comparing mailbox vs direct calls was found.

## 4. Open protocols (MCP, ACP, A2A)

### Takeaway
MCP is the practical one. ACP (Zed's Agent Client Protocol) is real for editor-to-agent, with adapters for Gemini CLI, Claude, Codex; A2A is an LF-governed spec with little evidence of use between coding CLIs.

### Cited Findings
- ACP: "an open standard that enables any agent to integrate seamlessly with any editing environment"; Zed partnered with Google on Gemini CLI as reference implementation; Zed open-sourced a Claude Code adapter (Apache) wrapping the SDK; Codex also has a Zed adapter; Zed asks users to request Anthropic adopt ACP. — [Zed ACP](https://zed.dev/acp), [Claude Code via ACP](https://zed.dev/blog/claude-code-via-acp), [External agents](https://zed.dev/docs/ai/external-agents?highlight=codex)
- A2A: "The A2A Protocol is an open source project under the Linux Foundation, contributed by Google." 26.4k stars, 658 commits. — [a2aproject/A2A](https://github.com/a2aproject/A2A)

### Inferences
- ACP is designed for a UI client driving an agent, so a Claude Code session could in principle act as an ACP client, but I found no evidence of that being done (UNVERIFIED).

### Gaps
- IBM-ACP / A2A merger claim not verified; no A2A implementations in Claude/Codex/Gemini CLIs found.

## 5. Failure modes

### Takeaway
Stdin-related hangs are the best-documented failure; others (truncation, context bloat, injection) have only partial support.

### Cited Findings
- Codex CLI 0.118+ "reads stdin at startup and blocks forever on the open-but-empty pipe" until a 300s wrapper timeout; fix is closing stdin (verified on 0.119.0 by the wrapper author). — [codex_wrapper_ex #34](https://github.com/genagent/codex_wrapper_ex/issues/34)
- Earlier: Codex hangs when stdin inherited from parent; workaround `</dev/null`. — [codex_wrapper_ex #38](https://github.com/genagent/codex_wrapper_ex/pull/38)
- Blog: backgrounded `codex exec` idle for ten minutes; suggests `</dev/null`, `timeout`, or pty via `script` (secondary source). — [openclawdc](https://openclawdc.com/blog/codex-exec-hangs-forever/)
- Claude Code headless can also hang reading its stream. — [claudeissues #7497](https://claudeissues.com/issue/7497-bug-process-hangs-indefinitely-when-reading-inputstream-from-claude-code-headles)
- Prompt injection between agents: Claude Code tells a receiving agent that a SendMessage "came from another Claude session, not from you"; teammates "can't approve a permission prompt or supply consent on your behalf"; in auto mode the classifier treats relayed approval claims "as untrusted input". — [Agent teams docs](https://code.claude.com/docs/en/agent-teams)
- Context bloat: teammates "use significantly more tokens"; subagents return summaries, keeping caller context lower. — [Agent teams docs](https://code.claude.com/docs/en/agent-teams)
- steipete/claude-code-mcp skips permissions by default (security risk). — [repo](https://github.com/steipete/claude-code-mcp)

### Inferences
- Always wrap with `timeout`, `</dev/null`, read-only sandbox/approval flags, and treat the other agent's output as untrusted data.

### Gaps
- No `gemini -p` hang reports found; no sourced data on output truncation limits for either CLI.
