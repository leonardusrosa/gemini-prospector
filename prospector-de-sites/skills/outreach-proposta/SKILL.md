---
name: outreach-proposta
description: Esta skill deve ser usada ao escrever e enviar a proposta comercial multicanal para um lead prospectado — seleção automática de canal (WhatsApp via Evolution API ou e-mail Gmail como alternativa), geração de mensagem hiperpersonalizada e factual, sem preço no primeiro contato. Acione quando o usuário disser "enviar proposta", "mandar proposta", "falar com o cliente", "contactar lead", "contato com lead", "enviar no WhatsApp", "mandar no WhatsApp", "enviar e-mail", "mandar o site", "outreach", "proposta" (skill outreach-proposta).
---

# Outreach de Proposta Multicanal (WhatsApp + Gmail)

A primeira mensagem NÃO é um discurso de vendas — ela comprova que um trabalho real já foi feito, desperta curiosidade e abre uma conversa humana.

---

## 1. Arquitetura de Seleção de Canal

A skill inspeciona os canais reais disponíveis do lead e a ordem definida em `outreach.channelPriority` (`prospector-config.json`):

```text
lead aprovado
    ↓
redesign publicado (URL disponível)
    ↓
verificar canais reais e prioritários
    ↓
WhatsApp válido (DDI + DDD) e Evolution API online ('open')?
    ├─ SIM → WhatsApp (preferencial por padrão)
    └─ NÃO
         ↓
E-mail confirmado cadastrado?
         ├─ SIM → Gmail
         └─ NÃO → Alerta: sem canal de contato viável
```

---

## 2. Modos de Operação

### Modo `review` (Padrão e Obrigatório)
1. Gera a mensagem personalizada baseada estritamente em fatos reais do lead.
2. Identifica o canal selecionado e mascara o destino para verificação.
3. Exibe o texto completo e a URL da proposta (`proposta.html`).
4. Aguarda aprovação explícita do usuário antes de qualquer disparo.

### Modo `send` (Envio Individual com Confirmação)
- Dispara a mensagem somente após clique ou confirmação expressa (`confirmed: true`).
- **Proibido envio em lote / campanhas automáticas.** Cada lead é tratado individualmente.

---

## 3. Diretrizes de Mensagem por Canal & Mercado (pt-BR vs pt-PT)

A geração de mensagem recebe `country`, `locale`, `language` e `siteMode`, aplicando o registro nativo de cada mercado.

### HARD RULE — deixar claro que é a primeira proposta funcional, não o site final

O prospecto deve entender simultaneamente que:

1. existe um trabalho real, funcional e já navegável para avaliar;
2. não é um mockup genérico nem apenas uma imagem;
3. **a versão mostrada é uma primeira proposta funcional / primeira versão para demonstração**, ainda aberta a refinamento conjunto antes da entrega final.

Não criar a impressão de que a página enviada já é o produto final fechado.

### Vocabulário recomendado

**pt-BR**

- `primeira proposta funcional de site`
- `primeira proposta de nova versão do site, já funcional`
- `primeira versão para demonstração`
- `serve como ponto de partida`
- `se fizer sentido, a versão final é refinada em conjunto — textos, imagens, prioridades e demais ajustes`

**pt-PT**

- `primeira proposta funcional de site`
- `primeira proposta de nova versão do site, já funcional`
- `primeira versão para demonstração`
- `serve como ponto de partida`
- `se fizer sentido, a versão final é refinada em conjunto — textos, imagens, prioridades e restantes ajustes`

### Evitar

Não usar linguagem que sugira conclusão definitiva, como:

- `site completo`
- `proposta de site completa`
- `nova versão completa do site`
- `site final`
- `site finalizado`
- `versão definitiva`

Também não desvalorizar o trabalho chamando-o de:

- `rascunho`
- `mockup`
- `teste`
- `protótipo simples`

A posição correta é: **trabalho real e funcional, mas primeira proposta sujeita a refinamento com o cliente.**

