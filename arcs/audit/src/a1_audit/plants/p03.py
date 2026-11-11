"""P3a (functional) and P3b (statistical; correct-leg test): C-gene plants on set-vs-map (RUN_PLAN.md v3.1 §7).

P3a: "production path = frozen engine (functional) | C-gene plants (prereg §6.3 construction, m = 25, a = .9), 20 per
class: V-AAL, V-DK, dk-ctx replica; set-vs-map | the production runner and the frozen engine functions (src/asdg
spatial, species and verdict, called directly as A3's h_verdicts does), given identical generator states, return
bit-identical leg p's, statuses and verdicts".
P3b: "catch rate (statistical; correct-leg test) | the same construction, n = 100 per class, plant K | V-AAL fails iff
<= 52 / 100 survive and V-DK iff <= 44 / 100 ... dk-ctx: reported only (no frozen rate)".

The frozen engine side of P3a is a3_port.claim_verdict / species_draws (the bit-identity-tested copies of A3's
h_verdicts.claim_verdict / species_draws, P0 (a)), called on the class context with the claim's own keys, one-sided
in each direction, its G6l windows drawn by the engine's own plant-mode call (asdg.species.WithinClassBasis.g6l_sets,
exact=False, on the G6l stream) - not the production screen object.
"""
from __future__ import annotations

import math

import numpy as np

from .. import a3_port as A3
from . import base as BS
from . import common as C
from . import construct as CO
from . import criteria as CR

CLASSES = ("V-AAL", "V-DK", "dk-ctx")
CHOICES_COMMON = (
    "PLANT CHOICE (not in §7): the claims are one-sided in the registered direction + (the C-gene plants are positive; "
    "the frozen battery's catch, P3b's basis, was measured one-sided +: e3_plants.one_plant sign = +1); the two-sided R1 "
    "verdict on the same legs is reported beside it, without a threshold.",
    "PLANT CHOICE (not in §7): the C-gene construction is e3_plants.one_plant's C-gene branch line for line (draw order "
    "S, G2 (500 coexpression-matched sets), field, y; generator cell i mod 10; the 3 PCs of the class's z-scored "
    "matrix), on the claim's construction stream; the dk-ctx replica uses V-DK's 34 left cortical parcels.",
)


class P3a(BS.PlantSpec):
    id = "P3a"
    module = "p03"
    kind = CR.FUNCTIONAL
    row = "RUN_PLAN §7 P3a: production path = frozen engine; C-gene plants, m = 25, a = .9, 20 per class"
    construction = ("C-gene (prereg §6.3; e3_plants.one_plant's C-gene branch), m = 25, a = .9, set-vs-map, plant K "
                    "(site 500, species 200, G6l plant mode); production legs vs a3_port.claim_verdict / species_draws "
                    "with the same keys, both directions")
    choices = CHOICES_COMMON + (
        "PLANT CHOICE (not in §7): plant id 3, cases 0..19 per class (P3b uses 1000 + j).",
        "PLANT CHOICE (not in §7): compared with Python == (bit identity): Level 0, S1c, S2c, G1, G3m, G6s, G6l one-sided "
        "p's in both directions, every floor, the G6l status and windows, the uninformative share, and the one-sided "
        "verdict (status, survival, conjunction p); a planted one-ulp change of one engine p must be reported by the "
        "comparator (i = 0 of every class).",
        "PLANT CHOICE (not in §7): a plant whose G2 is unmatched is recorded and not compared (it has no map).",
    )
    cost_s = 20.0

    def cells(self):
        return [BS.Cell(c, c, "set-vs-map") for c in CLASSES]

    def n_official(self, cell):
        return 20

    def case_of(self, cell, i):
        return int(i)

    def run_case(self, cell, i, K):
        keys = self.keys(cell, i)
        c = CO.cgene(cell.cls, keys.rng(), i)
        head = dict(construction={k: v for k, v in c.items() if k not in ("S", "y")}, S=BS.gene_list(c["S"]))
        if c["status"] != "ok":
            return dict(status="unmatched for plant", **head, seeds=keys.record())
        y, S = c["y"], np.asarray(c["S"], dtype=int)
        pr = C.prepare("set-vs-map", cell.cls, y, S)
        screen = C.g6l_screen(pr, keys, K)
        legs = C.full_legs(pr, keys, K, screen)
        vplus = C.assemble(legs, "+")
        eng = engine(cell.cls, y, S, K, lambda: self.keys(cell, i))
        mism = compare(legs, vplus, screen, eng)
        planted = None
        if i == 0:
            bad = dict(eng)
            bad["+"] = dict(eng["+"])
            bad["+"]["p_S1c"] = math.nextafter(eng["+"]["p_S1c"], 2.0)
            planted = compare(legs, vplus, screen, bad)
            if not planted:
                raise AssertionError("P3a comparator missed a planted one-ulp change")
        return dict(status="computed", **head, identical=not mism, mismatches=mism,
                    planted_mismatch_reported=planted, verdict_plus=C.compact_verdict(vplus),
                    legs=C.leg_table(legs), extra=C.legs_extra(legs),
                    engine={d: {k: v for k, v in e.items() if k in ("p_level0_one_sided", "p_S1c", "p_S2c", "p_G1",
                                                                     "p_G3m", "p_G6s", "p_G6l", "status", "survives",
                                                                     "p_verdict")}
                            for d, e in eng.items() if d in ("+", "-")},
                    seeds=keys.record())

    def summarise(self, cell, recs, n_official):
        comp = [r for r in recs if r["status"] == "computed"]
        bad = [r["case"] for r in comp if not r["identical"]]
        res = "PASS" if (not bad and len(recs) == n_official) else (
            "FAIL (functional: a code defect; RUN_PLAN §7, §17)" if bad else
            CR.NOT_EVALUATED_DEV % (len(recs), n_official))
        return dict(n=len(recs), n_computed=len(comp), n_unmatched=len(recs) - len(comp), n_identical=len(comp) - len(bad),
                    cases_not_identical=bad, mismatches={r["case"]: r["mismatches"] for r in comp if r["mismatches"]},
                    criterion=dict(kind=CR.FUNCTIONAL, result=res, threshold="every computed plant bit-identical"),
                    survivors_one_sided_plus=BS.count(comp, lambda r: r["verdict_plus"]["survives"]))


