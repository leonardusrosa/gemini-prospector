---
name: website-core-rules
description: HARD RULES obrigatórias para qualquer site, landing page, conceito, redesign ou preview público criado pelo Prospector. Use SEMPRE junto com redesign-premium e qualquer skill que gere UI pública de cliente. Proíbe tags/pills decorativos, emojis e travessões em copy visível, limita o hero a um único botão CTA, exige CTAs contextuais sem repetição mecânica de wording e aplica sentence case natural ao PT-BR.
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

## 4. HARD RULE: hero tem exatamente um botão CTA

Todo hero deve conter **um único botão CTA**.

Não use dois ou mais botões de ação lado a lado ou empilhados no hero.

Exemplos proibidos:

- `Agendar pelo WhatsApp` + `Ligar agora`
- `Solicitar orçamento` + `Conhecer serviços`
- CTA primário + CTA secundário em estilo outline
- dois botões diferentes apontando para canais de contato distintos

### Como escolher

Escolha a ação de maior prioridade comercial e deixe apenas ela como botão do hero.

As demais ações devem ser movidas para:

- header
- navegação
- seção de contato
- seção imediatamente abaixo da dobra
- link textual discreto somente quando realmente necessário e sem competir visualmente com o CTA principal

Não transforme a segunda ação em outro elemento com aparência de botão para contornar esta regra.

Ícones sociais ou de contato no header não contam como CTA do hero, desde que estejam fora do hero e cumpram função clara.

### Mobile

A mesma regra vale no mobile: exatamente um botão CTA na primeira composição do hero.

Se faltar espaço, preserve primeiro:

1. identidade/visual principal
2. headline
3. supporting copy curta
4. CTA principal único

Remova ações secundárias antes de reduzir ou duplicar o CTA.

## 5. HARD RULE: evitar redundância de wording nos CTAs

Não repita mecanicamente o mesmo texto de botão em várias seções da página.

Exemplo ruim:

- hero: `Agendar no WhatsApp`
- serviços: `Agendar no WhatsApp`
- bio: `Agendar no WhatsApp`
- contato: `Agendar no WhatsApp`

Quatro botões com o mesmo wording deixam a página repetitiva, genérica e com aparência de template.

### Regra de contexto

Cada CTA deve refletir o contexto da seção e a próxima ação real do usuário.

Se todos os botões levarem ao mesmo canal, como WhatsApp, ainda assim varie a copy de forma contextual e honesta.

Exemplos possíveis, apenas quando factualmente adequados ao contexto:

- hero: `Agendar avaliação`
- seção de ortodontia: `Conversar sobre ortodontia`
- bio do profissional: `Falar com a equipe`
- seção de dúvidas: `Tirar uma dúvida`
- contato final: `Chamar no WhatsApp`

Não use sinônimos aleatórios só para parecer diferente. A variação deve comunicar intenção, etapa ou assunto diferente.

### Consistência sem repetição mecânica

É aceitável repetir um CTA em um ponto estrutural persistente, como header ou floating CTA, quando a consistência funcional justificar. Mesmo assim, evite espalhar o mesmo wording por todas as seções.

Antes de adicionar um novo botão, pergunte:

1. este CTA acrescenta uma próxima ação relevante?
2. o texto corresponde ao contexto da seção?
3. já existe outro botão com wording idêntico muito próximo?
4. a página está repetindo o canal em vez de avançar a narrativa?

Se a resposta indicar redundância, reescreva ou remova o CTA.

Nunca prometa uma ação diferente daquilo que o link realmente faz. Um botão que abre WhatsApp não deve sugerir confirmação imediata de consulta se isso não estiver garantido.

## 6. HARD RULE: PT-BR usa sentence case natural, não Title Case inglês

Para interfaces e copy em português do Brasil, use capitalização natural de PT-BR.

Por padrão, títulos, subtítulos, labels, itens de navegação, botões e headings devem usar **sentence case**:

- primeira palavra com inicial maiúscula quando apropriado
- nomes próprios, marcas, siglas e termos oficialmente grafados preservam sua capitalização
- demais palavras permanecem em minúsculas conforme a norma natural do português

