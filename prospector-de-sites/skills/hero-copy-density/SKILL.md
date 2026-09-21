---
name: hero-copy-density
<<<<<<< HEAD
description: HARD RULE and governance standard for hero copy structure and density on all public prospect sites. Eliminates redundant repetition of material facts across hero layers (eyebrow, headline, supporting copy, trust metadata, CTA). Enforces a disciplined, editorial 5-layer hero architecture, compact single-line trust presentation, and natural evidence-backed phrasing. Mandatory for every new or regenerated site.
---

# Hero Copy Density & De-Duplication Rule

This standard is mandatory for every new or actively regenerated public website created or audited by Prospector. It has absolute authority over hero textual composition and applies across GPT-Taste creative direction, copywriting review, and deterministic QA.

---

## 1. The 5 Hero Fact Layers

Every hero section is organized into up to five distinct structural layers:

1. **EYEBROW (`EYEBROW_FACTS`)**: Architectural location, service category, or business identifier (e.g., `AUTO DETAILING • ADDISON, TEXAS`).
2. **HEADLINE (`HEADLINE_FACTS`)**: Dominant, factual primary offer or capability statement (e.g., `AUTOMOTIVE DETAILING & PAINT REFINEMENT`).
3. **SUPPORTING COPY (`SUPPORTING_COPY_FACTS`)**: Exactly one short sentence expanding service scope or factual specialty.
4. **CTA (`CTA_FACTS`)**: One disciplined primary contact or action trigger (e.g., `Call (214) 400-7287 →`).
5. **TRUST METADATA (`TRUST_FACTS`)**: Maximum one compact editorial trust line (e.g., `★ 4.9 / 268 Reviews`).

---

## 2. Universal De-Duplication Invariant

**Rule:** The same material fact must never be repeated across hero layers. Repeating a fact across layers unnecessarily triggers an automatic **FAIL**.

### Fact Dimensions to Audit:
- **Location / City:** If city/state appears in the Eyebrow, it must NOT appear in Supporting Copy or CTA.
- **Rating:** If aggregate rating (e.g., `4.9`) appears in Trust Metadata, it must NOT be mentioned in Supporting Copy.
- **Review Count:** If review volume (e.g., `268 Reviews`) appears in Trust Metadata, it must NOT be mentioned in Supporting Copy.
- **Phone Number:** If phone number appears in the primary CTA button/link, it must NOT be repeated in Supporting Copy.
- **Service Scope:** Core service keywords should be divided cleanly between Headline and Supporting Copy rather than repeating the exact same terms.
- **Expert / Person:** Do not repeat the owner or specialist name in both eyebrow and supporting copy.

### Fact Normalization:
Gate checks normalize semantic equivalents:
- `4.9`, `4.9 / 5`, `4.9 rating`, `★ 4.9` are evaluated as the same rating fact.
- `268 reviews`, `268 public reviews`, `268` are evaluated as the same review-count fact.
- Formatted phone numbers `(214) 400-7287` and raw digits `2144007287` are evaluated as the same phone fact.
- `Addison`, `Addison, TX`, `Addison, Texas` are evaluated as the same location fact.

---

## 3. Supporting Copy Discipline & Natural English

Supporting copy must remain concise (1 short sentence) and describe the actual service capabilities.

### Banned Repetitions in Supporting Copy:
- Do **NOT** write: `Auto detailing in [City]. Backed by a 4.9 rating across 268 reviews.` (Duplicates location and trust facts).
- Do **NOT** write: `Call us today at [Phone] for appointments.` (Duplicates CTA).
- Do **NOT** write unnatural phrasing such as: `Individual service by Wilson` (Awkward English). If verified expert relationship is established and desired, use natural syntax: `Detailing and paint correction by Wilson.`—provided it introduces no duplicate facts. If direct evidence is ambiguous, omit personal names from supporting copy entirely.

---

## 4. Trust Presentation & Source-Neutral Wording

### Compact Editorial Trust Line:
Trust metadata must be rendered as a single compact editorial line:
```text
★ 4.9   /   268 Reviews
```
or
```text
4.9 / 5   •   268 Reviews
```

### Prohibited Trust Formats:
- NO separate rating cards or review cards.
- NO dual stat boxes or floating cards.
- NO pill badges, badge clusters, or pill capsules.
- NO platform vendor names (`Google`, `Google Reviews`, `Google Maps`).
- The word **"Public"** is NOT required merely to achieve source neutrality. Prefer clean terms: `Rating`, `Reviews`. Only include "Public" if disambiguation strictly requires it.

---

## 5. Hero Density Ceiling

The hero is an executive entry portal, not an exhaustive summary.

- **Eyebrow:** 0 or 1 line.
- **Headline:** 1 dominant title.
- **Supporting Copy:** 1 concise sentence (maximum 18 words).
- **CTA:** Exactly 1 primary action button or link.
- **Trust:** Maximum 1 compact line.

Do not transform the hero section into an About section, review summary, service catalog, or contact directory.
=======
description: Regra global obrigatória para heroes do Prospector. Evita repetição de localização, rating, review count, CTA e outros trust facts entre eyebrow, headline, supporting copy, metadata e CTA. Use junto com website-core-rules e redesign-premium.
---