def compare(legs: dict, vplus: dict, screen, eng: dict) -> list:
    """The mismatches between the production legs / one-sided + verdict and the frozen engine's records (==)."""
    out = []

    def eq(a, b, what):
        same = (a is None and b is None) or (a is not None and b is not None and (
            (isinstance(a, float) and isinstance(b, float) and math.isnan(a) and math.isnan(b)) or a == b))
        if not same:
            out.append(f"{what}: production {a!r} != engine {b!r}")

    for sym, d in (("+", 1), ("-", -1)):
        e = eng[sym]
        eq(float(legs["level0"]["p"][d]), float(e["p_level0_one_sided"]), f"Level 0 ({sym})")
        for leg in ("S1c", "S2c"):
            eq(float(legs["site"][leg]["p"][d]), float(e[f"p_{leg}"]), f"{leg} ({sym})")
        for leg in ("G1", "G3m", "G6s", "G6l"):
            p = legs["species"]["p"][leg]
            ev = e[f"p_{leg}"]
            eq(None if p is None else float(p[d]), None if (ev is None or math.isnan(ev)) else float(ev), f"{leg} ({sym})")
        for leg in ("S1c", "S2c"):
            eq(float(legs["site"][leg]["floor"]), float(e["site_info"][leg]["floor"]), f"{leg} floor ({sym})")
        for leg, f in legs["species"]["floors"].items():
            eq(float(f), float(e["floors_raw"][f"species_{leg}"]), f"{leg} floor ({sym})")
        eq(legs["species"]["status"]["G6l"], e["g6l"]["status"], f"G6l status ({sym})")
        eq(float(legs["uninformative"]["share"]), float(e["uninformative_share"]), f"uninformative share ({sym})")
    e = eng["+"]
    eq(vplus["primary_status"], e["status"], "verdict status (+)")
    eq(bool(vplus["survives"]), bool(e["survives"]), "verdict survives (+)")
    if vplus["primary_status"] == "ok":
        eq(float(vplus["p_conjunction"]), float(e["p_verdict"]), "conjunction p (+)")
    s_prod, s_eng = screen[0], eng["g6l_sets"]
    if (s_prod is None) != (s_eng is None) or (s_prod is not None and not np.array_equal(s_prod, s_eng)):
        out.append("G6l windows differ")
    return out


