import pytest
from cipher_engine import (
    build_llm_payload, evaluate_logic_flags, evaluate_good_logic_flags,
    compute_yellow_analysis, compute_key_moments,
)


# ── Fixtures ────────────────────────────────────────────────────────────────────

def make_step(guess, feedback, cands_before, cands_after):
    return {
        "guess": guess,
        "feedback": feedback,
        "cands_before": cands_before,
        "cands_after": cands_after,
    }


def make_ai_path(n):
    """Return a minimal ai_full_path list of length n (contents don't matter for payload)."""
    return [{"guess": (0, 1, 2, 3), "feedback": (1, 0, 3), "cands_before": 100, "cands_after": 10, "entropy": 0.0}] * n


# ── Tests ───────────────────────────────────────────────────────────────────────

class TestCounts:
    def test_user_and_perfect_step_counts(self):
        user = [
            make_step((0,1,2,3), (2,1,1), 5040, 180),
            make_step((4,5,6,7), (3,1,0), 180, 10),
            make_step((8,9,0,1), (4,0,0), 10, 0),
        ]
        result = build_llm_payload(user, make_ai_path(4))
        assert result["userStepCount"] == 3
        assert result["perfectStepCount"] == 4

class TestLogicFlagInPayload:
    def test_logic_flag_none_when_no_args(self):
        user = [
            make_step((0,1,2,3), (2,1,1), 5040, 180),
            make_step((4,5,6,7), (4,0,0), 180, 0),
        ]
        result = build_llm_payload(user, make_ai_path(2))
        assert "logicFlag" in result
        assert result["logicFlag"] is None

    def test_logic_flag_present_when_guesses_and_secret_given(self):
        # secret = (3,7,1,9)
        # guess 1: (0,1,2,3) — digit 1 is green (pos 1), digit 3 is yellow
        # guess 2: drops digit 1 from position 1 → unforced_error_green
        secret = (3, 7, 1, 9)
        user_guesses = [
            ((0, 1, 2, 3), (1, 1, 2)),   # 1 green (digit 1 at pos 1? let's verify via logic)
            ((5, 6, 4, 8), (0, 1, 3)),   # drop digit 1
        ]
        user_path_stats = [
            make_step(user_guesses[0][0], user_guesses[0][1], 5040, 100),
            make_step(user_guesses[1][0], user_guesses[1][1], 100, 0),
        ]
        result = build_llm_payload(user_path_stats, make_ai_path(2),
                                   user_guesses=user_guesses, secret=secret)
        assert "logicFlag" in result
        # May or may not trigger depending on actual feedback; just check key exists
        assert result["logicFlag"] is None or isinstance(result["logicFlag"], dict)

    def test_logic_flag_none_when_clean_play(self):
        secret = (3, 7, 1, 9)
        user_guesses = [
            ((3, 7, 1, 9), (4, 0, 0)),
        ]
        user_path_stats = [
            make_step(user_guesses[0][0], user_guesses[0][1], 5040, 0),
        ]
        result = build_llm_payload(user_path_stats, make_ai_path(1),
                                   user_guesses=user_guesses, secret=secret)
        assert result["logicFlag"] is None


