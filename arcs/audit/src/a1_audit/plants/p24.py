"""P24 (statistical; correct-leg test): the species leg of the decoded-list adapter on expression-aligned maps
(RUN_PLAN.md v3.1 §7 P24: "V-AAL, V-DK, dk-ctx replica; amendment 3 §4's F-align targets T-wmod and T-brain at w = .9,
built by its frozen generator (e3_align_plants.py); kinds rand-25, brand-100 and brand-300 scored on every map; n = 300
maps per class x target; plant K | per stratum (class x target x kind), the species-leg rate at .025 passes iff the
one-sided binomial test of rate <= .05 is not rejected at alpha = .01 (<= 24 of 300) ... The set-vs-map leg on the
same maps and sets is reported beside it.").

The maps and sets come from the frozen generator, imported unchanged (e3_align_plants.Ctx: its field generator, its
targets - T-wmod a k = 64 module's score demeaned within class, T-brain d_B = mu_B^w - mu^w - and its set kinds), with
its paired construction y = w z(target) + sqrt(1 - w^2) z(field) at w = .9 only, on plant seeds (§7) instead of its
own; its matrix, classes, centroids and brain>body genes are asserted bit-equal to the production class context's.
"""
from __future__ import annotations

import functools
import math

import numpy as np

from .. import adapters as AD
import e3_align_plants as EA  # noqa: E402  (amendment 3's frozen generator; arcs/audit/src on sys.path via a3_port)
import e3_plants as P  # noqa: E402
from . import base as BS
from . import common as C
from . import criteria as CR

EA_ATLAS = {"V-AAL": "aal", "V-DK": "dk", "dk-ctx": "dk-ctx"}
W = 0.9
KINDS = ("rand-25", "brand-100", "brand-300")
TARGET_OFF = {"wmod": 0, "brain": 10_000}


@functools.lru_cache(maxsize=None)
def ea_ctx(cls: str):
    """The frozen generator's context for the class, asserted equal to the production class context."""
    ea = EA.Ctx(EA_ATLAS[cls])
    base = C.class_context(cls)
    if not (np.array_equal(ea.X, base.X) and np.array_equal(ea.classes, base.classes)
            and np.array_equal(ea.xyz, base.xyz) and np.array_equal(np.sort(ea.brain), np.sort(base.brain))
            and list(ea.U.genes) == list(base.U.genes)):
        raise AssertionError(f"{cls}: e3_align_plants.Ctx differs from the production class context")
    return ea


def map_case(target: str, i: int) -> int:
    return TARGET_OFF[target] + int(i)


def claim_case(mcase: int, kind: str) -> int:
    """PLANT CHOICE: one claim = one (map, set kind): case 1,000,000 + 100 x map case + the generator's KIND_ID."""
    return 1_000_000 + 100 * int(mcase) + int(EA.KIND_ID[kind])


def aligned_map(cls: str, target: str, i: int, keys: C.PlantKeys) -> dict:
    """e3_align_plants.one_plant's paired construction (field, then target, on the map's stream) at w = .9."""
    ea = ea_ctx(cls)
    rng = keys.rng()
    gen, step = P.GENERATOR_CELLS[i % len(P.GENERATOR_CELLS)]
    fld = ea.fg.field(gen, rng, step)
    tgt, t_cluster = ea.target(target, i, rng)
    y = W * EA.z(tgt) + math.sqrt(1 - W * W) * EA.z(fld)
    return dict(y=y, gen=gen, step=float(step), target=target, target_cluster=int(t_cluster), w=W)


def make_set(cls: str, kind: str, t_cluster: int, keys: C.PlantKeys):
    """The generator's make_set on the claim's construction stream (as its r2 = SeedSequence(base + [KIND_ID]))."""
    return ea_ctx(cls).make_set(kind, keys.rng(), t_cluster)


def species_record(sp: dict) -> dict:
    return dict(p={k: C.pdir(v) for k, v in sp["p"].items()}, status=sp["status"], uninformative=sp["uninformative"],
                uninformative_share=sp["uninformative_share"], floors=sp["floors"],
                g6l={k: sp["g6l"].get(k) for k in ("status", "n_used", "draws", "eligible", "pool_jaccard")},
                rejects=C.species_rejects(sp, C.PLUS))


