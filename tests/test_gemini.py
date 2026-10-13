import json

import httpx
import pytest

from analysis import AnalysisError, analyze_requirements
from tests.test_analysis import CATALOG, SOURCE, payload


def gemini_response(body):
    return {'candidates': [{'finishReason': 'STOP', 'content': {'role': 'model',
        'parts': [{'text': json.dumps(body)}]}}]}


def test_gemini_extracts_validated_requirements_with_schema_and_header_key():
    requests = []
    def serve(request):
        requests.append(request)
        return httpx.Response(200, json=gemini_response(payload()))
    with httpx.Client(transport=httpx.MockTransport(serve)) as client:
        result = analyze_requirements(SOURCE, '', CATALOG, 'test-gemini-key', 'gemini-3.8-flash', provider='gemini', client=client)
    assert result.requirements[0].quantity == 20
    assert result.requirements[1].suggested_product_id is None
    assert requests[0].url.host == 'generativelanguage.googleapis.com'
    assert requests[0].url.path.endswith('/models/gemini-3.8-flash:generateContent')
    assert requests[0].headers['x-goog-api-key'] == 'test-gemini-key'
    assert 'test-gemini-key' not in str(requests[0].url)
    body = json.loads(requests[0].content)
    assert body['generationConfig']['responseMimeType'] == 'application/json'
    assert body['generationConfig']['responseJsonSchema']['type'] == 'object'
    assert 'monthly_price' not in json.dumps(body['contents'])


@pytest.mark.parametrize('status,expected', [(400, 'key|request'), (403, 'access|key'), (404, 'model'), (429, 'limit|quota'), (503, 'unavailable')])
def test_gemini_provider_errors_are_sanitized(status, expected):
    with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(status,
        json={'error': {'message': SOURCE}}))) as client:
        with pytest.raises(AnalysisError, match=expected) as caught:
            analyze_requirements(SOURCE, '', CATALOG, 'test-key', 'gemini-3.8-flash', provider='gemini', client=client)
    assert SOURCE not in str(caught.value)


@pytest.mark.parametrize('body', [
    {'promptFeedback': {'blockReason': 'SAFETY'}},
    {'candidates': [{'finishReason': 'MAX_TOKENS', 'content': {'parts': [{'text': '{}'}]}}]},
    {'candidates': [{'finishReason': 'STOP', 'content': {'parts': [{'text': 'not json'}]}}]},
    {'candidates': [{'finishReason': 'STOP', 'content': {'parts': [{'text': '{}'}]}}]},
])
def test_gemini_blocked_incomplete_and_invalid_results_never_become_quotes(body):
    with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200, json=body))) as client:
        with pytest.raises(AnalysisError):
            analyze_requirements(SOURCE, '', CATALOG, 'test-key', 'gemini-3.8-flash', provider='gemini', client=client)


def test_gemini_hallucinated_product_is_rejected_by_shared_validation():
    body = payload()
    body['requirements'][0]['suggested_product_id'] = 'INVENTED'
    with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200, json=gemini_response(body)))) as client:
        with pytest.raises(AnalysisError, match='outside the catalog'):
            analyze_requirements(SOURCE, '', CATALOG, 'test-key', 'gemini-3.8-flash', provider='gemini', client=client)


def test_missing_gemini_key_does_not_reuse_openai_credentials():
    with pytest.raises(AnalysisError, match='Gemini API key'):
        analyze_requirements(SOURCE, '', CATALOG, '', 'gemini-3.8-flash', provider='gemini')


def test_default_model_uses_low_thinking_and_longer_read_timeout():
    requests = []
    def serve(request):
        requests.append(request)
        return httpx.Response(200, json=gemini_response(payload()))
    with httpx.Client(transport=httpx.MockTransport(serve)) as client:
        analyze_requirements(SOURCE, '', CATALOG, 'test-key', 'gemini-3.8-flash', provider='gemini', client=client)
    request = requests[0]
    assert request.extensions['timeout']['read'] == 120.0
    assert request.extensions['timeout']['connect'] == 10.0
    assert json.loads(request.content)['generationConfig']['thinkingConfig']['thinkingLevel'] == 'low'


@pytest.mark.parametrize('error_type,message', [(httpx.ReadTimeout, '120 seconds'),
    (httpx.ConnectTimeout, 'connect'), (httpx.ConnectError, 'network')])
def test_connection_and_slow_response_errors_are_distinguished_without_retry(error_type, message):
    requests = []
    def fail(request):
        requests.append(request)
        raise error_type('private provider details', request=request)
    with httpx.Client(transport=httpx.MockTransport(fail)) as client:
        with pytest.raises(AnalysisError, match=message) as caught:
            analyze_requirements(SOURCE, '', CATALOG, 'test-key', 'gemini-3.8-flash', provider='gemini', client=client)
    assert len(requests) == 1
    assert 'private provider details' not in str(caught.value)


def test_other_models_do_not_receive_unsupported_thinking_settings():
    requests = []
    def serve(request):
        requests.append(request)
        return httpx.Response(200, json=gemini_response(payload()))
    with httpx.Client(transport=httpx.MockTransport(serve)) as client:
        analyze_requirements(SOURCE, '', CATALOG, 'test-key', 'gemini-2.5-flash', provider='gemini', client=client)
    assert 'thinkingConfig' not in json.loads(requests[0].content)['generationConfig']
