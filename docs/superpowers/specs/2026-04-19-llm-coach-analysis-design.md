# LLM Coach Analysis — Upgraded Design

**Date:** 2026-04-19  
**Status:** Approved  
**Files affected:** `app.py`

---

## Overview

Upgrade the existing Gemini-powered "Coach's Notes" panel on the reveal page. The goal is to make the LLM's only job vocabulary and phrasing — every structural decision (tier, percentages, strong/weak move identification) is made in Python before the API call.

The output schema changes from `{"headline", "body"}` (a paragraph) to `{"headline", "bullets": [str, str, str]}` (three numbered lines).

---

## Data Layer

### `precompute_user_path_stats()` (new)

Mirrors `precompute_ai_full_game()`. Replays `st.session_state.user_guesses` through `filter_candidates`, computing `cands_before` and `cands_after` for each user guess.

Returns a list of dicts:
```python
[
    {
        "guess": tuple,
        "feedback": tuple,
        "cands_before": int,
        "cands_after": int,
    },
    ...
]
```

Cached in `session_state["user_path_stats"]`. Called once at the top of `reveal_page()`.

Cache cleared in `start_game()` alongside `ai_full_path` and `llm_analysis`.

### `_build_llm_payload(user_path_stats, ai_full_path)` (new private helper)

Pure function — no session state access. Returns an enriched dict ready to serialise as the LLM data block.

**Fields computed:**

| Field | Formula |
|---|---|
| `userStepCount` | `len(user_path_stats)` |
| `perfectStepCount` | `len(ai_full_path)` |
| `efficiencyRating` | `round(perfect / user * 100)` |
| `performanceTier` | `"efficient"` if delta ≤ 1, `"average"` if delta ≤ 3, `"struggling"` otherwise |
| `strongMove` | User guess with highest `cands_before − cands_after`, plus `eliminated_pct = round(eliminated / 5040 * 100)` |
| `struggleMove` | User guess with lowest `cands_before − cands_after`, **excluding the final solving guess**, plus `eliminated_pct` |

`strongMove` and `struggleMove` each have the shape:
```python
{
    "guessNumber": int,       # 1-indexed position in user's sequence
    "guess": str,             # e.g. "5-2-9-0"
    "eliminated_count": int,
    "eliminated_pct": int,
}
```

Edge cases:
- If the user solves in 1 guess, `struggleMove` is omitted and Bullet 2 is replaced with a compliment in the prompt task.
- If `strongMove` and `struggleMove` resolve to the same guess index (e.g. 2-guess solve where both criteria point to guess 1), `struggleMove` is omitted.

---

## Prompt and API Layer

`get_llm_analysis()` restructured — same Gemini API (`gemma-3-27b-it`), same caching pattern, internals replaced.

### System prompt structure

Four labeled blocks:

```
[ROLE]
You are a sharp, friendly game coach analysing a code-breaking puzzle. Speak like a person, not a textbook.

[RULES]
- Never use: entropy, minimax, algorithm, search space, heuristic, optimal
- Use instead: ruled out, narrowed down, options left, possibilities
- Each bullet must be under 20 words
- Return ONLY a raw JSON object: {"headline": string, "bullets": [string, string, string]}
- The very first character of your response must be {

[DATA]
{serialised payload as JSON}

[TASK]
Write a headline (3–7 words) and exactly 3 bullets:
  Bullet 1 → strongMove highlight
  Bullet 2 → struggleMove critique
  Bullet 3 → performanceTier-calibrated takeaway:
    efficient  → open with a compliment, give one sharpening tip
    average    → encouraging but direct, name one habit to build
    struggling → honest but kind, name one thing costing them turns
```

### Defensive parsing

Strip markdown fences before `json.loads`:
```python
raw = response.text.strip()
raw = re.sub(r"^```(?:json)?\s*", "", raw)
raw = re.sub(r"\s*```$", "", raw.strip())
data = json.loads(raw)
```

### Post-parse validation

```python
assert isinstance(data["headline"], str) and 3 <= len(data["headline"].split()) <= 7
assert len(data["bullets"]) == 3
assert all(len(b.split()) <= 22 for b in data["bullets"])
```

If any assertion fails (or `json.loads` raises), fall back to a plain templated dict using `performanceTier` and step counts — never show a broken response to the user.

Fallback shape:
```python
{
    "headline": "Analysis unavailable",
    "bullets": [
        f"You solved it in {user_steps} guesses.",
        f"The perfect path was {perfect_steps} guesses.",
        "Try again to see a detailed breakdown.",
    ]
}
```

---

## Render Layer

### CSS addition to `CSS_ANALYSIS`

New `.analysis-bullet` class — same Caveat font and `1.55rem` size as `.analysis-body`, with `margin-bottom: 0.75rem` between bullets.

### Reveal page render (right column)

```html
<div class="analysis-headline fade-in">{headline}</div>
<div class="analysis-bullet fade-in">1. {bullets[0]}</div>
<div class="analysis-bullet fade-in">2. {bullets[1]}</div>
<div class="analysis-bullet fade-in">3. {bullets[2]}</div>
```

`precompute_user_path_stats()` called at the top of `reveal_page()` alongside `precompute_ai_full_game()`. The result is read from `session_state["user_path_stats"]` inside `get_llm_analysis()` via `_build_llm_payload()`.

---

## Summary of changes

| Layer | Before | After |
|---|---|---|
| JSON safety | regex fence strip only | fence strip + first-char constraint in prompt + post-parse assertions |
| Move context | none | count + percentage of 5040 total possibilities |
| Bullet 3 tone | generic advice | tier-gated (efficient / average / struggling) |
| Prompt structure | mixed blob | `[ROLE]` / `[RULES]` / `[DATA]` / `[TASK]` |
| Output schema | `{"headline", "body"}` | `{"headline", "bullets": [str, str, str]}` |
| Output validation | none | assertion schema with templated fallback |
| Render | single paragraph | three numbered bullet divs |
