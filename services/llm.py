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
        logic_flag = payload.get("logicFlag")

        if logic_flag is None:
            bullet2_directive = (
                "    No logical errors detected. Highlight a second strong decision\n"
                "    the player made, with a specific concrete detail."
            )
        else:
            flag_type  = logic_flag["type"]
            digit      = logic_flag["digit_involved"]
            trig       = logic_flag["trigger_guess"]
            wasted     = logic_flag.get("wasted_guesses", [])
            wasted_str = ", ".join(str(g) for g in wasted) if wasted else ""
            plural     = "es" if len(wasted) > 1 else ""

            directives = {
                "unforced_error_green": (
                    f"    The player correctly confirmed digit {digit} as a green peg\n"
                    f"    in an earlier guess, but in Guess {trig} they moved or dropped\n"
                    f"    it, undoing their own progress. State the factual error and\n"
                    f"    consequence. NO PRESCRIPTIVE ADVICE."
                ),
                "missed_proof": (
                    f"    Guess {trig} provided mathematical proof that digit {digit}\n"
                    f"    was not in the code because the total peg count dropped, yet\n"
                    f"    the player reused it in Guess{plural} {wasted_str}.\n"
                    f"    State the factual error and consequence. NO PRESCRIPTIVE ADVICE."
                ),
                "false_negative": (
                    f"    Adding digit {digit} in Guess {trig} caused the peg count to\n"
                    f"    increase, proving it was a correct digit, but the player dropped\n"
                    f"    it immediately after. State the factual error and consequence.\n"
                    f"    NO PRESCRIPTIVE ADVICE."
                ),
                "false_anchor": (
                    f"    The player anchored onto digit {digit} starting around Guess {trig}\n"
                    f"    even though it was never in the code, wasting Guess{plural} {wasted_str}.\n"
                    f"    State the factual error and consequence. NO PRESCRIPTIVE ADVICE."
                ),
                "repeated_slot": (
                    f"    The player already knew digit {digit} was a yellow peg (wrong\n"
                    f"    position), but in Guess {trig} they tested it in that exact same\n"
                    f"    slot again. State the factual error and consequence.\n"
                    f"    NO PRESCRIPTIVE ADVICE."
                ),
                "dropped_yellow": (
                    f"    The player had guaranteed yellow pegs from the previous guess,\n"
                    f"    but in Guess {trig} they didn't carry forward enough digits to\n"
                    f"    account for them. State the factual error and consequence.\n"
                    f"    NO PRESCRIPTIVE ADVICE."
                ),
            }
            bullet2_directive = directives.get(
                flag_type,
                "    Point out the specific logical lapse in the player's guess sequence."
            )

        system_prompt = (
            "You are a sharp, friendly game coach analysing a code-breaking puzzle. "
            "Talk like a coach to a player — direct, specific, human.\n\n"
            "[RULES]\n"
            "- Banned words: entropy, minimax, algorithm, search space, heuristic, optimal\n"
            "- Use instead: ruled out, narrowed down, options left, possibilities\n"
            "- Each bullet: exactly 2–3 sentences, 30–60 words. "
            "Count the words. If a bullet exceeds 60 words, rewrite it before responding.\n"
            "- For Logic Error bullets: state facts and consequences only. "
            "Do NOT add any advice, tips, or 'next time' phrases.\n"
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
            + bullet2_directive + "\n\n"
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
