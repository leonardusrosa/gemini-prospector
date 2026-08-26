---
name: redesign-premium
description: Use esta skill ao criar um conceito de site novo para um prospecto sem site OU redesenhar o site existente de um cliente prospectado. Gera HTML/CSS/JS estático, factual, responsivo, contextualmente orientado e de alta conversão. Usa gpt-taste como direção criativa principal, design-taste-frontend como apoio anti-slop/contextual, uma camada obrigatória de motion/behavior e Impeccable apenas como QA final. Acione quando o usuário pedir "redesenhar site", "criar site do cliente", "conceito de site", "melhorar página", "refazer o site" ou equivalente.
---

# Redesign & Novo Conceito de Site

Crie uma presença digital específica para o negócio, nunca um template genérico com logo/cores trocados. Suporta:

- `siteMode = redesign` para site oficial existente e fraco.
- `siteMode = new_site_concept` para negócio forte sem site oficial confirmado.

A arquitetura de saída continua estática: `sites/[slug]/[slug].html`, CSS inline, vanilla JS, sem React/Next/Tailwind/npm/build.

---

## 1. Ordem Absoluta de Prioridades

1. **Integridade factual** — zero invenções.
2. **Identidade e ativos reais** — logo, fotos, profissional, local, produto, cores e conteúdo reais.
3. **Referências/requisitos do usuário** — extrair princípios, não clonar skins.
4. **`gpt-taste` = direção criativa PRIMÁRIA** — composição, layout variance, hierarquia, ritmo, art direction e motion concepts.
5. **`design-taste-frontend` = apoio contextual/anti-slop** — detectar clichês e verificar adequação ao negócio.
6. **Arquitetura estática do Prospector** — HTML/CSS/JS puro.
7. **Motion & Behavior Pass** — obrigatório decidir comportamento, mesmo que `Motion = 0`.
8. **`impeccable` = QA/polimento final** — qualidade de execução; não é diretor criativo.

Quando as skills estiverem instaladas, leia seus `SKILL.md` atuais. Não presuma regras antigas de memória.

**Regra estrutural:** preserve o que já funciona. Use criatividade onde ela tem maior alavanca. Não force novidade site-wide nem permita que um passe posterior reinterprete uma seção já aprovada.

---

## 2. Design Read Obrigatório Antes de Codificar

Crie/salve `sites/[slug]/design-read.md` quando possível. Deve conter:

```text
Business Context
Factual Constraints
Available Real Assets

Hero Mode
Hero Composition
Creative Intervention Scope

Creative Direction
Layout Variance
Section Rhythm
Typography Strategy
Color Strategy
Image Strategy

Mobile Art Direction

Motion Intensity
Hero Reveal
Section Reveal Grammar
Image Behavior
Microinteractions
Navbar Behavior
Floating CTA Behavior
Reduced Motion

Density
Anti-Slop Risks
Business-Specific Decisions
```

### Dials

Use 0–10 conscientemente:

- **Design Variance**
- **Motion**
- **Density**

Referências, não regras fixas:

- médico/odontologia: Variance 4–6, Motion 2–4, Density 3–5
- advocacia: 3–5, 1–3
- restaurante: 5–7, 3–6
- academia: 5–7, 4–7
- estúdio criativo: 7–9, 6–9

Não maximize variance sem motivo.

### Creative Intervention Scope

Classifique cada área como `HIGH`, `MEDIUM`, `LOW` ou `FROZEN`.

Exemplo:

```text
Hero: HIGH
Services: MEDIUM
Gallery: LOW
Bio: FROZEN
Contact: FROZEN
```

Se uma seção já passa factualidade, especificidade, responsividade, conversão e acabamento, congele-a.

---

## 3. Perguntas Obrigatórias de Especificidade

Antes e depois da implementação, responda internamente:

1. **Se eu trocar só logo, nome e cor, esta página poderia pertencer a 50 concorrentes?** Se sim, ainda está genérica.
2. **Quais decisões estruturais existem por causa dos ativos reais DESTE negócio?** Deve haver respostas concretas.
3. **Estou apenas trocando “AI slop” por outra estética universal da moda?** Ex.: beige editorial, luxo serif/gold, dark SaaS, glassmorphism, bento, brutalism, Swiss grid.
4. **A novidade prejudicou navegação/conversão?** Se sim, simplifique.
5. **O hero repete informações que aparecem logo abaixo?** Se sim, corte.
6. **Mobile é apenas desktop empilhado?** Se sim, rearticule.
7. **Cada animação melhora hierarquia/percepção de qualidade?** Se não, remova.

