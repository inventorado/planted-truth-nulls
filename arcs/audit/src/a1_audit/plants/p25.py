"""P25 (statistical): planted flawed species legs the P24 regime must catch (RUN_PLAN.md v3.1 §7 P25: "the decoded-list
adapter through the production path, each flaw behind a plant-only flag; V-AAL and V-DK; n = 500 each: (a) the v2
species max (G1, universe-centred G6s, G6l; no brain matching: amendment 3 §4's reference leg) on T-brain x brand-300 x
w = .9; (b) the minimum instead of the maximum over the four species legs, on (a)'s maps; (c) unconditioned G1 and G3m
nulls on a between-class plant: S = 25 members of the module-generator cluster (amendment 3 §4) whose mean profile has
the largest between-class share of variance, y = z(s_B(S) - s_B-bar) + z(a within-class field), with s_B-bar the mean
class profile over all genes | each flawed leg must reject 'rate <= .025' at alpha = .01 (>= 22 of 500) ... The correct
legs' rates on the same maps are reported, and (c)'s correct species leg must pass P24's test at n = 500 (<= 37 of
500)").

Must-catch tests: (a), (b), (c)-G1, (c)-G3m; correct-leg test: (c)'s correct species leg. The flawed legs are
a1_audit.plants.flaws, enabled only inside this plant (flaws.enabled(flag, 'P25', 'plant')).
"""
from __future__ import annotations

import functools

import numpy as np

from . import base as BS
from . import common as C
from . import construct as CO
from . import criteria as CR
from . import flaws as FL
from . import p24

N = CR.P25_N


@functools.lru_cache(maxsize=None)
def between_cluster(cls: str) -> dict:
    """The module-generator cluster (e3_align_plants.Ctx.mods: k = 64 spherical k-means, amendment 3 §4) of >= 25
    members whose mean profile (mean of its members' columns of the §3.1 matrix) has the largest between-class share of
    variance (1 - var(within-class part) / var(profile), WithinClassBasis.bshare's definition)."""
    ea = p24.ea_ctx(cls)
    best, best_share, shares = None, -1.0, {}
    for j, g in enumerate(ea.mods):
        if len(g) < 25:
            continue
        p = ea.X[:, g].mean(1)
        tot = p.var()
        share = float(1.0 - ea.B.within_y(p).var() / tot) if tot > 0 else 0.0
        shares[j] = share
        if share > best_share:
            best, best_share = j, share
    return dict(cluster=int(best), share=best_share, size=int(len(ea.mods[best])), n_eligible=len(shares),
                median_share=float(np.median(list(shares.values()))))


