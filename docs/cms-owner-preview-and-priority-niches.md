# Prospector — priority niches, private owner previews and required Client CMS

Status: isolated feature branch. Depends on market scope PR #4 and Engine C review
controller PR #5. No production deployment, CRM write, outreach, image scraping,
CMS provisioning or client credentials are created by this change.

## Owner's niche preference

New lead sourcing remains limited to the USA, Canada and European markets.
The initial commercially preferred verticals, without excluding other
qualified local businesses, are:

1. Pizzerias / pizza restaurants (local hero, real dishes, menu, ordering CTA).
2. Independent cafes / coffee shops (venue atmosphere, signature products,
   menu/hours and location).
3. Independent restaurants (menu, experience, reservations, opening hours).
4. Dental practices / dentistry (source-verified services, practitioners,
   appointments, healthcare marketing review).
5. Other local clinics (legitimate credentials, appointments and localized
   medical-claim/patient-data review).

This is a **priority classification**, not a contact permission, marketing
approval, automatic niche exclusion or unsupported promise of outcomes.
The classifier is multilingual across the supported markets, and a clinical
priority adds an explicit regulated-claims review requirement. Site visuals
and factual copy must adapt to each individual business, not clone a
generic niche template.

## Current canonical Client CMS — verified from Dashboard source

Canonical implementation repository: leonardusrosa/prospector-dashboard.

- Product rules: docs/client-cms-framework.md
- Admin shell: public/client-admin-template.html
- Visual editor: src/lib/editor-layer.ts
- Auth/session/API: src/app/api/client-cms/[...path]/route.ts
- Persistence/drafts/publish/rollback: src/lib/cms-store.ts and Supabase CMS RPC
- Tenant provisioning: Supabase Edge Function cms-operator and CRM CMS operator
  interface.
- Admin tenant URL: /clientes/{slug}/admin/
- Published CMS page endpoint: /clientes/{slug}/site/

The editor is **HTML round-trip oriented**:
- The authenticated shell creates one persistent toolbar and embeds the
  underlying site HTML in an iframe. It injects editor controls dynamically.
- Clients can edit headings, paragraphs, button/link destinations,
  image sources and photo alt text, including content references and
  synchronized business-contact channels when supported by the markup.
- Preview of unsaved changes, draft save, publish, rollback, export, password
  recovery and sign-out are part of the established client UI.
- On publish, the editor strips its own UI and transient contenteditable
  state before persisting complete sanitized HTML.
- A generated site MUST NOT contain another permanent CMS toolbar.
- Site locale and CMS chrome locale derive from the lead's canonical
  locale/tenant provisioning. Current documented UI packs are pt-BR and en-US,
  so new language packs need browser QA before French, German, Spanish,
  Italian, Dutch etc customer handoff.

### Mandatory stack and delivery interpretation

**Default website implementation is static HTML + CSS + JS.**
This matches the existing CMS's persist-entire-HTML model.
React/Next.js hydration is not banned globally, but a new site relying on
a hydrated runtime fails the conservative structural gate unless a separate,
demonstrably equivalent CMS bridge and true E2E have been implemented.

Every delivered site must have a provisioned Client CMS tenant and must
pass an authenticated, end-to-end:
login -> edit heading/image/link -> preview unsaved state -> save draft ->
publish -> verify public HTML -> rollback -> verify restored version.
A static index.html by itself is **not** a delivered admin panel.
The CMS structure validator is necessary but not that live proof.
CMS credentials are only provisioned via the existing secured operator flow,
not embedded into generated pages, Git or source artifacts.

**Out-of-scope today without a CMS product extension:** structured CRUD for
adding/removing restaurant menu items, product variants, galleries, staff,
or booking services as distinct entities. The current visual editor can
change existing rendered text/images/links; expanding schema-driven
collections is a separate product feature.

### Automated review stage

The Engine C pipeline now has EIGHT review stages:
facts -> media -> A/B/C candidate generation -> independent selection ->
implementation -> CLIENT_CMS_COMPATIBILITY -> real browser QA ->
factual/conversion re-check. Only after all stages may a final Preview be
shown to the owner for approval.

