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

## Integridade

- review entre aspas = texto fiel
- autoria pública fiel
- estrelas do review individual fiéis
- aggregate e quantidade do mesmo perfil e mesmo passe de coleta
- sem mistura de unidades/perfis
- sem reviews inventadas, fundidas ou parafraseadas como verbatim
- evidência local fora do bundle público
