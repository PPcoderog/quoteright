from pathlib import Path

from streamlit.testing.v1 import AppTest
from analysis import Analysis

APP = Path(__file__).resolve().parents[1] / 'app.py'
SOURCE = 'We need shared planning for 2 employees for 12 months. Payroll is nice to have.'


def analyzed_fixture():
    # Controlled provider result for tests only; never used by the live app.
    return Analysis.model_validate({'customer_name': 'Fictional customer', 'summary': 'Planning with optional payroll.',
        'term_months': 12, 'term_source_quote': 'for 12 months',
        'requirements': [{'requirement_id': 'R1', 'description': 'Shared planning', 'priority': 'must_have',
            'source_quote': 'shared planning for 2 employees', 'suggested_product_id': 'TEAM', 'quantity': 2,
            'rationale': 'Supports shared planning.'},
            {'requirement_id': 'R2', 'description': 'Payroll', 'priority': 'nice_to_have', 'source_quote': 'Payroll is nice to have.',
             'suggested_product_id': None, 'quantity': None, 'rationale': 'Not in the catalog.'}], 'questions': []})


def review_app():
    app = AppTest.from_file(str(APP), default_timeout=15).run()
    app.session_state['source_text'] = SOURCE
    app.session_state['analysis'] = analyzed_fixture()
    app.session_state['analysis_inputs'] = (SOURCE, '')
    app.session_state['nav'] = 1
    return app.run()


def proposal_app():
    app = review_app()
    app.button(key='confirm_understanding').click().run()
    assert not app.exception
    assert app.multiselect(key='products').value == ['TEAM']
    assert app.text_input(key='quantity_TEAM').value == '2'
    app.checkbox(key='coverage_ack').check().run()
    return app


def test_first_screen_is_document_intake_and_later_steps_are_locked():
    app = AppTest.from_file(str(APP), default_timeout=15).run()
    assert not app.exception
    assert len(app.get('file_uploader')) == 1
    assert not app.multiselect
    app.radio(key='nav').set_value(2).run()
    assert not app.multiselect
    assert any('Complete' in item.value for item in app.info)


def test_missing_key_explains_connection_without_fabricating_result(monkeypatch):
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    monkeypatch.delenv('GEMINI_API_KEY', raising=False)
    app = AppTest.from_file(str(APP), default_timeout=15).run()
    app.button(key='load_sample').click().run()
    app.button(key='analyze').click().run()
    assert not app.exception
    assert any('API key' in item.value for item in app.error)
    assert 'analysis' not in app.session_state


def test_confirmation_prefills_solution_and_keeps_unsupported_needs_visible():
    app = proposal_app()
    assert any('Payroll' in item.value for item in app.warning)
    assert app.selectbox(key='months').value == 12


def test_coverage_acknowledgement_is_required_before_quote():
    app = review_app()
    app.button(key='confirm_understanding').click().run()
    app.button(key='calculate').click().run()
    assert any('uncovered' in item.value for item in app.error)
    assert 'draft' not in app.session_state


def test_normal_quote_and_back_navigation_keep_confirmed_inputs():
    app = proposal_app()
    app.button(key='calculate').click().run()
    assert not app.exception
    assert app.metric[0].value == '$480.00'
    assert app.metric[2].value == '$480.00'
    assert any('DRAFT' in item.value for item in app.markdown)
    app.button(key='back_solution').click().run()
    assert app.text_input(key='quantity_TEAM').value == '2'
    app.radio(key='nav').set_value(3).run()
    assert app.metric[2].value == '$480.00'


def test_discount_exception_and_changed_quantity_recalculate_across_screens():
    app = proposal_app()
    app.number_input(key='discount').set_value(15.0).run()
    app.button(key='calculate').click().run()
    assert app.metric[2].value == '$408.00'
    assert any('Approval required' in item.value for item in app.warning)
    app.button(key='back_solution').click().run()
    app.text_input(key='quantity_TEAM').set_value('3').run()
    assert 'draft' not in app.session_state
    app.radio(key='nav').set_value(3).run()
    assert not app.metric
    app.radio(key='nav').set_value(2).run()
    app.button(key='calculate').click().run()
    assert not app.exception
    assert app.metric[0].value == '$720.00'
    assert app.metric[2].value == '$612.00'


def test_changed_clarifications_invalidate_confirmation_and_draft():
    app = proposal_app()
    app.button(key='calculate').click().run()
    app.radio(key='nav').set_value(1).run()
    app.text_area(key='clarifications').set_value('Actually 30 employees.').run()
    assert 'draft' not in app.session_state
    assert app.button(key='confirm_understanding').disabled
    app.radio(key='nav').set_value(2).run()
    assert not app.multiselect


