---
name: website-core-rules
description: HARD RULES obrigatórias para qualquer site, landing page, conceito, redesign ou preview público criado pelo Prospector. Use SEMPRE junto com redesign-premium e qualquer skill que gere UI pública de cliente. Proíbe tags/pills decorativos, emojis e travessões em copy visível.
---

# Website Core Rules

Estas regras são globais, permanentes e têm precedência sobre escolhas estéticas de `gpt-taste`, `design-taste-frontend`, referências visuais e padrões de template.

Aplicam-se a qualquer UI pública criada para cliente ou prospecto, incluindo hero, header, serviços, cards, bio, galeria, CTA, footer, landing page, proposta visual e preview funcional.

Não se aplicam ao dashboard interno do Prospector, código-fonte, nomes de arquivo, slugs, URLs ou documentação técnica.

## 1. HARD RULE: nunca usar tags, pills, chips ou badges decorativos

Não use elementos de metadata em formato de cápsula, etiqueta, chip, tag, badge ou bubble em nenhum ponto do site.

Exemplo proibido acima do headline do hero:

`Ortodontia & Harmonização · Rio Claro · Jardim Portugal`

Também é proibido transformar esse conteúdo em um retângulo arredondado, cápsula com border, fundo colorido, chip ou badge.

Isto vale site-wide, não apenas para o hero.

### Alternativas permitidas

Quando a informação for realmente necessária, use uma destas soluções:

- microtexto simples sem container
- eyebrow tipográfico sem fundo e sem borda
- linha curta de texto integrada à composição
- informação incorporada naturalmente ao headline ou supporting copy
- lista textual simples quando houver múltiplos fatos
- ícone real + texto quando o ícone tiver função clara

CTA buttons e controles funcionais continuam permitidos. A proibição é contra metadata e decoração disfarçadas de componente clicável ou capsule UI.

### Regra de teste

Se remover `background`, `border` e `border-radius` fizer o elemento parecer apenas metadata normal, provavelmente ele não deveria ter sido uma pill/tag/badge.

## 2. HARD RULE: nunca usar emoji

Não use emoji em nenhum texto, botão, navegação, CTA, trust fact, contato, card, título ou elemento decorativo da UI pública.

Exemplos proibidos incluem pictogramas Unicode como telefone, localização, estrela, check, envelope, foguete, fogo, seta decorativa ou similares quando usados como emoji.

### Use ícones de verdade

Quando houver necessidade visual, use:

- SVG inline
- biblioteca de ícones já aprovada no projeto
- ícone vetorial local
- CSS simples quando apropriado

O ícone deve ser semanticamente adequado, visualmente consistente e acessível.

Não substitua emoji por outro caractere Unicode com aparência de emoji.

Para links com ícone, preserve `aria-label` ou texto acessível quando necessário.

## 3. HARD RULE: nunca usar travessões em copy pública

Não use travessão longo ou médio em textos visíveis do site:

- `—`
- `–`

Reescreva a frase usando pontuação natural:

- ponto
- vírgula
- dois-pontos
- ponto e vírgula quando apropriado
- parênteses com moderação
- quebra de frase

A solução preferida é normalmente reescrever a frase, não apenas trocar o caractere mecanicamente.

### Escopo

Esta regra vale para:

- headlines
- supporting copy
- parágrafos
- CTAs
- labels
- navegação
- captions
- testimonials quando editáveis
- metadata textual
- footer
- proposta pública

Hífens ortográficos necessários continuam permitidos. Hífens em código, CSS, nomes de classe, slugs, URLs, atributos e nomes de arquivo não são travessões de copy e não devem ser alterados.

## 4. Hero específico

Hero deve começar com composição e tipografia, não com uma coleção de UI ornaments.

Acima do headline, prefira nada. Se uma eyebrow realmente acrescentar contexto, ela deve ser texto puro e discreto, sem capsule, badge, tag, chip, bubble, ícone emoji ou container decorativo.

Evite especialmente o padrão AI-slop:

`[ pill de categoria ]`
`Headline grande`
`Supporting copy`
`[ dois ou três chips de confiança ]`

Trust facts, quando necessários, devem ser integrados de forma tipográfica, estrutural ou editorial, sem badges.

## 5. Componentes funcionais versus decoração

Não confunda esta regra com proibição de todos os elementos arredondados.

Permitido quando funcional:

- botão CTA
- input
- select
- menu
- controle de formulário
- card quando o card ajuda scanning ou agrupamento real

Proibido quando decorativo ou metadata-first:

- category chip
- location pill
- specialty badge
- trust badge estilizado como cápsula
- floating label decorativa
- mini tag acima do título
- fileira de chips de serviços

## 6. QA obrigatório antes de aprovar qualquer site

Antes do Screenshot Review e antes de publicar, faça uma revisão explícita:

```text
SITE CORE RULE QA

Decorative pills/tags/chips/badges: NONE
Emoji in public UI: NONE
Visible em dash: NONE
Visible en dash used as punctuation: NONE
Hero metadata capsule: NONE
CTA buttons/icons remain functional: PASS
```

Faça também uma busca textual no HTML final por `—` e `–` e revise qualquer ocorrência visível ao usuário.

Revise visualmente o screenshot, pois pills/tags podem existir sem nomes de classe óbvios.

Para emoji, revise tanto texto visível quanto pseudo-elements CSS `content:`.

## 7. Precedência

Se outra skill, inspiração, template, referência, componente existente ou ferramenta de design sugerir pills, chips, badges decorativos, emojis ou travessões em copy, esta skill vence.

Só altere estas regras se o usuário pedir explicitamente uma exceção para um site específico.
