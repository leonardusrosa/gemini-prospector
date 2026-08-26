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

A geração de mensagem recebe `country`, `locale`, `language` e `siteMode`, aplicando o registro nativo de cada mercado:

### A. WhatsApp (Curto, Conversacional e Direto)
- **Tamanho**: ~60 a 110 palavras.
- **Estrutura para Brasil (`pt-BR`)**:
  - *Redesign*: "Olá, [nome]! Tudo bem? Vi o trabalho excelente de vocês em [cidade]... Notei que no site atual [motivo]. Por conta disso, tomei a liberdade de preparar um conceito novo e mais moderno... Dá uma olhada quando puder (abre muito bem no celular)..."
  - *Novo Site*: "Olá, [nome]! Tudo bem? Vi o trabalho de vocês... Como notei que vocês ainda não possuem um site próprio oficial para facilitar o contato e agendamento de clientes, tomei a liberdade de preparar um conceito exclusivo para demonstração... Dá uma olhada quando puder (abre muito bem no celular)..."
- **Estrutura para Portugal (`pt-PT`)**:
  - *Redesign*: "Olá, [nome]! Tudo bem? Acompanho o vosso trabalho de referência em [cidade]... Notei que na página atual [motivo]. Por esse motivo, tomei a liberdade de preparar uma proposta nova e mais moderna para vocês... Veja quando tiver oportunidade (funciona perfeitamente no telemóvel)..."
  - *Novo Site*: "Olá, [nome]! Tudo bem? Acompanho o vosso trabalho de referência em [cidade]... Como reparei que ainda não dispõem de um site oficial próprio para centralizar contactos e marcações diretas, tomei a liberdade de preparar uma proposta de site exclusiva para demonstração... Veja quando tiver oportunidade (funciona perfeitamente no telemóvel)..."
- **Restrições**: Sem emojis por padrão, sem formatação agressiva de marketing. **NUNCA dizer "redesenhei seu site" para leads sem site.**

### B. E-mail / Gmail (Rapport, Prova e Respeito)
- **Tamanho**: ~120 a 180 palavras.
- **Assunto**: Pergunta pessoal ≤ 60 caracteres (ex.: `[Nome], uma proposta de site próprio para o vosso espaço` para PT, ou `[Nome], uma ideia de site próprio para o seu negócio` para BR).
- **Assinatura**: Tratamento adequado (`Um abraço` para BR; `Com os melhores cumprimentos` para PT).

### HARD RULE — não transformar o primeiro contato em lista de features

O editor de conteúdo é um diferencial da oferta, mas **não deve ser despejado na primeira mensagem fria** junto com SEO, hospedagem, animações, performance etc.

No primeiro contato:
- vender a curiosidade e a prova visual já pronta;
- usar um único link principal para a proposta;
- não listar funcionalidades do pacote;
- mencionar o editor apenas se for naturalmente necessário para responder a uma objeção/pergunta do lead.

Depois que o lead demonstrar interesse, o editor pode ser usado como argumento de fechamento, por exemplo:

- `pt-BR`: "Além disso, o site pode ser entregue com um editor próprio para vocês atualizarem textos, imagens, WhatsApp e links sem depender de mim para cada pequena alteração."
- `pt-PT`: "Além disso, o site pode ser entregue com um editor próprio para poderem atualizar textos, imagens, WhatsApp e ligações sem depender de mim para cada pequena alteração."

Não afirmar que o cliente "publica sozinho" ou que existe `/admin` autenticado se o backend Client CMS ainda não estiver efetivamente configurado para aquele projeto.

---

## 4. Página-Capa da Proposta (`proposta.html`)

Publicada em `[basePath]/[slug]/proposta.html` junto à página gerada:
1. **Para Redesign**: Comparador antes/depois interativo (`Site atual` vs `Nova versão`) + seção **O que foi repensado** (2 a 4 melhorias reais).
2. **Para Novo Site**: Apresentação contextual da presença atual vs conceito (`Presença atual` vs `Conceito de site`) + seção **O que este conceito organiza** (centralização de informações, contato ágil, agendamento, mobile).
3. **Autonomia de conteúdo**: quando o editor visual estiver incluído na oferta, mostrar uma seção curta de valor explicando que textos, imagens, telefone, WhatsApp e redes/links podem ser mantidos por um editor simples, sem transformar a proposta em ficha técnica.
4. **Sobre quem preparou**: breve apresentação do autor e link para portfólio (`outreach.portfolioUrl`) apenas se configurado.

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