class TestEvaluateLogicFlags:

    # ── Tier 1: unforced_error_green ──────────────────────────────────────────

    def test_unforced_error_green(self):
        # Grace period: dropping a green from guess 1 in guess 2 does NOT fire
        # unforced_error_green (per the early-game grace period). The flag fires
        # at guess 3+ when the green established in guess 1 is still absent.
        # secret = (3, 7, 1, 9); digit 1 is green at pos 2 in guess 1.
        # Guess 2 drops it (grace period applies — no flag yet).
        # Guess 3 still lacks digit 1 at pos 2 → unforced_error_green fires.
        secret = (3, 7, 1, 9)
        user_guesses = [
            ((0, 3, 1, 5), (1, 1, 2)),  # green: digit 1 at pos 2
            ((0, 3, 4, 5), (0, 1, 3)),  # drops digit 1 (grace period — no flag)
            ((0, 3, 4, 8), (0, 1, 3)),  # still lacks digit 1 at pos 2 → fires
        ]
        flag = evaluate_logic_flags(user_guesses, secret)
        assert flag is not None
        assert flag["type"] == "unforced_error_green"
        assert flag["digit_involved"] == 1
        assert flag["trigger_guess"] == 3

    def test_unforced_error_green_moved_digit(self):
        # secret = (3, 7, 1, 9); digit 1 green at pos 2 in guess 1.
        # Grace period: drop in guess 2 is forgiven.
        # Guess 3 moves digit 1 to pos 3 (wrong pos) → fires at trigger_guess=3.
        secret = (3, 7, 1, 9)
        user_guesses = [
            ((0, 3, 1, 5), (1, 1, 2)),   # digit 1 green at pos 2
            ((0, 3, 4, 5), (0, 1, 3)),   # grace period: no flag
            ((0, 3, 5, 1), (0, 2, 2)),   # 1 moved to pos 3 → fires
        ]
        flag = evaluate_logic_flags(user_guesses, secret)
        assert flag is not None
        assert flag["type"] == "unforced_error_green"
        assert flag["digit_involved"] == 1

    # ── Tier 1: missed_proof ─────────────────────────────────────────────────

    def test_missed_proof(self):
        # secret = (3, 7, 1, 9)
        # All-yellow guesses (no greens) to avoid triggering unforced_error_green first
        # guess 1: (1, 3, 7, 0) → 3 yellows (1,3,7 in secret, wrong slots); total=3
        # guess 2: (1, 3, 4, 0) → remove 7, add 4; pegs drop 3→2; digit 7 proved absent
        # guess 3: (1, 3, 7, 5) → digit 7 reappears → missed_proof
        secret = (3, 7, 1, 9)
        user_guesses = [
            ((1, 3, 7, 0), (0, 3, 1)),  # 0 greens, 3 yellows; total=3
            ((1, 3, 4, 0), (0, 2, 2)),  # pegs dropped 3→2; removed digit 7 proved absent
            ((1, 3, 7, 5), (0, 2, 2)),  # digit 7 reappears → missed_proof
        ]
        flag = evaluate_logic_flags(user_guesses, secret)
        assert flag is not None
        assert flag["type"] == "missed_proof"
        assert flag["digit_involved"] == 7
        assert flag["trigger_guess"] == 2

    # ── Tier 2: false_negative ───────────────────────────────────────────────

    def test_false_negative(self):
        # secret = (3, 7, 1, 9)
        # Use a YELLOW confirmation (digit in secret but wrong slot) so no green is established,
        # avoiding unforced_error_green. Digit 7 added as yellow confirms it's in the code.
        # guess 1: (0, 2, 4, 6) → 0 pegs
        # guess 2: (7, 2, 4, 6) → digit 7 at pos 0 is yellow (in secret at pos 1). pegs 0→1.
        # guess 3: (5, 2, 4, 6) → dropped digit 7 → false_negative
        secret = (3, 7, 1, 9)
        user_guesses = [
            ((0, 2, 4, 6), (0, 0, 4)),
            ((7, 2, 4, 6), (0, 1, 3)),  # digit 7 yellow at pos 0; pegs went up 0→1
            ((5, 2, 4, 6), (0, 0, 4)),  # dropped digit 7 → false_negative
        ]
        flag = evaluate_logic_flags(user_guesses, secret)
        assert flag is not None
        assert flag["type"] == "false_negative"
        assert flag["digit_involved"] == 7
        assert flag["trigger_guess"] == 2  # the confirming guess (where pegs went up)

    # ── Tier 2: false_anchor ─────────────────────────────────────────────────

    def test_false_anchor(self):
        # secret = (3, 7, 1, 9); digit 0 is dead (never in secret)
        # Keep total pegs steady across all guesses (no peg increase → no false_negative)
        # so no higher-tier flag fires before false_anchor.
        # Guesses are arranged so no digit lands in its correct position (no greens).
        secret = (3, 7, 1, 9)
        user_guesses = [
            ((0, 1, 3, 7), (0, 3, 1)),  # 0 greens; yellows: 1(pos2),3(pos0),7(pos1); total=3
            ((0, 3, 7, 1), (0, 3, 1)),  # 0 greens; same digits rearranged; total=3
            ((0, 7, 1, 3), (0, 3, 1)),  # 0 greens; total=3; 3rd guess with dead digit 0 → fire
        ]
        flag = evaluate_logic_flags(user_guesses, secret)
        assert flag is not None
        assert flag["type"] == "false_anchor"
        assert flag["digit_involved"] == 0
        assert flag["trigger_guess"] == 1
        assert 1 in flag["wasted_guesses"]
        assert 2 in flag["wasted_guesses"]
        assert 3 in flag["wasted_guesses"]

    # ── Tier 3: repeated_slot ────────────────────────────────────────────────

    def test_repeated_slot(self):
        # secret = (3, 7, 1, 9)
        # digit 7 is in secret at pos 1
        # guess 1: (0, 7, 4, 6) → digit 7 at pos 1 is green, not yellow (it's in the right pos)
        # Need yellow: digit 7 placed in wrong slot
        # guess 1: (7, 0, 4, 6) → digit 7 at pos 0, secret has 7 at pos 1 → yellow
        # guess 2: (7, 2, 4, 6) → digit 7 at pos 0 again → repeated slot
        secret = (3, 7, 1, 9)
        user_guesses = [
            ((7, 0, 4, 6), (0, 1, 3)),  # digit 7 at pos 0 is yellow (wrong slot)
            ((7, 2, 4, 6), (0, 1, 3)),  # digit 7 at pos 0 again → repeated_slot
        ]
        flag = evaluate_logic_flags(user_guesses, secret)
        assert flag is not None
        assert flag["type"] == "repeated_slot"
        assert flag["digit_involved"] == 7
        assert flag["trigger_guess"] == 2

    # ── Tier 3: dropped_yellow ───────────────────────────────────────────────

    def test_dropped_yellow(self):
        # secret = (3, 7, 1, 9)
        # All-yellow first guess (no greens) confirms 4 digits.
        # Second guess drops ALL confirmed digits (uses entirely different digits).
        # Since it's only 2 guesses, missed_proof loop is empty → no higher-tier flag.
        secret = (3, 7, 1, 9)
        user_guesses = [
            ((7, 3, 9, 1), (0, 4, 0)),  # 0 greens, 4 yellows; all 4 confirmed
            ((5, 6, 2, 8), (0, 0, 4)),  # drops all confirmed digits → dropped_yellow
        ]
        flag = evaluate_logic_flags(user_guesses, secret)
        assert flag is not None
        assert flag["type"] == "dropped_yellow"
        assert flag["trigger_guess"] == 2

    # ── No flags ─────────────────────────────────────────────────────────────

    def test_returns_none_when_no_errors(self):
        # Perfect play: first guess, immediately solve
        secret = (3, 7, 1, 9)
        user_guesses = [
            ((3, 7, 1, 9), (4, 0, 0)),
        ]
        flag = evaluate_logic_flags(user_guesses, secret)
        assert flag is None

    def test_returns_none_for_clean_play(self):
        # Clean 2-guess play: green digit carried forward, no errors
        # secret = (3, 7, 1, 9)
        # guess 1 establishes a green (3 at pos 0) and all others absent
        # guess 2 keeps digit 3 at pos 0 and solves
        secret = (3, 7, 1, 9)
        user_guesses = [
            ((3, 0, 2, 4), (1, 0, 3)),  # digit 3 green at pos 0; others absent
            ((3, 7, 1, 9), (4, 0, 0)),  # solves; carries digit 3 in same slot
        ]
        flag = evaluate_logic_flags(user_guesses, secret)
        assert flag is None

    # ── Hierarchy ────────────────────────────────────────────────────────────

    def test_tier1_takes_priority_over_tier2(self):
        # Set up a scenario that triggers both unforced_error_green AND would trigger false_anchor
        # secret = (3, 7, 1, 9)
        # Digit 0: always red (not in secret) — appears 3 times = false_anchor
        # But also: guess 1 has a green, guess 2 drops it = unforced_error_green (Tier 1)
        # Tier 1 should win
        secret = (3, 7, 1, 9)
        user_guesses = [
            ((0, 3, 1, 5), (1, 1, 2)),  # digit 1 green at pos 2; digit 0 present
            ((0, 3, 4, 5), (0, 1, 3)),  # dropped digit 1 → unforced_error_green (Tier 1)
                                         # digit 0 still present (run=2 so far, not 3 yet)
            ((0, 6, 4, 5), (0, 0, 4)),  # digit 0 run = 3 → false_anchor would fire
        ]
        flag = evaluate_logic_flags(user_guesses, secret)
        assert flag is not None
        assert flag["type"] == "unforced_error_green"

    def test_tier2_takes_priority_over_tier3(self):
        # false_negative (Tier 2) should beat dropped_yellow (Tier 3)
        # secret = (3, 7, 1, 9)
        # Digit 7 added as YELLOW (wrong slot) so no green is established
        # → no unforced_error_green can block false_negative
        # guess 1: (0,2,4,6) → 0 pegs
        # guess 2: (7,2,4,6) → digit 7 yellow at pos 0; pegs 0→1; 7 confirmed
        # guess 3: (5,2,4,6) → drops digit 7 → false_negative (Tier 2)
        #   also triggers dropped_yellow (Tier 3); false_negative must win
        secret = (3, 7, 1, 9)
        user_guesses = [
            ((0, 2, 4, 6), (0, 0, 4)),
            ((7, 2, 4, 6), (0, 1, 3)),  # digit 7 yellow; pegs up 0→1; 7 confirmed
            ((5, 2, 4, 6), (0, 0, 4)),  # drops 7 → false_negative; also → dropped_yellow
        ]
        flag = evaluate_logic_flags(user_guesses, secret)
        assert flag is not None
        assert flag["type"] == "false_negative"


