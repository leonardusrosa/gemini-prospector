---
name: hero-copy-density
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