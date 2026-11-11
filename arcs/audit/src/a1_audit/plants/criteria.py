"""The statistical criteria of RUN_PLAN.md v3.1 §7 (thresholds fixed before any plant runs; §7 :1097-1101, §17).

Each threshold is written as §7 states it AND re-derived here from the tail §7 gives as its basis (scipy), and the
re-derivation is asserted at import against §7's stated numbers (an apparatus check: a wrongly typed threshold stops
the import). `self_test()` plants boundary counts through every criterion function (each must flip exactly at its
threshold) - the must-fail half of the check.

Two kinds of statistical test (§7 :1109-1116):
- correct-leg test (P3b, P4, P6, P12, P24, P26's site leg, P25 (c)'s correct leg): a FAIL with no defect named blocks
  the claims of that form x class until a frozen amendment says how they are read (§7, §17);
- must-catch test (P25 (a)-(c)'s flawed legs, P26's planted permutation leg): NOT CAUGHT with no defect named reads
  "plant regime insensitive for this form x class" and blocks nothing.
A rate reported without a threshold (P5's and P7's catch rates, P8's survival counts, P12's two-gene maps) never
triggers a code change.
"""
from __future__ import annotations

from scipy import stats

CORRECT_LEG = "correct-leg test"
MUST_CATCH = "must-catch test"
REPORTED = "reported (no threshold)"
FUNCTIONAL = "functional (exact assertions; a failure is a code defect)"
INSENSITIVE = "plant regime insensitive for this form x class"
CORRECT_LEG_FAIL = ("FAIL (correct-leg test): written diagnosis and asdg-skeptic review; with no defect named, the "
                    "claims of this form x class do not run until a frozen amendment says how they are read "
                    "(RUN_PLAN §7, §17)")
NOT_EVALUATED_DEV = "not evaluated (DEV run at n = %d; the criterion is stated for n = %d)"


def _largest_not_rejected(n: int, p0: float, alpha: float = 0.01) -> int:
    """The largest k for which the one-sided binomial test of rate <= p0 is not rejected at alpha (P(X >= k) > alpha)."""
    k = 0
    while stats.binom(n, p0).sf(k) > alpha:  # sf(k) = P(X >= k + 1)
        k += 1
    return k


def _smallest_rejecting(n: int, p0: float, alpha: float = 0.01) -> int:
    """The smallest k for which the one-sided binomial test of rate <= p0 is rejected at alpha (P(X >= k) <= alpha)."""
    k = 0
    while stats.binom(n, p0).sf(k - 1) > alpha:
        k += 1
    return k


def _approx(x: float, want: float, tol: float, what: str) -> float:
    if not abs(x - want) <= tol:
        raise AssertionError(f"criteria: {what} = {x!r}, §7 states {want} (tolerance {tol})")
    return float(x)


# ---- P3b (§7 row P3b) ---------------------------------------------------------------------------------------------
P3B_N = 100
P3B = {
    "V-AAL": dict(threshold=52, bb=(100, 198, 100), frozen="197 / 296 (.666) (prereg_amend_5.md:85)",
                  stated=(0.0064, 0.0103, 0.0018)),
    "V-DK": dict(threshold=44, bb=(100, 176, 125), frozen="175 / 299 (.585) (prereg_amend_5.md:85, :127)",
                 stated=(0.0075, 0.0119, 0.0024)),
}
P3B_TEXT = ("V-AAL fails iff <= 52 / 100 survive and V-DK iff <= 44 / 100; dk-ctx reported only (no frozen rate) "
            "(RUN_PLAN §7 P3b)")
for _cls, _d in P3B.items():
    _n, _a, _b = _d["bb"]
    _bb = stats.betabinom(_n, _a, _b)
    _d["tail_at"] = _approx(_bb.cdf(_d["threshold"]), _d["stated"][0], 5e-5, f"P3b {_cls} predictive tail at k")
    _d["tail_next"] = _approx(_bb.cdf(_d["threshold"] + 1), _d["stated"][1], 5e-5, f"P3b {_cls} tail at k + 1")
    assert _d["tail_at"] <= 0.01 < _d["tail_next"], f"P3b {_cls}: k is not the largest with tail <= .01"
    _p = (_a - 1) / (_a - 1 + _b - 1)  # the frozen rate (the uniform prior's update by the frozen count)
    _d["tail_exact_rate"] = _approx(stats.binom(_n, _p).cdf(_d["threshold"]), _d["stated"][2], 5e-5,
                                    f"P3b {_cls} tail at the exact rate")
    _d["p_fail_if_15_lower"] = float(stats.binom(_n, _p - 0.15).cdf(_d["threshold"]))
_approx(P3B["V-AAL"]["p_fail_if_15_lower"], 0.575, 5e-4, "P3b V-AAL P(fail) .15 lower")
_approx(P3B["V-DK"]["p_fail_if_15_lower"], 0.579, 5e-4, "P3b V-DK P(fail) .15 lower")


