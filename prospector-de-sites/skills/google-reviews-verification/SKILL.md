---
name: google-reviews-verification
description: HARD GATE para Google Reviews. Use em TODO site, redesign, novo conceito ou QA público criado pelo Prospector quando existir ou puder existir Google Business Profile/Google Maps do lead. Identifica inequivocamente o perfil, lê aggregate atual, coleta reviews textuais do mesmo perfil e torna a seção de prova social obrigatória quando houver 3+ reviews verificáveis. Nunca permita omissão silenciosa por falha de scraping/coleta.
---

# Google Reviews Verification

Esta skill é obrigatória junto de `website-core-rules` e `redesign-premium` sempre que o lead possuir ou puder possuir um Google Business Profile.

Leia e execute integralmente:

`../redesign-premium/references/google-reviews-verification.md`

Valide o evidence record com:

`prospector-de-sites/google_reviews_evidence.py`

## Hard gate

Antes de concluir o site, declarar:

```text
GOOGLE PROFILE IDENTIFIED: PASS/FAIL
AGGREGATE CURRENTLY VERIFIED: PASS/FAIL
AGGREGATE RATING: <valor>
REVIEW COUNT: <valor>
VERIFIED TEXT REVIEWS: <n>
GOOGLE REVIEWS STATUS: VERIFIED_STRONG / VERIFIED_AGGREGATE_ONLY / PROFILE_CONFLICT / NO_USABLE_REVIEWS
CAROUSEL REQUIRED: YES/NO
```

`CAROUSEL REQUIRED` é mantido por compatibilidade com o validator/gate existente. Na renderização, uma seção masonry acessível pode satisfazer essa exigência quando o conteúdo tiver alturas muito diferentes e masonry for a solução visual superior.

### VERIFIED_STRONG

Perfil correto inequívoco + aggregate atual + pelo menos 3 reviews textuais positivos verificáveis do mesmo perfil.

Resultado obrigatório:

`CAROUSEL REQUIRED: YES`

O site NÃO pode passar QA nem deploy final sem uma apresentação pública das avaliações verificadas. A apresentação pode ser carrossel ou masonry conforme a regra de layout abaixo.

### VERIFIED_AGGREGATE_ONLY

Nota/quantidade estão confirmadas, mas ainda faltam 3 reviews textuais verificáveis.

Quando o perfil contém várias avaliações, isso é um bloqueador de coleta. NÃO é permissão para omitir silenciosamente a seção.

Tente as rotas de coleta previstas no protocolo e, se uma limitação externa real impedir a leitura, pare para revisão humana.

### PROFILE_CONFLICT

Não publique nota, contagem ou reviews até resolver inequivocamente o perfil correto.

### NO_USABLE_REVIEWS

Somente quando o perfil correto foi de fato inspecionado e não existem reviews textuais suficientes. Nunca use este estado como fallback de scraping falho.

## Fonte canônica

A leitura live atual do perfil correto vence CRM/cache/snippet antigo. O CRM serve para localização, não como fonte pública canônica da nota e quantidade.

Se houver conflito, registre-o e use a leitura live somente após confirmar a identidade do perfil.

## Proibição de omissão silenciosa

Se o negócio possui múltiplas avaliações Google positivas visíveis e o sistema ainda não conseguiu capturar pelo menos 3 textos, o resultado correto é:

`GOOGLE REVIEWS QA: BLOCKED`

Nunca:

`reviews não extraídas -> omitir seção -> PASS`

## HARD RULE de apresentação pública

A fonte Google é parte da verificação e da proveniência interna, NÃO da mensagem principal da seção pública.

Na UI pública da seção de avaliações:

- NÃO usar `Google Reviews`, `Avaliações no Google`, `O que dizem no Google`, `Veja nossas avaliações no Google` ou qualquer equivalente como título, eyebrow, subtítulo, descrição, CTA ou label de aggregate;
- usar título natural de prova social, específico ao idioma e ao negócio, por exemplo `O que nossos clientes dizem`, `Experiências de quem já passou por aqui` ou outra formulação natural adequada ao contexto;
- o aggregate pode aparecer de forma neutra, por exemplo `5,0 · 36 avaliações`, sem texto visível dizendo `Google`;
- é permitido um pequeno logotipo/ícone do Google dentro do card da avaliação, de forma discreta e secundária, apenas para indicar origem;
- não transformar o logo em badge, selo, heading, faixa de marca ou elemento dominante;
- não simular widget oficial do Google;
- a proveniência completa continua registrada no evidence record interno mesmo quando a UI pública é source-neutral.

Esta regra é HARD RULE e vale para todos os sites futuros e revisões de sites existentes.

## HARD RULE avançada de layout dos testimonial/review cards

Quando os depoimentos possuem comprimentos significativamente diferentes, prefira **masonry/Pinterest-style grid de cards com alturas variadas** em vez de uma fileira rígida ou carrossel que deixe grandes vazios.

Princípio visual:

`Create a testimonial section as a masonry/Pinterest-style grid of varied-height testimonial cards. Match the visual style, colors, typography, and overall aesthetic of the existing UI.`

### Quando usar masonry

Masonry é o padrão preferido quando qualquer uma destas condições aparecer no desktop/tablet:

- diferença visual clara entre reviews curtos, médios e longos;
- o maior card fica aproximadamente 35% ou mais alto que os menores;
- uma linha/carrossel deixa grandes áreas vazias abaixo de cards curtos;
- existem 4+ reviews e o conjunto se beneficia de ocupar verticalmente o espaço disponível.

Se as alturas forem próximas e a navegação horizontal fizer sentido, carrossel continua aceitável.

### Comportamento obrigatório do masonry

- cada card mantém altura intrínseca/`auto` conforme conteúdo e metadata;
- cards ocupam os espaços verticais disponíveis como uma composição Pinterest-style, sem criar buracos artificiais grandes;
- largura/colunas consistentes por breakpoint, tipicamente 3 desktop, 2 tablet e 1 mobile;
- gaps horizontais e verticais consistentes;
- footer imediatamente após o review com espaçamento natural;
- não truncar review para equalizar altura;
- não usar `height:100%`, `min-height` fixa, `align-stretch` ou `justify-content:space-between` para equalização visual;
- não posicionar cards manualmente com offsets frágeis;
- layout deve recalcular corretamente em resize, carregamento de fontes e expansão `Ler mais` quando existir.

### Ordem e acessibilidade

A ordem DOM continua sendo a ordem canônica dos depoimentos.

- teclado e leitor de tela seguem a ordem DOM;
- não reordenar DOM somente para preencher melhor colunas;
- preferir CSS Grid + medição/row-span ou outra implementação que preserve DOM order;
- evitar `column-count` quando isso produzir uma ordem visual incompatível com a ordem de leitura;
- mobile com 1 coluna deve seguir exatamente a ordem DOM;
- se houver `Ler mais`, o conteúdo integral permanece acessível e o masonry recalcula a altura após expansão.

### Carrossel vs masonry

Não force um carousel só porque o gate legado se chama `CAROUSEL REQUIRED`.

Para reviews de tamanhos muito variados:

`VERIFIED_STRONG -> REVIEW DISPLAY REQUIRED -> MASONRY PREFERRED`

Para reviews de tamanhos semelhantes ou quando houver necessidade real de browse horizontal:

`VERIFIED_STRONG -> REVIEW DISPLAY REQUIRED -> CAROUSEL ALLOWED`

No QA visual:

- grandes blocos vazios dentro de cards curtos = FAIL;
- grandes corredores vazios entre cards que masonry poderia preencher = FAIL quando há 4+ reviews variados;
- ordem de leitura quebrada = FAIL;
- overlap/clipping = FAIL;
- masonry natural, responsivo, acessível e bem preenchido = PASS.

## Integridade

- review entre aspas = texto fiel
- autoria pública fiel
- estrelas do review individual fiéis
- aggregate e quantidade do mesmo perfil e mesmo passe de coleta
- sem mistura de unidades/perfis
- sem reviews inventadas, fundidas ou parafraseadas como verbatim
- evidência local fora do bundle público
