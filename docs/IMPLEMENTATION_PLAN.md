# QuoteRight Week 1 implementation plan

**Goal:** Implement the approved manual draft-quoting workflow in three working increments.
**Spec:** DESIGN.md. **Stack:** Python, Streamlit, pandas, Decimal, pytest.
**Execution:** In this session, in a dedicated new project folder. User explicitly authorized building; no additional approval gate is introduced.

## Increment 1: Catalog
- [x] Add synthetic catalog and explicit rules, dependency list, theme.
- [x] Test real catalog loading and search before implementing catalog.py.
- [x] Build catalog browsing with visible monthly prices and product selection.
- [x] Verify catalog tests and local UI startup.

## Increment 2: Deterministic quoting
- [x] Write failing tests for exact line totals, discount, threshold boundary, quantity changes, rounding, and invalid inputs.
- [x] Implement pricing.py with load_rules(path) and calculate_quote(catalog, quantities, months, discount_percent, rules).
- [x] Verify full suite. Prices must remain Decimal throughout calculations.

## Increment 3: Draft review
- [x] Test real UI with Streamlit AppTest: normal quote, approval-required quote, quantity edit makes draft stale, recalculation updates totals, empty selection.
- [x] Complete app.py with one-page catalog/configuration/draft flow and session-state snapshot comparison.
- [x] Verify full suite and local HTTP health.
- [x] Document run steps, acceptance scenarios, prompt/change log, and learning questions.

## Review focus
Empty selections should give an actionable error; invalid or unknown products must fail validation; exactly 10% must not require approval; non-finite numeric values must be rejected; changing selection, term, discount, or quantity must invalidate the current draft.
