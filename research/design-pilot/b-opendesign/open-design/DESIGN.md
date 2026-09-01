# Design System & Visual Specification: Ateliê Clínico Editorial
**Business**: Clínica Odontológica Dra. Francine Goulart  
**Slug**: `clinica-dra-francine-goulart-rio-claro`  
**Selection**: Direction 1 (Critiqued & Approved via `gpt-taste`)  
**Status**: Authoritative visual contract for production candidate

---

## 1. Anti-House-Style Audit Record
- `OPEN_DESIGN_HOUSE_STYLE_CHECK`: PASS
- **Business Specific Decisions**:
  - Direct individual clinical practice established in 2019 by Dra. Francine Aparecida Goulart (CRO SP-CD-104303) in downtown Rio Claro (Avenida 7, nº 310).
  - Continuous card-free clinical procedure directory structured around real preventive, restorative, and periodontal scope, replacing generic SaaS card boxes.
  - Absence of artificial process numbering (`01/02/03/04` removed per repository rules against decorative ordering).
  - Explicit verified Google proof plate (4.2 stars, 5 direct Maps verified reviews, including verbatim quotes from Luis and Maria José Leite, and 3 star-only entries).
- **Rejected OpenDesign / Template Defaults**:
  - Rejected default dark SaaS background with floating cards.
  - Rejected 3-card feature rows with drop-shadows.
  - Rejected decorative tags, pills, chips, and artificial stats strips.
  - Rejected generic gradient glow or glassmorphism.
- **Why Typography & Composition Fit this Prospect**:
  - Newsreader serif display delivers calm medical authority, dignity, and individualized patient focus, perfectly matching a private solo practice in a historic interior São Paulo city center.
  - Plus Jakarta Sans provides crisp technical contrast for clinical specifications and contact affordances.
- **Anti-Generalization Rule**:
  - Do NOT generalize "ivory + editorial serif + medical publication" as the default dental/health aesthetic. It was chosen here because this prospect is an individualized solo practice where clinical intimacy, craftsmanship, and downtown trust take precedence over high-volume orthodontic tech imagery.

---

## 2. Design Tokens
- **Canvas / Background**: `#fafaf9` (Warm Ivory / Linho Clínico)
- **Surface / Contrast Section**: `#f4f4f2` (Porcelana Neutra)
- **Primary Deep / Headings**: `#132a24` (Verde Floresta Cirúrgico Profundo)
- **Body Text**: `#292524` (Ardósia Quente Escura)
- **Muted Text / Notes**: `#78716c` (Stone Médio)
- **Accent Action**: `#1e473d` (Sálvia Cirúrgico Profundo)
- **Accent Hover**: `#14352d`
- **Hairline Dividers**: `#e7e5e4` (Linha divisória sutil 1px)
- **Contrast Proof Plate**: `#132a24` (Fundo sólido para destaque de avaliações verificadas)

---

## 3. Typography Stack
- **Display Headings (H1, H2, H3)**: `'Newsreader', serif` (pesos 400, 500, 600)
  - Proporção H1: `clamp(2.4rem, 4.2vw, 3.6rem)` com entrelinha estrita `1.15` e largura máxima controlada para 2 linhas no desktop.
- **Body & Technical Copy**: `'Plus Jakarta Sans', system-ui, sans-serif` (pesos 400, 500, 600)
  - Corpo regular `1rem`, entrelinha `1.65`.

---

## 4. Spacing & Rhythm
- Seções com espaçamento editorial generoso: `padding: 96px 0` no desktop, `56px 0` no mobile.
- Alinhamento em grade de 12 colunas com gutter de `32px`.
- Container central: `max-width: 1180px`.

---

## 5. Hero Architecture
- Full-bleed background layout mode (`data-hero-layout="full-bleed-background"`) with `data-hero-frame-policy="preserve-complete-frame"`.
- Dedicated responsive `<picture>` wrapper with desktop ultrawide (`dentistry-female.webp`, 1983x793) and mobile (`dentistry-female-mobile.webp`, 941x1672).
- Single high-contrast CTA button: "Agendar avaliação no WhatsApp".

---

## 6. Treatment Directory Grammar (Zero Cards, Zero Decorative Numbers)
- Substituição total de cards por linhas divisórias horizontais (`border-top: 1px solid var(--hairline)`).
- Sem numeração artificial (`01`, `02`, etc.), apoiado puramente no nome do tratamento e tipografia serifada.
- Links diretos com destinação para o WhatsApp verificado com mensagem contextual.

---

## 7. Google Reviews Presentation
- Seção verificada `data-role="reviews"` com `data-review-mode="verified-text"`, `data-review-rating="4.2"`, `data-review-count="5"`.
- Carrossel com 5 slides vinculados estritamente às evidências observadas com `nativeReviewId`.
- 2 itens com texto completo e citação fidedigna (Luis, Maria José Leite).
- 3 itens com avaliação de estrelas e menção neutra ("Avaliação sem comentário").
- Sem aspas fabricadas, sem "Paciente Verificado #1", sem marca Google em copy pública.

---

## 8. Anti-Slop & Core Rules Compliance
- Zero decorative tags/pills/badges.
- Zero emojis in public UI.
- Zero em dashes (`—`) or en dashes (`–`) in public text.
- Full PT-BR sentence case.
- Floating WhatsApp synchronized: appears only after hero CTA leaves viewport.
- No competing assistant launcher.
- Responsive Google Maps embed for Avenida 7, nº 310, Centro, Rio Claro - SP.
