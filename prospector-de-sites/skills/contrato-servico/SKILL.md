---
name: contrato-servico
description: Esta skill deve ser usada ao gerar contratos de prestação de serviço para clientes fechados — criação/redesign de site, publicação e manutenção. Acione quando o usuário disser "contrato", "gerar contrato", "formalizar", "cliente fechou", "enviar contrato" ou pedir o contrato (skill contrato-servico).
---

# Contrato de prestação de serviço

Gerar a minuta do contrato do serviço fechado (redesign + publicação de página, com manutenção opcional), pronta pra virar PDF e ir por e-mail.

## Fonte dos dados (nesta ordem)

1. **Banco (`prospector.db`)**: nome do cliente, cidade, valor fechado, URL publicada.
2. **Config (`prospector-config.json`)**: dados do PRESTADOR — nome, CPF/CNPJ, endereço, cidade/UF (campo `contratante`; se não existir, colete do usuário UMA vez e salve).
3. **Usuário** (ele pergunta ao cliente): CPF/CNPJ e endereço do CONTRATANTE, forma de pagamento, prazo, manutenção mensal (sim/não + valor).

## Termos comerciais padrão atuais

Trate os pontos abaixo como padrão comercial atual, salvo exceção explicitamente acordada pelo usuário com aquele cliente:

- **Domínio**: registro, propriedade e renovação do domínio ficam por conta do cliente. Preferir que o domínio esteja em conta/controlado pelo próprio cliente. Não apresentar domínio como item gratuito incluído.
- **Hospedagem fornecida pela AutoCORA**: pode ser oferecida sem cobrança separada de hospedagem ao cliente. Não converter isso automaticamente em mensalidade de manutenção.
- **Hospedagem própria do cliente**: se o cliente preferir manter a infraestrutura atual, ele pode fazê-lo por sua conta, desde que o ambiente seja tecnicamente compatível com a entrega. Compatibilidade/migração deve ser validada antes de prometer implantação.
- **Painel/editor de conteúdo**: faz parte da proposta comercial. Alterações simples que o painel suportar, como textos, imagens, contatos, WhatsApp e links, podem ser feitas pelo cliente sem cobrança por edição.
- **Alterações complexas**: mudanças estruturais, novas páginas/seções relevantes, novas integrações, novas funcionalidades, fluxos especiais, redesign estrutural ou outras alterações fora do escopo original podem ser cobradas separadamente, sempre com orçamento/aprovação antes da execução.
- **Sem suporte ilimitado implícito**: hospedagem sem cobrança separada e editor incluído não significam automaticamente suporte ilimitado, SLA, redesign contínuo ou desenvolvimento ilimitado.
- **Condições de infraestrutura**: não escrever "hospedagem grátis para sempre" nem inventar SLA, política de backup, disponibilidade, prazo de continuidade ou garantia operacional que não tenham sido formalizados.
- **Landing page da AutoCORA**: `https://autocora.com.br/pt/landing-pages` é referência de identidade/portfólio neste momento. Preços, FAQ, pacotes, métricas e outras condições publicados ali podem estar desatualizados e não devem ser copiados para contrato sem confirmação do usuário.

### O contrato deve distinguir claramente

1. **custo do projeto/desenvolvimento**;
2. **domínio**, pago/renovado pelo cliente;
3. **hospedagem**, quando fornecida pela AutoCORA sem cobrança separada ou quando mantida pelo cliente por conta própria;
4. **edição simples pelo painel**, incluída no escopo entregue;
5. **alterações estruturais/complexas futuras**, sujeitas a orçamento separado;
6. **manutenção mensal**, somente se tiver sido contratada explicitamente como serviço adicional.

Nunca usar `manutenção` como sinônimo automático de `hospedagem`.

## Geração

- Template: `references/contrato-template.html` — arquivo único com CSS A4 de impressão. Substituir todos os `{{PLACEHOLDERS}}`; conferir que nenhum sobrou (busca por `{{`).
- Salvar em `sites/[slug]/contrato-[slug].html`. PDF: abrir no navegador → Ctrl+P → Salvar como PDF (informe isso ao usuário).
- Cláusulas parametrizáveis: manutenção mensal (incluir só se contratada) e parcelamento (texto muda conforme forma de pagamento).
- Antes de finalizar, revisar o template gerado e garantir que domínio, hospedagem, editor e alterações futuras estejam coerentes com os termos comerciais acima. Se o template antigo conflitar, adaptar a redação do contrato para o acordo real; não preservar cláusula desatualizada apenas porque existe no template.

## DOCX travado (o arquivo que vai pro cliente)

Script pronto: `references/gerar-docx.py` (requer `python-docx`). Recebe `dados.json` (mesmas chaves do template HTML + `MANUTENCAO: true/false` e `VALOR_MANUTENCAO`) e gera o .docx com proteção `readOnly` + regiões editáveis (`permStart/permEnd`, grupo everyone) nos pontos do cliente: CPF/CNPJ e endereço quando vierem como "(preencher)", data e assinatura — destacados em amarelo. Limitação honesta (avise o usuário 1 vez): a proteção do Word é dissuasória, guia o preenchimento mas não impede quem quiser desativá-la; para validade forte, assinatura eletrônica (gov.br, Autentique).

## E-mail de envio (rascunho no Gmail)

Assunto: `Contrato de prestação de serviço — nova página [Nome do negócio]`. Corpo (adaptar à voz do usuário): agradecer a confiança, resumir em 2 linhas o combinado (escopo + valor + prazo), pedir que leia a minuta anexa e responda com um "de acordo" (ou assine digitalmente, se o usuário usar alguma ferramenta), e fechar com a assinatura do config. Instruir o usuário a ANEXAR o PDF exportado antes de enviar.

## Limites

- SEMPRE manter o aviso do rodapé: minuta base, recomenda-se revisão por advogado.
- Não prometer validade jurídica nem substituir assinatura formal; se o usuário pedir assinatura eletrônica, sugerir que suba o PDF na ferramenta dele (gov.br, Autentique etc.).
- Nunca inventar cláusula financeira: tudo vem do banco/usuário.
- Nunca inventar prazo de hospedagem gratuita, SLA, suporte ilimitado ou condição de domínio que o usuário não tenha confirmado.
