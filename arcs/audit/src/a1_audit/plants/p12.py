"""P12, its statistical part (correct-leg test) and the two-gene maps (reported) (RUN_PLAN.md v3.1 §7 P12: "component
forms | MIST64 (PLSRegression(2) cumulative R^2, refit on 10,000 permutations and on S1c/S2c, classes < 10 permuted);
dk-ctx fixed component r (parametric Level 0); PLS1 R^2; component k of PLSRegression(K, scale=True) | refit equals
direct (1e-12). A map built from two genes' profiles: results reported, no threshold (...). 20 independent fields:
<= 4 pass at component level (for a site leg at the gate cap .05, P(>= 5 of 20) = .0026)"). 'Refit equals direct' is
WP1's (tests/test_p0.py); RUN_PLAN_amend_1 R34's P12 extension is WP1's (tests/test_amend1.py)."""
from __future__ import annotations

import numpy as np

from . import base as BS
from . import common as C
from . import construct as CO
from . import criteria as CR

# (name, class, component spec, verdict direction): the component forms of the TSV (forms x classes, read by script:
# plsr cumulative 2 on MIST64 with the row's set, 3 rows '+'; fixed on dk-ctx, 3 rows two-sided; PLS1 R^2 on dk-ctx (6)
# and V-AAL (4), '+'; PLSRegression component 3 of 3 on dk-ctx, 1 row '+')
FORMS = (("plsr cumulative R2 (2) / MIST64", "MIST64",
          dict(kind="plsr", n_components=2, cumulative=True, genes_from_set=True), "+"),
         ("fixed component r / dk-ctx", "dk-ctx", dict(kind="fixed", genes_from_set=False), "two"),
         ("PLS1 R2 / dk-ctx", "dk-ctx", dict(kind="pls1-r2", genes_from_set=False), "+"),
         ("PLS1 R2 / V-AAL", "V-AAL", dict(kind="pls1-r2", genes_from_set=False), "+"),
         ("PLSRegression component 3 of 3 / dk-ctx", "dk-ctx",
          dict(kind="plsr", n_components=3, component=3, genes_from_set=False), "+"))
K_PERMUTATION = 10_000  # RUN_PLAN.md:1139 "refit on 10,000 permutations" (orchestrator, WP1 review C4)
N_TWO_GENE = 5


def pc1(cls: str) -> np.ndarray:
    """The class matrix's expression PC1 (column-centred, unscaled; sign: corr(PC score, mean expression over genes) > 0,
    amendment 3's convention, prereg_amend_3.md:146)."""
    X = C.class_context(cls).X
    u, s, _ = np.linalg.svd(X - X.mean(0), full_matrices=False)
    v = u[:, 0]
    return v * np.sign(np.corrcoef(v, X.mean(1))[0, 1])


