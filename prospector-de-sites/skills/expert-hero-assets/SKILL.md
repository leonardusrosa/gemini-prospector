---
name: expert-hero-assets
description: Use automaticamente como subskill durante redesign/criação quando `redesign-premium` classificar o hero como `expert_fullscreen` e existir uma foto real, clara e verificada do profissional. Gera/produz assets de hero separados para desktop e mobile preservando identidade, preferindo geração/edição nativa disponível no Google Antigravity antes de qualquer API externa paga. Acione também quando o usuário pedir hero com expert à direita no desktop ou expert no topo no mobile.
---

# Expert Hero Assets

Esta skill é uma etapa de produção visual do `redesign-premium`, não um substituto da direção de design.

Leia e siga integralmente:

```text
../redesign-premium/references/expert-hero-generation.md
../redesign-premium/references/hero-image-quality.md
```

## Trigger obrigatório

Quando TODOS forem verdadeiros:

- `Hero Mode = expert_fullscreen`;
- negócio genuinely expert-led;
- retrato real/verificado disponível;
- rosto e pose utilizáveis;

execute esta etapa **antes de fechar o HTML/CSS final do hero**.

## Capability order

```text
Antigravity-native image generation/editing
→ source-preserving fallback
→ external API/provider apenas se explicitamente configurado pelo usuário
```

### Billing guardrail

O fluxo padrão NÃO deve:

- exigir `GEMINI_API_KEY`;
- pedir uma API key só porque existe um retrato;
- ativar API paga silenciosamente;
- tratar Google AI Pro/Antigravity quota como se fosse automaticamente Gemini API billing.

Primeiro detecte se a sessão atual do Antigravity disponibiliza geração/edição de imagem capaz de usar a imagem-fonte e salvar o resultado no workspace.

Se sim, use essa capacidade.

Se não, use o fallback source-preserving ou reporte que a geração nativa não está disponível. Só use provider externo quando ele já estiver configurado/explicitamente autorizado.

## Outputs

Produza:

```text
sites/[slug]/assets/hero-expert-desktop.webp
sites/[slug]/assets/hero-expert-mobile.webp
```

Não sobrescreva o retrato-fonte.

## Desktop — preferred ultrawide architecture

Para `expert_fullscreen`, **prefira um asset desktop ultrawide art-directed em vez de 16:9** quando o layout tiver copy à esquerda e o expert à direita.

- aspect ratio preferencial: aproximadamente `2.3:1–2.6:1` quando suportado;
- resolução de classe 3K/4K é recomendada quando útil;
- **para qualidade final, prefira aproximadamente `3500–4500+ px` de largura quando a fonte/gerador suportar isso de forma real**;
- `4200×1728` é um benchmark forte de produção, não requisito;
- **o expert deve ficar centrado dentro da metade direita do canvas** — visual center aproximadamente em `x ≈ 75%` do quadro;
- não empurre o expert contra a borda direita e não deixe o sujeito derivar para o centro da página;
- preserve breathing room suficiente ao redor do sujeito para que widescreen/contain não corte cabeça/torso;
- exact real identity/pose anchor;
- expert fully opaque, sharp e dominante;
- metade esquerda calma para HTML copy;
- background suave/desfocado/contextual;
- nenhum texto/logo/UI dentro da imagem;
- nenhum gradient/fog sobre o expert.

**16:9 deixa de ser o default desktop para este modo.** Use 16:9 apenas se a composição real funcionar melhor ou se a capacidade de geração não suportar um ultrawide útil.

### HARD RULE — high-quality source/output

Não gere um hero pequeno/soft para depois ampliá-lo no CSS.

Qualidade deve ser avaliada visualmente, não apenas pelo número de pixels:

- rosto, cabelo, roupa e bordas importantes devem permanecer nítidos em 1440p e wide-screen review;
- compressão não pode criar smearing, ringing, halos, blockiness ou perda material de detalhe facial;
- não faça upscale destrutivo de uma fonte ruim só para atingir 4K nominal;
- prefira uma fonte first-party melhor, enhancement source-preserving ou geração de referência que preserve identidade;
- mantenha qualidade facial antes de perseguir um limite arbitrário de KB.