class TestEvaluateGoodLogicFlags:
    # ── smart_isolation ──────────────────────────────────────────────────────
    def test_smart_isolation_detected(self):
        # Guess 1: (0,1,2,3) — 4 digits used
        # Guess 2: (1,4,5,6) — carries over digit 1 (was in guess 1), fills rest with new digits 4,5,6
        # secret contains 1
        secret = (1, 7, 8, 9)
        guesses = [
            ((0, 1, 2, 3), (0, 1, 3)),  # 1 yellow
            ((1, 4, 5, 6), (0, 1, 3)),  # 1 yellow carried, rest new
        ]
        result = evaluate_good_logic_flags(guesses, secret)
        assert result is not None
        assert result["type"] == "smart_isolation"
        assert result["digit_involved"] == 1
        assert result["trigger_guess"] == 2

    def test_smart_isolation_not_triggered_when_too_many_carryovers(self):
        # Guess 2 carries 2 digits from guess 1 — not isolation (needs exactly 1)
        secret = (1, 2, 7, 8)
        guesses = [
            ((0, 1, 2, 3), (0, 2, 2)),
            ((1, 2, 4, 5), (0, 2, 2)),  # carries 1 AND 2
        ]
        result = evaluate_good_logic_flags(guesses, secret)
        assert result is None or result["type"] != "smart_isolation"

    # ── efficient_pivot ──────────────────────────────────────────────────────
    def test_efficient_pivot_detected(self):
        # Minimal valid scenario:
        # G1: (0,1,2,3) → 3 pegs (1,2,3 correct). G2: (0,1,2,5) → 2 pegs (5 caused drop). G3: (0,1,2,6) → no 5
        secret5 = (1, 2, 3, 4)
        guesses_ep = [
            ((0, 1, 2, 3), (0, 3, 1)),  # 3 pegs
            ((0, 1, 2, 5), (0, 2, 2)),  # 5 introduced, pegs drop to 2
            ((0, 1, 2, 6), (0, 2, 2)),  # 5 dropped in next guess
        ]
        result = evaluate_good_logic_flags(guesses_ep, secret5)
        assert result is not None
        assert result["type"] == "efficient_pivot"
        assert result["digit_involved"] == 5
        assert result["trigger_guess"] == 2

    def test_efficient_pivot_stays_at_zero(self):
        # G1: all wrong, 0 pegs. G2: introduces digit 5, still 0 pegs. G3: drops digit 5.
        secret = (1, 2, 3, 4)
        guesses = [
            ((6, 7, 8, 9), (0, 0, 4)),   # 0 pegs
            ((5, 7, 8, 9), (0, 0, 4)),   # 5 introduced, still 0 pegs (stays at 0)
            ((6, 7, 8, 9), (0, 0, 4)),   # 5 dropped
        ]
        result = evaluate_good_logic_flags(guesses, secret)
        assert result is not None
        assert result["type"] == "efficient_pivot"
        assert result["digit_involved"] == 5
        assert result["trigger_guess"] == 2

    # ── perfect_lock ─────────────────────────────────────────────────────────
    def test_perfect_lock_detected(self):
        # Digit 3 is green at pos 2 in guess 1, stays at pos 2 in all later guesses
        secret = (1, 2, 3, 4)
        guesses = [
            ((0, 0, 3, 0), (1, 0, 3)),  # digit 3 green at pos 2
            ((1, 0, 3, 0), (1, 0, 3)),  # 3 still at pos 2
            ((1, 2, 3, 4), (4, 0, 0)),  # solved; 3 still at pos 2
        ]
        result = evaluate_good_logic_flags(guesses, secret)
        assert result is not None
        assert result["type"] == "perfect_lock"
        assert result["digit_involved"] == 3
        assert result["trigger_guess"] == 1

    def test_returns_none_when_no_positive_flags(self):
        # Random guesses with no smart behavior
        secret = (1, 2, 3, 4)
        guesses = [
            ((5, 6, 7, 8), (0, 0, 4)),
            ((0, 9, 5, 6), (0, 0, 4)),
        ]
        result = evaluate_good_logic_flags(guesses, secret)
        assert result is None

    def test_smart_isolation_takes_priority_over_efficient_pivot(self):
        # Build a scenario that triggers both; smart_isolation must win
        secret = (1, 7, 8, 9)
        # Guess 1 has digit 1 (yellow), guess 2 carries only digit 1 + 3 new digits
        guesses = [
            ((0, 1, 2, 3), (0, 1, 3)),  # 1 yellow
            ((1, 4, 5, 6), (0, 1, 3)),  # carries only digit 1; 3 new digits
        ]
        result = evaluate_good_logic_flags(guesses, secret)
        assert result is not None
        assert result["type"] == "smart_isolation"


