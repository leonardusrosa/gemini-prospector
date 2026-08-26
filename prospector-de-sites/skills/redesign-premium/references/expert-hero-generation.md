# Expert Hero Asset Generation — Antigravity-native first

Use esta referência quando `Hero Mode = expert_fullscreen` e existir uma foto real, clara e verificada do profissional.

O objetivo é transformar o retrato real em duas composições de hero próprias para web — desktop e mobile — mantendo a identidade do expert e deixando o texto do site em HTML, nunca dentro da imagem.

## 1. Regra de ativação

Gerar assets dedicados quando TODOS forem verdadeiros:

- o negócio é genuinamente expert-led;
- o profissional é central para confiança/conversão;
- existe foto real verificada com rosto nítido e resolução utilizável;
- a identidade da pessoa pode ser preservada;
- `heroMode = expert_fullscreen`.

Exemplos comuns: dentista, médico, advogado, arquiteto, consultor, terapeuta, contador, chef, especialista/founder-led service.

Não ativar quando o retrato for ambíguo, muito pequeno, fortemente obstruído ou quando venue/product/brand for claramente o visual principal.

## 2. Ordem de capacidade — HARD RULE

O Prospector deve preferir a capacidade de geração/edição de imagem já disponível dentro da sessão do Google Antigravity, para aproveitar a conta/quota do ambiente em vez de introduzir cobrança de API separada sem necessidade.

Ordem:

```text
1. Image generation/editing nativo disponível ao agent no Antigravity
   ↓ se disponível
   usar como primeira opção

2. Nativo indisponível ou incapaz de salvar resultado no workspace
   ↓
   usar fallback source-preserving sem geração paga

3. API externa/direta (Gemini API ou outro provider)
   ↓
   SOMENTE se o usuário tiver configurado explicitamente esse provider
```

### HARD RULE — não criar dependência paga silenciosa

- Não exigir `GEMINI_API_KEY` para o fluxo padrão.
- Não pedir API key automaticamente apenas para gerar hero.
- Não ativar billing/API externa silenciosamente.
- Não assumir que assinatura Google AI Pro e billing de Gemini API são a mesma coisa.
- Se um provider externo estiver explicitamente configurado pelo usuário, ele pode ser usado como fallback conforme a configuração.

O agent deve registrar no `design-read.md` qual capacidade foi usada:

```text
Hero Asset Generation: antigravity-native | source-preserving-fallback | external-provider
```

## 3. Outputs canônicos

Salvar sempre no diretório do lead:

```text
sites/[slug]/assets/hero-expert-desktop.webp
sites/[slug]/assets/hero-expert-mobile.webp
```

Preservar também o retrato-fonte original em `assets/` ou seu caminho original. Nunca sobrescrever o source real.

Se o gerador produzir PNG/JPEG, converter/otimizar para WebP depois sem recompressão destrutiva visível.

## 4. Desktop — composição ultrawide preferencial

Para `expert_fullscreen` com copy à esquerda e expert à direita, **o default desktop passa a ser ultrawide art-directed**, não 16:9.

Aspect ratio preferencial:

```text
~2.3:1 a ~2.6:1
```

Resolução recomendada quando útil:

```text
3K/4K-class
ex.: 3584 × 1533
```

A proporção e dimensão exatas são heurísticas, não hard limits.

### HARD RULE — expert centered in the right half

O expert deve estar **centrado visualmente dentro da metade direita do canvas**.

Referência geométrica:

```text
left half center  ≈ x 25%
right half center ≈ x 75%
expert visual center ≈ x 75%
```

Isso significa:

- o expert não deve ficar colado à borda direita;
- o expert não deve derivar para o centro geral da imagem e competir com a copy;
- deve existir breathing room ao redor do sujeito;
- cabeça/torso devem permanecer íntegros quando a imagem for exibida em widescreen com subject-safe scaling;
- a metade esquerda continua reservada como negative space para headline/CTA HTML.

### Objetivo visual desktop

- cinematic ultrawide website hero;
- expert no centro da metade direita;
- manter pose, rosto, expressão, roupa e orientação do retrato-fonte;
- expert grande, nítido e 100% opaco;
- left half calma para copy HTML;
- background suave, levemente desfocado e pouco distrativo;
- sem texto, logo, botão, badge, UI ou lettering dentro da imagem;
- nenhum gradient/fog sobre o expert.

Nunca gerar um portrait-card dentro de uma imagem maior.

### Prompt-base desktop

