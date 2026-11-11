"""The plant interface the driver runs (a1_audit.plants.driver), and the full-verdict claim every plant module shares.

A plant module defines PLANTS = {id: PlantSpec}. A PlantSpec names its cells (form x class x ...), the official n of
each cell (RUN_PLAN §7), how a cell's i-th case maps to a case number (the seed word, common.PlantKeys), and
run_case / summarise. run_case returns a JSON-able record with status 'computed' or 'unmatched for plant'; a plant
with replace_unmatched draws further cases (in case order) until n are computed (the frozen battery's convention:
'denominator = computed plants', prereg_amend_3.md:193-194).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from . import common as C


@dataclass(frozen=True)
class Cell:
    name: str
    cls: str
    form: str | None = None
    extra: tuple = field(default_factory=tuple)

    def get(self, key, default=None):
        return dict(self.extra).get(key, default)

    @property
    def slug(self) -> str:
        return "".join(ch if ch.isalnum() or ch in "-_." else "_" for ch in self.name)


class PlantSpec:
    id = "P?"
    module = "?"
    kind = "?"
    row = "?"
    construction = "?"
    choices: tuple = ()
    replace_unmatched = False
    cost_s = 10.0          # seconds per case (DEV-measured, driver.COSTS overrides; LPT ordering and estimates)

    @property
    def plant_id(self) -> int:
        return C.plant_int(self.id)

    def cells(self) -> list[Cell]:
        raise NotImplementedError

    def n_official(self, cell: Cell) -> int:
        raise NotImplementedError

    def case_of(self, cell: Cell, i: int) -> int:
        raise NotImplementedError

    def keys(self, cell: Cell, i: int) -> C.PlantKeys:
        case = self.case_of(cell, i)
        C.SD.check_plant_case(self.id, case)   # seeds.PLANT_CASE_RANGES (P3a / P3b kept apart)
        return C.PlantKeys(self.plant_id, case, C.class_id(cell.cls))

    def run_case(self, cell: Cell, i: int, K: dict) -> dict:
        raise NotImplementedError

    def summarise(self, cell: Cell, recs: list, n_official: int) -> dict:
        raise NotImplementedError

    def finish(self, cell_summaries: dict) -> dict:
        """Plant-level outcome: every criterion record found in the cell summaries (keys 'criterion' / 'criteria' at
        any depth), with counts of PASS / FAIL / CAUGHT / NOT CAUGHT / not evaluated / reported."""
        found = []

        def walk(o, path):
            if isinstance(o, dict):
                for k, v in o.items():
                    if k == "criterion" and isinstance(v, dict) and "result" in v:
                        found.append((path, v))
                    elif k == "criteria" and isinstance(v, dict):
                        for kk, vv in v.items():
                            if isinstance(vv, dict) and "result" in vv:
                                found.append((path + [kk], vv))
                    else:
                        walk(v, path + [k])

        for name, s in cell_summaries.items():
            walk(s, [name])
        res = [str(v["result"]) for _, v in found]
        return dict(n_criteria=len(found),
                    n_PASS=sum(r.startswith("PASS") for r in res), n_FAIL=sum(r.startswith("FAIL") for r in res),
                    n_CAUGHT=sum(r.startswith("CAUGHT") for r in res),
                    n_NOT_CAUGHT=sum(r.startswith("NOT CAUGHT") for r in res),
                    n_not_evaluated=sum(r.startswith("not evaluated") for r in res),
                    n_reported=sum(r.startswith("reported") for r in res),
                    criteria=[dict(where=" / ".join(map(str, p)), **v) for p, v in found])

    def describe(self) -> dict:
        return dict(id=self.id, plant_id=self.plant_id, module=f"a1_audit.plants.{self.module}", kind=self.kind,
                    row=self.row, construction=self.construction, plant_choices=list(self.choices),
                    replace_unmatched=self.replace_unmatched)


# ---- the full-verdict claim (run.prepare -> plant-mode G6l screen -> run.g_legs -> assemble_verdict_a1) -------------
def full_claim(form: str, cls: str, y, S, keys: C.PlantKeys, K: dict, specs=("+",)) -> dict:
    """One full-verdict claim through the production calls; verdicts assembled for each direction spec ('+', '-',
    'two') from the same legs. Returns compact records (no null array)."""
    pr = C.prepare(form, cls, y, S)
    screen = C.g6l_screen(pr, keys, K)
    legs = C.full_legs(pr, keys, K, screen)
    out = dict(form=form, legs=C.leg_table(legs), extra=C.legs_extra(legs),
               verdicts={s: C.compact_verdict(C.assemble(legs, s)) for s in specs})
    return out


def component_claim(cls: str, y, comp_spec: dict, keys: C.PlantKeys, K: dict, spec: str, S=None,
                    component_values=None) -> dict:
    """One component claim (prereg §4.7; R34) through run.prepare / run.g_legs / assemble_verdict_a1."""
    pr = C.prepare("component", cls, y, S, component=comp_spec, component_values=component_values)
    legs = C.full_legs(pr, keys, K)
    v = C.assemble(legs, spec)
    return dict(form=pr.adapter.form, legs=C.leg_table(legs), extra=C.legs_extra(legs), verdict=C.compact_verdict(v))


def count(recs, pred) -> int:
    return int(sum(1 for r in recs if pred(r)))


def leg_rates(recs: list, spec: str, d: int, legs=("Level 0", "S1c", "S2c", "site", "G1", "G3m", "G6s", "G6l",
                                                      "species")) -> dict:
    """Each leg's rate of one-sided p < .025 in direction d over the computed claims (a leg without a p counts as a
    non-rejection), plus the verdict's survival rate for the spec."""
    n = len(recs)
    out = {}
    for leg in legs:
        k = count(recs, lambda r: C.below(r["legs"].get(leg), d))
        out[leg] = dict(k=k, n=n, rate=C.rate(k, n))
    k = count(recs, lambda r: bool(r["verdicts"][spec]["survives"]))
    out[f"verdict ({spec})"] = dict(k=k, n=n, rate=C.rate(k, n))
    return out


def statuses(recs: list, spec: str) -> dict:
    out: dict = {}
    for r in recs:
        s = r["verdicts"][spec]["primary_status"]
        out[s] = out.get(s, 0) + 1
    return dict(sorted(out.items()))


def gene_list(S) -> list:
    return [int(x) for x in np.asarray(S).tolist()]
