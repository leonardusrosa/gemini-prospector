# Assistant proposal copy standard

Use this reference for client-facing proposal pages (`proposta.html`) when the optional website assistant is offered.

## Goal

Keep the assistant explanation clear to a non-technical client. The proposal should communicate three things only:

1. what the assistant does;
2. that AutoCORA handles the initial integration/configuration;
3. that third-party AI usage is paid separately by the client and is inexpensive at ordinary small-business volume.

Do not turn the proposal page into a technical or contractual disclosure. Detailed provider/account/limit clauses belong in the contract.

## Canonical pt-BR copy

### Title

**Assistente virtual inteligente (opcional)**

### Body

> Também é possível incluir um assistente no site para responder dúvidas usando as informações reais da clínica e encaminhar interessados para o WhatsApp quando necessário.
>
> A AutoCORA cuida da integração e configuração inicial. O uso da inteligência artificial fica por conta do cliente e tem custo baixo para esse tipo de atendimento.
>
> **Estimativa atual:** cerca de **R$ 1 a R$ 3 por 1.000 respostas curtas**.

## Pricing note

The BRL estimate must be based on the **production** assistant pool, never on the Groq test pool.

Current runtime contract:

- test: Groq with `qwen/qwen3.8-27b` and `openai/gpt-oss-120b` fallback;
- production: OpenRouter with `inclusionai/ling-3.0-flash` and `qwen/qwen3.7-flash` as the configured pool/fallback set.

Reference prices checked on OpenRouter on 2026-09-02:

- Ling 3.0 Flash: US$ 0.021 / 1M input tokens and US$ 0.063 / 1M output tokens;
- Qwen 3.7 Flash: US$ 0.03 / 1M input and US$ 0.13 / 1M output;
- OpenRouter standard pay-as-you-go credit purchases currently add a 5.5% platform fee.
*(Nex N2 Mini was removed from the default pool on 2026-09-02 following scheduled deprecation).*

Using a planning envelope from roughly 1.5k–10k input tokens and 120–500 output tokens per short response, the current production pool is comfortably below R$ 3 per 1,000 responses at the exchange rate used for this review. The public range is intentionally rounded upward to **R$ 1–3 / 1,000 short responses** for clarity and ordinary exchange/provider variance.

This remains a planning estimate, not a guaranteed tariff. Recheck it whenever provider/model pricing, routing, prompt size, or the production pool changes materially.

For non-Brazilian proposals, do not automatically reuse the BRL figure. Use a locale-appropriate estimate explicitly approved for that market.

## Visual treatment

Prefer one visually light, integrated information block, similar to the proposal status block rather than a second dense commercial card.

Recommended structure:

- title;
- first short paragraph: value/use case;
- second short paragraph: AutoCORA setup + client usage responsibility;
- final compact cost line with stronger emphasis.

Avoid nested cards, long legal paragraphs, feature-list treatment, tables, badges, pills, or technical diagrams.

## Client-facing vocabulary

Prefer:

- `assistente virtual inteligente`
- `informações reais da clínica` / `informações reais do negócio`
- `encaminhar interessados para o WhatsApp`
- `integração e configuração inicial`
- `uso da inteligência artificial`
- `estimativa atual`

Do not use in proposal body:

- API
- RAG
- LLM
- Groq
- Qwen
- OpenRouter
- prompt
- tokens
- inference

Those terms may appear only in technical/internal material or where legally necessary in the contract.

## Contract separation

The contract may contain the fuller operational disclosure: third-party provider account responsibility, variable consumption, provider/model substitution, suspension/limits, and non-binding estimates.

The proposal should remain concise and readable for a layperson.