```text
Create a cinematic ultrawide desktop website hero image using the provided real expert portrait as the identity and pose anchor.

Preserve this exact person's facial identity, approximate age, expression, hairstyle, professional clothing and pose. Do not replace, beautify into a different person, or substantially alter the subject.

Canvas/composition:
- use an ultrawide composition, preferably around 2.3:1 to 2.6:1
- the expert must be CENTERED WITHIN THE RIGHT HALF of the frame
- place the expert's visual center approximately around x = 75% of the canvas
- do not pin the expert to the far-right edge
- do not let the expert drift toward the center/left copy territory
- keep the expert large, crisp, fully opaque and visually dominant
- preserve comfortable breathing room around the head and upper body
- reserve the LEFT HALF as calm negative space for HTML headline and CTA that will be added later
- no text inside the image

Background:
- extend/fill the scene naturally around the real portrait
- soft, restrained, slightly blurred professional atmosphere appropriate to the supplied factual business/expert context
- background must stay unobtrusive
- do not invent extra people, patients, staff, procedures, awards, prominent equipment or fake luxury architecture

Important:
- do not put a white gradient, fog or transparency over the expert
- do not fade the face, torso, shoulders, uniform/clothing or hands
- leave enough clean environment at all canvas edges for later edge integration/feathering if needed
- no logos, badges, buttons, UI or typography
```

Append factual expert context after the prompt, clearly labelled as context only. Example:

```text
Expert context (factual context only; do not render as text):
Dr. Cássio Renato Lourenço Ferreira — cirurgião-dentista dedicado à ortodontia e harmonização facial [...verified summary...].
```

### Desktop fallback

If the provider cannot create a useful ultrawide asset:

1. generate the widest practical composition while preserving right-half centering;
2. extend canvas/background source-preservingly afterward;
3. only fall back to 16:9 when it genuinely preserves the layout better.

Do not treat 16:9 as the preferred desktop target for this mode.

## 5. Mobile — composição obrigatória

Preferir asset dedicado, não crop do desktop ultrawide.

Target recomendado quando o provider aceitar:

```text
1080 × 1920
9:16
```

Se o provider não oferecer 9:16, gerar a proporção vertical mais próxima e fazer crop final controlado.

Objetivo visual:

- composição pensada para a primeira dobra mobile;
- expert grande no TOP ~50–55%;
- mostrar cabeça + upper body;
- **não mostrar o expert da cintura para baixo**;
- preservar pose/direção e identidade;
- lower ~45–50% mais calmo/limpo para HTML headline, frase curta e CTA;
- nenhum texto dentro da imagem;
- fundo suave/desfocado e não distrativo.

### Prompt-base mobile

```text
Create a dedicated vertical mobile website hero image using the provided real expert portrait as the identity and pose anchor.

Preserve this exact person's facial identity, approximate age, expression, hairstyle, professional clothing and pose direction. Do not create a different person.

Composition:
- vertical mobile hero, ideally 9:16
- place the expert large in the TOP 50–55% of the frame
- show head and upper body only
- DO NOT show the expert waist-down
- keep the face and upper body crisp, recognizable and fully opaque
- reserve the LOWER 45–50% as calm negative space for HTML headline, short supporting text and CTA added later
- no text inside the image

Background:
- softly extend the real scene into a restrained, slightly blurred professional environment appropriate to the factual context
- no extra people, patients, staff, procedures, awards, prominent invented equipment or fake luxury architecture

Important:
- do not fade or wash out the expert
- do not place copy over the face
- no logos, badges, buttons, UI or typography
```

## 6. Identity preservation hierarchy

For expert-led sites, identity fidelity has priority over creativity.

Use this hierarchy:

```text
exact real subject / pose
> realistic scene extension
> aesthetic novelty
```

Reject an output if the face is materially changed even when the composition looks better.

### Source-preserving fallback

If native generation changes identity too much:

1. keep the original portrait pixels for the expert;
2. generate/construct only the environment/background extension if possible;
3. composite the untouched expert into that environment;
4. blend only the subject/background boundary;
5. never feather/fade the expert itself;
6. if background generation is unavailable, create a restrained source-derived background using real clinic/brand imagery, blur, crop and tonal extension.

Do not use a synthetic replacement face as fallback.

## 7. Desktop edge integration / image preparation

Ultrawide + `contain` may intentionally expose canvas boundaries against the page background. Eliminate the rectangular-box effect before final QA.

### Preferred principle

If boundaries are visible, dissolve all four canvas edges into the page background while keeping the expert untouched.

A suitable implementation may use:

- four-edge cosine/gradient feathering;
- tonal continuation into the exact/near-exact hero background;
- source-preserving background extension;
- equivalent alpha/mask treatment.

### Example PIL heuristics — not hard limits

For a ~3584px-wide source, a starting point may be:

```text
left fade   ~220px
right fade  ~220px
top fade    ~110px
bottom fade ~130px
```

These are examples only. Scale/adapt based on canvas dimensions and source composition.

### HARD RULE — never feather the expert

The expert's face/body/clothing must remain outside the feather zones or be explicitly protected by the mask.

Feather:

```text
environment/canvas edge = allowed
expert silhouette        = protected / fully opaque
```

### Resampling/sharpening

Lanczos and restrained sharpening are valid offline post-process options. Dual-stage unsharp mask may be used when it genuinely restores texture after resampling.

Do not oversharpen skin, hair, clothing edges or create halos.

WebP `quality=99` is a high-quality heuristic, not a permanent requirement. Tune perceptually and preserve LCP budget.

