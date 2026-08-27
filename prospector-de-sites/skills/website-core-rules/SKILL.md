---
name: website-core-rules
description: HARD RULES obrigatórias para qualquer site, landing page, conceito, redesign ou preview público criado pelo Prospector. Use SEMPRE junto com redesign-premium e qualquer skill que gere UI pública de cliente. Prioriza verdade factual, design específico sem AI-slop, copy natural, CTA disciplinado, imagens semanticamente corretas, fidelidade em fotos de experts, acessibilidade, performance e SEO adequados ao ambiente.
---

# Website Core Rules

Estas regras são globais, permanentes e têm precedência sobre escolhas estéticas de `gpt-taste`, `design-taste-frontend`, referências visuais, templates e atalhos de geração.

Aplicam-se a qualquer UI pública criada para cliente ou prospecto, incluindo hero, header, serviços, cards, bio, galeria, CTA, footer, landing page, proposta visual e preview funcional.

Não se aplicam ao dashboard interno do Prospector, código-fonte, nomes de arquivo, slugs, URLs ou documentação técnica, exceto quando uma regra técnica abaixo tratar explicitamente do build/deploy público.

## 1. HARD RULE: verdade factual e rastreabilidade vencem o design

Nunca invente, complete ou embeleze como fato qualquer informação que não esteja sustentada por fonte verificável do lead ou por material fornecido explicitamente pelo usuário.

Isto inclui:

- citações e depoimentos
- nomes, cargos, credenciais e títulos
- números, percentuais, anos de experiência e métricas
- certificações, selos, rankings e avaliações
- serviços, especialidades e tecnologias
- endereços, horários, canais de contato e formas de atendimento
- resultados, promessas, diferenciais e claims comerciais
- autoria de frases
- contexto de imagens

Se houver dúvida, não presuma. Remova, reescreva de forma factual ou marque internamente para verificação.

### Citações, depoimentos e falas atribuídas

Nunca coloque entre aspas uma frase criada pelo agente, inferida, embelezada ou parafraseada como se tivesse sido dita pelo profissional, pela clínica, por um cliente ou por qualquer pessoa real.

Uma citação só pode aparecer quando o texto estiver verbatim em fonte verificável do lead ou em material fornecido pelo usuário.

Ao usar uma quote real:

- preserve o sentido e a redação original dentro das aspas
- preserve a atribuição somente se ela existir na fonte
- se a fonte não atribuir a uma pessoa específica, não invente autor
- mantenha rastreável internamente a URL, página ou arquivo de origem
- se precisar editar ou condensar, remova as aspas e converta em prosa factual

Nunca estilize um parágrafo comum como blockquote apenas para preencher espaço ou criar “personalidade”. Quotes devem parecer quotes porque são quotes.

## 2. HARD RULE: cada componente precisa ganhar o direito de existir

Nenhum elemento visual deve existir apenas para “preencher”, “dar cara de design”, ocupar espaço ou imitar um template premium.

Antes de adicionar qualquer elemento, pergunte:

> Se eu remover isto, alguma informação, hierarquia, significado, prova, navegação ou experiência relevante é perdida?

Se a resposta for não, remova.

Resolva primeiro:

- espaço
- grid
- alinhamento
- contraste
- escala
- ritmo
- hierarquia
- tipografia
- fotografia

Não tente consertar composição fraca adicionando ornamentos.

Como teste final de edição, considere se é possível cortar aproximadamente 20% dos elementos sem perda real. Se for, simplifique.

## 3. HARD RULE: nunca usar tags, pills, chips ou badges decorativos

Não use metadata em formato de cápsula, etiqueta, chip, tag, badge ou bubble em nenhum ponto do site.

Exemplo proibido acima do headline:

`Ortodontia & Harmonização · Rio Claro · Jardim Portugal`

Também é proibido transformar esse conteúdo em retângulo arredondado, cápsula com border, fundo colorido ou mini-card decorativo.

Alternativas permitidas quando a informação for necessária:

- microtexto simples sem container
- eyebrow tipográfico sem fundo e sem borda
- linha curta integrada à composição
- informação incorporada naturalmente ao headline ou supporting copy
- lista textual simples
- ícone real + texto quando o ícone tiver função semântica clara

CTA buttons e controles funcionais continuam permitidos.

## 4. HARD RULE: evitar ornamentos automáticos e sem semântica

Não use automaticamente:

- traços decorativos antes/depois de eyebrows
- numeração `01 / 02 / 03` em cards independentes
- estrelas sem avaliação real
- selos sem certificação real
- gráficos sem dados
- porcentagens sem fonte
- círculos, setas ou ícones que não comuniquem algo
- aspas gigantes sem citação real
- linhas ou divisores usados apenas porque “faltou design”

