---
name: prospeccao-maps
description: Use for Google Maps prospect discovery, score-based website opportunities, verified business identity, official site/social media inventory and lead qualification. New discoveries are strictly limited to the USA, Canada and Europe; existing international CRM records may be maintained. Do not infer country, rights or telephone permission.
---

# Google Maps Prospect Discovery (USA, Canada, Europe)

Encontrar negócios bem avaliados e consolidados (nota alta, muitas avaliações) que perdem clientes por:
1. **Site Fraco (`existing_weak` → `redesign`)**: negócio com site ativo porém datado, quebrado no mobile ou sem conversão.
2. **Sem Site Oficial (`none` → `new_site_concept`)**: negócio forte cuja presença digital se limita ao Maps, redes sociais, WhatsApp ou Linktree, necessitando de uma presença própria profissional.

---

## 1. Geographic Policy — USA, Canada and Europe only

**HARD GATE: New prospect discovery is restricted to the United States (US),
Canada (CA), and Europe.** The exact ISO country allowlist lives in
prospector-de-sites/market_scope.py. Every new lead must have an independently
verified ISO 3166-1 alpha-2 country. Uncertain, absent or out-of-scope
countries are blocked, not guessed from phone digits, language, or city names.

Historical CRM leads from outside this scope, including existing Brazilian
leads, remain editable. A conflicting country for an existing CRM identity
requires manual resolution before merging. No exceptions to the NEW discovery
scope are inferred from historical lead states or a previous search session.

Research priority:
- **Tier A**: US, CA, GB, IE, NL, CH, DE, AT, DK, SE, NO.
- **Tier B**: Other European ISO countries; initial exploratory markets
  include FR, ES, PT, IT, BE, FI and PL.
- **Out of scope for NEW discovery**: BR, MX, CL, PA, CR, UY, and any
  non-US/CA/non-European country.

Initial pilot niche: independent automotive-detailing businesses. This is a
research-cohort preference, not a universal industry exclusion.

Country evidence priority:
1. Exact country explicitly specified by the operator;
2. Direct Google Maps/Places country/address evidence;
3. Independent official business-address source.

If evidence conflicts, **HOLD** rather than overwrite the lead's country.
Do not apply a Brazilian locale fallback to North American/European copy.

Separate opportunity ranking, source/media readiness and channel verification
from legal outreach authorization and callback permission. Neither a verified
phone number nor an admin ON/OFF preference is permission for AI sales calls.

Canonical lead metadata: country, locale/language as actually verified for
that market, currency and calling code only when known, marketTier,
websiteStatus, classification evidence, and media provenance.

See docs/international-market-media-pilot.md for the executable research
and asset-rights workflow.

---

## 2. Classificação Conservadora do Status do Site (Com Verificação)

Nunca classifique um negócio como `none` apenas porque o Google Maps não trouxe a URL preenchida. Execute uma verificação prévia rápida:

```text
Maps não lista website próprio
    ↓
Passo de Verificação (busca por "Nome Exato + Cidade / Endereço / Telefone" e checagem de links em redes sociais oficiais)
    ├─ Nenhum site oficial legítimo encontrado → websiteStatus = "none" (siteMode = "new_site_concept")
    ├─ Possível domínio oficial encontrado mas duvidoso → websiteStatus = "unknown" (siteMode = "none")
    ├─ Site oficial confirmado com falhas graves → websiteStatus = "existing_weak" (siteMode = "redesign")
    └─ Site oficial confirmado moderno e saudável → websiteStatus = "healthy" (descartar e registrar motivo)
```

**Definições Importantes**:
- **Sites Oficiais**: Domínio próprio, Google Sites, Wix, Squarespace, WordPress, Webflow.
- **NÃO são sites oficiais**: Instagram, Facebook, TikTok, WhatsApp, Linktree, Google Business Profile, iFood, Doctoralia, diretórios locais. Esses perfis contam como `websiteStatus = "none"` e servem de fontes factuais legítimas de conteúdo.

---

## 3. Normalização Telefônica por País

- **Formato Canônico Interno**: Dígitos internacionais E.164 sem `+` nem espaços (ex: Brasil: `5511999999999`, Portugal: `351912345678`).
- **Números em formato nacional/local**: Só podem ser convertidos automaticamente quando o país do lead estiver **confirmado** (`BR` ou `PT`).
- **País desconhecido (`unknown`)**: Rejeitar normalização automática e exigir número com código de país explícito.

---

## 4. Modelos Separados de Pontuação (Opportunity Score 0–100)

O cálculo de oportunidade é neutro em relação ao país:

### A. Redesign Score (0–100)
- **Força do Negócio (30 pts)**: `rating` ≥ 4.7 (15 pts) + `avaliacoes` ≥ 50 (15 pts).
- **Fraqueza do Site Atual (35 pts)**: 2+ problemas graves verificáveis (mobile quebrado, sem CTA claro, layout antigo, construtor gratuito).
- **Disponibilidade de Conteúdo (15 pts)**: fotos reais, logo e serviços descritos.
- **Contactabilidade (20 pts)**: WhatsApp direto validado (10 pts) + e-mail público (10 pts).

