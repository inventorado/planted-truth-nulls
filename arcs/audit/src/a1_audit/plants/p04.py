"""P4 (statistical; correct-leg test): random sets on independent fields (RUN_PLAN.md v3.1 §7).

"random sets on independent fields (n = 100 per cell) | every form x class used (set-vs-map dk-ctx / V-DK / V-AAL /
V-DK-subcortex; decoded-list dk-ctx / V-DK / V-AAL / MIST64; PLS-enrichment V-AAL / dk-ctx) | verdict rejections <= 9 /
100 ... Every leg's rate reported. Scope: this cannot test the species or site leg ...; P24-P26 test those legs".
"""
from __future__ import annotations

from . import base as BS
from . import construct as CO
from . import criteria as CR

CELLS = (("set-vs-map", "dk-ctx"), ("set-vs-map", "V-DK"), ("set-vs-map", "V-AAL"), ("set-vs-map", "V-DK-subcortex"),
         ("decoded-list", "dk-ctx"), ("decoded-list", "V-DK"), ("decoded-list", "V-AAL"), ("decoded-list", "MIST64"),
         ("PLS-enrichment", "V-AAL"), ("PLS-enrichment", "dk-ctx"))


class P4(BS.PlantSpec):
    id = "P4"
    module = "p04"
    kind = "statistical: " + CR.CORRECT_LEG
    row = "RUN_PLAN §7 P4: random sets on independent fields, n = 100 per cell; verdict rejections <= 9 / 100"
    construction = ("y = an independent field (prereg §6.1 generators on the class's primary-parcel centroids, "
                    "generator cell i mod 10: grf15 / grf30 / grf60 / sar5 / sar9 x class step 0 / 1); S = 25 uniform "
                    "genes of the class universe (prereg §6.2 F-sp); the full verdict at plant K through the production "
                    "path")
    choices = (
        "PLANT CHOICE (not in §7): m = 25 (prereg §6.2 F-sp's set size); S drawn before the field on the construction "
        "stream (F-sp's order); case = 10,000 x cell index + i (cells in the §7 row's order), so every cell's maps are "
        "its own.",
        "PLANT CHOICE (not in §7): the criterion is applied to BOTH the one-sided (+) verdict (the direction the frozen "
        "false-alarm rates were measured in) and the two-sided R1 verdict, assembled from the same legs; P4 fails in a "
        "cell if either exceeds 9 / 100. Every leg's one-sided rate is reported in both directions.",
        "PLANT CHOICE (not in §7): V-DK-subcortex = V-DK's 7 left subcortical parcels (common.class_context): at plant K "
        "its G6s is exact (2^6 = 64 <= 200; floor 2/65 >= .025), so every claim there is resolution-limited and a "
        "non-rejection (reported).",
    )
    cost_s = 10.0

    def cells(self):
        return [BS.Cell(f"{f} / {c}", c, f, (("index", j),)) for j, (f, c) in enumerate(CELLS)]

    def n_official(self, cell):
        return CR.P4_N

    def case_of(self, cell, i):
        return 10_000 * int(cell.get("index")) + int(i)

    def run_case(self, cell, i, K):
        keys = self.keys(cell, i)
        rng = keys.rng()
        S = CO.random_set(cell.cls, rng, 25)
        y, gen, step = CO.field(cell.cls, rng, i)
        claim = BS.full_claim(cell.form, cell.cls, y, S, keys, K, ("+", "two"))
        return dict(status="computed", construction=dict(gen=gen, step=float(step), m=25), S=BS.gene_list(S),
                    claim=claim, seeds=keys.record())

    def summarise(self, cell, recs, n_official):
        claims = [r["claim"] for r in recs]
        n = len(claims)
        kp = BS.count(claims, lambda c: c["verdicts"]["+"]["survives"])
        k2 = BS.count(claims, lambda c: c["verdicts"]["two"]["survives"])
        return dict(n=n, rejections={"one-sided +": kp, "two-sided R1": k2},
                    criteria={"one-sided +": CR.p4(kp, n), "two-sided R1": CR.p4(k2, n)},
                    leg_rates={"+": BS.leg_rates(claims, "+", 1), "-": BS.leg_rates(claims, "two", -1)},
                    statuses={"+": BS.statuses(claims, "+"), "two": BS.statuses(claims, "two")},
                    scope="cannot test the species or site leg (a correct site leg alone holds the verdict count; "
                          "prereg_amend_3.md:192); P24-P26 test those legs (RUN_PLAN §7 P4)")


PLANTS = {"P4": P4()}
