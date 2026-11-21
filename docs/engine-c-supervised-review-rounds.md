# Engine C supervised autonomous-build protocol — review rounds v1

**Status:** isolated local QA implementation; not a live site-generation executor.
This is a code handoff contract for browser/vision/code agents. It does not run
an LLM, log into social media, build or deploy a site, mutate CRM, call Telnyx,
schedule a job, send outreach, or approve Preview by itself.

## What exists

- The Prospector international research planner
  (prospector-de-sites/automation/site_research.py) inventories possible
  official website/social sources while keeping all social identity and
  media rights unverified until actual browser/human evidence is collected.
- Engine C from the prospector-sites Dallas experiment proposes three
  divergent, image-first layouts, evaluates them, selects a winner and converts
  that winner to a responsive static site.
- The **new bridge** (prospector-de-sites/automation/engine_c_bridge.py)
  recomputes the selected winner from all three weighted scores/hard gates,
  hashes actual mock images and rejects missing generation/reviewer context
  separation in evaluations.
- The **new protocol** (prospector-de-sites/automation/site_review_rounds.py)
  gives each lead eight explicit gates, stale artifact and witness protection,
  an independent reviewer identity requirement, two correction rounds per gate,
  an atomic, local-only state receipt, and a terminal human Preview decision.

The local review protocol returns only PROTOCOL STATES. Evidence files and
fresh reviewer identity fields are necessary but never sufficient to prove
that a person or independent visual model really inspected the content.
Live browser, factual, media-rights and creative evidence must be
independently observed; never treat a self-authored JSON PASS as authority.

## Stage order

1. FACTS_AND_IDENTITIES: direct business identity, correct location,
   services, site classification and source references.
2. MEDIA_RIGHTS_AND_RELEVANCE: actual business-owned media, exact original
   source, documented commercial reuse rights, semantic suitability.
3. ENGINE_C_CANDIDATES: exactly A/B/C with different source-image SHAs,
   each bound to its generation identity and the source manifest SHA.
4. INDEPENDENT_DESIGN_DIRECTION: verified Engine C selector decision,
   recomputed hard gates, all mock/image hashes and fresh evaluator context.
5. IMPLEMENTATION_AND_RESPONSIVE: code and layout from the selected visual
   candidate, responsive design, accessibility and valid contact links.
6. CLIENT_CMS_COMPATIBILITY: full static HTML source and SHA, verified
   through the canonical AutoCORA CMS structural compatibility check.
   Provisioned tenant login/edit/draft/publish/rollback runtime smoke is
   a separate mandatory prerequisite for client delivery.
7. BROWSER_VISUAL_AND_INTERACTIONS: real desktop (>=1000 px) and mobile
   (320–600 px) PNG screenshots plus independently observed interactions,
   no horizontal overflow and zero page errors. If preview-only business
   images lack reuse checks, a protected recipient-only URL plus real
   independent HTTP privacy/noindex probes are mandatory.
8. FACTUAL_AND_CONVERSION_RECHECK: real deterministic site-review gate
   exit/log hash and renewed source-backed factual/commercial checks.

When every stage has independently observed PASS_REVIEWED, the run becomes
AWAITING_HUMAN_PREVIEW. It **never** becomes production-authorized.
The review protocol now uses schemaVersion=2; legacy v1 local runs cannot
be silently upgraded to skip Client CMS compatibility. They must be
restarted as new isolated runs. CMS tenant provisioning and actual authenticated
edit/draft/publish/rollback are still required for final client handoff.
Preview publication itself remains a separate capability/policy decision.

## Correction loop

Every FAIL yields NEEDS_CORRECTION for that stage and a targeted corrective
task for a code/vision agent. New artifact bytes are mandatory. A correction
increments the stage round counter. Following exactly two corrections, a third
FAIL becomes BLOCKED and requires an operator decision. Changes invalidate
the previous SHA-bound review. On every CLI action the **entire previous
chain** of source, artifact, report, and witness hashes is checked again.

This prevents accidental drift and unsupported re-use of an old PASS across
a new screenshot or candidate implementation, even if a local script reports
success. It does not cryptographically authenticate who submitted a report.

Only one writer may update a run at a time. A stale .lock requires manual
process diagnosis rather than automatic unsafe lock stealing.

## Engine C evaluator contract (new experiments)

