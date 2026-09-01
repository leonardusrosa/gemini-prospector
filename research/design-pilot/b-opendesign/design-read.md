# Design Read — Clínica Odontológica Dra. Francine Goulart

## 1. Business Context & Factual Constraints
- **Business**: Clínica Odontológica Dra. Francine Goulart
- **Legal Entity**: Clínica Odontológica Dra. Francine Aparecida Goulart Ltda (CNPJ: 33.339.590/0001-30, fundação: 2019)
- **Responsible Expert**: Dra. Francine Aparecida Goulart (CRO SP-CD-104303)
- **Niche**: Odontologia Clínica Geral e Diagnóstico Preventivo
- **City**: Rio Claro - SP
- **Address**: Avenida 7, nº 310, Centro, Rio Claro - SP, CEP 13500-143
- **Phone / WhatsApp**: (19) 98849-4898 / 5519988494898 (verified primary channel)
- **Factual Verified Services**: Avaliação e Prevenção, Restaurações Estéticas, Profilaxia Profissional, Conservação e Alívio de Dor

## 2. GPT-Taste Creative Direction & Pre-flight
GPT_TASTE_READ: PASS
GPT_TASTE_PATH: C:\Users\leo_b\.gemini\config\skills\gpt-taste\SKILL.md
GPT_TASTE_SHA256: 6a19b70e6b53761d5788f284c615bf93a07cd9f94d5f0a452520260d9d951523
Design Variance: 5
Motion: 3
Density: 4

## 3. OpenDesign Direction Contract (Schema v2)
OPEN_DESIGN_DIRECTION: PASS
OPEN_DESIGN_MCP: open-design
OPEN_DESIGN_MCP_PROBE: PASS
OPEN_DESIGN_DIRECTIONS_GENERATED: 2
OPEN_DESIGN_SELECTED_DIRECTION: Ateliê Clínico Editorial
OPEN_DESIGN_DESIGN_MD: open-design/DESIGN.md
OPEN_DESIGN_IMPLEMENTATION_ROLE: DIRECTION_ONLY
OPEN_DESIGN_GPT_TASTE_REVIEW: PASS
OPEN_DESIGN_HOUSE_STYLE_CHECK: PASS

- **Anti-House-Style Audit**:
  - Selected direction ("Ateliê Clínico Editorial") is strictly justified by the solo clinical practice profile of Dra. Francine Goulart in downtown Rio Claro.
  - Rejected generic dark SaaS templates, drop-shadow cards, and arbitrary gradients.
  - Removed decorative numbering (`01/02/03/04`) per repository policy against decorative ordering.
  - Explicit rule: Do NOT generalize "ivory + editorial serif + medical publication" as the default dental/health aesthetic.

## 4. Hero Architecture & Template Visual
HERO_VISUAL_SOURCE: canonical-template
HERO_TEMPLATE_ID: dentistry-female
HERO_LAYOUT_MODE: full-bleed-background
HERO_TEMPLATE_DESKTOP: assets/templates/dentistry-female.webp
HERO_TEMPLATE_MOBILE: assets/templates/dentistry-female-mobile.webp
HERO_REPRESENTS_ACTUAL_EXPERT: false
HERO_REPRESENTS_ACTUAL_BUSINESS: false

- **Hero Attributes**: `data-role="hero"`, `data-hero-layout="full-bleed-background"`, `data-hero-frame-policy="preserve-complete-frame"`.
- **H1 Container**: max-w-3xl ensuring H1 strictly flows in 2 lines on desktop.
- **Hero CTA**: Exactly ONE button ("Agendar avaliação no WhatsApp") linking directly to verified WhatsApp 5519988494898.

## 5. Google Reviews Evidence & Presentation
GOOGLE_REVIEWS_CHECK: PASS
SECONDARY_REVIEW_SEARCH: PASS
SECONDARY_SOURCES_CHECKED: Doctoralia, Guia da Cidade Rio Claro, Serasa
VERIFIED_TEXT_REVIEWS_FOUND: 2
GOOGLE_REVIEWS_STATE: VERIFIED_TEXT_LIMITED
GOOGLE_AGGREGATE_RATING: 4.2
GOOGLE_RATING_COUNT: 5
GOOGLE_OBSERVED_RATING_ENTRIES: 5
GOOGLE_OBSERVED_TEXT_ENTRIES: 2
GOOGLE_CAPTURED_TEXT_COUNT: 2
GOOGLE_STAR_ONLY_COUNT: 3
PANEL_FULLY_TRAVERSED: YES

- **Direct Maps Evidence**:
  - Exact profile: `Dentista Dra. Francine Goulart` (Place ID: `0x94c7da5a58a30833:0x1f93843856f80228`).
  - Observed aggregate rating 4.2 from 5 verified ratings.
  - Complete panel traversal completed (5 of 5 entries captured).
  - 2 verified textual reviews: Luis (5 estrelas, "Foi muito bom excelente dentista eu recomendo") and Maria José Leite (5 estrelas, "Muuto eficiente e atenciosa.").
  - 3 star-only ratings: DELMA LOPES MATOS (5 estrelas), isabelly polido (1 estrela), Yasmin Breda (5 estrelas).
  - Review section rendered with verified aggregate (4,2 de nota média em 5 avaliações públicas) and evidence-bound carousel presenting all 5 source-backed items. Zero fabricated quotes or synthetic reviewer identities.

## 6. Motion & Reveal Behavior
- Header transitions on scroll (`data-role="site-header"`).
- Section reveals with `data-motion="reveal"`.
- Full `prefers-reduced-motion: reduce` handling in CSS.
- No-JS accessibility: content fully readable if script execution is disabled.

## 7. Floating WhatsApp Synchronization
- Assistant launcher: Absent (`present: false`).
- Floating WhatsApp (`data-role="floating-whatsapp"`): Appears only after hero CTA leaves viewport.
- No competing fixed bottom controls.

## 8. Google Maps Embed
- Verified address: Avenida 7, nº 310, Centro, Rio Claro - SP, CEP 13500-143.
- Responsive iframe with `loading="lazy"`, `title="Localização da Clínica Odontológica Dra. Francine Goulart em Rio Claro"`, `referrerpolicy="no-referrer-when-downgrade"`.
