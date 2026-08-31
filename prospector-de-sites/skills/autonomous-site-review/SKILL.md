---
name: autonomous-site-review
description: HARD GATE obrigatorio depois de criar ou alterar qualquer site/conceito/redesign do Prospector e antes de Screenshot Review, deploy, proposta ou outreach. Deve detectar autonomamente omissoes de gpt-taste, motion/scroll behavior, WhatsApp, Instagram mock/real, mapa incorporado, colisao de floating UI, reduced motion, no-JS fallback, factualidade e regressões visuais. Nunca marque um site como Core QA PASS sem executar esta skill.
---

# Autonomous Site Review

Esta skill é uma barreira de qualidade, não uma revisão opcional. Ela existe para impedir que um agente produza uma página tecnicamente válida, mas incompleta em experiência, conversão ou requisitos permanentes.

## Regra de precedência

Use sempre em conjunto com:

1. `../website-core-rules/SKILL.md`
2. `../redesign-premium/SKILL.md`
3. `gpt-taste` instalado no ambiente

O review não substitui essas skills. Ele verifica se elas realmente apareceram no resultado final.

## 1. HARD GATE: gpt-taste foi realmente usado

Para qualquer criação, redesign ou rework visual:

- leia o `SKILL.md` ATUAL do `gpt-taste` antes de codificar;
- não trabalhe de memória;
- registre o caminho lido, SHA-256 do arquivo e a decisão visual em `sites/[slug]/design-read.md`;
- o arquivo deve conter, no mínimo:

```text
GPT_TASTE_READ: PASS
GPT_TASTE_PATH: <caminho real lido>
GPT_TASTE_SHA256: <sha256 do SKILL.md lido>
Design Variance: <0-10>
Motion: <0-10>
Density: <0-10>
```

O validator abre o caminho registrado e compara o hash. Portanto, escrever apenas `GPT_TASTE_READ: PASS` sem ter o arquivo atual disponível não satisfaz o gate.

Se a skill mudar, o agente deve reler e registrar o novo hash.

`scroll-behavior: smooth` não conta como Motion & Behavior Pass.

## 2. HARD GATE: motion e comportamento

Sites de prospecção/redesign devem ter `Motion > 0` por padrão. Exceções só com motivo explícito no `design-read.md`.

O review exige evidência real de comportamento, de forma coerente com o negócio:

- estado do header ao rolar a página;
- hero entry/reveal curto quando Motion > 0;
- pelo menos dois grupos/áreas com reveal ou comportamento de entrada quando a página tiver conteúdo suficiente;
- microinterações funcionais;
- conteúdo permanece legível sem JavaScript;
- `prefers-reduced-motion` respeitado;
- sem scroll-jacking, loops gratuitos ou animação ornamental excessiva.

Para facilitar QA determinístico, novos sites devem usar hooks semânticos invisíveis ao usuário:

```html
<header data-role="site-header">...</header>
<section data-role="hero">...</section>
<div data-motion="reveal">...</div>
<a data-role="floating-whatsapp" ...>...</a>
```

Esses atributos não são copy pública nem ornamentação.

## 3. HARD GATE: WhatsApp

Quando houver WhatsApp/telefone verificado e apropriado para contato:

- CTA primário funcional;
- ação funcional na área de contato;
- floating WhatsApp depois que o CTA principal do hero deixa a viewport, salvo exceção de UX documentada;
- número/destino deve ser o verificado;
- não mostrar floating CTA competindo com o CTA do hero ao mesmo tempo.

O floating CTA deve usar `data-role="floating-whatsapp"` nos novos sites para QA automatizado.

Em mockup comercial onde WhatsApp ainda não tiver destino verificável, represente a affordance somente quando o manifesto pedir `mockAffordanceRequired`, usando `data-social="whatsapp"`, `aria-disabled="true"` e **sem atributo `href`**.

## 4. HARD GATE: Instagram/social em mockups comerciais

Para conceitos/noindex de prospecção, represente a UI de Instagram mesmo quando o perfil ainda não estiver verificado.

### Perfil verificado

- link real ativo;
- `data-social="instagram"`;
- destino verificado.

### Perfil não verificado

- affordance visual presente;
- `data-social="instagram"`;
- `aria-disabled="true"`;
- **nenhum atributo `href`**, nem `#`, nem `javascript:void(0)`;
- sem URL inventada;
- sem username inventado;
- não navegável (`tabindex="-1"` ou equivalente).

Nunca fabricar `instagram.com/<handle>`.

Na entrega final do cliente, nenhum destino fake pode permanecer ativo.

## 5. HARD GATE: mapa

Se existir endereço físico público e VERIFICADO do negócio, a seção de localização deve, por padrão, incluir mapa incorporado real.

Aceitável:

```html
<iframe
  src="https://maps.google.com/maps?q=<ENDERECO>&z=16&output=embed"
  loading="lazy"
  referrerpolicy="no-referrer-when-downgrade"
  title="Mapa de localização ..."
></iframe>
```

Também mantenha uma ação externa `Abrir no Google Maps`/equivalente quando útil.

Um card com pin + endereço + botão, sem preview incorporado, NÃO satisfaz o gate.

Só omita iframe quando endereço for privado, o operador pedir ou houver bloqueio técnico documentado.

## 6. HARD GATE: floating UI e assistant

Quando coexistirem assistant, WhatsApp, cookie bar ou outros controles fixos:

- eles não podem se sobrepor;
- não podem esconder CTA ou conteúdo essencial;
- validar 1440x900, 800x1024 e 390x844;
- no mobile, evitar empilhar múltiplos controles grandes sobre o conteúdo.

O launcher do assistant deve usar `data-role="assistant-launcher"` quando a implementação permitir, para permitir geometry QA determinístico.

## 7. Review em duas camadas

### Camada A: determinística/estática

Execute:

```bash
python prospector-de-sites/autonomous_site_review.py \
  --html sites/[slug]/[slug].html \
  --design-read sites/[slug]/design-read.md \
  --manifest sites/[slug]/review-manifest.json
```

Ela deve falhar (exit code != 0) quando requisitos estruturais obrigatórios estiverem ausentes.

### Camada B: browser/visual

Execute depois com site local ou URL pública:

```bash
python prospector-de-sites/autonomous_site_review_browser.py \
  --url <URL> \
  --manifest sites/[slug]/review-manifest.json
```

Se Playwright não estiver disponível, não marque Browser Review PASS. Instale/use o ambiente de QA apropriado ou reporte o bloqueio.

## 8. Manifesto obrigatório por site

Crie `sites/[slug]/review-manifest.json` usando o exemplo em `references/review-manifest.example.json`.

O manifesto registra fatos de QA, não fatos comerciais inventados. Exemplos:

- endereço verificado: true/false;
- WhatsApp verificado e número esperado;
- Instagram: `verified`, `unverified`, `not_applicable`;
- assistant presente: true/false;
- motion esperado: true/false;
- preview/noindex: true/false.

Nunca marque `verified=true` apenas para fazer o teste passar.

## 9. Review adversarial obrigatório

Depois do primeiro PASS, faça uma segunda revisão com postura adversarial:

> "Se eu fosse o revisor tentando REPROVAR esta página, quais requisitos o agente poderia ter esquecido apesar de o site parecer bonito?"

Inspecione especialmente:

- gpt-taste apenas citado, mas não usado/arquivo atual não comprovado;
- `Motion > 0` no design-read mas página imóvel;
- mapa substituído por placeholder;
- Instagram omitido porque não havia URL real;
- social mock desabilitado mas ainda com `href`, `#` ou `javascript:void(0)`;
- WhatsApp apenas no hero, sem floating/contact;
- floating WhatsApp colidindo com assistant;
- reduced motion declarado no CSS, mas comportamento ainda animado;
- no-JS deixando conteúdo invisível;
- CTA/fato removido em desktop mas quebrado no mobile;
- console/network 404 silencioso;
- claims reintroduzidos depois do factual hardening.

## 10. Proibição de autoaprovação por checklist textual

Um relatório escrito pelo próprio agente não é evidência suficiente.

`PASS` requer observação verificável:

- inspeção do HTML/DOM;
- execução do validator;
- hash do gpt-taste atual validado;
- browser QA;
- screenshots/geometry quando aplicável;
- network/console checks;
- fonte factual quando o item depender de verdade do negócio.

Se o agente apenas disser “PASS” sem executar, o estado é `NOT VERIFIED`.

## 11. Gate final

Use este bloco na saída:

```text
AUTONOMOUS SITE REVIEW
GPT_TASTE_READ: PASS/FAIL
GPT_TASTE_SHA_MATCH: PASS/FAIL
STATIC REVIEW: PASS/FAIL
BROWSER REVIEW: PASS/FAIL
ADVERSARIAL REVIEW: PASS/FAIL
MOTION: PASS/FAIL
WHATSAPP: PASS/FAIL/N/A
INSTAGRAM UI: PASS/FAIL/N/A
MAP EMBED: PASS/FAIL/N/A
FLOATING UI COLLISION: PASS/FAIL/N/A
REDUCED MOTION: PASS/FAIL
NO-JS: PASS/FAIL
DESKTOP: PASS/FAIL
TABLET: PASS/FAIL
MOBILE: PASS/FAIL
CONSOLE/NETWORK: PASS/FAIL
FACTUAL REGRESSION: PASS/FAIL

AUTONOMOUS_REVIEW_PASS: YES/NO
```

Deploy/proposta/outreach só podem avançar quando `AUTONOMOUS_REVIEW_PASS: YES`.
