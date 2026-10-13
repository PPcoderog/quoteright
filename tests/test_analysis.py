import json
from pathlib import Path

import httpx
import pytest
from openai import OpenAI

from analysis import Analysis, AnalysisError, analyze_requirements, validate_analysis
from catalog import load_catalog

SOURCE = "We need shared planning for 20 employees for 12 months. Payroll is nice to have."
CATALOG = load_catalog(Path(__file__).resolve().parents[1] / "data/products.csv")


def payload():
    return {"customer_name": None, "summary": "Shared planning with optional payroll.",
        "term_months": 12, "term_source_quote": "for 12 months",
        "requirements": [
            {"requirement_id": "R1", "description": "Shared planning", "priority": "must_have",
             "source_quote": "shared planning for 20 employees", "suggested_product_id": "TEAM",
             "quantity": 20, "rationale": "Catalog supports shared planning."},
            {"requirement_id": "R2", "description": "Payroll", "priority": "nice_to_have",
             "source_quote": "Payroll is nice to have.", "suggested_product_id": None,
             "quantity": None, "rationale": "No payroll product in the catalog."}],
        "questions": []}


def response(body):
    return {"id": "resp_test", "object": "response", "created_at": 0, "model": "gpt-4.1-mini",
        "status": "completed", "output": [{"id": "msg_test", "type": "message", "role": "assistant",
        "status": "completed", "content": [{"type": "output_text", "text": json.dumps(body), "annotations": []}]}]}


def test_source_backed_analysis_preserves_unsupported_needs():
    result = validate_analysis(Analysis.model_validate(payload()), SOURCE, CATALOG)
    assert result.requirements[0].quantity == 20
    assert result.requirements[1].suggested_product_id is None


@pytest.mark.parametrize("change", ["unknown_product", "invented_evidence", "duplicate_id", "zero_quantity", "invented_term"])
def test_untrusted_model_values_are_rejected(change):
    body = payload()
    if change == "unknown_product": body["requirements"][0]["suggested_product_id"] = "PAYROLL"
    if change == "invented_evidence": body["requirements"][0]["source_quote"] = "We need 500 seats."
    if change == "duplicate_id": body["requirements"][1]["requirement_id"] = "R1"
    if change == "zero_quantity": body["requirements"][0]["quantity"] = 0
    if change == "invented_term": body["term_source_quote"] = "36 months"
    with pytest.raises((ValueError, AnalysisError)):
        validate_analysis(Analysis.model_validate(body), SOURCE, CATALOG)


def test_real_sdk_parses_provider_response_and_sends_no_prices():
    requests = []
    def serve(request):
        requests.append(json.loads(request.content))
        return httpx.Response(200, json=response(payload()))
    client = OpenAI(api_key="test-key", http_client=httpx.Client(transport=httpx.MockTransport(serve)))
    result = analyze_requirements(SOURCE, "", CATALOG, "test-key", "gpt-4.1-mini", client=client)
    assert result.term_months == 12
    assert result.requirements[0].suggested_product_id == "TEAM"
    assert requests[0]["store"] is False
    assert requests[0]["text"]["format"]["type"] == "json_schema"
    assert "monthly_price" not in json.dumps(requests[0]["input"])


def test_missing_key_does_not_attempt_analysis():
    with pytest.raises(AnalysisError, match="API key"):
        analyze_requirements(SOURCE, "", CATALOG, "", "gpt-4.1-mini")


@pytest.mark.parametrize("status,match", [(401, "key"), (429, "quota|limit"), (500, "unavailable")])
def test_provider_errors_are_actionable_without_echoing_document(status, match):
    client = OpenAI(api_key="test-key", max_retries=0,
        http_client=httpx.Client(transport=httpx.MockTransport(lambda request:
            httpx.Response(status, json={"error": {"message": SOURCE, "type": "server_error"}}))))
    with pytest.raises(AnalysisError, match=match) as caught:
        analyze_requirements(SOURCE, "", CATALOG, "test-key", "gpt-4.1-mini", client=client)
    assert SOURCE not in str(caught.value)


def test_refused_response_is_not_treated_as_requirements():
    body = response(payload())
    body["output"][0]["content"] = [{"type": "refusal", "refusal": "Cannot analyze this."}]
    client = OpenAI(api_key="test-key", http_client=httpx.Client(transport=httpx.MockTransport(
        lambda request: httpx.Response(200, json=body))))
    with pytest.raises(AnalysisError, match="complete|refused"):
        analyze_requirements(SOURCE, "", CATALOG, "test-key", "gpt-4.1-mini", client=client)
