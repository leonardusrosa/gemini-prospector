---
name: redesign-premium
description: Esta skill deve ser usada ao criar um conceito de site novo (para clientes sem site) OU redesenhar o site existente de um cliente prospectado — gerando uma versão premium, contextualmente orientada e de alta conversão, mantendo conteúdo 100% factual. Orquestra princípios das skills Taste e Impeccable para geração estática sem frameworks. Acione quando o usuário disser "redesenhar site", "criar site do cliente", "conceito de site", "melhorar página", "refazer o site" ou pedir para redesenhar/criar páginas (skill redesign-premium).
---

# Redesign & Criação de Conceito de Site (Taste + Impeccable)

Gera uma presença digital de altíssimo padrão para o prospecto — seja um **Redesign (`redesign`)** de site fraco existente ou um **Novo Conceito de Site (`new_site_concept`)** para negócios fortes que ainda não possuem site oficial.

Esta skill orquestra princípios de direção visual da **Taste Skill** (`design-taste-frontend` / `gpt-taste`) e de auditoria/polimento da **Impeccable** (`impeccable`), adaptando-os com rigor para saída estática pura em HTML/CSS/JS.

---

## 1. Ordem Absoluta de Prioridades

1. **Integridade Factual**: zero invenções (sem serviços, médicos, anos de experiência ou depoimentos falsos).
2. **Identidade Existente**: logo, fotos reais do Maps/redes e família de cores do cliente são prioridade máxima.
3. **Requisitos do Usuário**: referências e diretrizes específicas informadas.
4. **Arquitetura Estática do Prospector**: arquivo único `sites/[slug]/[slug].html` (CSS inline, vanilla JS, sem build, sem React/Next/Tailwind/npm).
5. **Direção de Design (Taste)**: leitura contextual, quebra de clichês de IA, ritmo visual.
6. **Auditoria e Polimento (Impeccable)**: hierarquia, tipografia, contraste e responsividade em 1 passe único.

---

## 2. Fase 1: Design Read por Lead (Antes de Codificar)

Antes de gerar qualquer linha de código, deduza uma leitura de design específica para o prospecto (salva opcionalmente em `sites/[slug]/design-read.md`).

### Para Negócios Sem Site (`new_site_concept`):
- Infira a direção visual a partir da categoria, público-alvo, fotos reais da fachada/consultório no Maps, cores da logo existente ou estética do espaço físico.
- "Sem site" **não é permissão para inventar marca**. Construa uma identidade contida e refinada em torno do nome e ativos reais do negócio.

### Dimensões de Análise:
- **Nicho & Posicionamento**: público-alvo, sensibilidade a confiança, faixa de preço percebida.
- **Identidade Existente**: logo, paleta base, fotos disponíveis, tom de voz.
- **Dials de Design**:
  - **Design Variance (1–10)**: 2–4 para clínicas/advocacia (simétrico/estruturado); 6–8 para arquitetura/estética/gastronomia.
  - **Motion Intensity (1–10)**: padrão 2–3 (restrito a micro-interações CSS; sem bibliotecas pesadas).
  - **Visual Density (1–10)**: 3–4 (espaçoso e focado) a 6 (informações técnicas).

---

## 3. Fase 2: Regras Anti-Slop (Diretrizes Taste para HTML Estático)

- **Fim do "Template Padrão de IA"**:
  - Proibido usar gradientes roxos/azuis de SaaS genérico.
  - Proibido usar dark mode com "glow blob" em negócios locais tradicionais.
  - Proibido usar cards dentro de cards ou envolver todas as seções em caixas idênticas.
  - Proibido usar títulos meta genéricos ("SECTION 01", "SOBRE NÓS", "PERGUNTA 05").
  - Proibido usar o mesmo ritmo visual repetitivo (ex.: 3 seções seguidas de grid de 3 cards).
- **Hero Disciplinado**:
  - H1 com largura generosa (`max-width: 65-80ch` ou fluid) para garantir no máximo **2 a 3 linhas** (usar `clamp(2rem, 4vw, 3.5rem)`).
  - Mensagem clara de benefício + kicker/subtítulo + 1 CTA primário evidente (WhatsApp ou agendamento real) + no máximo 1 CTA secundário justificado.
  - Nunca sobrecarregar o Hero com 5 botões, estatísticas inventadas ou selos flutuantes falsos.
- **Imagens e Ativos Reais**:
  - Use sempre as fotos reais do cliente e logo original (coletadas via Maps ou site antigo).
  - **NUNCA crie ou use imagens de pessoas/médicos falsos, clínicas falsas ou depoimentos fictícios.** Se faltarem fotos, compense com tipografia premium e espaço em branco.
- **Tipografia e Cores**:
  - No máximo **2 famílias tipográficas** (Google Fonts). Nunca use serifado por padrão se o nicho não pedir; nunca use Inter automaticamente.
  - Comprimento de linha para corpo de texto entre 60–75 caracteres.
  - Paleta preservando a marca do cliente, com contraste mínimo **WCAG AA** em todos os textos.

---

## 4. Fase 3: Geração do Código Estático & Localização de Mercado

Gere a página em `sites/[slug]/[slug].html`:
1. **Estrutura Semântica HTML5** (`header`, `main`, `section`, `footer`) com `lang="pt-BR"` ou `lang="pt-PT"` conforme o `locale` do lead.
2. **Localização Linguística Natural**:
   - **Brasil (`pt-BR`)**: sintaxe e vocabulário natural do Brasil (ex.: *"Agendar Consulta"*, *"Fale Conosco"*, *"Como Chegar"*).
   - **Portugal (`pt-PT`)**: sintaxe, ortografia e nível de formalidade de Portugal (ex.: *"Marcar Consulta"*, *"Contactar"*, *"Localização"*, *"Horário de Funcionamento"*, *"Telemóvel"*).
   - **Nunca traduzir nomes de negócios, médicos/profissionais ou marcas registradas.**
3. **CSS inline no `<head>`** com variáveis `:root` organizadas.
4. **Botão de contato/WhatsApp contextual** com mensagem pré-formatada e telefone no formato internacional.
5. **Mapa / localização e horários reais** coletados do Maps (respeitando formato de endereço do país).
6. **Camada do editor**: gere `sites/[slug]/[slug]-editor.html` utilizando o template em `references/editor-visual.md`.

---

## 5. Fase 4: Auditoria e Polimento Impeccable (1 Passe Bounded)

Após gerar o HTML, execute uma auditoria rápida de qualidade:
1. **Inspeção de Responsividade**: breakpoints `360px`, `375px`, `768px`, `1024px`, `1280px`. Zero rolagem horizontal.
2. **Inspeção de Contraste e Acessibilidade**: textos legíveis, `:hover` e `:focus-visible` adequados.
3. **Passe Único de Correção**: aplique ajustes em uma única edição consolidada.

---

## 6. Fase 5: Atualização do Comparador e CRM

1. Atualizar `comparar.html` na raiz do projeto:
   - Para `redesign`: comparador mostra site antigo vs nova versão.
   - Para `new_site_concept`: comparador mostra resumo da presença atual (Google Maps / Redes Sociais) vs conceito do site.
2. Registrar o lead com status `redesenhado` no CRM local (`prospector-mcp.py` / SQLite) e regenerar o dashboard.
