---
name: hero-visual-rule
description: HARD RULE para todo site, conceito, redesign ou preview público criado pelo Prospector. O hero deve conter uma imagem visualmente relevante ao negócio mesmo quando não existe foto utilizável do expert. Prioriza foto real verificada; quando não existir, busca no catálogo canônico de templates hero-expert (templates/hero-expert/manifest.json); quando não houver template de nicho, exige imagem contextual ilustrativa honesta. Proíbe heros sem imagem, heros apenas tipográficos, ou apresentar stock/template como instalação/pessoa real.
---

# Hero Visual Rule

Esta regra é obrigatória para qualquer site público, conceito inicial ou preview comercial criado pelo Prospector, salvo exceção explícita do usuário para um site específico.

## 1. Todo hero de primeira versão precisa de uma imagem relevante

Hero apenas tipográfico, hero com card abstrato, mock dashboard, formas decorativas, gradientes ou ícones **NÃO** satisfaz esta regra.

O hero deve conter uma imagem que ajude a comunicar imediatamente o negócio e o contexto do lead.

Use a seguinte ordem estrita de preferência:

1. **Foto real e verificável do expert/profissional** quando houver fonte factual utilizável (ex: site original, CRO/CRM/OAB com foto oficial verificada, perfil de autoridade confirmado);
2. **Foto first-party verificável do local, equipe, produto ou contexto real do negócio** (ex: fotos de fachada/consultório validadas via Google Maps / Place Details);
3. **Imagem fornecida pelo usuário/cliente**;
4. **Template canônico do catálogo `hero-expert`** (`prospector-de-sites/templates/hero-expert/manifest.json`), quando o negócio for liderado por especialista e não houver foto real verificada;
5. **Imagem contextual ilustrativa de nicho**, criada especificamente quando não houver material factual nem template de nicho no catálogo.

Um hero **NUNCA** pode se tornar apenas tipográfico ou abstrato meramente porque um template ou foto real não está disponível.

## 2. Catálogo Canônico de Templates Hero-Expert

O Prospector mantém um catálogo canônico de templates em `prospector-de-sites/templates/hero-expert/manifest.json`.

### Seleção Automática de Template:
Durante a fase de planejamento visual (`design-read.md`):
- Se não houver foto real verificada do especialista, inspecione `templates/hero-expert/manifest.json` pelo nicho correspondente (ex: `dentistry`).
- Se houver variante compatível com o gênero confirmado nos dados factuais do lead (ex: `female` para Dra., `male` para Dr.), selecione o `templateId` (ex: `dentistry-female`).
- Se o gênero for ambíguo ou não puder ser determinado com segurança absoluta a partir dos dados do lead, **NÃO** adivinhe por nome; use composição contextual neutra ou solicite decisão.

### Registro no `design-read.md`:
```text
HERO_VISUAL_SOURCE: canonical-template
HERO_TEMPLATE_ID: dentistry-female
HERO_TEMPLATE_DESKTOP: templates/hero-expert/dentistry/female/desktop-ultrawide.webp
HERO_TEMPLATE_MOBILE: templates/hero-expert/dentistry/female/mobile.webp
HERO_REPRESENTS_ACTUAL_EXPERT: false
HERO_REPRESENTS_ACTUAL_BUSINESS: false
```

## 3. Imagem de Template ou Contextual NÃO Pode Virar Fato Inventado

Templates com silhueta e badge "SUA FOTO AQUI" ou imagens contextuais geradas servem para demonstrar layout e atmosfera, mas **NUNCA** podem ser apresentadas como prova da instalação real ou do profissional real.

Quando usar template ou imagem contextual:
- **NUNCA** use copy como "Foto da Dra. X" ou "Nosso consultório" sobre a imagem;
- **NUNCA** use `alt` que sugira que aquela é a pessoa ou instalação real;
- **SEMPRE** use `alt` factual e neutro, por exemplo:
  `"Imagem ilustrativa de consultório odontológico com espaço reservado para foto profissional"`
