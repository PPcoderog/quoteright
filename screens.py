"""Distinct requirements, interpretation, proposal, and draft screens."""
import pandas as pd
import streamlit as st

from analysis import AnalysisError, analyze_requirements
from catalog import search_catalog
from documents import extract_document
from pricing import calculate_quote
from workflow import invalidate


def go(step):
    st.session_state['nav'] = step


def next_screen(step):
    st.session_state['requested_step'] = step
    st.rerun()


def load_sample(root):
    st.session_state['source_mode'] = 'Paste text'
    st.session_state['requirements_text'] = (root / 'data/sample_rfp.txt').read_text()


def clear_upload():
    st.session_state.pop('uploaded_text', None)
    st.session_state.pop('uploaded_name', None)
    st.session_state['upload_version'] = st.session_state.get('upload_version', 0) + 1


def run_analysis(catalog, api_key, model, clarifications, target, *, provider='openai'):
    # An explicit retry replaces all downstream work; failed calls never leave an approved-looking old result.
    invalidate(st.session_state, 'source')
    try:
        with st.spinner('Reading requirements and matching them to the catalog…' + (' Gemini may take up to two minutes.' if provider == 'gemini' else '')):
            result = analyze_requirements(st.session_state['source_text'], clarifications,
                                          catalog, api_key, model, provider=provider)
        st.session_state['analysis'] = result
        st.session_state['analysis_inputs'] = (st.session_state['source_text'], clarifications)
        st.session_state['analysis_connection'] = f'{provider.title()} · {model}'
        next_screen(target)
    except (AnalysisError, ValueError) as error:
        st.error(str(error))


def render_intake(catalog, api_key, model, root, *, provider='openai'):
    st.title('Start with the customer’s requirements')
    st.write('Upload an RFP or requirements document. QuoteRight will identify the needs, surface gaps, and suggest a solution for your review.')
    with st.container(border=True):
        mode = st.radio('Requirements source', ['Upload document', 'Paste text'], horizontal=True, key='source_mode')
        text = ''
        if mode == 'Upload document':
            uploaded = st.file_uploader('Customer RFP or requirements document', type=['pdf', 'docx', 'txt'],
                key=f"upload_{st.session_state.get('upload_version', 0)}",
                help='Text-based PDF, DOCX or UTF-8 TXT. Up to 5 MB and 40,000 characters; scanned PDFs need OCR.')
            if uploaded is not None:
                try:
                    text = extract_document(uploaded.name, uploaded.getvalue())
                    st.session_state['uploaded_text'] = text
                    st.session_state['uploaded_name'] = uploaded.name
                except ValueError as error:
                    st.session_state.pop('uploaded_text', None)
                    st.session_state.pop('uploaded_name', None)
                    st.error(str(error))
            else:
                text = st.session_state.get('uploaded_text', '')
            name = st.session_state.get('uploaded_name', '')
            if name:
                st.caption(f'Loaded: {name}')
                st.button('Clear document', key='clear_upload', on_click=clear_upload)
        else:
            text = st.text_area('Customer requirements', height=230, key='requirements_text',
                                placeholder='Paste the customer’s requirements here…').strip()
            name = 'Pasted customer requirements' if text else ''
        st.button('Try a synthetic sample RFP', key='load_sample', on_click=load_sample, args=(root,))
        if text != st.session_state.get('source_text', ''):
            invalidate(st.session_state, 'source')
            st.session_state['source_text'] = text
            st.session_state['clarifications'] = ''
        st.session_state['document_name'] = name
        if text:
            with st.expander(f'Preview extracted text · {len(text):,} characters', expanded=True):
                st.code(text, language=None, wrap_lines=True)
        st.caption(f'Analyze sends extracted text, seller clarifications, and catalog descriptions to {provider.title()}. Use synthetic customer data for this prototype.')
        if st.button('Analyze requirements →', type='primary', key='analyze', disabled=not text):
            run_analysis(catalog, api_key, model, st.session_state.get('clarifications', ''), 1, provider=provider)
        if 'analysis' in st.session_state:
            st.button('Continue to understanding →', on_click=go, args=(1,))


