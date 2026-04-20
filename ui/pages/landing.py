from __future__ import annotations
import streamlit as st
from ui.styles import CSS_BASE, CSS_LANDING_BG
from ui.assets import GREEN_PAINT, YELLOW_PAINT, RED_PAINT
from ui.state import start_game


@st.dialog(" ", width="large")
def show_intro_dialog() -> None:
    """Narrative briefing overlay shown after clicking START GAME."""
    st.markdown(
        f'<div class="dialog-title">MISSION BRIEFING</div>'
        f'</div>'
        f'<div class="dialog-rules-block">'
        f'<p style="font-size:1.8rem;font-family:\'Caveat\',cursive !important;margin:0 0 0.7rem 0;">Guess the <strong>4-digit secret code</strong>. No repeating digits.</p>'
        f'<p style="font-size:1.8rem;font-family:\'Caveat\',cursive !important;color:#3A2810;margin:0 0 0.55rem 0;">After each guess you receive colour feedback:</p>'
        f'<div class="rule-row" style="display:flex;align-items:center;gap:1rem;margin-bottom:0.5rem;"><img src="{GREEN_PAINT}" style="width:80px;height:80px;object-fit:contain;flex-shrink:0;" alt="green">'
        f'<span><strong>Green</strong> — correct digit &amp; correct position</span></div>'
        f'<div class="rule-row" style="display:flex;align-items:center;gap:1rem;margin-bottom:0.5rem;"><img src="{YELLOW_PAINT}" style="width:80px;height:80px;object-fit:contain;flex-shrink:0;" alt="yellow">'
        f'<span><strong>Yellow</strong> — correct digit, wrong position</span></div>'
        f'<div class="rule-row" style="display:flex;align-items:center;gap:1rem;margin-bottom:0.5rem;"><img src="{RED_PAINT}" style="width:80px;height:80px;object-fit:contain;flex-shrink:0;" alt="red">'
        f'<span><strong>Red</strong> — digit not in the code at all</span></div>'
        f'<p style="font-size:1.8rem;font-family:\'Caveat\',cursive !important;color:#5C3A1A;">'
        f'Feedback blocks do <em>not</em> show exact digit positions — only counts. '
        f'No repeated digits.</p>'
        f'</div>'
        f'<div class="dialog-question">'
        f'Can human intuition beat an Information Theory algorithm?'
        f'</div>',
        unsafe_allow_html=True,
    )
    if st.button("Start", key="commence_btn"):
        start_game()
        st.rerun()


def landing_page() -> None:
    st.markdown(CSS_BASE + CSS_LANDING_BG, unsafe_allow_html=True)

    st.markdown('<div class="game-title">Cipher</div>', unsafe_allow_html=True)

    st.markdown('<div id="start-btn-marker"></div>', unsafe_allow_html=True)
    if st.button("START GAME", key="start_btn"):
        show_intro_dialog()
    st.markdown('<div class="landing-btn-gap"></div>', unsafe_allow_html=True)
