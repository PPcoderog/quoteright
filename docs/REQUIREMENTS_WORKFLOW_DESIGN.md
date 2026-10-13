# Requirements-first QuoteRight

## Provider amendment
The user approved Gemini as the default on October 13, 2026 after encountering an OpenAI quota/rate-limit error. Connection settings offer Gemini (default `gemini-3.8-flash`) and OpenAI with separate session keys/model values and separate environment fallbacks. `gemini_provider.py` calls generateContent with the shared JSON schema. Both providers feed the same schema, excerpt, catalog-ID validation, and deterministic quote engine. Analysis records its provider/model. Free-tier access is subject to Google project limits and data-use terms; synthetic data remains required. No hidden provider fallback or automatic paid-model switch.

The user approved this expansion on October 13, 2026 and selected the OpenAI API. It supersedes the original Week 1 exclusions of document parsing and LLM interpretation. The original source briefs remain unchanged as historical context.

## Experience
Four distinct screens with persistent sidebar navigation and progress: customer requirements → review understanding → review proposed solution → review draft quote. Back navigation preserves inputs; changed upstream inputs invalidate dependent results. Downstream navigation requires completion of prerequisites.

1. Upload a text-based PDF, DOCX, or UTF-8 TXT file, or paste requirements. Preview extracted text. A supplied synthetic sample is an input document, not a simulated analysis. Explicit Analyze button calls OpenAI.
2. Show extracted requirements, must-have/nice-to-have priority, supporting excerpts, missing information, and catalog fit. Seller can add clarifications and rerun analysis before confirming understanding.
3. Prefill suggested products/quantities when stated; unknown quantities and terms require seller input. Unsupported needs remain visible and require acknowledgement; the system never presents them as covered. Seller can change/remove/add catalog products. Deterministic validation checks quantities and terms.
4. Display itemized DRAFT quote, pricing explanation, requirement coverage, and approval flag. Commercial edits invalidate the previous draft.

## Architecture and boundaries
documents.py extracts text locally. analysis.py uses OpenAI Responses API structured outputs, then validates schema, source excerpts, unique requirement IDs, and catalog IDs. workflow.py manages prerequisite and invalidation behavior. app.py provides shell/navigation; screens.py renders the four experiences. Existing catalog.py and pricing.py remain authoritative.

Use configurable OPENAI_MODEL (default gpt-4.1-mini). Read OPENAI_API_KEY from environment or private session-only connection settings. Never persist keys or uploaded documents to disk. store=False on API request. Only explicit analysis actions send extracted text, seller clarifications, and catalog descriptions to OpenAI. No price calculation is delegated to the model.

Accept at most 5 MB and 40,000 extracted characters; reject oversize rather than silently truncate. Reject corrupt/encrypted/no-text PDF, malformed DOCX, invalid UTF-8, empty input, unsupported formats. No OCR. DOCX includes paragraphs and tables. One bounded analysis call with a timeout; display actionable sanitized errors on missing key, refusal, invalid response, timeout, authentication, quota, and connection failure. Existing outputs cannot survive failed analysis of changed inputs.

All quotes stay DRAFT. Approval flag strictly above 10%; shared 1/12-month quote term; USD and tax excluded. An unsupported requested duration is shown in analysis and must be explicitly corrected. Missing discount defaults to the existing seller-controlled 0%, never an AI discount policy. No integrations, autonomous actions, persistence, actual approvals, or sending.

## Verification
Test real document parsers with generated PDF/DOCX fixtures, invalid inputs, response validation and provider HTTP contract through a transport double, prerequisite navigation and state invalidation, and the full four-screen workflow via Streamlit AppTest. Live model quality requires a configured key; no fixture is presented as a live model result.