### Numeração

Só use números quando houver informação real de ordem, como:

- etapas sequenciais
- cronologia
- ranking
- prioridade
- processo estruturado
- referência posterior ao item

Se `03` puder virar `07` sem mudar o significado, a numeração provavelmente é decorativa e deve sair.

### Eyebrows

Eyebrows podem se sustentar por tipografia, tamanho, peso, cor, espaço e posicionamento. Não adicione automaticamente uma linha horizontal antes ou depois.

## 5. HARD RULE: evitar estética de “template premium genérico”

Não use como padrão automático:

- glassmorphism
- glow
- gradientes decorativos
- sombras em todos os componentes
- cantos excessivamente arredondados
- bento grid sem necessidade do conteúdo
- ícones dentro de círculos apenas por estilo
- cards para todo tipo de informação

Esses recursos só são permitidos quando a identidade, a referência aprovada ou a função do componente realmente pedir.

“Premium” deve vir de composição, tipografia, fotografia, proporção, detalhe e especificidade, não de uma coleção de efeitos.

## 6. HARD RULE: variar a estrutura conforme o conteúdo

Evite repetir seção após seção o mesmo molde:

`eyebrow + título + parágrafo + 3 cards`

A estrutura deve nascer do conteúdo. Quando apropriado, varie com:

- composição editorial
- imagem + conteúdo
- galeria
- timeline
- processo
- FAQ
- prova documental
- comparativo
- case
- lista tipográfica
- seção de contato

Não varie apenas por variedade visual. A mudança de estrutura deve melhorar leitura ou significado.

A página deve parecer específica daquele lead. Use fatos, palavras, imagens, objetos de mercado, história e repertório reais do cliente. Evite uma página que poderia ser trocada de nome e usada por qualquer concorrente.

## 7. HARD RULE: nunca usar emoji em UI pública

Não use emoji em texto, botão, navegação, CTA, trust fact, contato, card, título ou elemento decorativo.

Quando houver necessidade visual, use:

- SVG inline
- biblioteca de ícones já aprovada
- ícone vetorial local
- CSS simples quando apropriado

O ícone precisa representar algo real, ser visualmente consistente e ter texto acessível ou `aria-label` quando necessário.

Não substitua emoji por outro caractere Unicode com aparência de emoji.

## 8. HARD RULE: nunca usar travessões em copy pública

Não use travessão longo ou médio em textos visíveis:

- `—`
- `–`

Reescreva naturalmente com ponto, vírgula, dois-pontos, ponto e vírgula, parênteses com moderação ou quebra de frase.

Vale para headlines, parágrafos, CTAs, labels, navegação, captions, metadata textual, footer e proposta pública.

Hífens ortográficos, URLs, classes, slugs, CSS, JS e nomes de arquivo não entram nesta regra.

## 9. HARD RULE: PT-BR usa sentence case natural

Para interfaces e copy em português do Brasil, use capitalização natural de PT-BR.

Por padrão, títulos, subtítulos, labels, itens de navegação, botões e headings usam sentence case:

- primeira palavra com inicial maiúscula quando apropriado
- nomes próprios, marcas, siglas e produtos preservam grafia oficial
- demais palavras ficam em minúsculas conforme o português natural

Correto:

- `Conheça nossos tratamentos`
- `Tecnologia para cada etapa do seu tratamento`
- `Agendar avaliação`
- `Falar com a equipe`

Evitar:

- `Conheça Nossos Tratamentos`
- `Tecnologia Para Cada Etapa Do Seu Tratamento`
- `Agendar Avaliação`

Evite também headings, CTAs e frases completas em ALL CAPS. Microtexto curto pode receber `text-transform: uppercase` somente quando houver razão clara de hierarquia e o texto-fonte continuar natural.

## 10. HARD RULE: hero tem exatamente um botão CTA

Todo hero deve conter exatamente **um botão CTA** no desktop e no mobile.

Não use:

- CTA primário + secundário
- dois botões lado a lado
- CTA + botão outline
- dois canais de contato como botões concorrentes

Escolha a ação comercial prioritária. Mova ações secundárias para header, navegação, contato ou seção abaixo da dobra.

Não transforme a segunda ação em outro elemento com aparência de botão para contornar a regra.

## 11. HARD RULE: evitar redundância de wording nos CTAs

Não repita mecanicamente o mesmo texto em várias seções, como quatro botões `Agendar no WhatsApp`.

