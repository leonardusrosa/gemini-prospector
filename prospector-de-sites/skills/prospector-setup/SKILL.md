---
name: prospector-setup
description: Configuração inicial do Prospector de Sites no Antigravity — coleta assinatura, nichos, cidade e configuração de deploy (GitHub + Vercel), e instala o painel local. Use quando o usuário disser "configurar prospector", "setup", "começar", "meus dados", ou na primeira vez que rodar qualquer skill do prospector sem um prospector-config.json.
---

# Prospector — Configuração Inicial (Antigravity)

Rode UMA vez. Salva tudo em `prospector-config.json` na pasta de trabalho do projeto.

## 1. Verificar Config Existente e Migração

Procure `prospector-config.json` na pasta do projeto.
- Se já existir com o bloco `hostgator` antigo: faça a migração automática preservando todos os dados de assinatura, prospecção e envio, criando o bloco `deploy` no lugar e mantendo um backup `prospector-config.backup.json`.
- Se existir no formato atual: mostre um resumo e pergunte o que atualizar.
- Se não existir: colete os dados abaixo em blocos curtos.

## 2. Dados do Usuário (pergunte em blocos curtos)

- **Assinatura da proposta**: nome completo, apresentação (ex.: "Designer de páginas de alta conversão") e WhatsApp `55DDDNUMERO`.
- **Nichos padrão**: sugira nutricionistas, psicólogos, advogados, psiquiatras — deixe editar.
- **Cidade/região padrão**.
- **Leads por busca**: padrão 10.
- **Modo de envio da proposta**: padrão "rascunho no Gmail para revisão".

## 3. Configuração de Deploy (GitHub + Vercel)

A publicação é feita via repositório Git conectado à Vercel:

1. **Detecção do ambiente**:
   - Verificar se `git` está instalado no sistema (`git --version`).
   - Solicitar/verificar o caminho local do repositório de publicação (`repoPath`, ex.: `C:/Projetos/prospector-sites`).
2. **Inspeção do repositório Git**:
   - Verificar se `repoPath` já é um repositório Git inicializado.
   - Detectar o remote origin (`git remote -v`) para identificar `githubRepo` (ex.: `usuario/prospector-sites`).
   - Detectar a branch atual/padrão (normalmente `main`).
   - Se já estiver configurado, reutilizar os dados automaticamente sem recriar ou alterar o histórico.
3. **Domínio público**:
   - Coletar o domínio da Vercel ou domínio próprio vinculado (ex.: `prospector-sites.vercel.app` ou `preview.meudominio.com`).
   - Pasta base: padrão `clientes`.
4. **Sem senhas no chat**:
   - Nunca solicitar tokens, senhas de GitHub ou chaves de API.
   - A autenticação Git é gerenciada pelo sistema operacional (Git Credential Manager, SSH ou GitHub CLI).

## 4. Salvar Configuração

Salvar em `prospector-config.json` na pasta do projeto:

```json
{
  "assinatura": { "nome": "", "apresentacao": "", "whatsapp": "" },
  "prospeccao": { "nichos": ["nutricionistas","psicologos","advogados","psiquiatras"], "cidade": "", "leadsPorBusca": 10 },
  "envio": { "modo": "rascunho" },
  "deploy": {
    "provider": "vercel-github",
    "repoPath": "",
    "githubRepo": "",
    "branch": "main",
    "basePath": "clientes",
    "domain": ""
  },
  "evolution": {
    "enabled": false,
    "baseUrl": "",
    "instance": "",
    "apiKeyEnv": "EVOLUTION_API_KEY",
    "timeoutSeconds": 15
  }
}
```

> **Nota sobre Evolution API**: Configuração opcional de integração com WhatsApp na VPS. A chave de API nunca passa pelo chat nem é salva no JSON — configure via variável de ambiente `$env:EVOLUTION_API_KEY="sua_chave"` no terminal.

## 5. Painel Local

Siga a skill `dashboard-leads` para copiar `dashboard-server.py` + o iniciador e criar o banco `prospector.db` e o `dashboard.html`. Explique: duplo clique no `iniciar-dashboard.bat` (Windows) / `.command` (Mac) abre o painel em `http://localhost:8765`.

## 6. Pré-requisitos do Antigravity

1. **Plugin Google Maps Platform** — instalado em Customizations → Build with Google (busca oficial de negócios via Places). Sem ele, a busca opera raspando o Maps pelo Playwright.
2. **MCP de Navegador (Playwright)** — inspeciona páginas e coleta e-mails.
3. **MCP do Prospector CRM** (`prospector-mcp.py`) — gerencia os leads e o banco SQLite.
4. (Opcional) **MCP/Plugin do Gmail** — rascunhos de e-mail automatizados.

## 7. Encerrar

Confirme os dados salvos e apresente o ciclo de trabalho:
**prospectar** (skill prospeccao-maps) → **redesenhar** (skill redesign-premium) → **publicar** (skill deploy-site) → **outreach / proposta** (skill outreach-proposta), com o `dashboard.html` administrando todo o funil.
