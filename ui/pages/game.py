from __future__ import annotations
import streamlit as st
from ui.styles import CSS_BASE, CSS_GAME_BG
from ui.components import guess_row_html, digit_input_component
from ui.state import process_user_guess


def game_page() -> None:
    st.markdown(CSS_BASE + CSS_GAME_BG, unsafe_allow_html=True)

    guesses = st.session_state.user_guesses
    history_html = "".join(
        guess_row_html(i + 1, g, f)
        for i, (g, f) in enumerate(guesses)
    )
    if not history_html:
        history_html = (
            '<div style="font-family:\'Caveat\',cursive;font-size:1.3rem;'
            'color:#8a7050;text-align:center;padding:0.8rem 0;font-style:italic;">'
            'No guesses yet — make your first move.</div>'
        )

    st.markdown(
        f'<div class="panel-wrapper">'
        f'<div class="panel">'
        f'<div class="panel-inner">'
        f'<div class="panel-title">YOUR PROCESS</div>'
        f'{history_html}'
        f'<div class="prompt-label">Enter your next 4-digit guess:</div>'
        f'</div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Hidden Streamlit form — kept for server-side processing;
    # the native input and submit button are hidden via CSS.
    with st.form("guess_form", clear_on_submit=True):
        guess_val = st.text_input(
            "guess", placeholder="_ _ _ _", max_chars=4,
            key="digit_input", label_visibility="collapsed",
        )
        submitted = st.form_submit_button("SUBMIT")
        if submitted and guess_val:
            process_user_guess(guess_val)
            st.rerun()

    # Custom 4-digit input grid (non-linear, no per-keystroke reruns)
    digit_input_component()

    if st.session_state.get("input_error"):
        st.markdown(
            f'<div class="err-msg">⚠ {st.session_state.input_error}</div>',
            unsafe_allow_html=True,
        )
