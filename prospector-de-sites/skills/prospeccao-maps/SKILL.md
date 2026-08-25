---
name: prospeccao-maps
description: Esta skill deve ser usada ao prospectar clientes no Google Maps — buscar negócios bem avaliados com sites ruins OU sem site próprio, qualificar leads com score de oportunidade, classificar o status do site e montar a base de leads. Acione quando o usuário disser "prospectar", "buscar clientes", "achar leads", "clientes com site ruim", "clientes sem site", "prospecta negócios sem site" ou pedir para prospectar (skill prospeccao-maps).
---

# Prospecção no Google Maps (Redesign & Novo Site)

Encontrar negócios bem avaliados e consolidados (nota alta, muitas avaliações) que perdem clientes por:
1. **Site Fraco (`existing_weak` → `redesign`)**: negócio com site ativo porém datado, quebrado no mobile ou sem conversão.
2. **Sem Site Oficial (`none` → `new_site_concept`)**: negócio forte cuja presença digital se limita ao Maps, Instagram, WhatsApp ou Linktree, necessitando de uma presença própria profissional.

---

## 1. Classificação do Status do Site

Para cada estabelecimento encontrado, determine o `websiteStatus`:
- **`existing_weak`**: site próprio encontrado, porém com problemas claros de design, mobile, lentidão ou conversão.
- **`none`**: nenhum site próprio encontrado. Perfis de Instagram, Facebook, Google Maps, Linktree, diretórios de terceiros (Doctoralia, TripAdvisor, iFood) ou links de WhatsApp **são classificados como `none`** (e servem como fontes factuais de conteúdo).
- **`healthy`**: site atual é moderno, responsivo e funcional. Não é um bom candidato; descartar e registrar motivo.
- **`unknown`**: perfil sem URL direta no Maps, mas com indícios de domínio oficial que precisam de verificação rápida antes de declarar `none`.

Mapeamento de Modo:
- `existing_weak` → `siteMode = 'redesign'`
- `none` → `siteMode = 'new_site_concept'`

---

## 2. Modelos Separados de Pontuação (Opportunity Score 0–100)

Nunca misture as fórmulas de scoring; avalie cada modalidade com seus próprios critérios:

### A. Redesign Score (0–100)
- **Força do Negócio (30 pts)**: `rating` ≥ 4.7 (15 pts) + `avaliacoes` ≥ 50 (15 pts).
- **Fraqueza do Site Atual (35 pts)**: 2+ problemas graves verificáveis (mobile quebrado, sem CTA WhatsApp, layout >10 anos, plataforma gratuita Wix/Sites).
- **Disponibilidade de Conteúdo (15 pts)**: fotos reais, logo e serviços descritos no site antigo.
- **Contactabilidade (20 pts)**: WhatsApp direto validado (10 pts) + e-mail público (10 pts).

### B. Novo Site Score (0–100)
- **Força do Negócio (35 pts)**: `rating` ≥ 4.7 (20 pts) + `avaliacoes` ≥ 40 (15 pts).
- **Completude do Perfil Maps/Social (25 pts)**: endereço claro, horário de funcionamento, fotos reais de fachada/ambiente, categoria precisa.
- **Disponibilidade de Conteúdo Factual (20 pts)**: serviços verificados listados no Maps/Instagram, avaliações detalhadas com elogios específicos.
- **Contactabilidade (20 pts)**: WhatsApp direto do negócio (10 pts) + telefone/e-mail (10 pts).
- *Penalização (-30 pts)*: negócio com dados insuficientes para montar conceito factual ou indício de inatividade.

---

## 3. Comandos em Linguagem Natural

- **Geral**: `"prospecta nutricionistas em Campinas"` → busca mista (prioriza os maiores scores em Redesign e Novo Site).
- **Só Sem Site**: `"prospecta dentistas sem site em Rio Claro"` / `"procura negócios sem site"` → filtra exclusivamente `websiteStatus = 'none'` (`new_site_concept`).
- **Só Site Ruim**: `"prospecta restaurantes com site fraco em SP"` → filtra exclusivamente `websiteStatus = 'existing_weak'` (`redesign`).

---

## 4. Hierarquia de Fontes & Regras Fatuais Estritas (Zero Invenção)

Para leads **Sem Site (`new_site_concept`)**:
- **Fontes Permitidas**:
  1. Google Business Profile / Maps (nome, nota, avaliações reais, fotos do local, endereço, horários).
  2. Redes sociais oficiais públicas (Instagram/Facebook oficiais vinculados).
  3. Diretórios oficiais onde o profissional listou seus serviços expressamente.
- **PROIBIDO INVENTAR**:
  - Proibido inventar especialidades, anos de experiência ("há 15 anos no mercado"), preços ou promoções.
  - Proibido inventar depoimentos fictícios ou estatísticas falsas ("+1000 pacientes atendidos").
  - Proibido usar fotos genéricas de banco de imagens para médicos, pratos de restaurante ou instalações. Se faltar fotos, use tipografia sólida e layout espaçoso.

---

## 5. Apresentação de Candidatos

Antes de gerar os sites/redesigns, apresente a lista com distinção nítida de modo:

```markdown
1. Clínica Sorriso Perfeito
- Modo: ＋ SEM SITE / NOVO SITE
- Google: 4.9 ★ · 142 avaliações
- Presença atual: Google Maps + Instagram oficial
- Contato: WhatsApp (19) 99123-4567 disponível
- Score de Oportunidade: 92/100
- Justificativa: Reputação impecável no Google, 18 fotos reais do consultório, sem site oficial.

2. Advocacia Mendes & Associados
- Modo: 🌐 REDESIGN
- Google: 4.8 ★ · 65 avaliações
- Site atual: http://mendesadv.sites.google.com (lento, não abre no celular)
- Contato: WhatsApp + e-mail
- Score de Oportunidade: 88/100
- Justificativa: Negócio forte usando Google Sites gratuito sem botão de contato na 1ª dobra.
```

---

## 6. Persistência no Banco e Dashboard

Ao salvar o lead (no SQLite via MCP `prospector-mcp.py` ou `dashboard-server.py`):
- Preencha `websiteStatus` (`existing_weak` | `none` | `healthy` | `unknown`).
- Preencha `siteMode` (`redesign` | `new_site_concept`).
- Para `none`: `siteAntigo` recebe a URL da presença principal (ex: link do Maps ou Instagram).
- Registre o `motivo` com precisão factual.
- Mantenha `status = 'novo'`.
