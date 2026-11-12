# Site Automation Queue Pilot (local QA only)

## Scope

This is a manually triggered **fail-closed** pilot for site-preview QA. It is
not a site builder, an outreach campaign, a deployment service, or a scheduler.

- **Source of truth:** existing canonical local SQLite CRM (prospector.db).
- **Canonical CRM access:** SQLite read-only URI. No CRM schema changes, write
  operations, lead promotions, or hosted PREVIEW_COPY writes.
- **Queue:** separate ignored .prospector/auto-deploy-queue.sqlite3 file.
- **Website QA:** uses the existing prospector-sites npm run site-review gate.
- **Completion:** ready_for_review only. This means local deterministic checks
  passed, NOT that visual QA, Vercel deployment, AI assistant live smoke,
  proposal QA, release approval, or customer delivery passed.
- **No automated sends:** no ManyReach, Gmail, WhatsApp, SMS, phone calls, or
  payments. No automatic publish, push, or GitHub repository creation.
- **No schedule registered:** calls are explicit until a separate design/PR
  authorizes a trusted always-on worker and its budget/lease policies.

The worker handles **at most one** lead per invocation. Default run is a
read-only dry-run and does not mutate the queue.

## Prerequisites

Use a local checkout of this repository containing the canonical
prospector.db and a separate local prospector-sites checkout. Do not upload
CRM databases, contact evidence, tokens, or customer photographs into Git.

From the root of gemini-prospector:

1. python prospector-de-sites/automation/worker.py init
2. python prospector-de-sites/automation/worker.py enqueue --slug LEAD-SLUG
3. python prospector-de-sites/automation/worker.py list
4. python prospector-de-sites/automation/worker.py run --sites-repo ../prospector-sites
5. python prospector-de-sites/automation/worker.py run --sites-repo ../prospector-sites --execute-gates

Step 4 is strictly read-only. Step 5 explicitly acquires one lease and runs
the existing full-repository local deterministic QA suite. Before Step 5,
verify that npm dependencies are available in the sites checkout. The worker
does not install dependencies or select/merge branches.

Custom paths can be passed as --crm-db and --queue-db **before** the subcommand.
For example, use a local temporary fixture database to test safely.

To retry after correcting a blocker, run:

- python prospector-de-sites/automation/worker.py requeue --slug LEAD-SLUG

The command does not steal an active lease. It resets a previously blocked,
retrying, or reviewed job into pending. The same slug is never enqueued twice
by accident.

## Eligibility and handoff

The worker reads the canonical lead by slug and refuses new work unless:

- stage is qualified or redesigned (or the corresponding Portuguese aliases);
- there is a verified actionable non-SMS contact method with source and
  verification timestamp, or equivalent verified email evidence;
- the matching prospector-sites client directory has index.html,
  proposta.html, and review-manifest.json;
- the sites repository has a clean Git worktree and a resolvable HEAD SHA.

The lead-contact gate is deliberately stricter than an unverified CRM record.
No missing source or timestamp is inferred. It is never an authorization to
contact the lead.

The existing site-review command remains authoritative for its own test
coverage. It currently runs across the site repository rather than exclusively
against the selected tenant; an unrelated failing tenant can block this
pilot. The worker stores the exact source SHA and only an exit code, not
sensitive command output. Tests are not passed by simply checking HTTP 200.

Only a separate authorized workflow may later perform:
- rendered desktop/mobile inspection and formal creative review;
- source-backed factual/review reconciliation and proposal QA;
- Vercel deployment and verification bound to exact commit/deployment;
- assistant live smoke at exact Preview SHA, if provisioned;
- human release decision and subsequent CRM promotion;
- individual human-approved outreach.

Existing Prospector Core design rules, agent-runtime adapters, Engine C, and
predeploy gates are not changed by this pilot. In case of differing historical
documents, the current repository's AGENTS.md and canonical skills win.

## Queue semantics

- SQLite BEGIN IMMEDIATE makes selection and claim a single-writer atomic
  transaction across simultaneous workers sharing the same local database.
- UNIQUE (lead_slug, job_kind) prevents duplicate queue jobs.
- Each claim has a random lease_token and a finite lease_until.
- Expired leases may be reclaimed; an old token cannot complete the new claim.
- Operational errors retry with bounded exponential backoff (30s to 1h).
- Quality, eligibility, and factual blockers stop as blocked until explicit
  operator requeue. There is no silent bypass of QA.
- Events are stored separately from job state for an audit trail.
- SQLite lease protection is local-filesystem scoped. The queue file must not
  be synchronized between machines via cloud drive or Git. Multi-host
  production scheduling would require a server-side transactional store.

## Local regression

From repository root:

python test_site_automation_pilot.py

Expected coverage includes duplicate prevention, lease recovery and fencing,
read-only CRM byte integrity, non-SMS verification checks, missing artifact
blocks, explicit gate-only execution, retry backoff, and no-send/no-deploy
completion semantics. GitHub Actions tests this file with Python 3.12.

## Known limitations

This is a **local-queue and gate adapter pilot**, not full autonomous site
generation. No first-party factual research, image design, render QA or
production deploy is automatically executed. Direct triggering of the core
site-creation 18-step process remains a separate future integration.

No performance or pricing savings have been measured. Never label a job
ready_for_review as "published", "proposal sent", or "assistant ready".
