"""
Cipher — Streamlit front-end (open ledger visual)
"""
import re
import base64
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from cipher_engine import (
    ALL_INDICES, FIRST_GUESS,
    generate_secret, get_feedback,
    filter_candidates, best_guess, explain_step,
    build_llm_payload,
)

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Cipher",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Texture & paint assets ─────────────────────────────────────────────────────
def _b64(filename: str, mime: str = "image/png") -> str:
    with open(Path(__file__).parent / "image" / filename, "rb") as _f:
        return f"data:{mime};base64,{base64.b64encode(_f.read()).decode()}"

TEXTURE        = _b64("image_7.jpg",   "image/jpeg")
WRINKLED_PAPER = _b64("image_10.jpg",  "image/jpeg")
GREEN_PAINT    = _b64("green_paint.png")
YELLOW_PAINT   = _b64("yellow_paint.png")
RED_PAINT      = _b64("red_paint.png")

# ── CSS ────────────────────────────────────────────────────────────────────────

# Shared styles — injected on every page
CSS_BASE = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Caveat:wght@400;500;600;700&display=swap');

*, *::before, *::after {{ box-sizing: border-box; }}

html, body,
[data-testid="stAppViewContainer"],
[data-testid="stMain"] {{
    font-family: 'Caveat', cursive;
    color: #1A0E08;
}}

/* ─── Hide Streamlit chrome ─── */
#MainMenu, footer,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
[data-testid="stHeader"],
.stDeployButton {{ display: none !important; visibility: hidden !important; }}

/* ─── All page buttons (START GAME / INSTRUCTIONS / CLOSE / PLAY AGAIN) ─── */
div[data-testid="stButton"] > button {{
    font-family: 'Caveat', cursive !important;
    font-size: 2.1rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.08em !important;
    background: transparent !important;
    color: #1A0E08 !important;
    border: 2.5px solid #1A0E08 !important;
    padding: 0.6rem 3rem !important;
    border-radius: 0 !important;
    box-shadow: none !important;
    cursor: pointer !important;
    transition: background 0.08s ease, color 0.08s ease !important;
    display: block !important;
    margin: 0 auto !important;
}}

div[data-testid="stButton"] > button:hover,
div[data-testid="stButton"] > button:focus {{
    background: #1A0E08 !important;
    color: #F5ECCC !important;
    outline: none !important;
    box-shadow: none !important;
}}

/* ─── Panel title ─── */
.panel-title {{
    font-family: 'Caveat', cursive;
    font-size: 2.4rem;
    font-weight: 700;
    text-align: center;
    color: #1A0E08;
    border-bottom: 1.5px solid rgba(75,50,18,0.40);
    padding-bottom: 0.55rem;
    margin-bottom: 0.85rem;
    letter-spacing: 0.04em;
}}

/* ─── Guess rows ─── */
.guess-row {{
    display: flex;
    align-items: center;
    gap: 0.45rem;
    padding: 0.28rem 0;
    border-bottom: 1px solid rgba(75,50,18,0.12);
    font-family: 'Caveat', cursive;
}}

.guess-row:last-child {{ border-bottom: none; }}

.guess-num {{
    font-size: 1rem;
    font-weight: 600;
    color: #1A0E08;
    min-width: 1.5rem;
}}

.guess-digits {{
    font-size: 2.2rem;
    font-weight: 700;
    color: #1A0E08;
    flex: 1;
    text-decoration: underline;
    text-underline-offset: 2px;
    text-decoration-thickness: 1.5px;
}}

.solved-label {{
    font-size: 0.9rem;
    color: #1A0E08;
    font-style: italic;
    margin-right: 0.2rem;
}}

.guess-blocks {{
    display: flex;
    gap: 4px;
    flex-shrink: 0;
}}

/* ─── Hand-painted feedback images — scaled +20% (32 → 38px) ─── */
.feedback-img {{
    width: 38px;
    height: 38px;
    object-fit: contain;
    display: inline-block;
    vertical-align: middle;
    flex-shrink: 0;
    border-radius: 3px 4px 2px 4px;
}}

/* ─── Prompt / input area ─── */
.prompt-label {{
    font-family: 'Caveat', cursive;
    font-size: 1.9rem;
    color: #1A0E08;
    margin-top: 0.9rem;
    padding-top: 0.75rem;
    border-top: 1.5px solid rgba(75,50,18,0.30);
}}

/* ─── Input form — strip all backgrounds ─── */
.stForm,
[data-testid="stForm"],
[data-testid="stForm"] > div {{
    background: transparent !important;
    background-color: transparent !important;
    background-image: none !important;
    border: none !important;
    padding: 0 !important;
    box-shadow: none !important;
}}

[data-testid="stTextInput"] * {{
    background: transparent !important;
    background-color: transparent !important;
    background-image: none !important;
    border: none !important;
    border-radius: 0 !important;
    box-shadow: none !important;
    outline: none !important;
}}

[data-testid="stTextInput"] input {{
    border-bottom: 2.5px solid #2A1B0A !important;
    font-family: 'Caveat', cursive !important;
    font-size: 3.2rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.72em !important;
    color: #2A1B0A !important;
    text-align: center !important;
    padding: 0.1rem 0.5rem !important;
    max-width: 300px !important;
    display: block !important;
    margin: 0 auto !important;
}}

