"""WP4: the gated G2 sets (RUN_PLAN.md v3.1 §11 "Gated sets (built under G2 by the frozen §1.6 rules)", R18, R9 / §16
"the < 5 outcomes of gated sets are reported, and the population is restated"; claims_register.md:334-338).

The 41 sets of register_sets/MANIFEST.json with status "built under gate G2" (Giacomel's repository lists, the MDD
lists and the post-mortem DEG sets) are built here, from the gene-level objects the material stage extracted, by the
FROZEN S-build itself: `src_register/s_build.py` (sha256 0bea273f..., its freeze-manifest entry) is loaded from its
verified bytes and its `build_set(hg, uni, raw)` and `load_universes(hg)` are called (the §1.6 HGNC rule; the class
universes of the §3.1 matrices; "< 5 columns in the class universe -> not testable"). Nothing of the rule is copied.

Each set is written as the S-build writes a set (members_hgnc, mapping counts, drop list, per-class universe columns
and outcome) to register_sets/post_freeze/G2/<set_id>.json, plus the signed weights where the cell's functional needs
them (TWAS z / logFC per HGNC member; a duplicate gene's weight is the mean of its rows: RUN_PLAN_amend_2 R42 (a)'s
rule, counted), and listed in register_sets/post_freeze/G2/MANIFEST_G2.json (sha256 of every file, read back).
V-DK-subcortex (the subcortical cells' class) is not an S-build class: its member columns are V-DK's (the same
matrix; the class context's Universe rule drops columns constant over the 7 parcels at use, U14) - an implementation
choice (no frozen text names a V-DK-subcortex universe), listed in the WP4 report.

The population is restated (§16 :1690): a cell whose set has < 5 columns in its class universe reads "not testable
(< 5)" at use; restate() returns the per-cell outcomes and the count of in-m cells that leave the population.
"""
from __future__ import annotations

import hashlib
import json
import types
from pathlib import Path

from . import wp4_layout as L

S_BUILD_REL = "arcs/audit/src_register/s_build.py"
S_BUILD_SHA256 = "0bea273fcb15cecabea8eb2fa8816cce0d2f6b6ac86664c0362201d3b92e5f98"   # register_freeze_manifest.json
SET_SCHEMA = "a1_gated_set_v1"
LT5 = "not testable (< 5)"
VDK_SUB = "V-DK-subcortex"
VDK_SUB_RULE = ("V-DK-subcortex member columns = V-DK's (the same matrix; columns constant over its 7 parcels are "
                "dropped at use by the class context's Universe rule, U14): implementation choice, WP4 phase 1")

# cell -> (source kind, source key, weighted?)   (TSV rows 103-131 set_S; claims_register.md §2.3)
_THR = {"01": 1, "05": 5, "10": 10, 1: 1, 5: 5, 10: 10}