Exemplos corretos:

- `Conheça nossos tratamentos`
- `Tecnologia para cada etapa do seu tratamento`
- `Agendar avaliação`
- `Falar com a equipe`
- `Ortodontia e harmonização orofacial`

Exemplos a evitar quando usados como capitalização de interface:

- `Conheça Nossos Tratamentos`
- `Tecnologia Para Cada Etapa Do Seu Tratamento`
- `Agendar Avaliação`
- `Falar Com A Equipe`

Não replique automaticamente Title Case de referências, templates ou copy em inglês.

### Exceções legítimas

Preserve capitalização oficial ou necessária em:

- nomes próprios
- marcas
- siglas e acrônimos, como `ABOR`, `WFO`, `CRO`
- produtos cuja grafia oficial exija maiúsculas, como `Invisalign`
- início de frase
- abreviações convencionais

### Caixa alta visual

Evite frases ou headings inteiros em `ALL CAPS` como recurso editorial padrão em PT-BR.

Se houver microtexto muito curto visualmente estilizado por CSS com `text-transform: uppercase`, use apenas quando houver razão clara de hierarquia visual e a leitura continuar natural. Não transforme frases completas, CTAs ou headings principais em caixa alta.

A preferência é que o texto-fonte no HTML continue escrito em sentence case mesmo quando um micro-rótulo aprovado receber transformação visual por CSS.

## 7. Hero específico

Hero deve começar com composição e tipografia, não com uma coleção de UI ornaments.

Acima do headline, prefira nada. Se uma eyebrow realmente acrescentar contexto, ela deve ser texto puro e discreto, sem capsule, badge, tag, chip, bubble, ícone emoji ou container decorativo.

Evite especialmente o padrão AI-slop:

`[ pill de categoria ]`
`Headline grande`
`Supporting copy`
`[ dois ou três chips de confiança ]`

Trust facts, quando necessários, devem ser integrados de forma tipográfica, estrutural ou editorial, sem badges.

O hero deve manter um único CTA principal, conforme a regra anterior.

## 8. Componentes funcionais versus decoração

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

## 9. QA obrigatório antes de aprovar qualquer site

Antes do Screenshot Review e antes de publicar, faça uma revisão explícita:

```text
SITE CORE RULE QA

Decorative pills/tags/chips/badges: NONE
Emoji in public UI: NONE
Visible em dash: NONE
Visible en dash used as punctuation: NONE
Hero metadata capsule: NONE
Hero CTA buttons: EXACTLY 1
CTA button functional: PASS
Repeated CTA wording across distinct sections: NONE or JUSTIFIED
CTA wording matches section context and destination: PASS
PT-BR headings/buttons/labels use natural sentence case: PASS
Unjustified Title Case in PT-BR: NONE
Unjustified ALL CAPS phrases/headings in PT-BR: NONE
```

Faça também uma busca textual no HTML final por `—` e `–` e revise qualquer ocorrência visível ao usuário.

Revise visualmente o screenshot, pois pills/tags podem existir sem nomes de classe óbvios.

Para emoji, revise tanto texto visível quanto pseudo-elements CSS `content:`.

Conte também os elementos clicáveis com aparência de botão dentro do hero. O total deve ser exatamente 1.

Liste os textos de todos os CTAs da página e revise repetições. Se houver wording idêntico em seções diferentes, ele deve ter justificativa funcional clara ou ser variado/removido.

Para páginas em PT-BR, liste também headings, CTAs e labels relevantes e verifique se a capitalização segue sentence case natural. Corrija Title Case importado do inglês e caixa alta sem justificativa.

## 10. Precedência

Se outra skill, inspiração, template, referência, componente existente ou ferramenta de design sugerir pills, chips, badges decorativos, emojis, travessões em copy, múltiplos botões CTA no hero, repetição mecânica do mesmo CTA ou Title Case inglês em PT-BR, esta skill vence.

Só altere estas regras se o usuário pedir explicitamente uma exceção para um site específico.