[data-testid="stTextInput"] input:focus {{
    border-bottom-color: #10B981 !important;
}}

[data-testid="stTextInput"] input::placeholder {{
    color: #8A7050 !important;
    letter-spacing: 0.55em !important;
    font-weight: 400 !important;
}}

/* ─── Input helper text — color fix + inline positioning ─── */
[data-testid="stTextInput"] {{
    display: flex !important;
    flex-direction: row !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 1rem !important;
    flex-wrap: wrap !important;
}}

[data-testid="InputInstructions"] {{
    color: #2A1B0A !important;
    font-family: 'Caveat', cursive !important;
    font-size: 1rem !important;
    white-space: nowrap !important;
    margin: 0 0 0 50px !important;
    padding: 0 !important;
    flex-shrink: 0 !important;
    order: 2 !important;
}}

[data-testid="stTextInput"] > div:not([data-testid]) {{
    flex: 0 0 auto !important;
    order: 1 !important;
}}

[data-testid="stTextInput"] small {{
    color: #2A1B0A !important;
    font-family: 'Caveat', cursive !important;
}}

/* ─── SUBMIT button ─── */
[data-testid="stFormSubmitButton"] {{
    display: flex !important;
    justify-content: center !important;
}}
[data-testid="stFormSubmitButton"] > button {{
    font-family: 'Caveat', cursive !important;
    font-size: 1.9rem !important;
    font-weight: 600 !important;
    background: transparent !important;
    color: #1A0E08 !important;
    border: 2px solid rgba(75,50,18,0.55) !important;
    padding: 0.3rem 2rem !important;
    border-radius: 0 !important;
    box-shadow: none !important;
    cursor: pointer !important;
    margin-top: 0.6rem !important;
    letter-spacing: 0.06em !important;
}}

[data-testid="stFormSubmitButton"] > button:hover,
[data-testid="stFormSubmitButton"] > button:focus {{
    background: rgba(75,50,18,0.08) !important;
    outline: none !important;
    box-shadow: none !important;
}}

/* ─── Error message ─── */
.err-msg {{
    font-family: 'Caveat', cursive;
    font-size: 1.05rem;
    color: #962828;
    margin-top: 0.25rem;
    text-align: center;
}}

/* ─── Analysis page ─── */
.page-title {{
    font-family: 'Caveat', cursive;
    font-size: 1.3rem;
    font-weight: 700;
    text-align: center;
    color: #1A0E08;
    border-bottom: 2px solid #1A0E08;
    padding-bottom: 0.45rem;
    margin-bottom: 1.2rem;
    letter-spacing: 0.04em;
}}

.score-banner {{
    font-family: 'Caveat', cursive;
    font-size: 2rem;
    font-weight: 700;
    color: #1A0E08;
    text-align: center;
    margin-bottom: 1.1rem;
    line-height: 1.3;
}}

.ai-row {{
    display: flex;
    align-items: baseline;
    gap: 0.45rem;
    margin-bottom: 0.65rem;
}}

.ai-row-num {{
    font-family: 'Caveat', cursive;
    font-size: 1.1rem;
    font-weight: 700;
    color: #1A0E08;
    min-width: 1.6rem;
}}

.ai-row-digits {{
    font-family: 'Caveat', cursive;
    font-size: 1.75rem;
    font-weight: 700;
    color: #1A0E08;
    text-decoration: underline;
    text-underline-offset: 2px;
    text-decoration-thickness: 1.5px;
    flex: 1;
}}

.ai-solved-txt {{
    font-family: 'Caveat', cursive;
    font-size: 0.9rem;
    color: #1A0E08;
    font-style: italic;
    margin-left: 0.15rem;
}}

.explain-entry {{
    font-family: 'Caveat', cursive;
    font-size: 1.2rem;
    color: #1A0E08;
    line-height: 1.5;
    margin-bottom: 0.6rem;
    padding-bottom: 0.45rem;
    border-bottom: 1px solid rgba(75,50,18,0.13);
}}

.explain-entry:last-child {{ border-bottom: none; margin-bottom: 0; }}
.explain-entry b {{ font-weight: 700; }}

.play-again-area {{ margin-top: 1.1rem; }}

/* ─── Fade-in animation ─── */
@keyframes fadeUp {{
    from {{ opacity: 0; transform: translateY(8px); }}
    to   {{ opacity: 1; transform: translateY(0); }}
}}

.fade-in {{ animation: fadeUp 0.65s ease; }}

[data-testid="stVerticalBlock"] > [data-testid="stVerticalBlockBorderWrapper"]:empty {{ display: none; }}

/* ─── Narrative intro dialog ─── */
[data-testid="stModal"],
[data-testid="stDialog"] {{
    font-family: 'Caveat', cursive !important;
}}

/* Dialog backdrop tint */
[data-testid="stModal"]::before,
div[data-testid="stModal"] > div:first-child {{
    background: rgba(20, 10, 4, 0.82) !important;
}}

