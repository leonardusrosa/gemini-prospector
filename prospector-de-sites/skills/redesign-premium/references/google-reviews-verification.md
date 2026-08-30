# Google Reviews Verification Protocol

Use este protocolo em TODO redesign/novo site quando existir um Google Business Profile / Google Maps plausível para o lead.

Objetivo: eliminar leituras ambíguas, evitar dados stale do CRM e impedir que avaliações reais sejam silenciosamente omitidas por falha de coleta.

## 1. Identidade do perfil antes de ler qualquer número

Antes de aceitar nota, quantidade ou texto de review, confirme que a tela/painel pertence ao perfil correto.

A evidência deve combinar, na medida em que estiver disponível:

- nome exibido no Google
- endereço/cidade
- telefone/site oficial
- URL canônica do Google Maps / Google Business Profile
- `place_id`, `cid` ou outro identificador estável quando acessível

Não misture dados de unidades, profissionais, clínicas homônimas ou perfis antigos.

### Regra de identidade

`rating`, `reviewCount` e os reviews selecionados DEVEM vir do mesmo perfil identificado.

Se houver dúvida sobre qual perfil é o correto, marque `PROFILE_CONFLICT` e pare a coleta. Não use o CRM para desempatar automaticamente.

## 2. Fonte atual vence cache

Para página pública, a leitura do Google feita durante a pesquisa atual tem precedência sobre:

- valores antigos do CRM
- snippets de buscas antigas
- screenshots anteriores
- caches locais
- dados salvos de outro passe

O CRM pode ajudar a localizar o perfil, mas NÃO é fonte canônica de nota/quantidade para renderização pública.

Sempre registre `collectedAt`.

Se o usuário verificar explicitamente a leitura live do perfil correto, essa confirmação pode validar o aggregate atual. Ela não autoriza inventar ou reconstruir textos individuais de reviews.

## 3. Leitura inequívoca do aggregate

No mesmo perfil, capture explicitamente:

- `aggregateRating`
- `reviewCount`
- nome do perfil
- URL/identificador do perfil
- timestamp da coleta

Não derive `reviewCount` somando páginas, snippets ou resultados de busca.

Não use um número de avaliações de um snippet e a nota de outro painel.

Exemplo de evidência:

```json
{
  "profileName": "Instituto Ferreira Odontologia e Harmonização Orofacial",
  "profileUrl": "<google-maps-url>",
  "placeIdOrCid": "<quando disponível>",
  "aggregateRating": 5.0,
  "reviewCount": 36,
  "collectedAt": "2026-08-30T...",
  "aggregateEvidence": "live-google-profile"
}
```

## 4. Coleta obrigatória de reviews para prova social

Se o perfil correto possui múltiplas avaliações textuais positivas, coletar no mínimo **3 reviews utilizáveis**, com alvo de **4 a 6** para a seção pública.

Para cada review, preservar:

- nome público do avaliador
- estrelas daquele review
- texto verbatim
- data ou label temporal exatamente como o Google disponibiliza
- vínculo com o mesmo perfil verificado

Preferir reviews:

- específicos e informativos
- com texto suficiente para transmitir experiência real
- relevantes ao serviço/experiência do negócio
- sem depender de informação sensível desnecessária

Não selecionar apenas reviews porque são curtos e convenientes.

## 5. Ordem de tentativa de coleta

Quando reviews existem, não omita a seção na primeira dificuldade técnica. Tente, nesta ordem:

1. perfil Google Maps/GBP live no navegador e painel de avaliações;
2. rota/visualização alternativa do mesmo perfil Google;
3. outra forma de leitura live do MESMO perfil que preserve autoria, estrelas e texto;
4. evidência fornecida pelo usuário, como screenshots/cópia do painel do Google, validada contra o mesmo perfil.

Nunca substituir Google Reviews por depoimentos inventados, agregadores desconhecidos ou conteúdo de outro perfil.

## 6. Estados de verificação

### `VERIFIED_STRONG`

Exige:

- identidade inequívoca do perfil;
- aggregate atual verificado;
- pelo menos 3 reviews textuais positivos verificáveis do mesmo perfil.

Resultado: **seção de prova social obrigatória**.

O gate legado pode continuar emitindo `CAROUSEL REQUIRED: YES`, mas a implementação visual pode ser masonry quando essa for a composição superior.

### `VERIFIED_AGGREGATE_ONLY`

