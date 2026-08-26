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

---

## 4. Página-Capa da Proposta (`proposta.html`)

Publicada em `[basePath]/[slug]/proposta.html` junto à página gerada:
1. **Para Redesign**: Comparador antes/depois interativo (`Site atual` vs `Nova versão`) + seção **O que foi repensado** (2 a 4 melhorias reais).
2. **Para Novo Site**: Apresentação contextual da presença atual vs conceito (`Presença atual` vs `Conceito de site`) + seção **O que este conceito organiza** (centralização de informações, contato ágil, agendamento, mobile).
3. **Sobre quem preparou**: breve apresentação do autor e link para portfólio (`outreach.portfolioUrl`) apenas se configurado.

---

## 5. Histórico e Follow-ups no CRM

1. Cada envio registra uma entrada na tabela `outreach_history` do SQLite com canal, destino mascarado, ID da mensagem e status.
2. Após `outreach.followUpAfterBusinessDays` (padrão: 3 dias úteis) sem resposta, o card no kanban/dashboard indica `followup_due`.
3. **Limite de 1 follow-up** gentil e contextual por lead.
