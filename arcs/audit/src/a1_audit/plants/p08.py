"""P8 (a), its survival counts (reported, no threshold), on the real dk-ctx matrix (RUN_PLAN.md v3.1 §7 P8: "(a) 20
planted negative-signal maps: wherever d* = -, the two-sided conjunction p = 2 x the one-sided '-' conjunction p
(exact); survival counts of both reported"). P8 (b), (c) and the toy-matrix (a) are WP1's (tests/test_verdict.py); the
exact identity of (a) is asserted again here on every map (a failure is a code defect)."""
from __future__ import annotations

import numpy as np

from . import base as BS
from . import common as C
from . import construct as CO
from . import criteria as CR

FORMS = ("set-vs-map", "decoded-list")


class P8(BS.PlantSpec):
    id = "P8"
    module = "p08"
    kind = CR.REPORTED + " (survival counts); the exact (a) identity asserted (functional)"
    row = ("RUN_PLAN §7 P8 (a): 20 planted negative-signal maps (dk-ctx): wherever d* = -, two-sided conjunction p = 2 x "
           "one-sided '-' conjunction p (exact); survival counts of both reported")
    construction = ("C-gene (prereg §6.3), m = 25, a = .9, sign -1: y = -.9 z(e~_S) + sqrt(1 - .81) field; each map "
                    "evaluated on set-vs-map and decoded-list; two-sided R1 and one-sided (-) verdicts from the same "
                    "legs, plant K")
    choices = (
        "PLANT CHOICE (not in §7): 'negative-signal map' = P3's C-gene construction with the signal's sign reversed "
        "(y = -a z(e~_S) + sqrt(1 - a^2) field, a = .9; e3_plants' draw order).",
        "PLANT CHOICE (not in §7): each of the 20 maps is evaluated on both forms used for two-sided dk-ctx claims "
        "(set-vs-map: 24 TSV rows; decoded-list: 112), one claim per form, both forms on the same leg keys (common "
        "random numbers); survival counts reported per form.",
        "PLANT CHOICE (not in §7): plant id 8, cases 0..19; an unmatched plant (G2) is replaced by the next case.",
    )
    replace_unmatched = True
    cost_s = 16.0

    def cells(self):
        return [BS.Cell("dk-ctx", "dk-ctx", None)]

    def n_official(self, cell):
        return 20

    def case_of(self, cell, i):
        return int(i)

    def run_case(self, cell, i, K):
        keys = self.keys(cell, i)
        c = CO.cgene(cell.cls, keys.rng(), i, sign=-1)
        head = dict(construction={k: v for k, v in c.items() if k not in ("S", "y")}, S=BS.gene_list(c["S"]))
        if c["status"] != "ok":
            return dict(status="unmatched for plant", **head, seeds=keys.record())
        out = {}
        for form in FORMS:
            pr = C.prepare(form, cell.cls, c["y"], np.asarray(c["S"], dtype=int))
            legs = C.full_legs(pr, keys, K)
            two, minus = C.assemble(legs, "two"), C.assemble(legs, "-")
            check = None
            if two["d_star"] == -1:
                if two["p_conjunction"] != min(1.0, 2.0 * minus["p_conjunction"]):
                    raise AssertionError(f"P8 (a) {form}: two-sided p {two['p_conjunction']} != 2 x one-sided "
                                         f"{minus['p_conjunction']}")
                for leg, rec in two["legs"].items():
                    o = minus["legs"][leg]["p_reported"]
                    if not ((o is None and rec["p_reported"] is None) or rec["p_reported"] == min(1.0, 2.0 * o)):
                        raise AssertionError(f"P8 (a) {form}: leg {leg} reported p != 2 x one-sided")
                check = "d* = -: conjunction and every leg's reported p = min(1, 2 x one-sided '-') (exact)"
            out[form] = dict(two=C.compact_verdict(two), minus=C.compact_verdict(minus), legs=C.leg_table(legs),
                             exact_check=check)
        return dict(status="computed", **head, forms=out, seeds=keys.record())

    def summarise(self, cell, recs, n_official):
        comp = [r for r in recs if r["status"] == "computed"]
        per = {}
        for form in FORMS:
            fs = [r["forms"][form] for r in comp]
            per[form] = dict(n=len(fs), n_dstar_minus=BS.count(fs, lambda f: f["two"]["d_star"] == -1),
                             exact_checks=BS.count(fs, lambda f: f["exact_check"] is not None),
                             survivors_two_sided=BS.count(fs, lambda f: f["two"]["survives"]),
                             survivors_one_sided_minus=BS.count(fs, lambda f: f["minus"]["survives"]))
        res = "reported" if len(comp) == n_official else CR.NOT_EVALUATED_DEV % (len(comp), n_official)
        return dict(n_cases=len(recs), n_computed=len(comp), per_form=per,
                    criterion=dict(kind=CR.REPORTED, result=res + " (survival counts; the exact identity held on "
                                                                  "every d* = - map, else the plant stops)"))


PLANTS = {"P8": P8()}
