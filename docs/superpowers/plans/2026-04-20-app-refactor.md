# app.py Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split `app.py` (1,700 lines) into 9 focused modules without changing any user-visible behaviour or breaking existing tests.

**Architecture:** Pure move refactor — no logic changes. CSS constants go to `ui/styles.py`, HTML/JS components to `ui/components.py`, session state to `ui/state.py`, page functions to `ui/pages/`, and the Gemini API call to `services/llm.py`. `app.py` becomes a ~30-line router.

**Tech Stack:** Python 3.9, Streamlit, Google GenAI SDK (gemma-3-27b-it), pytest

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `ui/__init__.py` | Create | Package marker |
| `ui/pages/__init__.py` | Create | Package marker |
| `services/__init__.py` | Create | Package marker |
| `ui/assets.py` | Create | `_b64()` loader + image URL constants |
| `ui/styles.py` | Create | All CSS string constants |
| `ui/components.py` | Create | `blocks_html`, `guess_row_html`, `md_bold`, `digit_input_component`, `js_input_validate` |
| `ui/state.py` | Create | `init_state`, `start_game`, `run_ai_step`, `process_user_guess` |
| `services/llm.py` | Create | `get_llm_analysis` |
| `ui/pages/landing.py` | Create | `landing_page`, `show_intro_dialog` |
| `ui/pages/game.py` | Create | `game_page` |
| `ui/pages/reveal.py` | Create | `reveal_page`, `precompute_ai_full_game`, `precompute_user_path_stats` |
| `app.py` | Rewrite | Page config + routing only (~30 lines) |

---

## Task 1: Create package skeleton

**Files:**
- Create: `ui/__init__.py`
- Create: `ui/pages/__init__.py`
- Create: `services/__init__.py`

- [ ] **Step 1: Create three empty `__init__.py` files**

```bash
touch ui/__init__.py ui/pages/__init__.py services/__init__.py
```

Or create each file with this content (identical for all three):

```python
```

(Empty files — they exist only to mark the directories as Python packages.)

- [ ] **Step 2: Verify Python sees the packages**

Run:
```bash
cd c:/Users/yeekw/Documents/Cipher && python -c "import ui; import ui.pages; import services; print('OK')"
```
Expected output: `OK`

- [ ] **Step 3: Run existing tests to confirm nothing broke**

Run:
```bash
cd c:/Users/yeekw/Documents/Cipher && python -m pytest tests/ -v
```
Expected: all tests pass (same as before this task).

- [ ] **Step 4: Commit**

```bash
git add ui/__init__.py ui/pages/__init__.py services/__init__.py
git commit -m "refactor: add ui and services package skeletons"
```

---

## Task 2: Create `ui/assets.py`

**Files:**
- Create: `ui/assets.py`
- Source: `app.py` lines 33–41

- [ ] **Step 1: Create `ui/assets.py`**

```python
from __future__ import annotations
import base64
from pathlib import Path


def _b64(filename: str, mime: str = "image/png") -> str:
    # __file__ is ui/assets.py; parent.parent is the project root
    with open(Path(__file__).parent.parent / "image" / filename, "rb") as _f:
        return f"data:{mime};base64,{base64.b64encode(_f.read()).decode()}"


TEXTURE        = _b64("image_7.jpg",   "image/jpeg")
WRINKLED_PAPER = _b64("image_10.jpg",  "image/jpeg")
GREEN_PAINT    = _b64("green_paint.png")
YELLOW_PAINT   = _b64("yellow_paint.png")
RED_PAINT      = _b64("red_paint.png")
```

- [ ] **Step 2: Verify the import loads image data correctly**

Run:
```bash
cd c:/Users/yeekw/Documents/Cipher && python -c "from ui.assets import TEXTURE, GREEN_PAINT; assert TEXTURE.startswith('data:image/jpeg;base64,'); assert GREEN_PAINT.startswith('data:image/png;base64,'); print('OK')"
```
Expected output: `OK`

- [ ] **Step 3: Run existing tests**

Run:
```bash
python -m pytest tests/ -v
```
Expected: all tests pass.

- [ ] **Step 4: Commit**