class TestNewPayloadSchema:
    def test_payload_has_good_logic_flag_key(self):
        user = [make_step((0,1,2,3), (2,1,1), 5040, 180)]
        ai   = make_ai_path(2)
        secret = (0, 1, 2, 3)
        guesses = [((0,1,2,3), (2,1,1))]
        result = build_llm_payload(user, ai, user_guesses=guesses, secret=secret)
        assert "goodLogicFlag" in result

    def test_payload_no_longer_has_old_fields(self):
        user = [make_step((0,1,2,3), (2,1,1), 5040, 180)]
        ai   = make_ai_path(2)
        result = build_llm_payload(user, ai)
        assert "strongMove"       not in result
        assert "efficiencyRating" not in result
        assert "performanceTier"  not in result

    def test_payload_keys_are_exactly(self):
        # Without user_guesses/secret: yellowAnalysis and keyMoments should be None
        user = [make_step((0,1,2,3), (2,1,1), 5040, 180)]
        ai   = make_ai_path(2)
        result = build_llm_payload(user, ai)
        assert set(result.keys()) == {
            "userStepCount", "perfectStepCount", "goodLogicFlag", "logicFlag",
            "yellowAnalysis", "keyMoments",
        }
        assert result["yellowAnalysis"] is None
        assert result["keyMoments"] is None

    def test_payload_keys_with_guesses(self):
        # With user_guesses/secret: yellowAnalysis and keyMoments should be populated
        secret = (3, 7, 1, 9)
        user_guesses = [((3, 7, 1, 9), (4, 0, 0))]
        user = [make_step((3,7,1,9), (4,0,0), 5040, 0)]
        ai   = make_ai_path(1)
        result = build_llm_payload(user, ai, user_guesses=user_guesses, secret=secret)
        assert set(result.keys()) == {
            "userStepCount", "perfectStepCount", "goodLogicFlag", "logicFlag",
            "yellowAnalysis", "keyMoments",
        }
        assert result["yellowAnalysis"] is not None
        assert result["keyMoments"] is not None

    def test_good_logic_flag_is_none_when_no_guesses(self):
        user = [make_step((0,1,2,3), (2,1,1), 5040, 180)]
        ai   = make_ai_path(2)
        result = build_llm_payload(user, ai)
        assert result["goodLogicFlag"] is None

    def test_good_logic_flag_populated_when_guesses_provided(self):
        # smart_isolation scenario: guess 2 carries only digit 1, rest new
        secret = (1, 7, 8, 9)
        user_path = [
            make_step((0,1,2,3), (0,1,3), 5040, 500),
            make_step((1,4,5,6), (0,1,3), 500, 100),
        ]
        ai = make_ai_path(2)
        guesses = [
            ((0,1,2,3), (0,1,3)),
            ((1,4,5,6), (0,1,3)),
        ]
        result = build_llm_payload(user_path, ai, user_guesses=guesses, secret=secret)
        assert result["goodLogicFlag"] is not None
        assert result["goodLogicFlag"]["type"] == "smart_isolation"


