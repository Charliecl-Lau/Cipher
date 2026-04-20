from __future__ import annotations
import streamlit as st
from cipher_engine import (
    ALL_INDICES, FIRST_GUESS,
    generate_secret, get_feedback,
    filter_candidates, best_guess,
)


def init_state() -> None:
    if "page" not in st.session_state:
        st.session_state.page = "landing"


def start_game() -> None:
    st.session_state.secret        = generate_secret()
    st.session_state.user_guesses  = []
    st.session_state.ai_guesses    = []
    st.session_state.ai_candidates = ALL_INDICES.copy()
    st.session_state.ai_next_guess = FIRST_GUESS
    st.session_state.ai_entropy    = 0.0
    st.session_state.input_error   = ""
    st.session_state.page          = "game"
    # Clear post-game caches so they recompute fresh next round
    st.session_state.pop("ai_full_path",        None)
    st.session_state.pop("llm_analysis",        None)
    st.session_state.pop("llm_analysis_error",  None)
    st.session_state.pop("user_path_stats",     None)


def run_ai_step() -> None:
    if (st.session_state.ai_guesses and
            st.session_state.ai_guesses[-1]["feedback"] == (4, 0, 0)):
        return

    secret       = st.session_state.secret
    guess        = st.session_state.ai_next_guess
    cands_before = len(st.session_state.ai_candidates)
    entropy_bits = st.session_state.ai_entropy

    fb        = get_feedback(guess, secret)
    new_cands = filter_candidates(st.session_state.ai_candidates, guess, fb)

    st.session_state.ai_guesses.append({
        "guess": guess, "feedback": fb,
        "cands_before": cands_before, "cands_after": len(new_cands),
        "entropy": entropy_bits,
    })
    st.session_state.ai_candidates = new_cands

    if len(new_cands) > 0:
        ng, ne = best_guess(new_cands)
        st.session_state.ai_next_guess = ng
        st.session_state.ai_entropy    = ne
    else:
        st.session_state.ai_next_guess = guess


def process_user_guess(raw: str) -> bool:
    raw = raw.strip()
    if len(raw) != 4 or not raw.isdigit():
        st.session_state.input_error = "Enter exactly 4 digits (0–9)."
        return False
    if len(set(raw)) != 4:
        st.session_state.input_error = "No repeated digits allowed."
        return False
    guess  = tuple(int(d) for d in raw)
    already = [g for g, _ in st.session_state.user_guesses]
    if guess in already:
        st.session_state.input_error = "Already tried that combination."
        return False

    st.session_state.input_error = ""
    secret = st.session_state.secret
    fb     = get_feedback(guess, secret)
    st.session_state.user_guesses.append((guess, fb))
    run_ai_step()

    if fb == (4, 0, 0):
        st.session_state.page = "reveal"
        return True
    return False
