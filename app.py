"""QuoteRight application shell and four-step navigation."""
import os
from decimal import InvalidOperation
from pathlib import Path

import streamlit as st

from catalog import load_catalog
from pricing import load_rules
from screens import render_intake, render_understanding, render_solution, render_quote
from workflow import can_visit

ROOT = Path(__file__).resolve().parent
STEPS = ['Customer requirements', 'Review understanding', 'Review solution', 'Draft quote']
st.set_page_config(page_title='QuoteRight · Requirements to quote', page_icon='✳', layout='wide')
# Preserve editable values when their screen is not rendered (Streamlit otherwise cleans them up).
PERSISTENT = {'api_key', 'model', 'gemini_api_key', 'gemini_model', 'provider', 'source_mode', 'requirements_text', 'clarifications',
              'products', 'months', 'discount', 'coverage_ack', 'questions_ack', 'search'}
for key in list(st.session_state):
    if key in PERSISTENT or key.startswith('quantity_'):
        st.session_state[key] = st.session_state[key]
if 'requested_step' in st.session_state:
    st.session_state['nav'] = st.session_state.pop('requested_step')
st.session_state.setdefault('nav', 0)
st.markdown('''
<style>
.block-container {max-width: 1120px; padding-top: 2.5rem; padding-bottom: 3rem;}
h1,h2,h3 {letter-spacing:-0.035em;}
section[data-testid="stSidebar"] {border-right: 1px solid #D0E5DE;}
.brand {background:#C8F04B;color:#152E34;padding:.5rem .8rem;border-radius:9px;
        display:inline-block;font-weight:800;letter-spacing:.03em;margin-bottom:1rem;}
.eyebrow {color:#087F8C;font-size:.8rem;font-weight:700;letter-spacing:.12em;margin-bottom:.5rem;}
.draft-tag {background:#C8F04B;color:#152E34;padding:.3rem .75rem;border-radius:6px;display:inline-block;font-weight:800;}
div[data-testid="stMetric"] {background:#E8F3EF;padding:1rem;border-radius:12px;}
</style>
''', unsafe_allow_html=True)
try:
    catalog = load_catalog(ROOT / 'data/products.csv')
    rules = load_rules(ROOT / 'data/rules.json')
except (OSError, ValueError, InvalidOperation, KeyError) as error:
    st.error(f'Unable to load catalog or pricing rules: {error}')
    st.stop()

with st.sidebar:
    st.markdown('<div class="brand">✳ QuoteRight</div>', unsafe_allow_html=True)
    st.caption('Complex quotes. Done right.')
    st.radio('YOUR QUOTE WORKFLOW', range(4), key='nav',
             format_func=lambda i: f'{i + 1:02d}  {STEPS[i]}')
    locked = [str(i + 1) for i in range(1, 4) if not can_visit(st.session_state, i)]
    if locked:
        st.caption('Complete preceding steps to unlock: ' + ', '.join(locked))
    st.divider()
    if st.session_state.get('document_name'):
        st.caption('CURRENT REQUEST')
        st.write(st.session_state['document_name'])
    with st.expander('Connection settings'):
        provider_name = st.selectbox('AI provider', ['Gemini', 'OpenAI'], key='provider')
        if provider_name == 'Gemini':
            st.text_input('Gemini API key', type='password', key='gemini_api_key',
                          help='Use a Google AI Studio key. Alternatively set GEMINI_API_KEY before starting the server.')
            st.link_button('Get a Gemini API key', 'https://aistudio.google.com/apikey')
            st.text_input('Model', value=os.getenv('GEMINI_MODEL', 'gemini-3.8-flash'), key='gemini_model')
            st.caption('Free-tier availability and limits depend on your Google project. Use synthetic RFPs; free-tier content may be used to improve Google products.')
            api_key = st.session_state.get('gemini_api_key', '').strip() or os.getenv('GEMINI_API_KEY', '')
            model = st.session_state.get('gemini_model', '').strip() or 'gemini-3.8-flash'
        else:
            st.text_input('OpenAI API key', type='password', key='api_key',
                          help='Session only. Alternatively set OPENAI_API_KEY before starting the server.')
            st.text_input('Model', value=os.getenv('OPENAI_MODEL', 'gpt-4.1-mini'), key='model')
            api_key = st.session_state.get('api_key', '').strip() or os.getenv('OPENAI_API_KEY', '')
            model = st.session_state.get('model', '').strip() or 'gpt-4.1-mini'
        st.caption('Key stays in server session memory; it is not written to a file.')
    provider = provider_name.lower()
    st.caption('API key configured' if api_key else 'Add an API key to enable analysis')
    st.caption('Synthetic catalog · Session-only drafts')

step = st.session_state['nav']
st.markdown(f'<div class="eyebrow">NEW QUOTE / STEP {step + 1} OF 4</div>', unsafe_allow_html=True)
st.progress((step + 1) / 4)
if not can_visit(st.session_state, step):
    st.title(STEPS[step])
    st.info('Complete the preceding steps first. Analyze a document, confirm your understanding, then review and price the solution.')
    st.button('Back to requirements', on_click=lambda: st.session_state.update(nav=0))
else:
    [lambda: render_intake(catalog, api_key, model, ROOT, provider=provider),
     lambda: render_understanding(catalog, api_key, model, provider=provider),
     lambda: render_solution(catalog, rules),
     lambda: render_quote(catalog, rules)][step]()
st.divider()
st.caption('Human-reviewed drafts · Explicit pricing rules · USD, tax excluded · No approval or sending workflow connected')