## 8. Autonomous workflow

When building a lead autonomously:

```text
RESEARCH
→ FACTUAL SOURCE SET
→ ASSET INVENTORY
→ HERO MODE
→ expert_fullscreen + usable verified portrait?
   ├─ NO  → continue with chosen non-expert hero strategy
   └─ YES
       → detect Antigravity-native image generation/edit capability
       → generate ULTRAWIDE desktop asset with expert centered in right half
       → generate dedicated mobile asset
       → source-preserving edge integration/post-process when needed
       → save both in sites/[slug]/assets/
       → identity/composition QA
       → fallback if needed
→ STATIC BUILD
→ MOBILE PASS
→ IMAGE/PERFORMANCE PASS
→ MOTION
→ IMPECCABLE QA
```

Do not finish the HTML first and bolt the hero asset on afterward. The generated assets must exist before final hero composition/CSS is locked.

## 9. QA gate — desktop

Reject/regenerate/fallback if any are true:

- desktop source is needlessly constrained to 16:9 when ultrawide would preserve the composition better;
- expert is not centered within the right half;
- expert is pinned awkwardly against the far-right edge;
- expert drifts into left copy territory;
- face/body is washed out by gradient/fog;
- expert looks like a card pasted into the background;
- left side is too busy for copy;
- identity materially differs from source;
- text/logo/UI was baked into the image;
- invented people/equipment/claims appear;
- head/torso crops or zooms aggressively at 1280/1440/ultrawide widths;
- visible rectangular canvas edges remain after integration.

## 10. QA gate — mobile

Reject/regenerate/fallback if any are true:

- asset is merely a crop of desktop;
- expert does not dominate the top half;
- waist-down is visible when avoidable;
- face is too small for first-fold recognition;
- lower half is too busy for HTML copy;
- identity materially differs from source;
- text/UI is baked into image;
- image composition forces the page to push CTA below the first fold unnecessarily.

## 11. HTML/CSS integration

Desktop ultrawide should normally use **no-zoom subject-safe rendering**.

Preferred CSS-background pattern when appropriate:

```css
.hero-section {
  position: relative;
  background-color: var(--hero-bg);
  background-image: url('assets/hero-expert-desktop.webp');
  background-size: contain;
  background-position: right center;
  background-repeat: no-repeat;
  min-height: clamp(580px, calc(100vh - var(--header-height, 105px)), 840px);
  display: flex;
  align-items: center;
  overflow: hidden;
}
```

The exact height values are heuristics. Do not stack contradictory `min-height` declarations where the latter silently overrides the former.

### Avoid breakpoint jumps

Within the desktop range, prefer fluid scaling/positioning over a chain of hard breakpoint-specific zoom/position changes.

Use a dedicated mobile art-direction switch because mobile uses a genuinely different asset/composition; avoid unnecessary intermediate desktop breakpoints that cause visible jumps.

### Copy-side readability gradient

If needed, use a gradient that resolves fully before the expert silhouette.

Example only:

```css
.hero-gradient-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    90deg,
    var(--hero-bg) 0%,
    color-mix(in srgb, var(--hero-bg) 95%, transparent) 28%,
    color-mix(in srgb, var(--hero-bg) 40%, transparent) 44%,
    transparent 54%
  );
  pointer-events: none;
}
```

Tune stops to the actual composition. The governing rule is: **the overlay must end before it crosses the expert.**

### Hero-to-section transition

For light immersive/composited heroes, a subtle bottom fade into the next section is a valid default when it removes a hard seam.

Do not force it if the composition already transitions naturally.

### Mobile integration

Use the dedicated mobile asset rather than trying to reuse the ultrawide desktop file.

A continuous image-to-copy fade is allowed/preferred when it avoids an artificial image-box + card split.

## 12. LCP / performance integration

- hero image must not be lazy-loaded;
- preload the actual desktop/mobile hero resource when it is known critical;
- if using `<img>`, use `fetchpriority="high"` on the actual LCP image when appropriate;
- if using CSS background, rely on appropriate `<link rel="preload" as="image">` rather than pretending `fetchpriority` exists on the CSS declaration;
- reserve hero dimensions/min-height to avoid layout shift;
- preserve expert facial quality before chasing an arbitrary KB target.

Compression, sharpening and super-resolution are tuning tools, not substitutes for a correctly composed source asset.

## 13. Reporting

At the end of the redesign report:

```text
Hero Mode: expert_fullscreen
Source Portrait: [path]
Hero Asset Generation: antigravity-native | source-preserving-fallback | external-provider
Desktop Architecture: ultrawide-preferred | fallback-16:9
Desktop Aspect Ratio: [ratio]
Expert Right-Half Centering: PASS | FAIL
Desktop Asset: [path + dimensions]
Mobile Asset: [path + dimensions]
Identity QA: PASS | FALLBACK USED
Desktop Composition QA: PASS
Desktop Edge Integration QA: PASS
Mobile First-Fold QA: PASS
```

Never report `antigravity-native` unless that capability was actually used.