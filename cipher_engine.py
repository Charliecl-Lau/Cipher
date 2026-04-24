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


def evaluate_logic_flags(user_guesses: list, secret: tuple):
    """
    Analyse the player's guess history for logical errors.

    Args:
        user_guesses: list of (guess_tuple, feedback_tuple) pairs
        secret: 4-tuple of unique digits

    Returns:
        A logicFlag dict with at least 'type', 'digit_involved', 'trigger_guess',
        and optionally 'wasted_guesses', or None if no errors found.
        Flags are evaluated in tier order; first triggered is returned.
    """
    n = len(user_guesses)
    if n == 0:
        return None

    # Helper: which positions in guess match secret (green positions)
    def green_positions(guess):
        return {pos: guess[pos] for pos in range(4) if guess[pos] == secret[pos]}

    # Helper: which digits in guess are in secret but at wrong position (yellow digits)
    def yellow_digits_with_slots(guess):
        secret_set = set(secret)
        return {pos: guess[pos] for pos in range(4)
                if guess[pos] in secret_set and guess[pos] != secret[pos]}

    # ── Tier 1: unforced_error_green ─────────────────────────────────────────
    for i in range(n - 1):
        g_pos = green_positions(user_guesses[i][0])
        if g_pos:
            for j in range(i + 1, n):
                later_guess = user_guesses[j][0]
                for pos, digit in g_pos.items():
                    if later_guess[pos] != digit:
                        return {
                            "type": "unforced_error_green",
                            "digit_involved": digit,
                            "trigger_guess": j + 1,
                        }

    # ── Tier 1: missed_proof ─────────────────────────────────────────────────
    for i in range(1, n - 1):
        prev_guess, prev_fb = user_guesses[i - 1]
        curr_guess, curr_fb = user_guesses[i]
        prev_total = prev_fb[0] + prev_fb[1]
        curr_total = curr_fb[0] + curr_fb[1]
        if curr_total < prev_total:
            # digits in prev not in curr were removed; if total dropped, they proved absent
            prev_set = set(prev_guess)
            curr_set = set(curr_guess)
            removed = prev_set - curr_set
            if removed:
                for k in range(i + 1, n):
                    next_guess = user_guesses[k][0]
                    next_set = set(next_guess)
                    reused = removed & next_set
                    if reused:
                        digit = next(iter(reused))
                        wasted = []
                        for m in range(i + 1, n):
                            if digit in set(user_guesses[m][0]):
                                wasted.append(m + 1)
                        return {
                            "type": "missed_proof",
                            "digit_involved": digit,
                            "trigger_guess": i + 1,
                            "wasted_guesses": wasted,
                        }

    # ── Tier 2: false_negative ───────────────────────────────────────────────
    for i in range(1, n - 1):
        prev_guess, prev_fb = user_guesses[i - 1]
        curr_guess, curr_fb = user_guesses[i]
        prev_total = prev_fb[0] + prev_fb[1]
        curr_total = curr_fb[0] + curr_fb[1]
        if curr_total > prev_total:
            # Pegs went up; intersect with secret to only flag genuinely confirmed digits
            prev_set = set(prev_guess)
            curr_set = set(curr_guess)
            added = (curr_set - prev_set) & set(secret)
            if added and i + 1 < n:
                next_guess = user_guesses[i + 1][0]
                next_set = set(next_guess)
                dropped = added - next_set
                if dropped:
                    digit = next(iter(dropped))
                    return {
                        "type": "false_negative",
                        "digit_involved": digit,
                        "trigger_guess": i + 1,  # the confirming guess (where pegs went up)
                    }

    # ── Tier 2: false_anchor ─────────────────────────────────────────────────
    secret_set = set(secret)
    for digit in range(10):
        if digit in secret_set:
            continue
        # find runs of 3+ consecutive guesses containing this dead digit
        run_start = None
        run_len = 0
        for i, (guess, _) in enumerate(user_guesses):
            if digit in guess:
                if run_len == 0:
                    run_start = i
                run_len += 1
                if run_len >= 3:
                    wasted = list(range(run_start + 1, run_start + run_len + 1))
                    return {
                        "type": "false_anchor",
                        "digit_involved": digit,
                        "trigger_guess": run_start + 1,
                        "wasted_guesses": wasted,
                    }
            else:
                run_len = 0
                run_start = None

    # ── Tier 3: repeated_slot ────────────────────────────────────────────────
    # Build map of (digit, slot) → first guess index where it was yellow
    yellow_seen: dict = {}
    for i, (guess, _) in enumerate(user_guesses):
        yw = yellow_digits_with_slots(guess)
        for pos, digit in yw.items():
            key = (digit, pos)
            if key in yellow_seen:
                return {
                    "type": "repeated_slot",
                    "digit_involved": digit,
                    "trigger_guess": i + 1,
                }
            else:
                yellow_seen[key] = i

    # ── Tier 3: dropped_yellow ───────────────────────────────────────────────
    for i in range(n - 1):
        curr_guess, curr_fb = user_guesses[i]
        g, y, _ = curr_fb
        confirmed_count = g + y  # digits confirmed in code
        if confirmed_count == 0:
            continue
        # Which specific digits are confirmed in code?
        confirmed_digits = {d for d in curr_guess if d in secret_set}
        next_guess = user_guesses[i + 1][0]
        next_set = set(next_guess)
        carried = confirmed_digits & next_set
        if len(carried) < len(confirmed_digits):
            return {
                "type": "dropped_yellow",
                "digit_involved": None,
                "trigger_guess": i + 2,
            }

    return None