For candidate X in A/B/C, maintain separate image outputs at:

    mocks/candidate-x.png
    evaluations/candidate-x.json

Every evaluation JSON retains the canonical hard_gates/scores fields and adds:

    provenance:
      generatorId: named distinct generator/executor
      evaluatorId: distinct independent design judge
      generationContextSha256: hash of the generation prompt/context bundle
      evaluationContextSha256: different hash of clean evaluation context
      mockSha256: SHA256 of exact candidate image bytes

The selector decision continues to use the canonical
scripts/engine-c-select.mjs. Do not change its weighting or hidden task
constraints. The bridge independently recomputes eligibility and winner
without modifying the experiment. All three hard-gate sets must be truthful
and evaluated by a fresh independent context; a distinct string alone is
not proof of independence.

Legacy Dallas experiment:
- Its deterministic winner C is reproducible (C score 90.5).
- Its older evaluation files lack the new provenance fields. The bridge
  correctly returns BLOCKED pending independent re-evaluation and evidence.
- **Do not fabricate provenance retrospectively**; retain legacy output as
  historic evidence, and independently rerun evaluation when required.

## Local CLI and ignored receipts

First create/update the actual factual/media evidence manifest with
Remote Desktop/browser research. Public social profile URLs are NOT
permission to download/re-host media. Bind every claimed approved image
to its exact verified official profile and independent rights record.
Keep source manifests and generated prospect data under .prospector/.

Then, from the canonical repository root:

    python prospector-de-sites/automation/site_review_rounds.py init --research .prospector/pilot/site-research.json --run .prospector/pilot/review-run.json

Inspect:

    python prospector-de-sites/automation/site_review_rounds.py status --run .prospector/pilot/review-run.json

Per stage, a code/vision agent writes a JSON artifact containing:
schemaVersion=1, exact stage name, sourceManifestSha256 and stage-specific
payload, then an independent review agent writes a JSON report with exact
artifactSha256, reviewerId, verdict and nonempty observations pointing to
real existing evidencePath + evidenceSha256 witnesses.

    python prospector-de-sites/automation/site_review_rounds.py submit --run .prospector/pilot/review-run.json --stage FACTS_AND_IDENTITIES --artifact .prospector/pilot/facts.json --author implementation-agent
    python prospector-de-sites/automation/site_review_rounds.py review --run .prospector/pilot/review-run.json --report .prospector/pilot/facts-independent-review.json

The system never interprets an operator ID string as a signed identity or
uses it to authorize publication. Every stage of true autonomous generation,
image/visual evaluation and correction requires its own connected agent
executor; this repository code only defines and enforces the safe handoff.

## What an agent executor still must provide

- A source-observing Remote Desktop/browser adapter (public sites only to
  begin with), with explicit site identity checks and no social login
  bypass, CAPTCHA evasion, mass media download or outreach.
- An image-capable design generator able to create three divergent mockups
  from a verified source brief (not site-wide template copies).
- An independent evaluator running with fresh context, with original image
  pixels available (mock screenshots are not sufficient through text alone).
- A code builder and correction agent, limited to the exact requested
  site worktree and with external network/file changes separately guarded.
- A browser QA adapter producing real screenshot files, page-error/overflow
  observations and source-verifiable claims before recording PASS.
- A final operator Preview process. Production publication and all contact
  activity remain separate, manual releases.

## QA

    python test_engine_c_bridge.py
    python test_site_review_rounds.py
    python test_market_scope_and_site_research.py
    python test_site_automation_pilot.py

All tests are synthetic and offline. No fixture or local PASS establishes
permission for international outbound voice calling, copyright reuse or
production website publication.

## New owner decisions: verticals, CMS and internal-only imagery

See docs/cms-owner-preview-and-priority-niches.md. Prioritize restaurants,
pizzerias, cafes and clinics/dentistry across US/Canada/Europe. Use static
HTML/CSS/JS by default because the existing Client CMS edits and persists
complete HTML. Clinical advertising/patient imagery needs extra local review.
A verified, identity-linked brand image with unconfirmed reuse rights may be
used for a genuinely access-protected owner-review-only preview. It may not
be silently copied into public site assets or deployed anonymously. The
independent browser step must prove recipient-only/noindex access before
any private media is exposed. A standalone static HTML file is not proof
that the client admin tenant has been provisioned.