def _gia_cells() -> dict:
    out = {}
    # C01-C06 combined (weighted), C07-C12 up-only, C13-C18 down-only: (thr, compartment) in TSV order
    fam = (("top", True, range(1, 7)), ("top_pos", False, range(7, 13)), ("top_neg", False, range(13, 19)))
    for scheme, weighted, rng in fam:
        for k, c in enumerate(rng):
            thr = (1, 5, 10)[k // 2]
            out[f"GIA-C{c:02d}"] = ("list", f"ASD_{scheme}_genes_thr_{thr}", weighted)
    for k, c in enumerate(range(19, 25)):                     # C19-C24: the ASD post-mortem DEG sets (logFC weights)
        out[f"GIA-C{c}"] = ("deg", f"ASD_{(1, 5, 10)[k // 2]}", True)
    out["GIA-MDD-U1"] = ("list", "MDD_top_pos_genes_thr_1", False)
    out["GIA-MDD-D10"] = ("list", "MDD_top_neg_genes_thr_10", False)
    for t in (1, 5, 10):
        out[f"GIA-MDD-C{t}"] = ("list", f"MDD_top_genes_thr_{t}", True)
    for dset in ("MDDset", "ASDset"):
        for t in ("01", "05", "10"):
            for comp in ("ctx", "sub"):
                out[f"GIA-MDD-DEG-{dset}-{t}-{comp}"] = ("deg", f"{dset[:3]}_{_THR[t]}", True)
    return out


GATED_CELLS = _gia_cells()
MDD_LIST_PATHS = {"MDD_top_pos_genes_thr_1": "results/MDD/MDD_top_pos_genes_thr_1.tsv",
                  "MDD_top_neg_genes_thr_10": "results/MDD/MDD_top_neg_genes_thr_10.tsv",
                  **{f"MDD_top_genes_thr_{t}": f"results/MDD/MDD_top_genes_thr_{t}.tsv" for t in (1, 5, 10)}}


def set_id(cell: str) -> str:
    return f"gated_G2_{cell}"


def frozen_s_build() -> types.ModuleType:
    """The frozen S-build module from its verified bytes (LF sha256 == the freeze-manifest pin); its own imports
    (name_match, privacy_guard, reduce_v68, s_build_v66 beside it) resolve from src_register as frozen."""
    import sys
    p = L.REPO / S_BUILD_REL
    lf = p.read_bytes().replace(b"\r\n", b"\n")
    if hashlib.sha256(lf).hexdigest() != S_BUILD_SHA256:
        raise ImportError("src_register/s_build.py differs from its freeze-manifest pin")
    name = "a1_audit._frozen_s_build"
    if name in sys.modules:
        return sys.modules[name]
    mod = types.ModuleType(name)
    mod.__file__ = str(p)
    sys.modules[name] = mod
    exec(compile(lf.decode("utf-8"), str(p), "exec"), mod.__dict__)
    return mod


def weights_of(raw: list[dict], hg) -> tuple[dict | None, dict]:
    """{HGNC: mean weight of its rows} (None if the rows carry no weight) and the counts."""
    if not raw or raw[0].get("weight") is None:
        return None, {"weighted": False}
    acc: dict = {}
    for r in raw:
        g, _ = hg.resolve(r.get("kind"), r.get("id"), r.get("symbol"))
        if g is None:
            continue
        if r.get("weight") is None:
            raise ValueError("a list row without its weight")
        acc.setdefault(g, []).append(float(r["weight"]))
    dup = sum(1 for v in acc.values() if len(v) > 1)
    return {g: sum(v) / len(v) for g, v in sorted(acc.items())}, {"weighted": True, "n_genes_with_several_rows": dup}


def build_one(cell: str, raw: list[dict], hg, uni: dict, sb, *, source: dict) -> dict:
    """One gated set by the frozen build_set; V-DK-subcortex = V-DK's columns; weights beside the members."""
    body = sb.build_set(hg, uni, raw)
    per = dict(body["universe"])
    per[VDK_SUB] = dict(per["V-DK"], rule=VDK_SUB_RULE)
    # each member column's HGNC gene per class (the weights of R41 are per gene; a gene's columns share its weight)
    col_gene = {c: {col: m for m in body["members_hgnc"] for col in uni[c].get(m, [])} for c in sb.CLASSES}
    col_gene[VDK_SUB] = dict(col_gene["V-DK"])
    w, wc = weights_of(raw, hg)
    kind, key, weighted = GATED_CELLS[cell]
    if weighted and w is None:
        status = L.STATUS_WEIGHT_COLUMN
    else:
        status = "built under gate G2"
    rec = {"schema": SET_SCHEMA, "set_id": set_id(cell), "status": status, "cells": [cell], "gate": L.GATE,
           "definition": f"claims_register.md §2.3 / TSV set_S of {cell}", "source": source,
           "rule": "§1.6 (the frozen S-build's build_set; src_register/s_build.py sha256 %s)" % S_BUILD_SHA256,
           **{k: v for k, v in body.items() if k != "universe"}, "universe": per, "universe_column_gene": col_gene,
           "weights": ({g: w[g] for g in body["members_hgnc"] if g in w} if w else None),
           "weights_used_by": ("the signed-weight descriptor (R41) and the 4.1 check" if weighted else
                               "the |z|-weighted 4.1 check only (T is unweighted)") if w else None,
           "weights_counts": wc}
    return rec


def write_set(path: Path, rec: dict) -> str:
    """Written like the S-build writes a set (UTF-8, indent 1, read back); never overwritten with different bytes."""
    txt = json.dumps(rec, indent=1, ensure_ascii=False) + "\n"
    data = txt.encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != data:
            raise FileExistsError("a gated set file exists with other bytes (never overwritten)")
    else:
        tmp = path.with_name(path.name + ".tmp")
        tmp.write_bytes(data)
        tmp.replace(path)
    back = path.read_bytes()
    if back != data or json.loads(back.decode("utf-8")) != json.loads(txt):
        raise OSError("read-back")
    return hashlib.sha256(back).hexdigest()


def class_of_cell(cell: str, rows_by_cell: dict) -> str:
    return rows_by_cell[cell]["analysis_class"]


def restate(records: dict, rows_by_cell: dict) -> dict:
    """§16 :1690 / RUN_PLAN.md:1478-1479: each cell's outcome in its class universe; the in-m cells whose set reads
    '< 5' leave the population (counted)."""
    out, n_lt5, n_lt5_m = {}, 0, 0
    for cell, rec in records.items():
        cls = class_of_cell(cell, rows_by_cell)
        u = (rec.get("universe") or {}).get(cls) or {}
        n = int(u.get("n_columns", 0))
        lt5 = n < 5
        out[cell] = {"class": cls, "n_columns": n, "outcome": LT5 if lt5 else "testable", "status": rec["status"],
                     "in_m": rows_by_cell[cell]["in_m"]}
        n_lt5 += int(lt5)
        n_lt5_m += int(lt5 and rows_by_cell[cell]["in_m"])
    return {"cells": out, "n_cells": len(out), "n_not_testable_lt5": n_lt5, "n_in_m_not_testable_lt5": n_lt5_m,
            "rule": "claims_register.md:337-338 '< 5 columns in the class universe -> not testable'; RUN_PLAN §16 "
                    ":1690 'the < 5 outcomes of gated sets are reported, and the population is restated'"}


def build_all(roots: L.Roots, raws: dict, hg, uni: dict, sb, rows_by_cell: dict, sources: dict, em=None) -> dict:
    """raws: {cell: raw rows}; sources: {cell: provenance dict}. Writes every set and MANIFEST_G2.json; returns the
    manifest document (with the restatement)."""
    d = roots.set_dir()
    recs, entries = {}, []
    for cell in sorted(raws):
        rec = build_one(cell, raws[cell], hg, uni, sb, source=sources.get(cell, {}))
        name = versioned_name(d, set_id(cell), rec)       # never overwritten: <set_id>.<n>.json beside a differing one
        sha = write_set(d / name, rec)
        recs[cell] = rec
        entries.append({"set_id": set_id(cell), "cell": cell, "json": name, "sha256": sha,
                        "status": rec["status"], "n_hgnc": rec["n_hgnc"]})
        if em is not None:
            em.say(f"wp4_sets: {set_id(cell)} written sha256 {sha}; HGNC genes {rec['n_hgnc']}; drops {rec['n_drops']}")
    man = {"schema": "a1_gated_set_manifest_v1", "gate": L.GATE, "sets": entries,
           "restatement": restate(recs, rows_by_cell), "s_build_sha256": S_BUILD_SHA256}
    # versioned (2026-10-17, resume): a rerun whose set list differs (e.g. the DEG sets added once R17 runs) writes
    # MANIFEST_G2.<n>.json beside the earlier version (never overwritten); an identical version is adopted
    name = set_manifest_name(d, man)
    sha = write_set(d / name, man)
    man["_sha256"] = sha
    man["_name"] = name
    return man


def versioned_name(d: Path, stem: str, rec: dict) -> str:
    """2026-10-21: <stem>.json if absent or byte-identical, else the first <stem>.<n>.json (n >= 2) that is absent or
    byte-identical; an earlier version is never overwritten. The set manifest names the file it holds."""
    data = (json.dumps(rec, indent=1, ensure_ascii=False) + "\n").encode("utf-8")
    for nm in [f"{stem}.json"] + [f"{stem}.{k}.json" for k in range(2, 1000)]:
        p = d / nm
        if not p.exists() or p.read_bytes() == data:
            return nm
    raise FileExistsError("too many versions of a gated set file")


def set_manifest_name(d: Path, man: dict) -> str:
    data = (json.dumps(man, indent=1, ensure_ascii=False) + "\n").encode("utf-8")
    stem = L.SET_MANIFEST_NAME[:-len(".json")]
    names = [L.SET_MANIFEST_NAME] + [f"{stem}.{k}.json" for k in range(2, 1000)]
    for nm in names:
        p = d / nm
        if not p.exists() or p.read_bytes() == data:
            return nm
    raise FileExistsError("too many set manifest versions")
