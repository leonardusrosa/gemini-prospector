# Editor visual client-ready

Todo site gerado pelo Prospector deve poder receber uma versão de editor visual sem expor HTML/CSS/JS arbitrário ao cliente.

O objetivo é permitir manutenção cotidiana de conteúdo sem depender do desenvolvedor para cada troca de texto, telefone, WhatsApp, rede social, link, logo ou imagem.

## Geração

Use o gerador canônico através do wrapper da raiz:

```bash
python create_editor.py sites/[slug]/[slug].html
```

Saída padrão:

```text
sites/[slug]/[slug]-editor.html
```

**HARD RULE:** use o wrapper da raiz, não invoque diretamente o gerador interno do plugin em workflows normais. O wrapper executa os compatibility patches do editor, incluindo reconhecimento/prioridade de logo/brand media e o workflow `Salvar rascunho / Publicar alterações`.

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

## HARD RULE — logo/marca é mídia editável de primeira classe

Header/footer logo, wordmark e imagem de marca devem ser substituíveis pelo cliente como **mídia**, não tratados apenas como link para a home.

Isso vale mesmo quando o logo está dentro de:

```html
<a href="/">...</a>
```

### Prioridade de clique

Quando o clique ocorre diretamente em uma imagem editável dentro de um link:

```text
imagem/logo
→ abrir propriedades de mídia
→ NÃO abrir propriedades do link pai
→ NÃO navegar
```

Quando o usuário clicar numa área do link que não seja a própria imagem, o link/ação pode continuar abrindo o painel de ação.

Assim, um logo clicável continua tendo **duas responsabilidades separadas**:

```text
brand.logo = arquivo/URL/alt da marca
brand.home = destino do link da marca
```

### Markup recomendado para novos sites

```html
<a href="/" data-pe-field="brand.home" aria-label="Página inicial">
  <img
    src="assets/logo.webp"
    alt="Nome do negócio"
    data-pe-field="brand.logo">
</a>
```

Use `brand.logo` para ocorrências que devem trocar juntas, por exemplo header + footer.

Quando existirem variantes genuinamente diferentes, use campos explícitos, por exemplo:

```text
brand.logo
brand.logo.mobile
brand.logo.light
brand.logo.dark
```

Não crie variantes sem necessidade.

### Inferência para sites existentes

Mesmo sem `data-pe-field`, o runtime/wrapper tenta reconhecer logos por sinais como:

- `src`/`alt` contendo `logo`, `logotipo`, `brand` ou `marca`;
- classes/IDs de logo/brand;
- imagem clicável dentro de header/nav/footer apontando para a home.

Quando inferido como logo, o campo compartilhado é `brand.logo`.

A inferência é fallback. **Novos sites devem marcar explicitamente `data-pe-field="brand.logo"`.**

### `<picture>` / `srcset`

Logo/imagem editável dentro de `<picture>` deve continuar trocável. Quando o editor altera a imagem principal, fontes associadas do `<picture>` não podem manter uma versão antiga que sobreponha visualmente a alteração.

Evite estruturas de imagem responsiva desnecessariamente complexas para logos simples.

### SVG

- SVG usado via `<img src="logo.svg">` é mídia editável normalmente.
- SVG inline não deve abrir edição arbitrária de paths/código.
- Se uma marca inline SVG precisar ser substituível, prefira transformá-la em asset externo ou fornecer mecanismo explícito de brand asset.

### Proporção

Trocar o logo não deve deformá-lo. Layout/CSS deve preservar `object-fit`, proporção e limites de tamanho adequados.

## Markup obrigatório para novos sites — ações

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
brand.logo
brand.home
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

Mesmo em páginas antigas sem `data-pe-field`, o runtime tenta inferir automaticamente campos conhecidos a partir do URL (`wa.me`, `tel:`, `mailto:`, Instagram, Facebook, YouTube, TikTok e Google Maps) e sinais de identidade visual para logos.

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
- sincronizar ocorrências quando houver campo compartilhado

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
- SVG paths/código inline
- GSAP/motion logic
- tokens/chaves
- configuração de deploy
- analytics
- código de terceiros

A experiência é um CMS leve de conteúdo, não editor de código.

## Draft / Preview / Publish / Export — responsabilidades separadas

O editor deve oferecer quatro ações distintas:

- **`Salvar rascunho`**: persiste o estado sem alterar o site público. O editor mantém snapshot no navegador e, quando o backend está disponível, também salva um draft server-side.
- **`Pré-visualizar`**: testa a versão atual no próprio editor, sem publicar.
- **`Publicar alterações`**: ação explícita que grava a versão limpa no destino autorizado. Nunca ocorre automaticamente a cada edição/keystroke.
- **`Exportar página`**: fallback/portabilidade; baixa um HTML limpo. Não é mais o caminho principal para atualizar um site quando o publish backend está disponível.

### HARD RULE — não auto-publicar edição

```text
editar texto/imagem/link
≠ publicar
```

O fluxo correto é:

```text
Editar
→ opcional Salvar rascunho
→ Pré-visualizar
→ Publicar alterações
→ confirmação explícita
→ backend autorizado
→ site atualizado
```

Uma alteração de DOM nunca deve chegar à produção apenas porque o cliente digitou algo.

