# QuoteRight learning and iteration log

Date: October 13, 2026. These are observed implementation notes; personal reflections are left for the learner to supply.

## Problem and dataset

B2B sellers need accurate, reviewable quotes with clear discount exceptions. Week 1 isolates manual configuration and deterministic calculation. The dataset contains five fictional SaaS products with synthetic USD prices: Team Workspace ($20), Flow Automation ($35), Insight Reports ($15), Support Desk ($25), Secure Access ($10), all per seat per month.

## Prompt and decision record

1. User asked to read AGENTS.md, PRODUCT_BRIEF.md, and WEEK1_SCOPE.md, propose the simplest journey and architecture, and wait for approval before coding.
2. User approved a one-page workflow, five products, shared 1/12-month term, whole-quote discount, and a strictly-above-10% approval threshold.
3. User requested a system diagram separating agentic and programmatic responsibilities. Decision: all Week 1 behavior is programmatic; agents remain future scope.
4. User authorized building and requested fresh colors. Presentation: teal controls, electric lime brand accent, light neutral background, dark text.

## Increment 1 — Catalog

Added synthetic CSV data, JSON rules, local dependency environment, catalog loading and case-insensitive search. The first test failed because the catalog module did not exist; after implementation it passed. Prices load as strings before Decimal conversion so floating-point approximations cannot enter authoritative pricing.

## Increment 2 — Quoting functions

Added pure Python input validation, itemized pricing, quote-level discount rounding, and approval flags. Tests first failed because the pricing module did not exist. After implementation, 22 catalog/business tests passed. One useful edge: 10% and 10.01% can produce the same rounded price but different approval flags. Policy evaluates the entered percentage, not the rounded dollar discount.

## Increment 3 — Draft review

Added a Streamlit page and seven AppTest scenarios. Tests initially failed because app.py did not exist. After implementation all 29 tests passed. Editing a product, quantity, term, or discount hides outdated totals until recalculation. Catalog searches leave the selected quote intact.

## Environment issues

- The first dependency download failed due to sandbox network restrictions; after requesting permission, installation succeeded in the project's virtual environment.
- The sandbox blocked the local server from binding to port 8501. After requesting permission, the server started on 127.0.0.1:8501.
- No existing repository or QuoteRight code was present. Work was placed in a separate project folder under the writable workspace; unrelated files were left intact.

## What the implementation illustrates

- Product decisions define the commercial contract: term, discount scope, approval threshold, draft status.
- Separating pricing from presentation makes exact outputs testable without clicking through the app.
- Rounding is a business rule worth stating explicitly.
- An approval flag is a policy result, not an approval grant.
- Correct totals can still mislead if they belong to old inputs; session-state snapshots address that problem.

## Final verification and review

All 29 tests passed, and the running local server's health endpoint returned `ok`. A separate code review found no critical or important defects in the approved workflow. Minor follow-up deferred: add duplicate-ID and invalid-price CSV loader regression fixtures before extending the catalog. No visual browser inspection was performed; AppTest verified interactions and displayed results.

## Your reflections — to complete after trying the app

- Which product decision did you find most consequential, and why?
- What surprised you about the architecture or tests?
- What would you change after observing a seller use the flow?
- Which prompt helped you steer the work? What would you phrase differently?

## Suggested demo sequence (under five minutes)

1. Explain the seller problem and synthetic dataset.
2. Browse/search and calculate two Team Workspace seats for 12 months: $480.
3. Enter 15% discount: $408, DRAFT and approval required.
4. Change seats to three: show recalculation message, then calculate $612.
5. Explain the deterministic pricing/agentic boundary and one lesson learned.

The user still needs to supply their own reflections, record the demo, and arrange the GitHub submission. Those have not been represented as complete.

## Iteration 4 — Requirements-first workflow

The user found the manual single-page experience too basic and requested document upload, LLM interpretation, and navigation. They approved a four-screen redesign and selected OpenAI. This explicitly expands the original Week 1 scope; the original brief files remain historical source documents.

Added local PDF/DOCX/TXT extraction; a real OpenAI Responses API structured-output adapter; supporting excerpt and catalog-ID validation; separate intake, understanding, solution, and draft screens; persistent sidebar navigation; and session-preserving Back/Continue actions. A synthetic sample RFP is supplied as input, not as a simulated analysis result. Prices are still calculated exclusively by the original Decimal functions.

Unknown seats are blank, unsupported duration requires an explicit choice, unsupported needs remain visible, and changed coverage gaps require a fresh acknowledgement. The commercial acceptance scenarios still produce $480, $408 with approval required, and $612 after revising seats.

