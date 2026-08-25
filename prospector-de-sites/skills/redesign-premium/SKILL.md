---
name: redesign-premium
description: Esta skill deve ser usada ao redesenhar o site de um cliente prospectado — criar uma versão nova, premium, contextualmente orientada e de alta conversão da página existente, mantendo conteúdo factual, logo e paleta do cliente. Orquestra princípios das skills Taste e Impeccable para geração estática sem frameworks. Acione quando o usuário disser "redesenhar site", "melhorar página", "refazer o site do cliente" ou pedir para redesenhar (skill redesign-premium).
---

# Redesign Premium de Páginas (Orquestração Taste + Impeccable)

Criar uma NOVA VERSÃO da página do cliente — não uma página genérica. O cliente precisa reconhecer imediatamente o próprio negócio, elevado ao padrão estético e de conversão que seu faturamento merece.

Esta skill orquestra princípios de direção visual da **Taste Skill** (`design-taste-frontend` / `gpt-taste`) e de auditoria/polimento da **Impeccable** (`impeccable`), adaptando-os com rigor para saída estática pura em HTML/CSS/JS.

---

## 1. Ordem Absoluta de Prioridades

1. **Integridade Factual**: zero invenções (sem serviços, dados ou avaliações falsas).
2. **Identidade Existente**: logo, fotos reais e família de cores do cliente são prioridade máxima.
3. **Requisitos do Usuário**: referências e diretrizes específicas informadas.
4. **Arquitetura Estática do Prospector**: arquivo único `sites/[slug]/[slug].html` (CSS inline, vanilla JS, sem build, sem React/Next/Tailwind/npm).
5. **Direção de Design (Taste)**: leitura contextual, quebra de clichês de IA, ritmo visual.
6. **Auditoria e Polimento (Impeccable)**: hierarquia, tipografia, contraste e responsividade em 1 passe único.

---

## 2. Fase 1: Design Read por Lead (Antes de Codificar)

Antes de gerar qualquer linha de código, deduza uma leitura de design específica para o prospecto (salva opcionalmente em `sites/[slug]/design-read.md`).

### Dimensões de Análise:
- **Nicho & Posicionamento**: público-alvo, sensibilidade a confiança, faixa de preço percebida.
- **Identidade Existente**: logo, paleta base, fotos disponíveis, tom de voz.
- **Dials de Design**:
  - **Design Variance (1–10)**: 2–4 para clínicas/advocacia (simétrico/estruturado); 6–8 para arquitetura/estética/gastronomia.
  - **Motion Intensity (1–10)**: padrão 2–3 (restrito a micro-interações CSS; sem bibliotecas pesadas).
  - **Visual Density (1–10)**: 3–4 (espaçoso e focado) a 6 (informações técnicas).

### Linguagem Visual por Nicho (Adequação Contextual — Não use fórmula única):
- **Clínica / Odonto / Saúde**: foco em confiança e clareza, layout limpo, tipografia sólida e acolhedora, cores precisas, baixa moção, destaque para equipe real e credenciais.
- **Advocacia / Jurídico**: autoridade institucional, tipografia editorial de alta legibilidade, sóbrio, sem excessos decorativos.
- **Academia / Fitness**: alto contraste, energia, tipografia display impactante, composição dinâmica, foco em horários e chamada rápida de WhatsApp.
- **Restaurante / Gastronomia**: fotografia em primeiro plano, cardápio legível, atmosfera do ambiente, localização e reserva em destaque.
- **Oficina / Serviços / Reformas**: direto ao ponto, robusto, foco em agilidade, provas reais de atendimento e botão de WhatsApp imediato.
- **Arquitetura / Design**: alta variação visual, ênfase em portfólio visual, diagramação editorial assimétrica.

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
  - Use sempre as fotos reais do cliente e logo original (coletadas via navegador).
  - **NUNCA crie ou use imagens de pessoas/médicos falsos, clínicas falsas ou depoimentos fictícios.** Se faltarem fotos, compense com tipografia premium e espaço em branco.
- **Tipografia e Cores**:
  - No máximo **2 famílias tipográficas** (Google Fonts). Nunca use serifado por padrão se o nicho não pedir; nunca use Inter automaticamente.
  - Comprimento de linha para corpo de texto entre 60–75 caracteres.
  - Paleta preservando a marca do cliente, com contraste mínimo **WCAG AA** em todos os textos.
- **Moção Sóbria**:
  - Transições suaves em CSS puro (`0.2s–0.3s ease-out`).
  - Respeito obrigatório a `@media (prefers-reduced-motion: reduce)`.

---

## 4. Fase 3: Geração do Código Estático

Gere a página em `sites/[slug]/[slug].html`:
1. Estrutura semântica HTML5 (`header`, `main`, `section`, `footer`).
2. CSS inline no `<head>` com variáveis `:root` organizadas.
3. Botão de contato/WhatsApp contextual com mensagem pré-formatada.
4. Mapa / localização e horários reais.
5. Camada do editor: gere `sites/[slug]/[slug]-editor.html` utilizando o template em `references/editor-visual.md`.

---

## 5. Fase 4: Auditoria e Polimento Impeccable (1 Passe Bounded)

Após gerar o HTML, execute uma auditoria rápida de qualidade:

1. **Inspeção de Responsividade**:
   - Verificar nos breakpoints essenciais: `360px`, `375px`, `768px`, `1024px`, `1280px`, `1440px`.
   - Garantir: zero rolagem horizontal (`overflow-x: hidden`), sem quebras de texto indesejadas, paddings proporcionais.
2. **Inspeção de Contraste e Acessibilidade**:
   - Textos legíveis contra o fundo, botões com estados `:hover` e `:focus-visible`.
3. **Passe Único de Correção**:
   - Corrija os pontos identificados em uma única edição consolidada no arquivo.
   - Pare após o passe de ajuste (sem loops intermináveis de refatoração).

---

## 6. Fase 5: Atualização do Comparador e CRM

1. Atualizar `comparar.html` na raiz do projeto com o template de `references/comparador-template.html`.
2. Registrar o lead com status `redesenhado` no CRM local (`prospector-mcp.py` / SQLite) e regenerar o dashboard.

---

## 7. Checklist Final de Entrega

- [ ] Design Read coerente com o nicho real do cliente
- [ ] Conteúdo 100% factual e fotos originais preservadas
- [ ] Zero dependências de build, frameworks ou npm
- [ ] Responsividade impecável em mobile e desktop
- [ ] `sites/[slug]/[slug].html` e `sites/[slug]/[slug]-editor.html` gerados
- [ ] `comparar.html` atualizado
