# Editor visual client-ready

Todo site gerado pelo Prospector deve poder receber uma versão de editor visual sem expor HTML/CSS/JS arbitrário ao cliente.

O objetivo é permitir manutenção cotidiana de conteúdo sem depender do desenvolvedor para cada troca de texto, telefone, WhatsApp, rede social ou imagem.

## Geração

Use o gerador canônico da raiz do projeto:

```bash
python create_editor.py sites/[slug]/[slug].html
```

Saída padrão:

```text
sites/[slug]/[slug]-editor.html
```

O editor é injetado antes de `</body>` e não deve alterar a página pública original.

## O que deve ser editável

### Texto

- headings
- parágrafos
- listas
- captions
- textos editoriais comuns

Colar conteúdo deve virar **texto puro**, sem HTML arbitrário.

### Imagens

Ao clicar em uma imagem, abrir propriedades para:

- trocar arquivo
- editar URL/origem
- editar `alt`

Arquivos escolhidos localmente podem ser incorporados como Data URL no HTML exportado. Para produção em escala, prefira posteriormente um pipeline de upload de assets em vez de Base64.

### Imagens de fundo

Se uma imagem de fundo precisar ser editável pelo cliente, marque o elemento explicitamente:

```html
<section
  data-pe-bg
  data-pe-bg-src="assets/hero.webp"
  style="background-image:url('assets/hero.webp')">
</section>
```

Não dependa de introspecção automática de CSS complexo.

### Botões, links e CTAs

**HARD RULE:** todo botão/link relevante ao negócio deve ser editável no editor.

Inclui:

- WhatsApp
- telefone
- e-mail
- Instagram
- Facebook
- TikTok/YouTube quando reais
- booking/agendamento
- Google Maps
- links internos
- links externos
- CTA de navbar
- CTA de hero
- CTA flutuante
- CTA de rodapé

Ao clicar no link em modo edição, **não navegar**. Abra painel de propriedades.

O painel deve permitir editar:

- texto/label do botão quando houver label simples
- tipo de ação
- destino
- mensagem pré-preenchida do WhatsApp
- `aria-label`
- abrir ou não em nova aba

Tipos suportados:

```text
URL/página
WhatsApp
Telefone
E-mail
Âncora interna
```

URLs com esquemas perigosos como `javascript:` devem ser rejeitadas.

## Campos compartilhados / conteúdo repetido

Contato e socials normalmente aparecem várias vezes. O cliente não deve precisar trocar o mesmo WhatsApp em cinco lugares.

O editor oferece atualização de todos os links com o mesmo destino automaticamente.

Para controle ainda mais robusto, marque elementos equivalentes com `data-pe-field`:

```html
<a
  href="https://wa.me/5511999999999"
  data-pe-field="business.whatsapp">
  <span data-pe-label>Agendar no WhatsApp</span>
</a>

<a
  href="https://wa.me/5511999999999"
  data-pe-field="business.whatsapp"
  aria-label="WhatsApp">
  ...ícone...
</a>
```

Quando `data-pe-field` existe, alterações de destino devem sincronizar todas as ocorrências do campo.

Campos recomendados quando aplicável:

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

Não invente canais ausentes.

## Labels de botões complexos

Para CTAs que contêm SVG/ícone + texto, marque explicitamente a parte editável:

```html
<a href="..." data-pe-field="business.whatsapp">
  <svg aria-hidden="true">...</svg>
  <span data-pe-label>Agendar consulta</span>
</a>
```

Isso evita destruir ícones ao alterar o texto.

Se o botão for apenas ícone, o editor deve alterar o destino e `aria-label`, não substituir o SVG.

## Limites de segurança

O cliente **não** recebe edição arbitrária de:

- HTML
- CSS
- JavaScript
- GSAP/motion logic
- tokens/chaves
- configuração de deploy
- scripts de analytics
- código de terceiros

A experiência deve funcionar como um CMS leve de conteúdo, não como editor de código.

## Preview e exportação

O editor deve oferecer:

- `Pré-visualizar`: desliga temporariamente os handlers de edição e permite testar a página
- `Exportar página`: baixa HTML limpo, sem toolbar/painel/runtime do editor

A exportação deve manter `data-pe-field`, `data-pe-label` e `data-pe-bg` porque esses atributos são inofensivos na página pública e permitem recriar o editor futuramente.

## Publicação pelo próprio cliente

A versão atual do editor é **client-ready para edição**, mas `Exportar página` ainda é o limite seguro do runtime estático.

Não finja que existe publicação direta se não houver backend autenticado.

Para permitir `Salvar rascunho` / `Publicar` no site ao vivo, a arquitetura futura deve ser:

```text
cliente autenticado
→ editor protegido
→ endpoint backend/serverless autorizado
→ valida payload/slug/campos permitidos
→ salva assets
→ commit restrito ao diretório do cliente
→ GitHub
→ Vercel deploy
```

### Segurança da publicação futura

- nunca expor GitHub token no browser
- nunca expor Vercel token no browser
- autenticar cliente
- autorizar cliente apenas ao próprio slug/site
- bloquear path traversal
- aceitar somente campos/assets permitidos
- separar `Salvar rascunho` de `Publicar`
- manter histórico/versionamento
- permitir rollback
- registrar auditoria de publicação

Até esse backend existir e estar protegido, mantenha publicação como ação manual/controlada após exportação.

## QA obrigatório do editor

Para cada novo site, testar pelo menos:

1. editar heading/parágrafo
2. editar label de CTA com ícone sem destruir SVG
3. trocar WhatsApp e confirmar sincronização nas ocorrências repetidas
4. trocar Instagram/Facebook
5. editar telefone/e-mail
6. editar URL normal
7. trocar imagem + `alt`
8. preview permite usar os links normalmente
9. exportação remove totalmente o runtime visual do editor
10. HTML exportado continua funcional e responsivo
11. `javascript:` é rejeitado
12. nenhum segredo/config de deploy aparece no HTML

## Regra permanente de geração

Ao criar qualquer página futura, pense na editabilidade durante o próprio markup:

- CTAs importantes com `<a href>` real em vez de handlers opacos
- `data-pe-label` em labels dentro de botões complexos
- `data-pe-field` em contatos/socials repetidos
- `data-pe-bg` para backgrounds que o cliente deve poder trocar
- `alt` factual e editável em imagens

A editabilidade não deve mudar a estética da página pública.
