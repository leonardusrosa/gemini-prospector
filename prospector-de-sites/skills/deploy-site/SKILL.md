---
name: deploy-site
description: Esta skill deve ser usada ao publicar páginas via GitHub e Vercel — cópia para repositório Git local, commit, push para o GitHub, verificação de URL pública HTTPS na Vercel e atualização do CRM e dashboard. Acione quando o usuário disser "publicar", "subir o site", "colocar no ar", "deploy", "publicar redesign", "vercel", "github" ou pedir para publicar (skill deploy-site).
---

# Deploy de Sites — GitHub + Vercel

Publicar páginas estáticas em repositório dedicado no GitHub conectado à Vercel, garantindo a URL pública `https://[domain]/[basePath]/[slug]/` ativa e validada.

## 1. Configuração

Todas as definições de deploy ficam no `prospector-config.json` (bloco `deploy`):

```json
{
  "deploy": {
    "provider": "vercel-github",
    "repoPath": "C:/caminhos/prospector-sites",
    "githubRepo": "usuario/prospector-sites",
    "branch": "main",
    "basePath": "clientes",
    "domain": "prospector-sites.vercel.app"
  }
}
```

- **`repoPath`**: caminho absoluto local do clone Git usado para publicação.
- **`githubRepo`**: identificador `usuario/repositorio` no GitHub.
- **`branch`**: branch de produção configurada na Vercel (padrão: `main`).
- **`basePath`**: subpasta de clientes no repositório (padrão: `clientes`).
- **`domain`**: domínio público da Vercel ou domínio próprio vinculado.

> **Segurança de credenciais**: NUNCA armazene nem solicite tokens ou senhas no chat ou no arquivo de configuração. A autenticação depende da configuração Git do próprio sistema operacional (Git Credential Manager, GitHub CLI `gh auth login` ou chaves SSH).

## 2. Estrutura do Repositório de Publicação

O repositório dedicado de previews deve seguir a estrutura:

```text
prospector-sites/
├── index.html
├── robots.txt
└── clientes/
    ├── clinica-exemplo/
    │   ├── index.html
    │   └── proposta.html (opcional)
    └── ...
```

- A página principal do cliente (`sites/[slug]/[slug].html`) é publicada como `[repoPath]/[basePath]/[slug]/index.html`.
- A página de proposta (`sites/[slug]/proposta.html`), quando existir, é publicada como `[repoPath]/[basePath]/[slug]/proposta.html`.
- URL final do site: `https://[domain]/[basePath]/[slug]/`
- URL da proposta: `https://[domain]/[basePath]/[slug]/proposta.html`

### HARD RULE — não publicar `*-editor.html` como página pública desprotegida

O arquivo visual `sites/[slug]/[slug]-editor.html` é uma ferramenta de edição, não uma página pública do prospecto.

Durante preview/prospecção:
- não copiar `*-editor.html` para a pasta pública;
- não enviar URL pública do editor ao lead;
- não assumir que um arquivo estático em `/admin` está protegido só porque a URL não foi divulgada.

Para cliente final, o editor só pode ser exposto online quando houver autenticação/autorização real conforme a seção **Client CMS** abaixo.

---

## 3. Fluxo de Publicação

Ao receber ordens como *"publica os 5 redesigns"* ou *"sobe o site da clinica-exemplo"*:

1. **Validação local**:
   - Verificar se `prospector-config.json` possui o bloco `deploy` preenchido.
   - Verificar se o arquivo do redesign existe em `sites/[slug]/[slug].html`.
2. **Preparação de arquivos**:
   - Criar diretório `[repoPath]/[basePath]/[slug]/`.
   - Copiar `sites/[slug]/[slug].html` para `[repoPath]/[basePath]/[slug]/index.html`.
   - Se houver `sites/[slug]/proposta.html`, copiar para `[repoPath]/[basePath]/[slug]/proposta.html`.
   - **Não copiar `*-editor.html` automaticamente.**
   - Garantir `robots.txt` na raiz de `repoPath` (`User-agent: *\nDisallow: /`) para evitar indexação de rascunhos.
   - Garantir `index.html` básico na raiz se ainda não existir.