Cada CTA deve refletir o contexto da seção e a próxima ação real do usuário.

Mesmo quando vários CTAs levam ao WhatsApp, varie de forma contextual e honesta, por exemplo:

- hero: `Agendar avaliação`
- ortodontia: `Conversar sobre ortodontia`
- bio: `Falar com a equipe`
- dúvidas: `Tirar uma dúvida`
- contato final: `Chamar no WhatsApp`

Não use sinônimos aleatórios apenas para parecer diferente. Nunca prometa uma ação diferente daquilo que o link realmente faz.

Repetição em CTA estrutural persistente, como header ou floating CTA, pode ser aceita quando houver justificativa funcional clara.

## 12. HARD RULE: imagens precisam provar o que a interface diz

Toda imagem de conteúdo deve ser semanticamente compatível com o card, título, alt e contexto em que aparece.

Exemplos:

- card `Consultório clínico` precisa mostrar um consultório/sala de atendimento real
- `Central de esterilização` precisa mostrar esterilização/biossegurança real
- `Fachada` precisa mostrar a fachada real

Nunca escolha uma imagem apenas pelo filename. Faça inspeção visual.

Prioridade de fonte:

1. imagens first-party do site/material do lead
2. imagens fornecidas explicitamente pelo usuário
3. imagem gerada ou stock somente quando o projeto permitir e ficar claramente separada de qualquer alegação factual sobre instalações, pessoas ou resultados reais

Não use lavabo como consultório, recepção como sala clínica, foto genérica como estrutura real ou imagem de outro profissional como se fosse o lead.

O `alt` deve descrever honestamente o que a imagem mostra, sem acrescentar claims não visíveis ou não verificáveis.

## 13. HARD RULE: estatísticas só com fonte e valor decisório

Não crie automaticamente faixas com 3 ou 4 números para preencher a página.

Uma métrica deve existir somente quando:

- for verificável
- tiver contexto
- ajudar a provar autoridade, dimensão, resultado ou vantagem
- for relevante para a decisão do usuário

Evite métricas banais, porcentagens sem fonte e números usados apenas porque o template espera uma seção de stats.

Quando o dado for útil, prefira integrá-lo à narrativa, bio, case, timeline ou prova correspondente antes de criar uma faixa exclusiva.

Se uma seção de estatísticas for realmente justificada, motion discreto pode apoiar leitura, mas deve respeitar `prefers-reduced-motion` e nunca virar espetáculo.

## 14. PERFORMANCE CORE: mídia, fontes e renderização

Para páginas públicas, performance faz parte da qualidade visual.

### Imagens

- entregue raster em formato moderno e otimizado, preferindo WebP ou AVIF conforme suporte do stack
- não faça lazy-load da imagem crítica acima da dobra
- use prioridade alta apenas para a principal imagem crítica do hero quando aplicável
- use `loading="lazy"` nas imagens de conteúdo abaixo da dobra, quando apropriado
- declare `width` e `height` ou `aspect-ratio` para evitar CLS
- não sirva arquivos muito maiores que o tamanho de renderização necessário
- preserve masters/originais fora do bundle público quando forem úteis como fonte; não delete evidência original apenas para otimizar deploy

### Fontes

- prefira no máximo 2 famílias tipográficas no site
- carregue somente pesos realmente usados
- quando self-hosted, prefira WOFF2 e `font-display: swap`
- não bloqueie renderização inicial com fonte ou stylesheet desnecessário

### Scripts e animação

- scripts de terceiros devem ser `async` ou `defer` quando tecnicamente compatível
- remova bibliotecas não utilizadas
- use bibliotecas de animação somente quando interação/scroll realmente justificarem
- loop visual simples deve preferir CSS, não JS contínuo
- `will-change` só em elementos que realmente serão animados e pelo menor tempo necessário
- respeite `prefers-reduced-motion`

Não prometa PageSpeed/Lighthouse 95+ sem medir. Quando o ambiente permitir medição, busque 95+ em Performance e 100 em SEO como alvo, mas reporte o resultado real e as limitações.

## 15. ACCESSIBILITY CORE

Toda página pública deve passar no mínimo por esta revisão:

- `<html lang>` correto
- imagens decorativas com `alt=""` e, quando necessário, `aria-hidden="true"`
- imagens de conteúdo com alt factual e útil
- contraste de texto visando WCAG AA, normalmente 4.5:1 para texto comum
- botões e links com texto ou `aria-label` descritivo
- headings em hierarquia coerente, sem saltos arbitrários
- foco de teclado visível em controles interativos
- elementos clicáveis semanticamente corretos (`button` para ação, `a` para navegação)
- nenhuma informação essencial dependente apenas de cor, hover ou animação

