# RFC — Future supervised automation orchestration (DEFERRED / NOT APPROVED)

**Status:** `BACKLOG_ONLY — DO_NOT_IMPLEMENT`  
**Recorded:** 2026-11-12  
**Owner decision:** Retain all useful ideas for potential later evaluation; do not implement or activate any new automation features until explicit owner validation and authorization.  
**Repository authority:** `AGENTS.md`, `prospector-de-sites/skills/repository-policy/SKILL.md`, `prospector-de-sites/skills/agent-runtime/SKILL.md` and current canonical Prospector Core skills remain authoritative.  
**Implementation authorization:** **NONE.** This document is an archival design proposal, not a work order, acceptance of a feature, or permission for a scheduling or deployment side effect.

> NO scheduler/cron (including a two-hour cadence), NO batch executor, NO autonomous site building, NO automatic deployment, NO new outreach, NO provider integrations, NO automatic CRM writes, and NO remote queue execution are approved at this stage. This RFC does not enable any flags, change workflows or schedule tasks. Explicit owner approval is required for EACH later phase and separately for any live release.

## 1. Background and sources

The initial reference was the user-supplied document **"Recurring Auto-Deploy: Prospect Sites to GitHub Pages"** (a Claude Code design for template cloning, CSV queue, a two-hour recurring job, up to five sites per run, GitHub Pages publication, optional ManyReach, rate-limit checks, retries, HTTP polling and one notification per batch).

We extracted transferable **infrastructure patterns**, but expressly rejected its generic template-copying, public repo-per-lead and autonomous cold-outreach architecture because those conflict with Prospector's factual provenance, individually directed sites, canonical 19-step process, human QA/release rules and private Vercel workflow. Its proposed interval and batch size are examples, **not requirements or approved defaults**.

Relevant shipped milestones (read code; descriptions are not substitutes for independent tests):