Benchmark de referência, não hard limit:

```text
4200 × 1728 WebP
~417 KB
ultrawide expert hero
```

Um hero em torno de `400–500 KB` pode ser aceitável quando a qualidade visual justifica o payload e o carregamento LCP está corretamente otimizado.

### Edge integration / post-process

Quando o ultrawide for renderizado com `contain` e puder revelar suas bordas:

- dissolva as bordas visíveis no background da página com feather/tonal continuation;
- 4-edge feathering é uma técnica recomendada quando necessária;
- o feather deve atuar no **ambiente/bordas do canvas**, nunca sobre rosto, corpo ou roupa do expert;
- mantenha o expert fora das zonas de feather;
- valores de fade em pixels, Lanczos, sharpening e WebP quality são heurísticas de implementação, não tokens universais.

## Mobile

- target 1080×1920 / 9:16 quando suportado;
- composição própria, não crop do desktop;
- expert grande no top ~50–55%;
- head + upper body;
- **não mostrar waist-down**;
- lower ~45–50% calma para HTML copy;
- nenhum texto/logo/UI dentro da imagem;
- usar resolução suficiente para nitidez HiDPI; `1080px` de largura é um baseline útil, não teto;
- não reutilizar um crop mobile de baixa qualidade do ultrawide desktop.

## Identity QA

Identidade tem prioridade sobre estética.

Se o output alterar materialmente rosto/idade/expression/pose:

1. rejeite o output;
2. preserve os pixels do expert original;
3. gere/construa apenas background/environment quando possível;
4. composite o expert real sem feather/fade no sujeito;
5. nunca use uma pessoa sintética parecida como substituta.

## Quality QA — obrigatório

Antes de aceitar o hero desktop, confirme:

```text
Source/output resolution: PASS
Large-screen sharpness: PASS
Expert facial detail: PASS
Hair/clothing edge detail: PASS
Compression artifacts: NONE MATERIAL
Oversharpening/halos: NONE MATERIAL
Ultrawide composition: PASS
Expert Right-Half Centering: PASS
No destructive upscale: PASS
LCP/preload integration: PASS
```

Se qualquer item crítico falhar, reprocessar, regenerar ou usar fallback antes de concluir a página.

## Factual visual safety

Não invente:

- staff;
- patients;
- procedures;
- prominent clinical equipment;
- awards;
- credentials;
- luxury architecture;
- business facts não verificados.

O contexto textual serve para orientar atmosfera, não para renderizar claims.

## Integration

Após gerar/validar assets:

1. registrar no `design-read.md`:
   - `Hero Asset Generation`;
   - source portrait path;
   - desktop/mobile output paths;
   - desktop aspect ratio;
   - desktop dimensions e encoded size quando mensuráveis;
   - `Expert Right-Half Centering: PASS | FAIL`;
   - `Large-Screen Sharpness QA: PASS | FAIL`;
   - `Facial Detail QA: PASS | FAIL`;
   - `Compression Artifact QA: PASS | FAIL`;
   - `No Destructive Upscale: PASS | FAIL`;
   - identity QA;
2. para desktop ultrawide, preferir integração fluida/subject-safe (`contain`, controlled `<img>`/`<picture>` ou equivalente), evitando `cover` destrutivo;
3. manter headline, supporting copy, CTA e trust facts como HTML semântico;
4. continuar para mobile-specific pass, image/performance pass, motion e Impeccable QA.

## Stop conditions

Não bloquear todo o redesign apenas porque geração nativa não existe.

Se a capacidade nativa não estiver disponível e nenhum provider externo tiver sido explicitamente configurado:

- use fonte real + background source-preserving/CSS/compositing;
- mantenha as regras de expert dominance, right-half centering e quality QA;
- registre `Hero Asset Generation: source-preserving-fallback`.

Nunca fingir que uma imagem foi gerada nativamente quando não foi.