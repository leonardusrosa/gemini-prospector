# Local CRM + Vercel Public Architecture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make local Windows SQLite and dashboard the only active Prospector CRM runtime while keeping public sites, proposals, and the production assistant on Vercel.

**Architecture:** The local checkout owns CRM state, evidence, generation, gates, and deployment orchestration. Vercel remains the public serving layer. Phoenix remains only as a preserved rollback/archive target; its remote adapter stays available for explicit legacy inspection but is removed from normal publication semantics.

**Tech Stack:** Python 3 standard library, SQLite, repository-owned deterministic gates, Node.js/Vercel static deployment, SSH/systemd for Phoenix rollback state.

---

### Task 1: Reconcile and preserve Phoenix state

**Files:**
- Remote read-only state: `/var/lib/prospector-dashboard/prospector.db`, `/var/lib/prospector-dashboard/prospector-config.json`, systemd and Traefik configuration.
- Remote backup: `/var/lib/prospector-dashboard/backups/prospector-final-20260903-162747/`.

- [x] Compare all six local/Phoenix leads on identity, status, address, phone, WhatsApp, rating, rating count, URLs, and relevant metadata; preserve observed divergences without mutating factual lead data.
- [x] Create a root-only protected Phoenix backup containing the SQLite database, Prospector config, service/env configuration, and active proxy route files.
- [x] Verify backup file modes, SHA-256 hashes, SQLite integrity, and lead count without printing credential contents.

### Task 2: Keep publication local-only and document Phoenix as legacy

**Files:**
- Modify: `prospector-mcp.py`
- Modify: `prospector-de-sites/prospector-mcp.py`
- Modify: `prospector_remote.py`
- Modify: `prospector-de-sites/prospector_remote.py`
- Modify: `deploy/phoenix/README.md`

- [x] Ensure `f_status` and `f_salvar` mutate local SQLite and return `PUBLISHED_LOCAL_ONLY` without importing or calling the remote adapter.
- [x] Ensure active workflow source contains no automatic remote-sync call or mandatory `REMOTE_SYNC_PENDING`/`REMOTE_SYNC_FAILED` branch.
- [x] Make the remote adapter module docstring and Phoenix deployment documentation explicitly state legacy/optional rollback-only status.

### Task 3: Add and run migration regressions

**Files:**
- Modify: `test_remote_sync_regression.py`

- [x] Cover local SQLite status mutation with `urllib.request.urlopen` patched and assert no remote result fields.
- [x] Preserve isolated legacy-adapter tests for explicit sync success, divergence reporting, and credential redaction.
- [x] Add a static regression proving active MCP publication source has no remote adapter import/call and that the adapter is explicitly legacy.
- [x] Run the migration regression plus dashboard, runtime, and relevant repository tests.

### Task 4: Verify canonical local dashboard

**Files:**
- Read/verify: `dashboard-server.py`, `dashboard-template.html`, `iniciar-dashboard.bat`, `prospector.db`.

- [x] Start the existing local server in a hidden test process, read `/api/leads`, and verify the three published lead metrics and two qualified leads.
- [x] Verify server mode reads SQLite and that localStorage is not the source of server-mode lead state.
- [x] Stop only the test process and confirm no listener remains on port 8765.

### Task 5: Verify Vercel and gates without changing prospect sites

**Files:**
- Read/verify: `E:/Antigravity/prospector-sites/package.json`, `assistant/provider-runtime.js`, live Vercel endpoints.
- Modify: `E:/Antigravity/prospector-sites/vercel.json` (preview-route robots headers only).

- [x] Run the complete `npm run site-review` and `npm run vercel-build` gates from the clean sites repository.
- [x] Verify live Vercel root, generated site/proposal routes, robots policy including the new Vercel `X-Robots-Tag`, assistant method behavior, and production OpenRouter provider order after the config push.
- [x] Confirm generated prospect HTML and assistant/provider source remain unchanged; only the required preview header config differs.

### Task 6: Verify Phoenix retirement and domain state

**Files:**
- Remote read-only state: `prospector-dashboard.service`, preserved `/var/lib/prospector-dashboard`, `/opt/gemini-prospector`, and Traefik route files.

- [x] Stop and disable `prospector-dashboard.service`; verify inactive/disabled and no Prospector timer restarts it.
- [x] Verify preserved rollback files/directories remain present.
- [x] Remove the retired `prospector.autocora.com.br` DNS record without changing other records; verify authoritative and public resolvers return NXDOMAIN while the apex and `www` records remain intact.

### Task 7: Final verification and integration

**Files:**
- Git state in `E:/Antigravity/prospector` and `E:/Antigravity/prospector-sites`.

- [x] Run fresh final tests after all edits and inspect both repository diffs/status.
- [x] Commit local Prospector changes and the required Vercel preview-header change with descriptive messages.
- [x] Push both repository commits to `origin/main`.
- [x] Report local CRM, Vercel, Phoenix, domain, tests, Git, remaining issues, and `Messages sent: 0`.
