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
            "  Bullet 2 — The Weak Move:\n"
            + (
                "    Use `struggleMove`. Explain the specific lapse — did it test something already ruled out,\n"
                "    or did it barely narrow the remaining options? Name the wasted potential concretely.\n"
                if has_struggle else
                "    No `struggleMove` this game — the player avoided any clear weak guess.\n"
                "    Highlight a second strong decision the player made, with a specific detail.\n"
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
