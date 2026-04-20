"""
Cipher Game Engine
Maximum-Entropy AI solver for 4-digit non-positional feedback game.
"""
from itertools import permutations
import numpy as np
import random

# All 5040 permutations of 4 unique digits from 0-9
ALL_PERMS = list(permutations(range(10), 4))
N = len(ALL_PERMS)  # 5040
PERM_TO_IDX = {p: i for i, p in enumerate(ALL_PERMS)}
ALL_INDICES = np.arange(N, dtype=np.int32)

def _build_feedback_table():
    perms_arr = np.array(ALL_PERMS, dtype=np.int8)  # (N, 4)

    # Greens: exact position matches
    greens = np.sum(
        perms_arr[:, None, :] == perms_arr[None, :, :],
        axis=2
    ).astype(np.int8)  # (N, N)

    # Digit membership: member[i, d] = 1 if digit d appears in ALL_PERMS[i]
    member = np.zeros((N, 10), dtype=np.int8)
    for i, p in enumerate(ALL_PERMS):
        for d in p:
            member[i, d] = 1

    # Common digits (any position)
    common = (member @ member.T).astype(np.int8)  # (N, N)
    yellows = common - greens                       # wrong-position matches

    # Encode as g*5 + y  (reds = 4 - g - y, so two values suffice)
    table = (greens * 5 + yellows).astype(np.int8)
    return table, greens, yellows

_FEEDBACK_TABLE, _GREENS_TABLE, _YELLOWS_TABLE = _build_feedback_table()

FIRST_GUESS = (0, 1, 2, 3)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_secret() -> tuple:
    """Random 4-digit sequence, no repeated digits."""
    return tuple(random.sample(range(10), 4))


def reveal_secret(secret: tuple) -> None:
    """Print the secret code to the terminal."""
    print(f"Secret code: {'-'.join(str(d) for d in secret)}")


def get_feedback(guess: tuple, secret: tuple) -> tuple:
    """Returns (greens, yellows, reds). Feedback is non-positional (counts only)."""
    gi = PERM_TO_IDX[guess]
    si = PERM_TO_IDX[secret]
    g = int(_GREENS_TABLE[gi, si])
    y = int(_YELLOWS_TABLE[gi, si])
    return (g, y, 4 - g - y)


def filter_candidates(candidates_idx: np.ndarray, guess: tuple, feedback: tuple) -> np.ndarray:
    """Keep only candidates consistent with this guess+feedback pair."""
    g, y, _ = feedback
    encoded = np.int8(g * 5 + y)
    gi = PERM_TO_IDX[guess]
    mask = _FEEDBACK_TABLE[gi, candidates_idx] == encoded
    return candidates_idx[mask]


def best_guess(candidates_idx: np.ndarray) -> tuple:
    """
    Find the guess maximising Shannon entropy over remaining candidates.
    Returns (guess_tuple, entropy_bits).
    """
    n_cands = len(candidates_idx)
    if n_cands == 0:
        return FIRST_GUESS, 0.0
    if n_cands == 1:
        return ALL_PERMS[candidates_idx[0]], 0.0

    sub = _FEEDBACK_TABLE[:, candidates_idx]  # (N, n_cands), values 0..24

    # Count occurrences of each feedback code per guess (vectorised over 25 codes)
    count = np.zeros((N, 25), dtype=np.int32)
    for f in range(25):
        count[:, f] = np.sum(sub == f, axis=1)

    # Shannon entropy H = -Σ p·log₂(p)
    probs = count / n_cands
    safe_log = np.where(probs > 0, np.log2(np.where(probs > 0, probs, 1.0)), 0.0)
    entropy = -np.sum(probs * safe_log, axis=1)  # (N,)

    # Tiebreak: slightly prefer guesses that are still valid candidates
    bonus = np.zeros(N)
    bonus[candidates_idx] = 1e-9
    best_gi = int(np.argmax(entropy + bonus))
    return ALL_PERMS[best_gi], float(entropy[best_gi])


def explain_step(step: int, guess: tuple, feedback: tuple,
                 cands_before: int, cands_after: int, entropy_bits: float) -> str:
    """Human-readable explanation of one AI move."""
    g, y, r = feedback
    gs = "-".join(str(d) for d in guess)

    if step == 1:
        method = f"Opening move — chosen to maximally partition the 5,040-possibility search space."
    else:
        method = (
            f"Selected via Maximum Entropy: this guess yields "
            f"{entropy_bits:.2f} bits of information gain."
        )

    result = (
        f"{g} correct position{'s' if g != 1 else ''}, "
        f"{y} correct digit{'s' if y != 1 else ''} wrong position, "
        f"{r} absent."
    )

    if cands_after <= 0:
        space = f"Search space: {cands_before:,} → solved."
    elif cands_after == 1:
        space = f"Search space: {cands_before:,} → 1 (secret confirmed)."
    else:
        pct = (1 - cands_after / cands_before) * 100
        space = f"Search space: {cands_before:,} → {cands_after:,} ({pct:.0f}% reduction)."

    return f"**Guess {step} ({gs}):** {method} Result: {result} {space}"


def build_llm_payload(user_path_stats: list, ai_full_path: list) -> dict:
    """
    Build the enriched JSON payload for the LLM coaching prompt.
    All structural decisions (tier, percentages, strong/weak move) are made
    here in Python — the LLM's only job is vocabulary and phrasing.

    Args:
        user_path_stats: list of dicts from precompute_user_path_stats(),
            each with keys: guess, feedback, cands_before, cands_after.
        ai_full_path: list of dicts from precompute_ai_full_game(),
            each with keys: guess, feedback, cands_before, cands_after, entropy.

    Returns:
        dict with keys: userStepCount, perfectStepCount, efficiencyRating,
        performanceTier, strongMove, and optionally struggleMove.
    """
    user_steps    = len(user_path_stats)
    perfect_steps = len(ai_full_path)
    delta         = user_steps - perfect_steps

    if delta <= 1:
        tier = "efficient"
    elif delta <= 3:
        tier = "average"
    else:
        tier = "struggling"

    efficiency = round(perfect_steps / user_steps * 100) if user_steps > 0 else 100

    # Annotate each step with eliminated count and percentage of total space
    annotated = [
        {
            "guessNumber":      i + 1,
            "guess":            "-".join(str(d) for d in s["guess"]),
            "eliminated_count": s["cands_before"] - s["cands_after"],
            "eliminated_pct":   round((s["cands_before"] - s["cands_after"]) / 5040 * 100),
        }
        for i, s in enumerate(user_path_stats)
    ]

    # strongMove: highest eliminated_count across all guesses
    strong = max(annotated, key=lambda s: s["eliminated_count"])

    # struggleMove: lowest eliminated_count among non-final guesses that are
    # not the same step as strongMove (avoid double-counting short games)
    non_final_excl_strong = [
        s for s in annotated[:-1]
        if s["guessNumber"] != strong["guessNumber"]
    ]
    struggle = (
        min(non_final_excl_strong, key=lambda s: s["eliminated_count"])
        if non_final_excl_strong
        else None
    )

    payload: dict = {
        "userStepCount":    user_steps,
        "perfectStepCount": perfect_steps,
        "efficiencyRating": efficiency,
        "performanceTier":  tier,
        "strongMove":       strong,
    }
    if struggle:
        payload["struggleMove"] = struggle

    return payload
