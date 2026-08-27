---
name: website-core-rules
description: HARD RULES obrigatórias para qualquer site, landing page, conceito, redesign ou preview público criado pelo Prospector. Use SEMPRE junto com redesign-premium e qualquer skill que gere UI pública de cliente. Prioriza verdade factual, design específico sem AI-slop, copy natural, CTA disciplinado, imagens semanticamente corretas, fidelidade em fotos de experts, prova social verificável, acessibilidade, performance e SEO adequados ao ambiente.
---

# Website Core Rules

Estas regras são globais e permanentes. Têm precedência sobre `gpt-taste`, `design-taste-frontend`, templates, referências visuais e atalhos de geração.

Aplicam-se a qualquer UI pública criada para cliente ou prospecto. Não se aplicam ao dashboard interno, nomes de arquivo, slugs ou documentação técnica, exceto quando uma regra tratar explicitamente do build/deploy.

## 1. Verdade factual e rastreabilidade vencem o design

Nunca invente, complete ou embeleze como fato informação não sustentada por fonte verificável do lead ou material fornecido pelo usuário.

Inclui:

- citações e depoimentos
- nomes, cargos, credenciais e títulos
- números, percentuais, avaliações e métricas
- certificações, selos, rankings e avaliações
- serviços, especialidades e tecnologias
- endereços, horários e canais de contato
- resultados, promessas, diferenciais e claims
- autoria de frases
- contexto de imagens

Se houver dúvida, não presuma. Remova, reescreva de forma factual ou marque internamente para verificação.

### Quotes, depoimentos e falas

Nunca coloque entre aspas uma frase criada, inferida, embelezada ou parafraseada como se tivesse sido dita por pessoa real.

Uma quote só pode aparecer quando o texto estiver verbatim em fonte verificável do lead ou material fornecido pelo usuário.

- preserve a redação e o sentido dentro das aspas
- preserve atribuição somente se ela existir na fonte
- não invente autor
- mantenha URL/página/arquivo de origem rastreável internamente
- se editar ou condensar, remova as aspas e transforme em prosa factual
- nunca estilize parágrafo comum como quote apenas para preencher espaço

## 2. Cada componente precisa ganhar o direito de existir

Nenhum elemento visual deve existir só para preencher, “dar cara de design” ou imitar template premium.

Teste:

> Se eu remover isto, alguma informação, hierarquia, significado, prova, navegação ou experiência relevante é perdida?

Se não, remova.

Resolva primeiro espaço, grid, alinhamento, contraste, escala, ritmo, hierarquia, tipografia e fotografia. Não conserte composição fraca com ornamentos.

## 3. Anti-AI-slop

### Nunca usar como padrão

- tags, pills, chips, badges ou bubbles decorativos
- traços automáticos antes/depois de eyebrows
- numeração `01 / 02 / 03` sem ordem real
- estrelas sem avaliação real
- selos sem certificação real
- gráficos sem dados
- porcentagens sem fonte
- ícones, círculos ou setas sem semântica
- aspas gigantes sem citação real
- linhas/divisores só porque “faltou design”
- glassmorphism, glow ou gradientes decorativos como fórmula
- bento grid sem necessidade do conteúdo
- sombras em todos os componentes
- cards para todo tipo de informação

“Premium” deve vir de composição, tipografia, fotografia, proporção, detalhe e especificidade.

### Estrutura

Evite repetir seção após seção:

`eyebrow + título + parágrafo + 3 cards`

A estrutura deve nascer do conteúdo. Varie quando isso melhorar leitura: editorial, imagem + texto, galeria, timeline, processo, FAQ, prova, comparativo, case, lista tipográfica ou contato.

A página deve parecer específica daquele lead, com fatos, linguagem, imagens e repertório reais.

## 4. Copy pública

### Sem emoji

Não use emoji em UI pública. Use SVG, ícone vetorial real ou CSS quando houver função semântica.

### Sem travessões

Não use `—` ou `–` em copy pública. Reescreva naturalmente com pontuação comum.

Hífens ortográficos, URLs, classes, slugs, CSS, JS e nomes de arquivo são exceções técnicas.

### PT-BR em sentence case natural

Em PT-BR, títulos, subtítulos, labels, navegação, botões e headings usam sentence case.

Correto:

- `Conheça nossos tratamentos`
- `Agendar avaliação`
- `Falar com a equipe`

Evitar:

- `Conheça Nossos Tratamentos`
- `Agendar Avaliação`

Preserve nomes próprios, marcas, siglas e produtos. Evite frases, headings e CTAs inteiros em ALL CAPS. Microtexto curto pode receber uppercase por CSS somente com justificativa visual clara.

