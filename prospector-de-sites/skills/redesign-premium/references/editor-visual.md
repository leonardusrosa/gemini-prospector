# Editor visual client-ready

Todo site gerado pelo Prospector deve poder receber uma versão de editor visual sem expor HTML/CSS/JS arbitrário ao cliente.

O objetivo é permitir manutenção cotidiana de conteúdo sem depender do desenvolvedor para cada troca de texto, telefone, WhatsApp, rede social, link ou imagem.

## Geração

Use o gerador canônico do plugin através do wrapper da raiz:

```bash
python create_editor.py sites/[slug]/[slug].html
```

Saída padrão:

```text
sites/[slug]/[slug]-editor.html
```

**IMPORTANTE:** arquivos `*-editor.html` já gerados não se atualizam quando o gerador muda. Depois de atualizar o Prospector, regenere o editor a partir do HTML público.

## HARD RULE — ações do negócio precisam ser editáveis

Todo CTA/link relevante deve abrir o painel de propriedades em modo edição, inclusive quando o clique ocorrer no SVG/ícone interno.

Inclui obrigatoriamente:

- botão `Agendar Consulta`
- botão/CTA sticky ou flutuante `Agendar no WhatsApp`
- CTA de navbar
- CTA de hero
- CTA de rodapé
- WhatsApp
- telefone
- e-mail
- Instagram
- Facebook
- YouTube/TikTok quando reais
- booking/agendamento
- Google Maps
- links internos e externos

O editor usa **event delegation em capture phase** para interceptar esses cliques antes dos handlers da página. Isso evita que SVGs internos, scripts de navegação ou `stopPropagation()` tornem os links impossíveis de editar.

Também existe compatibilidade com navegação legada via `onclick` simples (`window.open`, `location.href`, `location.assign`), mas novos sites devem preferir links semânticos.

## Markup obrigatório para novos sites

Prefira sempre `<a href>` para ações navegáveis, mesmo quando visualmente parece um botão.

### WhatsApp

```html
<a
  href="https://wa.me/5511999999999"
  data-pe-field="business.whatsapp">
  <svg aria-hidden="true">...</svg>
  <span data-pe-label>Agendar Consulta</span>
</a>
```

### Sticky WhatsApp

```html
<a
  href="https://wa.me/5511999999999"
  data-pe-field="business.whatsapp"
  aria-label="Agendar no WhatsApp">
  <svg aria-hidden="true">...</svg>
  <span data-pe-label>Agendar no WhatsApp</span>
</a>
```

### Social apenas com ícone

```html
<a
  href="https://instagram.com/empresa"
  data-pe-field="business.instagram"
  aria-label="Instagram">
  <svg aria-hidden="true">...</svg>
</a>
```

Links somente com ícone continuam editáveis: o cliente altera destino e `aria-label`; o SVG não é destruído.

## Campos compartilhados

Use `data-pe-field` para dados repetidos. Alterar um campo pode atualizar todas as suas ocorrências quando a opção de sincronização estiver marcada.

Campos recomendados:

```text
business.whatsapp
business.phone
business.email
business.instagram
business.facebook
business.youtube
business.tiktok
business.maps
business.booking
```

Mesmo em páginas antigas sem `data-pe-field`, o runtime tenta inferir automaticamente campos conhecidos a partir do URL (`wa.me`, `tel:`, `mailto:`, Instagram, Facebook, YouTube, TikTok e Google Maps).

## Painel de ações

Ao clicar em um CTA/link em modo edição, não navegue. Abra o painel para editar:

- texto/label, quando houver um nó de label simples
- tipo de ação
- destino
- mensagem pré-preenchida do WhatsApp
- `aria-label`
- abrir ou não em nova aba
- sincronizar ocorrências do mesmo campo/canal

Tipos suportados:

```text
URL/página
WhatsApp
Telefone
E-mail
Âncora interna
```

Bloqueie esquemas perigosos como `javascript:`, `vbscript:` e `data:text/html`.

## Texto

Editável:

- headings
- parágrafos
- listas
- captions
- textos editoriais comuns

Colar conteúdo deve virar texto puro, sem HTML arbitrário.

## Imagens

Ao clicar em uma imagem, permitir:

- trocar arquivo
- editar URL/origem
- editar `alt`

Arquivos locais podem ser incorporados como Data URL no HTML exportado. Para produção em escala, prefira futuramente pipeline de upload de assets.

### Imagens de fundo

Marque explicitamente imagens de fundo editáveis:

```html
<section
  data-pe-bg
  data-pe-bg-src="assets/hero.webp"
  style="background-image:url('assets/hero.webp')">
</section>
```

Não dependa de introspecção automática de CSS complexo.

## Labels complexos

Para CTA com SVG/ícone + texto, marque a parte textual:

```html
<span data-pe-label>Agendar consulta</span>
```

Isso permite trocar o texto sem substituir o SVG.

## Limites de segurança

O cliente não recebe edição arbitrária de:

- HTML
- CSS
- JavaScript
- GSAP/motion logic
- tokens/chaves
- configuração de deploy
- analytics
- código de terceiros

A experiência é um CMS leve de conteúdo, não editor de código.

## Preview e exportação

O editor deve oferecer:

- `Pré-visualizar`: permite testar links/comportamentos normalmente
- `Exportar página`: baixa HTML limpo sem toolbar/painel/runtime do editor

## QA obrigatória do editor

Para cada site novo, teste no `*-editor.html` pelo menos:

1. CTA principal do hero abre propriedades, não navega.
2. CTA sticky/flutuante do WhatsApp abre propriedades.
3. Clique diretamente no SVG de Instagram/Facebook abre o link pai no editor.
4. Link social somente com ícone permite alterar URL e `aria-label`.
5. Alterar `business.whatsapp` com sincronização atualiza navbar + hero + sticky + footer quando existirem.
6. Preview volta a permitir navegação real.
7. HTML exportado não contém a UI/runtime do editor.

Se qualquer CTA/social relevante não for link-editável, o editor falhou QA e não deve ser considerado concluído.
