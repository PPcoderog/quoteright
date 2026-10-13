# Approved Week 1 design

Approved in chat on October 13, 2026. The user owns product decisions and requested fresh colors when authorizing implementation.

## Outcome
A seller manually creates an accurate, reviewable DRAFT quote from five fictional SaaS products. One Streamlit page supports catalog search, product selection, quantities, shared duration, discount, calculation, and draft review.

## Commercial rules
- Synthetic per-seat monthly USD prices. No tax or term-based price reductions.
- Duration: 1 or 12 months. Positive integer quantities.
- Quote discount: 0–100%, at most two decimal places, applied to the subtotal.
- Each line = monthly price × quantity × months. Round the subtotal's discount once to cents using ROUND_HALF_UP; total = subtotal − discount.
- Discounts strictly above 10% require approval; exactly 10% does not.
- Every quote stays DRAFT, including quotes not requiring discount approval.
- Editing any quote input makes the previous draft stale until recalculated.

## Components
Streamlit owns interaction and session state. pandas loads CSV values as strings to preserve decimal prices. Pure Python functions validate inputs, calculate with Decimal, and flag approval. A JSON rules file supplies terms, currency, and threshold. Tests exercise business rules and the UI workflow.

## Agentic boundary
Week 1 contains no agent or model. Future agents may interpret requirements and call validated quoting tools. Deterministic code continues to own authoritative pricing and approval conditions; humans review consequential outputs.

## Presentation
Light neutral background, dark ink, fresh teal primary controls, electric lime accents. Clear draft and approval labels; no gradients. No persistence beyond the browser session.

## Scope
No database, authentication, sending, export, real approvals, integrations, RAG, agents, contracts, or billing.