The new offline CMS gate checks real generated HTML bytes and SHA, HTML5
structure, language, semantic text, actionable links, editor contamination,
duplicate ids and likely Next hydration hazards.
It does not certify tenant provisioning or authenticated CMS functionality.
The QA controller permanently exposes readyForClientHandoff=false;
a separate delivery gate must explicitly verify the actual tenant/runtime.

## Using actual business photos without permission checks for private previews

Owner preference: do NOT require individual image reuse-license validation
before designing an **access-protected preview for that business owner**.

The private-preview path therefore permits source-confirmed, business-linked
website/Instagram/Facebook images with rightsStatus=UNCONFIRMED, on condition
that:
- The business and official profile identity/source URL are verified to
  avoid using another business's photos. The preview is factually accurate.
- The files remain in an ignored isolated .prospector workspace, outside
  the public site's assets directory. The media manifest retains original
  source/page references and marks useInProtectedOwnerPreview.
- Preview access is restricted to that intended business owner, not
  anonymous/public, and noindex headers are verified through independent
  HTTP/browser checks.
- The private owner preview is for review, not a representation that the
  image reuse rights are cleared. A visible social photograph may belong to
  a photographer, employee, third party or platform rights holder.
- No automatic publication, public search indexing or unauthorized broad
  redistribution. For a final publicly accessible site, clear any needed
  rights or replace unconfirmed media; patient imagery also needs appropriate
  privacy/consent validation.
- The agent must not conflate the preview provenance gate with a copyright
  license or treat a JSON boolean as proof that authentication is enforced.
  Actual host access must be independently tested before exposure.

The pipeline accepts a properly scoped private media stage without checking
licensing, but blocks proceeding through the browser stage without separate
access-protection evidence. The public-site asset audit remains strict.

## Acceptance commands

    python test_cms_compatibility_and_owner_preview.py
    python test_market_scope_and_site_research.py
    python test_site_review_rounds.py
    python test_engine_c_bridge.py

Manual/runtime checks still required:
- Browser: CMS login/edit/photo/CTA/preview/draft/publish/rollback, with
  tenant locale and responsive layouts.
- Protected Preview: unauthenticated request denied, owner-specific
  access, noindex headers, no public image mirroring.
- Engine C: independent visual evaluation and live responsive screenshots.

No production flags or external publishing endpoints are enabled by tests.


## Editable collections for the chosen niches (dashboard PR #40)

The product owner confirmed clients should be able to add/remove/reorder
repeatable cards **if easily achievable**. The dashboard implements this
as an opt-in, no-migration static HTML Client CMS extension, merged and
deployed on the primary CRM (`8deeff0`):
https://github.com/leonardusrosa/prospector-dashboard/pull/40

For new websites based on verified sources, the generator must annotate
`data-pe-collection` containers and direct `data-pe-item`
children for restaurant/cafe menu highlights, gallery photos, verified
clinic services and staff where applicable. The existing visual editor
continues to edit individual text, image, pricing and CTA content.

Do not invent empty menu products, doctors, prices or gallery images just
to enable the controls. Avoid hydrating these static lists from React
because it may overwrite client edits in the CMS HTML roundtrip.
The new browser QA should test add/edit/move/remove/reopen as well as the
existing authenticated draft, publish and rollback lifecycle.

This adds no structured menu/product backend. CMS version control is still
whole HTML-page versioning. Real client tenant provisioning is required.


## Engine C collection adapter

The research-to-site handoff is implemented by
`prospector-de-sites/automation/cms_collections_handoff.py`. Its
post-generation, source-hash-bound plan adds exact
`data-pe-collection` / `data-pe-item` attributes to real cards without
fabricating content or overwriting the original static HTML. The
`CLIENT_CMS_COMPATIBILITY` review stage requires the annotated output
to be bit-for-bit equal to the deterministic transformer. Tests are
in `test_engine_c_cms_collections.py`, and CI covers them.

This is an auditable adapter; production data collection, actual
image-generation execution, browser-based independent review, and
per-customer CMS tenant provisioning are separate responsibilities.