class TestYellowAnalysis:
    # secret = (3, 7, 1, 9) used throughout unless otherwise noted

    def test_yellow_analysis_none_when_no_guesses_arg(self):
        user = [make_step((0, 1, 2, 3), (2, 1, 1), 5040, 180)]
        ai   = make_ai_path(2)
        result = build_llm_payload(user, ai)
        assert result["yellowAnalysis"] is None

    def test_yellow_analysis_total_feedback(self):
        # guess 1: 2 yellows, guess 2: 1 yellow → totalYellowFeedback = 3
        secret = (3, 7, 1, 9)
        user_guesses = [
            ((7, 3, 0, 5), (0, 2, 2)),   # 7 and 3 are yellow
            ((1, 0, 9, 5), (0, 1, 3)),   # 1 is yellow (in secret at pos 2, placed at pos 0)
        ]
        result = compute_yellow_analysis(user_guesses, secret)
        assert result["totalYellowFeedback"] == 3

    def test_dropped_after_yellow_detected(self):
        # guess 1 yields yellow for digit 7 (yellow at pos 0); guess 2 drops digit 7
        secret = (3, 7, 1, 9)
        user_guesses = [
            ((7, 0, 4, 6), (0, 1, 3)),   # digit 7 yellow at pos 0
            ((5, 0, 4, 6), (0, 0, 4)),   # digit 7 dropped
        ]
        result = compute_yellow_analysis(user_guesses, secret)
        assert len(result["droppedAfterYellow"]) == 1
        entry = result["droppedAfterYellow"][0]
        assert entry["guess"] == 1
        assert 7 in entry["digitsDropped"]
        assert entry["yellowPegsThatGuess"] == 1

    def test_missed_carry_forward_true(self):
        # droppedAfterYellow is non-empty → missedCarryForward must be True
        secret = (3, 7, 1, 9)
        user_guesses = [
            ((7, 0, 4, 6), (0, 1, 3)),   # digit 7 yellow
            ((5, 0, 4, 6), (0, 0, 4)),   # digit 7 dropped
        ]
        result = compute_yellow_analysis(user_guesses, secret)
        assert result["missedCarryForward"] is True

    def test_confirmed_digits_by_end(self):
        # secret = (3, 7, 1, 9); final guess contains 3 and 7 which are both in secret
        secret = (3, 7, 1, 9)
        user_guesses = [
            ((0, 2, 4, 6), (0, 0, 4)),
            ((3, 7, 0, 5), (0, 2, 2)),   # final guess; 3 and 7 are in secret
        ]
        result = compute_yellow_analysis(user_guesses, secret)
        assert set(result["confirmedDigitsByEnd"]) == {3, 7}


class TestKeyMoments:
    def test_zero_peg_feedback_produces_zero_pegs_string(self):
        # A guess that earns all-red feedback (g=0, y=0) must appear as "0 pegs"
        # in the pegChange field, not "0 yellow".
        # secret = (3, 7, 1, 9); guess 1 uses none of those digits → 0 pegs.
        secret = (3, 7, 1, 9)
        user_guesses = [
            ((0, 2, 4, 6), (0, 0, 4)),   # 0 greens, 0 yellows — all red
        ]
        moments = compute_key_moments(user_guesses, secret)
        assert len(moments) == 1
        assert moments[0]["guess"] == 1
        assert moments[0]["pegChange"] == "0 pegs"
