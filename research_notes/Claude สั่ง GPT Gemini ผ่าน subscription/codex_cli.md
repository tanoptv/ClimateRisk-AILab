# Codex CLI headless use with ChatGPT Plus/Pro subscription (no API key)

NOTE ON SOURCE QUALITY: developers.openai.com, help.openai.com, learn.chatgpt.com and codex.danielvaughan.com did not resolve from this sandbox (network allowlist), so I could NOT read the official pages directly. Findings below come from (a) github.com/openai/codex README (fetched directly) and (b) WebSearch result summaries that quote official pages (summaries, not verbatim page reads), plus third-party blogs. Anything not directly fetched is marked "search-summary" or "unverified". Re-verify against the official URLs listed.

## 1. Does `codex exec` work with "Sign in with ChatGPT"? Flags and output formats

### Takeaway
Yes in principle: the official README recommends ChatGPT sign-in for Plus/Pro, and the non-interactive docs describe `codex exec` with JSONL output, `-o` last-message file and `--output-schema`. Exact flag text and the sandbox/approval flag names were not verified from the primary page.

### Cited Findings
- README: "Run `codex` and select **Sign in with ChatGPT**. We recommend signing into your ChatGPT account to use Codex as part of your Plus, Pro, Business, Edu, or Enterprise plan." (fetched directly) — [openai/codex README](https://github.com/openai/codex/blob/main/README.md)
- Non-interactive docs describe `--json` as a JSON Lines event stream, `-o`/`--output-last-message` as writing only the final message to a file, and `--output-schema` as constraining the final response to a JSON Schema file (search-summary of official page) — [Non-interactive mode](https://developers.openai.com/codex/noninteractive.md)
- Progress goes to stderr; the final message still goes to stdout even when `-o` is used (search-summary) — [Non-interactive mode](https://developers.openai.com/codex/noninteractive)
- `CODEX_API_KEY` sets an API key for a single run and is supported only in `codex exec` (search-summary). This is an API-key path, not needed for subscription use — [Non-interactive mode](https://developers.openai.com/codex/noninteractive)
- Docs have an "advanced" section on running CI/CD with a Codex user account (ChatGPT-managed access) rather than an API key, aimed at enterprise teams on trusted runners (search-summary) — [learn.chatgpt.com mirror](https://learn.chatgpt.com/docs/non-interactive-mode.md)
- Event names such as `thread.started`, `turn.completed`, `item.completed` appear in a third-party mirror of the source; may not match current release — [forge.lthn.ai mirror of exec/cli.rs](https://forge.lthn.ai/core/core-agent-ide/src/commit/31102af54b79e5a56883b9108a6fc9d5d0af8937/codex-rs/exec/src/cli.rs)
- github docs/exec.md and docs/authentication.md in the repo are only pointers to developers.openai.com/codex/noninteractive and /codex/auth (fetched) — [exec.md](https://github.com/openai/codex/blob/main/docs/exec.md)

### Inferences
- A shell call like `codex exec --json -o out.txt "prompt"` (or with `--output-schema`) from Claude Code should return text/JSON using the cached ChatGPT login, as the same auth cache is used by all CLI modes. Not verified end to end.

### Gaps
- Exact sandbox/approval flags (e.g. `--sandbox read-only`, `--full-auto`, `--skip-git-repo-check`) not verified from primary source.
- No direct confirmation that `codex exec` with ChatGPT login has no extra restrictions beyond the enterprise CI section.

## 2. MCP server mode

### Takeaway
Yes: `codex mcp-server` runs Codex as an MCP server (stdio) exposing `codex` and `codex-reply` tools. Claude Code can attach it as a stdio MCP server. Exact Claude Code config below is my inference.

### Cited Findings
- "The Codex CLI can also be run as an MCP _server_ via `codex mcp-server`." — [docs/advanced.md mirror](https://forge.lthn.ai/core/core-agent-ide/raw/commit/789e65b9d260ea5aa317a2e7dea80381cdcbde7e/docs/advanced.md) (third-party mirror of OpenAI file; check official repo)
- Two tools: `codex` ("Run a Codex session. Accepts configuration parameters matching the Codex Config struct.") and `codex-reply` (required `prompt` and `conversationId`) — same mirror
- `config` param overrides `$CODEX_HOME/config.toml`; `mcp_servers` in config.toml is for MCP servers Codex itself consumes, managed by `codex mcp` — same mirror
- Docs advise 10-minute (600000 ms) timeouts since runs take minutes — same mirror
- Mirrors differ across versions (e.g. `include-plan-tool`, approval-policy values), so parameters may have changed.

### Inferences
- Claude Code attach (unverified): `claude mcp add codex -- codex mcp-server`, or `.mcp.json` `{"mcpServers":{"codex":{"command":"codex","args":["mcp-server"]}}}`. Long calls may need a raised MCP tool timeout.

### Gaps
- Current official page (developers.openai.com/codex/mcp) not read; no verification of whether mcp-server uses the ChatGPT login (likely, same auth cache, unverified).

## 3. Plans and usage limits

### Takeaway
Codex is included in Plus, Pro, Business, Edu, Enterprise. Limits are shifting and sources conflict; Plus reportedly has a 5-hour window again, Pro reportedly no 5-hour window but weekly caps. Metering moved to credits/tokens, so message counts are rough.

### Cited Findings
- Plans including Codex: Plus, Pro, Business, Edu, Enterprise — [README](https://github.com/openai/codex/blob/main/README.md)
- Reports: 5-hour cap removed July 2026 (temporary), restored for Plus from Aug 25, 2026; OpenAI said it won't be reactivated on the $100/$200 Pro plans; weekly limits still apply (secondary) — [aiweekly.co](https://aiweekly.co/alerts/openai-brings-back-5-hour-codex-work-cap-for-chatgpt-plus), [aiidelist](https://aiidelist.com/blog/codex-5-hour-limit-plus-pro.md), [Notebookcheck](https://www.notebookcheck.net/OpenAI-abruptly-restores-harsh-5-hour-Codex-and-Work-limits-for-ChatGPT-Plus.1378377.0.html)
- Plus message estimates conflict: "15 to 80 local messages, 5 cloud tasks, 5 code reviews per 5h" vs "~30-150 local messages or 5-40 cloud tasks per 5h", with shared weekly limit (secondary, search-summary); since April 2026 usage is metered in credits/tokens
- $100 Pro offers 5x Codex usage vs Plus; $200 Pro 20x (older, secondary) — [bensbites](https://news.bensbites.co/posts/63518-openai-launches-a-100month-chatgpt-pro-subscription-which-offers-5x-more-codex-usage-than-plus-the-200month-pro-plan-offers-20x-higher-limits-than-plus)
- Official pricing: [developers.openai.com/codex/pricing](https://developers.openai.com/codex/pricing) (not readable here)

### Inferences
- Headless runs count against the same pool as interactive use, so heavy automation could exhaust the Plus 5-hour/weekly windows quickly.

### Gaps
- Official current numbers not verified; need to read pricing page.

## 4. Headless auth on an unattended home machine

### Takeaway
Two documented routes: `codex login --device-auth` on a headless box, or log in elsewhere and copy `~/.codex/auth.json`. Token refresh and expiry behavior over long unattended periods not verified from primary sources.

### Cited Findings
- `codex login --device-auth` or "Sign in with Device Code" in login UI; device-code login must be enabled in ChatGPT security settings (personal) or by workspace admin; otherwise falls back to browser login (search-summary of official page) — [Authentication](https://developers.openai.com/codex/auth)
- Alternative: log in on a machine with a browser, confirm `~/.codex/auth.json`, copy to same path on headless machine; docs give scp and Docker examples (search-summary) — [Authentication](https://developers.openai.com/codex/auth.md)
- Third-party claims: device code needs a human, so API keys recommended for scheduled `codex exec`; seeding auth.json in CI from a secret is a community pattern, not official — [search results incl. danielvaughan.com](https://codex.danielvaughan.com/2026/04/01/codex-cli-authentication-flows-credential-management/) (unfetched)

### Inferences
- A one-time device-auth/copy on a home machine then cached use is plausible, but refresh-token lifetime is unknown; plan for occasional re-login.

### Gaps
- Token refresh/expiry details, concurrent use of copied auth.json across machines: not verified.

## 5. OpenAI statements on automated/programmatic use of subscription Codex

### Takeaway
No primary OpenAI text found. Commentary says terms are ambiguous (generic "automatically or programmatically" language) while OpenAI staff publicly tolerate or endorse subscription use in third-party harnesses; Platform API recommended for production/commercial use.

### Cited Findings
- "Nothing in OpenAI's terms of use explicitly permits or prohibits using your ChatGPT subscription inside a non-OpenAI tool." (commentary) — [manifest.build](https://manifest.build/blog/chatgpt-plus-tokens-third-party-harnesses/)
- Codex lead Thibault Sottiaux reportedly endorsed subscription tokens in third-party harnesses; a Sept 2026 report says OpenAI broadened plan usage to Plus and Pro in participating tools (secondary, unverified) — [Zylos](https://zylos.ai/research/2026-07-13-subscription-auth-boundaries-official-cli-agent-automation), [danielvaughan](https://codex.danielvaughan.com/2026/04/24/codex-subscription-api-programmatic-access-gpt-5-5-chatgpt-plan/)
- Official CLI use by the user's own scripts is the first-party tool; this differs from third-party harnesses.

### Inferences
- Calling the official `codex` binary from Claude Code at personal, low volume is lowest risk; multi-user or commercial use is riskier.

### Gaps
- OpenAI Terms of Use and Codex help-center text not read; no explicit OpenAI policy statement on `codex exec` automation found.
