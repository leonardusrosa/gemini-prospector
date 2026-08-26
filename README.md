# Prospector de Sites — Plugin para Google Antigravity

Prospecção semiautomática de clientes com site fraco, redesign premium, publicação automática via GitHub + Vercel e proposta multicanal — empacotado como **Plugin do Antigravity** (Agy 2.0 / IDE / CLI compartilham a mesma config).

É a mesma lógica da versão Claude, no formato nativo do Antigravity: um **plugin** (`plugin.json` + `mcp_config.json` + `skills/`). A busca de negócios usa o plugin oficial **Google Maps Platform** (Places); o navegador entra só pra avaliar o site do lead.

## Estrutura do plugin

```text
prospector-de-sites/          ← esta é a pasta do plugin
├── plugin.json               marcador do plugin
├── mcp_config.json           define os MCP (CRM + navegador Playwright)
├── prospector-mcp.py         servidor MCP do CRM (SQLite)
├── evolution_client.py       conector seguro Evolution API WhatsApp
├── outreach_service.py       gerador e orquestrador de outreach multicanal
├── editor_publish_server.py  backend de referência para draft/publish local ou Git
├── skills/                   as 8 skills (SKILL.md)
│   ├── prospector-setup/
│   ├── prospeccao-maps/
│   ├── redesign-premium/
│   ├── expert-hero-assets/   geração autônoma de hero desktop/mobile a partir de expert real
│   ├── outreach-proposta/    outreach multicanal (WhatsApp + Gmail)
│   ├── deploy-site/          deploy via GitHub + Vercel
│   ├── dashboard-leads/
│   └── contrato-servico/
└── dashboard/                painel local (Python/SQLite)
```

Na raiz do workspace:

- `create_editor.py` gera o editor visual client-ready;
- `editor_server.py` serve o site/editor e habilita `Salvar rascunho` + `Publicar alterações` em localhost.

## Instalação

### 1. Instalar o plugin

Copie a pasta `prospector-de-sites/` inteira para um dos locais que o Antigravity varre:

