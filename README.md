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
├── skills/                   as 7 skills (SKILL.md)
│   ├── prospector-setup/
│   ├── prospeccao-maps/
│   ├── redesign-premium/
│   ├── outreach-proposta/    outreach multicanal (WhatsApp + Gmail)
│   ├── deploy-site/          deploy via GitHub + Vercel
│   ├── dashboard-leads/
│   └── contrato-servico/
└── dashboard/                painel local (Python/SQLite)
```

Na raiz do workspace, `create_editor.py` gera o editor visual client-ready de qualquer site estático criado pelo Prospector.

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
2. **"redesenha os 5 melhores"** → redesign premium + editor + comparador antes/depois.
3. **"publica os redesigns"** → copia para o repositório Git local, faz commit/push para o GitHub, a Vercel publica e o plugin valida o HTTPS público.
4. **"manda a proposta"** → outreach multicanal (WhatsApp via Evolution API ou Gmail) com link da proposta personalizada.
5. Depois: contrato, e o `dashboard.html` administra tudo (kanban + financeiro + histórico de outreach).

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
- trocar imagens e `alt`;
- editar label + hyperlink de CTAs;
- editar WhatsApp e mensagem pré-preenchida;
- editar telefone e e-mail;
- editar Instagram/Facebook/outros links reais;
- sincronizar destinos repetidos (ex.: o mesmo WhatsApp em navbar, hero, footer e botão flutuante);
- pré-visualizar a página com os links funcionando;
- exportar HTML limpo sem a camada do editor.

Para CTAs complexos, o gerador de páginas deve usar `data-pe-label`; para contatos/socials repetidos, `data-pe-field`; e para backgrounds editáveis, `data-pe-bg`. A referência canônica está em `prospector-de-sites/skills/redesign-premium/references/editor-visual.md`.

O editor **não** expõe HTML/CSS/JS arbitrário. Publicação direta pelo próprio cliente só deve ser habilitada quando houver backend autenticado com autorização restrita ao site/slug do cliente; tokens de GitHub/Vercel nunca devem ir para o browser.

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
| Editor | conteúdo básico | **texto + imagens + CTAs + links + WhatsApp/socials** |

Mesma lógica, mesmos entregáveis. O CRM (`prospector-mcp.py`), o painel e as templates são reaproveitados sem mudança.

---

Feito por **Helio Arreche**.