def p3b(cls: str, survivors: int, n: int) -> dict:
    if cls not in P3B:
        return dict(kind=REPORTED, result="reported only (no frozen rate)", k=survivors, n=n)
    t = P3B[cls]["threshold"]
    if n != P3B_N:
        return dict(kind=CORRECT_LEG, result=NOT_EVALUATED_DEV % (n, P3B_N), k=survivors, n=n,
                    threshold=f"fail iff <= {t} / {P3B_N}")
    return dict(kind=CORRECT_LEG, k=survivors, n=n, threshold=f"fail iff <= {t} / {P3B_N}",
                result="PASS" if survivors > t else CORRECT_LEG_FAIL)


# ---- P4 ----------------------------------------------------------------------------------------------------------
P4_N, P4_MAX = 100, 9
P4_TEXT = "verdict rejections <= 9 / 100 per cell (RUN_PLAN §7 P4)"
P4_TAILS = dict(at_cap=_approx(stats.binom(P4_N, 0.05).sf(P4_MAX), 0.028, 5e-4, "P4 P(fail) at the .05 cap"),
                at_004=float(stats.binom(P4_N, 0.004).sf(P4_MAX)),
                predictive_2_of_500=_approx(stats.betabinom(P4_N, 3, 499).sf(P4_MAX), 5.4e-7, 5e-9,
                                            "P4 predictive tail at 2 / 500"))
assert 1e-12 < P4_TAILS["at_004"] < 1e-10, P4_TAILS  # §7: "P(fail) ~ 1e-11"


def le_max(k: int, n: int, n_official: int, k_max: int, kind: str = CORRECT_LEG) -> dict:
    """A correct-leg test 'k <= k_max of n_official' (pass) / 'k > k_max' (FAIL)."""
    base = dict(kind=kind, k=k, n=n, threshold=f"pass iff <= {k_max} / {n_official}")
    if n != n_official:
        return dict(base, result=NOT_EVALUATED_DEV % (n, n_official))
    return dict(base, result="PASS" if k <= k_max else CORRECT_LEG_FAIL)


def ge_min(k: int, n: int, n_official: int, k_min: int) -> dict:
    """A must-catch test 'k >= k_min of n_official' (caught) / not caught -> plant regime insensitive."""
    base = dict(kind=MUST_CATCH, k=k, n=n, threshold=f"caught iff >= {k_min} / {n_official}")
    if n != n_official:
        return dict(base, result=NOT_EVALUATED_DEV % (n, n_official))
    return dict(base, result="CAUGHT" if k >= k_min else
                f"NOT CAUGHT: with no defect named, reported as '{INSENSITIVE}' (blocks nothing; RUN_PLAN §7, §17)")


def p4(k: int, n: int) -> dict:
    return le_max(k, n, P4_N, P4_MAX)


# ---- P6 / P12 -----------------------------------------------------------------------------------------------------
P6_N, P6_MAX = 20, 3
P6_TEXT = "signed T survives in <= 3 of 20 per class (RUN_PLAN §7 P6)"
P6_TAIL = _approx(stats.binom(P6_N, 0.025).sf(P6_MAX), 0.0014, 5e-5, "P6 P(>= 4 of 20) at .025")
P12_N, P12_MAX = 20, 4
P12_TEXT = "20 independent fields: <= 4 pass at component level (RUN_PLAN §7 P12)"
P12_TAIL = _approx(stats.binom(P12_N, 0.05).sf(P12_MAX), 0.0026, 5e-5, "P12 P(>= 5 of 20) at .05")


def p6(k: int, n: int) -> dict:
    return le_max(k, n, P6_N, P6_MAX)


def p12(k: int, n: int) -> dict:
    return le_max(k, n, P12_N, P12_MAX)


# ---- P24 / P25 / P26 ------------------------------------------------------------------------------------------------
P24_N = 300
P24_MAX = _largest_not_rejected(P24_N, 0.05)
assert P24_MAX == 24, P24_MAX
P24_TEXT = ("per stratum (class x target x kind), the species-leg rate at .025 passes iff the one-sided binomial test "
            "of rate <= .05 is not rejected at alpha = .01 (<= 24 of 300) (RUN_PLAN §7 P24)")
P24_TAILS = dict(at_022=_approx(stats.binom(P24_N, 0.022).sf(P24_MAX), 2e-8, 1e-9, "P24 P(fail | .022)"),
                 at_10=_approx(stats.binom(P24_N, 0.10).sf(P24_MAX), 0.86, 5e-3, "P24 P(fail | .10)"),
                 at_15=_approx(stats.binom(P24_N, 0.15).sf(P24_MAX), 1.0, 1e-3, "P24 P(fail | .15)"))
