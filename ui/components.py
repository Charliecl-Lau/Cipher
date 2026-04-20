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