```bash
git add ui/assets.py
git commit -m "refactor: extract asset loader and image constants to ui/assets.py"
```

---

## Task 3: Create `ui/styles.py`

**Files:**
- Create: `ui/styles.py`
- Source: `app.py` lines 43–978 (all CSS constants)

This task also fixes the silent bug: `CSS_ANALYSIS` is defined twice in `app.py` (lines 709–731 and lines 855–978). Only the second definition (lines 855–978) is used. The first dead definition is dropped here.

- [ ] **Step 1: Create `ui/styles.py`**

The file has this structure — copy the CSS string content verbatim from the indicated line ranges in `app.py`:

```python
from __future__ import annotations
from ui.assets import TEXTURE, WRINKLED_PAPER

# ── Shared base styles (injected on every page) ───────────────────────────────
# Copy the f-string body from app.py lines 46–458 verbatim.
CSS_BASE = f"""
<style>
...
</style>
"""

# ── Open-book/ledger background — result page ─────────────────────────────────
# Copy the f-string body from app.py lines 461–707 verbatim.
CSS_BOOK_BG = f"""
<style>
...
</style>
"""

# ── Flat parchment — landing page ─────────────────────────────────────────────
# Copy the f-string body from app.py lines 734–853 verbatim.
CSS_LANDING_BG = f"""
<style>
...
</style>
"""

# ── Post-game analysis page extras ────────────────────────────────────────────
# Copy the string body from app.py lines 856–978 verbatim.
# NOTE: This is the ONLY CSS_ANALYSIS definition — the earlier one (lines 709–731)
# is dead code and is intentionally omitted.
CSS_ANALYSIS = """
<style>
...
</style>
"""

# ── Flat seamless parchment + memo pad — active game page only ────────────────
# Copy the f-string body from app.py lines 981–1110 verbatim.
CSS_GAME_BG = f"""
<style>
...
</style>
"""
```

When copying, replace `...` with the actual CSS content from the specified line ranges. `CSS_BASE`, `CSS_BOOK_BG`, `CSS_LANDING_BG`, and `CSS_GAME_BG` are f-strings (they reference `TEXTURE` and/or `WRINKLED_PAPER`). `CSS_ANALYSIS` is a plain string (no image refs).

- [ ] **Step 2: Verify import and that CSS strings are non-empty**

Run:
```bash
cd c:/Users/yeekw/Documents/Cipher && python -c "
from ui.styles import CSS_BASE, CSS_BOOK_BG, CSS_LANDING_BG, CSS_GAME_BG, CSS_ANALYSIS
assert 'Caveat' in CSS_BASE
assert 'stMainBlockContainer' in CSS_BOOK_BG
assert 'landing' in CSS_LANDING_BG.lower() or 'stMain' in CSS_LANDING_BG
assert 'analysis' in CSS_ANALYSIS.lower() or 'stRadio' in CSS_ANALYSIS
assert 'stAppViewContainer' in CSS_GAME_BG
print('OK')
"
```
Expected output: `OK`

- [ ] **Step 3: Run existing tests**

Run:
```bash
python -m pytest tests/ -v
```
Expected: all tests pass.

- [ ] **Step 4: Commit**

```bash
git add ui/styles.py
git commit -m "refactor: extract CSS constants to ui/styles.py, remove dead CSS_ANALYSIS definition"
```

---

## Task 4: Create `ui/components.py`

**Files:**
- Create: `ui/components.py`
- Source: `app.py` lines 1113–1197

- [ ] **Step 1: Create `ui/components.py`**

```python
from __future__ import annotations
import re
import streamlit.components.v1 as components
from ui.assets import GREEN_PAINT, YELLOW_PAINT, RED_PAINT


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


def digit_input_component() -> None:
    """Custom 4-box digit input rendered as an HTML/JS iframe component."""
    from ui.assets import GREEN_PAINT  # noqa: F401 — not used here; kept for symmetry
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
```

