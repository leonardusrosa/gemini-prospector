# Engine C -> AutoCORA Client CMS: verified repeatable collections

**Status:** executable offline integration, source- and hash-bound; not a live
site generator, social scraper, CMS tenant provisioner, or publication agent.
AutoCORA's Client CMS card editing is live in `prospector-dashboard` main
(commit `8deeff0`), with full authenticated Chromium/real Supabase staging
coverage completed separately. New sites require a real CMS tenant and
deployment/runtime test before client delivery.

## Handoff architecture

Research first: establish the actual business's identity, country, verified
official site/social accounts, real offerings/menu/prices/staff, and source
evidence. The initial immutable research manifest contains the lead's niche
and the requirement for editable collections. Never amend this manifest
mid-run to insert future generated HTML hashes.

Generation next: Engine C generates and visually evaluates A/B/C and
implements the selected static HTML/CSS/JS site. Its real business sections
must have stable unique IDs on each collection container and direct child.
The new CMS annotation step runs **after** static HTML generation and
**before** the Client CMS compatibility/reviewer gate. Its separate
collection plan is bound both to the immutable source research SHA and
the exact unannotated HTML SHA. This prevents invented, stale or extra
cards from silently becoming editable.

The annotation tool modifies **attributes only** and outputs a new HTML
file, preserving existing contents, design, CSS/JS and CTA behavior.
It never fabricates services, menu items, prices, contact details or photos.

### Required input documents

1. Existing immutable research manifest (schema v1, `noOutbound=true`);
   `assessment.priorityNiche` is `restaurant`, `pizzeria`, `cafe`,
   `dentistry` or `clinic`.
2. Unannotated generated HTML file, **read-only original**.
3. New, separate `cms-collection-plan.json` (not an edit to the research
   manifest), including:
   - `schemaVersion=1`, the exact `leadSlug`, `country`,
     `noOutbound=true`, and matching `assessment` (scope ALLOW and
     priority niche, plus clinical review flag where applicable);
   - `sourceManifestSha256` of the frozen original research manifest;
   - `cmsSourceHtmlSha256` of the unannotated site;
   - `cmsCollections`: array of source-reviewed sections, each with
     `kind`, `containerId`, `itemIds`, `sourcePage` (HTTPS), and
     `sourceEvidence.path` + `sourceEvidence.sha256` for the actual
     browser/first-party evidence file; clinical groups also need an
     explicitly independently reviewed claims record.
4. New output file path in an isolated worktree, never overwriting
   original site HTML.

Example, **fictional** restaurant design and dummy paths only:

```html
<div id="menu-grid" class="menu-grid">
  <article id="menu-pizza-one" class="menu-card">
    <h3>Fictional Example Pizza</h3>
    <p>$12 (fictional)</p>
  </article>
</div>
```

```json
{
  "schemaVersion": 1,
  "leadSlug": "fictional-pizzeria-qa",
  "country": "US",
  "noOutbound": true,
  "assessment": {"scope": "ALLOW", "priorityNiche": "pizzeria"},
  "sourceManifestSha256": "<real sha256 of frozen research manifest>",
  "cmsSourceHtmlSha256": "<real sha256 of original Engine C HTML>",
  "cmsCollections": [{
    "kind": "menu",
    "containerId": "menu-grid",
    "itemIds": ["menu-pizza-one"],
    "sourcePage": "https://example.org/fictional-menu",
    "sourceEvidence": {
      "path": ".prospector/pilot/menu-source-review.txt",
      "sha256": "<real sha256 of source-review file>"
    }
  }]
}
```

This example is a **schema illustration, not source verification**.

Run from the canonical `gemini-prospector` repo root:

```bash
python prospector-de-sites/automation/cms_collections_handoff.py \
  --html .prospector/pilot/site/index.html \
  --research .prospector/pilot/cms-collection-plan.json \
  --output .prospector/pilot/site/cms-ready.html
python prospector-de-sites/automation/cms_compatibility.py \
  --html .prospector/pilot/site/cms-ready.html
```

Result: `data-pe-collection="menu"` on the container,
`data-pe-item` on each reviewed direct child, and a SHA-bound report.
Existing template structure is retained. There is no extra persistent
client editor UI in the public HTML.

## Strict acceptance rules

- For restaurants/pizzerias/cafes, at least one source-reviewed
  `menu` or `services` section must exist. For clinics/dentistry, a
  `services` section and clinical-claims review are mandatory.
- Additional `gallery`, `team` and `pricing` collections are
  allowed **only** when those facts/images are already verified. Omit
  unverified content, never fabricate it to satisfy the editor.
- Every collection must have 1–40 matching **actual direct children**.
  IDs must be unique; no unplanned children or unsupported markers.
- Per-item business-global `data-pe-field` sync attributes are refused.
- Evidence paths must exist, with matching SHA; HTTPS source-page
  references alone do not prove that the page was inspected.
- Generated HTML must pass the existing Client CMS structural audit.
  Nested React/hydrated runtime, stale source hashes, unsupported HTML
  and embedded editor UI are rejected. The output cannot overwrite source.
- The Client CMS QA stage verifies the annotation plan SHA, original
  Engine C HTML SHA, frozen research manifest SHA, lead/country/niche
  identity, exact deterministic generated markup and final HTML SHA.
  Stage requires **independent reviewer PASS**, not just a local
  validator result.
- No automatically provisioned CMS account, preview publishing,
  outbound calls, or site deployment. All contact flags remain OFF.

## End-to-end status and next executor boundary

The Client CMS editor itself is deployed and production-smoke-checked,
including unauthorized API 401 handling. Its staging tests have
separately exercised actual hosted Vercel/real Supabase publishing and
rollback with a disposable fictional restaurant and verified cleanup.

The new adapter connects Engine C HTML artifacts to CMS-compatible
repeatable markup and the independent QA state machine. **It does
not connect an autonomous browser/image generator/coder to every real
prospect yet.** That still requires a real source-observing browser agent,
independent design critique, implementation worker, protected Preview
access probe, and a real tenant auth/edit/publish/rollback smoke before
customer handoff.

## Regression tests

```bash
python test_engine_c_cms_collections.py
python test_cms_compatibility_and_owner_preview.py
python test_site_review_rounds.py
```

No test fixtures are real restaurant, clinic or patient information.