class P12(BS.PlantSpec):
    id = "P12"
    module = "p12"
    kind = "statistical: " + CR.CORRECT_LEG + " (20 independent fields); two-gene maps " + CR.REPORTED
    row = ("RUN_PLAN §7 P12: component forms; 20 independent fields: <= 4 pass at component level; a map built from two "
           "genes' profiles: results reported")
    construction = ("per component form x class: 20 independent fields (prereg §6.1, generator cell i mod 10) and 5 "
                    "two-gene maps y = z(x_a) + z(x_b); component Level 0 = 10,000 parcel-label permutations with refit "
                    "(R34, leg 8; parametric for the fixed component), site leg S1c / S2c at plant K 500; read 'passes / "
                    "does not pass at component level (Level 0 and site leg at .025)'")
    choices = (
        "PLANT CHOICE (not in §7): the cells are the TSV's component forms x classes: PLSRegression(2) cumulative R^2 "
        "on MIST64 with a set (U8: the row's set; here 25 uniform genes), the fixed component r on dk-ctx, PLS1 R^2 on "
        "dk-ctx and on V-AAL, PLSRegression component 3 of 3 on dk-ctx; the criterion (<= 4 of 20) per cell.",
        "PLANT CHOICE (not in §7): the fixed component is the dk-ctx matrix's expression PC1 (centred, unscaled; sign by "
        "corr with mean expression, amendment 3's convention); the fields are independent of it.",
        "PLANT CHOICE (not in §7): directions as the TSV's rows of each form: R^2 forms one-sided (+), the fixed "
        "component two-sided (R1).",
        "PLANT CHOICE (not in §7): Level-0 permutations K = 10,000 (§7 P12 'refit on 10,000 permutations'; orchestrator "
        "on WP1 review C4); S1c / S2c at plant K = 500 (§7 gives the site leg no count: 'else at plant K', §7 cost "
        "model).",
        "PLANT CHOICE (not in §7): two-gene maps: 5 per cell, y = z(x_a) + z(x_b) on the class's §3.1 matrix; the two "
        "genes are two members of the cell's set where the form uses a set (MIST64 PLSR), else two uniform genes; "
        "cases 10,000 x cell index + i (fields) and + 5,000 + j (two-gene maps).",
    )
    cost_s = 8.0

    def cells(self):
        out = []
        for j, (name, cls, spec, d) in enumerate(FORMS):
            out.append(BS.Cell(f"{name} / fields", cls, "component", (("index", j), ("kind", "fields"))))
            out.append(BS.Cell(f"{name} / two-gene", cls, "component", (("index", j), ("kind", "two-gene"))))
        return out

    def n_official(self, cell):
        return CR.P12_N if cell.get("kind") == "fields" else N_TWO_GENE

    def case_of(self, cell, i):
        return 10_000 * int(cell.get("index")) + (0 if cell.get("kind") == "fields" else 5_000) + int(i)

    def run_case(self, cell, i, K):
        name, cls, spec, d = FORMS[int(cell.get("index"))]
        if int(K["permutation"]) != K_PERMUTATION:  # the driver passes run.PLANT_K_OVERRIDES['P12']
            raise AssertionError(f"P12 needs {K_PERMUTATION} Level-0 permutations, got {K['permutation']}")
        keys = self.keys(cell, i)
        rng = keys.rng()
        ctx = C.class_context(cls)
        S = CO.random_set(cls, rng, 25) if spec["genes_from_set"] else None
        if cell.get("kind") == "fields":
            y, gen, step = CO.field(cls, rng, i)
            built = dict(gen=gen, step=float(step))
        else:
            two = S[:2] if S is not None else rng.choice(ctx.G, size=2, replace=False)
            y = C.z(ctx.X[:, two[0]]) + C.z(ctx.X[:, two[1]])
            built = dict(two_genes=BS.gene_list(two))
        comp = pc1(cls) if spec["kind"] == "fixed" else None
        claim = BS.component_claim(cls, y, dict(spec), keys, K, d, S=S, component_values=comp)
        return dict(status="computed", construction=built, S=None if S is None else BS.gene_list(S), claim=claim,
                    K=K, seeds=keys.record())

    def summarise(self, cell, recs, n_official):
        claims = [r["claim"] for r in recs]
        k = BS.count(claims, lambda c: c["verdict"]["passes_component_level"])
        out = dict(n=len(claims), passes_component_level=k,
                   level0_rate=dict(k=BS.count(claims, lambda c: (c["verdict"]["p_reported"]["Level 0"] or 1) < CR_A),
                                    n=len(claims)),
                   site_rate=dict(k=BS.count(claims, lambda c: (c["verdict"]["p_reported"]["site"] or 1) < CR_A),
                                  n=len(claims)),
                   values=[dict(T=c["verdict"]["T"], p_component=c["verdict"]["p_conjunction"],
                                passes=c["verdict"]["passes_component_level"]) for c in claims])
        if cell.get("kind") == "fields":
            out["criterion"] = CR.p12(k, len(claims))
        else:
            out["criterion"] = dict(kind=CR.REPORTED, result="reported (no threshold: component tests are weak by "
                                                             "design; RUN_PLAN §7 P12)")
        return out


CR_A = C.ALPHA
PLANTS = {"P12": P12()}