P25_N = 500
P25_MIN = _smallest_rejecting(P25_N, 0.025)
assert P25_MIN == 22, P25_MIN
P25C_MAX = _largest_not_rejected(P25_N, 0.05)
assert P25C_MAX == 37, P25C_MAX
P25_TEXT = ("each flawed leg must reject 'rate <= .025' at alpha = .01 (>= 22 of 500); (c)'s correct species leg must "
            "pass P24's test at n = 500 (<= 37 of 500) (RUN_PLAN §7 P25)")
P25_TAILS = dict(caught_at_04=_approx(stats.binom(P25_N, 0.04).sf(P25_MIN - 1), 0.36, 0.01, "P25 P(caught | .04)"))
P26_N = 300
P26_SITE_MAX = P24_MAX
P26_PLANT_MIN = _smallest_rejecting(P26_N, 0.025)
assert P26_PLANT_MIN == 15, P26_PLANT_MIN
P26_TEXT = ("the site-leg rate at .025 passes iff <= 24 of 300 (P24's criterion); the planted within-class "
            "parcel-label permutation must reject 'rate <= .025' at alpha = .01 (>= 15 of 300) (RUN_PLAN §7 P26)")
P26_TAILS = dict(caught_at_05=_approx(stats.binom(P26_N, 0.05).sf(P26_PLANT_MIN - 1), 0.54, 5e-3,
                                      "P26 P(caught | .05)"))


def p24(k: int, n: int, n_official: int = P24_N) -> dict:
    return le_max(k, n, n_official, P24_MAX)


def p25_flawed(k: int, n: int) -> dict:
    return ge_min(k, n, P25_N, P25_MIN)


def p25_correct(k: int, n: int) -> dict:
    return le_max(k, n, P25_N, P25C_MAX)


def p26_site(k: int, n: int) -> dict:
    return le_max(k, n, P26_N, P26_SITE_MAX)


def p26_planted(k: int, n: int) -> dict:
    return ge_min(k, n, P26_N, P26_PLANT_MIN)


def derivations() -> dict:
    """Every threshold with the tails it was checked against (written into each plant's output)."""
    return dict(
        P3b={c: {k: v for k, v in d.items() if k != "stated"} for c, d in P3B.items()},
        P4=dict(n=P4_N, max=P4_MAX, **P4_TAILS), P6=dict(n=P6_N, max=P6_MAX, p_ge_4_at_025=P6_TAIL),
        P12=dict(n=P12_N, max=P12_MAX, p_ge_5_at_05=P12_TAIL), P24=dict(n=P24_N, max=P24_MAX, **P24_TAILS),
        P25=dict(n=P25_N, flawed_min=P25_MIN, correct_max=P25C_MAX, **P25_TAILS),
        P26=dict(n=P26_N, site_max=P26_SITE_MAX, planted_min=P26_PLANT_MIN, **P26_TAILS),
        tails="scipy %s (RUN_PLAN §7: tails computed 2026-10-01 with scipy 1.18.1)" % __import__("scipy").__version__)


def self_test() -> list:
    """Planted boundary counts through every criterion function: each must flip exactly at its threshold."""
    out = []

    def want(rec, prefix, what):
        if not str(rec["result"]).startswith(prefix):
            raise AssertionError(f"criteria self-test: {what}: {rec['result']!r} does not start with {prefix!r}")
        out.append(f"{what}: {rec['result'][:12]}")

    want(p3b("V-AAL", 52, 100), "FAIL", "P3b V-AAL 52/100")
    want(p3b("V-AAL", 53, 100), "PASS", "P3b V-AAL 53/100")
    want(p3b("V-DK", 44, 100), "FAIL", "P3b V-DK 44/100")
    want(p3b("V-DK", 45, 100), "PASS", "P3b V-DK 45/100")
    want(p3b("dk-ctx", 0, 100), "reported only", "P3b dk-ctx")
    want(p3b("V-AAL", 1, 3), "not evaluated", "P3b DEV n")
    want(p4(9, 100), "PASS", "P4 9/100")
    want(p4(10, 100), "FAIL", "P4 10/100")
    want(p6(3, 20), "PASS", "P6 3/20")
    want(p6(4, 20), "FAIL", "P6 4/20")
    want(p12(4, 20), "PASS", "P12 4/20")
    want(p12(5, 20), "FAIL", "P12 5/20")
    want(p24(24, 300), "PASS", "P24 24/300")
    want(p24(25, 300), "FAIL", "P24 25/300")
    want(p25_flawed(22, 500), "CAUGHT", "P25 flawed 22/500")
    want(p25_flawed(21, 500), "NOT CAUGHT", "P25 flawed 21/500")
    want(p25_correct(37, 500), "PASS", "P25 (c) correct 37/500")
    want(p25_correct(38, 500), "FAIL", "P25 (c) correct 38/500")
    want(p26_site(24, 300), "PASS", "P26 site 24/300")
    want(p26_site(25, 300), "FAIL", "P26 site 25/300")
    want(p26_planted(15, 300), "CAUGHT", "P26 planted 15/300")
    want(p26_planted(14, 300), "NOT CAUGHT", "P26 planted 14/300")
    return out
