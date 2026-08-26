# First-Party Source Tree Crawl

Use this reference whenever `siteMode = redesign` and an official website exists.

## Principle

The official website is a **source tree**, not a single homepage.

A weak homepage does not imply weak source material. Before designing, inspect relevant same-domain internal pages for factual content, authentic imagery, service hierarchy and business identity.

Do not start the final Design Read from homepage-only evidence when useful first-party subpages are discoverable.

## Required crawl flow

```text
official domain confirmed
→ homepage
→ collect same-domain navigation/internal links
→ prioritize high-value pages
→ crawl relevant pages to depth ~2–3
→ extract facts + assets + source URLs
→ deduplicate
→ build factual/source manifest
→ only then finalize Design Read
```

This is a **targeted crawl**, not an indiscriminate spider of the entire domain.

## Priority page classes

Inspect these first when they exist:

1. `sobre`, `quem-somos`, `institucional`, history/mission pages
2. expert/team/body-clinical/profile pages
3. services/specialties/treatments/product/category pages
4. gallery/facilities/office/venue pages
5. contact/location/hours pages
6. testimonials/cases only for factual source review and only when clearly first-party
7. relevant editorial/blog pages when they contain evergreen factual material useful to the business presentation

For a medical/dental site, specialty pages such as `/especialidades/...` are high-value sources and must not be ignored merely because the homepage already lists the specialties.

## Scope rules

Default crawl depth: **2–3 meaningful internal hops** from homepage/navigation.

Stay on the confirmed official domain/subdomain unless a first-party page intentionally points to an official asset host/CDN.

Prefer navigation and semantic links over guessing URL patterns.

Skip or strongly deprioritize:

- privacy/terms/cookie pages
- login/admin areas
- tag/archive pagination
- duplicate print pages
- calendar pagination
- irrelevant old news
- search result pages
- third-party directories

Stop when additional pages are no longer adding material facts/assets relevant to the redesign.

## Factual extraction

For every useful claim, retain provenance:

```text
fact
source URL
source page title/section
confidence
```

Useful facts include:

- services/specialties
- expert names and roles
- credentials explicitly stated by the business
- treatment philosophy/process
- contact channels
- opening hours
- addresses
- equipment/facilities only when explicitly shown/stated
- differentiators supported by first-party evidence

Do not infer credentials, outcomes, seniority, procedure availability or claims from an image alone.

## Asset extraction

Build or update an asset manifest such as:

```text
asset
source URL
source page
category
resolution/dimensions when known
factual confidence
visual quality
possible usage
notes/restrictions
```

Recommended categories:

```text
identity/expert
team
facility
service/procedure
case/result
product
logo/brand
decorative
unknown
```

Rank assets by:

- first-party confidence
- relevance
- resolution
- visual quality
- contextual clarity
- hero suitability
- section suitability

## Treatment/case images

First-party treatment/case/result images may be inspected and used only with care.

Rules:

- preserve the original context;
- do not invent before/after relationships;
- do not create new outcome claims;
- do not imply endorsement/testimonial not present in the source;
- avoid automatically making identifiable patient/case imagery the dominant hero;
- prefer expert/facility/service imagery for broad brand sections when appropriate.

## Asset reuse vs generation

Use authentic first-party assets before generating replacements.

For `expert_fullscreen`, a strong verified expert portrait discovered on any relevant official subpage is eligible input for `expert-hero-assets`.

Generative extension may improve composition but must not replace the real identity or fabricate people/facilities/equipment.

## Research QA

Before Design Read, answer:

- Did I inspect the homepage **and** relevant internal pages?
- Did service pages add information omitted from the homepage?
- Did I discover stronger real images on subpages?
- Can every important claim be traced to a source?
- Did I accidentally treat navigation labels or image interpretation as factual claims?
- Did I stop before turning the crawl into irrelevant site-wide scraping?

If the answer to the first question is no for an existing official website with discoverable internal pages, the research pass is incomplete.