# Hero Copy Density & Trust-Fact De-duplication

Esta regra é global para qualquer hero público criado ou regenerado pelo Prospector.

## 1. Invariante principal

Cada camada do hero deve adicionar informação nova.

Não repita o mesmo fato entre:

- eyebrow / microtext
- headline
- supporting copy
- trust metadata
- rating/review line
- CTA

Se um fato já aparece de forma clara em uma camada, remova-o das demais, salvo quando a repetição for necessária para acessibilidade ou compreensão em viewport diferente.

## 2. Trust facts não pertencem ao supporting copy quando já estão visíveis

Se rating, review count, localização, telefone ou outra prova factual já aparece como metadata/trust line no hero, o supporting copy não deve repeti-la.

Exemplo proibido:

```text
Auto detailing, paint correction, and buffing in Addison, Texas. Individual service by Wilson, backed by a 4.9 rating across 268 public reviews.

Call (214) 400-7287

4.9 Public Rating
268 Public Reviews
```

Problemas:

- localização repetida quando já está no eyebrow/metadata
- rating repetido
- review count repetido
- supporting copy sobrecarregado
- `Public Rating` / `Public Reviews` soam burocráticos quando a neutralidade de fonte já está garantida por contexto

## 3. Composição preferida

Prefira uma hierarquia enxuta:

```text
AUTO DETAILING • ADDISON, TEXAS

Paint Correction,
Done With Precision.

Auto detailing, paint correction, and buffing.

Call (214) 400-7287 →

★ 4.9   /   268 Reviews
```

Se a relação de Wilson com o serviço estiver diretamente verificada, uma alternativa possível é:

```text
Detailing and paint correction by Wilson.
```

Se não estiver diretamente verificada, omita o nome.

## 4. Regras de densidade

Hero não é seção Sobre, FAQ ou bloco de prova social completo.

Por padrão:

- eyebrow factual opcional ou ausente
- 1 headline
- 1 supporting line curta
- exatamente 1 CTA primário
- no máximo 1 linha compacta de trust facts

Desktop supporting copy: normalmente 12–30 palavras.

Mobile supporting copy: normalmente 8–20 palavras.

Detalhes adicionais devem ir abaixo da dobra.

## 5. Rating e reviews

A neutralidade de fonte não exige a palavra `Public` em cada label.

Prefira:

```text
4.9
Rating

268
Reviews
```

ou, para hero editorial/minimalista:

```text
★ 4.9   /   268 Reviews
```

Evite por padrão:

```text
4.9 Public Rating
268 Public Reviews
```

`Public` só deve aparecer quando necessário para eliminar ambiguidade factual real.

Nunca exponha o nome da plataforma de review no hero público.

## 6. Localização

Se a localização já está no eyebrow, por exemplo:

```text
AUTO DETAILING • ADDISON, TEXAS
```

o supporting copy não deve repetir `in Addison, Texas` sem motivo específico.

A mesma regra vale para cidade, bairro, país ou área de atendimento.

## 7. CTA

O supporting copy não deve repetir a ação literal do CTA.

Exemplo ruim:

```text
Call Wilson today to discuss your vehicle.
Call (214) 400-7287 →
```

Prefira deixar a ação somente no CTA.

## 8. Factualidade continua soberana

De-duplicação nunca autoriza copy nova não verificada.

Uma versão mais curta ainda precisa obedecer:

- evidence safety
- claim granularity
- relationship provenance
- review provenance
- public review source neutrality

Não use a busca por concisão para introduzir hype como `premium`, `expert`, `specialist`, `leading`, `award-winning`, `luxury`, `best`, `#1` ou equivalentes sem evidência.

## 9. QA obrigatório

Para cada hero, extraia e compare:

```text
EYEBROW_FACTS
HEADLINE_FACTS
SUPPORTING_COPY_FACTS
TRUST_FACTS
CTA_FACTS
```

Falha se o mesmo fato material aparecer desnecessariamente em mais de uma camada.

Estados:

```text
HERO_COPY_DEDUP: PASS | FAIL
HERO_COPY_DENSITY: PASS | FAIL
```

Casos que devem falhar:

```text
supporting copy: "Backed by a 4.9 rating across 268 reviews."
trust line: "★ 4.9 / 268 Reviews"
```

```text
eyebrow: "Auto Detailing • Addison, Texas"
supporting copy: "Auto detailing in Addison, Texas."
```

Casos que devem passar:

```text
eyebrow: "Auto Detailing • Addison, Texas"
headline: "Paint Correction, Done With Precision."
supporting copy: "Auto detailing, paint correction, and buffing."
trust line: "★ 4.9 / 268 Reviews"
CTA: "Call (214) 400-7287"
```

## 10. Precedência

Se uma referência visual, template, component library, 21st.dev component, GPT-generated layout ou copy pass repetir trust facts para preencher o hero, esta regra vence.

Evidence safety permanece soberana sobre esta regra.
>>>>>>> 111bb01277813dd9eca929b882156644eca90b9e
