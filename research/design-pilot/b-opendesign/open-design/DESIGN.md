# Design System & Visual Specification: Ateliê Clínico Editorial
**Business**: Clínica Odontológica Dra. Francine Goulart  
**Slug**: `clinica-dra-francine-goulart-rio-claro`  
**Selection**: Direction 1 (Critiqued & Approved via `gpt-taste`)  
**Status**: Authoritative visual contract for Variant B implementation

---

## 1. Design Thesis
Uma composição médica editorial de alta distinção e serenidade visual. Substitui inteiramente os arquétipos genéricos de SaaS (fundo escuro obrigatório, cards isolados com sombra e botões flutuantes descontextualizados) por uma narrativa em canvas luminoso marfim, tipografia serifada de autoridade médica (Newsreader), divisores horizontais geométricos finos e direcionamento de conversão contextual.

## 2. Color Tokens
- **Canvas / Background**: `#fafaf9` (Warm Ivory / Linho Clínico)
- **Surface / Contrast Section**: `#f4f4f2` (Porcelana Neutra)
- **Primary Deep / Headings**: `#132a24` (Verde Floresta Cirúrgico Profundo)
- **Body Text**: `#292524` (Ardósia Quente Escura)
- **Muted Text / Notes**: `#78716c` (Stone Médio)
- **Accent Action**: `#1e473d` (Sálvia Cirúrgico Profundo)
- **Accent Hover**: `#14352d`
- **Hairline Dividers**: `#e7e5e4` (Linha divisória sutil 1px)
- **Contrast Proof Badge**: `#132a24` (Fundo sólido contrastante para destaque de nota Google)

## 3. Typography Stack
- **Display Headings (H1, H2, H3)**: `'Newsreader', serif` (pesos 400, 500, 600)
  - Proporção H1: `clamp(2.5rem, 4.2vw, 3.8rem)` com entrelinha estrita `1.15` e largura máxima controlada para 2 linhas no desktop.
- **Body & Technical Copy**: `'Plus Jakarta Sans', system-ui, sans-serif` (pesos 400, 500, 600)
  - Corpo regular `1rem`, entrelinha `1.65`.

## 4. Spacing & Rhythm
- Seções com espaçamento editorial generoso: `padding: 104px 0` no desktop, `64px 0` no mobile.
- Alinhamento em grade de 12 colunas com gutter de `32px`.
- Container central: `max-width: 1200px`.

## 5. Hero Architecture
- **Composição**: Canvas claro e luminoso (`#fafaf9`). Coluna de texto à esquerda com amplitude tipográfica (`max-w-3xl`), exibindo headline com serifa editorial expressiva.
- **Asset Visual**: O template ultrawide da dentista (`desktop-ultrawide.webp`) é acomodado à direita em uma moldura arquitetônica com proporção refinada e máscara suave de luminosidade, preservando a silhueta da profissional sem corte abrupto e sem overlay escuro artificial.
- **CTA**: Exatamente UM botão com preenchimento verde floresta cirúrgico e texto branco de alto contraste ("Solicitar horário de avaliação").

## 6. Treatment Directory Grammar (Zero Cards)
- Ao invés de cards flutuantes com sombras, os tratamentos são dispostos em um diretório editorial contínuo com linhas divisórias horizontais finas (`border-top: 1px solid var(--hairline)`).
- Cada linha apresenta:
  - Número técnico discreto em serifa (`01`, `02`, `03`, `04`).
  - Nome do tratamento em destaque editorial (`font-family: Newsreader; font-size: 1.6rem`).
  - Descrição clínica factual em prosa corrida.
  - Link de ação contextual direta ("Agendar pelo WhatsApp").

## 7. Google Reviews Presentation
- Apresentação em formato de placa editorial de certificação:
  - Métrica central `4,8` em tipografia serifada de grande porte.
  - Avaliação de 28 pacientes verificados no Google Maps.
  - Texto de compromisso clínico com pontualidade e acolhimento humano.
  - Link externo verificado para o perfil do Google Maps.

## 8. Location & Accessibility Hub
- Bloco em 2 colunas com moldura unificada:
  - Esquerda: Dados de conveniência (Avenida 7, nº 310, Centro, Rio Claro), telefone (19) 98849-4898, orientações de chegada.
  - Direita: Mapa interativo responsivo com borda milimétrica neutra e cantos sutis (4px).

## 9. Motion & Behavior
- Entrada suave das linhas editoriais com transição de opacidade e sutil deslocamento vertical (0.5s).
- Header com efeito de vidro esmerilado claro (`backdrop-filter: blur(16px)` com transparência de 90%).
- Botão flutuante de WhatsApp que se torna visível somente após o CTA do hero sair do viewport.

## 10. Anti-Slop & Core Rules Constraints
- Proibição absoluta de pills, chips decorativos, gradientes fluorescentes e caixas elevadas por sombras.
- Zero emojis e zero travessões (`—` / `–`).
- Conformidade total com WCAG AA em todas as combinações de texto e fundo.