---

## 4. Classificação do Hero

Antes de desenhar, escolha um modo conceitual. Modos sugeridos:

- `expert_fullscreen`
- `venue_fullscreen`
- `product_fullscreen`
- `brand_typographic`
- `editorial_split`
- `conversion_split`
- `minimal_identity`

São estratégias, não templates rígidos.

### Seleção por ativo

- negócio centrado em profissional real + retrato forte → `expert_fullscreen`
- restaurante/hotel/imóvel com ambiente forte → `venue_fullscreen`
- produto físico forte → `product_fullscreen`
- identidade forte e imagem fraca → `brand_typographic`
- serviço institucional → split quando fizer sentido

Não force `expert_fullscreen` sem profissional real e central ao negócio.

---

## 5. HARD RULE — Expert Fullscreen Hero

Quando o negócio é claramente expert-led e existe foto real verificada do profissional, `expert_fullscreen` é a opção preferencial.

### Desktop

Objetivo padrão:

- hero ~90–100vh quando adequado
- **45–55% do território visual pertence ao expert**
- expert domina a direita/área visual escolhida e chega visualmente à borda
- expert fica **100% opaco, nítido e reconhecível**
- copy ocupa negative space intencional
- 1 CTA primário
- copy density baixa

**A direita pertence ao expert.** Não cubra rosto, torso, roupa/uniforme ou mãos com overlay branco amplo.

Se houver blend/fade, ele pode atuar **somente na fronteira do lado da copy / ambiente**, nunca “lavando” o profissional. O ambiente pode desaparecer; a pessoa não.

Rejeite:

- expert em rounded card/tile
- portrait com moldura/shadow de componente
- expert <30% do hero sem justificativa
- expert ghosted/transparente
- gradient atravessando rosto/corpo
- texto sobre o rosto
- badge colado no retrato
- pessoa visualmente subordinada ao bloco de copy

### Mobile

Mobile NÃO é desktop empilhado.

Composição padrão para `expert_fullscreen`:

```text
TOP ~50–55%     → expert image
BOTTOM ~45–50%  → headline + frase curta + CTA + 1–2 trust facts
```

A primeira dobra (~390×844) deve comunicar:

- quem
- o que faz
- ação principal

**Prioridade:** preserve a presença do expert; se não couber, REMOVA copy secundária antes de reduzir o expert.

Mobile normalmente tem MENOS texto que desktop.

### Assets separados

Quando o posicionamento do sujeito exigir, gere duas composições próprias:

```text
assets/hero-desktop.webp
assets/hero-mobile.webp
```

Não dependa de um único `object-fit: cover` se isso destruir a composição.

### Preservação de identidade

Prioridade de fonte:

1. retrato real verificado
2. ambiente real
3. ativos reais de marca

Se houver extensão/outpainting/composição:

- preserve a identidade real
- nunca regenere/substitua o rosto se isso mudar a pessoa
- não invente equipe/pacientes/ambiente/equipamentos
- prefira manter pixels reais do sujeito e estender apenas o ambiente

Se a geração não preservar a identidade, use composição do sujeito original em ambiente estendido.

---

## 6. HARD RULE — Hero Copy Density

Hero não é biografia nem seção “sobre”. Regra padrão para qualquer hero de alta proeminência (`expert_fullscreen`, `venue_fullscreen`, `product_fullscreen`):

- metadata opcional e discreta
- headline
- **1 frase curta de apoio**
- **1 CTA primário**
- no máximo 2–3 trust facts no desktop
- no máximo 1–2 trust facts no mobile

Referência de comprimento:

- desktop supporting copy: ~20–35 palavras
- mobile supporting copy: ~10–20 palavras

Não repita credenciais/serviços em parágrafo + bullets + badges.

Detalhes vão abaixo da dobra.

### HARD RULE — Proibido metadata pill/bubble no hero

**Nunca use pills, chips, cápsulas ou bubbles para metadata de categoria/localização no hero.** Exemplo proibido:

`Ortodontia & Harmonização · Rio Claro`

Não use isso nem como padrão “premium”.

Se metadata for realmente útil, use:

- plain microtext
- linha tipográfica discreta
- texto simples separado por ponto/divisor

Só use bubble/pill no hero se o usuário pedir explicitamente esse estilo.