3. **Controle Git seguro**:
   - Executar `git status --porcelain` no `repoPath`. Se nada foi alterado, pular commit/push e ir direto para a verificação da URL.
   - Conferir se o remote `origin` bate com `githubRepo` (`git remote -v`). Se houver divergência, pausar e alertar o usuário.
   - Adicionar apenas os arquivos necessários (`git add [basePath]/[slug]`).
   - Criar commit descritivo: `Deploy prospect: [slug]` ou `Deploy N prospect previews`.
   - Executar `git push origin [branch]`. **NUNCA usar `--force`**.
4. **Tratamento de exceções Git**:
   - Se o push for rejeitado por commits remotos mais recentes: inspecione a branch, execute `git pull --rebase origin [branch]` de forma limpa, preservando os arquivos locais gerados, e repita o push.
   - Se houver erro de autenticação: oriente o usuário a autenticar o Git no terminal via Git Credential Manager ou `gh auth login`. Nunca peça credenciais no chat.

## 4. Verificação Pública e Validação de Conteúdo

Após o push com sucesso:

1. Montar a URL: `https://[domain]/[basePath]/[slug]/`.
2. Fazer requisição HTTP para a URL.
3. **Validar resposta**:
   - Resposta HTTP 200 com HTTPS válido.
   - Confirmar que o corpo HTML contém o conteúdo real do cliente (ex.: nome do estabelecimento ou título específico), garantindo que não é uma página 404 genérica da Vercel.
4. **Propagação Vercel**:
   - A Vercel costuma levar de 5 a 15 segundos para fazer o deploy automático do commit.
   - Se na primeira checagem retornar 404, aguarde 5 segundos e tente novamente (até 3 tentativas).
   - Se após o intervalo a URL ainda não responder com o conteúdo esperado, relate o status como: `push concluído, deploy ainda não verificado` e NÃO marque como `publicado` definitivo.

## 5. Atualização do CRM e Dashboard

Quando a URL for verificada com sucesso:

1. Atualizar lead no banco `prospector.db`:
   - `status = 'publicado'`
   - `urlNova = 'https://[domain]/[basePath]/[slug]/'`
2. No MCP: chamar `salvar_lead(slug=slug, urlNova=url)` e `atualizar_status(slug, 'publicado')`.
3. Chamar `regenerar_dashboard()` para atualizar o `dashboard.html`.
4. Informar ao usuário as URLs publicadas ativas prontas para a etapa de proposta.

---

## 6. Client CMS — Entrega do Editor ao Cliente

O editor visual gerado pelo Prospector possui agora a interface de edição e um **publish bridge de referência** para localhost e backend Git protegido:

```text
prospector-de-sites/editor_publish_server.py
```

A experiência deve continuar sendo:

```text
site-do-cliente.com
        ↓
/editor protegido
        ↓
login / sessão autorizada
        ↓
editor visual
        ↓
Salvar rascunho / Pré-visualizar / Publicar alterações
        ↓
backend autorizado
        ↓
validação por cliente + slug
        ↓
Git commit restrito ao diretório do cliente
        ↓
Vercel deploy
        ↓
site atualizado
```

O cliente não deve precisar ver GitHub, Vercel ou HTML.

### HARD RULE — Publish é explícito

Editar não publica.

```text
keystroke/edit
≠ deploy
```

O editor oferece ações separadas:

- **Salvar rascunho**: mantém snapshot sem alterar produção;
- **Pré-visualizar**: testa a versão editada;
- **Publicar alterações**: exige confirmação explícita;
- **Exportar página**: fallback/portabilidade, não mecanismo principal de deploy.

Nunca publicar automaticamente a cada keystroke.

### Local publish mode — disponível

Na raiz do workspace:

```bash
python editor_server.py
```

Abra:

```text
http://127.0.0.1:8787/sites/[slug]/[slug]-editor.html
```

Em `local` mode o botão `Publicar alterações`:

```text
POST /api/editor/publish
→ aceita somente target sites/[slug]/[slug].html
→ cria backup em .prospector-editor/backups/
→ faz atomic write do HTML limpo
→ localhost passa a servir a nova versão após refresh
```

Isso permite testar o fluxo real antes de deploy. `python -m http.server` continua válido para preview somente, mas não implementa POST/persistência.

### Git publish mode — backend de referência

Quando explicitamente configurado:

```text
PROSPECTOR_EDITOR_PUBLISH_MODE=git
```

o backend mapeia a publicação do editor para:

```text
[deploy.repoPath]/[deploy.basePath]/[slug]/index.html
```

Depois:

1. recusa se já houver mudanças previamente staged, evitando commit misto;
2. `git add` somente no path daquele cliente;
3. cria commit `Client publish: [slug]`;
4. `git push` para remote/branch configurados;
5. Vercel pode executar auto-deploy pela integração existente.

O backend não usa `--force`.

### HARD RULE — nenhuma credencial Git/Vercel no navegador

Nunca inserir no HTML/editor:
- GitHub PAT/token;
- Vercel token;
- chave privada;
- Git credential;
- segredo mestre do backend.

Toda escrita no GitHub/Vercel acontece server-side.

### Autorização por site

Para qualquer modo Git ou bind não-local, o backend de referência exige `PROSPECTOR_EDITOR_CLIENTS`, mapeando **token opaco de editor** → slug(s) autorizados.

Exemplo conceitual:

```json
{
  "opaque-client-token-a": ["instituto-ferreira"],
  "opaque-client-token-b": ["outro-cliente"]
}
```

Esse token é somente autorização do editor. **Nunca reutilizar GitHub PAT/Vercel token como token do cliente.**

Uma credencial/sessão do cliente deve autorizar apenas o próprio site:

```text
cliente: instituto-ferreira
permitido: clientes/instituto-ferreira/index.html
bloqueado: clientes/outro-cliente/**
bloqueado: plugin/**
bloqueado: dashboard/**
```

Bloquear path traversal e qualquer caminho fora do slug autorizado.

Para produção real, colocar o backend atrás de HTTPS e login/session/reverse proxy. O prompt de token do backend de referência é um mecanismo técnico mínimo de autorização por slug, não a UX final de autenticação.

### HARD RULE — static Vercel sozinho não fornece persistência

Uma página estática na Vercel não consegue gravar no GitHub sozinha.

Para o botão `Publicar alterações` funcionar no deploy, `/api/editor/publish` deve ser roteado para o backend protegido, com Git credentials server-side e autorização daquele slug.

Não publicar `*-editor.html` desprotegido e não afirmar que o Client CMS online está funcional para um cliente antes dessa rota/autenticação estar realmente configurada.

### Campos publicáveis pelo cliente

Permitir por padrão apenas conteúdo de negócio através da UI do editor:
- texto;
- imagens/alt/logo;
- telefone;
- WhatsApp + mensagem;
- e-mail;
- socials;
- booking;
- Maps;
- horários/endereço quando modelados como conteúdo editável.

Bloquear na UI:
- CSS/design system;
- estrutura HTML arbitrária;
- JavaScript/GSAP;
- analytics;
- secrets;
- deploy config;
- dependências externas.

O publish bridge também rejeita documentos contendo runtime/UI do editor e restringe rigidamente o target; segurança de produção ainda depende de autenticação e exposição controlada do editor.

### Dados compartilhados

Campos como `brand.logo`, `business.whatsapp`, `business.phone`, `business.instagram` etc. devem atualizar todas as ocorrências relevantes do site de uma vez.

### Versionamento e rollback

Em Git mode, cada publicação gera commit SHA identificável. O backend retorna o SHA ao editor quando o push é concluído.

Manter no roadmap/entrega completa:
- autor/cliente;
- timestamp;
- slug;
- resumo dos campos alterados;
- UI de rollback/restauração.

Local mode cria backup antes de sobrescrever a página pública para permitir recuperação manual durante desenvolvimento.

### Status atual do Prospector

```text
editor visual = disponível
edição de textos/imagens/links/logo = disponível
Salvar rascunho = disponível (browser + backend quando alcançável)
Publicar alterações em localhost = disponível via editor_server.py
publish bridge Git restrito por slug = implementado como backend de referência
Vercel auto-deploy após push = compatível com integração existente
login/magic-link final do cliente = ainda deve ser configurado/implementado por entrega
/editor público protegido = NÃO presumir sem infraestrutura real
```

A proposta comercial deve distinguir **capacidade implementada** de **configuração de produção concluída**. Não vender `/editor` protegido/login como pronto para um cliente enquanto essa infraestrutura não estiver efetivamente configurada.
