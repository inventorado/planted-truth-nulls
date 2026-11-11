"""A1 reporting labels (arcs/audit/RUN_PLAN.md v3.1 R27, FROZEN 16c60232...; RUN_PLAN_amend_2.md v2.1 R37, FROZEN
acdb1290...). Pure functions: nothing here opens a file, a map or a carrier, and nothing here computes a statistic.

R27 (RUN_PLAN.md:968-981) produces two kinds of label; both are produced here.

1. The reproduction check (prereg.md:120-122; claims_register.md:316-332; R27 :980-981), read by RUN_PLAN_amend_2 R37
   option (B) (`reproduction_check`):
   - the claim is "reproduced" iff |ours - published| <= .05;
   - a miss is "not reproduced (sign)" iff both values are non-zero and of opposite sign, else "not reproduced"; a value
     of exactly 0 has no sign; ours is never re-oriented;
   - for R^2, R^2_adj and dominance (non-negative functionals) the sign label never applies.
   The tolerance is decided in exact rationals: the published value as its decimal text (the register's digits), ours as
   the exact value of its binary float, so a boundary case (a difference of exactly .05) is never decided by rounding.
   R37's must-fail variant (A), the sign overriding the tolerance, exists only in the plant (tests/test_amend2.py).
2. Amendment 5 §3-§4 labels and readings (R27 :969-977): a port of A3's reading() / descriptors() (a3_port.reading,
   a3_port.descriptors) "with A3's gate logic removed" (`r27_reading`: gate=None, so a3_port.apply_gate adds no label
   and never reads NOT EVALUATED); the power columns, R2_grad, R2_|x|, f / m, the hypergeometric p, c_S, "calibrated
   evidence" versus "calibration extrapolated (set size / class / gradient)", the re-parcellation labels and the
   single-class-outside-dk-ctx reading come from that port unchanged.
"""
from __future__ import annotations

import math
from fractions import Fraction

from . import a3_port as A3

REPRO_TOLERANCE = Fraction(1, 20)   # prereg.md:120-122 "the paper's reported value ±0.05"
REPRO_TOLERANCE_TEXT = ".05"
REPRODUCED = "reproduced"
NOT_REPRODUCED = "not reproduced"
NOT_REPRODUCED_SIGN = "not reproduced (sign)"
R37_RULE = ("RUN_PLAN_amend_2 R37 (B): reproduced iff |ours - published| <= .05; a miss is 'not reproduced (sign)' iff "
            "both values are non-zero and of opposite sign, else 'not reproduced'; ours is never re-oriented; the sign "
            "label never applies to R^2, R^2_adj or dominance")
# The functionals of R27 :978-980 (claims_register.md §1.5) by whether a sign label can apply. A functional outside
# this vocabulary is refused (fail closed): its caller names it here first.
FUNCTIONALS = {
    "pearson r": True,
    "spearman rho": True,
    "beta": True,
    "mean bicor": True,                  # R13 (Patel)
    "|z|-weighted rho": True,            # Giacomel's |z|-weighted GEDAR rho (claims_register.md:319)
    "signed-weight rho": True,           # Giacomel's T_S (RUN_PLAN_amend_2 R41; TSV rows 103 / 105 / 107, 115-117)
    "rank-biserial": True,               # Liu T3 / T4 / T5
    "R2": False,                         # R37: non-negative, never a sign label
    "R2_adj": False,
    "dominance": False,
}


def _published_fraction(published) -> Fraction:
    """The published value as an exact rational of its decimal text ('-0.150', '.531', U+2212 minus accepted)."""
    if isinstance(published, bool):
        raise ValueError("reproduction check: a boolean is not a published value")
    if isinstance(published, float):
        if not math.isfinite(published):
            raise ValueError("reproduction check: the published value is not finite")
        text = repr(published)
    elif isinstance(published, (int, Fraction)):
        return Fraction(published)
    elif isinstance(published, str):
        text = published.strip().replace("−", "-")
    else:
        raise ValueError(f"reproduction check: a published value of type {type(published).__name__}")
    try:
        return Fraction(text)
    except (ValueError, ZeroDivisionError):
        raise ValueError("reproduction check: the published value is not a decimal number") from None


def _sign(x: Fraction) -> int:
    return (x > 0) - (x < 0)


def reproduction_check(published, ours, *, functional: str) -> dict:
    """R37 (B). published: the register's value (decimal text preferred; a number accepted); ours: our functional's
    value (a finite float). Returns the label and the inputs it was decided on."""
    if functional not in FUNCTIONALS:
        raise ValueError(f"reproduction check: functional {functional!r} is not in the vocabulary (reporting.FUNCTIONALS)")
    if isinstance(ours, bool) or not isinstance(ours, (int, float, Fraction)):
        raise ValueError("reproduction check: our value must be a number")
    if isinstance(ours, float) and not math.isfinite(ours):
        raise ValueError("reproduction check: our value is not finite")
    pub = _published_fraction(published)
    our = Fraction(ours)
    diff = abs(our - pub)
    signed = FUNCTIONALS[functional]
    if diff <= REPRO_TOLERANCE:
        label = REPRODUCED
    elif signed and _sign(pub) != 0 and _sign(our) != 0 and _sign(pub) != _sign(our):
        label = NOT_REPRODUCED_SIGN
    else:
        label = NOT_REPRODUCED
    return dict(label=label, published=str(published), ours=float(ours), abs_difference=float(diff),
                tolerance=REPRO_TOLERANCE_TEXT, functional=functional, sign_label_applies=bool(signed), rule=R37_RULE)


def is_reproduced(check: dict) -> bool:
    return check.get("label") == REPRODUCED


def r27_reading(rec: dict, desc: dict | None, ctx, *, reparcellated: bool = False, scope: dict | None = None,
                reproduction: dict | None = None) -> dict:
    """R27's amendment-5 labels and reading of one claim: a3_port.reading with A3's gate logic removed (gate=None);
    the reproduction check (reproduction_check's record) is attached beside it, never folded into the reading."""
    out = A3.reading(rec, desc, ctx, reparcellated=reparcellated, gate=None, scope=scope)
    g = out.get("gate") or {}
    if g.get("not_evaluated") or g.get("labels") or g.get("planted"):
        raise AssertionError("R27: A3's gate logic must be removed (gate=None adds nothing)")
    out = dict(out)
    out.pop("gate", None)
    out["gate_logic"] = "removed (RUN_PLAN R27 :969-970: the A3 port with A3's gate logic removed)"
    if reproduction is not None:
        if reproduction.get("rule") != R37_RULE:
            raise ValueError("R27: the reproduction record is not reporting.reproduction_check's")
        out["reproduction"] = dict(reproduction)
    return out
