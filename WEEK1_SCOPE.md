# Week 1 — Vibe coding MVP

**Assignment:** Build a functional application using an AI coding assistant. The instructor's custom-app path permits any stack; CSV visualizations are examples, **not mandatory** for Path C. Submission consists of a writeup documenting problem, dataset, prompts and iterations; a working screen recording (≤5 minutes); and a GitHub code link. Refer to the instructor's handout for submission timing.

**Product slice:** A seller manually produces a **draft** quote from a synthetic product catalog.

## Minimum screens / experiences
- Product catalog: search/browse synthetic SaaS offerings with visible prices.
- Configure: choose product, quantity and duration; optionally discount.
- Price & validate: exact itemized pricing, subtotal/discount/total, explicit rule explaining when approval is needed.
- Draft quote: readable summary, not represented as customer-approved.

## Acceptance tests
1. Normal configuration returns correct price and a draft quote.
2. Discount above configured limit shows 'Approval required' and cannot silently be treated as approved.
3. Changing quantity recalculates all totals correctly.

## Scope guardrails
Do not build autonomous AI, RAG, real CRM or ERP integrations, document parsing, full product dependency rules, or live approval routing.

## Learning process
Plan → sketch user flow → make first build → run locally → verify scenarios → iterate deliberately → capture prompt/change log → document learning → record ≤5-minute demo → publish code.

## Technical simplicity
Default Streamlit + pandas + small synthetic CSV files + pure Python pricing functions with unit tests. Use currency-safe arithmetic (Decimal or integer cents), never unconstrained language-model math.
