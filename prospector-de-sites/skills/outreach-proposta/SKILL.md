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

## 3. Diretrizes de Mensagem por Canal

### A. WhatsApp (Curto, Conversacional e Direto)
- **Tamanho**: ~60 a 110 palavras.
- **Estrutura para Redesign (`siteMode = 'redesign'`)**:
  1. Saudação natural pelo nome real do profissional/empresa.
  2. Observação específica e respeitosa sobre o site existente (ex.: leitura no celular).
  3. Informar que preparou e publicou um conceito novo demonstrativo.
  4. **1 único link**: a página da proposta (`https://[domain]/[basePath]/[slug]/proposta.html`).
  5. CTA leve: dar uma olhada e dizer o que achou.
- **Estrutura para Novo Site (`siteMode = 'new_site_concept'`)**:
  1. Saudação natural pelo nome real.
  2. Elogio factual ao destaque no Google Maps (nota/avaliações reais).
  3. Observação de que não encontrou site oficial do negócio para agendamento direto.
  4. Informar que preparou um conceito exclusivo de site próprio no ar para demonstração.
  5. **1 único link**: a página da proposta.
- **Restrições**: Sem emojis por padrão, sem formatação agressiva de marketing, sem anexos. **NUNCA dizer "redesenhei seu site" para leads sem site.**

### B. E-mail / Gmail (Rapport, Prova e Respeito)
- **Tamanho**: ~120 a 180 palavras.
- **Assunto**: Pergunta pessoal ≤ 60 caracteres sem cara de marketing (ex.: `[Nome], uma ideia de site próprio para a [Clínica]` para novo site, ou `[Nome], posso te mostrar uma ideia para o site?` para redesign).
- **Estrutura**:
  1. Rapport inicial com elogio específico (nota/avaliações reais do Google).
  2. Contextualização honesta (análise do site atual para Redesign OU ausência de site próprio para Novo Site).
  3. Trabalho já executado + 1 link HTML limpo da proposta.
  4. CTA leve e assinatura completa (nome, apresentação, WhatsApp).
- **Envio**: Criação de rascunho no Gmail via link compose ou conector para revisão humana.

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
