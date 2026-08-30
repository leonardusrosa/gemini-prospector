---
name: google-reviews-verification
description: HARD GATE para Google Reviews. Use em TODO site, redesign, novo conceito ou QA público criado pelo Prospector quando existir ou puder existir Google Business Profile/Google Maps do lead. Identifica inequivocamente o perfil, lê aggregate atual, coleta reviews textuais do mesmo perfil e torna o carrossel obrigatório quando houver 3+ reviews verificáveis. Nunca permita omissão silenciosa por falha de scraping/coleta.
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

### VERIFIED_STRONG

Perfil correto inequívoco + aggregate atual + pelo menos 3 reviews textuais positivos verificáveis do mesmo perfil.

Resultado obrigatório:

`CAROUSEL REQUIRED: YES`

O site NÃO pode passar QA nem deploy final sem o carrossel.

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

`reviews não extraídas -> omitir carrossel -> PASS`

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

## HARD RULE de layout dos review cards

Review cards devem respeitar a altura natural do conteúdo. NÃO force todos os cards de uma linha/viewport a terem a altura do review mais longo.

- cada card usa altura intrínseca/`auto` de acordo com seu texto e metadata;
- proibido `height`, `min-height`, `align-stretch`, `height:100%` ou `justify-content:space-between` quando usados apenas para equalizar cards e criar grandes áreas vazias;
- mantenha organização por largura consistente, grid/carrossel, gaps e alinhamento no topo, não por altura artificial;
- o footer do review vem logo após o conteúdo, com espaçamento natural, e não deve ser empurrado para o fundo de um card esticado;
- o conjunto deve ocupar bem a largura disponível em desktop/tablet/mobile, enquanto a altura de cada card continua independente;
- o track/viewport do carrossel deve acomodar alturas variáveis sem clipping e, quando possível, adaptar a altura ao grupo/slide visível em vez de reservar uma altura fixa excessiva;
- não truncar texto somente para deixar os cards iguais. Se houver necessidade real de compactação, use expansão acessível (`Ler mais`/equivalente) preservando o review verbatim completo;
- layouts tipo masonry só são aceitáveis quando preservam ordem de leitura, teclado e acessibilidade. Não sacrifique sequência semântica para preencher espaço visual.

No QA visual, grandes blocos vazios dentro de cards curtos causados pelo review mais longo = FAIL.

## Integridade

- review entre aspas = texto fiel
- autoria pública fiel
- estrelas do review individual fiéis
- aggregate e quantidade do mesmo perfil e mesmo passe de coleta
- sem mistura de unidades/perfis
- sem reviews inventadas, fundidas ou parafraseadas como verbatim
- evidência local fora do bundle público