def render_understanding(catalog, api_key, model, *, provider='openai'):
    result = st.session_state['analysis']
    st.title('Review what the customer needs')
    if st.session_state.get('analysis_connection'):
        st.caption('Analyzed with ' + st.session_state['analysis_connection'])
    st.write('Check the interpretation against the source. Correct gaps with a clarification before confirming.')
    if result.customer_name:
        st.caption(f'CUSTOMER / {result.customer_name}')
    st.markdown(f'### {result.summary}')
    for req in result.requirements:
        with st.container(border=True):
            st.markdown(f'**{req.requirement_id} · {req.description}**')
            st.caption('MUST HAVE' if req.priority == 'must_have' else 'NICE TO HAVE')
            st.text(f'Source: “{req.source_quote}”')
            st.write(f'Requested seats: {req.quantity}' if req.quantity is not None else 'Requested seats: not specified')
            st.caption(f'Suggested match: {catalog[req.suggested_product_id].name}' if req.suggested_product_id else 'No matching product in the current catalog')
    st.write(f'Requested duration: {result.term_months} months' if result.term_months else 'Requested duration: not specified')
    if result.term_source_quote:
        st.text(f'Duration source: “{result.term_source_quote}”')
    if result.questions:
        st.warning('Clarification needed')
        for question in result.questions:
            st.write(f'• {question}')
    clarifications = st.text_area('Clarifications or corrections', key='clarifications', height=120,
        placeholder='For example: the automation seats are a subset of the 20 employees.')
    stale = (st.session_state['source_text'], clarifications) != st.session_state['analysis_inputs']
    if stale:
        invalidate(st.session_state, 'analysis')
        st.warning('Your clarifications changed. Update the analysis before confirming understanding.')
    if st.button('Update analysis', key='reanalyze', disabled=not stale):
        run_analysis(catalog, api_key, model, clarifications, 1, provider=provider)
    if result.questions and not stale:
        st.checkbox('I have reviewed the open questions and will resolve quote inputs or accept the documented gaps.', key='questions_ack')
    if st.button('Confirm understanding →', type='primary', key='confirm_understanding',
                 disabled=stale or (bool(result.questions) and not st.session_state.get('questions_ack', False))):
        st.session_state['understanding_confirmed'] = True
        next_screen(2)
    st.button('← Back to requirements', key='back_requirements', on_click=go, args=(0,))


def initialize_proposal(result, rules):
    if st.session_state.get('proposal_initialized'):
        return
    products = list(dict.fromkeys(r.suggested_product_id for r in result.requirements if r.suggested_product_id))
    st.session_state['products'] = products
    for pid in products:
        quantities = {r.quantity for r in result.requirements if r.suggested_product_id == pid}
        # Do not sum possibly overlapping seats or guess missing quantities.
        quantity = next(iter(quantities)) if len(quantities) == 1 else None
        st.session_state[f'quantity_{pid}'] = str(quantity) if quantity is not None else ''
    st.session_state['months'] = result.term_months if result.term_months in rules.allowed_months else None
    st.session_state['discount'] = 0.0
    st.session_state['proposal_initialized'] = True


def coverage_gaps(result, selected):
    return [r for r in result.requirements if not r.suggested_product_id or r.suggested_product_id not in selected]


