"""P26 (statistical): the site leg of the new adapters (RUN_PLAN.md v3.1 §7 P26: "decoded-list (per-gene r recomputed
per surrogate) and PLS-enrichment (refit) x V-AAL, V-DK, dk-ctx; independent fields (§6.1 generators) with class step
1 (step 0 in dk-ctx); S = rand-25; n = 300 per class; 500 surrogates each of S1c and S2c | the site-leg rate at .025
passes iff <= 24 of 300 (P24's criterion) ... Planted flaw (must-catch): within-class parcel-label permutation in place
of S1c / S2c must reject 'rate <= .025' at alpha = .01 (>= 15 of 300)").

Correct-leg test: each adapter's site leg (max(S1c, S2c), the adapter's site_leg: the call verdict.collect_legs makes).
Must-catch test: the within-class permutation leg (a1_audit.plants.flaws, enabled only inside this plant).
"""
from __future__ import annotations

import math

import numpy as np

from . import base as BS
from . import common as C
from . import construct as CO
from . import criteria as CR
from . import flaws as FL

FORMS = ("decoded-list", "PLS-enrichment")
K_PERM = 500


class P26(BS.PlantSpec):
    id = "P26"
    module = "p26"
    kind = "statistical: " + CR.CORRECT_LEG + " (site leg) and " + CR.MUST_CATCH + " (planted permutation leg)"
    row = ("RUN_PLAN §7 P26: site leg of decoded-list and PLS-enrichment x V-AAL, V-DK, dk-ctx; independent fields, "
           "class step 1 (0 in dk-ctx); S = rand-25; n = 300; site <= 24 / 300; planted within-class permutation >= 15 / "
           "300")
    construction = ("y = an independent field (prereg §6.1 generator i mod 5; class step 1, 0 in dk-ctx); S = 25 uniform "
                    "genes; each adapter's site leg (S1c, S2c at 500 surrogates, the form's T refit per surrogate) and, "
                    "behind a plant-only flag, 500 within-class parcel-label permutations in their place")
    choices = (
        "PLANT CHOICE (not in §7): generator = the five §6.1 generators in rotation (i mod 5), the class step fixed by "
        "§7; S drawn before the field on the case's construction stream; plant id 26, cases 0..299.",
        "PLANT CHOICE (not in §7): both adapters on the same map, set and leg keys (the same S1c / S2c surrogates: common "
        "random numbers); the correct-leg and must-catch tests are applied per adapter x class.",
        "PLANT CHOICE (not in §7): a rejection = p(+) < .025 (one-sided +, the direction the frozen §6.4 gates and the "
        "naive-Level-0 basis were measured in); the site leg's p = max(p_S1c, p_S2c) (prereg_amend_3.md:74).",
        "PLANT CHOICE (not in §7): the permutation leg has K = 500 permutations on the plant-only leg word 90 "
        "(flaws.within_class_permutation).",
    )
    cost_s = 9.0

    def cells(self):
        return [BS.Cell(c, c, None) for c in ("V-AAL", "V-DK", "dk-ctx")]

    def n_official(self, cell):
        return CR.P26_N

    def case_of(self, cell, i):
        return int(i)

    def run_case(self, cell, i, K):
        keys = self.keys(cell, i)
        rng = keys.rng()
        S = CO.random_set(cell.cls, rng, 25)
        gen = CO.GENERATORS[i % len(CO.GENERATORS)]
        step = 0.0 if cell.cls == "dk-ctx" else 1.0
        y = CO.field_kind(cell.cls, rng, gen, step)
        out = {}
        for form in FORMS:
            pr = C.prepare(form, cell.cls, y, S)
            site = pr.adapter.site_leg(int(K["site"]), keys.seed_of)
            for leg in ("S1c", "S2c"):
                for d in (1, -1):
                    v = float(site[leg]["p"][d])
                    if not (math.isfinite(v) and 0.0 <= v <= 1.0):
                        raise ValueError(f"{form} {leg}: p {v!r}")
            p_site = {d: max(site["S1c"]["p"][d], site["S2c"]["p"][d]) for d in (1, -1)}
            with FL.enabled("within-class-permutation", "P26", "plant"):
                perm = FL.within_class_permutation(pr.adapter, K_PERM,
                                                   keys.seed_of("within-class permutation (plant only)"))
            out[form] = dict(T=float(pr.adapter.T_obs), S1c=C.pdir(site["S1c"]["p"]), S2c=C.pdir(site["S2c"]["p"]),
                             site=C.pdir(p_site), site_rejects=C.below(C.pdir(p_site)),
                             site_seeds={k: int(site[k]["seed"]) for k in ("S1c", "S2c")},
                             site_exact={k: bool(site[k]["info"]["exact"]) for k in ("S1c", "S2c")},
                             permutation=C.pdir(perm["p"]), permutation_rejects=C.below(C.pdir(perm["p"])))
        return dict(status="computed", gen=gen, step=step, S=BS.gene_list(S), map_sha256=C.R.arr_sha(y), forms=out,
                    seeds=keys.record())

    def summarise(self, cell, recs, n_official):
        n = len(recs)
        crit, rates = {}, {}
        for form in FORMS:
            ks = BS.count(recs, lambda r, f=form: r["forms"][f]["site_rejects"])
            kp = BS.count(recs, lambda r, f=form: r["forms"][f]["permutation_rejects"])
            crit[f"{form}: site leg"] = CR.p26_site(ks, n)
            crit[f"{form}: planted within-class permutation"] = CR.p26_planted(kp, n)
            rates[form] = dict(site=dict(k=ks, n=n), permutation=dict(k=kp, n=n),
                               S1c=dict(k=BS.count(recs, lambda r, f=form: C.below(r["forms"][f]["S1c"])), n=n),
                               S2c=dict(k=BS.count(recs, lambda r, f=form: C.below(r["forms"][f]["S2c"])), n=n))
        return dict(n=n, criteria=crit, rates=rates)


PLANTS = {"P26": P26()}