/* Dialog content box — parchment texture */
[data-testid="stModal"] > div > div,
[data-testid="stDialogContent"],
div[role="dialog"] {{
    background-image:
        linear-gradient(rgba(80,55,20,0.11) 1px, transparent 1px),
        linear-gradient(90deg, rgba(80,55,20,0.11) 1px, transparent 1px),
        url('{TEXTURE}') !important;
    background-size: 26px 26px, 26px 26px, cover !important;
    background-color: #EDE0B0 !important;
    border: 1.5px solid rgba(75,50,18,0.55) !important;
    border-radius: 2px !important;
    color: #1A0E08 !important;
    font-family: 'Caveat', cursive !important;
}}

.dialog-title {{
    font-family: 'Caveat', cursive !important;
    font-size: 2.2rem;
    font-weight: 700;
    color: #1A0E08;
    text-align: center;
    border-bottom: 2px solid rgba(75,50,18,0.55);
    padding-bottom: 0.6rem;
    margin-bottom: 1.2rem;
    letter-spacing: 0.06em;
}}

.dialog-lore {{
    font-family: 'Caveat', cursive !important;
    font-size: 1.8rem !important;
    color: #1A0E08;
    line-height: 1.65;
    margin-bottom: 1rem;
    text-align: center;
}}

.dialog-rules-block {{
    font-family: 'Caveat', cursive !important;
    font-size: 1.5rem !important;
    color: #1A0E08;
    line-height: 1.5;
    margin-bottom: 0.5rem;
}}

.dialog-question {{
    font-family: 'Caveat', cursive !important;
    font-size: 1.8rem !important;
    font-weight: 700;
    color: #1A0E08;
    text-align: center;
    margin-top: 1.2rem;
    margin-bottom: 1rem;
    padding-top: 1rem;
    border-top: 1px dashed rgba(75,50,18,0.35);
}}

/* ─── Win / Loss declaration banner ─── */
.win-loss-banner {{
    font-family: 'Caveat', cursive;
    font-size: 2.6rem;
    font-weight: 700;
    text-align: center;
    padding: 0.6rem 1rem;
    margin-bottom: 1.1rem;
    border: 2.5px solid #1A0E08;
    letter-spacing: 0.06em;
    line-height: 1.2;
}}

.win-loss-banner.win {{
    color: #1A5C2E;
    border-color: #1A5C2E;
    background: rgba(26, 92, 46, 0.08);
}}

.win-loss-banner.lose {{
    color: #7A1A1A;
    border-color: #7A1A1A;
    background: rgba(122, 26, 26, 0.08);
}}
</style>
"""

# ── Open-book/ledger background — result page ─────────────────────────────────
CSS_BOOK_BG = f"""
<style>
html, body,
[data-testid="stAppViewContainer"],
[data-testid="stMain"] {{
    background: #5A3A22 !important;
}}

/* ─── Open ledger container ─── */
[data-testid="stMainBlockContainer"] {{
    max-width: 1200px !important;
    width: 95vw !important;
    margin: 2rem auto !important;
    padding: 0 !important;
    background-image:
        linear-gradient(rgba(80,55,20,0.11) 1px, transparent 1px),
        linear-gradient(90deg, rgba(80,55,20,0.11) 1px, transparent 1px),
        url('{TEXTURE}');
    background-size: 26px 26px, 26px 26px, cover;
    background-position: top left, top left, center;
    background-color: #EDE0B0;
    box-shadow:
        0 28px 65px rgba(0,0,0,0.60),
        0 8px 20px rgba(0,0,0,0.35),
        inset 0 0 0 1px rgba(60,40,15,0.25);
    position: relative;
    min-height: 660px;
}}

/* Central spine overlay */
[data-testid="stMainBlockContainer"]::after {{
    content: '';
    position: absolute;
    top: 0;
    left: calc(50% - 12px);
    width: 24px;
    height: 100%;
    background: linear-gradient(
        to right,
        transparent 0%,
        rgba(40,25,8,0.22) 30%,
        rgba(40,25,8,0.35) 50%,
        rgba(40,25,8,0.22) 70%,
        transparent 100%
    );
    pointer-events: none;
    z-index: 50;
}}

/* ─── Column handling ─── */
[data-testid="stHorizontalBlock"] {{
    gap: 0 !important;
    padding: 0 !important;
    align-items: stretch !important;
}}

[data-testid="stColumn"] {{
    padding: 0 !important;
    background: transparent !important;
}}

[data-testid="stColumn"] > div:first-child {{
    background: transparent !important;
    padding: 0 !important;
    min-height: 620px;
}}