## 16. SEO E METADATA CORE

Adapte SEO ao estágio do projeto. Nunca transforme preview de prospecção em página indexável “final” por acidente.

### Produção final do cliente

Quando houver domínio/URL final real:

- title descritivo e conciso, geralmente até ~60 caracteres
- meta description útil, normalmente entre 120 e 160 caracteres
- canonical absoluto correto
- robots coerente com intenção de indexação
- Open Graph com `og:title`, `og:description`, `og:url`, `og:image`, `og:image:alt`, `og:site_name` e locale apropriado
- social card equivalente quando necessário
- JSON-LD Schema.org somente com tipo e dados realmente sustentados
- favicon e apple-touch-icon quando houver identidade aprovada
- `theme-color` quando fizer sentido

Imagem de compartilhamento 1200x630 é o padrão preferido quando houver OG image dedicada, mas não invente uma arte ou branding não aprovado apenas para cumprir checklist.

### Preview/proposta de prospecção

Para preview temporário, demonstração ou URL genérica de Vercel:

- prefira `noindex, nofollow` ou política equivalente quando aplicável
- não invente canonical de domínio final que ainda não existe
- não publique schema com dados não verificados
- não simule autoria, propriedade ou domínio definitivo do cliente

`meta author` não é requisito obrigatório. Use somente se existir autoria real e houver motivo para expô-la.

## 17. SECURITY E BEST PRACTICES CORE

Antes de publicar:

- HTTPS ativo
- `target="_blank"` acompanhado de `rel="noopener noreferrer"`
- nenhum erro de console ou network relevante
- nenhuma dependência conhecida e desnecessariamente vulnerável no build
- nenhum segredo, token, chave, endpoint administrativo ou URL local exposto no HTML público
- nenhuma UI de editor/debug publicada junto com o site final

## 18. Hero específico

Hero deve começar com composição e tipografia, não com uma coleção de ornaments.

Acima do headline, prefira nada. Se uma eyebrow realmente acrescentar contexto, use texto puro e discreto, sem capsule, badge, tag, chip, bubble, emoji ou traço decorativo automático.

Evite especialmente:

`[ pill de categoria ]`
`Headline grande`
`Supporting copy`
`[ chips de confiança ]`
`[ CTA primário ] [ CTA secundário ]`

Trust facts, quando necessários, devem ser integrados editorialmente, sem badges.

### Hero com foto real de expert

Quando o hero usa uma foto real do profissional/lead, a imagem deve funcionar como **retrato factual**, não como matéria-prima para recriar a pessoa.

#### Fidelidade da pessoa

Ao editar, expandir ou adaptar a foto fornecida, preserve a pessoa real. Não altere sem pedido explícito do usuário:

- identidade e estrutura facial
- expressão
- pose
- roupa
- cabelo
- textura natural da pele
- proporções corporais
- mãos e anatomia

Evite beauty filter, smoothing artificial, “perfeição” de pele, rejuvenescimento, mudança de corpo, reconstrução facial, alteração de roupa ou qualquer transformação que faça o expert parecer outra pessoa.

Se não existir foto-fonte utilizável do expert, **não gere uma suposta foto real dele por inferência**. Peça ou use uma fonte first-party verificável.

#### Desktop

Para hero editorial full-width com texto e expert:

- prefira asset horizontal dedicado, 16:9 ou mais largo quando a composição pedir
- coloque o expert no lado oposto ao bloco principal de texto; em layouts com copy à esquerda, o expert normalmente fica à direita
- reserve uma área limpa de leitura para headline, supporting copy e CTA, tipicamente nos primeiros 40% a 50% do canvas quando o texto está à esquerda
- não posicione texto sobre rosto, olhos, mãos ou detalhes importantes da pessoa
- extensão de background deve manter perspectiva, luz, profundidade e ambiente coerentes
- não adicione objetos, arquitetura, equipamento ou contexto que possa ser confundido com fatos reais sobre a clínica/profissional

#### Overlay funcional para legibilidade

Gradiente/overlay é permitido no hero quando tiver função real de contraste, mesmo que gradientes decorativos sejam evitados em outras partes.

Quando usado:

- escolha cor coerente com o background da página/identidade
- mantenha a área do texto suficientemente sólida para contraste confiável
- inicie a transição de forma progressiva próximo à região central, conforme a composição
- faça o overlay desaparecer **antes de alcançar a pessoa**
- nunca lave rosto, pele, roupa ou silhueta do expert
- preserve contraste, nitidez e tons naturais no lado da pessoa
- evite haze, neblina, blur artificial ou efeito “washed out”
- prefira overlay em CSS quando isso oferecer melhor controle responsivo e não prejudicar a fotografia; baked overlay só quando houver motivo técnico/compositivo claro

O objetivo é legibilidade, não criar atmosfera genérica.

#### Mobile

Não trate o mobile como simples crop automático do desktop quando isso prejudicar o expert ou a leitura.

Prefira um asset/composição mobile dedicado quando necessário:

- formato vertical ou portrait apropriado ao primeiro fold
- expert central ou levemente acima do centro quando fizer sentido
- preserve rosto, cabeça, ombros e anatomia sem cortes acidentais
- evite crop em pescoço, articulações, mãos ou pontos visualmente estranhos
- crie negative space real acima ou abaixo da pessoa para a copy, conforme a composição
- use gradiente vertical apenas quando necessário para contraste e sem encobrir o expert
- mantenha a pessoa dominante e reconhecível sem empurrar todo o conteúdo essencial para fora do primeiro fold

Desktop e mobile podem usar assets diferentes derivados da mesma foto-fonte, desde que ambos preservem identidade e veracidade.

#### Extensão generativa de background

Pode ser usada para completar o canvas quando necessário, mas somente como extensão compositiva neutra.

A extensão deve:

- parecer continuidade plausível do ambiente
- manter iluminação e perspectiva coerentes
- não introduzir instalações, equipamentos, diplomas, logos, pessoas ou sinais que impliquem fatos não verificados
- não competir com o expert
- não ter aparência de stock genérico ou cenário artificial

Se a extensão puder induzir o visitante a acreditar que um espaço gerado é a clínica real, não use esse recurso.

## 19. Componentes funcionais versus decoração

Permitido quando funcional:

- botão CTA
- input
- select
- menu
- controle de formulário
- card quando melhora scanning ou agrupamento real
- ícone quando comunica função/semântica real

Proibido quando decorativo ou metadata-first:

- category chip
- location pill
- specialty badge
- trust badge
- floating label decorativa
- mini tag acima do título
- fileira de chips de serviços
- ícone sem significado
- selo sem certificado
- número sem ordem real

## 20. QA obrigatório antes de Screenshot Review e deploy

```text
SITE CORE RULE QA

SOURCE TRUTH
Invented facts/metrics/credentials: NONE
Invented quotes/testimonials/attributions: NONE
All retained quotes traceable to verified source: PASS
Image semantics match section/card labels: PASS
Image source/provenance appropriate: PASS

EXPERT HERO IMAGE (when applicable)
Expert uses verified/source image: PASS
Face/identity/expression/pose/clothing fidelity: PASS
Natural skin/hair/body proportions preserved: PASS
Desktop text safe area: PASS
Desktop text does not overlap important subject features: PASS
Overlay reaches/washes over expert: NO
Background extension introduces factual-looking invented context: NO
Mobile uses deliberate composition/crop: PASS
Mobile expert anatomy/crop natural: PASS
Desktop/mobile hero asset quality: PASS

ANTI-SLOP
Decorative pills/tags/chips/badges: NONE
Decorative eyebrow strokes without rationale: NONE
Decorative numbering without sequence meaning: NONE
Fake quote styling: NONE
Unsourced or weak stats strip: NONE
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
Hero metadata capsule: NONE
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
Below-fold content images lazy-loaded where appropriate: PASS
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

Além do checklist automático:

1. faça busca textual por `—`, `–` e Unicode emoji em copy visível
2. liste todos os CTAs e compare wording/destino
3. liste quotes/depoimentos e a fonte de cada um
4. revise visualmente cada imagem de conteúdo contra o label da seção
5. em hero com expert, compare desktop e mobile com a foto-fonte e verifique identidade, crop, safe area e overlay
6. revise screenshots desktop e mobile procurando AI-slop que não aparece em nomes de classe
7. não marque Performance/SEO como PASS sem verificar o build real correspondente

## 21. Precedência

Se outra skill, inspiração, template, referência, componente existente ou ferramenta sugerir fabricação factual, pills/chips/badges, emoji, travessões, múltiplos CTAs no hero, CTA repetitivo, Title Case inglês em PT-BR, quotes inventadas, imagens semanticamente erradas, alteração indevida da identidade do expert, stats sem fonte ou ornamentação genérica sem função, esta skill vence.

Só altere estas regras se o usuário pedir explicitamente uma exceção para um site específico.