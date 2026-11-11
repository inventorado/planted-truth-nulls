"""P22 (functional): multiverse plumbing (RUN_PLAN.md v3.1 §7 P22: "multiverse plumbing (R11) | dk-ctx, V-AAL |
primary matrix through the multiverse path reproduces the primary result; keys common").

For each claim: (1) the primary path - run.prepare on the claim's sources, verdict legs, verdict and descriptor legs
(a1_audit.multiverse.run_cell on the claim's CaseSources); (2) the multiverse path with the PRIMARY matrix
(multiverse.CellSources with the class context's own expression frame), on fresh key objects of the same claim. Asserted:
the verdict legs, the verdict, the descriptor record and the analysis parcels are identical (canonical JSON), and the
seed keys each path drew are the same words. Planted checks the comparison must catch / pass: (3) a cell matrix with one
member gene's value at one parcel scaled by (1 + 1e-6) must give a different T; (4) a cell matrix whose last parcel's
row is missing (a leave-one-donor-out cell losing a parcel) must equal the primary path on the map with that parcel's
value missing (the §4 rule drops it in both), legs and verdict identical.
"""
from __future__ import annotations

import json

import numpy as np

from .. import a3_port as A3
from .. import multiverse as MV
from . import base as BS
from . import common as C
from . import construct as CO
from . import criteria as CR

CELLS = (("set-vs-map", "dk-ctx"), ("decoded-list", "dk-ctx"), ("set-vs-map", "V-AAL"), ("decoded-list", "V-AAL"))


def canon(o) -> str:
    return json.dumps(A3.jsonable(o), sort_keys=True)


class P22(BS.PlantSpec):
    id = "P22"
    module = "p22"
    kind = CR.FUNCTIONAL
    row = "RUN_PLAN §7 P22: multiverse plumbing (R11), dk-ctx and V-AAL: primary matrix through the multiverse path"
    construction = ("C-gene (prereg §6.3), m = 25, a = .9; two-sided claims; verdict and descriptor legs at plant K "
                    "(site 500, species 200, G1-G5 200 sets, J1 100 sets x 500 surrogates, naive joint 500)")
    choices = (
        "PLANT CHOICE (not in §7): the multiverse path is a1_audit.multiverse (new in WP2: CellSources + run_cell); "
        "cells set-vs-map and decoded-list x dk-ctx and V-AAL, 2 maps each (plant id 22, case = 100 x cell index + i).",
        "PLANT CHOICE (not in §7): the claims are two-sided (R1), so the descriptor legs are read at the verdict's d*; "
        "BrainSpan trajectories for G5 as the frozen code reads them (asdg.brainspan.load_trajectories).",
        "PLANT CHOICE (not in §7): planted checks (3) one value of one member gene scaled by 1 + 1e-6 must change T, "
        "(4) a missing parcel row in the cell equals the primary path with that parcel's map value missing.",
    )
    replace_unmatched = True
    cost_s = 90.0

    def cells(self):
        return [BS.Cell(f"{f} / {c}", c, f, (("index", j),)) for j, (f, c) in enumerate(CELLS)]

    def n_official(self, cell):
        return 2

    def case_of(self, cell, i):
        return 100 * int(cell.get("index")) + int(i)

    def run_case(self, cell, i, K):
        k0 = self.keys(cell, i)
        c = CO.cgene(cell.cls, k0.rng(), i)
        if c["status"] != "ok":
            return dict(status="unmatched for plant", S=BS.gene_list(c["S"]), seeds=k0.record())
        S = np.asarray(c["S"], dtype=int)
        genes = C.genes_of(cell.cls, S)
        plan = C.plan_of(cell.form, cell.cls)
        base = C.class_context(cell.cls)
        kw = dict(g6l_mode=C.G6L_MODE, two_sided=True)
        k1, k2 = self.keys(cell, i), self.keys(cell, i)
        prim = MV.run_cell(plan, C.CaseSources(cell.cls, c["y"], genes), 0, K, k1.callables(), descriptors=True, **kw)
        cells = MV.CellSources(C.CaseSources(cell.cls, c["y"], genes), MV.PRIMARY, base.expr)
        mult = MV.run_cell(plan, cells, 0, K, k2.callables(), descriptors=True, **kw)
        bad = []
        for what in ("legs", "verdict", "parcel_ids"):
            if canon(prim[what]) != canon(mult[what]):
                bad.append(f"{what} differ between the primary and the multiverse path")
        if canon(prim["descriptors"]["record"]) != canon(mult["descriptors"]["record"]):
            bad.append("descriptor record differs")
        if k1.record() != k2.record() or k1.used != k2.used:
            bad.append("the seed keys drawn differ")
        # (3) planted: one member value scaled -> T must differ
        e3 = base.expr.copy()
        e3.iloc[0, int(S[0])] = e3.iloc[0, int(S[0])] * (1 + 1e-6)
        k3 = self.keys(cell, i)
        r3 = MV.run_cell(plan, MV.CellSources(C.CaseSources(cell.cls, c["y"], genes), "(zscore, True)", e3), 0, K,
                         k3.callables(), **kw)
        planted_changed = r3["verdict"]["T"] != prim["verdict"]["T"]
        if not planted_changed:
            bad.append("planted (3): a changed matrix value left T unchanged")
        # (4) planted: a missing parcel row = the primary path with that parcel's map value missing
        e4 = base.expr.copy()
        last = int(base.parcel_ids[-1])
        e4.loc[last] = np.nan
        y4 = np.array(c["y"], dtype=float)
        y4[-1] = np.nan
        k4a, k4b = self.keys(cell, i), self.keys(cell, i)
        r4c = MV.run_cell(plan, MV.CellSources(C.CaseSources(cell.cls, c["y"], genes), "leave-one-donor-out 1", e4),
                          0, K, k4a.callables(), **kw)
        r4p = MV.run_cell(plan, C.CaseSources(cell.cls, y4, genes), 0, K, k4b.callables(), **kw)
        if canon(r4c["legs"]) != canon(r4p["legs"]) or canon(r4c["verdict"]) != canon(r4p["verdict"]) \
                or r4c["parcel_ids"] != r4p["parcel_ids"] or last in r4c["parcel_ids"]:
            bad.append("planted (4): a missing parcel row did not equal the primary path without that parcel")
        if bad:
            raise AssertionError("P22: " + "; ".join(bad))
        return dict(status="computed", S=BS.gene_list(S), identical=True, keys_common=True,
                    T=float(prim["verdict"]["T"]), d_star=prim["verdict"]["d_star"],
                    survives=bool(prim["verdict"]["survives"]), planted_3_T_changed=bool(planted_changed),
                    planted_4_dropped_parcel=last, n_parcels=len(prim["parcel_ids"]),
                    context_hash_primary=prim["hashes"]["context"], context_hash_cell=mult["hashes"]["context"],
                    seeds=k1.record())

    def summarise(self, cell, recs, n_official):
        comp = [r for r in recs if r["status"] == "computed"]
        res = "PASS" if len(comp) == n_official else CR.NOT_EVALUATED_DEV % (len(comp), n_official)
        return dict(n_cases=len(recs), n_computed=len(comp),
                    criterion=dict(kind=CR.FUNCTIONAL, result=res,
                                   threshold="primary matrix through the multiverse path = the primary result; keys "
                                             "common; planted (3) caught and (4) equal (a failure stops the plant)"))


PLANTS = {"P22": P22()}