Tests initially failed because the new parser/analysis/workflow modules were absent and the existing UI had no upload or review screens. After implementation, the navigation tests exposed a widget-identity issue: dynamic lock labels reset the current step. Stable navigation labels with separate lock status fixed it. A coverage test also caught an acknowledgement surviving newly uncovered requirements; it now resets when gap IDs change.

Verification: 60 tests passed, including real generated PDF/DOCX fixtures, SDK response parsing against controlled HTTP transport, malformed inputs and evidence, prerequisite navigation, cross-screen edits and stale drafts. Live model quality remains unverified because no local OpenAI API key was configured. Connection settings accept a private session-only key; no secrets or customer documents were persisted. A final independent review and rendered browser inspection are performed separately and recorded after completion.

Questions for your reflection: Did shifting from manual configuration to reviewing a proposed solution better express the product value? Which LLM assumptions should need explicit confirmation? What would you evaluate on a set of synthetic RFPs before trusting suggested configurations?


### Final review and browser verification

Independent review found one consequential defect: a seat count of 10^30 triggered Decimal InvalidOperation. Added a regression test, a numeric-range guard (quantities above 10^18 produce an actionable validation error), and a dedicated 64-digit local Decimal context. This is an operational numeric boundary, not a commercial seat policy. All 62 tests now pass.

Added one integrated UI test exercising Analyze through the actual OpenAI adapter and SDK with a controlled HTTP response, then confirming and calculating a draft. A headless Chrome check verified the rendered upload screen, sample RFP loading, and missing-key message. Saved intake-preview.png and sample-preview.png after waiting for the actual interface, rather than the initial loading skeleton.

Deferred minor limitations: excerpt-presence checks do not verify the semantic correctness of extracted quantities; humans must verify the displayed evidence and inputs. DOCX paragraphs and tables are grouped rather than preserving interleaved body order. Both are documented in the README. Live model quality remains unverified until the user supplies an API key in the app or server environment.

## Iteration 5 — Gemini as the default

The user created an OpenAI key but encountered a quota/rate-limit error; their ChatGPT subscription did not supply API credits. After reviewing free-tier provider options, the user approved adding Gemini and making it the default, with OpenAI still available.

Implemented a bounded Gemini REST adapter using structured JSON output. Both providers share the same validated requirements schema, catalog checks, and deterministic pricing. Connection settings retain separate provider keys/models and show where to create a Google AI Studio key. No automatic fallback sends documents to another provider. Existing analyzed results retain provider/model provenance when connection settings change.

Test-first evidence: 13 new provider/credential tests failed before implementation. After adding the adapter, routing, and UI fields, 75 tests passed. Adding the full Gemini Analyze-button → understanding → solution → draft integration test brought the suite to 76 passing tests. HTTP responses are controlled test fixtures; the app uses real provider calls and no simulated fallback. Gemini live quality still needs the user's Gemini key.

Learning: a chat subscription and developer API usage are different products; a reusable structured-data boundary makes switching model providers smaller than rewriting the quoting workflow. Free-tier eligibility, quotas, and data-use terms belong to the provider/account, not the application. Google currently lists the default Flash model as free-tier eligible, but account availability and pricing can change.

Final provider review found no consequential defects. A headless Chrome check verified the updated intake/sample flow and Gemini-specific missing-key message. Deferred minor test additions: direct timeout/network and malformed-response-shape fixtures for Gemini. Existing error handling covers those cases; live Gemini compatibility remains unverified until a key is connected.

Deployment verification note: the first browser check failed because the long-running Streamlit process retained an older screens module signature. Restarting the local server loaded the updated modules; the repeated browser check then passed (intake renders, sample loads, missing Gemini key produces the correct message). Final suite: 76 passed. The restart cleared prior server-session credentials; the user must enter a Gemini key in the refreshed app.

## Iteration 6 — Gemini timeout diagnosis

User's live Gemini call timed out. The original adapter used one 45-second timeout for connecting and reading, so the displayed error did not identify the failing stage. The user-session key is not available to the development process; the exact live failure cannot be reproduced here.

Added a 10-second connection timeout and 120-second response-read timeout, a lower thinking level for the verified default gemini-3.8-flash model, separate connection/read timeout messages, and a two-minute spinner hint. Other model IDs do not receive the model-specific thinking parameter. No automatic retries or paid-provider fallback were introduced. Google documents that default thinking increases latency; this is a mitigation and diagnostic improvement, not proof that it resolves the user's live request.

Three regression tests failed against the old timeout behavior, then passed with the change. Full suite: 81 passed. Restarted the local server to reload imported modules; session credentials must be re-entered. Next live check: retry the synthetic sample RFP; a failure on the sample suggests provider/network issues rather than a large customer document.
