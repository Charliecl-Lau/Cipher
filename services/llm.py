from __future__ import annotations
import re
import json
import streamlit as st
from cipher_engine import build_llm_payload


def get_llm_analysis() -> dict:
    """
    Call the Gemini API (gemma-3-27b-it) to analyse the user's gameplay.
    Returns a dict with 'headline' and 'bullets' keys on success, or a
    plain fallback template on any error. Result cached in session_state.
    """
    if "llm_analysis" in st.session_state:
        return st.session_state.llm_analysis

    user_path_stats = st.session_state.user_path_stats
    ai_full_path    = st.session_state.ai_full_path

    try:
        payload = build_llm_payload(
            user_path_stats, ai_full_path,
            user_guesses=st.session_state.user_guesses,
            secret=st.session_state.secret,
        )
        has_flag = payload.get("logicFlag") is not None

        system_prompt = (
            "You are a sharp, friendly game coach analysing a code-breaking puzzle. "
            "Talk like a coach to a player — direct, specific, human.\n\n"
            "[RULES]\n"
            "- Banned words: entropy, minimax, algorithm, search space, heuristic, optimal\n"
            "- Use instead: ruled out, narrowed down, options left, possibilities\n"
            "- Each bullet: exactly 2–3 sentences, 30–60 words. "
            "Count the words. If a bullet exceeds 60 words, rewrite it before responding.\n"
            "- Do NOT include the bullet label (e.g. 'The Best Move:') inside the string value.\n"
            '- Return ONLY a raw JSON object — no markdown fences, no extra keys:\n'
            '  {"headline": string, "bullets": [string, string, string]}\n'
            "- The very first character of your response must be {\n\n"
            "[DATA]\n"
            f"{json.dumps(payload, indent=2)}\n\n"
            "[TASK]\n"
            "Write a headline (3–7 words) and exactly 3 bullets:\n\n"
            "  Bullet 1 — The Best Move:\n"
            "    Use `strongMove`. State exactly how many possibilities it ruled out\n"
            "    and why that guess was the turning point.\n\n"
            "  Bullet 2 — The Logic Check:\n"
            + (
                "    `logicFlag` is present. Use ONLY the directive below for its type.\n"
                "    State the factual error and its consequence. NO prescriptive advice\n"
                "    (no 'Next time...' or 'Always...'). Tone: analytical, direct, factual.\n\n"
                "    - unforced_error_green: Tell the player they locked in {digit_involved}\n"
                "      correctly, but undid that progress by moving or dropping it in Guess {trigger_guess}.\n"
                "    - missed_proof: Point out Guess {trigger_guess} proved {digit_involved} wasn't\n"
                "      in the code (total pegs dropped), yet they reused it in Guesses {wasted_guesses}.\n"
                "    - false_negative: Highlight that adding {digit_involved} in Guess {trigger_guess}\n"
                "      raised peg count — proving it correct — but they dropped it in the very next guess.\n"
                "    - false_anchor: Explain they anchored on dead digit {digit_involved} starting\n"
                "      Guess {trigger_guess}, misreading clues and wasting Guesses {wasted_guesses}.\n"
                "    - repeated_slot: Note that {digit_involved} was a known yellow (wrong spot),\n"
                "      but they wasted Guess {trigger_guess} testing it in that exact slot again.\n"
                "    - dropped_yellow: Point out that in Guess {trigger_guess} they didn't carry\n"
                "      enough digits to account for guaranteed yellows on the board.\n"
                if has_flag else
                "    `logicFlag` is null — the player made no logical errors.\n"
                "    Highlight a second strong decision with a specific detail.\n"
            )
            + "\n"
            "  Bullet 3 — Takeaway (use `performanceTier` from the data to pick one branch):\n"
            "    efficient  → open with a compliment, then give one concrete tip for cross-referencing\n"
            "                  clues to eliminate the last few options without guessing blindly\n"
            "    average    → encouraging but direct; name one specific habit that would cut a guess off\n"
            "    struggling → honest but kind; name the one thing costing them the most turns"
        )

        from google import genai
        from google.genai import types

        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
        response = client.models.generate_content(
            model="gemma-3-27b-it",
            contents=system_prompt,
            config=types.GenerateContentConfig(max_output_tokens=950),
        )

        raw = response.text.strip()
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw.strip())
        result = json.loads(raw)

        assert isinstance(result["headline"], str) and 3 <= len(result["headline"].split()) <= 7
        assert len(result["bullets"]) == 3
        assert all(len(b.split()) <= 65 for b in result["bullets"])

        st.session_state.llm_analysis = result
        return result

    except Exception as e:
        st.session_state.llm_analysis_error = f"{type(e).__name__}: {e}"
        fallback: dict = {
            "headline": "Analysis unavailable",
            "bullets": [
                f"You solved it in {len(user_path_stats)} guesses.",
                f"The perfect path was {len(ai_full_path)} guesses.",
                "Try again to see a detailed breakdown.",
            ],
        }
        st.session_state.llm_analysis = fallback
        return fallback