### B. Novo Site Score (0–100)
- **Força do Negócio (35 pts)**: `rating` ≥ 4.7 (20 pts) + `avaliacoes` ≥ 40 (15 pts).
- **Completude do Perfil Maps/Social (25 pts)**: endereço claro, horário, fotos reais de fachada/ambiente, categoria precisa.
- **Disponibilidade de Conteúdo Factual (20 pts)**: serviços verificados, avaliações detalhadas com elogios específicos.
- **Contactabilidade (20 pts)**: WhatsApp direto (10 pts) + telefone/e-mail (10 pts).
- *Penalização (-30 pts)*: dados insuficientes para conceito factual ou indício de inatividade.

---

## 5. Example discovery instructions

- United States: research automotive detailers in Dallas TX with a missing
  or visibly weak official business website and independently verified Maps
  identity, services and review count.
- Canada: find independent service providers in Toronto ON with a strong
  verified local reputation and demonstrably weak mobile website.
- Europe: research local businesses in Dublin IE, Amsterdam NL, or Porto PT
  with a website opportunity and actual first-party/social asset inventory.

New discovery outside the US, Canada and Europe is blocked; Brazilian legacy
lead maintenance remains permitted.

---

## 6. Candidate presentation before site creation

Present evidence-backed leads with separate country, website opportunity,
research-readiness and independent callback/outreach authorization status.

Illustrative response structure (fictional examples, not verified leads):

1. Example Workshop, Dallas, US
   - Market: US / English-language review pending
   - Opportunity: weak official mobile website, source verification pending
   - Reputation: rating/count only if independently verified in Maps
   - Media: inspect official site and confirmed brand socials for assets
   - Commercial: research score, not contact authorization
   - Callback: disabled until real recipient request and admin review

2. Example Studio, Porto, PT
   - Market: PT / Portuguese (Portugal)
   - Opportunity: potentially no official site; independently verify
   - Media: official social presence is research evidence, not a reuse license
   - Commercial: scored independently from image rights
   - Callback: disabled regardless of score

Never present a fabricated real business or unverifiable review count as
a ranked prospect. Omit out-of-scope new leads entirely.

---

## 7. HARD RULE — Conteúdo do site oficial não termina na homepage

Para leads `existing_weak`, a homepage serve para classificar fraqueza rapidamente, mas **não deve ser tratada como inventário completo de conteúdo/ativos do negócio**.

### Durante qualificação

Se o score de `Disponibilidade de Conteúdo` depender de saber se existem fotos reais, expert bios, serviços ou instalações, faça uma checagem targeted de links internos óbvios antes de concluir que o negócio tem pouco conteúdo.

Priorize links oficiais para:

- serviços/especialidades;
- sobre/equipe/expert;
- instalações/gallery;
- contato/localização.

Não precisa executar o crawl profundo de todo candidato antes de ranking inicial. O objetivo aqui é evitar falso negativo de conteúdo.

### Handoff obrigatório para `redesign-premium`

Quando um lead `existing_weak` for selecionado para redesign, o próximo estágio deve ler:

```text
redesign-premium/references/first-party-source-crawl.md
```

e executar o crawl dirigido do domínio oficial antes do Design Read final.

O handoff correto é:

```text
QUALIFY
→ official site confirmed
→ candidate selected for redesign
→ targeted first-party source-tree crawl
→ facts/assets + provenance
→ design
```

Uma homepage fraca pode esconder ótimas fotos, descrições e credenciais em subpáginas. Não penalize nem redesenhe com evidência incompleta quando essas páginas forem facilmente descobríveis.

## 8. Official social identity and media reuse gate

The desktop-assisted research pass must inspect confirmed official websites
and verified business-owned social accounts (Instagram, Facebook, TikTok,
YouTube, when applicable) before final design direction. These accounts
are legitimate **sources of observations**, not automatically licensed
asset repositories and not outbound messaging channels.

- Record official profile URL, evidence of business identity, observation
  date and the specific original asset/source-page URL.
- Classify each photo, logo, staff image and video by semantic purpose,
  quality and documented commercial reuse permission.
- A publicly accessible social photo cannot be downloaded/rehosted on a
  customer site without documented rights for that specific use.
- Google Maps/Places photos are reference-only unless separately authorized;
  compliant official embeds are distinct from downloading/serving copies.
- If the profile is unverified, do not present it as a clickable official
  brand account. Never fabricate a logo, handle, staff identity or image.
- The local research manifest gate blocks attempted use of media without
  source identity and permission evidence. Do not mark independent visual
  or factual QA PASS based on a manifest checkbox alone.
- Full design implementation and two-round targeted visual corrections are
  separate, evidence-bound stages. Final Preview release remains manual.

Implementation: prospector-de-sites/automation/site_research.py
Regression: test_market_scope_and_site_research.py