[data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child > div:first-child {{
    box-shadow: inset -10px 0 25px rgba(0,0,0,0.10);
}}

[data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:last-child > div:first-child {{
    box-shadow: inset 10px 0 25px rgba(0,0,0,0.07);
}}

.page-left-content {{
    padding: 2.5rem 2.2rem 2rem;
    min-height: 620px;
    position: relative;
}}

.page-right-content {{
    padding: 2.5rem 2.2rem 2rem;
    min-height: 620px;
    position: relative;
}}

/* ─── Landing page wrapper ─── */
.landing-wrap {{
    display: flex;
    align-items: center;
    justify-content: center;
    flex-direction: column;
    width: 100%;
    min-height: 600px;
    padding: 0 1rem;
    gap: 0;
}}

/* ─── Game title on landing page ─── */
.game-title {{
    font-family: 'Caveat', cursive;
    font-size: 4.5rem;
    font-weight: 700;
    color: #2A1B0A;
    text-align: center;
    letter-spacing: 0.02em;
    line-height: 1.05;
    margin: 0 0 1.4rem 0;
    padding: 0;
}}

/* Spacing between the two landing buttons */
.landing-btn-gap {{
    height: 0.85rem;
}}

/* ─── Landing page: dead-center the tirules to the landing column only */
[data-testid="stVerticalBlock"]:htle+button stack ─── */
/* :has(.landing-btn-gap) scopes these as(.landing-btn-gap) {{
    display: flex !important;
    flex-direction: column !important;
    justify-content: center !important;
    align-items: center !important;
    min-height: 560px;
}}

[data-testid="stVerticalBlock"]:has(.landing-btn-gap) > * {{
    width: 100%;
}}

/* ─── Landing START GAME button: light cream fill ─── */
[data-testid="stMarkdown"]:has(#start-btn-marker) ~ [data-testid="stButton"] > button {{
    background:    rgba(246, 239, 215, 0.92) !important;
    border:        1.5px solid rgba(42, 27, 10, 0.55) !important;
    color:         #2A1B0A !important;
    font-family:   'Caveat', cursive !important;
    font-size:     1.0rem !important;
    font-weight:   500 !important;
    letter-spacing: 0.22em !important;
    padding:       0.52rem 2.4rem !important;
    box-shadow:    0 1px 3px rgba(0,0,0,0.07) !important;
    text-transform: uppercase !important;
    border-radius: 0 !important;
    transition:    background 0.08s ease !important;
}}
[data-testid="stMarkdown"]:has(#start-btn-marker) ~ [data-testid="stButton"] > button:hover,
[data-testid="stMarkdown"]:has(#start-btn-marker) ~ [data-testid="stButton"] > button:focus {{
    background: rgba(230, 222, 196, 0.98) !important;
    color:      #1A0E08 !important;
    outline:    none !important;
}}

/* ─── Landing INSTRUCTIONS button: darker recessed ─── */
[data-testid="stMarkdown"]:has(#instr-btn-marker) ~ [data-testid="stButton"] > button {{
    background:    rgba(148, 120, 72, 0.36) !important;
    border:        1.5px solid rgba(42, 27, 10, 0.42) !important;
    color:         #2A1B0A !important;
    font-family:   'Caveat', cursive !important;
    font-size:     1.0rem !important;
    font-weight:   500 !important;
    letter-spacing: 0.22em !important;
    padding:       0.52rem 2.4rem !important;
    box-shadow:    inset 0 1px 4px rgba(0,0,0,0.14), 0 1px 2px rgba(0,0,0,0.06) !important;
    text-transform: uppercase !important;
    border-radius: 0 !important;
    transition:    background 0.08s ease !important;
}}
[data-testid="stMarkdown"]:has(#instr-btn-marker) ~ [data-testid="stButton"] > button:hover,
[data-testid="stMarkdown"]:has(#instr-btn-marker) ~ [data-testid="stButton"] > button:focus {{
    background: rgba(148, 120, 72, 0.58) !important;
    color:      #1A0E08 !important;
    outline:    none !important;
}}

/* ─── Instructions index card ─── */
.index-card {{
    background: #f7f2e0;
    border: 1.5px solid rgba(75,50,18,0.45);
    border-top: 5px solid rgba(75,50,18,0.58);
    border-radius: 2px;
    box-shadow:
        3px 7px 22px rgba(0,0,0,0.32),
        0 1px 4px rgba(0,0,0,0.14);
    padding: 1.8rem 2.2rem 1.6rem;
    margin-bottom: 1.1rem;
}}

.index-card-title {{
    font-family: 'Caveat', cursive;
    font-size: 2.1rem;
    font-weight: 700;
    color: #1A0E08;
    text-align: center;
    border-bottom: 1.5px solid rgba(75,50,18,0.32);
    padding-bottom: 0.6rem;
    margin-bottom: 1rem;
    letter-spacing: 0.05em;
}}

.index-card-body {{
    font-family: 'Caveat', cursive;
    color: #1A0E08;
}}

.rule-main {{
    font-size: 1.35rem;
    line-height: 1.4;
    margin: 0 0 0.9rem 0;
}}

.rule-sub {{
    font-size: 1.1rem;
    color: #3A2810;
    margin: 0 0 0.55rem 0;
}}

.rule-row {{
    display: flex;
    align-items: center;
    gap: 0.65rem;
    font-size: 1.2rem;
    line-height: 1.3;
    margin-bottom: 0.45rem;
}}

.rule-img {{
    width: 30px !important;
    min-width: 30px !important;
    max-width: 30px !important;
    height: 30px;
    object-fit: contain;
    flex-shrink: 0;
    border-radius: 3px 4px 2px 4px;
}}

.rule-note {{
    font-size: 1.05rem;
    color: #5C3A1A;
    margin: 0.95rem 0 0 0;
    padding-top: 0.75rem;
    border-top: 1px dashed rgba(75,50,18,0.28);
    line-height: 1.45;
    font-style: italic;
}}
</style>
"""

# ── Flat parchment — landing page ──────────────────────────────────────────────
CSS_LANDING_BG = f"""
<style>
/* ─── Dark outer surround ─── */
html, body,
[data-testid="stAppViewContainer"] {{
    background: #5A3A22 !important;
}}

