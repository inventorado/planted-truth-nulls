"""P6 (statistical; correct-leg test): the pooled-sign plant (RUN_PLAN.md v3.1 §7).

"pooled-sign plant: S = S+ u S-, y = z(e~_{S+}) - z(e~_{S-}) | decoded-list dk-ctx, V-DK, V-AAL; n = 20 per class |
signed T survives in <= 3 of 20 (for a verdict at the .025 cap, P(>= 4 of 20) = .0014); T_abs values = direct
computation; T_abs Level 0 p reported (T_abs is uncalibrated by registration, claims_register.md:311-313)".
"""
from __future__ import annotations

import numpy as np
from scipy import stats

from .. import adapters as AD
from asdg.genesets import coexpr_matched_sets
from . import base as BS
from . import common as C
from . import construct as CO
from . import criteria as CR


class P6(BS.PlantSpec):
    id = "P6"
    module = "p06"
    kind = "statistical: " + CR.CORRECT_LEG
    row = ("RUN_PLAN §7 P6: pooled-sign plant S = S+ u S-, y = z(e~_{S+}) - z(e~_{S-}); decoded-list dk-ctx, V-DK, "
           "V-AAL; n = 20 per class; signed T survives in <= 3 of 20")
    construction = ("S+, S- two disjoint sets of 25 uniform genes; e~ = each set's C-gene residual (prereg §6.3: set "
                    "score residualised on [1, mean score of its 500 G2 sets, 3 PCs]); y = z(e~_{S+}) - z(e~_{S-}) "
                    "(no field); S = S+ u S- (50 genes); decoded-list verdict at plant K")
    choices = (
        "PLANT CHOICE (not in §7): |S+| = |S-| = 25 (prereg §6.3's m), disjoint, drawn in that order on the "
        "construction stream; each G2 (500 coexpression-matched sets) excludes its own set, as the frozen construction; "
        "y has no field (as §7 writes it).",
        "PLANT CHOICE (not in §7): the signed T is tested two-sided (R1: d* = argmin_d of the conjunction; a pooled list "
        "has no registered sign); the one-sided (+) and (-) survivals are reported beside it.",
        "PLANT CHOICE (not in §7): a plant with either G2 unmatched is recorded and replaced by the next case (n = 20 "
        "computed plants per class); cases j = 0, 1, ...",
        "PLANT CHOICE (not in §7): T_abs = adapters.TAbs on the prepared decoded-list claim (as run.g_tabs builds it); its value is checked "
        "against mean_{g in S} |np.corrcoef(y, x_g)| to 1e-12 and its Welch-t Level 0 against scipy.stats.ttest_ind("
        "equal_var=False) to 1e-12 (both directions); the upper-tail Level 0 p is reported.",
    )
    replace_unmatched = True
    cost_s = 12.0

    def cells(self):
        return [BS.Cell(c, c, "decoded-list") for c in ("dk-ctx", "V-DK", "V-AAL")]

    def n_official(self, cell):
        return CR.P6_N

    def case_of(self, cell, i):
        return int(i)

    def run_case(self, cell, i, K):
        keys = self.keys(cell, i)
        rng = keys.rng()
        ctx = C.class_context(cell.cls)
        al = CO.aux(cell.cls)["all"]
        Sp = rng.choice(al, size=25, replace=False)
        Sm = rng.choice(np.setdiff1d(al, Sp), size=25, replace=False)
        G2 = []
        for Sx in (Sp, Sm):
            sets, info = coexpr_matched_sets(ctx.U, al, 25, ctx.U.mean_coexpr(Sx), CO.G2_SETS, rng, exclude=Sx)
            G2.append((sets, info["status"]))
        head = dict(S_plus=BS.gene_list(Sp), S_minus=BS.gene_list(Sm), G2_status=[s for _, s in G2])
        if any(s is None for s, _ in G2):
            return dict(status="unmatched for plant", **head, seeds=keys.record())
        y = C.z(CO.cgene_residual(cell.cls, Sp, G2[0][0])) - C.z(CO.cgene_residual(cell.cls, Sm, G2[1][0]))
        S = np.concatenate([Sp, Sm])
        claim = BS.full_claim("decoded-list", cell.cls, y, S, keys, K, ("two", "+", "-"))
        pr = C.prepare("decoded-list", cell.cls, y, S)
        tb = AD.TAbs(pr.ctx, pr.y, pr.S, parcel_ids=pr.parcel_ids)  # as run.g_tabs builds it
        r_direct = np.array([np.corrcoef(pr.y, pr.ctx.X[:, g])[0, 1] for g in range(pr.ctx.G)])
        tabs_direct = float(np.abs(r_direct[S]).mean())
        if not abs(tb.T_obs - tabs_direct) <= 1e-12:
            raise AssertionError(f"P6: T_abs {tb.T_obs} != direct {tabs_direct}")
        a, b = np.abs(r_direct[S]), np.abs(np.delete(r_direct, S))
        t, _ = stats.ttest_ind(a, b, equal_var=False)
        df = (a.var(ddof=1) / a.size + b.var(ddof=1) / b.size) ** 2 / (
            (a.var(ddof=1) / a.size) ** 2 / (a.size - 1) + (b.var(ddof=1) / b.size) ** 2 / (b.size - 1))
        l0 = tb.level0_both()
        l0_direct = {1: float(stats.t.sf(t, df)), -1: float(stats.t.cdf(t, df))}
        for d in (1, -1):
            if not abs(l0[d] - l0_direct[d]) <= 1e-12:
                raise AssertionError(f"P6: T_abs Level 0 ({d:+d}) {l0[d]} != direct {l0_direct[d]}")
        return dict(status="computed", **head, claim=claim,
                    t_abs=dict(T=float(tb.T_obs), T_direct=tabs_direct, level0_upper=float(l0[1]),
                               level0_direct_upper=l0_direct[1], label=AD.TAbs.LABEL),
                    seeds=keys.record())

    def summarise(self, cell, recs, n_official):
        comp = [r for r in recs if r["status"] == "computed"]
        claims = [r["claim"] for r in comp]
        k = BS.count(claims, lambda c: c["verdicts"]["two"]["survives"])
        return dict(n_cases=len(recs), n_computed=len(comp), n_unmatched_for_plant=len(recs) - len(comp),
                    signed_survivors_two_sided=k, criterion=CR.p6(k, len(comp)),
                    one_sided_survivors={s: BS.count(claims, lambda c, s=s: c["verdicts"][s]["survives"])
                                         for s in ("+", "-")},
                    T_signed=[c["verdicts"]["two"]["T"] for c in claims],
                    t_abs=dict(values_equal_direct=True,
                               level0_upper_p=[r["t_abs"]["level0_upper"] for r in comp],
                               label="unsigned descriptor, uncalibrated (claims_register.md:311-313): reported only"),
                    leg_rates_two_sided_dstar=BS.leg_rates(claims, "two", 1))


PLANTS = {"P6": P6()}
