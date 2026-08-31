---
name: hero-visual-rule
description: HARD RULE para todo site, conceito, redesign ou preview publico criado pelo Prospector. O hero deve conter uma imagem visualmente relevante ao negocio mesmo quando nao existe foto utilizavel do expert. Prioriza foto real verificada; quando isso nao existir, exige imagem contextual honesta e impede que stock/gerada seja apresentada como instalacao, pessoa ou resultado real do lead.
---

# Hero Visual Rule

Esta regra e obrigatoria para qualquer site publico ou preview comercial criado pelo Prospector, salvo excecao explicita do usuario para um site especifico.

## 1. Todo hero precisa de uma imagem relevante

Hero apenas tipografico, hero com card abstrato, mock dashboard, formas decorativas, gradientes ou icones nao satisfaz esta regra.

O hero deve conter uma imagem que ajude a comunicar imediatamente o negocio e o contexto do lead.

Use a seguinte ordem de preferencia:

1. foto real e verificavel do expert/profissional quando houver fonte utilizavel;
2. foto first-party verificavel do local, equipe, produto ou contexto real do negocio;
3. imagem fornecida pelo usuario;
4. imagem contextual stock ou gerada, apenas quando nao houver material factual utilizavel e sem simular que a cena pertence ao lead.

Exemplo para uma clinica odontologica sem foto utilizavel da profissional: use uma imagem contextual de consultorio/sala odontologica coerente com o servico, em vez de deixar o hero sem fotografia.

## 2. Imagem contextual nao pode virar fato inventado

Stock ou imagem gerada pode comunicar categoria, atmosfera e contexto, mas nao pode ser apresentada como prova da instalacao real, da equipe real, de resultado real ou de equipamento real do prospecto.

Quando a imagem nao retratar fato real do lead:

- nao use copy como `Nosso consultorio` sobre a imagem;
- nao use alt que sugira que aquela e a instalacao real;
- use alt factual, por exemplo `Imagem ilustrativa de consultorio odontologico`;
- registre no manifesto `representsActualBusiness: false`;
- use `data-image-context="illustrative"` no elemento de imagem para permitir QA deterministico.

Quando a imagem realmente retratar o lead, `representsActualBusiness: true` so e permitido com fonte first-party, material fornecido pelo usuario ou outra evidencia verificavel.

## 3. Hook obrigatorio

A imagem principal do hero deve ser um elemento `<img>` com:

```html
<img
  data-role="hero-image"
  src="..."
  alt="..."
  width="..."
  height="..."
>
```

`data-role="hero-image"` e um hook tecnico de QA. Nao e copy publica.

Se usar `<picture>`, aplique `data-role="hero-image"` no `<img>` interno.

Nao esconda a imagem principal apenas em `background-image` CSS. O hero pode ter background complementar, mas a imagem semantica principal deve continuar existindo como `<img>` para acessibilidade, performance e QA.

## 4. Performance e composicao

- hero image critica nao usa `loading="lazy"`;
- forneca `width` e `height` ou geometria equivalente para evitar CLS;
- use WebP/AVIF quando apropriado;
- desktop e mobile podem usar assets/crops diferentes quando isso melhorar composicao;
- preserve safe area para headline, supporting copy e CTA;
- nao cubra rosto, equipamento essencial ou foco visual com copy;
- se houver expert real, continuam valendo integralmente as regras de fidelidade do `website-core-rules`.

## 5. Manifesto de review

Todo novo site deve declarar:

```json
"heroVisual": {
  "required": true,
  "kind": "expert | facility | contextual | product | other",
  "sourceType": "first_party | user_provided | stock | generated",
  "representsActualBusiness": false,
  "illustrativeDisclosureRequired": true
}
```

`required: false` so e aceito quando o usuario pediu explicitamente hero sem imagem e a excecao estiver documentada no review.

## 6. Gate de QA

O autonomous review deve reprovar quando:

- nao existir `[data-role="hero-image"]`;
- a imagem nao estiver dentro do hero;
- `src` estiver ausente/vazio;
- `alt` estiver ausente/vazio;
- a imagem critica estiver com `loading="lazy"`;
- `sourceType` for `stock` ou `generated`, `representsActualBusiness` for falso e o elemento nao tiver `data-image-context="illustrative"`;
- `sourceType` for `stock` ou `generated` e o manifesto declarar `representsActualBusiness: true`;
- a imagem nao estiver visivel ou tiver dimensoes insignificantes em desktop/tablet/mobile.

A verificacao automatica de existencia e geometria nao substitui a revisao semantica. Na revisao adversarial e Screenshot Review, confirme visualmente que a imagem realmente corresponde ao negocio e nao cria contexto factual falso.