[data-testid="stMain"] {{
    background: transparent !important;
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: center !important;
    min-height: 100vh !important;
    padding: 3rem 1rem !important;
}}

/* ─── Framed parchment canvas ─── */
[data-testid="stMainBlockContainer"] {{
    max-width: 1300px !important;
    width: 100% !important;
    margin: 0 auto !important;
    padding: 5rem 2.5rem !important;
    min-height: 72vh !important;
    background-image:
        linear-gradient(rgba(80,55,20,0.11) 1px, transparent 1px),
        linear-gradient(90deg, rgba(80,55,20,0.11) 1px, transparent 1px),
        url('{TEXTURE}');
    background-size: 26px 26px, 26px 26px, cover;
    background-position: top left, top left, center;
    background-color: #EDE0B0;
    box-shadow:
        0 28px 65px rgba(0,0,0,0.60),
        0 8px 20px rgba(0,0,0,0.35),
        inset 0 0 0 1px rgba(60,40,15,0.25);
}}

[data-testid="stMainBlockContainer"]::after {{
    display: none !important;
}}

/* ─── Game title ─── */
.game-title {{
    font-family: 'Caveat', cursive;
    font-size: 6.5rem;
    font-weight: 700;
    color: #2A1B0A;
    text-align: center;
    letter-spacing: 0.02em;
    line-height: 1.05;
    margin: 0 0 2.4rem 0;
    padding: 0;
}}

.landing-btn-gap {{ height: 0.85rem; }}

/* Center the title + button stack vertically and horizontally */
[data-testid="stVerticalBlock"]:has(.landing-btn-gap) {{
    display: flex !important;
    flex-direction: column !important;
    justify-content: center !important;
    align-items: center !important;
    min-height: 68vh;
}}

/* Center each child element */
[data-testid="stVerticalBlock"]:has(.landing-btn-gap) > [data-testid="stButton"],
[data-testid="stVerticalBlock"]:has(.landing-btn-gap) > [data-testid="stMarkdown"] {{
    display: flex !important;
    justify-content: center !important;
}}

/* ─── START GAME button ─── */
[data-testid="stMarkdown"]:has(#start-btn-marker) ~ [data-testid="stButton"] > button {{
    background:     rgba(246, 239, 215, 0.92) !important;
    border:         1.5px solid rgba(42, 27, 10, 0.42) !important;
    color:          #2A1B0A !important;
    font-family:    'Caveat', cursive !important;
    font-size:      1.0rem !important;
    font-weight:    500 !important;
    letter-spacing: 0.22em !important;
    padding:        0.52rem 2.4rem !important;
    width:          220px !important;
    box-shadow:     0 1px 3px rgba(0,0,0,0.07) !important;
    text-transform: uppercase !important;
    border-radius:  0 !important;
    transition:     background 0.08s ease !important;
}}
[data-testid="stMarkdown"]:has(#start-btn-marker) ~ [data-testid="stButton"] > button:hover,
[data-testid="stMarkdown"]:has(#start-btn-marker) ~ [data-testid="stButton"] > button:focus {{
    background: rgba(230, 222, 196, 0.98) !important;
    color:      #1A0E08 !important;
    outline:    none !important;
}}

/* ─── INSTRUCTIONS button ─── */
[data-testid="stMarkdown"]:has(#instr-btn-marker) ~ [data-testid="stButton"] > button {{
    background:     rgba(148, 120, 72, 0.36) !important;
    border:         1.5px solid rgba(42, 27, 10, 0.42) !important;
    color:          #2A1B0A !important;
    font-family:    'Caveat', cursive !important;
    font-size:      1.0rem !important;
    font-weight:    500 !important;
    letter-spacing: 0.22em !important;
    padding:        0.52rem 2.4rem !important;
    width:          220x !important;
    box-shadow:     inset 0 1px 4px rgba(0,0,0,0.14), 0 1px 2px rgba(0,0,0,0.06) !important;
    text-transform: uppercase !important;
    border-radius:  0 !important;
    transition:     background 0.08s ease !important;
}}
[data-testid="stMarkdown"]:has(#instr-btn-marker) ~ [data-testid="stButton"] > button:hover,
[data-testid="stMarkdown"]:has(#instr-btn-marker) ~ [data-testid="stButton"] > button:focus {{
    background: rgba(148, 120, 72, 0.58) !important;
    color:      #1A0E08 !important;
    outline:    none !important;
}}
</style>
"""

# ── Flat seamless parchment + memo pad — active game page only ─────────────────
CSS_GAME_BG = f"""
<style>
/* ─── Full-screen flat parchment (no book split) ─── */
[data-testid="stAppViewContainer"] {{
    background-image:
        linear-gradient(rgba(80,55,20,0.11) 1px, transparent 1px),
        linear-gradient(90deg, rgba(80,55,20,0.11) 1px, transparent 1px),
        url('{TEXTURE}');
    background-size: 26px 26px, 26px 26px, cover;
    background-attachment: fixed;
    background-color: #EDE0B0 !important;
    background-position: top left, top left, center;
    min-height: 100vh;
}}

/* Center content vertically + horizontally */
[data-testid="stMain"] {{
    background: transparent !important;
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: center !important;
    min-height: 100vh !important;
    padding: 2.5rem 1rem !important;
}}

