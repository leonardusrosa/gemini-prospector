---
name: prospector-setup
description: Configuração inicial do Prospector de Sites no Antigravity — coleta identidade real de outreach, assinatura, portfólio, nichos, cidade e configuração de deploy (GitHub + Vercel), e instala o painel local. Use quando o usuário disser "configurar prospector", "setup", "começar", "meus dados", ou na primeira vez que rodar qualquer skill do prospector sem um prospector-config.json.
---

# Prospector — Configuração Inicial (Antigravity)

Rode UMA vez. Salva tudo em `prospector-config.json` na pasta de trabalho do projeto.

## 1. Verificar Config Existente e Migração

Procure `prospector-config.json` na pasta do projeto.
- Se já existir com o bloco `hostgator` antigo: faça a migração automática preservando todos os dados de assinatura, prospecção e envio, criando o bloco `deploy` no lugar e mantendo um backup `prospector-config.backup.json`.
- Se existir no formato atual: mostre um resumo e pergunte o que atualizar.
- Se não existir: colete os dados abaixo em blocos curtos.

## 2. Identidade real de outreach

A identidade usada em proposta, e-mail ou WhatsApp precisa corresponder a uma pessoa/empresa real e autorizada pelo usuário.

Colete ou confirme:

- **Nome real do operador/autor**: nome completo que pode ser apresentado ao prospecto.
- **Apresentação real**: função, empresa ou descrição curta do serviço, sem credencial inventada.
- **WhatsApp real do operador** em formato internacional `DDI+DDD+número`.
- **Marca/empresa**, quando aplicável, integrada naturalmente à apresentação.
- **URL de portfólio/oferta** em `outreach.portfolioUrl`, quando houver uma página pública apropriada.

### HARD RULE — fail closed para identidade ausente

Nunca fabricar identidade, cargo ou apresentação para preencher campos vazios.

São proibidos fallbacks como:

- `Especialista em Web`
- `Criação e Redesign de Páginas`
- qualquer nome, cargo, empresa ou credencial que o usuário não tenha confirmado

Antes de gerar mensagem pronta para envio ou enviar outreach, `assinatura.nome` e `assinatura.apresentacao` precisam estar preenchidos com identidade real. Para envio por canais que expõem contato do operador, `assinatura.whatsapp` também precisa estar configurado quando aplicável.

Se algum campo obrigatório estiver ausente, interrompa a geração/envio e peça apenas o dado faltante. Nunca substitua por texto genérico inventado.

A URL de portfólio pode apontar para uma página ainda em evolução comercial, mas preços, FAQ, métricas ou claims dessa página não devem ser copiados para mensagens/propostas sem verificação atual.

## 3. Dados de prospecção

- **Nichos padrão**: sugira nutricionistas, psicólogos, advogados, psiquiatras — deixe editar.
- **Cidade/região padrão**.
- **Leads por busca**: padrão 10.
- **Modo de envio da proposta**: padrão revisão humana antes de qualquer envio.

## 4. Configuração de Deploy (GitHub + Vercel)

A publicação é feita via repositório Git conectado à Vercel:

1. **Detecção do ambiente**:
   - Verificar se `git` está instalado no sistema (`git --version`).
   - Solicitar/verificar o caminho local do repositório de publicação (`repoPath`, ex.: `C:/Projetos/prospector-sites`).
2. **Inspeção do repositório Git**:
   - Verificar se `repoPath` já é um repositório Git inicializado.
   - Detectar o remote origin (`git remote -v`) para identificar `githubRepo`.
   - Detectar a branch atual/padrão (normalmente `main`).
   - Se já estiver configurado, reutilizar os dados automaticamente sem recriar ou alterar o histórico.
3. **Domínio público**:
   - Coletar o domínio da Vercel ou domínio próprio vinculado.
   - Pasta base: padrão `clientes`.
4. **Sem senhas no chat**:
   - Nunca solicitar tokens, senhas de GitHub ou chaves de API.
   - A autenticação Git é gerenciada pelo sistema operacional.

## 5. Salvar Configuração

Salvar em `prospector-config.json` na pasta do projeto:

```json
{
  "assinatura": {
    "nome": "",
    "apresentacao": "",
    "whatsapp": ""
  },
  "prospeccao": {
    "nichos": ["nutricionistas", "psicologos", "advogados", "psiquiatras"],
    "cidade": "",
    "leadsPorBusca": 10
  },
  "envio": {
    "modo": "rascunho"
  },
  "outreach": {
    "channelPriority": ["whatsapp", "email"],
    "mode": "review",
    "portfolioUrl": "",
    "maxFollowUps": 1,
    "followUpAfterBusinessDays": 3
  },
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

> **Evolution API**: a chave nunca passa pelo chat nem é salva no JSON. Configure-a por variável de ambiente.

## 6. Sincronização local e produção

Quando o dashboard/CRM canônico estiver em uma VPS, a configuração efetiva de identidade precisa ser sincronizada entre o workspace local e a configuração persistente usada pela instância de produção.

Antes de qualquer outreach real:

1. leia a configuração efetiva local;
2. leia a configuração efetiva da VPS sem imprimir segredos;
3. confirme que `assinatura.nome`, `assinatura.apresentacao`, `assinatura.whatsapp` e `outreach.portfolioUrl` são os valores aprovados;
4. gere uma mensagem de teste em modo review;
5. confirme que nenhum fallback inventado aparece;
6. não envie nada durante o teste.

## 7. Painel local

Siga a skill `dashboard-leads` para copiar `dashboard-server.py` + o iniciador e criar o banco `prospector.db` e o `dashboard.html`.

## 8. Pré-requisitos do Antigravity

1. **Plugin Google Maps Platform** — busca oficial de negócios via Places.
2. **MCP de Navegador (Playwright)** — inspeciona páginas e coleta e-mails.
3. **MCP do Prospector CRM** (`prospector-mcp.py`) — gerencia leads e SQLite.
4. (Opcional) **MCP/Plugin do Gmail** — rascunhos de e-mail automatizados.

## 9. Encerrar

Confirme os dados salvos e apresente o ciclo:
**prospectar** → **redesenhar** → **publicar** → **outreach / proposta**, com revisão humana antes de qualquer envio real.