class P25(BS.PlantSpec):
    id = "P25"
    module = "p25"
    kind = ("statistical: " + CR.MUST_CATCH + " ((a), (b), (c) G1, (c) G3m) and " + CR.CORRECT_LEG +
            " ((c)'s correct species leg)")
    row = ("RUN_PLAN §7 P25: (a) v2 species max on T-brain x brand-300 x w = .9; (b) min over the four species legs; "
           "(c) unconditioned G1 / G3m on a between-class plant; V-AAL, V-DK, n = 500; flawed >= 22 / 500; (c) correct "
           "<= 37 / 500")
    construction = ("(a)/(b): e3_align_plants T-brain maps at w = .9 with a brand-300 set (as P24); the correct "
                    "decoded-list species leg and, behind plant-only flags, the v2 species max and the species minimum. "
                    "(c): S = 25 members of the class's highest between-class-share module (amendment 3 §4's module "
                    "generator); y = z(s_B(S) - s_B-bar) + z(within-class field) on the decoded-list's z-scored matrix; "
                    "the correct species leg and, behind a plant-only flag, unconditioned G1 / G3m")
    choices = (
        "PLANT CHOICE (not in §7): (a)/(b) maps = P24's construction (e3_align_plants, T-brain, w = .9; map case = i, "
        "claim case = 1,000,000 + 100 i + KIND_ID['brand-300']); (c) cases 100,000 + i.",
        "PLANT CHOICE (not in §7): the v2 G1 / G6s and (c)'s unconditioned G1 / G3m reuse the correct legs' streams "
        "(legs 2, 3, 4: the same null sets / sign draws scored the flawed way); the v2 G6l rescores the claim's own "
        "windows (as frozen); see flaws.py.",
        "PLANT CHOICE (not in §7): a flawed leg 'rejects' iff its p(+) < .025 (one-sided +, as the frozen rates); the "
        "v2 max has no p (non-rejection) when the claim's G6l is unmatched / degenerate; the minimum (b) is over the "
        "legs that have a p.",
        "PLANT CHOICE (not in §7): (c)'s s_B(S) and s_B-bar are the class means of S's set score and of the mean profile "
        "over all genes on the decoded-list's z-scored matrix (adapters.z_basis, the basis R2 decomposes r_g on); the "
        "'within-class field' is a prereg §6.1 field (generator i mod 5, class step 0) demeaned within each class; the "
        "two terms z-scored and added with weight 1 each, as written; S = 25 members drawn uniformly from the chosen "
        "cluster (fixed per class: the largest between-class share among clusters of >= 25 members), S before the "
        "field on the case's stream.",
        "PLANT CHOICE (not in §7): (c)'s correct species leg uses P24's rejection rule (C.species_rejects).",
    )
    cost_s = 4.0

    def cells(self):
        return ([BS.Cell(f"{c} / (a)(b) T-brain brand-300", c, "decoded-list", (("part", "ab"),))
                 for c in ("V-AAL", "V-DK")]
                + [BS.Cell(f"{c} / (c) between-class", c, "decoded-list", (("part", "c"),)) for c in ("V-AAL", "V-DK")])

    def n_official(self, cell):
        return N

    def case_of(self, cell, i):
        return int(i) if cell.get("part") == "ab" else 100_000 + int(i)

    def run_case(self, cell, i, K):
        if cell.get("part") == "ab":
            return self._ab(cell, i, K)
        return self._c(cell, i, K)

    def _ab(self, cell, i, K):
        mkeys = self.keys(cell, i)
        mp = p24.aligned_map(cell.cls, "brain", i, mkeys)
        ck = C.PlantKeys(self.plant_id, p24.claim_case(mkeys.case, "brand-300"), mkeys.class_id)
        S, _ = p24.make_set(cell.cls, "brand-300", mp["target_cluster"], ck)
        pr = C.prepare("decoded-list", cell.cls, mp["y"], S)
        screen = C.g6l_screen(pr, ck, K)
        sp = C.species_only(pr, ck, K, screen)
        with FL.enabled("v2-species-max", "P25", "plant"):
            v2 = FL.v2_species_max(pr.adapter, int(K["species"]), ck.seed_of, screen[0], sp["g6l"]["status"])
        with FL.enabled("species-min", "P25", "plant"):
            mn = FL.species_min({k: v for k, v in sp["p"].items()})
        rec = dict(correct=p24.species_record(sp),
                   v2=dict(p={k: C.pdir(v) for k, v in v2["p"].items()}, p_max=C.pdir(v2["p_max"]),
                           rejects=C.below(C.pdir(v2["p_max"]))),
                   minimum=dict(p_min=C.pdir(mn["p_min"]), n_legs=mn["n_legs"], rejects=C.below(C.pdir(mn["p_min"]))))
        return dict(status="computed", part="ab", map={k: v for k, v in mp.items() if k != "y"},
                    map_sha256=C.R.arr_sha(mp["y"]), m=int(len(S)), **rec, seeds=ck.record())

    def _c(self, cell, i, K):
        keys = self.keys(cell, i)
        rng = keys.rng()
        bc = between_cluster(cell.cls)
        ea = p24.ea_ctx(cell.cls)
        S = rng.choice(ea.mods[bc["cluster"]], size=25, replace=False)
        gen = CO.GENERATORS[i % len(CO.GENERATORS)]
        fld = CO.field_kind(cell.cls, rng, gen, 0.0)
        ctx = C.class_context(cell.cls)
        Bz = C.AD.z_basis(ctx)
        sB = Bz.parts(np.asarray(S))[1]                       # class means of S's z-scored set score
        sB_bar = Bz.X.mean(1) - Bz.within_y(Bz.X.mean(1))     # class means of the all-gene mean profile
        y = C.z(sB - sB_bar) + C.z(Bz.within_y(fld))
        pr = C.prepare("decoded-list", cell.cls, y, S)
        screen = C.g6l_screen(pr, keys, K)
        sp = C.species_only(pr, keys, K, screen)
        with FL.enabled("unconditioned-g1-g3m", "P25", "plant"):
            un = FL.unconditioned_g1_g3m(pr.adapter, int(K["species"]), keys.seed_of)
        rec = dict(correct=p24.species_record(sp),
                   unconditioned={k: dict(p=C.pdir(v), rejects=C.below(C.pdir(v))) for k, v in un["p"].items()})
        return dict(status="computed", part="c", cluster=bc, gen=gen, S=BS.gene_list(S), map_sha256=C.R.arr_sha(y),
                    **rec, seeds=keys.record())

    def summarise(self, cell, recs, n_official):
        n = len(recs)
        corr_k = BS.count(recs, lambda r: r["correct"]["rejects"])
        legs = {}
        for leg in ("G1", "G3m", "G6s", "G6l"):
            k = BS.count(recs, lambda r, leg=leg: C.below(r["correct"]["p"][leg]))
            legs[leg] = dict(k=k, n=n, rate=C.rate(k, n))
        if cell.get("part") == "ab":
            ka = BS.count(recs, lambda r: r["v2"]["rejects"])
            kb = BS.count(recs, lambda r: r["minimum"]["rejects"])
            return dict(n=n, criteria={"(a) v2 species max": CR.p25_flawed(ka, n),
                                       "(b) minimum over the four species legs": CR.p25_flawed(kb, n)},
                        flawed_rates={"(a)": dict(k=ka, n=n, rate=C.rate(ka, n)),
                                      "(b)": dict(k=kb, n=n, rate=C.rate(kb, n))},
                        correct_species_leg_reported=dict(k=corr_k, n=n, rate=C.rate(corr_k, n)),
                        correct_leg_rates=legs,
                        basis_note="(a)'s basis is borrowed: .086 / .133 were measured on the set-vs-map adapter "
                                   "(RUN_PLAN §7 P25)")
        kg1 = BS.count(recs, lambda r: r["unconditioned"]["G1 (unconditioned)"]["rejects"])
        kg3 = BS.count(recs, lambda r: r["unconditioned"]["G3m (unconditioned)"]["rejects"])
        return dict(n=n, cluster=recs[0]["cluster"] if recs else None,
                    criteria={"(c) unconditioned G1": CR.p25_flawed(kg1, n),
                              "(c) unconditioned G3m": CR.p25_flawed(kg3, n),
                              "(c) correct species leg": CR.p25_correct(corr_k, n)},
                    flawed_rates={"G1": dict(k=kg1, n=n, rate=C.rate(kg1, n)),
                                  "G3m": dict(k=kg3, n=n, rate=C.rate(kg3, n))},
                    correct_species_leg=dict(k=corr_k, n=n, rate=C.rate(corr_k, n)), correct_leg_rates=legs)


PLANTS = {"P25": P25()}