---

## 7. Social/Contato no Topo

Quando existirem canais oficiais verificados, torne-os acessíveis cedo sem poluir o hero.

Desktop:

- logo
- navegação
- CTA principal
- ícones/ações compactas para canais úteis (Instagram, Facebook, WhatsApp, telefone) quando reais

Mobile:

- preserve CTA primário + menu
- secundários podem ir para drawer/menu

Nunca invente perfis sociais.

---

## 8. Regras Anti-Slop & Estrutura Visual

Evite padrões genéricos automáticos:

- gradiente roxo/azul SaaS sem contexto
- dark mode + glow blob para negócio local tradicional
- card dentro de card
- toda seção dentro do mesmo tipo de caixa
- três seções seguidas de `heading → paragraph → 3 cards`
- serif = premium por reflexo
- verde + dourado = luxo por reflexo
- beige editorial como “cura” para AI slop
- bento/glass/brutalism/Swiss grid usados como estética universal
- giant centered hero sem motivo

Cards são permitidos quando ajudam scanning, comparação ou agrupamento. Não use card só porque existe conteúdo.

### Section rhythm

Varie de forma coerente:

- split
- imagem/texto assimétricos
- full-width photographic moment
- serviço em hierarquia
- índice factual compacto
- gallery/mosaic guiado pelas fotos reais
- bloco funcional de conversão

Não transforme variedade em caos.

### Serviços

Quando houver evidência factual de prioridade, diferencie serviços principais e secundários. Não invente hierarquia comercial se ela não estiver sustentada.

---

## 9. Imagem Real Deve Influenciar a Estrutura

Ativos reais não são decoração de template.

Pergunta obrigatória:

> O layout funcionaria exatamente igual com imagens stock aleatórias?

Se sim, as imagens reais não estão influenciando a composição o suficiente.

Use fotos reais para determinar:

- hero
- crops
- proporções
- mosaicos
- transições de seção
- campos de fundo
- ritmo visual

**Nunca invente** profissional, equipe, pacientes, clínica, pratos, produtos, resultados, equipamentos, awards ou depoimentos.

Se faltarem imagens, responda com tipografia/layout — não com fotografia falsa.

---

## 10. Mobile Art Direction é Obrigatória

Não apenas reduza o desktop.

No Design Read, decida explicitamente:

- asset separado?
- copy reduzida?
- ordem muda?
- CTA secundário desaparece?
- socials migram para menu?
- crop muda?
- motion reduz?

### First-fold rule

Em hero de alta proeminência, a primeira dobra mobile deve mostrar o valor central + ação principal sempre que razoável. Se não couber, remova metadata/copy secundária/trust facts antes de reduzir o visual principal.

---

## 11. Motion & Behavior Pass — Permanente

Todo site deve tomar uma decisão explícita de motion, inclusive `Motion = 0`.

### Motion Read obrigatório

- Motion Intensity 0–10
- Hero Reveal
- Section Reveal Grammar
- Image Behavior
- Hover/Microinteractions
- Navbar Scroll Behavior
- Floating CTA Behavior
- Reduced Motion

### Vocabulário recomendado

Não use o mesmo fade-up em tudo.

- texto: opacity + translate discreto
- hero/expert/imagem: mask/clip/reveal ou scale muito pequeno
- cards: stagger curto
- gallery/mosaic: reveal seguindo a hierarquia visual
- bio: image/text paired reveal
- contato: reveal mínimo

Normalmente execute reveal **uma vez**.

### GSAP

Pode usar GSAP/ScrollTrigger em HTML estático quando melhorar a experiência.

Permitido:

- CDN estável/pinado ou asset local
- transform/opacity/clip-path
- hero choreography restrita
- reveal de seções
- microinterações

Proibido:

- scroll-jacking
- parallax gratuito
- partículas
- glow decorativo contínuo
- longas timelines que atrasam conteúdo
- animação word-by-word por padrão
- loops sem função
- tudo começando invisível e dependente de JS

**No-JS fallback:** conteúdo continua visível se a biblioteca falhar.

**Reduced motion:** respeite `prefers-reduced-motion: reduce`; remova atrasos/reveals e deixe conteúdo imediatamente visível.

### Hero reveal

Quando `Motion > 0`, planeje sequência curta, normalmente <1.2s:

1. visual principal resolve
2. headline
3. supporting copy
4. CTA
5. trust facts

Não anime cada palavra.

### Navbar

