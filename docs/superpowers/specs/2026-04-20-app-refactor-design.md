# app.py Refactor — Design Spec

**Date:** 2026-04-20
**Status:** Approved

## Problem

`app.py` is 1,700 lines mixing CSS strings, HTML/JS components, session state logic, page rendering, and an external API call. It is hard to navigate, hard to hand off to a collaborator, and contains at least one silent bug (duplicate `CSS_ANALYSIS` definition where the first is overridden).

## Goal

Split `app.py` into focused modules — each with one clear responsibility — without changing any behaviour visible to the user or breaking any tests.

## Approach

Pragmatic split (Approach 2): 9 files, each under ~150 lines. CSS stays as Python string constants (not external `.css` files) to preserve f-string image URL embedding. Pages use a nested `ui/pages/` package. LLM logic lives in a dedicated `services/` layer.

## File Structure

```
Cipher/
├── app.py                    # ~30 lines — page config, imports, routing only
├── cipher_engine.py          # unchanged
├── services/
│   ├── __init__.py
│   └── llm.py                # get_llm_analysis() — Gemini API call, caching, prompt
├── ui/
│   ├── __init__.py
│   ├── assets.py             # _b64() loader + image constants (TEXTURE, GREEN_PAINT, etc.)
│   ├── styles.py             # CSS_BASE, CSS_BOOK_BG, CSS_LANDING_BG, CSS_GAME_BG, CSS_ANALYSIS
│   ├── components.py         # blocks_html(), guess_row_html(), md_bold(),
│   │                         # digit_input_component(), js_input_validate()
│   ├── state.py              # init_state(), start_game(), run_ai_step(), process_user_guess()
│   └── pages/
│       ├── __init__.py
│       ├── landing.py        # landing_page(), show_intro_dialog()
│       ├── game.py           # game_page()
│       └── reveal.py         # reveal_page(), precompute_ai_full_game(),
│                             #               precompute_user_path_stats()
└── tests/                    # unchanged
```

## Estimated Line Counts

| File | ~Lines |
|---|---|
| `app.py` | 30 |
| `ui/assets.py` | 15 |
| `ui/styles.py` | 420 |
| `ui/components.py` | 130 |
| `ui/state.py` | 80 |
| `ui/pages/landing.py` | 80 |
| `ui/pages/game.py` | 60 |
| `ui/pages/reveal.py` | 130 |
| `services/llm.py` | 80 |

## Dependency Direction

Dependencies flow in one direction only — no circular imports:

```
cipher_engine.py
      ↓
ui/assets.py
      ↓
ui/styles.py          (imports assets for image URL f-strings)
ui/components.py      (imports assets for image URLs in blocks_html)
      ↓
ui/state.py           (imports cipher_engine)
services/llm.py       (imports cipher_engine.build_llm_payload, reads st.session_state)
      ↓
ui/pages/landing.py   (imports styles, components, state)
ui/pages/game.py      (imports styles, components, state)
ui/pages/reveal.py    (imports styles, components, state, services.llm)
      ↓
app.py                (imports pages, calls init_state + routes)
```

## Session State

All state remains in `st.session_state`. No shared mutable objects are passed between modules. `services/llm.py` reads `user_path_stats` and `ai_full_path` directly from `st.session_state`, matching the current pattern.

## Bug Fix Included

`CSS_ANALYSIS` is currently defined twice in `app.py` (lines 709–731 and lines 855–978). The first definition is silently overridden. The refactor removes the dead first definition and keeps only the complete second definition in `ui/styles.py`.

## What Does NOT Change

- All function signatures and logic
- `cipher_engine.py` — untouched
- `tests/` — untouched
- Session state keys and structure
- User-visible behaviour

## Migration Order

Each step leaves the app in a runnable state:

1. Create `ui/assets.py` — move `_b64()` and image constants
2. Create `ui/styles.py` — move all CSS constants, remove duplicate `CSS_ANALYSIS`
3. Create `ui/components.py` — move HTML/JS helpers
4. Create `ui/state.py` — move state management functions
5. Create `services/llm.py` — move `get_llm_analysis`
6. Create `ui/pages/landing.py` — move `landing_page`, `show_intro_dialog`
7. Create `ui/pages/game.py` — move `game_page`
8. Create `ui/pages/reveal.py` — move `reveal_page`, `precompute_*`
9. Rewrite `app.py` to thin router (~30 lines)
10. Verify app runs and no tests are broken
