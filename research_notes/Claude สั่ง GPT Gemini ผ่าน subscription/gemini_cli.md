# Gemini CLI / Antigravity (agy) headless use with Google-account login (no API key)

Research date: 2026-11-03. Caveat on quoting: WebFetch and WebSearch return model-processed summaries, not raw page text. Passages in quotation marks below are the quotes those tools returned; I could not open the primary pages myself for several hosts (developers.google.com, geminicli.com, antigravity.google and discuss.ai.google.dev did not resolve in this sandbox). Items resting only on search summaries are marked UNVERIFIED-SECONDARY. The report writer should treat these as leads to check against the primary page.

## 1. Headless mode: flags, stdin, unattended auth, token refresh

### Takeaway
Gemini CLI has a documented headless mode (`-p`, `--output-format`, exit codes). But as of Nov 2026 the Login-with-Google route for consumer accounts (free, AI Pro, AI Ultra) was shut off on 2026-06-18 per Google's deprecation page, so the premise "headless Gemini CLI on an AI Pro/Ultra login" appears no longer to work. Google's replacement is the Antigravity CLI (`agy`).

### Cited Findings
- Headless mode trigger: "Headless mode is triggered when the CLI is run in a non-TTY environment" (or when a query is given with `-p`/`--prompt`). The page says "You can specify the output format using the `--output-format` flag." It describes a "Streaming JSON output" option that returns JSONL events. (The fetch summary did not list the exact value names; check `gemini --help`.) — [headless.md](https://raw.githubusercontent.com/google-gemini/gemini-cli/main/docs/cli/headless.md)
- Exit codes: "The CLI returns standard exit codes to indicate the result of the headless execution:" 0 success; 1 general error or API failure; 42 input error (invalid prompt or arguments); 53 turn limit exceeded. — [headless.md](https://raw.githubusercontent.com/google-gemini/gemini-cli/main/docs/cli/headless.md)
- The headless page, per the fetch summary, does not cover stdin or authentication. Stdin piping and headless OAuth details are therefore not confirmed by an official source I could read. The authentication doc URL I tried returned 404. — [headless.md](https://raw.githubusercontent.com/google-gemini/gemini-cli/main/docs/cli/headless.md)
- Consumer-account shutdown (UNVERIFIED-SECONDARY, from a search summary of Google's pages): starting June 18, 2026, Gemini Code Assist IDE extensions stopped serving requests for the Gemini Code Assist for individuals, Google AI Pro and Google AI Ultra tiers; this "also applies to usage of Gemini CLI"; "Login with Google" can no longer be used for the extensions or Gemini CLI; Standard/Enterprise Code Assist are unchanged; users are pointed to Antigravity. — [Gemini Code Assist consumer accounts](https://developers.google.com/gemini-code-assist/docs/deprecations/code-assist-individuals) (search-result page, last updated about June 11, 2026, so older than 6 months is not the case but the page is about 5 months old)
- The same search summary says the deprecations table lists May 18, 2026 as deprecation date and June 18, 2026 as shutdown. — [Feature deprecations](https://developers.google.com/gemini-code-assist/docs/deprecations?authuser=3&hl=en)
- A third-party opencode plugin README (UNVERIFIED-SECONDARY) repeats that the Gemini CLI OAuth flow no longer works for individuals, AI Pro or AI Ultra accounts as of June 18, 2026. — [opencode-gemini-auth](https://github.com/jenslys/opencode-gemini-auth)

### Inferences
- If the June 2026 shutdown is accurate, `gemini -p` under an AI Pro/Ultra Google login will not return answers; the only working Gemini CLI auth would be an API key/Vertex or a Workspace Standard/Enterprise Code Assist seat, which is outside the user's constraint.
- Token refresh behaviour could not be sourced; moot if consumer login is closed.

### Gaps
- No official source read for stdin usage, `NO_BROWSER`/unattended OAuth flow, or refresh-token lifetime.
- Primary deprecation page not opened directly; verify wording and dates.

## 2. Quotas: free vs Google AI Pro/Ultra

### Takeaway
The official quota page (in the repo main branch, which may be stale relative to the June 2026 shutdown) lists 1,000/day free individual, 1,500/day AI Pro, 2,000/day AI Ultra, with no numeric per-minute limit. For Antigravity CLI, quotas are time-window based rather than per-day.

### Cited Findings
- Table "Maximum requests per user per day": Google account Code Assist (Individual) "1,000 requests"; Google AI Pro "1,500 requests"; Google AI Ultra "2,000 requests"; Workspace Standard "1,500"; Workspace Enterprise "2,000"; Gemini API key free tier "250 requests". — [quota-and-pricing.md](https://raw.githubusercontent.com/google-gemini/gemini-cli/main/docs/resources/quota-and-pricing.md)
- Per minute: no number given; "Requests are limited per user per minute and are subject to the availability of the service in times of high demand." — [quota-and-pricing.md](https://raw.githubusercontent.com/google-gemini/gemini-cli/main/docs/resources/quota-and-pricing.md)
- Antigravity (UNVERIFIED-SECONDARY, search summary of Plans page): Ultra gets the highest quota refreshed every five hours; Pro gets a high quota on the same cycle with a higher weekly limit; purchased AI credits can cover overage. — [Antigravity plans](https://antigravity.google/docs/plans.md)
- Forum staff (UNVERIFIED-SECONDARY) say headless runs draw from the same account quota, credit pool and rate limits as interactive sessions. — [Google AI forum thread](https://discuss.ai.google.dev/t/is-google-ai-pro-antigravity-cli-automation-with-codex-permitted/187241)

### Inferences
- The repo doc likely predates the consumer shutdown, so these per-day numbers may no longer apply to consumer logins.

### Gaps
- No exact Antigravity numeric limits retrieved. Plans page could not be opened.

## 3. MCP client/server and official ways for another agent to call Gemini CLI

### Takeaway
Gemini CLI is an MCP client and supports an ACP mode (`--acp`, JSON-RPC over stdio) for programmatic control. I found no official Google MCP-server mode for it; wrappers are community projects.

### Cited Findings
- Gemini CLI connects to MCP servers over stdio, SSE or Streamable HTTP. — [MCP servers with Gemini CLI](https://geminicli.com/docs/tools/mcp-server/) (search summary)
- ACP mode: started with `--acp`, JSON-RPC over stdio between the agent and a client, mainly for IDE integration; Gemini CLI is listed in the ACP Agent Registry. — [ACP mode](https://geminicli.com/docs/cli/acp-mode/) (search summary)
- Community bridges (not official, code unverified): `shenyunhuan/gemini_mcp` (MCP-to-ACP bridge) and `loming/gemini-mcp`. — [vibeindex listing](https://vibeindex.ai/mcp/shenyunhuan/gemini_mcp), [lobehub listing](https://lobehub.com/mcp/loming-gemini-mcp)

### Inferences
- Plain shell invocation of `gemini -p` is the simplest integration, but see section 4 for policy risk.

### Gaps
- Whether Gemini CLI can itself run as an MCP server: no evidence found.

## 4. Google policy on automated / third-party use of the CLI OAuth credentials

### Takeaway
Google's ToS/privacy page for Gemini CLI says accessing the backing services via third-party software with CLI OAuth is a violation and can lead to account suspension. Using one's own scripts with the official CLI is not separately addressed.

### Cited Findings
- The ToS page states that accessing the services "using third-party software, tools, or services" is a violation, giving "using OpenClaw with Gemini CLI OAuth" as an example; it "is a violation of applicable terms and policies." and "Such actions may be grounds for suspension or termination of your account." — [tos-privacy.md](https://raw.githubusercontent.com/google-gemini/gemini-cli/main/docs/resources/tos-privacy.md)
- The page does not separately address automated use or scripting. — [tos-privacy.md](https://raw.githubusercontent.com/google-gemini/gemini-cli/main/docs/resources/tos-privacy.md)
- Official FAQ (UNVERIFIED-SECONDARY; geminicli.com unreachable) reportedly lists using third-party tools such as Claude Code, OpenClaw or OpenCode to piggyback on Gemini CLI OAuth as disallowed and recommends an AI Studio or Vertex AI API key. — [Gemini CLI FAQ](https://geminicli.com/docs/resources/faq/)
- Enforcement claim (weak): a Puter tutorial says Google mass-suspended accounts, including Ultra subscribers, in Feb 2026; I could not confirm against a Google announcement. — [Puter tutorial](https://developer.puter.com/tutorials/gemini-oauth/)

### Inferences
- Claude Code driving `gemini -p` under a personal OAuth login is plausibly "third-party software" per the ToS wording; risk is real though the line for a local shell wrapper is not defined.

### Gaps
- No official statement on whether a local shell call from another agent counts; no confirmed Google enforcement announcement.

## 5. Antigravity (agy) headless/CLI mode

### Takeaway
Antigravity CLI exists with a print mode (`agy -p`), but it has an open reliability problem in non-TTY contexts, and forum staff (per search summaries) say wrapping it with third-party agents under a consumer login is unsupported.

### Cited Findings
- Issue #318: reporter says "the print mode command `agy -p "prompt"` hangs indefinitely" (v1.0.6, Windows, Jun 6, 2026); maintainer on Sep 3, 2026: "we believe this issue is obsolete and not seen in recent versions." Later users reproduced on v1.2.0 and v1.2.3 (Linux) and v1.4.10 (Windows, Oct 29, 2026): "print timeout after 5m0s with turn in progress..." and "Interactive mode works fine on the same account." — [antigravity-cli issue 318](https://github.com/google-antigravity/antigravity-cli/issues/318)
- Community wrapper `agy-headless-bridge` runs `agy -p` in a pseudo-terminal, has an MCP server, and notes that headless agy cannot answer tool approvals (`--dangerously-skip-permissions` is an option). Exit code 75 means quota/rate limit. UNVERIFIED-SECONDARY. — [agy-headless-bridge](https://pypi.org/project/agy-headless-bridge/1.3.0/)
- Install and auth (third-party guide): interactive OAuth or `ANTIGRAVITY_API_KEY`. — [guide](https://pasqualepillitteri.it/en/news/3422/antigravity-cli-agy-install-migrate-gemini-cli)
- Forum staff (UNVERIFIED-SECONDARY): `agy -p` for your own scripts and CI is supported; using third-party coding agents (Codex, Claude Code, OpenClaw, OpenCode) to orchestrate or wrap agy under a consumer login is not supported, may trigger automated ToS enforcement and suspension, and Additional Terms section 6 prohibit third-party tools; API key via AI Studio or Vertex suggested. Staff say they cannot give formal legal interpretations. — [forum thread](https://discuss.ai.google.dev/t/is-google-ai-pro-antigravity-cli-automation-with-codex-permitted/187241), [MCP thread](https://discuss.ai.google.dev/t/is-using-the-official-agy-cli-through-a-local-mcp-server-with-third-party-ai-agents-permitted/184829)

### Inferences
- Technically workable only with a PTY workaround and with known hang risk; policy-wise, Claude Code calling agy on a subscription login sits in the discouraged category.

### Gaps
- Official agy headless docs and exact flags not read (`--output-format stream-json` appears in a bug report but official flag list unconfirmed). Antigravity Additional Terms not read directly.