- **Global (todos os projetos):** `~/.gemini/config/plugins/prospector-de-sites/`
  (no Windows: `C:\Users\SEU_USUARIO\.gemini\config\plugins\prospector-de-sites\`)
- **Só no projeto atual:** `.agents/plugins/prospector-de-sites/` na raiz do workspace aberto.

As **skills** carregam sozinhas — não precisa copiar nada pra `~/.gemini/skills` na mão.

### 2. Ajustar o `mcp_config.json` do plugin

Abra `prospector-de-sites/mcp_config.json` e corrija os dois caminhos do `prospector-crm`:

- o caminho do `prospector-mcp.py` (dentro da pasta do plugin);
- o `--pasta` = a pasta do seu projeto (onde ficam `prospector.db`, os leads e os sites).

O Antigravity lê esse `mcp_config.json` do plugin automaticamente.

### 3. Instalar o plugin Google Maps Platform (a fonte da prospecção)

Em **Settings → Customizations → Build with Google**, baixe o plugin **Google Maps Platform**. Ele dá as ferramentas de Places (buscar negócios, ler nota, nº de avaliações, site, telefone) que a skill `prospeccao-maps` usa. Precisa de uma **API key do Google Maps Platform** (tem cota grátis mensal).

> Sem o plugin do Maps, a prospecção ainda funciona no modo navegador (raspando o Google Maps pelo Playwright) — só é menos confiável.

### 4. Configurar o Prospector

Abra a pasta do projeto e diga no chat: **"configurar o prospector"**. A skill `prospector-setup` coleta seus dados, o repositório Git de publicação e instala o painel local.

## Como usar (linguagem natural)

1. **"prospecta nutricionistas em São Paulo"** → busca no Google Maps Platform, qualifica e monta o dashboard.
2. **"redesenha os 5 melhores"** → redesign premium + assets de hero quando aplicável + editor + comparador antes/depois.
3. **"publica os redesigns"** → copia para o repositório Git local, faz commit/push para o GitHub, a Vercel publica e o plugin valida o HTTPS público.
4. **"manda a proposta"** → outreach multicanal (WhatsApp via Evolution API ou Gmail) com link da proposta personalizada.
5. Depois: contrato, e o `dashboard.html` administra tudo (kanban + financeiro + histórico de outreach).

## Hero expert autônomo

Quando `redesign-premium` classifica o hero como `expert_fullscreen` e existe uma foto real/verificada do profissional, a skill `expert-hero-assets` entra como etapa de produção antes do HTML final do hero.

Outputs canônicos:

```text
sites/[slug]/assets/hero-expert-desktop.webp
sites/[slug]/assets/hero-expert-mobile.webp
```

Padrão visual atual:

- **desktop**: preferir composição **ultrawide ~2.3:1–2.6:1** quando há copy à esquerda e expert à direita; expert centrado na metade direita (`x≈75%`), `contain`/rendering subject-safe, sem zoom destrutivo, edge integration quando necessária e alta resolução real (tipicamente 3.5K–4.5K+ de largura quando a fonte suporta);
- **mobile**: composição vertical própria, expert grande no top ~50–55%, head + upper body, sem mostrar waist-down, lower half calma para headline/CTA HTML;
- identidade/pose reais têm prioridade sobre novidade estética;
- se a geração mudar materialmente o rosto, usar fallback source-preserving com o expert original;
- `4200×1728 WebP ~417 KB` é benchmark forte de qualidade para desktop ultrawide, não hard limit.

### Capability/billing order

O fluxo padrão prefere primeiro a capacidade de geração/edição de imagem que já estiver disponível na sessão do **Google Antigravity**.

```text
Antigravity-native
→ source-preserving fallback
→ API/provider externo apenas se explicitamente configurado
```

O Prospector **não exige `GEMINI_API_KEY` por padrão**, não deve pedir API key automaticamente para gerar o hero e não pode ativar uma rota paga silenciosamente. Assinatura Google AI Pro/quota do Antigravity e billing de Gemini API devem ser tratados como coisas distintas.

A referência completa de prompts, QA, identidade e fallback fica em:

```text
prospector-de-sites/skills/redesign-premium/references/expert-hero-generation.md
```

## Editor visual client-ready

Para qualquer site gerado:

```bash
python create_editor.py sites/[slug]/[slug].html
```

Isso cria:

```text
sites/[slug]/[slug]-editor.html
```

O editor permite, sem editar código:

- alterar headings, parágrafos e textos;
- trocar imagens, logo e `alt`;
- editar label + hyperlink de CTAs;
- editar WhatsApp e mensagem pré-preenchida;
- editar telefone e e-mail;
- editar Instagram/Facebook/outros links reais;
- sincronizar destinos/brand assets repetidos;
- salvar rascunho;
- pré-visualizar a página;
- **publicar alterações explicitamente** quando o publish backend está disponível;
- exportar HTML limpo como fallback/portabilidade.

### Localhost com publicação real

Para testar persistência real no arquivo local:

```bash
python editor_server.py
```

Abra o editor via:

```text
http://127.0.0.1:8787/sites/[slug]/[slug]-editor.html
```

Fluxo:

```text
Editar
→ Salvar rascunho (opcional)
→ Pré-visualizar
→ Publicar alterações
→ confirmação
→ backup
→ sites/[slug]/[slug].html atualizado atomicamente
```

A publicação **não** ocorre a cada keystroke.

`python -m http.server` continua útil para preview, mas sozinho não fornece endpoint de escrita. Se outro servidor estiver servindo os mesmos arquivos, ele refletirá o HTML atualizado após o publish + refresh.

### Deploy / Client CMS

O mesmo botão `Publicar alterações` pode usar o backend de referência em `git mode`, que escreve somente `[basePath]/[slug]/index.html`, faz `git add` apenas daquele path, commit e push; a Vercel pode então auto-deployar pela integração existente.

Produção exige:

- HTTPS;
- editor protegido/autenticado;
- autorização restrita por slug;
- Git credentials somente server-side;
- rota `/api/editor/publish` realmente conectada ao backend.

Um deploy Vercel puramente estático **não vira CMS sozinho**. Nunca exponha `*-editor.html` publicamente sem proteção e nunca coloque GitHub/Vercel tokens no browser.

Para CTAs complexos, use `data-pe-label`; para contatos/socials/logo repetidos, `data-pe-field`; e para backgrounds editáveis, `data-pe-bg`. A referência canônica está em `prospector-de-sites/skills/redesign-premium/references/editor-visual.md`.

## Diferenças pra versão Claude

| | Claude Cowork | Antigravity |
|---|---|---|
| Empacotamento | plugin (.claude-plugin) | plugin (`plugin.json` + `mcp_config.json` + `skills/`) |
| Onde instala | marketplace | `~/.gemini/config/plugins/` (ou `.agents/plugins/`) |
| Comandos | `/prospectar`… | linguagem natural aciona a skill |
| Busca no Maps | Claude in Chrome | **plugin Google Maps Platform** (Places) + navegador |
| Navegador | Claude in Chrome | MCP Playwright / plugin Chrome DevTools |
| Publicação | HostGator / FTP | **GitHub + Vercel** (deploy estático automático) |
| CRM | MCP stdio | mesmo MCP, no `mcp_config.json` do plugin |
| Outreach | E-mail manual | **WhatsApp (Evolution API)** + **Gmail** com revisão humana |
| Hero expert | manual/composição | **ultrawide desktop + mobile dedicado, Antigravity-native first** |
| Editor | conteúdo básico | **texto + imagens/logo + CTAs + drafts + publish bridge local/Git** |

Mesma lógica, mesmos entregáveis. O CRM (`prospector-mcp.py`), o painel e as templates são reaproveitados sem mudança.

---

Feito por **Helio Arreche**.
