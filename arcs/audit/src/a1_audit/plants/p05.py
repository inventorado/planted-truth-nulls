"""P5, its catch-rate part (rate reported, no threshold): P3's construction on the decoded-list form (RUN_PLAN.md v3.1
§7 P5: "P3's construction run for this form, catch rate reported (no frozen rate exists for it)"; classes dk-ctx, V-DK,
V-AAL). The value checks of P5 (T = mean per-gene r, the conditioned species null, conditioned = unconditioned on a
single class, Pearson-r scoring gives a different p) are WP1's (tests/test_p0.py, test_verdict.py)."""
from __future__ import annotations

from . import base as BS
from . import criteria as CR
from . import p03

CHOICES = p03.CHOICES_COMMON + (
    "PLANT CHOICE (not in §7): n = 100 computed plants per class (P3b's n; §7 gives P5's catch rate no n), cases j = "
    "0, 1, ... with an unmatched plant replaced by the next case.",
)


class _Catch(BS.PlantSpec):
    kind = CR.REPORTED
    replace_unmatched = True
    form = "?"
    classes: tuple = ()
    cost_s = 10.0

    def cells(self):
        return [BS.Cell(c, c, self.form) for c in self.classes]

    def n_official(self, cell):
        return 100

    def case_of(self, cell, i):
        return int(i)

    def run_case(self, cell, i, K):
        return p03.cgene_case(self, cell, i, K, self.form, ("+", "two"))

    def summarise(self, cell, recs, n_official):
        comp = [r for r in recs if r["status"] == "computed"]
        k = BS.count(comp, lambda r: r["claim"]["verdicts"]["+"]["survives"])
        crit = dict(kind=CR.REPORTED, k=k, n=len(comp), result="reported (no frozen rate; never triggers a code change)")
        return p03.catch_summary(cell, recs, n_official, crit, "+")


class P5(_Catch):
    id = "P5"
    module = "p05"
    form = "decoded-list"
    classes = ("dk-ctx", "V-DK", "V-AAL")
    row = "RUN_PLAN §7 P5: decoded-list; P3's construction run for this form, catch rate reported"
    construction = ("C-gene (prereg §6.3), m = 25, a = .9, decoded-list, plant K, one-sided + verdict (the two-sided "
                    "R1 verdict beside it)")
    choices = CHOICES


PLANTS = {"P5": P5()}