## Publicação em localhost — suportada

Para testar edição real localmente, não use apenas `python -m http.server` se quiser que o botão `Publicar alterações` escreva no arquivo.

Na raiz do workspace:

```bash
python editor_server.py
```

Servidor padrão:

```text
http://127.0.0.1:8787
```

Abra o editor através desse servidor:

```text
http://127.0.0.1:8787/sites/[slug]/[slug]-editor.html
```

Ao clicar **Publicar alterações** em `local` mode:

```text
editor
→ POST /api/editor/publish
→ valida target canônico sites/[slug]/[slug].html
→ cria backup
→ grava HTML limpo atomicamente
→ site localhost passa a servir a nova versão
```

O target permitido é estrito: `sites/<slug>/<slug>.html`. Path traversal e escrita arbitrária fora de `sites/` são bloqueados.

O servidor local faz backup em `.prospector-editor/backups/` antes de substituir um arquivo existente. Drafts server-side ficam em `.prospector-editor/drafts/`.

Se outro servidor local (ex.: porta 8088) também estiver servindo os mesmos arquivos, ele refletirá a alteração depois do publish/refresh porque o arquivo no disco foi atualizado. Para usar o botão de publish, porém, abra o editor pelo `editor_server.py` ou configure explicitamente um endpoint compatível.

## Publicação em deploy — mesmo botão, backend protegido

`Publicar alterações` usa a mesma API conceitual em local e produção. O comportamento vem do backend:

```text
local mode
→ atualiza sites/[slug]/[slug].html no workspace

git mode
→ atualiza somente [basePath]/[slug]/index.html no clone de deploy
→ git add SOMENTE desse caminho
→ commit
→ push branch configurada
→ Vercel auto-deploy
```

O backend de referência é:

```text
prospector-de-sites/editor_publish_server.py
```

Modo local é default. Modo Git deve ser habilitado deliberadamente:

```text
PROSPECTOR_EDITOR_PUBLISH_MODE=git
```

Ele usa `deploy.repoPath`, `deploy.basePath` e `deploy.branch` do config quando disponíveis, ou overrides por environment/CLI.

### HARD RULE — autorização de produção

Nunca exponha `git mode` ou o editor online sem autenticação real.

Para backend não-local/git, `PROSPECTOR_EDITOR_CLIENTS` é obrigatório e deve mapear um **token opaco de editor** aos slugs permitidos. Esse token NÃO é GitHub/Vercel credential.

Exemplo conceitual:

```json
{
  "opaque-editor-token-a": ["cliente-a"],
  "opaque-editor-token-b": ["cliente-b"]
}
```

Git credentials ficam apenas no servidor via Git Credential Manager/SSH/secret server-side. Nunca embuta GitHub PAT ou Vercel token no editor.

Para entrega real ao cliente, coloque o backend atrás de HTTPS e autenticação/session/reverse proxy. O token prompt do backend de referência é um mecanismo técnico de autorização por slug, não substitui a UX final de login/magic-link.

### Static Vercel sozinho não é CMS

Um deploy puramente estático na Vercel não ganha persistência apenas porque o botão existe. Para o cliente publicar no ar, `/api/editor/publish` deve apontar para um backend protegido com acesso server-side ao repositório de deploy.

Não vender/publicar o editor como auto-CMS em produção se esse backend ainda não estiver efetivamente configurado para aquele cliente.

## QA obrigatória do editor

Para cada site novo, teste no `*-editor.html` pelo menos:

1. CTA principal do hero abre propriedades, não navega.
2. CTA sticky/flutuante do WhatsApp abre propriedades.
3. Clique diretamente no SVG de Instagram/Facebook abre o link pai no editor.
4. Link social somente com ícone permite alterar URL e `aria-label`.
5. Alterar `business.whatsapp` com sincronização atualiza navbar + hero + sticky + footer quando existirem.
6. **Clique diretamente no logo do header abre `Logo / marca` como mídia, não o link da home.**
7. Trocar `brand.logo` altera todas as ocorrências compartilhadas relevantes (ex.: header + footer).
8. Logo dentro de `<a href="/">` continua substituível sem navegar.
9. Se houver `<picture>`, a alteração não fica visualmente anulada por `source/srcset` antigo.
10. `Salvar rascunho` NÃO altera o HTML público.
11. Reload oferece restauração do draft local salvo quando existente.
12. Em `editor_server.py` local, editar texto → `Publicar alterações` → refresh do HTML público mostra a alteração.
13. Publish exige confirmação explícita.
14. Publish local cria backup antes da substituição quando existe versão anterior.
15. Backend rejeita target fora de `sites/<slug>/<slug>.html`.
16. Em git mode, token/slug não autorizado recebe 401 e nada é publicado.
17. Em git mode, somente o path do cliente é staged/committed; mudanças previamente staged fazem o backend recusar publish misto.
18. Preview volta a permitir navegação real.
19. HTML publicado/exportado não contém toolbar, painel, `contenteditable` ou runtime do editor.
20. `Exportar página` continua funcionando como fallback, sem ser confundido com publicação.

Se qualquer CTA/social relevante, logo principal ou fluxo explícito de publish falhar conforme sua função, o editor falhou QA e não deve ser considerado concluído.
