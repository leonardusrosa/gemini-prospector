# Design Read — Variant A (Baseline without OpenDesign)
**Lead**: Clínica Odontológica Dra. Francine Goulart  
**Slug**: `clinica-dra-francine-goulart-rio-claro`  
**Variant**: A (Baseline: Prospector Rules + gpt-taste + redesign-premium)  
**Status**: Frozen before OpenDesign generation

---

## 1. Design Thesis
- **Thesis**: Clean clinical editorial elegance. A structured, trustworthy dental practice interface anchored on medical rigor, patient comfort, and clear downtown Rio Claro accessibility.
- **Tone**: Warm clinical precision, restrained palette, zero ornamental AI clutter.
- **Typography Stack**: Outfit (headings) + Plus Jakarta Sans (body). Clean modern geometric sans with exceptional legibility.

## 2. Simulated gpt-taste Pre-flight & Randomization
- **Seed**: Len("Clínica Odontológica Dra. Francine Goulart") = 42
- **Hero Architecture**: Cinematic Center with directional contrast overlay and ultrawide template asset.
- **Typography**: Outfit + Plus Jakarta Sans.
- **Component Architectures**: Gapless Bento for clinical services, Editorial Aggregate Block for Google proof, Split Contact and Map grid.
- **Motion Paradigms**: Staggered hero entrance, IntersectionObserver scroll reveals, synchronized floating WhatsApp.

## 3. Hero Visual Contract
- **Source**: Canonical Template (`dentistry-female`)
- **Desktop Ultrawide**: `../assets/desktop-ultrawide.webp` (1983x793)
- **Mobile**: `../assets/mobile.webp` (941x1672)
- **Tag Context**: `data-image-context="illustrative"`
- **Alt**: "Imagem ilustrativa de consultório odontológico com espaço reservado para foto profissional"
- **CTA Count**: Exactly ONE button ("Agendar avaliação").
- **H1 Container**: max-w-4xl, strictly 2 lines on desktop viewport ("Cuidado odontológico completo com atenção dedicada ao seu bem-estar").

## 4. Factual Verification & Social Proof
- **Responsible**: Dra. Francine Aparecida Goulart (CRO SP-CD-104303)
- **Clinic Address**: Avenida 7, nº 310, Centro, Rio Claro - SP
- **Phone / WhatsApp**: (19) 98849-4898 / `https://wa.me/5519988494898`
- **Google Reviews State**: `VERIFIED_AGGREGATE_ONLY` (4.8 estrelas, 28 avaliações públicas)
- **Presentation**: Editorial aggregate badge with verified star rating and total count, without fabricated patient cards or fake quotes.

## 5. Anti-Slop & Core Rules Compliance
- Zero decorative badges/pills/chips.
- Zero emojis in public UI.
- Zero em dashes (`—`) or en dashes (`–`) in public text.
- Full PT-BR sentence case.
- Floating WhatsApp synchronized: appears only after hero CTA leaves viewport.
- No competing assistant launcher.
- Responsive Google Maps embed for Avenida 7, nº 310, Centro, Rio Claro - SP.
