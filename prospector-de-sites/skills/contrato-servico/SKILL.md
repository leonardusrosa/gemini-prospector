---
name: contrato-servico
description: Esta skill deve ser usada ao gerar contratos de prestação de serviço para clientes fechados — criação/redesign de site, publicação e manutenção. Acione quando o usuário disser "contrato", "gerar contrato", "formalizar", "cliente fechou", "enviar contrato" ou pedir o contrato (skill contrato-servico).
---

# Contrato de prestação de serviço

Gerar a minuta do contrato do serviço fechado (redesign + publicação de página, com manutenção opcional), pronta para virar PDF/DOCX e ser enviada de forma privada ao cliente.

## Fonte dos dados (nesta ordem)

1. **Banco (`prospector.db`)**: nome do cliente, cidade, valor fechado, URL publicada.
2. **Config (`prospector-config.json`)**: dados do PRESTADOR — nome, CPF/CNPJ, endereço, cidade/UF (campo `contratante`; se não existir, colete do usuário UMA vez e salve).
3. **Usuário** (ele pergunta ao cliente): CPF/CNPJ e endereço do CONTRATANTE, forma de pagamento, prazo, manutenção mensal (sim/não + valor e escopo).

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
6. **assistente inteligente do site**, opcional (`assistantIncluded: true/false`), com configuração técnica incluída, mas consumo de API terceiro por conta do cliente (~US$ 2–4/1.000 respostas curtas como estimativa de referência, sem promessa de mensagens ilimitadas ou preço fixo);
7. **manutenção mensal**, somente se tiver sido contratada explicitamente como serviço adicional e com escopo descrito.

Nunca usar `manutenção` como sinônimo automático de `hospedagem`.

### Assistente inteligente (quando `assistantIncluded=true`)

Campos estruturados opcionais: `assistantIncluded`, `assistantSetupValue`, `assistantApiResponsibility`, `assistantEstimatedUsageCost`, `assistantProviderPolicy`.

Quando contratado:
- Respostas a partir de informações reais e verificadas da página; caráter automatizado, sem substituir avaliação profissional.
- Consumo de API faturado à parte pelo provedor de IA; conta e custos sob responsabilidade do cliente (AutoCORA auxilia na configuração técnica).
- Estimativa de referência atual: aproximadamente US$ 2–4 por 1.000 respostas curtas (valor referencial, não vinculante e variável).
- Limite/esgotamento de saldo de API do cliente não é equivalente a queda ou indisponibilidade do site.
- Provedor e modelo podem ser substituídos tecnicamente mantendo funcionalidade e segurança factual.
- **PROIBIDO**: prometer mensagens ilimitadas, preço fixo de API, gratuidade permanente ou volume garantido.
- Se `assistantIncluded=false` (ou omitido), a cláusula do assistente não deve constar no contrato.

## Privacidade e forma de entrega — HARD RULE

Contrato contém dados pessoais, endereço, CPF/CNPJ e condições financeiras. Portanto:

- **NUNCA publicar contrato no repositório público de previews** (`prospector-sites`) ou em rota previsível como `/clientes/[slug]/contrato.html`, `/contrato`, `/contrato.pdf` ou equivalente.
- `noindex` não transforma uma URL pública em armazenamento privado. Não usar somente `robots` como proteção.
- Gerar contrato em área local/privada de trabalho e entregar como **PDF/DOCX anexado diretamente** ao cliente.
- Se no futuro existir portal web para contrato, ele deve ter autenticação/autorização ou link tokenizado de alta entropia, expiração adequada e controles coerentes de acesso. Não improvisar isso em hosting estático público.
- Dados fictícios de dry-run devem estar claramente identificados como sintéticos e nunca ser persistidos como dados reais do lead.

## Geração

- Template: `references/contrato-template.html` — arquivo único com CSS A4 de impressão. Substituir todos os `{{PLACEHOLDERS}}`; conferir que nenhum sobrou (busca por `{{`).
- Salvar o HTML contratual apenas em diretório local/privado, por exemplo `private/contracts/[slug]/contrato-[slug].html`, e mantê-lo fora do repositório público de deploy.
- PDF: gerar localmente a partir do HTML e manter na mesma área privada antes do envio ao cliente.
- Cláusulas parametrizáveis: manutenção mensal somente se contratada explicitamente; parcelamento e escopo devem refletir o acordo real.
- `TEXTO_OBJETO` deve funcionar tanto para redesign quanto para novo site. Não referenciar site anterior quando ele não existir.
- `TEXTO_HOSPEDAGEM` deve representar exatamente uma das condições acordadas: hospedagem AutoCORA sem cobrança separada ou hospedagem própria do cliente validada como compatível.
- Antes de finalizar, revisar o contrato e garantir que domínio, hospedagem, editor e alterações futuras estejam coerentes com os termos comerciais acima.

## DOCX protegido (arquivo para o cliente)

Script: `references/gerar-docx.py` (requer `python-docx`). Recebe `dados.json` com os campos contratuais, além de `MANUTENCAO: true/false`. Se `MANUTENCAO=true`, exigir também `VALOR_MANUTENCAO` e `TEXTO_MANUTENCAO`; nunca presumir o escopo recorrente.

O DOCX usa proteção `readOnly` + regiões editáveis (`permStart/permEnd`, grupo everyone) nos pontos do cliente: CPF/CNPJ e endereço quando vierem como "(preencher)", data e assinatura. A proteção do Word é dissuasória, não substitui assinatura eletrônica nem controle forte de acesso.

## Envio do contrato

Depois do fechamento comercial e revisão humana:

1. validar que os dados legais do prestador (nome, CPF/CNPJ, endereço, cidade/UF) estão preenchidos sem placeholders (bloqueio fail-closed para contratos reais; placeholders sintéticos permitidos apenas em dry-run);
2. gerar PDF e/ou DOCX privado;
3. revisar nomes, documento, endereço, valor, forma de pagamento, prazo, hospedagem, domínio, editor e eventuais serviços adicionais;
4. mostrar ao usuário o arquivo e a mensagem que serão enviados;
5. aguardar aprovação explícita;
6. enviar diretamente ao cliente como anexo pelo canal acordado, preferencialmente e-mail para documentos formais;
7. registrar no CRM apenas após o envio efetivo, sem tornar o documento público.

Assunto sugerido para e-mail: `Contrato de prestação de serviço - [Nome do negócio]`.

Corpo: agradecer a confiança, resumir brevemente escopo + valor + prazo, pedir revisão do documento anexo e orientar assinatura/aceite conforme a ferramenta escolhida. Fechar com a assinatura real do config.
- Para **pt-BR**: fechar com `Atenciosamente,` ou `Um abraço,` (proibido usar `Com os melhores cumprimentos`).
- Para **pt-PT**: fechar com `Com os melhores cumprimentos,`.

## Limites

- SEMPRE manter o aviso de que a minuta base recomenda revisão por profissional jurídico.
- Não prometer validade jurídica nem substituir assinatura formal.
- Nunca inventar cláusula financeira: tudo vem do banco/usuário.
- Nunca inventar prazo de hospedagem gratuita, SLA, suporte ilimitado ou condição de domínio que o usuário não tenha confirmado.
- Nunca inventar dados legais do prestador (nome, documento, endereço); falhar fechado se ausentes.
- Não prometer "/admin", "CMS completo" ou "publicação 100% autônoma" se o Client CMS autenticado não estiver configurado para o projeto.
- Nunca enviar contrato sem revisão e aprovação explícita do usuário.