- **SEMPRE** inclua `data-image-context="illustrative"` no elemento `<img>` ou container;
- **SEMPRE** registre no manifesto:
  `representsActualExpert: false`
  `representsActualBusiness: false`
  `containsPhotoPlaceholder: true` (se for template com "SUA FOTO AQUI")

## 4. Fluxo de Substituição por Foto Real do Expert

O template com "SUA FOTO AQUI" é um **placeholder de prospecção**.

Assim que uma foto real e verificada do profissional for obtida:
1. Substitua o template pela foto real do profissional;
2. Preserve a identidade, feições e vestimenta profissional reais;
3. Crie composição desktop ultrawide (~2000px de largura) com área limpa para o texto;
4. Crie composição mobile (~900px de largura) com enquadramento vertical e fade suave para legibilidade;
5. Remova completamente o badge "SUA FOTO AQUI" e a silhueta placeholder;
6. Atualize o `review-manifest.json`:
   - `representsActualExpert: true`
   - `sourceType: "first_party"` (ou `"user_provided"`)
   - `containsPhotoPlaceholder: false`

**NUNCA** deixe o placeholder em produção final após o cliente ter fornecido/aprovado sua foto real.

## 5. Hook Obrigatório e Estrutura Técnica

A imagem principal do hero deve ser um elemento `<img>` (ou `<picture>` com `<img>` interno) contendo:

```html
<picture>
  <source media="(max-width: 640px)" srcset="caminho/para/mobile.webp">
  <img
    data-role="hero-image"
    data-image-context="illustrative"
    src="caminho/para/desktop-ultrawide.webp"
    alt="Imagem ilustrativa de consultório odontológico com espaço reservado para foto profissional"
    width="1983"
    height="793"
  >
</picture>
```

- `data-role="hero-image"`: Hook técnico de QA (não é texto visível).
- Hero image crítica **NÃO** usa `loading="lazy"`.
- Forneça `width` e `height` para prevenir Cumulative Layout Shift (CLS).
- Safe area: Preserve espaço para headline, supporting copy e o único CTA do hero (`#hero-cta`).

## 6. Manifesto de Review (`review-manifest.json`)

Todo site deve declarar a seção `heroVisual`:

```json
{
  "heroVisual": {
    "required": true,
    "kind": "expert-placeholder",
    "templateId": "dentistry-female",
    "sourceType": "generated-template",
    "representsActualExpert": false,
    "representsActualBusiness": false,
    "illustrativeDisclosureRequired": true,
    "desktopAssetRequired": true,
    "mobileAssetRequired": true
  }
}
```

Valores permitidos para `kind`:
- `expert` (foto real do profissional)
- `expert-placeholder` (template com "SUA FOTO AQUI")
- `facility` (foto real do local)
- `contextual` (imagem ilustrativa de nicho/ambiente)
- `product` (produto real)
- `other`

## 7. Gate de QA e Bloqueios

O autonomous review estático e browser deve **REPROVAR / BLOQUEAR** quando:
1. Não existir `[data-role="hero-image"]` dentro do hero;
2. `src` estiver ausente ou apontar para arquivo inexistente;
3. `kind == "expert-placeholder"` e o `templateId` não existir no catálogo canônico `templates/hero-expert/manifest.json`;
4. `kind == "expert-placeholder"` e o arquivo desktop ou mobile declarado estiver ausente;
5. `sourceType` for `generated-template`, `stock` ou `generated` e o manifesto declarar `representsActualExpert: true` ou `representsActualBusiness: true`;
6. Template ou imagem ilustrativa não contiver `data-image-context="illustrative"`;
7. Imagem crítica do hero estiver com `loading="lazy"`;
8. Imagem do hero estiver invisível ou com geometria insignificante (<100px) em Desktop 1440x900 ou Mobile 390x844;
9. O nicho possuir template no catálogo mas o site foi gerado como hero text-only sem imagem.
