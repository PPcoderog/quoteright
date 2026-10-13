"""Gemini REST adapter: bounded request, structured output, sanitized errors."""
import json
import re

import httpx


class GeminiError(ValueError):
    pass


def generate_gemini(prompt: str, instructions: str, schema: dict, api_key: str,
                    model: str, *, client=None) -> dict:
    if not re.fullmatch(r'[A-Za-z0-9._-]+', model):
        raise GeminiError('Enter a Gemini model ID in Connection settings.')
    timeout = httpx.Timeout(120.0, connect=10.0, write=30.0, pool=10.0)
    config = {'responseMimeType': 'application/json',
              'responseJsonSchema': schema, 'maxOutputTokens': 12000}
    if model == 'gemini-3.8-flash':
        config['thinkingConfig'] = {'thinkingLevel': 'low'}
    owns_client = client is None
    if owns_client:
        client = httpx.Client(timeout=timeout)
    try:
        response = client.post(
            f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent',
            headers={'x-goog-api-key': api_key.strip()},
            json={'systemInstruction': {'parts': [{'text': instructions}]},
                  'contents': [{'role': 'user', 'parts': [{'text': prompt}]}],
                  'generationConfig': config},
            timeout=timeout,
        )
        if response.status_code in {400, 401}:
            raise GeminiError('Gemini rejected the key or request. Check your Gemini API key and model in Connection settings.')
        if response.status_code == 403:
            raise GeminiError('Gemini access denied. Check your API key, project permissions, and regional availability.')
        if response.status_code == 404:
            raise GeminiError('The Gemini model is unavailable. Choose an available model in Connection settings.')
        if response.status_code == 429:
            raise GeminiError('Gemini quota or rate limit reached. Check your free-tier limits in Google AI Studio and try again later.')
        if not response.is_success:
            raise GeminiError('Gemini is temporarily unavailable. Try again later.')
        body = response.json()
        candidates = body.get('candidates', [])
        if not candidates or candidates[0].get('finishReason') != 'STOP':
            raise GeminiError('Gemini blocked or could not complete the analysis. Try a shorter document or clarify its requirements.')
        parts = candidates[0]['content']['parts']
        text = ''.join(part.get('text', '') for part in parts if not part.get('thought', False))
        parsed = json.loads(text)
        if not isinstance(parsed, dict):
            raise GeminiError('Gemini returned an invalid analysis. Try again; no quote was generated.')
        return parsed
    except httpx.ConnectTimeout:
        raise GeminiError('Could not connect to Gemini within 10 seconds. Check your network, VPN, or firewall and try again.') from None
    except httpx.ReadTimeout:
        raise GeminiError('Gemini did not return a response within 120 seconds. Try the sample RFP to distinguish document size from provider or network delays.') from None
    except httpx.TimeoutException:
        raise GeminiError('The Gemini request timed out while sending or waiting for a connection. Check your network and try again.') from None
    except httpx.RequestError:
        raise GeminiError('Could not connect to Gemini. Check your network and try again.') from None
    except (json.JSONDecodeError, KeyError, IndexError, TypeError, AttributeError):
        raise GeminiError('Gemini returned an invalid analysis. Try again; no quote was generated.') from None
    finally:
        if owns_client:
            client.close()