def render_solution(catalog, rules):
    result = st.session_state['analysis']
    initialize_proposal(result, rules)
    st.title('Review the proposed solution')
    st.write('Start with the suggested configuration. Adjust products or quantities where needed; pricing comes from the catalog.')
    with st.expander('Why these products?', expanded=True):
        for req in result.requirements:
            if req.suggested_product_id:
                st.markdown(f'**{req.requirement_id} → {catalog[req.suggested_product_id].name}**')
                st.write(req.rationale)
    with st.expander('Browse the catalog'):
        query = st.text_input('Search products', key='search', placeholder='Search capabilities…')
        matches = search_catalog(catalog, query)
        if matches:
            st.dataframe(pd.DataFrame([{'Product': p.name, 'Description': p.description,
                'USD / seat / month': f'${p.monthly_price:,.2f}'} for p in matches]), hide_index=True, width='stretch')
        else:
            st.info('No matching catalog products.')
    left, right = st.columns([1.2, 1], gap='large')
    with left:
        selected = st.multiselect('Products in the solution', list(catalog), key='products', format_func=lambda pid: catalog[pid].name)
        raw_quantities = {}
        for pid in selected:
            raw_quantities[pid] = st.text_input(f'Seats · {catalog[pid].name}', key=f'quantity_{pid}',
                placeholder='Enter requested seats', help='Positive whole number. Missing or conflicting quantities are never guessed.')
        if result.term_months not in rules.allowed_months and result.term_months is not None:
            st.warning(f'The requested {result.term_months}-month term is not supported. Choose an allowed term explicitly.')
        months = st.selectbox('Quote duration', [None, *rules.allowed_months], key='months',
            format_func=lambda m: 'Choose duration' if m is None else f'{m} month' + ('s' if m != 1 else ''))
        discount = st.number_input('Quote discount (%)', min_value=0.0, max_value=100.0, step=0.5, format='%.2f', key='discount')
        st.caption(f'Discounts strictly above {rules.approval_threshold_percent:g}% require approval. USD · Tax excluded.')
    gaps = coverage_gaps(result, selected)
    gap_ids = tuple(r.requirement_id for r in gaps)
    if gap_ids != st.session_state.get('acknowledged_gap_ids'):
        st.session_state['coverage_ack'] = False
        st.session_state['acknowledged_gap_ids'] = gap_ids
    with right:
        st.markdown('### Requirement coverage')
        for req in result.requirements:
            if req in gaps:
                st.warning(f'{req.requirement_id} · {req.description} — uncovered')
            else:
                st.write(f'✓ {req.requirement_id} · {req.description} — suggested catalog match')
        st.caption('Suggested matches require seller review; a catalog match does not prove full compatibility.')
        if gaps:
            st.checkbox('I acknowledge the uncovered requirements and will keep them visible in this draft.', key='coverage_ack')
    snapshot = (tuple(sorted(raw_quantities.items())), months, str(discount), tuple(selected))
    if 'draft' in st.session_state and st.session_state['draft_inputs'] != snapshot:
        invalidate(st.session_state, 'commercial')
        st.warning('Recalculation required · Your configuration changed. Review and calculate the draft again.')
    if st.button('Calculate draft →', type='primary', key='calculate'):
        try:
            if gaps and not st.session_state.get('coverage_ack', False):
                raise ValueError('Acknowledge the uncovered requirements before creating a draft.')
            quantities = {}
            for pid, raw in raw_quantities.items():
                if not raw.strip().isascii() or not raw.strip().isdigit():
                    raise ValueError(f'Enter a positive whole-number seat quantity for {catalog[pid].name}.')
                quantities[pid] = int(raw.strip())
            quote = calculate_quote(catalog, quantities, months, str(discount), rules)
            st.session_state['draft'] = quote
            st.session_state['draft_inputs'] = snapshot
            next_screen(3)
        except ValueError as error:
            invalidate(st.session_state, 'commercial')
            st.error(str(error))
    st.button('← Back to understanding', key='back_understanding', on_click=go, args=(1,))


def render_quote(catalog, rules):
    quote = st.session_state['draft']
    result = st.session_state['analysis']
    st.title('Your quote, ready for review')
    st.markdown('<span class="draft-tag">DRAFT</span>', unsafe_allow_html=True)
    if result.customer_name:
        st.caption(f'Prepared for {result.customer_name}')
    st.write(result.summary)
    st.caption(f'{quote.lines[0].months}-month duration · USD · Tax excluded')
    if result.term_months is not None and result.term_months != quote.lines[0].months:
        st.warning(f'Term changed by seller: customer requested {result.term_months} months; this draft uses {quote.lines[0].months} months.')
    if quote.approval_required:
        st.warning(f'Approval required · The {quote.discount_percent:g}% discount exceeds the {rules.approval_threshold_percent:g}% limit. This draft has not been approved.')
    else:
        st.info('No discount approval required · This remains a draft for human review.')
    st.dataframe(pd.DataFrame([{'Product': line.product.name, 'Seats': line.quantity,
        'Monthly unit price': f'${line.product.monthly_price:,.2f}', 'Months': line.months,
        'Line total': f'${line.amount:,.2f}'} for line in quote.lines]), hide_index=True, width='stretch')
    subtotal, reduction, total = st.columns(3)
    subtotal.metric('Subtotal', f'${quote.subtotal:,.2f}')
    reduction.metric(f'Discount ({quote.discount_percent:g}%)', f'${quote.discount_amount:,.2f}')
    total.metric('Draft total', f'${quote.total:,.2f}')
    with st.expander('Requirements and remaining gaps', expanded=True):
        gaps = coverage_gaps(result, [line.product.product_id for line in quote.lines])
        for req in result.requirements:
            label = 'Uncovered' if req in gaps else 'Suggested match reviewed by seller'
            st.write(f'{req.requirement_id} · {req.description} — {label}')
        if gaps:
            st.warning('This draft does not cover every customer requirement. Review the documented gaps before any customer-facing use.')
        for question in result.questions:
            st.write(f'Open question: {question}')
    with st.expander('How this price was calculated'):
        st.write('Line total = monthly catalog price × seats × months. Discount = subtotal × discount percentage, rounded once to cents (half up). Total = subtotal − discount.')
        st.write(f'Approval is required for discounts strictly above {rules.approval_threshold_percent:g}%. The model does not calculate prices or grant approvals.')
    st.button('← Revise solution', key='back_solution', on_click=go, args=(2,))
