"""P7, its catch-rate part (rate reported, no threshold): P3's construction on the PLS-enrichment form (RUN_PLAN.md
v3.1 §7 P7: "catch rate of P3's construction reported"; classes V-AAL, dk-ctx). The value checks of P7 (T = mean
normalised weight; surrogate T* = direct refit; species p = decoded-list species p) are WP1's (tests/test_p0.py)."""
from __future__ import annotations

from . import p03
from .p05 import _Catch

CHOICES = p03.CHOICES_COMMON + (
    "PLANT CHOICE (not in §7): n = 100 computed plants per class (P3b's n; §7 gives P7's catch rate no n), cases j = "
    "0, 1, ... with an unmatched plant replaced by the next case.",
)


class P7(_Catch):
    id = "P7"
    module = "p07"
    form = "PLS-enrichment"
    classes = ("V-AAL", "dk-ctx")
    row = "RUN_PLAN §7 P7: PLS-enrichment refit; catch rate of P3's construction reported"
    construction = ("C-gene (prereg §6.3), m = 25, a = .9, PLS-enrichment (PLS1 refit per surrogate), plant K, "
                    "one-sided + verdict (the two-sided R1 verdict beside it)")
    choices = CHOICES


PLANTS = {"P7": P7()}
