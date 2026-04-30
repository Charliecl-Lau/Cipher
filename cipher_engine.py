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
                # Grace period: do not fire if green established in guess 1 and
                # the drop occurs in guess 2 (i==0, j==1). Wait until guess 3+.
                if i == 0 and j == 1:
                    continue
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


def compute_yellow_analysis(user_guesses: list, secret: tuple) -> dict:
    """
    Analyse the player's handling of yellow (correct digit, wrong position) feedback.

    Returns a dict with statistics and a plain-English summary about how well the
    player tracked and acted on yellow peg information throughout the game.
    """
    n = len(user_guesses)
    secret_set = set(secret)

    # More precise: position-aware yellow digits
    def yellow_digit_slot_map(guess):
        """Return {digit: pos} for digits that are in secret but at wrong position."""
        return {guess[pos]: pos for pos in range(4)
                if guess[pos] in secret_set and guess[pos] != secret[pos]}

    # earlyYellowGuesses: 1-indexed guess numbers (among first 3) with yellow pegs
    early_yellow_guesses = [
        i + 1
        for i in range(min(3, n))
        if user_guesses[i][1][1] > 0
    ]

    # totalYellowFeedback
    total_yellow_feedback = sum(fb[1] for _, fb in user_guesses)

    # droppedAfterYellow: for each guess i with yellows, check what yellow-confirmed
    # digits were absent from guess i+1
    dropped_after_yellow = []
    for i in range(n - 1):
        guess_i, fb_i = user_guesses[i]
        if fb_i[1] == 0:
            continue
        yellow_confirmed = set(yellow_digit_slot_map(guess_i).keys())
        next_guess = set(user_guesses[i + 1][0])
        dropped = sorted(yellow_confirmed - next_guess)
        if dropped:
            dropped_after_yellow.append({
                "guess": i + 1,
                "digitsDropped": dropped,
                "yellowPegsThatGuess": fb_i[1],
            })

    missed_carry_forward = len(dropped_after_yellow) > 0

    # repeatedYellowTesting: same (digit, slot) appeared as yellow in more than one guess
    yellow_seen: dict = {}
    repeated_yellow_testing = False
    for i, (guess, _) in enumerate(user_guesses):
        for pos in range(4):
            d = guess[pos]
            if d in secret_set and d != secret[pos]:
                key = (d, pos)
                if key in yellow_seen:
                    repeated_yellow_testing = True
                    break
                yellow_seen[key] = i
        if repeated_yellow_testing:
            break

    # confirmedDigitsByEnd: digits in final guess that are in secret
    final_guess = set(user_guesses[-1][0]) if n > 0 else set()
    confirmed_digits_by_end = sorted(final_guess & secret_set)

    wasted_guesses_on_yellow = len(dropped_after_yellow)

    # summary
    if missed_carry_forward and early_yellow_guesses:
        early_str = ", ".join(str(g) for g in early_yellow_guesses)
        summary = (
            f"Player got yellow feedback in guess {early_str} but dropped a "
            f"yellow-confirmed digit in the next guess, making it harder to track "
            f"which digits belonged in the code."
        )
    elif repeated_yellow_testing:
        summary = "Player re-tested a yellow digit in the same slot it was already proven wrong."
    else:
        summary = "Player managed yellow feedback consistently across the game."

    return {
        "earlyYellowGuesses":    early_yellow_guesses,
        "totalYellowFeedback":   total_yellow_feedback,
        "droppedAfterYellow":    dropped_after_yellow,
        "missedCarryForward":    missed_carry_forward,
        "repeatedYellowTesting": repeated_yellow_testing,
        "confirmedDigitsByEnd":  confirmed_digits_by_end,
        "wastedGuessesOnYellow": wasted_guesses_on_yellow,
        "summary":               summary,
    }


def compute_key_moments(user_guesses: list, secret: tuple) -> list:
    """
    Identify 2–3 significant moments in the player's game.

    Returns a list of dicts each with keys: guess (1-indexed), action, pegChange.
    Moments are selected by: always including guess 1, any guess where the total
    peg count changed by 2+, and any guess where yellows appeared for the first time.
    The list is capped at 3 entries.
    """
    n = len(user_guesses)
    if n == 0:
        return []

    secret_set = set(secret)

    def peg_total(fb):
        return fb[0] + fb[1]

    def format_peg_change(fb):
        g, y, _ = fb
        if g == 0 and y == 0:
            return "0 pegs"
        if g > 0 and y > 0:
            return f"{g} green, {y} yellow"
        if g > 0:
            return f"{g} green"
        return f"{y} yellow"

    def derive_action(i):
        """Derive a human-readable action description for guess i."""
        guess_i = set(user_guesses[i][0])
        fb_i = user_guesses[i][1]
        if i == 0:
            return "introduced new digits"
        prev_guess = set(user_guesses[i - 1][0])
        prev_fb = user_guesses[i - 1][1]
        added = guess_i - prev_guess
        removed = prev_guess - guess_i
        prev_yellows = {d for d in user_guesses[i - 1][0]
                        if d in secret_set and user_guesses[i - 1][0][list(user_guesses[i - 1][0]).index(d)] != secret[list(user_guesses[i - 1][0]).index(d)]}
        yellow_confirmed = prev_yellows

        if len(guess_i) == 4 and len(added) == 4:
            return "changed all digits"
        if prev_fb[1] > 0 and len(removed & yellow_confirmed) >= 2:
            return "dropped multiple digits after yellow"
        if prev_fb[1] > 0 and not (removed & yellow_confirmed):
            return "kept all yellow candidates"
        if fb_i[0] > prev_fb[0]:
            return "locked in green digit"
        return "introduced new digits"

    moments = []
    yellow_first_seen = False

    for i in range(n):
        fb_i = user_guesses[i][1]
        is_first = (i == 0)
        peg_change_big = False
        yellow_first_now = False

        if i > 0:
            prev_total = peg_total(user_guesses[i - 1][1])
            curr_total = peg_total(fb_i)
            peg_change_big = abs(curr_total - prev_total) >= 2

        if fb_i[1] > 0 and not yellow_first_seen:
            yellow_first_now = True
            yellow_first_seen = True

        if is_first or peg_change_big or yellow_first_now:
            moments.append({
                "guess":     i + 1,
                "action":    derive_action(i),
                "pegChange": format_peg_change(fb_i),
            })

        if len(moments) >= 3:
            break

    return moments


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
        dict with keys: userStepCount, perfectStepCount, goodLogicFlag, logicFlag,
        yellowAnalysis, keyMoments.
    """
    user_steps    = len(user_path_stats)
    perfect_steps = len(ai_full_path)

    logic_flag      = None
    good_logic_flag = None
    yellow_analysis = None
    key_moments     = None
    if user_guesses is not None and secret is not None:
        logic_flag      = evaluate_logic_flags(user_guesses, secret)
        good_logic_flag = evaluate_good_logic_flags(user_guesses, secret)
        yellow_analysis = compute_yellow_analysis(user_guesses, secret)
        key_moments     = compute_key_moments(user_guesses, secret)

    return {
        "userStepCount":    user_steps,
        "perfectStepCount": perfect_steps,
        "goodLogicFlag":    good_logic_flag,
        "logicFlag":        logic_flag,
        "yellowAnalysis":   yellow_analysis,
        "keyMoments":       key_moments,
    }
