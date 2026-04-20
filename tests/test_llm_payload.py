import pytest
from cipher_engine import build_llm_payload


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

class TestPerformanceTier:
    def test_efficient_when_delta_is_zero(self):
        user = [
            make_step((0,1,2,3), (2,1,1), 5040, 180),
            make_step((4,5,6,7), (4,0,0), 180, 0),
        ]
        result = build_llm_payload(user, make_ai_path(2))
        assert result["performanceTier"] == "efficient"

    def test_efficient_when_delta_is_one(self):
        user = [
            make_step((0,1,2,3), (2,1,1), 5040, 180),
            make_step((4,5,6,7), (3,1,0), 180, 10),
            make_step((8,9,0,1), (4,0,0), 10, 0),
        ]
        result = build_llm_payload(user, make_ai_path(2))
        assert result["performanceTier"] == "efficient"

    def test_average_when_delta_is_two(self):
        user = [
            make_step((0,1,2,3), (1,2,1), 5040, 180),
            make_step((4,5,6,7), (0,2,2), 180, 45),
            make_step((8,9,0,1), (2,1,1), 45, 12),
            make_step((2,3,4,5), (1,2,1), 12, 3),
            make_step((6,7,8,9), (4,0,0), 3, 0),
        ]
        result = build_llm_payload(user, make_ai_path(3))
        assert result["performanceTier"] == "average"

    def test_average_when_delta_is_three(self):
        user = [make_step((0,1,2,3), (1,0,3), 5040, 500)] * 5 + \
               [make_step((5,6,7,8), (4,0,0), 500, 0)]
        result = build_llm_payload(user, make_ai_path(3))
        assert result["performanceTier"] == "average"

    def test_struggling_when_delta_exceeds_three(self):
        user = [make_step((0,1,2,3), (1,0,3), 5040, 500)] * 7 + \
               [make_step((5,6,7,8), (4,0,0), 500, 0)]
        result = build_llm_payload(user, make_ai_path(4))
        assert result["performanceTier"] == "struggling"


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

    def test_efficiency_rating_rounded(self):
        # perfect=3, user=5 → 3/5*100 = 60
        user = [make_step((0,1,2,3), (1,0,3), 5040, 500)] * 4 + \
               [make_step((5,6,7,8), (4,0,0), 500, 0)]
        result = build_llm_payload(user, make_ai_path(3))
        assert result["efficiencyRating"] == 60

    def test_efficiency_100_when_equal_steps(self):
        user = [
            make_step((0,1,2,3), (2,1,1), 5040, 50),
            make_step((4,5,6,7), (4,0,0), 50, 0),
        ]
        result = build_llm_payload(user, make_ai_path(2))
        assert result["efficiencyRating"] == 100


class TestStrongMove:
    def test_strong_move_is_highest_eliminator(self):
        user = [
            make_step((0,1,2,3), (1,2,1), 5040, 180),   # eliminated 4860
            make_step((4,5,6,7), (0,2,2), 180, 45),      # eliminated 135
            make_step((8,9,0,1), (2,1,1), 45, 12),       # eliminated 33
            make_step((2,3,4,5), (1,2,1), 12, 3),        # eliminated 9
            make_step((6,7,8,9), (4,0,0), 3, 0),         # eliminated 3 (final)
        ]
        result = build_llm_payload(user, make_ai_path(3))
        assert result["strongMove"]["guessNumber"] == 1
        assert result["strongMove"]["eliminated_count"] == 4860

    def test_strong_move_guess_string_format(self):
        user = [
            make_step((5,3,8,1), (2,1,1), 5040, 100),
            make_step((0,2,4,6), (4,0,0), 100, 0),
        ]
        result = build_llm_payload(user, make_ai_path(2))
        assert result["strongMove"]["guess"] == "5-3-8-1"

    def test_strong_move_eliminated_pct(self):
        # 4860 / 5040 * 100 = 96.4... → rounded to 96
        user = [
            make_step((0,1,2,3), (1,2,1), 5040, 180),   # eliminated 4860
            make_step((4,5,6,7), (4,0,0), 180, 0),
        ]
        result = build_llm_payload(user, make_ai_path(2))
        assert result["strongMove"]["eliminated_pct"] == 96


class TestStruggleMove:
    def test_struggle_move_is_lowest_eliminator_excluding_final(self):
        user = [
            make_step((0,1,2,3), (1,2,1), 5040, 180),   # eliminated 4860 — strong
            make_step((4,5,6,7), (0,2,2), 180, 45),      # eliminated 135
            make_step((8,9,0,1), (2,1,1), 45, 12),       # eliminated 33
            make_step((2,3,4,5), (1,2,1), 12, 3),        # eliminated 9  — struggle
            make_step((6,7,8,9), (4,0,0), 3, 0),         # eliminated 3 (final — excluded)
        ]
        result = build_llm_payload(user, make_ai_path(3))
        assert result["struggleMove"]["guessNumber"] == 4
        assert result["struggleMove"]["eliminated_count"] == 9

    def test_no_struggle_move_on_one_guess_solve(self):
        user = [
            make_step((5,3,7,1), (4,0,0), 5040, 0),
        ]
        result = build_llm_payload(user, make_ai_path(1))
        assert "struggleMove" not in result

    def test_no_struggle_move_when_only_one_non_final_and_it_is_strong(self):
        # 2-guess solve: step 1 is both strong AND the only non-final candidate
        user = [
            make_step((0,1,2,3), (2,1,1), 5040, 10),   # eliminated 5030 — strong, only non-final
            make_step((5,6,7,8), (4,0,0), 10, 0),       # final
        ]
        result = build_llm_payload(user, make_ai_path(3))
        assert result["strongMove"]["guessNumber"] == 1
        assert "struggleMove" not in result

    def test_struggle_move_guess_string_format(self):
        user = [
            make_step((0,1,2,3), (1,2,1), 5040, 180),
            make_step((7,8,9,0), (0,1,3), 180, 45),
            make_step((2,3,4,5), (4,0,0), 45, 0),
        ]
        result = build_llm_payload(user, make_ai_path(2))
        # strongMove=step1(4860), non-final excl strong: [step2(135)]
        assert result["struggleMove"]["guess"] == "7-8-9-0"
