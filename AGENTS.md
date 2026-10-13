# QuoteRight — Codex project instructions

## User-approved scope amendment — October 13, 2026
The user explicitly approved expanding the original Week 1 prototype to a requirements-first, four-screen workflow with PDF/DOCX/TXT upload, OpenAI LLM interpretation, human review and suggested catalog configuration. Follow `docs/REQUIREMENTS_WORKFLOW_DESIGN.md` for current scope. The manual-only and document-parsing exclusions below describe the original starter scope and are superseded for this approved expansion. Deterministic pricing, human review, synthetic data, and no autonomous commercial actions remain binding.

## Product
QuoteRight — **Complex quotes. Done right.**
AI-native quoting and proposal automation for B2B businesses selling configurable products and services.

## Product principles
- AI interprets ambiguous customer requirements and may coordinate workflows; deterministic business rules own configuration validity, pricing calculations, discount thresholds, and approval conditions.
- Never invent prices, compatibility, policy exceptions, or approvals.
- Humans review consequential commercial outputs. Draft quotes are not approved/sent quotes.
- Keep the app simple, modular, testable and ready to extend in course Weeks 2–6.
- Use synthetic customers and products only; never include proprietary prior-employer data.

## Brand
Black, white, and electric lime (#C8F04B). Clean, minimal, accessible enterprise UI. No gradients or unnecessary dashboard clutter.

## How to collaborate with the user
- The user is learning vibe coding. Explain meaningful architectural and implementation choices briefly and let them make product decisions.
- First propose a short implementation plan and screen flow; wait for approval before coding substantial features.
- Implement in small working increments; demonstrate locally and check acceptance criteria after each increment.
- Maintain clear change summaries, steps to run, and tests. Do not expand scope silently.

## Week 1 scope
Use Python + Streamlit and synthetic CSV files unless a justified alternative is agreed. Build one simple, rule-based quoting workflow:
1. Browse/search a synthetic product catalog.
2. Select products, quantities, and term to configure a quote.
3. Calculate itemized pricing deterministically using explicit, inspectable rules.
4. Flag one discount-above-threshold case as **approval required** (no real approval workflow).
5. Display a reviewable DRAFT quote and allow changes to recalculate.

Test three scenarios through the same workflow: valid quote; discount needing approval; changed quantity triggers recalculation.

## Explicitly out of scope for Week 1
RAG, agent orchestration, RFP document extraction, live integrations, autonomous actions, full CPQ dependencies, real approval workflows, contracts and billing. Charts/analytics are optional, not required by the instructor's custom-app path.

## Longer-term roadmap (tentative; subject to actual weekly briefs)
- Week 2: RAG for product specifications, policies and requirement grounding.
- Week 3: bounded agent that investigates requests and calls deterministic quoting tools.
- Week 4: evaluate model approaches for structured requirement extraction.
- Week 5: golden datasets, accuracy tests, workflow/agent evals.
- Week 6: role permissions, safety, policy checks, auditability.
