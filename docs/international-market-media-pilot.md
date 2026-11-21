# Prospector P0/P1 — US, Canada and Europe market + media research pilot

Status: isolated feature branch. No production activation, customer contact or unattended crawler.

## New discovery market scope

Only US, CA and European ISO 3166-1 alpha-2 country codes in
prospector-de-sites/market_scope.py are eligible for *new* discovery.
An unknown country is BLOCKED. Never infer from a local phone number,
the operator's location, language or an ambiguous city name.
Historical records outside scope remain editable without cross-country merges.

Initial preferred niches are restaurants, pizzerias/pizza shops, cafes/
coffee shops and clinics/dentistry, with country-specific service/ad rules.
Automotive detailing remains a validated design benchmark but is not the
owner's current top niche. All selected leads still require a verified strong
Maps identity, a genuine website opportunity, real services and source media.
Priority countries for initial research are US, CA, GB, IE, NL, DE, CH,
AT, DK, SE, NO, FR, ES and PT. Other European countries are in scope,
but require language and jurisdiction-specific review.

## Do not collapse separate permissions

Geographic scope, commercial opportunity score, build/media readiness,
verified contact coordinates, legal outreach permission, and authorized
recipient-requested callback are **different dimensions**.
The advisory score in market_scope.py cannot authorize contact or dialing.
Contact information alone cannot authorize AI calling.

## Browser/Remote Desktop media discovery

1. Confirm business identity, map listing and independently sourced country.
2. Verify the official domain: Wix, Google Sites, Squarespace, WordPress
   etc are official websites when confirmed; a social profile is not.
3. For redesign, browse appropriate same-domain About, Services, Team,
   Gallery, Location, and Contact pages, depth 2–3, not only homepage.
4. Open official social accounts in a browser through Remote Desktop
   Commander. Verify ownership by cross-link/identity and record source URL,
   observation time, business identity and confidence.
5. Enumerate authentic logos, staff, service/process photos, facility media,
   product photos, and videos. Keep the original media URLs and source pages.
6. Verify media rights separately. Public availability, business ownership
   assumptions and identity evidence do not automatically grant commercial
   rehosting. Confirm explicit reuse permission before copying assets into
   a site; use authorized embeds where applicable. Google Maps photos
   are research-only without separate rights.
7. A social profile with unverified identity stays an inert/non-clickable
   affordance. Do not invent handles, claims, reviewers, professionals or
   patient/client imagery.
8. Prefer authentic permitted assets in the hero and gallery. When rights
   are missing, preserve only research references or use honestly labeled
   licensed contextual images. Do not ship unauthorized copied social media.

Research handoff CLI (local, read-only, no scraping):

    python prospector-de-sites/automation/site_research.py plan --lead-json .prospector/lead-source.json --output .prospector/site-research-plan.json
    python prospector-de-sites/automation/site_research.py audit --manifest .prospector/site-research-plan.json

The planner starts as REVIEW_REQUIRED with unverified social identities and
no asset rights. The PUBLIC site asset audit rejects attempted publication
of images with unverified reuse rights. A separate access-protected,
recipient-only owner preview path can use source-verified brand photos
without up-front license checks, provided the photos never enter public
site assets and a real independent host access/noindex probe is verified.
See docs/cms-owner-preview-and-priority-niches.md.
Even STRUCTURE_PASS means metadata shape/provenance references are consistent,
not that the browser, rights, or factual claims were independently verified;
readyForDesign remains false until a separate evidence-review phase approves it.
Store prospect-specific evidence under ignored .prospector/. Do not commit
customer photographs, private contact details, or source transcripts.

## Independent QA and correction contract (next stage)

Real pipeline: source facts → asset ownership/rights → three divergent
design concepts → independent design judge → implementation → rendered
desktop/mobile browser checks → adversarial factual/conversion re-check
→ final human Preview approval.

Review reports must tie observations to exact source hashes and screenshots.
A correction invalidates affected previous PASS findings. Each stage gets at
most two targeted automated correction rounds; repeated failures stop for
human inspection. Missing browser access, design judge, verified sources or
rights evidence prevents advancement; agent-authored text cannot itself prove
PASS. Existing deterministic npm site-review is not complete browser QA.
Preview publication, CRM promotion, production release and customer outreach
require separate authorization.

## Daniel callbacks: manual admin release only

Initial owner policy: ALL global callback enable/release controls default OFF,
no scheduled batch dispatch, no unattended grants or autonomous feature
activation. Production schema readiness only establishes database availability.

- TELNYX_CALLBACKS_ENABLED and TELNYX_CALLBACKS_LEGAL_RELEASED stay disabled
  until authenticated administrator release, provider validation and
  applicable market/jurisdiction review.
- The existing per-lead CRM ON/OFF is an extra prerequisite, not consent.
- Each callback must be independently requested by that recipient, with
  recent authenticated evidence, exact destination, admin attestation,
  suppressions/quiet-hours checks, one-shot reservation, revocation and audit.
- Future global toggle UI must be restricted to authenticated admins,
  separately audited, revoke-able, fail-closed and independent of each
  recipient's grant. A toggle cannot override regional legal gates.
- Brazil-only owner-test telephony does not establish US/CA/Europe readiness.

An admin-facing global callback toggle remains an implementation requirement;
it is not currently a verified live UI. Until the separate feature is built,
leave server-side callback dispatch and legal-release flags disabled.

## Offline regression

    python test_market_scope_and_site_research.py
    python test_site_automation_pilot.py
    python prospector-de-sites/prospector-mcp.py --teste

These tests use synthetic leads, local SQLite or local JSON and never send,
call, scrape social networks, or write to live Supabase.
