---
name: expert-hero-assets
description: Use automaticamente como subskill durante redesign/criação quando `redesign-premium` classificar o hero como `expert_fullscreen` e existir uma foto real, clara e verificada do profissional. Gera/produz assets de hero separados para desktop e mobile preservando identidade, preferindo geração/edição nativa disponível no Google Antigravity antes de qualquer API externa paga. Acione também quando o usuário pedir hero com expert à direita no desktop ou expert no topo no mobile.
---

# Expert Hero Assets

Esta skill é uma etapa de produção visual do `redesign-premium`, não um substituto da direção de design.

Leia e siga integralmente:

`../redesign-premium/references/expert-hero-generation.md`

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

## Desktop

- target 1920×1080 / 16:9 quando suportado;
- expert na direita, ~45–55% do quadro;
- exact real identity/pose anchor;
- expert fully opaque e dominante;
- left half calma para HTML copy;
- background suave/desfocado/contextual;
- nenhum texto/logo/UI dentro da imagem;
- nenhum gradient/fog sobre o expert.

## Mobile

- target 1080×1920 / 9:16 quando suportado;
- composição própria, não crop do desktop;
- expert grande no top ~50–55%;
- head + upper body;
- **não mostrar waist-down**;
- lower ~45–50% calma para HTML copy;
- nenhum texto/logo/UI dentro da imagem.

## Identity QA

Identidade tem prioridade sobre estética.

Se o output alterar materialmente rosto/idade/expression/pose:

1. rejeite o output;
2. preserve os pixels do expert original;
3. gere/construa apenas background/environment quando possível;
4. composite o expert real sem feather/fade no sujeito;
5. nunca use uma pessoa sintética parecida como substituta.

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
   - identity QA;
2. integrar os assets no hero via `<picture>` ou estratégia equivalente;
3. manter headline, supporting copy, CTA e trust facts como HTML semântico;
4. continuar para mobile-specific pass, motion e Impeccable QA.

## Stop conditions

Não bloquear todo o redesign apenas porque geração nativa não existe.

Se a capacidade nativa não estiver disponível e nenhum provider externo tiver sido explicitamente configurado:

- use fonte real + background source-preserving/CSS/compositing;
- mantenha as regras de expert dominance;
- registre `Hero Asset Generation: source-preserving-fallback`.

Nunca fingir que uma imagem foi gerada nativamente quando não foi.