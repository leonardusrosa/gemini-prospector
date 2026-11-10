# Prospector machine — local runtime readiness runbook

Status: **Draft-only machine preflight**. CI is deterministic evidence that
repository checks run in a clean runner; it does not prove this Windows host's
active AGY CLI, browser/MCP tools, CRM database, site deployment, or messaging.

## Scope and policy

Use the canonical repository `leonardusrosa/gemini-prospector`.
Read `AGENTS.md`, `prospector-de-sites/skills/repository-policy/SKILL.md`,
`prospector-de-sites/skills/agent-runtime/SKILL.md`, and relevant task
skills. The repository rules override agent-specific adapters.

This procedure is **read-only for CRM and deployed sites**. Do not run
discovery, create leads, generate/publish a customer website, contact
prospects, connect phone calls, run `migrate:apply`, or merge a PR.
New Brazilian lead discovery remains prohibited by the canonical market
policy. Do not use a live customer as a synthetic test fixture.

## Part A — portable Core evidence

From an existing authenticated local clone and a clean/preserved worktree:

```powershell
python prospector.py doctor --agent antigravity --json
python prospector.py self-test
python test_agent_runtime_portability.py
python test_google_reviews_evidence.py
python run_autonomous_site_review_regressions.py
```

Capture exit codes, number of tests and the failing test name if any.
The `doctor` is only a local/static inventory. Mark runtime-only
capabilities `NOT_VERIFIED`, not `PASS`, until actually probed.

As of 2026-11-10, the committed portable carousel fixture fix in Draft
PR #1 passed GitHub Actions quality-gates run
https://github.com/leonardusrosa/gemini-prospector/actions/runs/42835667021 .
The unmerged `main` branch still contains the historical
workspace-dependent test; test the PR branch to reproduce green CI.

## Part B — local MCP handoff, no side effects

```powershell
python prospector.py setup --agent antigravity --workspace .
```

This produces ignored files `.prospector/runtime.json` and
`.prospector/mcp.generated.json`. Import the latter into the native AGY
CLI using its documented MCP configuration mechanism.

**Probe the exact live state**:
1. Check AGY CLI sees the `prospector-crm` MCP server; read-only list
   of tool names is not yet proof that a CRM request succeeds.
2. Run only a safe read-only CRM metadata or lead-count request.
   Do not return private customer records, contacts, or credentials.
3. Probe the configured browser/Playwright MCP by opening a
   non-customer test page and recording whether navigation works.
4. Verify git/GitHub connectivity read-only and Vercel project access
   read-only, with no deployment.
5. If required for a future site, probe the actual design-judge
   capability; check current source/version rather than fabricating
   a `GPT_TASTE_*` or design-judge PASS marker.
6. For each capability distinguish `PASS`, `FAIL`, `NOT_CONFIGURED`,
   and `NOT_TESTED`. Never infer availability from a binary or file.

The ChatGPT AGY Bridge currently exposes only sandbox, tony,
poly-weather and atlas workspaces: it does **not** automatically
inherit native AGY CLI settings or access the Prospector clone.

## Part C — readiness report

Return a sanitized table with:
- local repo branch and head, worktree cleanliness
- doctor, self-test, portability, review evidence and autonomous QA results
- CRM MCP server discovery and **actual** read-only query results
- browser MCP, GitHub and Vercel live probe results
- missing runtimes/tools and permission or startup errors
- operator-held provider credentials: `present` / `missing` only
- counts: new leads = 0; outreach sends = 0; production changes = 0

Prospector **machine ready** is not an appropriate status until all
required capabilities are live-probed and a permitted synthetic end-to-end
site build has passed the canonical 19-step review/publish procedure.
Do not loosen deterministic QA rules to meet a nominal readiness target.
