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
</style>
"""

# ── Open-book/ledger background — landing + instructions + result pages ────────
CSS_BOOK_BG = f"""
<style>
html, body,
[data-testid="stAppViewContainer"],
[data-testid="stMain"] {{
    background: #3A2810 !important;
}}

/* ─── Open ledger container ─── */
[data-testid="stMainBlockContainer"] {{
    max-width: 1120px !important;
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

/* ─── Landing page: dead-center the title+button stack ─── */
/* :has(.landing-btn-gap) scopes these rules to the landing column only */
[data-testid="stVerticalBlock"]:has(.landing-btn-gap) {{
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
    width: 30px;
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
    background: #3A2810 !important;
}}

[data-testid="stMain"] {{
    background: transparent !important;
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: center !important;
    min-height: 10vh !important;
    padding: 2.5rem 1rem !important;
}}

/* ─── Framed parchment canvas ─── */
[data-testid="stMainBlockContainer"] {{
    max-width: 1300px !important;
    width: 100% !important;
    margin: 0 auto !important;
    padding: 3rem 2.5rem !important;
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
    font-size: 4.5rem;
    font-weight: 700;
    color: #2A1B0A;
    text-align: center;
    letter-spacing: 0.02em;
    line-height: 1.05;
    margin: 0 0 1.4rem 0;
    padding: 0;
}}

.landing-btn-gap {{ height: 0.85rem; }}

/* Center the title + button stack vertically and horizontally */
[data-testid="stVerticalBlock"]:has(.landing-btn-gap) {{
    display: flex !important;
    flex-direction: column !important;
    justify-content: center !important;
    align-items: center !important;
    min-height: 60vh;
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

def landing_page() -> None:
    st.markdown(CSS_BASE + CSS_LANDING_BG, unsafe_allow_html=True)

    st.markdown('<div class="game-title">Cipher</div>', unsafe_allow_html=True)

    st.markdown('<div id="start-btn-marker"></div>', unsafe_allow_html=True)
    if st.button("START GAME", key="start_btn"):
        start_game()
        st.rerun()

    st.markdown('<div class="landing-btn-gap"></div>', unsafe_allow_html=True)

    st.markdown('<div id="instr-btn-marker"></div>', unsafe_allow_html=True)
    if st.button("INSTRUCTIONS", key="instructions_btn"):
        st.session_state.page = "instructions"
        st.rerun()


def instructions_page() -> None:
    st.markdown(CSS_BASE + CSS_BOOK_BG, unsafe_allow_html=True)

    _, mid, _ = st.columns([2, 3, 2])
    with mid:
        st.markdown(
            f'<div class="index-card">'
            f'<div class="index-card-title">HOW TO PLAY</div>'
            f'<div class="index-card-body">'
            f'<p class="rule-main">Guess the <strong>4-digit secret code</strong>. No repeating digits.</p>'
            f'<p class="rule-sub">After each guess you receive colour feedback:</p>'
            f'<div class="rule-row">'
            f'  <img src="{GREEN_PAINT}" class="rule-img" alt="green">'
            f'  <span><strong>Green</strong> — correct digit &amp; correct position</span>'
            f'</div>'
            f'<div class="rule-row">'
            f'  <img src="{YELLOW_PAINT}" class="rule-img" alt="yellow">'
            f'  <span><strong>Yellow</strong> — correct digit, wrong position</span>'
            f'</div>'
            f'<div class="rule-row">'
            f'  <img src="{RED_PAINT}" class="rule-img" alt="red">'
            f'  <span><strong>Red</strong> — digit not in the code at all</span>'
            f'</div>'
            f'<p class="rule-note">The feedback blocks do <em>not</em> correspond to the '
            f'exact positions of the digits — only the counts are shown.</p>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        if st.button("CLOSE", key="close_btn"):
            st.session_state.page = "landing"
            st.rerun()


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

    with st.form("guess_form", clear_on_submit=True):
        guess_val = st.text_input(
            "guess", placeholder="_ _ _ _", max_chars=4,
            key="digit_input", label_visibility="collapsed",
        )
        submitted = st.form_submit_button("SUBMIT")
        if submitted and guess_val:
            process_user_guess(guess_val)
            st.rerun()

    if st.session_state.get("input_error"):
        st.markdown(
            f'<div class="err-msg">⚠ {st.session_state.input_error}</div>',
            unsafe_allow_html=True,
        )

    js_input_validate()


def reveal_page() -> None:
    st.markdown(CSS_BASE + CSS_BOOK_BG, unsafe_allow_html=True)

    ai_guesses   = st.session_state.ai_guesses
    user_guesses = st.session_state.user_guesses
    n_user       = len(user_guesses)

    # ── Left column: AI solution path ───────────────────────────────────────
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

    left_html = (
        f'<div class="page-left-content fade-in">'
        f'<div class="page-title">AI AGENT SOLUTION PATH</div>'
        f'{ai_rows_html}'
        f'</div>'
    )

    # ── Right column: score + step explanations ──────────────────────────────
    guess_word   = "guess" if n_user == 1 else "guesses"
    score_banner = (
        f'<div class="score-banner">'
        f'You cracked the cipher in {n_user} {guess_word}!'
        f'</div>'
    )

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
        f'{score_banner}'
        f'<div class="page-title">STEP-BY-STEP EXPLANATION</div>'
        f'{explain_html}'
        f'</div>'
    )

    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown(left_html, unsafe_allow_html=True)

    with col_right:
        st.markdown(right_html, unsafe_allow_html=True)
        if st.button("PLAY AGAIN", key="play_again"):
            start_game()
            st.rerun()


# ── Main ──────────────────────────────────────────────────────────────────────

init_state()
page = st.session_state.get("page", "landing")

if page == "landing":
    landing_page()
elif page == "instructions":
    instructions_page()
elif page == "game":
    game_page()
elif page == "reveal":
    reveal_page()