Quando fizer sentido:

- sticky
- transição sutil de estado após scroll
- smooth anchor navigation
- offset correto para header fixo

### Floating CTA

Evite CTA duplicado simultâneo. Se o hero já tem WhatsApp:

- floating CTA pode ficar oculto/minimizado enquanto o CTA do hero está visível
- aparece depois que o hero sai da viewport, preferencialmente via `IntersectionObserver`

### Microinteractions

Use feedback contido:

- underline
- color/border shift
- arrow 2–4px
- leve elevação

Sem bounce/neon/scale exagerado.

---

## 12. Factualidade para `new_site_concept`

Para negócio sem site:

- use Google Business Profile/Maps, redes oficiais e fontes públicas verificáveis
- não crie marca/persona/conteúdo fictício
- não invente serviços, preços, anos, credenciais, equipamentos, equipe, garantias
- não crie “site anterior” falso
- comparator/proposta devem dizer presença atual vs conceito de site
- outreach nunca deve dizer “redesenhei seu site”

Se o conteúdo for limitado, faça um site mais simples. Não compense lacunas com hallucination.

---

## 13. Localização de Mercado

Use `country`, `locale`, `language` e `phoneCountryCode` do lead.

- `pt-BR`: português brasileiro natural
- `pt-PT`: português europeu natural

Não traduza nomes próprios, marcas ou credenciais factuais sem motivo.

Telefone/WhatsApp deve usar número internacional normalizado pelo market service; não assuma `+55` globalmente.

---

## 14. Implementação Estática

Gere `sites/[slug]/[slug].html` com:

1. HTML5 semântico (`header`, `main`, `section`, `footer`).
2. CSS inline organizado via `:root`.
3. Vanilla JS.
4. CTA real (WhatsApp/telefone/booking) conforme o negócio.
5. endereço/horário/mapa factuais.
6. editor `sites/[slug]/[slug]-editor.html` via `references/editor-visual.md`.
7. sem React/Next/Tailwind/npm/build.

Dependências JS externas só quando justificadas e com fallback.

---

## 15. QA Final — Impeccable Bounded

Impeccable verifica qualidade de execução; não inicia outro redesign.

Teste pelo menos:

- 360
- 375
- 390/393 quando relevante ao mobile atual
- 768
- 1024
- 1280
- 1440

Verifique:

- zero overflow horizontal
- contraste WCAG AA
- legibilidade e line length
- hover/focus-visible
- tap targets
- mobile first fold
- hero crop/asset correto
- expert/product/venue realmente dominante quando esse for o modo
- nenhum gradient/overlay apagando sujeito principal
- **nenhum metadata pill/bubble no hero**
- CTA claro e cedo
- social/contact actions sem overcrowding
- motion sem jank/layout shift
- reduced-motion
- conteúdo visível sem JS
- copy sem redundância
- ausência de padrões AI repetitivos

Faça **1 passe consolidado de correção** e uma rechecagem.

### QA específico de hero proeminente

Desktop:

- o visual principal possui território próprio?
- está sendo lavado por overlay?
- copy está curta?
- CTA é óbvio?

Mobile:

- visual principal ocupa a primeira metade quando esse é o conceito?
- copy foi realmente reduzida?
- CTA aparece cedo?
- é uma composição própria, não desktop empilhado?

---

## 16. Workflow Permanente

```text
RESEARCH
→ FACTUAL SOURCE SET
→ DESIGN READ
→ SELECT HERO MODE
→ DEFINE CREATIVE INTERVENTION SCOPE
→ GPT-TASTE ART DIRECTION
→ STATIC BUILD
→ MOBILE-SPECIFIC PASS
→ MOTION & BEHAVIOR PASS
→ IMPECCABLE QA
→ SCREENSHOT REVIEW
→ HUMAN APPROVAL
```

Durante benchmark/teste, pare para aprovação humana antes de deploy/outreach.

Depois de aprovação, o fluxo normal pode seguir para proposta/deploy conforme as outras skills.

---

## 17. Comparador e CRM

1. `redesign`: comparar site atual vs nova versão.
2. `new_site_concept`: presença atual (Maps/redes) vs conceito.
3. atualizar o mesmo lead no CRM; não duplicar.
4. não registrar outreach durante geração de site.

A mudança de status deve seguir o lifecycle atual do CRM e nunca implicar contato/envio sem autorização específica.

---

## 18. HARD RULE — Companion Research, Hero Engineering & Performance References