- [Core PR #2](https://github.com/leonardusrosa/gemini-prospector/pull/2): independent local QA queue, real canonical CRM adapter, bounded retries, lease fencing, exact-SHA deterministic gates and no CRM mutation.
- [Core PR #3](https://github.com/leonardusrosa/gemini-prospector/pull/3): explicitly operator-exported, metadata-only JSON snapshots, no automatic synchronization.
- [Dashboard PR #8](https://github.com/leonardusrosa/prospector-dashboard/pull/8): browser-only operator snapshot import, read-only status and correlation with PREVIEW_COPY.
- Current operation guide: [site-automation-queue-pilot.md](site-automation-queue-pilot.md).
- Current code: `prospector-de-sites/automation/{crm_source.py,job_store.py,worker.py,snapshot_export.py}` and `test_site_automation_pilot.py`.

**Current reality as of recording:** `worker.py run` plans without queue mutation; `run --execute-gates` claims **one** local job, invokes repository-wide `npm run site-review`, and can only finish at `ready_for_review` (or `blocked` / `retry`). The canonical `prospector.db` is opened read-only. The dashboard imports an explicit local JSON file, not a live queue. No recurring task, batch dispatcher, publisher or outreach channel is wired into this queue. A synthetic positive path is not a real tenant publication QA.

## 2. Current boundary — MUST remain in force

1. Canonical lead truth: local SQLite `prospector.db` (read-only for automation); hosted Supabase `PREVIEW_COPY` is not authoritative and is not a write target.
2. Existing queue: ignored local `.prospector/auto-deploy-queue.sqlite3`. `site_automation_jobs` currently includes `(lead_slug,job_kind)` uniqueness, `state` in `pending | leased | retry | blocked | ready_for_review`, attempts, due timestamp, lease owner/token/expiry, last sanitized error, `last_sites_sha`, gate exit and timestamps; `site_automation_events` stores the audit trail. `BEGIN IMMEDIATE` ensures local atomic claims.
3. Eligibility: qualified/redesigned lead, source-and-time-verified actionable non-SMS contact evidence, required `clientes/<slug>/` or `sites/<slug>/` site artifacts, clean Git tree and same source SHA before/after gate. Never infer evidence from a bare contact value. Existence of contact evidence **does not authorize contact**.
4. Local deterministic `npm run site-review` is necessary but insufficient for rendered/browser QA, independent factual check, creative review, proposal approval, AI assistant live smoke or Vercel release.
5. QA queue status must never automatically become CRM `publicado`, proposal sent, contract approved, outreach eligible or customer-ready.
6. No provider/send/publish/call/payment endpoint may be introduced as part of this RFC, and no generic template clone may bypass the GPT-Taste / evidence / design diversity requirements.
7. No background watcher, GitHub Actions cron, Windows Task Scheduler, Automations task, n8n flow, Vercel Cron or hidden daemon may be registered as a side effect of writing or reviewing this document.
8. No secrets, PII, lead research or raw error logs may be committed or embedded in hosted snapshots. Queue file stays off Git/cloud drives.

## 3. Feature inventory — what already exists vs proposed

| Capability from reference | Present now | Possible future form | Decision |
| --- | --- | --- | --- |
| Durable queue / deduplication | SQLite queue, unique lead + job kind | Retain | Shipped |
| Atomic locks, overlapping jobs | Lease token, expiry fencing | Preserve with ownership and stale-lease recovery tests | Shipped |
| Retry after transient faults | Bounded backoff, 3 attempts and manual requeue | Add operator diagnostics only if needed | Shipped |
| Evidence/qualification safety | Read-only CRM + source-backed research artifacts | Preserve fail-closed | Shipped |
| Deterministic local QA and SHA | `site-review` plus SHA/worktree checks | Possibly tenant-scoped QA only if independently trustworthy | Shipped |
| Status dashboard | Manual sanitized JSON import | Maybe local-only faster refresh, never hosted CRM authority | Shipped manual / future optional |
| Two-hour recurrence | None | Optional configurable scheduler following explicit owner validation | Deferred, not authorized |
| Five-item batches / continue-on-error | One job per explicit invocation | Bounded sequential batch or capped concurrency | Deferred, not authorized |
| GitHub API budget / backpressure | No batch-level quota policy | Per-provider quotas, cost budgets, rate limits, circuit breakers | Deferred, not authorized |
| Reconciliation of repo/deployment/URL | Not part of local queue | Read-only evidence reconciliation with canonical artifacts and provider IDs | Deferred, not authorized |
| Monitoring / notifications | Audit events and manual export | Local summary and opt-in redacted alerting, no send by default | Deferred, not authorized |
| Live site generation from queue | Explicitly out of scope | Separate future integration with canonical site engine and mandatory reviews | Separate decision, not authorized |
| Template clone + brand replacement | Rejected | No generic replacement | Rejected |
| Public GitHub Pages per lead | Rejected | Continue current controlled Vercel design | Rejected |
| ManyReach automatic lead insertion | Rejected | Outreach remains separately authorized; primary Telnyx calls, secondary WhatsApp/email, each governed by its own workflow | Rejected for this queue |

## 4. Future architecture sketch (DESIGN ONLY)

Conceptual, not executable:

```text
explicit operator authorization
            |
     local-only preflight  ----> fail closed (no work)
            |
    read-only CRM + research evidence + immutable site SHA
            |
   planner (dry-run, no queue claim, no external calls)
            |
   bounded local QA dispatcher [FUTURE, OFF]
            |
   existing transactional claim + fencing
            |
   npm run site-review (unchanged canonical gate)
            |
  evidence ledger / sanitized run summary [FUTURE, OFF]
            |
    ready_for_review (human)
            X
   NOT deploy / NOT promote CRM / NOT outreach
```

Separation of responsibilities if designed later:

- **Core adapter**: authoritative evidence checks and source selection, without updating `prospector.db`.
- **Planner**: enumerate due jobs, compute eligibility, cost/quotas and immutable plan; explicit dry-run default. No remote preview-copy use as source of truth.
- **Dispatcher**: optional local process only, once approved; runs a bounded number of existing QA-only jobs; never imports a send/publish module.
- **Queue store**: transactional state machine and event ledger; preserve leases and retry budget. Any schema migration requires backup, forward-only design, migration test and independent QA.
- **Report**: sanitized per-cycle counts, SHA, reason codes and durations, without PII. The existing snapshot `schemaVersion=1` and `canExecute=false` remain unchanged until a separately approved compatibility plan.
- **Operator control**: explicit enable/disable and per-run authorization where relevant, stop/kill switch and readable status. Current dashboard must remain read-only; a future control plane requires its own threat model and permission review.

### 4.1 Work selection, batches and concurrency (not yet decided)

- Candidate job is eligible only after **re-reading** canonical CRM evidence and site files **at execution time**, not merely at enqueue or snapshot time.
- Preserve existing claim/lease fencing. Never use a mutable CSV `status` field as the only lock.
- Preserve fairness and deterministic ordering, enforce unique work by `lead_slug` and `job_kind`, disallow overlapping processing for the same slug.
- **Proposed** settings (not defaults in code): `max_jobs_per_cycle`, `max_parallel_jobs`, `max_cycle_seconds`, `per_job_timeout_seconds`, `max_daily_jobs`, and `max_daily_provider_cost`. Values must be based on local CPU/RAM, actual gate duration and provider budgets. Reference `BATCH_SIZE=5` is not approved.
- Prefer sequential execution initially; running the entire `site-review` suite concurrently against one `prospector-sites` checkout may conflict, be redundant or produce false results. Concurrency >1 must require isolated clean worktrees and independently proven non-mutating QA.
- A failed item must not silently mark a different item complete. Fatal global conditions (missing CRM, dirty worktree, source drift, budget exhaustion, unauthorized runtime) stop the cycle; per-lead factual blockers stop only that lead. No automatic requeue of factual errors.
- Empty queue is a successful no-op, with no external message or alert. Explicit manual requeue must not steal active leases.

### 4.2 Scheduling, cadence, runtime and pause/resume (not yet decided)

**No schedule is to be created now.** A potential schedule needs a new RFC approval, a chosen reliable host (Windows local task vs dedicated server, etc.), timezone, DST/missed-cycle policy, machine-off behavior, job identity, isolation and explicit execution windows.

If approved someday:
- Keep a disabled-by-default feature flag, fail closed when configuration is absent, invalid or ambiguous. No implicit `0 */2 * * *`.
- Single authoritative scheduler and distributed-lock model appropriate to the chosen host; do not synchronize the SQLite queue across hosts or treat a local lease as a distributed one.
- Prevent catch-up storms after downtime; require a separate missed-run policy. No unreviewed backlog flush.
- Expose a kill switch and tested disable procedure. A paused queue retains durable jobs; unpause requires explicit consent, not just a deploy.
- Record planned vs actual start, duration, outcome, reason codes and state, without contact or other sensitive data.
- Require an operational owner and documented on-call/incident and rollback instructions before enabling.

### 4.3 Quota, budgets and rate-limit governance (not yet decided)

- `gh api rate_limit` in the reference is only an example. Identify **actual** remote calls before adding any GitHub, Vercel, Maps, AI, image or communications quota monitoring.
- Record per-provider token/request/time costs without leaking credentials, handle `429`, quota headers and backoff, including a global circuit breaker.
- Do not retry non-idempotent provider actions automatically; any such future action requires an idempotency key, state reconciliation and explicit approval.
- Enforce stop-before-overage thresholds for time, money and throughput; do not invent budgets.
- Telephony, WhatsApp, email and payment spending are **out of scope for this QA queue**.

### 4.4 Reconciliation, evidence binding and reporting (not yet decided)

- Future read-only reconciliation may compare local job `last_sites_sha`, actual clean Git HEAD, canonical site artifacts and (only in a separately authorized release workflow) immutable Vercel deployment ID, domain aliases and readiness/smoke evidence.
- An HTTP 200 by itself is **never** sufficient. A deployment READY state by itself is not human sign-off; the exact SHA, rendered QA, factual/proposal review and assistant smoke must reconcile.
- For jobs stuck `leased`, use expiry/fencing semantics rather than blindly resetting a lock. For `blocked`, distinguish factual, eligibility, QA, repository drift and infrastructure failures with stable sanitized reason codes.
- Summary schema proposal: `run_id`, `mode`, `started_at`, `ended_at`, `source_sha`, `planned`, `claimed`, `ready_for_review`, `blocked`, `retry`, `skipped`, `budget_stop`, `notifications_sent=0`. Do **not** include emails, phone numbers, free-form review excerpts or tokens.
- The imported dashboard snapshot is **advisory** and may be old; it is not a dispatch command or approval record.
- Optional `ntfy`/email/Slack alerts are **not approved**. If proposed later, never make an externally visible topic publicly guessable; choose a verified private channel with strict PII redaction and user opt-in. Alert only on useful state changes, not on empty cycles.

## 5. Phased implementation roadmap — ALL PHASES WAIT FOR OWNER

The following is a plan to *consider*, not a to-do list agents may start:

**P0 — owner decision and baseline audit (mandatory before any code):**
- Owner verifies the present manual queue, source evidence quality, review outcomes, desired operational scope and reason to automate.
- Collect measured resource usage, test duration, false-block rates and realistic expected lead volume.
- Decide allowed environments, job classes, target throughput, maximum budgets, cadence if any, required operator sign-offs and explicit stop conditions.
- Agree whether even background **read-only checks** are acceptable. No silent trial scheduling.
- Write a new issue/PR with explicit user authorization, frozen threat model and acceptance criteria. Until then: stop.

**P1 — local planner / simulation only (requires a separate approval):**
- Read-only due-job view, immutable candidate-plan preview, reason-code diagnostics, quota *estimates* and operator-facing run receipts. No new queue claims, no cron and no network calls.
- Tests: empty queue, deterministic ordering, eligibility drift, duplicate slug, dirty repo, missing evidence, mixed stages, no side effects.

**P2 — explicit one-off bounded batch (requires a separate approval):**
- One user-invoked `run-batch --execute-gates` design, capped sequential execution using existing `execute_one`, per-cycle time/budget limits and no-send/no-deploy boundary.
- Tests: 2+ independent jobs, one blocked and one successful, lease collisions, expired lease, process kill/restart, partial failure, source SHA drift, retry exhaustion, queue/CRM integrity.

**P3 — supervised recurrence (requires a separate approval):**
- Only after P1/P2 observational results: choose host, schedule and cadence; start with a reversible feature-disabled configuration and dry-run telemetry; require explicit enable.
- Tests: scheduler disabled by default, duplicate triggers, sleep/wake, DST/timezone, missed schedule, rapid disable, restart, no unexpected external activity.

**P4 — optional read-only reconciliation and notifications (requires separate approval):**
- Improve QA evidence/status diagnostics and cost reporting; keep dashboard manual until the owner approves a separate data flow, privacy model and authentication.
- No public site deployment, CRM promotion, outbound contact or multi-host execution is implied.

**P5 — integration with the full site engine or release (a new project decision):**
- Not covered by the above phases. Requires canonical 19-step workflow, GPT-Taste pre/post reviews, design DNA, source-verified media/reviews, impeccable/copywriting audits, factual recheck, browser QA, Vercel build/Preview, assistant smoke and explicit human release. No template cloning or made-up evidence.
- Outreach remains a separate human-authorized system; do not attach Telnyx/WhatsApp/email send-on-ready behavior.

## 6. Security and QA acceptance gates for ANY future implementation

A later PR is not acceptable until it proves:

- **Disabled-by-default:** without an explicit enable and authorized operator, no scheduler is installed, no queue is claimed and no network/provider call occurs.
- **CRM immutability:** hash before/after of the real canonical `prospector.db` remains identical for dry-run and QA worker; no Supabase PREVIEW_COPY writes.
- **No send/release path:** a static import scan and integration tests prove no calls to outreach, telephony, payment, GitHub public repo creation or Vercel production deployment.
- **Atomic execution:** concurrent starts, duplicate queue entries, lease takeover, expiry, stale token and process crash cannot double-complete or overwrite another worker.
- **Fail-closed evidence:** incorrect stage, unverifiable contact, missing artifact, dirty tree, changed SHA, invalid/missing approval and stale release evidence block.
- **Bounded failure:** per-lead failure isolation, global kill on infrastructure errors, finite retries, backoff, rate-limit and budget-stop behavior.
- **No sensitive leakage:** fixture-only logs, sanitized event reason codes, strict snapshot schema, no tokens or customer evidence in CI logs, PRs, alerts or hosted endpoints.
- **Reversibility:** documented pause, disable, rollback and stale-lease recovery; no orphan scheduler and no unexpected catch-up run.
- **Full regression:** Python local tests, actual Windows CLI execution, clean checkout `npm run site-review`, dedicated CI, and independent browser QA only if UI changed. Test with synthetic fixtures; do not confuse their PASS with live tenant readiness.
- **Deployment/release gate:** owner must separately authorize any Production change, actual hosted publication or outbound action; passing code CI does not override this.
- **Performance/cost evidence:** measured runtimes, API quotas and resource consumption rather than reference-derived assumptions.

## 7. Decision log and rejected assumptions

**Accepted from source reference as concepts:** persistent queue, duplicate suppression, atomic state transitions, fair bounded selection, transient retry, rate-limit awareness, independent per-item error handling, status visibility, sanitized summary and explicit operator control. Some concepts are already shipped; the rest are merely documented.

**Rejected:** clone-and-rebrand static dental templates; automatically create public GitHub repos/Pages; add a prospect to ManyReach on deployment; declare completion on HTTP 200 / nonempty H1 / debrand grep; generic replacement of canonical expert design process; unrestricted public alert topic; assuming a cron expression, batch size or provider budget is approved; rewriting Prospector Core policy to mimic a third-party prompt.

**Open questions reserved for the owner:** What event demonstrates readiness to automate? How many leads/day? Which job kinds? Single-machine vs server? Exactly which steps may happen unattended? Acceptable hardware/time/money budget? When may a job be requeued? What fresh evidence is mandatory? Which notifications (if any)? What is the separate human approval and cancellation mechanism? What is the recovery objective after failure?

## 8. Explicit handoff to a future agent

Before doing anything beyond reading this document:

1. Read the current `AGENTS.md`, canonical skills, the existing queue code/tests and this RFC. Do not use assumptions from 2026 as facts after the code evolves.
2. Confirm that the operator **explicitly requested** a specific future phase; this RFC is not that request.
3. Re-audit real CRM schema, clean sites tree, provider capabilities, desired source/target environment and current deployment rules.
4. Propose a narrowly scoped PR with an acceptance matrix and default-disabled controls. Ask for approval before any behavioral change or task scheduling.
5. Never initiate an autonomous full-site build, GitHub Pages release, live outbound outreach, Telnyx call, WhatsApp/email send, payment, or CRM promotion as a side effect.
6. If approval is absent or ambiguous: report `DEFERRED_NOT_AUTHORIZED`, make **no changes** to execution paths, queue data, scheduler configuration or production settings.

**This is a parked research and implementation plan, not an activation ticket.**
