# Design Read — Variant B (OpenDesign Direction Pass)
**Lead**: Clínica Odontológica Dra. Francine Goulart  
**Slug**: `clinica-dra-francine-goulart-rio-claro`  
**Variant**: B (Experimental: OpenDesign MCP Direction + gpt-taste Critique + Prospector Implementation)  
**Status**: Authoritative implementation artifact for Pilot 1

---

## 1. OpenDesign Direction Contract (Schema v2)
- `OPEN_DESIGN_DIRECTION`: PASS
- `OPEN_DESIGN_MCP`: open-design
- `OPEN_DESIGN_MCP_PROBE`: PASS
- `OPEN_DESIGN_DIRECTIONS_GENERATED`: 2
- `OPEN_DESIGN_SELECTED_DIRECTION`: Ateliê Clínico Editorial
- `OPEN_DESIGN_DESIGN_MD`: open-design/DESIGN.md
- `OPEN_DESIGN_IMPLEMENTATION_ROLE`: DIRECTION_ONLY
- `OPEN_DESIGN_GPT_TASTE_REVIEW`: PASS

## 2. Design Thesis & Architectural Rationale
- **Thesis**: An authoritative, warm ivory editorial layout ("Ateliê Clínico Editorial") that dispenses completely with generic SaaS dark backgrounds, floating cards, and artificial elevation shadows.
- **Visual Distinction**:
  - Warm linen/porcelain background (`#fafaf9`) rather than deep naval blue.
  - High-dignity medical serif typography (`Newsreader`) paired with clean geometric sans (`Plus Jakarta Sans`).
  - Treatment Directory: Continuous horizontal rule structure with clean clinical paragraphs and contextual WhatsApp action links (100% card-free).
  - Editorial Google Reviews Plate: Deep forest slate block with verified 4.8 aggregate and 28 public reviews.
  - Asymmetric Hero: Left-aligned ultra-wide editorial heading with architectural framing for the dentist template asset.

## 3. Hero Visual Contract
- **Source**: Canonical Template (`dentistry-female`)
- **Desktop Ultrawide**: `../assets/desktop-ultrawide.webp` (1983x793)
- **Mobile**: `../assets/mobile.webp` (941x1672)
- **Tag Context**: `data-image-context="illustrative"`
- **Alt**: "Imagem ilustrativa de consultório odontológico com espaço reservado para foto profissional"
- **CTA Count**: Exactly ONE button ("Solicitar horário de avaliação").

## 4. Factual Parity (100% Equal to Variant A)
- **Responsible**: Dra. Francine Aparecida Goulart (CRO SP-CD-104303)
- **Clinic Address**: Avenida 7, nº 310, Centro, Rio Claro - SP
- **Phone / WhatsApp**: (19) 98849-4898 / `https://wa.me/5519988494898`
- **Google Reviews State**: `VERIFIED_AGGREGATE_ONLY` (4.8 estrelas, 28 avaliações públicas)
- **Conversion Destination**: Identical WhatsApp pre-filled greeting.

## 5. Anti-Slop & Core Rules Compliance
- Zero decorative tags/pills/chips.
- Zero emojis in public UI.
- Zero em dashes (`—`) or en dashes (`–`) in public text.
- Full PT-BR sentence case.
- Floating WhatsApp synchronized: appears only after hero CTA leaves viewport.
- No competing assistant launcher.
- Responsive Google Maps embed for Avenida 7, nº 310, Centro, Rio Claro - SP.