class P3b(BS.PlantSpec):
    id = "P3b"
    module = "p03"
    kind = "statistical: " + CR.CORRECT_LEG
    row = ("RUN_PLAN §7 P3b: the same construction, n = 100 per class, plant K; V-AAL fails iff <= 52 / 100 survive and "
           "V-DK iff <= 44 / 100; dk-ctx reported only")
    construction = P3a.construction.split("; production legs")[0] + "; production legs, one-sided + verdict"
    choices = CHOICES_COMMON + (
        "PLANT CHOICE (not in §7): plant id 3, cases 1000 + j per class; a plant whose G2 is unmatched ('unmatched for "
        "plant', the frozen battery's status) is recorded and replaced by the next case, so n = 100 COMPUTED plants per "
        "class (the frozen catch 197 / 296 and 175 / 299 counted computed plants only, prereg_amend_3.md:193-194).",
        "PLANT CHOICE (not in §7): 'survive' = the one-sided (+) A1 verdict survives (status ok and conjunction p < .025; "
        "any other status is a miss, as the frozen catch counted it).",
    )
    replace_unmatched = True
    cost_s = 10.0

    def cells(self):
        return [BS.Cell(c, c, "set-vs-map") for c in CLASSES]

    def n_official(self, cell):
        return CR.P3B_N

    def case_of(self, cell, i):
        return 1000 + int(i)

    def run_case(self, cell, i, K):
        return cgene_case(self, cell, i, K, "set-vs-map", ("+", "two"))

    def summarise(self, cell, recs, n_official):
        return catch_summary(cell, recs, n_official, CR.p3b(cell.cls, *_surv(recs)), "+")


def _surv(recs):
    comp = [r for r in recs if r["status"] == "computed"]
    return BS.count(comp, lambda r: r["claim"]["verdicts"]["+"]["survives"]), len(comp)


def cgene_case(spec, cell, i, K, form, verdict_specs, sign: int = 1) -> dict:
    """A C-gene plant (construct.cgene) through the production full-verdict path."""
    keys = spec.keys(cell, i)
    c = CO.cgene(cell.cls, keys.rng(), i, sign=sign)
    head = dict(construction={k: v for k, v in c.items() if k not in ("S", "y")}, S=BS.gene_list(c["S"]))
    if c["status"] != "ok":
        return dict(status="unmatched for plant", **head, seeds=keys.record())
    claim = BS.full_claim(form, cell.cls, c["y"], np.asarray(c["S"], dtype=int), keys, K, verdict_specs)
    return dict(status="computed", **head, claim=claim, map_sha256=C.R.arr_sha(c["y"]), seeds=keys.record())


def catch_summary(cell, recs, n_official, criterion: dict, spec: str, d: int = 1) -> dict:
    comp = [r for r in recs if r["status"] == "computed"]
    claims = [r["claim"] for r in comp]
    k = BS.count(claims, lambda c: c["verdicts"][spec]["survives"])
    out = dict(n_cases=len(recs), n_computed=len(comp), n_unmatched_for_plant=len(recs) - len(comp),
               survivors=k, rate=C.rate(k, len(comp)), direction=spec, criterion=criterion,
               leg_rates=BS.leg_rates(claims, spec, d), statuses=BS.statuses(claims, spec) if claims else {})
    if claims and "two" in claims[0]["verdicts"]:
        k2 = BS.count(claims, lambda c: c["verdicts"]["two"]["survives"])
        out["two_sided_R1_survivors (reported, no threshold)"] = dict(k=k2, n=len(comp), rate=C.rate(k2, len(comp)))
    return out


# ---- the frozen engine side of P3a ----------------------------------------------------------------------------
def engine(cls: str, y, S, K: dict, keys_factory) -> dict:
    """The frozen engine, called as A3's h_verdicts does (a3_port.claim_verdict / species_draws, the P0-tested copies),
    one-sided in each direction, on FRESH key objects of the same claim (keys_factory(): the same SeedSequences); its
    G6l windows from the engine's own plant-mode call WithinClassBasis.g6l_sets(S, K, rng, exact=False) on the G6l
    stream (amendment 3 §3 plant mode: budget 5 K, stop at K accepted)."""
    base = C.class_context(cls)
    S = np.asarray(S, dtype=int)
    out = {}
    for sym, d in (("+", 1), ("-", -1)):
        k = keys_factory()
        sets, info = base.B.g6l_sets(S, int(K["species"]), np.random.default_rng(k.seed_of("G6l")), exact=False)
        info = dict(info, n_used=0 if sets is None else int(len(sets)))
        dr = A3.species_draws(base, S, int(K["species"]), k.seed_of, g6l=(sets, info))
        out[sym] = A3.claim_verdict(base, y, S, int(K["site"]), k.seed_of, two_sided=False, direction=d, draws=dr,
                                    parcel_ids=base.parcel_ids)
        out["g6l_sets"] = sets
    return out


PLANTS = {"P3a": P3a(), "P3b": P3b()}
