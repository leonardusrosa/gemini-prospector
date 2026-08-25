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

## 3. Fluxo de Publicação

Ao receber ordens como *"publica os 5 redesigns"* ou *"sobe o site da clinica-exemplo"*:

1. **Validação local**:
   - Verificar se `prospector-config.json` possui o bloco `deploy` preenchido.
   - Verificar se o arquivo do redesign existe em `sites/[slug]/[slug].html`.
2. **Preparação de arquivos**:
   - Criar diretório `[repoPath]/[basePath]/[slug]/`.
   - Copiar `sites/[slug]/[slug].html` para `[repoPath]/[basePath]/[slug]/index.html`.
   - Se houver `sites/[slug]/proposta.html`, copiar para `[repoPath]/[basePath]/[slug]/proposta.html`.
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