class P24(BS.PlantSpec):
    id = "P24"
    module = "p24"
    kind = "statistical: " + CR.CORRECT_LEG
    row = ("RUN_PLAN §7 P24: species leg of the decoded-list adapter on F-align T-wmod / T-brain maps at w = .9 "
           "(e3_align_plants), kinds rand-25 / brand-100 / brand-300; n = 300 maps per class x target; <= 24 of 300 "
           "per stratum")
    construction = ("e3_align_plants (frozen): y = .9 z(target) + sqrt(.19) z(field), field from generator cell i mod 10, "
                    "target T-wmod or T-brain; on each map the sets rand-25, brand-100, brand-300 (the generator's "
                    "make_set); the decoded-list species leg (G1, G3m, G6s, G6l conditioned, K = 200, G6l plant mode) "
                    "and, beside it, the set-vs-map species leg on the same windows and keys")
    choices = (
        "PLANT CHOICE (not in §7): plant seeds replace the generator's own (§7 'Seeds'): map stream = plant key (24, map "
        "case = 10,000 x [target is T-brain] + i, class id), used in the generator's order (field, then target); set of "
        "kind k = make_set on the claim key (24, 1,000,000 + 100 x map case + KIND_ID[k], class id), as the generator's "
        "r2 = SeedSequence(base + [KIND_ID]); null legs on that claim key's leg words.",
        "PLANT CHOICE (not in §7): the species leg alone is computed (adapter.species_leg, the call verdict.collect_legs "
        "makes, with collect_legs' consistency checks); Level 0 and the site leg are not part of P24's test.",
        "PLANT CHOICE (not in §7): a rejection = all four species legs have a p, max p(+) < .025, the claim is not "
        "uninformative and the species floors are below .025 (amendment 3 §5's species-leg rule, one-sided + as the "
        "frozen rates); a G6l unmatched or degenerate claim is a non-rejection and stays in the denominator (n = 300 "
        "as §7 fixes it); amendment 3's '> 5 % unmatched or degenerate in a generator cell' is reported as a flag.",
        "PLANT CHOICE (not in §7): the set-vs-map species leg beside it uses the same keys and the same G6l windows "
        "(common random numbers; one screen serves both forms, RUN_PLAN §4 'Shared G6l screens').",
        "PLANT CHOICE (not in §7): dk-ctx T-wmod = the generator's 'wmod' target on the single-class replica (a module "
        "score demeaned over the one class; amendment 3 §4 registers T-mod / T-grad / T-brain for the replica).",
    )
    cost_s = 7.0

    def cells(self):
        return [BS.Cell(f"{c} / T-{t}", c, "decoded-list", (("target", t),))
                for c in ("V-AAL", "V-DK", "dk-ctx") for t in ("wmod", "brain")]

    def n_official(self, cell):
        return CR.P24_N

    def case_of(self, cell, i):
        return map_case(cell.get("target"), i)

    def run_case(self, cell, i, K):
        mkeys = self.keys(cell, i)
        mp = aligned_map(cell.cls, cell.get("target"), i, mkeys)
        kinds = {}
        for kind in KINDS:
            ck = C.PlantKeys(self.plant_id, claim_case(mkeys.case, kind), mkeys.class_id)
            S, cs = make_set(cell.cls, kind, mp["target_cluster"], ck)
            pr = C.prepare("decoded-list", cell.cls, mp["y"], S)
            screen = C.g6l_screen(pr, ck, K)
            dl = C.species_only(pr, ck, K, screen)
            svm_ad = AD.make_adapter("set-vs-map", pr.ctx, pr.y, parcel_ids=pr.parcel_ids, S=pr.S)
            svm = C.species_only(pr, ck, K, screen, adapter=svm_ad)
            B = pr.ctx.B
            kinds[kind] = dict(m=int(len(S)), f_over_m=float(B.brain[np.asarray(S)].mean()),
                               c_s_w=float(B.coherence_w(np.asarray(S))), set_clusters=[int(x) for x in cs],
                               decoded_list=species_record(dl), set_vs_map=species_record(svm), seeds=ck.record())
        return dict(status="computed", map={k: v for k, v in mp.items() if k != "y"}, map_sha256=C.R.arr_sha(mp["y"]),
                    kinds=kinds, seeds=mkeys.record())

    def summarise(self, cell, recs, n_official):
        out = dict(n_maps=len(recs), strata={})
        for kind in KINDS:
            rows = [r["kinds"][kind] for r in recs]
            n = len(rows)
            k = BS.count(rows, lambda x: x["decoded_list"]["rejects"])
            k2 = BS.count(rows, lambda x: x["set_vs_map"]["rejects"])
            per_cell = {}
            for r in recs:
                g = f"{r['map']['gen']}/step{r['map']['step']:g}"
                x = r["kinds"][kind]["decoded_list"]
                bad = x["g6l"]["status"] != "ok"
                a, b = per_cell.get(g, (0, 0))
                per_cell[g] = (a + int(bad), b + 1)
            flag = [g for g, (a, b) in per_cell.items() if b and a / b > 0.05]
            out["strata"][kind] = dict(
                n=n, decoded_list_rejections=k, rate=C.rate(k, n), criterion=CR.p24(k, n),
                set_vs_map_rejections_reported=dict(k=k2, n=n, rate=C.rate(k2, n)),
                decoded_list_leg_rates=_leg_rates(rows, "decoded_list"),
                set_vs_map_leg_rates=_leg_rates(rows, "set_vs_map"),
                g6l_not_ok=BS.count(rows, lambda x: x["decoded_list"]["g6l"]["status"] != "ok"),
                uninformative=BS.count(rows, lambda x: x["decoded_list"]["uninformative"]),
                amendment3_unmatched_flag=(f"> 5 % G6l unmatched / degenerate in generator cell(s) {flag}" if flag
                                           else "none above 5 %"))
        return out


def _leg_rates(rows: list, form: str) -> dict:
    """Each species sub-leg's one-sided (+) rate at .025 over the stratum (a leg without a p is a non-rejection)."""
    out = {}
    for leg in ("G1", "G3m", "G6s", "G6l"):
        k = BS.count(rows, lambda x, leg=leg: C.below(x[form]["p"][leg]))
        out[leg] = dict(k=k, n=len(rows), rate=C.rate(k, len(rows)))
    return out


PLANTS = {"P24": P24()}