Note: the `from ui.assets import GREEN_PAINT` inside `digit_input_component` is unnecessary (the function doesn't use it). Remove that line — it was added by mistake in the draft above. The function is self-contained HTML/JS and needs no image imports.

- [ ] **Step 2: Verify import and basic function behaviour**

Run:
```bash
cd c:/Users/yeekw/Documents/Cipher && python -c "
from ui.components import md_bold, blocks_html, guess_row_html
assert md_bold('hello **world**') == 'hello <b>world</b>'
assert 'green' in blocks_html(2, 1, 1)
row = guess_row_html(1, (1,2,3,4), (3,1,0))
assert 'guess-row' in row and '1-2-3-4' in row
print('OK')
"
```
Expected output: `OK`

- [ ] **Step 3: Run existing tests**

Run:
```bash
python -m pytest tests/ -v
```
Expected: all tests pass.

- [ ] **Step 4: Commit**

```bash
git add ui/components.py
git commit -m "refactor: extract HTML/JS components to ui/components.py"
```

---

## Task 5: Create `ui/state.py`

**Files:**
- Create: `ui/state.py`
- Source: `app.py` lines 1200–1275

- [ ] **Step 1: Create `ui/state.py`**

```python
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
```

- [ ] **Step 2: Verify import**

Run:
```bash
cd c:/Users/yeekw/Documents/Cipher && python -c "from ui.state import init_state, start_game, run_ai_step, process_user_guess; print('OK')"
```
Expected output: `OK`

- [ ] **Step 3: Run existing tests**

Run:
```bash
python -m pytest tests/ -v
```
Expected: all tests pass.

- [ ] **Step 4: Commit**

```bash
git add ui/state.py
git commit -m "refactor: extract session state management to ui/state.py"
```

---

## Task 6: Create `services/llm.py`

**Files:**
- Create: `services/llm.py`
- Source: `app.py` lines 1506–1582

- [ ] **Step 1: Create `services/llm.py`**

```python
from __future__ import annotations
import re
import json
import html
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
```

- [ ] **Step 2: Verify import**

Run:
```bash
cd c:/Users/yeekw/Documents/Cipher && python -c "from services.llm import get_llm_analysis; print('OK')"
```
Expected output: `OK`

- [ ] **Step 3: Run existing tests**

Run:
```bash
python -m pytest tests/ -v
```
Expected: all tests pass.

- [ ] **Step 4: Commit**

```bash
git add services/__init__.py services/llm.py
git commit -m "refactor: extract Gemini API call to services/llm.py"
```

---

## Task 7: Create `ui/pages/landing.py`

**Files:**
- Create: `ui/pages/landing.py`
- Source: `app.py` lines 1279–1413

- [ ] **Step 1: Create `ui/pages/landing.py`**

```python
from __future__ import annotations
import streamlit as st
from ui.styles import CSS_BASE, CSS_LANDING_BG
from ui.assets import GREEN_PAINT, YELLOW_PAINT, RED_PAINT
from ui.state import start_game


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


def landing_page() -> None:
    st.markdown(CSS_BASE + CSS_LANDING_BG, unsafe_allow_html=True)

    st.markdown('<div class="game-title">Cipher</div>', unsafe_allow_html=True)

    st.markdown('<div id="start-btn-marker"></div>', unsafe_allow_html=True)
    if st.button("START GAME", key="start_btn"):
        show_intro_dialog()
    st.markdown('<div class="landing-btn-gap"></div>', unsafe_allow_html=True)
```

- [ ] **Step 2: Verify import**

Run:
```bash
cd c:/Users/yeekw/Documents/Cipher && python -c "from ui.pages.landing import landing_page, show_intro_dialog; print('OK')"
```
Expected output: `OK`

- [ ] **Step 3: Run existing tests**

Run:
```bash
python -m pytest tests/ -v
```
Expected: all tests pass.

- [ ] **Step 4: Commit**

```bash
git add ui/pages/landing.py
git commit -m "refactor: extract landing page to ui/pages/landing.py"
```

---

## Task 8: Create `ui/pages/game.py`

**Files:**
- Create: `ui/pages/game.py`
- Source: `app.py` lines 1417–1465

- [ ] **Step 1: Create `ui/pages/game.py`**

```python
from __future__ import annotations
import streamlit as st
from ui.styles import CSS_BASE, CSS_GAME_BG
from ui.components import guess_row_html, digit_input_component
from ui.state import process_user_guess


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
```

- [ ] **Step 2: Verify import**

Run:
```bash
cd c:/Users/yeekw/Documents/Cipher && python -c "from ui.pages.game import game_page; print('OK')"
```
Expected output: `OK`

- [ ] **Step 3: Run existing tests**

Run:
```bash
python -m pytest tests/ -v
```
Expected: all tests pass.

- [ ] **Step 4: Commit**

```bash
git add ui/pages/game.py
git commit -m "refactor: extract game page to ui/pages/game.py"
```

---

## Task 9: Create `ui/pages/reveal.py`

**Files:**
- Create: `ui/pages/reveal.py`
- Source: `app.py` lines 1467–1688

- [ ] **Step 1: Create `ui/pages/reveal.py`**

```python
from __future__ import annotations
import html
import streamlit as st
from cipher_engine import ALL_INDICES, filter_candidates
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
```

- [ ] **Step 2: Verify import**

Run:
```bash
cd c:/Users/yeekw/Documents/Cipher && python -c "from ui.pages.reveal import reveal_page, precompute_ai_full_game, precompute_user_path_stats; print('OK')"
```
Expected output: `OK`

- [ ] **Step 3: Run existing tests**

Run:
```bash
python -m pytest tests/ -v
```
Expected: all tests pass.

- [ ] **Step 4: Commit**

```bash
git add ui/pages/reveal.py
git commit -m "refactor: extract reveal page to ui/pages/reveal.py"
```

---

## Task 10: Rewrite `app.py` and verify

**Files:**
- Modify: `app.py` (full rewrite — replace all 1,700 lines)

- [ ] **Step 1: Rewrite `app.py`**

Replace the entire contents of `app.py` with:

```python
"""
Cipher — Streamlit front-end entry point.
"""
from __future__ import annotations
import os

# Suppress gRPC/ALTS noise printed to stderr by the google-genai native layer
os.environ.setdefault("GRPC_VERBOSITY", "NONE")

import streamlit as st
from ui.state import init_state
from ui.pages.landing import landing_page
from ui.pages.game import game_page
from ui.pages.reveal import reveal_page

st.set_page_config(
    page_title="Cipher",
    layout="wide",
    initial_sidebar_state="collapsed",
)

init_state()
page = st.session_state.get("page", "landing")

if page == "landing":
    landing_page()
elif page == "game":
    game_page()
elif page == "reveal":
    reveal_page()
```

- [ ] **Step 2: Run existing tests**

Run:
```bash
cd c:/Users/yeekw/Documents/Cipher && python -m pytest tests/ -v
```
Expected: all tests pass.

- [ ] **Step 3: Verify the app starts without import errors**

Run:
```bash
python -c "
import os; os.environ.setdefault('GRPC_VERBOSITY', 'NONE')
# Import all modules to check for broken imports
from ui.assets import TEXTURE
from ui.styles import CSS_BASE, CSS_BOOK_BG, CSS_LANDING_BG, CSS_GAME_BG, CSS_ANALYSIS
from ui.components import blocks_html, guess_row_html, md_bold, digit_input_component
from ui.state import init_state, start_game, run_ai_step, process_user_guess
from services.llm import get_llm_analysis
from ui.pages.landing import landing_page, show_intro_dialog
from ui.pages.game import game_page
from ui.pages.reveal import reveal_page, precompute_ai_full_game, precompute_user_path_stats
print('All imports OK')
"
```
Expected output: `All imports OK`

- [ ] **Step 4: Start the app and manually verify all three pages load**

Run:
```bash
streamlit run app.py
```

Navigate to `http://localhost:8501` and verify:
- Landing page renders (parchment background, Cipher title, START GAME button)
- Clicking START GAME opens the mission briefing dialog
- Clicking Start in the dialog transitions to the game page
- The game page renders the memo pad panel and digit input grid
- Submitting a guess shows feedback rows
- Solving the code transitions to the reveal page
- The reveal page shows the win/loss banner, path toggle, and coach's notes

Stop the server with `Ctrl+C` when done.

- [ ] **Step 5: Commit**

```bash
git add app.py
git commit -m "refactor: rewrite app.py as thin 30-line router"
```
