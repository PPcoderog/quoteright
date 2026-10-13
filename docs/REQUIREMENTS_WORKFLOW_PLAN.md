# Requirements-first implementation plan

**Goal:** Turn the approved form prototype into a four-screen requirements-to-draft workflow.
**Architecture:** Local text extraction → validated LLM analysis → seller confirmation → deterministic quoting. Session-only state and dependency invalidation.
**Spec:** REQUIREMENTS_WORKFLOW_DESIGN.md
**Execution:** Continue in the existing dedicated project folder, implementing directly in this session as explicitly requested.

## Global constraints
PDF/DOCX/TXT; 5 MB and 40,000 characters; no OCR. Live OpenAI integration, no simulated product analysis. Existing Decimal pricing and DRAFT/approval boundaries remain. No documents or credentials persisted.

## Review focus
Missing key must not produce fabricated analysis; invalid model citations must be rejected; changed source/clarifications must invalidate downstream work; unknown quantities must require input; unsupported requirements must stay visible.

## Task 1 — Document intake
Files: documents.py, tests/test_documents.py, data/sample_rfp.txt.
- [x] Write tests for TXT decoding, DOCX paragraphs/tables, text PDF, no-text PDF, corruption and limits; run and observe missing-module failure.
- [x] Implement extract_document(name: str, content: bytes) -> str and validate_text(text: str) -> str.
- [x] Run document tests and existing business-rule suite.

## Task 2 — LLM and workflow boundary
Files: analysis.py, workflow.py, tests/test_analysis.py, tests/test_workflow.py.
- [x] Write tests for source-backed analysis, unknown product rejection, hallucinated evidence, missing key and provider response/error handling.
- [x] Implement Analysis/Requirement schemas, validate_analysis(result, source, catalog), analyze_requirements(text, clarifications, catalog, api_key, model), invalidate(state, stage), can_visit(state, step).
- [x] Use an actual OpenAI SDK client with a controlled HTTP transport for contract tests; no live calls without credentials.
- [x] Run relevant tests; record evidence.

## Task 3 — Four-screen application
Files: app.py, screens.py, tests/test_app.py, README.md, docs/LEARNING_LOG.md.
- [x] Replace prior single-screen tests with new workflow expectations; observe failure against old UI.
- [x] Build persistent sidebar navigation, locked prerequisites, progress, Back/Continue buttons, private connection settings, and distinct screens.
- [x] Verify confirmed extraction prefills proposal, unknown quantities/term require correction, unsupported needs need acknowledgement, edits hide stale draft, normal/approval/recalculation scenarios work across navigation.
- [x] Run full suite and server health; request independent final review; fix consequential findings with regression tests.
- [x] Update run steps and learning log; disclose live API verification status.