Identidade + nota + quantidade estão confirmadas, mas ainda não há pelo menos 3 textos individuais verificáveis.

Se o perfil possui múltiplas avaliações textuais visíveis, isto é um **bloqueador de coleta**, não justificativa para omitir silenciosamente a seção.

Resultado: QA de Google Reviews NÃO pode ser marcado como concluído até resolver a coleta ou registrar uma limitação externa real e explícita para revisão humana.

### `PROFILE_CONFLICT`

Há conflito de identidade entre fontes/perfis.

Resultado: não publicar aggregate nem reviews até resolver o perfil correto.

### `NO_USABLE_REVIEWS`

Perfil correto foi verificado, mas não há reviews textuais utilizáveis suficientes para uma seção rica.

Resultado: não inventar cards. Uma ou duas avaliações reais podem aparecer em formato estático, se úteis.

## 7. Conflitos entre números

Exemplo:

- CRM: 4,9 / 45
- Google live no perfil correto: 5,0 / 36

Não faça média, não escolha o maior e não preserve o CRM por conveniência.

Se a identidade do perfil live estiver inequívoca, a leitura live atual é a fonte pública canônica. Registre o conflito internamente e use o valor live.

## 8. Evidência local obrigatória

Durante a pesquisa, salvar um artefato interno, fora do deploy público, por exemplo:

`sites/[slug]/research/google-reviews-evidence.json`

Estrutura recomendada:

```json
{
  "status": "VERIFIED_STRONG",
  "profileName": "...",
  "profileUrl": "...",
  "placeIdOrCid": "...",
  "aggregateRating": 5.0,
  "reviewCount": 36,
  "collectedAt": "...",
  "reviews": [
    {
      "author": "...",
      "rating": 5,
      "text": "...",
      "dateLabel": "..."
    }
  ]
}
```

Não copie screenshot/evidência privada desnecessária para o bundle público.

## 9. Build gate

Antes do design final, declarar:

```text
GOOGLE PROFILE IDENTIFIED: PASS/FAIL
AGGREGATE CURRENTLY VERIFIED: PASS/FAIL
AGGREGATE RATING: <valor>
REVIEW COUNT: <valor>
VERIFIED TEXT REVIEWS: <n>
GOOGLE REVIEWS STATUS: VERIFIED_STRONG / VERIFIED_AGGREGATE_ONLY / PROFILE_CONFLICT / NO_USABLE_REVIEWS
CAROUSEL REQUIRED: YES/NO
```

Se `VERIFIED_STRONG` e houver pelo menos 3 reviews:

`CAROUSEL REQUIRED = YES`

Interpretação atual: o site precisa renderizar a prova social verificada; `masonry` pode satisfazer o gate visual quando for melhor que um carousel.

## 10. Renderização

Quando a seção for obrigatória:

- usar os textos fiéis coletados;
- não simular widget oficial do Google;
- NÃO mencionar `Google`, `Google Reviews`, `Avaliações no Google` ou equivalente em título, eyebrow, subtítulo, descrição, CTA, aggregate label ou qualquer outro texto visível da seção;
- usar heading natural de prova social, por exemplo `O que nossos clientes dizem`, adaptado naturalmente ao idioma/contexto do negócio;
- aggregate deve aparecer de forma neutra, por exemplo `5,0 · 36 avaliações`;
- é permitido um pequeno logo/ícone do Google dentro do card individual, discreto e secundário, apenas como indicação visual de origem;
- não usar o logo como badge, selo, heading, faixa ou elemento dominante;
- a proveniência Google completa permanece no evidence record interno e não precisa ser repetida como copy pública;
- estrelas individuais refletem o review individual;
- truncamento deve ser fiel e não mudar o sentido;
- responsivo, teclado, touch e reduced-motion conforme Website Core Rules.

### HARD RULE de copy da seção

A seção de prova social deve parecer uma parte natural do site do cliente, não uma seção promocional da plataforma de origem.

Permitido:

- `O que nossos clientes dizem`
- `Experiências de quem já passou por aqui`
- outro título natural e específico ao contexto
- pequeno logo do Google dentro do review card

Proibido:

- `Google Reviews`
- `Avaliações no Google`
- `O que dizem no Google`
- `Veja nossas avaliações no Google`
- qualquer headline/subheadline/label visível que transforme Google no tema da seção

### HARD RULE avançada de sizing/layout: Masonry testimonial grid

