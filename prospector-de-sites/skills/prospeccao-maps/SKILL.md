---
name: prospeccao-maps
description: Esta skill deve ser usada ao prospectar clientes no Google Maps — buscar negócios bem avaliados com sites ruins OU sem site próprio (Brasil, Portugal e internacional), qualificar leads com score de oportunidade, classificar o status do site e montar a base de leads. Acione quando o usuário disser "prospectar", "buscar clientes", "achar leads", "clientes com site ruim", "clientes sem site", "prospecta negócios sem site" ou pedir para prospectar (skill prospeccao-maps).
---

# Prospecção no Google Maps (Multimercado: Brasil, Portugal & Internacional)

Encontrar negócios bem avaliados e consolidados (nota alta, muitas avaliações) que perdem clientes por:
1. **Site Fraco (`existing_weak` → `redesign`)**: negócio com site ativo porém datado, quebrado no mobile ou sem conversão.
2. **Sem Site Oficial (`none` → `new_site_concept`)**: negócio forte cuja presença digital se limita ao Maps, redes sociais, WhatsApp ou Linktree, necessitando de uma presença própria profissional.

---

## 1. Resolução de País e Metadados de Mercado

A resolução do país do lead segue a ordem rigorosa de evidências:
1. **País explícito na busca/pedido do usuário** (ex: `"em Lisboa, Portugal"`, `"em Coimbra PT"`, `"em Campinas SP, Brasil"`).
2. **Metadados de endereço do Google Maps / Places** (`country`, `formatted_address`).
3. **Contexto de cidade/região inequívoco** (ex: Lisboa, Porto, Braga → `PT`; São Paulo, Rio Claro, Curitiba → `BR`).
4. **Configuração padrão** (`market.defaultCountry` em `prospector-config.json`) apenas quando não houver pistas locais suficientes.

Metadados canônicos por lead:
- `country`: Código ISO 3166-1 alpha-2 (`BR`, `PT`, etc.)
- `locale`: `pt-BR`, `pt-PT`
- `language`: `pt`
- `phoneCountryCode`: `55`, `351`

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

## 5. Comandos em Linguagem Natural

- **Brasil**: `"prospecta dentistas sem site em Rio Claro SP"` / `"procura nutricionistas em Campinas"`
- **Portugal**: `"prospecta dentistas sem site em Lisboa, Portugal"` / `"procura restaurantes em Coimbra PT"`
- **Misto / Específico**: `"prospecta clínicas com site fraco ou sem site no Porto"`

---

## 6. Apresentação de Candidatos

Antes de gerar os sites/redesigns, apresente a lista com distinção nítida de país e modo:

```markdown
1. Clínica Sorriso Lisboa
- País: 🇵🇹 Portugal (PT) · pt-PT
- Modo: ＋ SEM SITE / NOVO SITE
- Google: 4.9 ★ · 142 avaliações (Lisboa)
- Presença atual: Google Maps + Instagram oficial (sem site oficial após verificação)
- Contacto: WhatsApp +351 912 345 678
- Score de Oportunidade: 93/100

2. Advocacia Mendes & Associados
- País: 🇧🇷 Brasil (BR) · pt-BR
- Modo: 🌐 REDESIGN
- Google: 4.8 ★ · 65 avaliações (São Paulo)
- Site atual: http://mendesadv.sites.google.com (lento, quebra no mobile)
- Contato: WhatsApp +55 11 98888-7777
- Score de Oportunidade: 88/100
```