## 5. CTA

### Hero: exatamente um botão

Todo hero deve conter exatamente um botão CTA no desktop e no mobile.

Não use CTA primário + secundário, dois botões lado a lado, botão outline concorrente ou dois canais de contato como botões do hero.

### Evitar wording repetitivo

Não espalhe o mesmo texto de botão por várias seções.

Mesmo quando vários CTAs levam ao WhatsApp, varie de forma contextual e honesta:

- hero: `Agendar avaliação`
- ortodontia: `Conversar sobre ortodontia`
- bio: `Falar com a equipe`
- dúvidas: `Tirar uma dúvida`
- contato final: `Chamar no WhatsApp`

Não use sinônimos aleatórios e nunca prometa ação diferente do destino real.

## 6. Imagens precisam provar o que a interface diz

Toda imagem de conteúdo deve ser semanticamente compatível com card, título, alt e contexto.

- `Consultório clínico` mostra consultório/sala de atendimento real
- `Central de esterilização` mostra esterilização real
- `Fachada` mostra fachada real

Nunca escolha apenas pelo filename. Faça inspeção visual.

Prioridade:

1. first-party do lead
2. fornecida pelo usuário
3. gerada/stock apenas quando o projeto permitir e sem simular fato real sobre instalações, pessoas ou resultados

O `alt` deve descrever honestamente o que a imagem mostra.

## 7. Hero com foto real de expert

Quando houver foto real utilizável do profissional, ela é a fonte de identidade. Preserve rosto, expressão, identidade, pose, roupa, cabelo, textura de pele e proporções.

Proibido:

- beauty filter
- smoothing artificial
- rejuvenescimento
- troca de roupa não solicitada
- mudança de expressão/pose sem necessidade aprovada
- reconstrução facial que altere identidade
- extensão de fundo que invente diplomas, logos, equipamentos, instalações ou arquitetura como se fossem reais

Se não existir uma foto-fonte utilizável, não invente uma suposta foto real do expert.

### Desktop: asset ultrawide dedicado é regra

Para hero desktop full-width com expert, gere/use **um asset ultrawide dedicado**, não apenas uma imagem 16:9 reaproveitada.

Direção padrão:

- proporção alvo aproximadamente 2:1 a 2.4:1 ou mais larga conforme o layout, equivalente a uma composição 21:9-ish quando útil
- expert no lado oposto ao bloco principal de texto, normalmente à direita
- espaço negativo real e suficiente para headline, supporting copy e CTA
- expert preservado inteiro na região visual importante, sem corte arbitrário por responsividade
- composição deve continuar funcional em telas desktop largas e ultrawide

16:9 só é aceitável quando o hero não é realmente full-width/ultrawide ou quando há limitação factual/técnica da imagem-fonte. Não trate 16:9 como default para hero desktop com expert.

### Overlay de contraste

Overlay/gradiente é permitido quando tiver função de legibilidade.

- área do texto pode ser sólida/mais opaca
- transição começa perto do centro conforme a composição
- overlay deve desaparecer antes de chegar ao expert
- nunca lavar rosto, pele, cabelo ou roupa
- sem névoa, haze, wash ou aspecto artificial

Este gradiente funcional não viola a regra anti-gradiente decorativo.

### Contraste do texto de apoio no hero

Supporting copy, subheading, trust facts, bullets e seus ícones são conteúdo essencial da primeira dobra. Eles podem ter hierarquia menor que o headline, mas **não podem parecer desabilitados, lavados ou excessivamente opacos contra o fundo**.

- prefira cor sólida com contraste suficiente em vez de reduzir `opacity` do texto
- não use cinza claro/translúcido sobre fundo cinza, bege ou gradiente de luminância semelhante
- mire WCAG AA no texto efetivamente renderizado: normalmente pelo menos 4.5:1 para texto comum e 3:1 para texto grande
- valide o contraste no pior ponto real do background e não apenas contra a cor CSS nominal
- bullets, checkmarks e ícones que carregam significado também precisam permanecer claramente visíveis
- se o background fotográfico/gradiente comprometer leitura, fortaleça a cor do texto e/ou o overlay na área de copy
- ao fortalecer o overlay, preserve a regra anterior: ele deve desaparecer antes de alcançar o expert e não pode lavar a pessoa
- não sacrifique legibilidade apenas para manter uma estética `muted`

Hierarquia esperada:

1. headline = maior destaque
2. supporting copy/subheading = claramente legível, um nível abaixo
3. trust facts/bullets = discretos, mas ainda imediatamente legíveis