def test_unknown_quantity_and_term_are_not_silently_defaulted():
    app = review_app()
    result = analyzed_fixture()
    result.requirements[0].quantity = None
    result.term_months = None
    result.term_source_quote = ''
    app.session_state['analysis'] = result
    app.run()
    app.button(key='confirm_understanding').click().run()
    assert app.text_input(key='quantity_TEAM').value == ''
    assert app.selectbox(key='months').value is None
    app.checkbox(key='coverage_ack').check().run()
    app.button(key='calculate').click().run()
    assert app.error
    assert 'draft' not in app.session_state


def test_search_and_commercial_inputs_survive_back_navigation():
    app = proposal_app()
    app.text_input(key='search').set_value('handoffs').run()
    assert app.dataframe[0].value.iloc[0]['Product'] == 'Flow Automation'
    app.radio(key='nav').set_value(1).run()
    app.radio(key='nav').set_value(2).run()
    assert app.multiselect(key='products').value == ['TEAM']
    assert app.text_input(key='quantity_TEAM').value == '2'


def test_changed_source_discards_analysis_and_existing_draft():
    app = proposal_app()
    app.button(key='calculate').click().run()
    app.radio(key='nav').set_value(0).run()
    app.radio(key='source_mode').set_value('Paste text').run()
    app.text_area(key='requirements_text').set_value('A different customer needs 7 automation seats.').run()
    assert 'analysis' not in app.session_state
    assert 'draft' not in app.session_state
    app.radio(key='nav').set_value(3).run()
    assert not app.metric


def test_new_coverage_gaps_require_new_acknowledgement():
    app = proposal_app()
    assert app.checkbox(key='coverage_ack').value
    app.multiselect(key='products').set_value(['FLOW']).run()
    assert not app.checkbox(key='coverage_ack').value
    app.button(key='calculate').click().run()
    assert 'draft' not in app.session_state
    assert any('uncovered' in item.value for item in app.error)


def test_analyze_button_runs_real_adapter_and_advances_through_workflow(monkeypatch):
    import json
    import httpx
    from openai import OpenAI
    import analysis
    from tests.test_analysis import response

    client = OpenAI(api_key='test-key', http_client=httpx.Client(transport=httpx.MockTransport(
        lambda request: httpx.Response(200, json=response(analyzed_fixture().model_dump())))))
    monkeypatch.setattr(analysis, 'OpenAI', lambda **kwargs: client)
    app = AppTest.from_file(str(APP), default_timeout=15).run()
    app.selectbox(key='provider').set_value('OpenAI').run()
    app.radio(key='source_mode').set_value('Paste text').run()
    app.text_area(key='requirements_text').set_value(SOURCE).run()
    app.text_input(key='api_key').set_value('test-key').run()
    app.button(key='analyze').click().run()
    assert not app.exception
    assert app.radio(key='nav').value == 1
    assert app.session_state['analysis'].requirements[0].quantity == 2
    app.button(key='confirm_understanding').click().run()
    app.checkbox(key='coverage_ack').check().run()
    app.button(key='calculate').click().run()
    assert not app.exception
    assert app.metric[2].value == '$480.00'


def test_gemini_is_default_and_provider_credentials_are_separate(monkeypatch):
    monkeypatch.delenv('GEMINI_API_KEY', raising=False)
    monkeypatch.setenv('OPENAI_API_KEY', 'test-openai-env-key')
    app = AppTest.from_file(str(APP), default_timeout=15).run()
    assert app.selectbox(key='provider').value == 'Gemini'
    assert app.text_input(key='gemini_api_key').value == ''
    app.text_input(key='gemini_api_key').set_value('test-gemini-key').run()
    app.selectbox(key='provider').set_value('OpenAI').run()
    assert app.text_input(key='api_key').value == ''
    app.text_input(key='api_key').set_value('test-openai-key').run()
    app.selectbox(key='provider').set_value('Gemini').run()
    assert app.text_input(key='gemini_api_key').value == 'test-gemini-key'
    assert app.text_input(key='gemini_model').value.startswith('gemini-')


def test_gemini_analyze_button_advances_using_shared_validated_analysis(monkeypatch):
    import httpx
    import gemini_provider
    from tests.test_gemini import gemini_response
    client = httpx.Client(transport=httpx.MockTransport(lambda request:
        httpx.Response(200, json=gemini_response(analyzed_fixture().model_dump()))))
    monkeypatch.setattr(gemini_provider.httpx, 'Client', lambda **kwargs: client)
    app = AppTest.from_file(str(APP), default_timeout=15).run()
    app.radio(key='source_mode').set_value('Paste text').run()
    app.text_area(key='requirements_text').set_value(SOURCE).run()
    app.text_input(key='gemini_api_key').set_value('test-gemini-key').run()
    app.button(key='analyze').click().run()
    assert not app.exception
    assert app.radio(key='nav').value == 1
    assert app.session_state['analysis'].requirements[0].quantity == 2
    assert app.session_state['analysis_connection'].startswith('Gemini')
    app.button(key='confirm_understanding').click().run()
    app.checkbox(key='coverage_ack').check().run()
    app.button(key='calculate').click().run()
    assert app.metric[2].value == '$480.00'
