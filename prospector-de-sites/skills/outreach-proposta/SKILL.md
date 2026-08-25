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
- **Estrutura**:
  1. Saudação natural pelo nome real do profissional/empresa.
  2. Observação específica e respeitosa sobre o site existente (ex.: leitura no celular).
  3. Informar que preparou e publicou um conceito novo demonstrativo.
  4. **1 único link**: a página da proposta (`https://[domain]/[basePath]/[slug]/proposta.html`).
  5. CTA leve: dar uma olhada e dizer o que achou.
- **Restrições**: Sem emojis por padrão, sem formatação agressiva de marketing, sem anexos.

### B. E-mail / Gmail (Rapport, Prova e Respeito)
- **Tamanho**: ~120 a 180 palavras.
- **Assunto**: Pergunta pessoal ≤ 60 caracteres sem cara de marketing (ex.: `Dr. [Nome], posso te mostrar uma ideia para o site da [Clínica]?`).
- **Estrutura**:
  1. Rapport inicial com elogio específico (nota/avaliações reais do Google).
  2. Observação técnica objetiva do site atual.
  3. Trabalho já executado + 1 link HTML limpo da proposta.
  4. CTA leve e assinatura completa (nome, apresentação, WhatsApp).
- **Envio**: Criação de rascunho no Gmail via link compose ou conector para revisão humana.

---

## 4. Página-Capa da Proposta (`proposta.html`)

Publicada em `[basePath]/[slug]/proposta.html` junto ao redesign:
1. Comparador antes/depois interativo.
2. **O que foi repensado**: 2 a 4 melhorias reais e factuais (ex.: hierarquia mobile, agendamento rápido, clareza dos serviços).
3. **Sobre quem preparou**: breve apresentação do autor e link para portfólio (`outreach.portfolioUrl`) apenas se configurado.

---

## 5. Histórico e Follow-ups no CRM

1. Cada envio registra uma entrada na tabela `outreach_history` do SQLite com canal, destino mascarado, ID da mensagem e status.
2. Após `outreach.followUpAfterBusinessDays` (padrão: 3 dias úteis) sem resposta, o card no kanban/dashboard indica `followup_due`.
3. **Limite de 1 follow-up** gentil e contextual por lead.