Para depoimentos de comprimentos variados, o padrão preferido é uma **masonry/Pinterest-style grid** de cards com alturas intrínsecas diferentes.

Direção visual de referência:

> Create a testimonial section as a masonry/Pinterest-style grid of varied-height testimonial cards. Match the visual style, colors, typography, and overall aesthetic of the existing UI.

A referência descreve composição, não autoriza copiar estilos genéricos que conflitem com o site. O masonry deve parecer nativo ao design existente.

#### Gatilhos para usar masonry

Prefira masonry quando:

- houver 4 ou mais reviews com comprimentos variados;
- o maior card ficar cerca de 35% ou mais alto que o menor/mediano;
- a disposição em linha/carrossel criar corredores de espaço vazio relevantes;
- o conjunto puder usar melhor a área disponível encaixando cards curtos sob cards mais altos.

Se houver apenas 3 reviews ou alturas muito semelhantes, uma grid simples pode ser suficiente. Carousel deve ser usado apenas quando a navegação horizontal tiver valor real, não como padrão automático.

#### Estrutura visual esperada

- desktop: normalmente 3 colunas;
- tablet: normalmente 2 colunas;
- mobile: 1 coluna;
- cada card: `height:auto`;
- largura consistente dentro de cada breakpoint;
- gap visual consistente;
- cards seguintes sobem para ocupar espaço abaixo de cards curtos, formando o efeito masonry;
- sem alinhamento obrigatório por linhas horizontais;
- aggregate/heading continuam fora do masonry e alinhados ao sistema visual da página.

#### Implementação técnica preferida

Preserve a ordem DOM e implemente masonry com uma estratégia que não destrua a leitura semântica.

Preferência:

1. CSS Grid como base;
2. row sizing pequeno (`grid-auto-rows`) + cálculo de `grid-row-end: span N` medido por card, ou outra implementação equivalente;
3. `ResizeObserver` para recalcular spans quando fontes, viewport ou `Ler mais` alterarem altura;
4. fallback natural para grid/1 coluna se JavaScript falhar.

Evite `column-count` para testimonials quando a ordem visual por colunas divergir da ordem DOM e confundir teclado/leitor de tela.

Não usar posicionamento absoluto manual por coordenadas salvo implementação de layout comprovadamente acessível e resiliente.

#### Card anatomy

Cada card mantém:

- estrelas verificadas;
- texto integral ou expansão acessível;
- nome;
- data/label quando verificada;
- pequeno marcador de proveniência permitido;
- footer imediatamente após o conteúdo.

Não usar:

```css
height: 100%;
min-height: <valor para igualar>;
justify-content: space-between;
align-stretch;
```

quando o objetivo for fazer todos os cards parecerem da mesma altura.

#### Ordem e interação

- DOM order = source of truth;
- tab order = DOM order;
- leitor de tela = DOM order;
- mobile em 1 coluna = DOM order literal;
- não reordenar depoimentos dinamicamente apenas para produzir encaixe visual melhor;
- se houver `Ler mais`, foco permanece previsível e o card expande no lugar;
- masonry recalcula sem overlap, clipping ou salto destrutivo de foco.

#### QA visual obrigatório

FAIL se houver:

- grandes blocos vazios dentro de cards;
- grandes corredores vazios que uma composição masonry deveria preencher;
- cards sobrepostos ou cortados;
- ordem visual/teclado incoerente;
- layout quebrando após resize ou expansão;
- masonry com aparência genérica que não combina com o UI existente.

PASS quando:

- alturas variadas parecem intencionais;
- o espaço vertical é utilizado eficientemente;
- cards curtos encaixam naturalmente sob cards de outras colunas;
- largura/gaps permanecem organizados;
- a hierarquia e estética continuam pertencendo ao site do cliente;
- desktop/tablet/mobile mantêm boa leitura e acessibilidade.

### Compatibilidade com gate legado

Até o validator ser renomeado, trate:

`CAROUSEL REQUIRED: YES`

como:

`VERIFIED REVIEW DISPLAY REQUIRED: YES`

A escolha final entre masonry, grid e carousel é uma decisão de UI orientada pelo conteúdo e pelas regras acima.

## 11. Não confundir prova social com cold outreach

A confirmação de rating/review count para a página não significa que esses números devam ser colocados automaticamente no primeiro WhatsApp frio. As regras de outreach continuam independentes e podem proibir números stale ou desnecessários no cold contact.