### A. WhatsApp (Curto, Conversacional e Direto — Permissão Primeiro)
- **Regra fundamental**: O primeiro WhatsApp frio **NUNCA contém link/URL**. O objetivo é abrir conversa humana e pedir permissão antes de enviar o link da proposta.
- **Tamanho**: ~45 a 85 palavras.
- **Fluxo canonical**:
  1. Primeiro contato no WhatsApp: saudação + contextualização real + aviso de que preparou uma primeira proposta funcional + **pedido de permissão para enviar o link**.
  2. Prospecto responde com autorização/interesse.
  3. Envio da mensagem com o link da proposta (`afterPermission`), explicando que é uma versão demonstrativa para refinamento conjunto.
  4. Conversa e alinhamento.
- **Estrutura para Brasil (`pt-BR`)**:
  - *Redesign (primeiro contato)*: "Olá, [nome]! Tudo bem? Vi o trabalho de vocês em [cidade]... Notei que no site atual [motivo]. Por conta disso, preparei uma primeira proposta de nova versão do site, já funcional e adaptada para celular, para mostrar na prática a direção que imaginei. Posso te mandar o link para dar uma olhada? — [Autor]"
  - *Novo Site (primeiro contato)*: "Olá, [nome]! Tudo bem? Vi o trabalho de vocês... Como notei que vocês ainda não possuem um site próprio oficial para facilitar o contato e agendamento de clientes, preparei uma primeira proposta funcional de como o site poderia ficar, já navegável e adaptada para celular. Posso te mandar o link para dar uma olhada? — [Autor]"
  - *Mensagem após permissão*: "Claro. Fiz essa primeira versão principalmente para mostrar a direção visual e a organização do conteúdo na prática. Se fizer sentido para vocês, textos, fotos e detalhes finais podem ser ajustados em conjunto antes da publicação definitiva.\n\n[URL_PROPOSTA]"
- **Estrutura para Portugal (`pt-PT`)**:
  - *Redesign (primeiro contato)*: "Olá, [nome]! Tudo bem? Acompanho o vosso trabalho em [cidade]... Notei que na página atual [motivo]. Por esse motivo, preparei uma primeira proposta de nova versão do site, já funcional e adaptada para telemóvel, para mostrar na prática a direção que imaginei. Posso enviar-lhe o link para dar uma vista de olhos? — [Autor]"
  - *Novo Site (primeiro contato)*: "Olá, [nome]! Tudo bem? Acompanho o vosso trabalho... Como reparei que ainda não dispõem de um site oficial próprio para centralizar contactos e marcações diretas, preparei uma primeira proposta funcional de como a página poderia ficar, já navegável e adaptada para telemóvel. Posso enviar-lhe o link para dar uma vista de olhos? — [Autor]"
  - *Mensagem após permissão*: "Com certeza. Preparei esta primeira versão principalmente para mostrar a direção visual e a organização do conteúdo na prática. Se fizer sentido para vocês, textos, fotografias e detalhes finais podem ser ajustados em conjunto antes da publicação definitiva.\n\n[URL_PROPOSTA]"
- **Restrições**: Sem emojis por padrão, sem formatação agressiva de marketing. **NUNCA enviar link no primeiro WhatsApp.** **NUNCA dizer "redesenhei seu site" para leads sem site.**

### B. E-mail / Gmail (Rapport, Prova e Respeito)
- **Tamanho**: ~120 a 180 palavras.
- **Assunto**: Pergunta pessoal ≤ 60 caracteres (ex.: `[Nome], uma proposta de site próprio para o vosso espaço` para PT, ou `[Nome], uma ideia de site próprio para o seu negócio` para BR).
- **Assinatura**: Tratamento adequado (`Um abraço` para BR; `Com os melhores cumprimentos` para PT).
- Depois do link, incluir naturalmente que a página é uma **primeira versão funcional para demonstração** e que, havendo interesse, a versão final será refinada em conjunto.

### HARD RULE — não transformar o primeiro contato em lista de features

O editor de conteúdo é um diferencial da oferta, mas **não deve ser despejado na primeira mensagem fria** junto com SEO, hospedagem, animações, performance etc.

No primeiro contato:
- vender a curiosidade e a prova visual já pronta;
- pedir permissão antes de enviar o link no WhatsApp;
- não listar funcionalidades do pacote;
- mencionar o editor apenas se for naturalmente necessário para responder a uma objeção/pergunta do lead.

Depois que o lead demonstrar interesse, o editor pode ser usado como argumento de fechamento, por exemplo:

- `pt-BR`: "Além disso, o site pode ser entregue com um editor próprio para vocês atualizarem textos, imagens, WhatsApp e links sem depender de mim para cada pequena alteração."
- `pt-PT`: "Além disso, o site pode ser entregue com um editor próprio para poderem atualizar textos, imagens, WhatsApp e ligações sem depender de mim para cada pequena alteração."

Não afirmar que o cliente "publica sozinho" ou que existe `/admin` autenticado se o backend Client CMS ainda não estiver efetivamente configurado para aquele projeto.

---

## 4. Página-Capa da Proposta (`proposta.html`)

Publicada em `[basePath]/[slug]/proposta.html` junto à página gerada:
1. **Status da proposta, visível cedo**: deixar inequívoco que se trata de uma **primeira versão funcional para demonstração**, que serve como ponto de partida e será refinada com o cliente antes da entrega final.
2. **Para Redesign**: Comparador antes/depois interativo (`Site atual` vs `Nova versão`) + seção **O que foi repensado** (2 a 4 melhorias reais).
3. **Para Novo Site**: Apresentação contextual da presença atual vs conceito (`Presença atual` vs `Conceito de site`) + seção **O que este conceito organiza** (centralização de informações, contato ágil, agendamento, mobile).
4. **Autonomia de conteúdo**: quando o editor visual estiver incluído na oferta, mostrar uma seção curta de valor explicando que textos, imagens, telefone, WhatsApp e redes/links podem ser mantidos por um editor simples, sem transformar a proposta em ficha técnica.
5. **Sobre quem preparou**: breve apresentação do autor e link para portfólio (`outreach.portfolioUrl`) apenas se configurado.

### Copy obrigatória de status da proposta

O template possui `__STATUS_PROPOSTA__`. Preencha sempre de acordo com o locale.

**pt-BR**

> **Primeira versão funcional**  
> Esta proposta serve como ponto de partida. Se a direção fizer sentido, a versão final é refinada em conjunto antes da publicação definitiva — textos, imagens, prioridades e demais ajustes.

**pt-PT**

> **Primeira versão funcional**  
> Esta proposta serve como ponto de partida. Se a direção fizer sentido, a versão final é refinada em conjunto antes da publicação definitiva — textos, imagens, prioridades e restantes ajustes.

Não esconder esse esclarecimento apenas no rodapé. Ele deve aparecer antes ou imediatamente junto da demonstração do site.

### Como apresentar o editor na proposta

Copy de referência, adaptar ao locale e ao estágio real da implementação:

**pt-BR**

> **Atualizações sem depender de suporte para tudo**  
> O site pode ser entregue com um editor de conteúdo simples para alterar textos, fotos, contatos, WhatsApp e links das redes sociais. Alterações estruturais e de design continuam protegidas.

**pt-PT**

> **Atualizações sem depender de suporte para tudo**  
> O site pode ser entregue com um editor de conteúdo simples para alterar textos, fotografias, contactos, WhatsApp e ligações das redes sociais. Alterações estruturais e de design continuam protegidas.

Evitar chamar de "construtor de sites". Posicionamento recomendado: **editor de conteúdo próprio** / **editor de conteúdo do site**.

### Verdade comercial sobre publicação

Existem dois níveis distintos e a proposta deve refletir exatamente o nível entregue:

1. **Editor visual/exportação** — cliente edita conteúdo e gera a versão atualizada; publicação continua controlada/manual.
2. **Client CMS autenticado** — cliente entra em `/admin`, salva rascunho/publica e o backend autorizado faz commit/deploy.

Só prometer o nível 2 quando autenticação, autorização por slug, backend de publicação e rollback estiverem realmente ativos.

O template da proposta possui `__SECAO_EDITOR_CLIENTE__`; preencher somente quando esse diferencial fizer parte da oferta.

---

## 5. Histórico e Follow-ups no CRM

1. Cada envio registra uma entrada na tabela `outreach_history` do SQLite com canal, destino mascarado, ID da mensagem e status.
2. Após `outreach.followUpAfterBusinessDays` (padrão: 3 dias úteis) sem resposta, o card no kanban/dashboard indica `followup_due`.
3. **Limite de 1 follow-up** gentil e contextual por lead.