from __future__ import annotations
from ui.assets import TEXTURE, WRINKLED_PAPER

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

# ── Post-game analysis page extras ────────────────────────────────────────────
CSS_ANALYSIS = """
<style>
/* ─── Column padding on the open-ledger reveal page ─── */
[data-testid="stColumn"] > div:first-child {
    padding: 2.5rem 2.2rem 2rem !important;
}

/* ─── Path Toggle: strip radio chrome, render as tab underlines ─── */
div[data-testid="stRadio"] {
    margin: 0 0 1.1rem 0 !important;
}

/* options row */
div[data-testid="stRadio"] > div {
    display: flex !important;
    flex-direction: row !important;
    gap: 0 !important;
    border-bottom: 1.5px solid rgba(75,50,18,0.22) !important;
    padding-bottom: 0 !important;
    justify-content: flex-start !important;
    background: transparent !important;
}

/* each option label */
div[data-testid="stRadio"] > div > label {
    display: flex !important;
    align-items: center !important;
    font-family: 'Caveat', cursive !important;
    font-size: 1.55rem !important;
    font-weight: 600 !important;
    color: #8A7050 !important;
    cursor: pointer !important;
    padding: 0.12rem 1.2rem 0.48rem !important;
    border-bottom: 2.5px solid transparent !important;
    margin-bottom: -1.5px !important;
    transition: color 0.12s ease, border-color 0.12s ease !important;
    background: transparent !important;
    user-select: none !important;
}

div[data-testid="stRadio"] > div > label:hover {
    color: #3A2810 !important;
}

/* active (checked) tab */
div[data-testid="stRadio"] > div > label:has(input:checked) {
    color: #1A0E08 !important;
    border-bottom-color: #2A1B0A !important;
}

/* hide the actual radio circle dot */
div[data-testid="stRadio"] input[type="radio"] {
    position: absolute !important;
    opacity: 0 !important;
    width: 0 !important;
    height: 0 !important;
    pointer-events: none !important;
}

div[data-testid="stRadio"] > div > label > div:first-child {
    display: none !important;
}

/* label text */
div[data-testid="stRadio"] > div > label p {
    margin: 0 !important;
    font-family: 'Caveat', cursive !important;
    font-size: inherit !important;
    font-weight: inherit !important;
    color: #000000 !important;
}

/* ─── Coach's Notes analysis card ─── */
.analysis-headline {
    font-family: 'Caveat', cursive;
    font-size: 2.15rem;
    font-weight: 700;
    color: #1A0E08;
    text-align: center;
    margin-bottom: 0.75rem;
    line-height: 1.2;
    border-bottom: 1.5px solid rgba(75,50,18,0.25);
    padding-bottom: 0.55rem;
    letter-spacing: 0.04em;
}

.analysis-bullet {
    font-family: 'Caveat', cursive;
    font-size: 1.40rem;
    font-weight: 500;
    color: #2A1B0A;
    line-height: 1.65;
    margin-bottom: 0.7rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid rgba(75,50,18,0.13);
    letter-spacing: 0.01em;
}

.analysis-bullet:last-child {
    border-bottom: none;
    margin-bottom: 0;
}

/* ─── Spinner text ─── */
[data-testid="stSpinner"] p {
    font-family: 'Caveat', cursive !important;
    font-size: 1.25rem !important;
    color: #5C3A1A !important;
}

/* ─── Invisible scroll container for guess list ─── */
.guess-scroll-container {
    max-height: 450px;
    overflow-y: auto;
    -webkit-mask-image: linear-gradient(to bottom, black 85%, transparent 100%);
    mask-image: linear-gradient(to bottom, black 85%, transparent 100%);
}

/* Hide scrollbar — Webkit */
.guess-scroll-container::-webkit-scrollbar {
    display: none;
}

/* Hide scrollbar — Firefox */
.guess-scroll-container {
    scrollbar-width: none;
}

/* Hide scrollbar — IE/Edge */
.guess-scroll-container {
    -ms-overflow-style: none;
}
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