def evaluate_good_logic_flags(user_guesses: list, secret: tuple):
    n = len(user_guesses)
    if n < 2:
        return None

    # smart_isolation: carries exactly 1 digit from prev guess, rest are brand new
    all_used: set = set()
    for i in range(n - 1):
        prev_set = set(user_guesses[i][0])
        curr_set = set(user_guesses[i + 1][0])
        all_used |= prev_set
        carryover = prev_set & curr_set
        if len(carryover) == 1:
            new_digits = curr_set - prev_set
            if new_digits and not (new_digits & all_used):
                digit = min(carryover)
                return {
                    "type": "smart_isolation",
                    "digit_involved": digit,
                    "trigger_guess": i + 2,
                }

    # efficient_pivot: peg count drops when digit introduced; digit gone next guess
    for i in range(1, n - 1):
        prev_guess, prev_fb = user_guesses[i - 1]
        curr_guess, curr_fb = user_guesses[i]
        next_guess = user_guesses[i + 1][0]
        prev_total = prev_fb[0] + prev_fb[1]
        curr_total = curr_fb[0] + curr_fb[1]
        if curr_total < prev_total or (prev_total == 0 and curr_total == 0):
            added = set(curr_guess) - set(prev_guess)
            dropped_next = added - set(next_guess)
            absent_from_secret = dropped_next - set(secret)
            if absent_from_secret:
                digit = min(absent_from_secret)
                return {
                    "type": "efficient_pivot",
                    "digit_involved": digit,
                    "trigger_guess": i + 1,
                }

    # perfect_lock: green digit kept in same slot every subsequent guess
    def green_positions(guess):
        return {pos: guess[pos] for pos in range(4) if guess[pos] == secret[pos]}

    for i in range(n - 1):
        g_pos = green_positions(user_guesses[i][0])
        for pos, digit in g_pos.items():
            if all(user_guesses[j][0][pos] == digit for j in range(i + 1, n)):
                return {
                    "type": "perfect_lock",
                    "digit_involved": digit,
                    "trigger_guess": i + 1,
                }

    return None


def build_llm_payload(user_path_stats: list, ai_full_path: list,
                      user_guesses=None, secret=None) -> dict:
    """
    Build the enriched JSON payload for the LLM coaching prompt.
    All structural decisions (tier, percentages, strong move, logic flags) are
    made here in Python — the LLM's only job is vocabulary and phrasing.

    Args:
        user_path_stats: list of dicts from precompute_user_path_stats(),
            each with keys: guess, feedback, cands_before, cands_after.
        ai_full_path: list of dicts from precompute_ai_full_game(),
            each with keys: guess, feedback, cands_before, cands_after, entropy.
        user_guesses: optional list of (guess_tuple, feedback_tuple) pairs.
        secret: optional tuple — the secret code.

    Returns:
        dict with keys: userStepCount, perfectStepCount, efficiencyRating,
        performanceTier, strongMove, logicFlag.
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

    # strongMove: highest eliminated_count, skipping the opening guess (guess 1)
    # so the LLM highlights a mid-game turning point, not a standard opener.
    # Fall back to all guesses only if there is just one guess total.
    post_opening = [s for s in annotated if s["guessNumber"] != 1]
    strong = max(post_opening or annotated, key=lambda s: s["eliminated_count"])

    # logicFlag: detect logical errors in the player's path (requires raw guesses + secret)
    logic_flag = None
    if user_guesses is not None and secret is not None:
        logic_flag = evaluate_logic_flags(user_guesses, secret)

    payload: dict = {
        "userStepCount":    user_steps,
        "perfectStepCount": perfect_steps,
        "efficiencyRating": efficiency,
        "performanceTier":  tier,
        "strongMove":       strong,
        "logicFlag":        logic_flag,
    }

    return payload