/* Transparent block container — no book chrome */
[data-testid="stMainBlockContainer"] {{
    max-width: 600px !important;
    width: 100% !important;
    margin: 0 auto !important;
    padding: 0 !important;
    background: transparent !important;
    background-image: none !important;
    box-shadow: none !important;
}}

/* No spine on game page */
[data-testid="stMainBlockContainer"]::after {{
    display: none !important;
}}

/* Column transparency for the input form */
[data-testid="stHorizontalBlock"] {{
    gap: 0 !important;
    padding: 0 !important;
}}

[data-testid="stColumn"] {{
    padding: 0 !important;
    background: transparent !important;
}}

[data-testid="stColumn"] > div:first-child {{
    background: transparent !important;
    padding: 0 !important;
}}

/* ─── Memo pad wrapper (top space for tape) ─── */
.panel-wrapper {{
    width: 100%;
    margin: 0 auto 0.75rem;
    padding-top: 20px;
    position: relative;
    z-index: 60;
}}

/* ─── Masking tape ─── */
.panel-wrapper::before {{
    content: '';
    position: absolute;
    top: 0;
    left: 50%;
    transform: translateX(-50%) rotate(-1.5deg);
    width: 88px;
    height: 28px;
    background: rgba(210, 180, 140, 0.85);
    box-shadow:
        0 2px 5px rgba(0,0,0,0.20),
        inset 0 1px 0 rgba(255,255,255,0.38);
    border-radius: 2px;
    z-index: 4;
}}

/* ─── Memo pad — wrinkled aged paper texture ─── */
.panel {{
    background-image:
        linear-gradient(rgba(255,255,255,0.18), rgba(255,255,255,0.18)),
        url('{WRINKLED_PAPER}');
    background-size: cover;
    background-position: center;
    border: 1.5px solid rgba(75,50,18,0.60);
    border-radius: 2px;
    box-shadow:
        4px 10px 38px rgba(0,0,0,0.52),
        2px 4px 14px rgba(0,0,0,0.30),
        -1px 1px 5px rgba(0,0,0,0.12);
    padding: 1.3rem 1.5rem 0;
    position: relative;
    overflow: visible;
}}

/* ─── Inner scrollable area ─── */
.panel-inner {{
    max-height: 420px;
    overflow-y: auto;
    padding-bottom: 1.5rem;
    scrollbar-width: thin;
    scrollbar-color: rgba(105,70,22,0.5) transparent;
}}

.panel-inner::-webkit-scrollbar {{ width: 6px; }}
.panel-inner::-webkit-scrollbar-thumb {{
    background: rgba(105,70,22,0.50);
    border-radius: 3px;
}}

/* ─── Hide native text input + submit (replaced by custom 4-digit component) ─── */
[data-testid="stTextInput"],
[data-testid="stFormSubmitButton"] {{
    position: fixed !important;
    left: -9999px !important;
    top: -9999px !important;
    width: 1px !important;
    height: 1px !important;
    overflow: hidden !important;
    opacity: 0 !important;
}}
</style>
"""


# ── Helpers ────────────────────────────────────────────────────────────────────

def md_bold(text: str) -> str:
    """Convert **bold** markdown to <b> HTML."""
    return re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)


def blocks_html(g: int, y: int, r: int) -> str:
    imgs = (
        [f'<img src="{GREEN_PAINT}"  class="feedback-img" alt="green">']  * g +
        [f'<img src="{YELLOW_PAINT}" class="feedback-img" alt="yellow">'] * y +
        [f'<img src="{RED_PAINT}"    class="feedback-img" alt="red">']    * r
    )
    return "".join(imgs)


def guess_row_html(num: int, guess: tuple, feedback: tuple, solved: bool = False) -> str:
    g, y, r = feedback
    digits = "-".join(str(d) for d in guess)
    solved_span = '<span class="solved-label">Solved!</span>' if solved else ""
    return (
        f'<div class="guess-row">'
        f'<span class="guess-num">{num}.</span>'
        f'<span class="guess-digits">{digits}</span>'
        f'{solved_span}'
        f'<div class="guess-blocks">{blocks_html(g, y, r)}</div>'
        f'</div>'
    )


def js_input_validate() -> None:
    """Validate input, wire Enter to submit, and auto-focus the field."""
    components.html("""
