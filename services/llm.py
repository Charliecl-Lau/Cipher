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
        payload       = build_llm_payload(user_path_stats, ai_full_path)
        has_struggle  = "struggleMove" in payload
        struggle_note = (
            ""
            if has_struggle
            else " (struggleMove absent — replace Bullet 2 with a second compliment)"
        )

        system_prompt = (
            "[ROLE]\n"
            "You are a sharp, friendly game coach analysing a code-breaking puzzle. "
            "Speak like a person, not a textbook.\n\n"
            "[RULES]\n"
            "- Never use: entropy, minimax, algorithm, search space, heuristic, optimal\n"
            "- Use instead: ruled out, narrowed down, options left, possibilities\n"
            "- Each bullet must be 2–3 sentences (roughly 30–60 words)\n"
            '- Return ONLY a raw JSON object: {"headline": string, "bullets": [string, string, string]}\n'
            "- The very first character of your response must be {\n\n"
            "[DATA]\n"
            f"{json.dumps(payload, indent=2)}\n\n"
            "[TASK]\n"
            f"Write a headline (3–7 words) and exactly 3 bullets{struggle_note}:\n"
            "  Bullet 1 → strongMove highlight\n"
            "  Bullet 2 → struggleMove critique\n"
            "  Bullet 3 → performanceTier-calibrated takeaway:\n"
            "    efficient  → open with a compliment, give one sharpening tip\n"
            "    average    → encouraging but direct, name one habit to build\n"
            "    struggling → honest but kind, name one thing costing them turns"
        )

        from google import genai
        from google.genai import types

        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
        response = client.models.generate_content(
            model="gemma-3-27b-it",
            contents=system_prompt,
            config=types.GenerateContentConfig(max_output_tokens=700),
        )

        raw = response.text.strip()
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw.strip())
        result = json.loads(raw)

        assert isinstance(result["headline"], str) and 3 <= len(result["headline"].split()) <= 7
        assert len(result["bullets"]) == 3
        assert all(len(b.split()) <= 80 for b in result["bullets"])

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
