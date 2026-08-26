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

## 4. Desktop — composição obrigatória

Target recomendado:

```text
1920 × 1080
16:9
```

Objetivo visual:

- full-screen hero image;
- expert na direita, ocupando aproximadamente 45–55% do quadro;
- manter pose, rosto, expressão, roupa e orientação do retrato-fonte;
- expert grande, nítido, 100% opaco e chegando visualmente à borda direita;
- metade esquerda como negative space limpo para headline/CTA HTML;
- fundo suave, levemente desfocado e pouco distrativo;
- sem texto, logo, botão, badge, UI ou lettering dentro da imagem.

Nunca gerar um portrait-card dentro de uma imagem maior.

### Prompt-base desktop

```text
Create a full-screen desktop website hero image in 16:9 using the provided real expert portrait as the identity and pose anchor.

Preserve this exact person's facial identity, approximate age, expression, hairstyle, professional clothing and pose. Do not replace, beautify into a different person, or substantially alter the subject.

Composition:
- the expert owns the right 45–55% of the frame
- keep the expert large, crisp, fully opaque and visually dominant
- the subject should extend naturally toward the right edge
- reserve the left 45–55% as calm negative space for HTML headline and CTA that will be added later
- no text inside the image

Background:
- extend/fill the scene naturally around the real portrait
- soft, restrained, slightly blurred professional atmosphere appropriate to the supplied factual business/expert context
- background must stay unobtrusive
- do not invent extra people, patients, staff, procedures, awards, prominent equipment or fake luxury architecture

Important:
- do not put a white gradient, fog or transparency over the expert
- do not fade the face, torso, shoulders, uniform/clothing or hands
- any visual softening may occur only in the environment / transition toward the left copy area
- no logos, badges, buttons, UI or typography
```

Append factual expert context after the prompt, clearly labelled as context only. Example:

```text
Expert context (factual context only; do not render as text):
Dr. Cássio Renato Lourenço Ferreira — cirurgião-dentista dedicado à ortodontia e harmonização facial [...verified summary...].
```

## 5. Mobile — composição obrigatória

Preferir asset dedicado, não crop do desktop.

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

## 7. Autonomous workflow

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
       → generate desktop asset
       → generate mobile asset
       → save both in sites/[slug]/assets/
       → identity/composition QA
       → source-preserving fallback if needed
→ STATIC BUILD
→ MOBILE PASS
→ MOTION
→ IMPECCABLE QA
```

Do not finish the HTML first and bolt the hero asset on afterward. The generated assets must exist before final hero composition/CSS is locked.

## 8. QA gate — desktop

Reject/regenerate/fallback if any are true:

- expert does not own roughly the right half;
- face/body is washed out by gradient/fog;
- expert looks like a card pasted into the background;
- left side is too busy for copy;
- identity materially differs from source;
- text/logo/UI was baked into the image;
- invented people/equipment/claims appear;
- subject is too small or does not visually reach the right edge.

## 9. QA gate — mobile

Reject/regenerate/fallback if any are true:

- asset is merely a crop of desktop;
- expert does not dominate the top half;
- waist-down is visible when avoidable;
- face is too small for first-fold recognition;
- lower half is too busy for HTML copy;
- identity materially differs from source;
- text/UI is baked into image;
- image composition forces the page to push CTA below the first fold unnecessarily.

## 10. HTML integration

Use the generated assets through `<picture>` where practical:

```html
<picture class="hero-media" aria-hidden="true">
  <source media="(max-width: 767px)" srcset="assets/hero-expert-mobile.webp">
  <img src="assets/hero-expert-desktop.webp" alt="" fetchpriority="high">
</picture>
```

If the expert image itself conveys important identity/context, use factual alt text rather than `aria-hidden`; decide case-by-case for accessibility.

Hero text remains semantic HTML on top/in an adjacent layer. Never rasterize the headline or CTA into the generated image.

## 11. Reporting

At the end of the redesign report:

```text
Hero Mode: expert_fullscreen
Source Portrait: [path]
Hero Asset Generation: antigravity-native | source-preserving-fallback | external-provider
Desktop Asset: [path + dimensions]
Mobile Asset: [path + dimensions]
Identity QA: PASS | FALLBACK USED
Desktop Composition QA: PASS
Mobile First-Fold QA: PASS
```

Never report `antigravity-native` unless that capability was actually used.

## 12. Hero Rendering Engineering — HARD RULES vs defaults

Image generation quality is only half of the hero problem. The final CSS/HTML integration must preserve the composition.

Read `design-performance-playbook.md` for the general engineering rules.

### HARD RULE — no destructive `cover`

Do not use `background-size: cover` or `object-fit: cover` merely because the asset is 16:9.

At 1280, 1440 and wider desktop widths, verify that:

- the expert's head/torso remains intact;
- the expert still owns the intended right-side territory;
- copy negative space remains usable;
- scale does not become an accidental zoom.

If `cover` fails, switch to a subject-safe rendering strategy:

- `<picture>`/`<img>` with controlled dimensions/position;
- `contain` + right anchoring;
- dedicated art-directed breakpoint asset;
- source-preserving compositing.

`contain` is a preferred option for many expert heroes, **not a universal law**.

### Copy overlay boundary

Any readability gradient belongs behind the copy/environment only. Its transparent end must resolve before it crosses the expert silhouette.

Do not use a global white overlay over the image.

### Edge integration

If the hero asset does not naturally fill the container and its rectangular boundaries become visible, dissolve the image edges into the page background using subtle tonal continuation/vignette/gradient masks.

Do this only when needed. Do not force a vignette onto naturally full-bleed imagery.

### Mobile continuity

For immersive mobile expert heroes, prefer continuous visual flow between the upper expert image and lower HTML copy instead of a visibly clipped image-box + solid-card split.

A soft bottom fade into the page background is a valid default when it improves continuity, but its height/color must be tuned to the actual asset.

### LCP integration

- hero image must not be lazy-loaded;
- use `fetchpriority="high"` for the actual LCP image when appropriate;
- preload dedicated desktop/mobile hero resources when they are known critical;
- preserve intrinsic dimensions/aspect ratio to avoid layout shift.

Compression numbers are tuning heuristics. Preserve expert facial quality before chasing an arbitrary KB target.