<script>
(function(){
  const doc = window.parent.document;

  function tryFocus(){
    const inp = doc.querySelector('[data-testid="stTextInput"] input');
    if(inp){ inp.focus(); return true; }
    return false;
  }
  if(!tryFocus()){
    const t = setInterval(function(){ if(tryFocus()) clearInterval(t); }, 80);
    setTimeout(function(){ clearInterval(t); }, 4000);
  }

  function attach(){
    const inputs = doc.querySelectorAll('[data-testid="stTextInput"] input');
    inputs.forEach(function(inp){
      if(inp._cipherReady) return;
      inp._cipherReady = true;

      inp.addEventListener('keydown', function(e){
        if(e.key === 'Enter'){
          e.preventDefault();
          const btn = doc.querySelector('[data-testid="stFormSubmitButton"] button');
          if(btn) btn.click();
          return;
        }
        const dig = '0123456789';
        const nav = ['Backspace','Delete','ArrowLeft','ArrowRight','Tab'];
        if(!dig.includes(e.key) && !nav.includes(e.key)){
          e.preventDefault(); return;
        }
        if(dig.includes(e.key) && this.value.includes(e.key)){
          e.preventDefault();
        }
      });

      inp.addEventListener('input', function(){
        let v = this.value.replace(/[^0-9]/g,'');
        const seen = new Set();
        v = [...v].filter(d => !seen.has(d) && seen.add(d)).join('');
        if(v.length > 4) v = v.slice(0,4);
        if(this.value !== v) this.value = v;
      });
    });
  }

  attach();
  new MutationObserver(attach).observe(doc.body, {childList:true, subtree:true});
})();
</script>
""", height=0)


# ── Session state ──────────────────────────────────────────────────────────────

def init_state() -> None:
    if "page" not in st.session_state:
        st.session_state.page = "landing"


def start_game() -> None:
    st.session_state.secret        = generate_secret()
    print(f"DEBUG — Correct Answer: {st.session_state.secret}")
    st.session_state.user_guesses  = []
    st.session_state.ai_guesses    = []
    st.session_state.ai_candidates = ALL_INDICES.copy()
    st.session_state.ai_next_guess = FIRST_GUESS
    st.session_state.ai_entropy    = 0.0
    st.session_state.input_error   = ""
    st.session_state.page          = "game"
    # Clear post-game caches so they recompute fresh next round
    st.session_state.pop("ai_full_path",    None)
    st.session_state.pop("llm_analysis",    None)
    st.session_state.pop("user_path_stats", None)


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


# ── Pages ──────────────────────────────────────────────────────────────────────

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


def digit_input_component() -> None:
    """Custom 4-box digit input rendered as an HTML/JS iframe component."""
    component_html = f"""