A revisão deve ser visual em desktop e mobile e, quando possível, acompanhada de medição de contraste sobre a composição final.

### Mobile: composição própria

Use asset/crop mobile dedicado quando necessário.

- composição vertical apropriada
- expert central ou levemente acima do centro conforme o layout
- preserve anatomia e proporções
- evite cortes ruins em cabeça, pescoço, articulações e mãos
- reserve espaço real para texto sem cobrir o rosto
- não use simples crop automático do desktop se isso degradar a composição

## 8. Google Reviews como prova social

Sempre que houver avaliações positivas **reais e verificáveis** no Google Business Profile correto do lead, incorpore prova social baseada nessas avaliações no site.

### Regra de apresentação

Quando houver material suficiente para múltiplas avaliações, use **carrossel de avaliações** como formato padrão.

- prefira avaliações positivas específicas, informativas e relevantes
- use somente reviews do perfil correto do negócio/profissional
- preserve texto fiel quando apresentado entre aspas
- não invente, combine ou reescreva avaliações como se fossem verbatim
- não invente nome, nota, data ou número de reviews
- se truncar um review, use trecho fiel e não altere o sentido
- identifique a origem como Google de forma factual, sem simular widget oficial quando não for
- estrelas só podem aparecer quando correspondem à nota real daquele review ou ao aggregate real verificado
- aggregate rating e total de avaliações só podem aparecer se forem verificados no momento da coleta
- mantenha internamente fonte/URL/place/profile e evidência da coleta

Se existir somente uma avaliação positiva utilizável, não invente slides adicionais; use a avaliação real de forma adequada até haver material suficiente para um carrossel real.

### UX do carrossel

- deve funcionar em desktop e mobile
- suporte swipe/touch quando apropriado
- controles com labels/aria
- navegação por teclado
- não dependa apenas de autoplay
- se houver autoplay, ofereça pausa/controle e respeite `prefers-reduced-motion`
- não use carrossel só para decorar; cada slide deve conter prova social real

Se não houver reviews verificáveis, não crie seção falsa de depoimentos.

## 9. Estatísticas

Não crie faixa de números automaticamente.

Uma métrica só entra quando for verificável, tiver contexto, ajudar a provar algo relevante e apoiar decisão do usuário.

Sem porcentagem inventada, número sem fonte ou stats strip de preenchimento.

## 10. Performance

### Imagens

- raster moderno e otimizado, preferindo WebP/AVIF
- hero crítico sem lazy load
- prioridade alta apenas para a principal imagem crítica quando aplicável
- imagens abaixo da dobra com lazy load quando apropriado
- `width`/`height` ou `aspect-ratio` para evitar CLS
- não sirva imagem muito maior que o necessário
- preserve masters/originais fora do bundle público quando úteis como evidência

### Fontes

- preferir no máximo 2 famílias
- carregar apenas pesos usados
- WOFF2 + `font-display: swap` quando self-hosted

### Scripts/motion

- terceiros com `async`/`defer` quando compatível
- remover bibliotecas não utilizadas
- biblioteca de animação só quando interação/scroll justificar
- respeitar `prefers-reduced-motion`
- não deixar runtime de animação serializado no HTML publicado

Não prometa PageSpeed/Lighthouse 95+ sem medir. Reporte resultado real.

## 11. Acessibilidade

- `<html lang>` correto
- alt factual em imagem de conteúdo
- imagem decorativa com alt vazio quando apropriado
- contraste visando WCAG AA
- headings em hierarquia coerente
- foco de teclado visível
- links/botões com texto ou `aria-label`
- `button` para ação, `a` para navegação
- informação essencial não depende só de cor, hover ou animação

## 12. SEO e metadata

Adapte ao estágio do projeto.

### Produção final

Quando houver URL/domínio final real:

- title conciso e descritivo
- meta description útil
- canonical absoluto correto
- robots coerente
- Open Graph/social metadata apropriados
- JSON-LD somente com fatos verificados
- favicons/theme-color quando houver identidade aprovada

### Preview/prospecção

- prefira `noindex, nofollow` quando aplicável
- não invente canonical de domínio final
- não publique schema com dados não verificados
- não simule autoria, domínio ou propriedade definitiva do cliente

## 13. Segurança e best practices

Antes de publicar:

- HTTPS
- `target="_blank"` com `rel="noopener noreferrer"`
- zero erros relevantes de console/network
- nenhum segredo/token/chave no HTML público
- nenhuma URL local, UI de editor/debug ou endpoint administrativo publicado

