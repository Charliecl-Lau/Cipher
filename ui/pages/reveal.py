from __future__ import annotations
import html
import streamlit as st
from cipher_engine import ALL_INDICES, filter_candidates, reveal_secret
from ui.styles import CSS_BASE, CSS_BOOK_BG, CSS_ANALYSIS
from ui.components import guess_row_html
from ui.state import start_game
from services.llm import get_llm_analysis


def precompute_ai_full_game() -> list:
    """
    Return the AI's recorded guess path, caching it in session_state so
    downstream callers always get the same list object within a session.
    """
    if "ai_full_path" in st.session_state:
        return st.session_state.ai_full_path

    st.session_state.ai_full_path = list(st.session_state.ai_guesses)
    return st.session_state.ai_full_path


def precompute_user_path_stats() -> list:
    """
    Replay user_guesses through filter_candidates to compute candidate
    counts before/after each user guess. Mirrors precompute_ai_full_game()
    but follows the user's actual sequence. Cached in session_state.
    """
    if "user_path_stats" in st.session_state:
        return st.session_state.user_path_stats

    user_guesses = st.session_state.user_guesses
    candidates   = ALL_INDICES.copy()
    path: list   = []

    for guess, feedback in user_guesses:
        cands_before = len(candidates)
        candidates   = filter_candidates(candidates, guess, feedback)
        path.append({
            "guess":        guess,
            "feedback":     feedback,
            "cands_before": cands_before,
            "cands_after":  len(candidates),
        })

    st.session_state.user_path_stats = path
    return path


def reveal_page() -> None:
    st.markdown(CSS_BASE + CSS_BOOK_BG + CSS_ANALYSIS, unsafe_allow_html=True)
    reveal_secret(st.session_state.secret)


    # ── Pre-compute paths (cached after first run) ────────────────────────────
    precompute_ai_full_game()       # warms session_state["ai_full_path"]
    precompute_user_path_stats()    # warms session_state["user_path_stats"]
    ai_full_path = st.session_state.ai_full_path
    user_guesses = st.session_state.user_guesses
    n_user       = len(user_guesses)
    n_ai         = len(ai_full_path)

    # ── Win / loss ────────────────────────────────────────────────────────────
    user_won    = n_user <= n_ai
    outcome_cls = "win"  if user_won else "lose"
    outcome_txt = "You Win!" if user_won else "The AI Wins."
    outcome_sub = f"You: {n_user} guesses · AI: {n_ai} guesses"

    col_left, col_right = st.columns(2)

    # ── LEFT COLUMN — toggle + guess list ────────────────────────────────────
    with col_left:
        st.markdown(
            f'<div class="win-loss-banner {outcome_cls} fade-in">'
            f'{outcome_txt}<br>'
            f'<span style="font-size:1.25rem;font-weight:500;">{outcome_sub}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        view = st.radio(
            "View",
            options=["Your Path", "Perfect Path"],
            horizontal=True,
            key="path_toggle",
            label_visibility="collapsed",
        )

        if view == "Your Path":
            title     = f"YOUR PATH — {n_user} {'GUESS' if n_user == 1 else 'GUESSES'}"
            rows_html = "".join(
                guess_row_html(i + 1, g, f, solved=(f == (4, 0, 0)))
                for i, (g, f) in enumerate(user_guesses)
            )
        else:
            title     = f"PERFECT PATH — {n_ai} {'GUESS' if n_ai == 1 else 'GUESSES'}"
            rows_html = "".join(
                guess_row_html(
                    i + 1,
                    e["guess"],
                    e["feedback"],
                    solved=(e["feedback"] == (4, 0, 0)),
                )
                for i, e in enumerate(ai_full_path)
            )

        active_count = n_user if view == "Your Path" else n_ai
        st.markdown(
            f'<div class="page-title fade-in">{title}</div>'
            f'<div class="guess-scroll-container fade-in">{rows_html}</div>',
            unsafe_allow_html=True,
        )
        if active_count > 5:
            st.markdown(
                '<div style="font-family:\'Caveat\',cursive;font-size:1.1rem;'
                'color:rgba(0,0,0,0.5);text-align:center;margin-top:0.2rem;">'
                '(scroll to see more) ↓</div>',
                unsafe_allow_html=True,
            )

        st.markdown('<div class="play-again-area"></div>', unsafe_allow_html=True)
        if st.button("PLAY AGAIN", key="play_again"):
            start_game()
            st.rerun()

    # ── RIGHT COLUMN — LLM coach analysis ────────────────────────────────────
    with col_right:
        if "llm_analysis" not in st.session_state:
            with st.spinner("Analysing your gameplay..."):
                get_llm_analysis()

        analysis    = st.session_state.get("llm_analysis", {})
        headline    = html.escape(analysis.get("headline", ""))
        bullets     = [html.escape(b) for b in analysis.get("bullets", [])]
        bullet_html = "".join(
            f'<div class="analysis-bullet fade-in">{i + 1}. {b}</div>'
            for i, b in enumerate(bullets)
        )
        analysis_html = (
            f'<div class="analysis-headline fade-in">{headline}</div>'
            f'{bullet_html}'
            if (headline or bullets) else ""
        )
        st.markdown(
            f'<div class="page-right-content fade-in">'
            f'<div class="page-title">COACH\'S NOTES</div>'
            f'{analysis_html}'
            f'</div>',
            unsafe_allow_html=True,
        )
        err = st.session_state.get("llm_analysis_error", "")
        if err:
            st.error(err)