<link href="https://fonts.googleapis.com/css2?family=Caveat:wght@400;600;700&display=swap" rel="stylesheet">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: transparent; font-family: 'Caveat', cursive; display: flex; flex-direction: column; align-items: center; padding: 6px 0; }}
  .digit-grid {{ display: flex; gap: 14px; justify-content: center; margin-bottom: 14px; }}
  .digit-box {{
    width: 64px; height: 76px;
    border: none; border-bottom: 3px solid #2A1B0A;
    background: transparent;
    font-family: 'Caveat', cursive; font-size: 3rem; font-weight: 700;
    color: #2A1B0A; text-align: center; outline: none;
    transition: border-color 0.1s;
  }}
  .digit-box:focus {{ border-bottom-color: #10B981; }}
  .digit-box.filled {{ border-bottom-color: #4B3212; }}
  #submit-btn {{
    display: block; margin: 0 auto;
    font-family: 'Caveat', cursive; font-size: 1.5rem; font-weight: 600;
    background: transparent; color: #2A1B0A;
    border: 2px solid rgba(75,50,18,0.55);
    padding: 0.28rem 2.2rem; cursor: pointer; letter-spacing: 0.06em;
    border-radius: 0; transition: background 0.08s;
  }}
  #submit-btn:hover {{ background: rgba(75,50,18,0.09); }}
  #err-msg {{ font-family:'Caveat',cursive; font-size:1rem; color:#962828; text-align:center; margin-top:6px; min-height:1.1rem; }}
</style>
<div class="digit-grid">
  <input class="digit-box" id="d0" maxlength="1" type="text" inputmode="numeric" autocomplete="off">
  <input class="digit-box" id="d1" maxlength="1" type="text" inputmode="numeric" autocomplete="off">
  <input class="digit-box" id="d2" maxlength="1" type="text" inputmode="numeric" autocomplete="off">
  <input class="digit-box" id="d3" maxlength="1" type="text" inputmode="numeric" autocomplete="off">
</div>
<button id="submit-btn">SUBMIT</button>
<div id="err-msg"></div>
<script>
(function(){{
  const boxes = Array.from(document.querySelectorAll('.digit-box'));
  const submitBtn = document.getElementById('submit-btn');
  const errMsg = document.getElementById('err-msg');
  const doc = window.parent.document;

  // Focus first box on load
  setTimeout(() => boxes[0].focus(), 120);

  function showErr(msg) {{
    errMsg.textContent = msg;
    setTimeout(() => {{ errMsg.textContent = ''; }}, 2500);
  }}

  boxes.forEach((box, i) => {{
    box.addEventListener('keydown', e => {{
      if (e.key === 'Backspace' && box.value === '' && i > 0) {{
        e.preventDefault(); boxes[i-1].value = ''; boxes[i-1].classList.remove('filled'); boxes[i-1].focus(); return;
      }}
      if (e.key === 'ArrowLeft'  && i > 0) {{ boxes[i-1].focus(); return; }}
      if (e.key === 'ArrowRight' && i < 3) {{ boxes[i+1].focus(); return; }}
      if (e.key === 'Enter') {{ submitBtn.click(); return; }}
    }});
    box.addEventListener('input', () => {{
      const v = box.value.replace(/[^0-9]/g, '');
      if (!v) {{ box.value = ''; box.classList.remove('filled'); return; }}
      const digit = v[v.length - 1];
      const others = boxes.filter((_, j) => j !== i).map(b => b.value);
      if (others.includes(digit)) {{
        showErr('No repeated digits!'); box.value = ''; box.classList.remove('filled'); return;
      }}
      box.value = digit; box.classList.add('filled');
      errMsg.textContent = '';
      if (i < 3) boxes[i+1].focus();
    }});
  }});

  submitBtn.addEventListener('click', () => {{
    const digits = boxes.map(b => b.value);
    if (digits.some(d => d === '')) {{ showErr('Fill all 4 digit slots.'); return; }}
    const value = digits.join('');
    const stInput = doc.querySelector('[data-testid="stTextInput"] input');
    if (!stInput) {{ showErr('Input not ready — try again.'); return; }}
    const nativeSetter = Object.getOwnPropertyDescriptor(window.parent.HTMLInputElement.prototype, 'value').set;
    nativeSetter.call(stInput, value);
    stInput.dispatchEvent(new window.parent.Event('input', {{ bubbles: true }}));
    boxes.forEach(b => {{ b.value = ''; b.classList.remove('filled'); }});
    boxes[0].focus();
    setTimeout(() => {{
      const stSubmit = doc.querySelector('[data-testid="stFormSubmitButton"] button');
      if (stSubmit) stSubmit.click();
    }}, 80);
  }});
}})();
</script>
"""
    components.html(component_html, height=175)


def landing_page() -> None:
    st.markdown(CSS_BASE + CSS_LANDING_BG, unsafe_allow_html=True)

    st.markdown('<div class="game-title">Cipher</div>', unsafe_allow_html=True)

    st.markdown('<div id="start-btn-marker"></div>', unsafe_allow_html=True)
    if st.button("START GAME", key="start_btn"):
        show_intro_dialog()
    st.markdown('<div class="landing-btn-gap"></div>', unsafe_allow_html=True)



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
    st.markdown(CSS_BASE + CSS_BOOK_BG, unsafe_allow_html=True)

    # ── Pre-compute the complete AI game path (cached after first run) ────────
    ai_full_path     = precompute_ai_full_game()
    user_path_stats  = precompute_user_path_stats()
    user_guesses = st.session_state.user_guesses

    ai_guesses   = st.session_state.ai_guesses
    n_user       = len(user_guesses)
    n_ai         = len(ai_guesses)

    # ── Win / loss determination ──────────────────────────────────────────────
    user_won     = n_user <= n_ai
    outcome_cls  = "win"  if user_won else "lose"
    outcome_txt  = "You Win!" if user_won else "The AI Wins."
    outcome_sub  = (
        f"You solved it in {n_user} {'guess' if n_user == 1 else 'guesses'} — "
        f"the AI needed {n_ai}."
        if user_won else
        f"You needed {n_user} {'guess' if n_user == 1 else 'guesses'} — "
        f"the AI solved it in {n_ai}."
    )

    # ── AI solution path rows ─────────────────────────────────────────────────
    ai_rows_html = ""
    for i, entry in enumerate(ai_guesses, 1):
        g, y, r     = entry["feedback"]
        digits      = "-".join(str(d) for d in entry["guess"])
        solved_span = '<span class="ai-solved-txt">Solved!</span>' if entry["feedback"] == (4, 0, 0) else ""
        ai_rows_html += (
            f'<div class="ai-row">'
            f'<span class="ai-row-num">{i}.</span>'
            f'<span class="ai-row-digits">{digits}</span>'
            f'{solved_span}'
            f'<div class="guess-blocks">{blocks_html(g, y, r)}</div>'
            f'</div>'
        )

    # ── Left column: win/loss + user steps + AI path + Play Again ────────────
    guess_word = "guess" if n_user == 1 else "guesses"
    left_html = (
        f'<div class="page-left-content fade-in">'
        f'<div class="win-loss-banner {outcome_cls}">'
        f'{outcome_txt}<br>'
        f'<span style="font-size:1.25rem;font-weight:500;">{outcome_sub}</span>'
        f'</div>'
        f'<div class="page-title">AI AGENT SOLUTION PATH</div>'
        f'{ai_rows_html}'
        f'</div>'
    )

    # ── Right column: step-by-step AI explanation ─────────────────────────────
    explain_html = ""
    for i, entry in enumerate(ai_guesses, 1):
        raw_text = explain_step(
            step=i,
            guess=entry["guess"],
            feedback=entry["feedback"],
            cands_before=entry["cands_before"],
            cands_after=entry["cands_after"],
            entropy_bits=entry["entropy"],
        )
        explain_html += f'<div class="explain-entry">{md_bold(raw_text)}</div>'

    right_html = (
        f'<div class="page-right-content fade-in">'
        f'<div class="page-title">STEP-BY-STEP EXPLANATION</div>'
        f'{explain_html}'
        f'</div>'
    )

    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown(left_html, unsafe_allow_html=True)
        st.markdown('<div class="play-again-area"></div>', unsafe_allow_html=True)
        if st.button("PLAY AGAIN", key="play_again"):
            start_game()
            st.rerun()

    with col_right:
        st.markdown(right_html, unsafe_allow_html=True)


# ── Main ──────────────────────────────────────────────────────────────────────

init_state()
page = st.session_state.get("page", "landing")

if page == "landing":
    landing_page()
elif page == "game":
    game_page()
elif page == "reveal":
    reveal_page()