## 14. Hero específico

Hero começa com composição e tipografia, não uma coleção de ornaments.

Acima do headline, prefira nada. Se uma eyebrow for realmente necessária, use texto puro e discreto, sem capsule, badge, chip, emoji ou traço automático.

Evite:

`[ pill ]`
`Headline`
`Supporting copy`
`[ trust chips ]`
`[ CTA primário ] [ CTA secundário ]`

Trust facts, quando necessários, devem ser integrados editorialmente.

## 15. QA obrigatório antes de Screenshot Review e deploy

```text
SITE CORE RULE QA

SOURCE TRUTH
Invented facts/metrics/credentials: NONE
Invented quotes/testimonials/attributions: NONE
All retained quotes traceable to verified source: PASS
Image semantics match section/card labels: PASS
Image source/provenance appropriate: PASS

EXPERT HERO
Real expert source image verified when applicable: PASS
Desktop expert hero uses dedicated ultrawide composition: PASS
Desktop text safe area: PASS
Expert identity/face/pose/clothing fidelity: PASS
Overlay does not wash over expert: PASS
Hero supporting copy contrast: PASS
Hero trust facts/bullets contrast: PASS
Hero text/icons meet WCAG AA target against rendered background: PASS
Generated background adds no false factual context: PASS
Mobile composition/crop intentional and anatomically natural: PASS

GOOGLE REVIEWS
Verified Google reviews available: YES/NO
If YES, positive review proof incorporated: PASS
If multiple suitable reviews, carousel present: PASS
Reviewer text/identity/rating/date not fabricated: PASS
Aggregate rating/count, if shown, verified: PASS
Review carousel accessible and reduced-motion safe: PASS

ANTI-SLOP
Decorative pills/tags/chips/badges: NONE
Decorative eyebrow strokes without rationale: NONE
Decorative numbering without sequence meaning: NONE
Fake quote styling: NONE
Unsourced/weak stats strip: NONE
Meaningless icons/seals/stars/graphs: NONE
Repeated section template pattern: NONE or JUSTIFIED
Generic premium effects: NONE or BRAND-JUSTIFIED
Removable elements without information/hierarchy loss: NONE

COPY / CTA
Emoji in public UI: NONE
Visible em dash: NONE
Visible en dash used as punctuation: NONE
PT-BR sentence case: PASS
Unjustified Title Case in PT-BR: NONE
Unjustified ALL CAPS phrases/headings: NONE
Hero CTA buttons desktop: EXACTLY 1
Hero CTA buttons mobile: EXACTLY 1
Repeated CTA wording across distinct sections: NONE or JUSTIFIED
CTA wording matches context and destination: PASS

ACCESSIBILITY
html lang: PASS
Content image alt text truthful: PASS
Heading hierarchy: PASS
Interactive labels/aria: PASS
Keyboard focus: PASS
Contrast AA target: PASS

PERFORMANCE
Hero critical image lazy-loaded: NO
Below-fold images lazy-loaded where appropriate: PASS
Image dimensions/aspect-ratio prevent CLS: PASS
Modern optimized raster delivery: PASS
Fonts limited/optimized: PASS
Blocking/unused scripts: NONE
prefers-reduced-motion respected: PASS

SEO / SECURITY
Indexing policy matches environment: PASS
Canonical matches real environment or omitted intentionally: PASS
Metadata/OG appropriate to environment: PASS
Schema uses verified facts only: PASS
HTTPS: PASS
Target blank rel security: PASS
Console/network errors: NONE
Secrets/editor/debug/local URLs in public build: NONE
```

Além do checklist:

1. buscar `—`, `–` e Unicode emoji em copy visível
2. listar CTAs e comparar wording/destino
3. listar quotes/depoimentos e fonte
4. revisar visualmente imagens contra labels
5. verificar reviews Google e sua proveniência quando disponíveis
6. revisar screenshots desktop/mobile procurando AI-slop
7. medir/revisar contraste do supporting copy, bullets/trust facts e ícones do hero contra o background final
8. não marcar Performance/SEO como PASS sem verificar o build real

## 16. Precedência

Se outra skill, template ou referência sugerir fabricação factual, pills/chips/badges, emoji, travessões, múltiplos CTAs no hero, CTA repetitivo, Title Case inglês em PT-BR, quote inventada, imagem semanticamente errada, stats sem fonte, hero desktop 16:9 genérico quando deveria ser ultrawide, review fabricada ou texto de apoio do hero com contraste insuficiente, esta skill vence.

Só altere estas regras se o usuário pedir explicitamente uma exceção para um site específico.