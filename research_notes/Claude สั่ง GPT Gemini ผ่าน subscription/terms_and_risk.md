# ToS and enforcement risk: orchestrating Claude / ChatGPT / Google AI consumer subscriptions from one automated pipeline (as of 2026-11-03; research, not legal advice)

Method note: primary pages fetched directly were Anthropic Claude Code legal page, Anthropic Consumer Terms, and Google's Gemini CLI maintainer post / ToS page (via GitHub). Fetches of developers.openai.com, help.openai.com, thenewstack.io, thenextweb.com, zed.dev, aicoder.com failed (domains not allowed in this session), so OpenAI claims and the Anthropic April/May-June 2026 enforcement details rest on search-result summaries (secondary) and are flagged.

## Anthropic: what do the terms say about automation and third-party OAuth use? Does Claude Code calling other vendors' CLIs matter?

### Takeaway
Anthropic permits subscription OAuth only for its own unmodified Claude Code and native apps, and explicitly forbids routing subscription credentials through third-party products; Consumer Terms bar automated access except via API key or where Anthropic explicitly permits. Nothing found suggests Claude Code running other vendors' CLIs via Bash is an Anthropic issue; the exposure is on how Claude itself is driven (headless/Agent SDK) and on the other vendors' side.

### Cited Findings
- Claude Code legal page: "OAuth authentication is intended exclusively for purchasers of Claude Free, Pro, Max, Ultra, Team, and Enterprise subscription plans and is designed to support ordinary use of Claude Code and other native Anthropic applications." — [Claude Code legal and compliance](https://code.claude.com/docs/en/legal-and-compliance)
- Same page: "Anthropic does not permit third-party developers to offer Claude.ai login into their own applications, or to route requests through Free, Pro, Max, or Ultra plan credentials on behalf of their users. Moreover, developers may not collect, store, or intermediate Claude.ai credentials or session tokens". Developers "including those using the Agent SDK, should use API key authentication". — [same](https://code.claude.com/docs/en/legal-and-compliance)
- Same page: "Advertised usage limits for Pro, Max, and Ultra plans assume ordinary, individual usage of Claude Code and the Agent SDK." and "Anthropic reserves the right to take measures to enforce these restrictions and may do so without prior notice." — [same](https://code.claude.com/docs/en/legal-and-compliance)
- Same page carve-out: nothing prevents "an end user from signing in to the unmodified Claude Code binary with their own Claude subscription". "The Claude Code binary must not be modified." — [same](https://code.claude.com/docs/en/legal-and-compliance)
- Consumer Terms (effective Oct 8, 2025), Section 3 item 7 (per fetch summary): automated/non-human access barred "Except when you are accessing our Services via an Anthropic API Key or where we otherwise explicitly permit it." Section 12: "We may suspend or terminate your access to the Services (including any Subscriptions) at any time without notice to you." Section 2: no sharing login info/credentials. — [Consumer Terms](https://www.anthropic.com/legal/consumer-terms) (quotes came via a summarizing fetch; verify against page)
- Secondary: from April 4, 2026 Anthropic blocked subscription OAuth tokens in third-party harnesses such as OpenClaw; users could use "extra usage" (pay-as-you-go) or API keys; one-time credit offered; Boris Cherny said subscriptions weren't built for these usage patterns. — [TNW](https://thenextweb.com/news/anthropic-openclaw-claude-subscription-ban-cost), [TechRadar](https://www.techradar.com/pro/bad-news-claude-users-anthropic-says-youll-need-to-pay-to-use-openclaw-now), [HN thread](https://news.ycombinator.com/item?id=47633396) (search summaries only, not fetched). Earlier (Feb 2026) reporting that Anthropic formalized the ban: [AlternativeTo](https://alternativeto.net/news/2026/2/anthropic-officially-bans-using-subscription-authentication-for-third-party-claude-use) (secondary).
- Secondary, conflicting: May 2026 plan to move `claude -p`/Agent SDK usage to a separate monthly credit (Pro $20, Max 5x $100, Max 20x $200) from June 15; reports say it was paused; one source (Startup Fortune) says Oct 7 2026 Anthropic announced monthly API credits for Max/Team covering Agent SDK/`claude -p`, requiring a Console org link. Interactive Claude Code stays on subscription limits. — [Zed blog](https://zed.dev/blog/anthropic-subscription-changes), [Digital Applied](https://www.digitalapplied.com/blog/anthropic-claude-credit-overhaul-june-15-2026), [Startup Fortune](https://startupfortune.com/anthropic-quietly-separates-claude-agent-sdk-usage-from-subscription-limits/). Unconfirmed against Anthropic help center; the sources contradict each other on timing.

### Inferences
- Interactive/own-machine use of the unmodified Claude Code binary signed in with your own account is the explicitly protected pattern. Headless `claude -p` loops are a gray zone: "ordinary, individual usage" is the stated assumption, and billing for it has been in flux.
- Claude Code invoking `codex`/`gemini` through Bash is just a local process launching another process; no Anthropic term found addresses it. The risk shifts to the other vendors' rules. (No primary source directly on this; inference.)
- Proxies/routers that hold Claude OAuth tokens and re-expose them (OmniRoute-style, OpenCode Claude plugins) fall squarely under "route requests through ... plan credentials" and "intermediate Claude.ai credentials".

### Gaps
- Could not fetch Anthropic support/help-center pages on `claude -p`, extra usage, or the Agent SDK to confirm current (Nov 2026) billing/limits.
- No primary Anthropic statement found on Claude Code calling other vendors' CLIs.
- No Anthropic primary announcement of the April 2026 block fetched (only secondary).

## OpenAI: automated use of ChatGPT subscription / Codex CLI sign-in; third-party tools using Codex OAuth

### Takeaway
Codex CLI "Sign in with ChatGPT" is the official first-party path; third-party use is officially sanctioned only for partners/pure open-source clients per secondary reports, and no primary OpenAI text was retrievable. Terms language on programmatic extraction creates ambiguity, but no documented mass bans of Codex-OAuth users were found.

### Cited Findings
- OpenAI Service Terms say that if you use Sign in with ChatGPT (SIWC) in your services, the Sign in with ChatGPT Terms apply. — [OpenAI Service terms](https://openai.com/policies/service-terms/) (from search summary; SIWC terms text not seen)
- Secondary: OpenAI launched "Sign in with ChatGPT" for plan usage with 16 launch partners; third-party requests draw from the subscriber's included usage. — [The New Stack](https://thenewstack.io/sign-in-with-chatgpt/) (search summary only)
- Secondary: AICoder (Sept 2026) reports OpenAI's Codex lead said third-party Codex clients using Sign in With ChatGPT is not an approved use unless partner or pure OSS. — [AICoder](https://www.aicoder.com/news/news-20260908-openai-codex-sign-in-policy) (secondary; not fetched)
- GitHub discussion quotes OpenAI Terms barring extraction "automatically or programmatically"; an OpenAI staffer acknowledged Codex CLI itself makes programmatic requests and said they had seen no explicit statement approving OAuth use with third-party services. — [openai/codex Discussion #8338](https://github.com/openai/codex/discussions/8338) (search summary)
- Secondary: OpenClaw's OpenAI provider and OpenCode use Codex OAuth tokens via CLI-mimicking proxies and currently work, but may break if OpenAI changes checks. — [Puter tutorial](https://developer.puter.com/tutorials/openai-oauth/), [opencode-openai-codex-auth plugin](https://github.com/numman-ali/opencode-openai-codex-auth)
- Help center: Codex is included across ChatGPT plans; other activity subject to plan limits and charges. — [OpenAI Help](https://help.openai.com/en/articles/11369540-using-codex-with-your-chatgpt-plan) (summary)

### Inferences
- Driving the official `codex` CLI (e.g., `codex exec`) on your own machine with your own login is the lowest-risk OpenAI pattern; extracting its token for a router is the risky one. (Inference; official `codex exec`/CI guidance not retrieved.)

### Gaps
- Could not read OpenAI's Codex auth docs, SIWC terms, Terms of Use, or any primary statement on OpenCode; no confirmed OpenAI account bans for Codex OAuth reuse found.

## Google: Gemini CLI / Antigravity with Google login; third-party credential use

### Takeaway
Google is the clearest and most aggressive: its docs call third-party use of Gemini CLI OAuth (naming OpenClaw) a violation, and it actually suspended accounts in Feb 2026, with a second-strike permanent ban policy.

### Cited Findings
- Gemini CLI ToS page (per fetch summary): accessing the underlying services via third-party tools, with OpenClaw using Gemini CLI OAuth as the example, "is a violation of applicable terms and policies"; may be grounds for "suspension or termination of your account". — [Gemini CLI tos-privacy.md](https://github.com/google-gemini/gemini-cli/blob/main/docs/resources/tos-privacy.md) (paraphrase/short quotes via summarizer; verify)
- Maintainer post Feb 27, 2026: bans "to address violations of the Antigravity Terms of Service", cited "the use of 3rd party tools or proxies to access Antigravity resources and quotas"; bans "also blocked access to Gemini CLI and Gemini Code Assist"; "system-wide automated unban"; "If an account is flagged for a second violation of ToS, it will be permanently banned." — [gemini-cli Discussion #20632](https://github.com/google-gemini/gemini-cli/discussions/20632) (primary, vendor-maintainer)
- Same thread: May 2026 users reported appeals unresolved for days; others restored after resubmitting the form. — [same](https://github.com/google-gemini/gemini-cli/discussions/20632)
- User reports (secondary/anecdotal), Feb 11-20, 2026: bans after using OpenClaw with Antigravity/Gemini CLI OAuth, including paid AI Pro and Ultra accounts; error "Gemini has been disabled in this account for violation of Terms of Service"; some said web/app still worked; one speculated multi-agent Pro+Flash usage triggered it (speculation). — [openclaw/openclaw #14203](https://github.com/openclaw/openclaw/issues/14203)
- Secondary: Antigravity forum thread of a disabled account — [Google AI Developers Forum](https://discuss.ai.google.dev/t/antigravity-account-disabled-violation-of-terms-of-service-requesting-support/123014); one blog claims the terms were narrowed to "your Antigravity and/or Gemini CLI accounts" — [Zentor](https://zentor.ai/blog/antigravity-account-suspended-third-party) (single secondary source); claim that bans extend to whole Google account (Gmail/Drive) unverified. Hermes-agent removed these OAuth providers: [PR #50492](https://github.com/NousResearch/hermes-agent/pull/50492).

### Inferences
- Running the official `gemini` CLI yourself, signed in with Google, is the intended pattern; proxying its OAuth through other tools is the documented trigger. Heavy automated use via the official CLI was not shown to cause bans.

### Gaps
- Did not read Antigravity terms directly; current (Nov 2026) status of enforcement and whether scope covers only Gemini/Antigravity or entire Google account is unconfirmed.

## Real reported suspension cases (primary vs secondary)

### Takeaway
Google bans are well documented, including by a vendor maintainer (primary). Anthropic's enforcement is documented as token blocking/billing change, not clearly mass bans; OpenAI has no documented bans found.

### Cited Findings
- Primary-ish (vendor maintainer): Google Feb 2026 bans and unban — [Discussion #20632](https://github.com/google-gemini/gemini-cli/discussions/20632).
- Anecdotal user reports: [openclaw #14203](https://github.com/openclaw/openclaw/issues/14203) (including an unverified claim of a Claude ban while using OpenClaw with Max, flagged in the thread as unverified).
- Secondary news: [MLQ](https://mlq.ai/news/google-enforces-tos-bans-on-paid-antigravity-subscribers-using-openclaw-tool/), [secure.com](https://www.secure.com/blog/cybersecurity/google-bans-openclaw-users-a-warning-shot-for-the-agentic-ai-era).
- Anthropic enforcement as reported: technical block of OAuth in third-party harnesses (Apr 4, 2026) plus extra-usage billing — [TNW](https://thenextweb.com/news/anthropic-openclaw-claude-subscription-ban-cost) (secondary).

### Inferences
- Risk ranking for third-party OAuth routing: Google (documented bans) > Anthropic (explicit prohibition, technical block, ban right reserved) > OpenAI (ambiguous, partner-gated). For official CLIs on your own machine, risk is low across all three but not zero for high-volume headless loops.

### Gaps
- No reports found of bans for someone only chaining official CLIs via Bash; absence of evidence, not a confirmation. Full-text of OpenAI primary sources and Anthropic support pages remains unverified.
