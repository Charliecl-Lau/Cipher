from __future__ import annotations
import re
import json
import streamlit as st
from cipher_engine import build_llm_payload


# ── Prompt template ─────────────────────────────────────────────────────────

_BASE_TEMPLATE = """\
You are a sharp, friendly Mastermind coach. Speak directly and specifically to the player like an encouraging but honest coach reviewing their game.

Rules:
- Use simple, natural language. Never use: entropy, minimax, algorithm, search space, heuristic, optimal.
- Each bullet: 2–3 short sentences, about 30–60 words.
{yellow_peg_rule}- The very first character of your response must be {{.
- Return ONLY a raw JSON object — no markdown fences, no extra keys.
- Count the words in each bullet. If any bullet exceeds 60 words, rewrite it before responding.
- Return ONLY valid JSON: {{"headline": "3-7 word headline", "bullets": ["...", "..."]}}

Game Data:
{full_payload_json}

Task:
Write a short balanced headline (3–7 words) that matches the overall performance.
"""


def build_directives(payload: dict) -> tuple[int, str, str, str | None]:
    """
    Build bullet directives from the LLM payload.

    Returns a tuple:
        (bullet_count, bullet1_directive, bullet2_directive, bullet3_directive_or_None)

    bullet_count is 2 or 3. bullet3_directive_or_None is None when bullet_count is 2.
    """
    good_flag      = payload.get("goodLogicFlag")
    logic_flag     = payload.get("logicFlag")
    yellow         = payload.get("yellowAnalysis")  # dict or None

    step_diff = payload.get("userStepCount", 0) - payload.get("perfectStepCount", 0)

    # Derived yellow fields (safe defaults)
    missed_carry       = yellow.get("missedCarryForward", False)     if yellow else False
    repeated_testing   = yellow.get("repeatedYellowTesting", False)  if yellow else False
    total_yellow       = yellow.get("totalYellowFeedback", 0)        if yellow else 0
    early_yellow_list  = yellow.get("earlyYellowGuesses", [])        if yellow else []
    yellow_summary     = yellow.get("summary", "")                   if yellow else ""

    early_yellow_str = (
        ", ".join(str(g) for g in early_yellow_list) if early_yellow_list else "early guesses"
    )

    # ── How many bullets? ────────────────────────────────────────────────────
    use_three_bullets = (
        yellow is not None
        and (missed_carry or repeated_testing or total_yellow >= 3)
    )
    bullet_count = 3 if use_three_bullets else 2

    # ── Bullet 1 — Smart Play ────────────────────────────────────────────────
    if good_flag is not None:
        gf_type  = good_flag["type"]
        gf_digit = good_flag["digit_involved"]
        gf_trig  = good_flag["trigger_guess"]
        good_directives = {
            "smart_isolation": (
                f"    In Guess {gf_trig} the player isolated digit {gf_digit} alongside\n"
                f"    completely untested digits to confirm its status. Praise this\n"
                f"    deduction specifically. NO PRESCRIPTIVE ADVICE."
            ),
            "efficient_pivot": (
                f"    In Guess {gf_trig} the player immediately dropped digit {gf_digit}\n"
                f"    after the peg count fell — mathematical proof it was wrong. Praise\n"
                f"    this instant pivot specifically. NO PRESCRIPTIVE ADVICE."
            ),
            "perfect_lock": (
                f"    The player found a green peg for digit {gf_digit} in Guess {gf_trig}\n"
                f"    and never moved it for the rest of the game. Praise this discipline\n"
                f"    specifically. NO PRESCRIPTIVE ADVICE."
            ),
        }
        bullet1_directive = good_directives.get(
            gf_type,
            "    Praise a specific smart decision the player made."
        )
    elif yellow is not None and not missed_carry and total_yellow > 0:
        # Good yellow handling — player kept all yellow-confirmed digits
        bullet1_directive = (
            "    The player received yellow feedback but kept all yellow-confirmed digits\n"
            "    in subsequent guesses. Praise this consistent carry-forward specifically."
        )
    else:
        bullet1_directive = (
            "    No standout positive play detected. Briefly acknowledge they completed\n"
            "    the puzzle and highlight one moment where their process was solid."
        )

    # ── Bullet 2 — Logic or Yellow Insight ──────────────────────────────────
    yellow_flag_types = {"dropped_yellow", "repeated_slot"}

    if logic_flag is not None:
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

        # Strengthen yellow-related flags with yellowAnalysis.summary
        if flag_type in yellow_flag_types and yellow is not None:
            if missed_carry or repeated_testing:
                bullet2_directive += f"\n    Context from game data: {yellow_summary}"

    elif yellow is not None and missed_carry:
        # No logicFlag but yellow carry-forward was missed — use yellow pitfall directive
        bullet2_directive = (
            f"    Describe how changing digits after early yellow feedback in guesses "
            f"{early_yellow_str} made it harder to identify the correct set of digits. "
            f"Context: {yellow_summary}. Use a gentle, explanatory tone."
        )
    else:
        bullet2_directive = (
            "    No logical errors detected. Highlight a second strong decision\n"
            "    the player made, with a specific concrete detail."
        )

    # ── Bullet 3 (optional) ──────────────────────────────────────────────────
    if use_three_bullets:
        user_steps    = payload.get("userStepCount", "?")
        perfect_steps = payload.get("perfectStepCount", "?")

        if missed_carry:
            yellow_ref = f"in guess {early_yellow_str}" if early_yellow_list else "early in the game"
            if step_diff > 0:
                cost_note = f"They used {step_diff} more guess(es) than the perfect path."
            else:
                cost_note = "Keep it positive — they still solved it."
            bullet3_directive = (
                f"    Overall efficiency note: the yellow feedback {yellow_ref} "
                f"added some extra testing. {cost_note} Keep the tone gentle and encouraging."
            )
        elif repeated_testing:
            bullet3_directive = (
                "    Note that the player re-tested a yellow digit in the same slot it was "
                "already proven wrong. Explain the consequence briefly."
            )
        else:
            # totalYellowFeedback >= 3 but no major issues
            bullet3_directive = (
                f"    Provide an overall efficiency note comparing their {user_steps} steps "
                f"to the perfect {perfect_steps}. Be encouraging."
            )
    else:
        bullet3_directive = None

    return (bullet_count, bullet1_directive, bullet2_directive, bullet3_directive)


# ── Main public function ─────────────────────────────────────────────────────

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

        bullet_count, bullet1_directive, bullet2_directive, bullet3_directive = (
            build_directives(payload)
        )

        # Build the dynamic task section
        task_lines = [
            f"Write exactly {bullet_count} bullets:\n",
            "  Bullet 1 — Smart Play:",
            bullet1_directive,
            "",
            "  Bullet 2 — Logic or Yellow Insight:",
            bullet2_directive,
        ]
        if bullet3_directive is not None:
            task_lines += [
                "",
                "  Bullet 3 — Overall Efficiency:",
                bullet3_directive,
            ]

        task_section = "\n".join(task_lines)

        yellow_peg_rule = (
            "- Be accurate about yellow pegs: A yellow peg means one of the digits is in the"
            " code but in the wrong position. In the first 1–2 guesses, it does not confirm"
            " which specific digit is correct.\n"
            if payload.get("yellowAnalysis") is not None
            else ""
        )
        system_prompt = (
            _BASE_TEMPLATE.format(
                full_payload_json=json.dumps(payload, indent=2),
                yellow_peg_rule=yellow_peg_rule,
            )
            + task_section
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
        assert len(result["bullets"]) in (2, 3)
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
            ],
        }
        st.session_state.llm_analysis = fallback
        return fallback
