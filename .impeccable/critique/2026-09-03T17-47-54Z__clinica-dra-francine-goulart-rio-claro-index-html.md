---
timestamp: 2026-09-03T17-47-54Z
slug: clinica-dra-francine-goulart-rio-claro-index-html
---
# Design Critique: Clínica Odontológica Dra. Francine Goulart

**Target**: `sites/clinica-dra-francine-goulart-rio-claro/index.html`  
**Evaluation Mode**: Impeccable Design Review & Heuristic Audit  
**Date**: 2026-09-03  

---

### Design Health Score

| # | Heuristic | Score | Key Issue |
|---|-----------|-------|-----------|
| 1 | Visibility of System Status | 3/4 | Carousel counter & header scroll active, but directory rows lack expanded state feedback |
| 2 | Match System / Real World | 4/4 | Flawless domain terminology, natural sentence case PT-BR, CRO/CNPJ transparency |
| 3 | User Control and Freedom | 3/4 | Prev/next carousel buttons present; lacks mobile touch-swipe gesture support |
| 4 | Consistency and Standards | 4/4 | Cohesive typography scale (Newsreader + Outfit), uniform button grammar & spacing |
| 5 | Error Prevention | 4/4 | Pre-filled WhatsApp URLs prevent empty messages; zero broken or dead destinations |
| 6 | Recognition Rather Than Recall | 3/4 | Clear service naming and map embed; consultation details could be more explicit |
| 7 | Flexibility and Efficiency | 3/4 | Quick anchor navigation; keyboard focus indicators could be more prominent |
| 8 | Aesthetic and Minimalist Design | 3/4 | Refined editorial tone, but repeated kickers and 2px side-stripe border are AI tells |
| 9 | Error Recovery | 4/4 | Pure static HTML/CSS resilience; 100% readable if JavaScript is unavailable |
| 10 | Help and Documentation | 3/4 | Complete legal credentials; could add preparatory guidance for first consultation |
| **Total** | | **34/40** | **Strong (Production-Grade)** |

---

### Anti-Patterns Verdict

#### Automated Detection Scan
Ran `npx impeccable detect --json sites/clinica-dra-francine-goulart-rio-claro/index.html`:
- `repeated-section-kickers` (3 instances): Flagged repeating uppercase tracked kickers ("Pilares do atendimento", "Especialidades e tratamentos", "Atendimento presencial").
- `dark-glow` (1 instance): Flagged colored glow (`rgb(37,211,102)`) on the floating WhatsApp button box-shadow.
- `overused-font` (1 instance): Flagged `Plus Jakarta Sans` lingering in the font-family fallback stack and font link.

#### LLM Design Review & Slop Assessment
- **Side-Stripe Borders (Rule Violation)**: `.loc-block` in the location section uses `border-left: 2px solid var(--accent-sage)`. Impeccable shared design laws explicitly forbid colored side-stripe borders greater than 1px as accents.
- **Kicker Monotony**: Every section mechanically opens with `eyebrow + H2`. Breaking this pattern by dropping eyebrows where the H2 is self-explanatory creates a much more confident, human editorial rhythm.
- **Glow Removal**: The saturated neon glow on the floating WhatsApp button should be replaced with a neutral, physical elevation shadow (`rgba(0, 0, 0, 0.18)`).
- **Hero Typographic Win**: The 2-Line Iron Rule is strictly satisfied on desktop (`max-w: 880px` with `clamp(2.05rem, 3.1vw, 2.85rem)`), eliminating awkward hyphenation.

---

### Priority Issues

#### [P1] Ban Violation: Colored Side-Stripe Borders on Location Blocks
- **What**: `.loc-block` uses `border-left: 2px solid var(--accent-sage); padding-left: 20px;`.
- **Why it matters**: Side-stripe accent borders are an overt template cliché that looks decorative rather than purposeful.
- **Fix**: Replace with a soft background tint card, hairline full borders, or subtle leading icon/numeral tags.
- **Suggested command**: `/impeccable polish`

#### [P2] AI Editorial Scaffolding: Repeated Eyebrow Kickers
- **What**: Three consecutive sections feature small tracked uppercase category eyebrows above the H2.
- **Why it matters**: Repeating the exact same `kicker + heading + subtext` formula across the page feels like an LLM template rather than bespoke editorial art direction.
- **Fix**: Remove eyebrows from sections where the H2 is self-sufficient ("Diretório de procedimentos clínicos" and "Localização central e acesso facilitado") and vary the introduction layout.
- **Suggested command**: `/impeccable layout`

#### [P2] Dark Glow Tell on WhatsApp Floating Action
- **What**: `box-shadow: 0 8px 24px rgba(37, 211, 102, 0.35);` creates a bright green neon aura.
- **Why it matters**: Colored glows are a known AI aesthetic reflex. Physical UI controls should cast neutral shadows.
- **Fix**: Change to a clean neutral shadow: `box-shadow: 0 6px 20px rgba(0, 0, 0, 0.16);`.
- **Suggested command**: `/impeccable colorize`

#### [P3] Font Stack Cleanliness
- **What**: `Plus Jakarta Sans` is loaded in Google Fonts and listed in CSS, but `Outfit` is the designated primary sans-serif.
- **Why it matters**: Unnecessary font files add ~40KB of network payload and trigger detector alerts.
- **Fix**: Remove `Plus Jakarta Sans` from Google Fonts and CSS font stacks, committing fully to `Outfit + Newsreader`.
- **Suggested command**: `/impeccable typeset`

---

### Persona Red Flags

#### Marina (Busy Local Professional, Mobile)
- **Primary Action**: Find clinical phone/WhatsApp and schedule evaluation quickly.
- **Experience**: Clean hero, quick CTA. Floating WhatsApp trigger timing is now fixed and does not obscure content.
- **Red Flag**: Review carousel on mobile cannot be swiped horizontally; requires precise finger tap on 44px circular arrow buttons.

#### Sr. Geraldo (Older Patient seeking pain relief & reassuring care)
- **Primary Action**: Verify clinical credentials, location accessibility, and care for acute discomfort.
- **Experience**: Bento grid clearly states CRO SP-CD-104303 and CNPJ since 2019. Procedure directory clearly presents "Conservação e alívio de dor".
- **Red Flag**: Small tracked uppercase tags in Bento cards have slightly lower contrast on high-glare mobile screens.