Estas referências fazem parte do workflow desta skill; não são documentação opcional:

```text
references/first-party-source-crawl.md
references/design-performance-playbook.md
```

Quando `Hero Mode = expert_fullscreen`, leia também:

```text
references/expert-hero-generation.md
```

### Existing-site research

Para `siteMode = redesign`, **não finalize o Design Read com evidência apenas da homepage** quando houver subpáginas oficiais úteis e descobríveis.

Antes do Design Read final:

```text
official domain
→ homepage
→ targeted same-domain source-tree crawl
→ facts/assets + provenance
→ asset manifest
→ FACTUAL SOURCE SET
→ DESIGN READ
```

Serviços/especialidades, equipe/expert, instalações/gallery e contato/localização são páginas prioritárias. O crawl é dirigido e normalmente depth ~2–3, não spider indiscriminado.

### Subject-safe hero rendering

`cover` nunca é um requisito. Não use `background-size: cover`/`object-fit: cover` se ele cortar ou ampliar destrutivamente o sujeito principal em widescreen.

Quando necessário, use:

- asset dedicado desktop/mobile;
- `<picture>` e posicionamento controlado;
- `contain` + anchoring;
- source-preserving compositing.

Se houver gradient/overlay para legibilidade da copy, restrinja-o ao território da copy/ambiente. **Nunca lave o expert.**

Quando composição/outpainting revelar bordas retangulares, dissolva essas bordas de forma sutil no background. Isso é condicional, não efeito obrigatório.

### Header — default condicional

Prefira header primário limpo em vez de `utility bar + navbar` redundantes. Mantenha utility bar quando ela tiver utilidade comercial real.

Glass/translucency pode ser usada sobre hero imersivo quando melhorar legibilidade e fizer sentido para a identidade. **Glassmorphism não é estética padrão.** Valores CSS exatos do playbook são referência, não tokens universais.

### Mobile immersive flow

Para `expert_fullscreen`/hero imersivo no mobile, evite por padrão o retrato recortado numa caixa superior visualmente desconectada de um card branco inferior. Quando compatível com a direção, use continuidade/fade suave entre visual e copy.

### HARD RULE — image performance

- hero/LCP **não** usa `loading="lazy"`;
- use `fetchpriority="high"` no `<img>` LCP quando adequado;
- preload desktop/mobile hero quando forem recursos críticos conhecidos;
- `<img>` deve ter `width`/`height` intrínsecos quando conhecidos para reduzir CLS;
- imagens abaixo da dobra usam `loading="lazy"` + `decoding="async"` por padrão;
- prefira WebP/AVIF/formatos modernos e compressão perceptual apropriada.

Qualidade WebP, dimensão 2x e budgets de KB são **heurísticas**, não hard limits. Não degrade rosto/ativo real para atingir número arbitrário.

### Location conversion module

Quando localização física for relevante à conversão, prefira módulo compacto com endereço factual + CTA direto de rota. Map iframe é opcional e, se abaixo da dobra, deve ser lazy-loaded.

Não force mapa em todo site.

### Workflow efetivo

Interprete o workflow da seção 16 como:

```text
RESEARCH
→ FIRST-PARTY SOURCE TREE (redesign)
→ FACTUAL SOURCE SET + ASSET MANIFEST
→ DESIGN READ
→ SELECT HERO MODE
→ HERO ASSET/RENDERING STRATEGY
→ DEFINE CREATIVE INTERVENTION SCOPE
→ GPT-TASTE ART DIRECTION
→ STATIC BUILD
→ MOBILE-SPECIFIC PASS
→ IMAGE/PERFORMANCE PASS
→ MOTION & BEHAVIOR PASS
→ IMPECCABLE QA
→ SCREENSHOT REVIEW
→ HUMAN APPROVAL
```

### QA adicional obrigatório

Além da seção 15, confirme:

- subpáginas oficiais relevantes foram consideradas no redesign;
- hero não perde cabeça/torso/sujeito em 1280/1440 e telas mais largas;
- nenhum `cover` destrutivo;
- nenhum gradient cruza/lava o sujeito;
- hero não foi lazy-loaded;
- preload/fetchpriority foram usados apenas quando realmente críticos;
- dimensões intrínsecas evitam CLS evitável;
- imagens abaixo da dobra estão lazy/async salvo exceção justificada;
- glass/map/vignette/fades aparecem somente quando justificados pelo caso.
