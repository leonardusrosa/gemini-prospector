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

O editor visual gerado pelo Prospector já resolve a **interface de edição**. Para o cliente alterar o próprio site no ar sem depender do desenvolvedor, falta uma camada autenticada de persistência/publicação.

### Experiência-alvo

```text
site-do-cliente.com
        ↓
site-do-cliente.com/admin
        ↓
login / magic link
        ↓
editor visual
        ↓
Salvar rascunho / Publicar
        ↓
backend autorizado
        ↓
validação por cliente + slug + campos permitidos
        ↓
GitHub commit restrito ao diretório do cliente
        ↓
Vercel deploy
        ↓
site atualizado
```

O cliente não deve precisar ver GitHub, Vercel, HTML ou tokens.

### HARD RULE — nenhuma credencial no navegador

Nunca inserir no HTML/editor:
- GitHub PAT/token;
- Vercel token;
- chave privada;
- credencial do backend;
- segredo de sessão mestre.

Toda escrita no GitHub/Vercel deve acontecer server-side.

### Autorização por site

Uma sessão do cliente deve ser autorizada apenas para o próprio site. Exemplo:

```text
cliente: instituto-ferreira
permitido: clientes/instituto-ferreira/**
bloqueado: clientes/outro-cliente/**
bloqueado: plugin/**
bloqueado: dashboard/**
```

Bloquear path traversal e qualquer caminho fora do slug autorizado.

### Campos publicáveis pelo cliente

Permitir por padrão apenas conteúdo de negócio:
- texto;
- imagens/alt;
- telefone;
- WhatsApp + mensagem;
- e-mail;
- socials;
- booking;
- Maps;
- horários/endereço quando modelados como conteúdo editável.

Bloquear:
- CSS/design system;
- estrutura HTML arbitrária;
- JavaScript/GSAP;
- analytics;
- secrets;
- deploy config;
- dependências externas.

### Dados compartilhados

Campos como `business.whatsapp`, `business.phone`, `business.instagram` etc. devem atualizar todas as ocorrências relevantes do site de uma vez.

### Save Draft x Publish

Manter ações separadas:
- **Salvar rascunho**: persiste conteúdo sem afetar produção;
- **Publicar**: exige ação explícita e dispara a atualização do site.

Nunca publicar automaticamente a cada keystroke.

### Versionamento e rollback

Como o deploy já usa Git, cada publicação deve gerar versão identificável. O Client CMS deve registrar:
- autor/cliente;
- timestamp;
- slug;
- resumo dos campos alterados;
- commit SHA.

Permitir restaurar a versão anterior sem editar Git manualmente.

### Status atual do Prospector

Até que um backend autenticado de Client CMS esteja implementado/configurado:

```text
editor visual = disponível
edição de textos/imagens/links = disponível
exportação de HTML atualizado = disponível
publicação autônoma pelo cliente = NÃO presumir
/admin protegido = NÃO presumir
```

A proposta comercial deve ser fiel a esse status. Não vender publicação autônoma como pronta se o backend ainda não existir.
