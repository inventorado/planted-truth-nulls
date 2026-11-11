"""ASDG-AUD-E3 gates re-classed under prereg_amend_5 §5 (FROZEN 2026-09-24, sha256 023bc880…): the mechanical check.

Reads results/e3_gates_a3.json (the amendment-3 evaluation, asserted by its sha256), classes every gate as retained,
descriptor (gates 1-8 of amendment 5 §1) or scope (gates 9-11), evaluates amendment 5 §4.4's two gates on the cortex-only
replica (planted legs (a) and (c), with the call e3_gates_a3.py makes in the other classes, after asserting each plant
file's sha256 against the JSON's inputs_sha256), and writes results/e3_gates_a5.json and .md with K1's status under
amendment 5.
- K1 fires if a retained gate fails outside amendment 3 §5's partial-certification rule, or if the check stops on an input
  assertion (sha256, inventory, the value match of gates 1-11). On any such stop the output is written first with
  "K1 = fired" and the reason; the stop stands until a later frozen amendment. An exception in this code is not a stop.
- Planted leg (a) in the replica failing fires K1; planted leg (c) in the replica failing gives the scope label
  "brain-enrichment (N1) confound untested" on dk-ctx brain-enriched claims (amendment 5 §4.4), not K1.
The self-test (amendment 5 §5, plants p0-p13) runs first on planted copies of the JSON; every plant must match both its
status and its reason string before the real evaluation is written.
Run: env\\venv\\Scripts\\python.exe -X utf8 arcs\\audit\\src\\e3_gates_a5.py
"""
from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import e3_gates_a3 as G  # noqa: E402

ROOT, RES, A3 = G.ROOT, G.RES, G.A3
GATES_JSON = RES / "e3_gates_a3.json"
GATES_SHA = "105e81f1674aaf600af8c22cefd3fc547badd74f2dba27e10f6f8315bfc857b0"  # amendment 5 §0
CAP = G.CAP

# amendment 5 §1: the 11 failures under amendment 3, matched by name and k / n (only on the file with GATES_SHA)
ELEVEN = [
    (1, "VERDICT CATCH aal C-gene a=.9", 197, 296, "descriptor"),
    (2, "VERDICT CATCH dk C-gene a=.9", 175, 299, "descriptor"),
    (3, "POWER aal C-align a=.7 rand-25", 174, 500, "descriptor"),
    (4, "POWER aal C-align a=.7 fill-100", 91, 500, "descriptor"),
    (5, "POWER aal C-align a=.7 brand-100", 53, 500, "descriptor"),
    (6, "POWER dk C-align a=.7 rand-25", 176, 500, "descriptor"),
    (7, "POWER dk C-align a=.7 fill-100", 99, 500, "descriptor"),
    (8, "POWER dk C-align a=.7 brand-100", 106, 500, "descriptor"),
    (9, "ACTIVE aal grad w=.9 (max over kinds)", 28, 1000, "scope"),
    (10, "ACTIVE cc200 grad w=.9 (max over kinds)", 36, 1000, "scope"),
    (11, "PLANT c v2-species cc200 brain w=.9 brand-300", 23, 1000, "scope"),
]
CLASS_OF = {name: cls for _, name, _, _, cls in ELEVEN}
SCOPE_LABELS = {  # amendment 5 §4.1, §4.2
    "ACTIVE aal grad w=.9 (max over kinds)": "species leg untested (gradient): V-AAL claims with R2_grad >= .25",
    "ACTIVE cc200 grad w=.9 (max over kinds)": "species leg untested (gradient): V-CC200 claims with R2_grad >= .25",
    "PLANT c v2-species cc200 brain w=.9 brand-300":
        "brain-enrichment (N1) confound untested: V-CC200 claims with brain-enriched sets",
}
REPLICA_C_LABEL = "brain-enrichment (N1) confound untested: dk-ctx claims with brain-enriched sets (amendment 5 §4.4)"
REPLICA_FILES = {"a": "artifacts/plants_a3/dk-ctx_F-align_mod_0.5.csv.gz",
                 "c": "artifacts/plants_a3/dk-ctx_F-align_brain_0.9.csv.gz"}
REPLICA_NAMES = {"a": "PLANT a naive dk-ctx mod w=.5 rand-25", "c": "PLANT c v2-species dk-ctx brain w=.9 brand-300"}


class InputStop(Exception):
    """An input assertion failed (sha256, inventory, value match): K1 fires and the stop stands (amendment 5 §5)."""


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def expected_names() -> dict[str, list[str]]:
    """The exact gate inventory of e3_gates_a3.json, rebuilt by name from e3_gates_a3's own loops."""
    fa = [f"{c} {t} w={w:g} {kd}" for c, ts in G.TARGETS.items() for t in ts for w in G.WS for kd in G.kinds(t)]
    pa = [f"ACTIVE {c} {t} w=.9 (max over kinds)" for c, ts in G.TARGETS.items() for t in ts if t in G.PA_TARGETS[c]]
    legs = []
    for c in G.CLASSES:
        legs += [f"PLANT a naive {c} wmod w=.5 rand-25",
                 f"PLANT b v1-G6s {c} mod w=.9 rand-100/300" + (" (reported, not required)" if c == "aal" else ""),
                 f"PLANT c v2-species {c} brain w=.9 brand-300"]
    return {"species_fa": [f"SPECIES FA {x}" for x in fa],
            "verdict_fa_align": [f"VERDICT FA {x}" for x in fa],
            "verdict_fa_existing": [f"VERDICT FA {c} {f} step={s:g}" for c in G.CLASSES
                                    for f in ("F-sp", "F-mod", "F-traj") for s in (0.0, 1.0)],
            "verdict_catch": [f"VERDICT CATCH {c} {f} a=.9" for c in G.CATCH_CLASSES for f in ("C-sp", "C-gene")],
            "power": [f"POWER {c} C-align a=.7 {kd}" for c in G.CATCH_CLASSES
                      for kd in ("rand-25", "fill-100", "brand-100")],
            "plant_active": pa, "planted_legs": legs}


INVENTORY = {"species_fa": 372, "verdict_fa_align": 372, "verdict_fa_existing": 18, "verdict_catch": 4, "power": 6,
             "plant_active": 12, "planted_legs": 9}  # amendment 5 §5


def check_inventory(doc: dict) -> None:
    exp = expected_names()
    assert {k: len(v) for k, v in exp.items()} == INVENTORY, "expected-name builder disagrees with amendment 5 §5"
    gates = doc.get("gates", {})
    if set(gates) != set(INVENTORY):
        raise InputStop("inventory")
    for grp, names in exp.items():
        got = [g.get("gate") for g in gates[grp]]
        if len(got) != INVENTORY[grp] or sorted(got) != sorted(names) or len(set(got)) != len(got):
            raise InputStop("inventory")
        if any(g.get("status") == "not run" for g in gates[grp]):
            raise InputStop("inventory")
    fc = doc.get("frozen_carried", {})
    na = fc.get("naive_active", [])
    if sorted(g.get("gate") for g in na) != sorted(f"ACTIVE naive {c} F-sp" for c in G.CLASSES):
        raise InputStop("inventory")
    if any(g.get("status") == "not run" for g in na):
        raise InputStop("inventory")
    rp = fc.get("real_plants", {})
    if "P1_pass" not in rp or "P2_pass" not in rp:
        raise InputStop("inventory")
    if not isinstance(fc.get("G1_plant_active"), str):  # present, not a gate
        raise InputStop("inventory")
    if len(doc.get("descriptors", {}).get("site_rate_T-mod_not_gated", [])) != 3:  # present, not gates
        raise InputStop("inventory")


def check_eleven(doc: dict) -> None:
    by_name = {g["gate"]: g for gs in doc["gates"].values() for g in gs}
    for n, name, k, nn, _ in ELEVEN:
        g = by_name.get(name)
        if g is None or g.get("k") != k or g.get("n") != nn:
            raise InputStop(f"value mismatch, gate {n}")


def replica_gates(doc: dict) -> dict:
    """Amendment 5 §4.4: planted legs (a) and (c) on the cortex-only replica, by e3_gates_a3's own calls, after each
    plant file's sha256 is asserted against the JSON's inputs_sha256."""
    rec = doc.get("inputs_sha256", {})
    out = {}
    for leg, rel in REPLICA_FILES.items():
        f = ROOT / rel
        if rec.get(rel) is None or sha(f.read_bytes()) != rec[rel]:
            raise InputStop("sha256 (plant file)")
    d = G.load_a3("dk-ctx", "F-align", "mod", 0.5)
    out["a"] = G.rate_gate(d[d["kind"] == "rand-25"], "p_naive", REPLICA_NAMES["a"], "mustfail",
                           status_col="verdict_status_a3", meta={"group": "planted_legs", "atlas": "dk-ctx"})
    d = G.load_a3("dk-ctx", "F-align", "brain", 0.9)
    sub = d[d["kind"] == "brand-300"]
    g = G.rate_gate(sub, "p_v2_species", REPLICA_NAMES["c"], "mustfail", status_col="verdict_status_a3",
                    meta={"group": "planted_legs", "atlas": "dk-ctx"})
    k_all = int(((sub["p_v2_species"] < G.ALPHA_V) & (sub["verdict_status_a3"] == "ok")).sum())
    g["all_plants_nonok_as_nonrejection"] = dict(k=k_all, n=int(len(sub)), rate=k_all / len(sub))
    out["c"] = g
    return out


def injected(rate_a: float = 0.06, rate_c: float = 0.06) -> dict:
    """Self-test only: the §4.4 rates injected, not read from the plant files."""
    mk = lambda leg, r: dict(gate=REPLICA_NAMES[leg], kind="mustfail", group="planted_legs", atlas="dk-ctx",  # noqa
                             status="ok", rate=r, k=round(r * 1000), n=1000, pass_=bool(r > CAP))
    return {"a": mk("a", rate_a), "c": mk("c", rate_c)}


def evaluate(doc_bytes: bytes, expected_sha: str, replica, value_match: bool = True) -> dict:
    """Amendment 5 §5. replica: a callable doc -> the §4.4 gates (real run), or a dict of injected gates (self-test).
    Raises InputStop on an input assertion."""
    if sha(doc_bytes) != expected_sha:
        raise InputStop("sha256 (gates JSON)")
    doc = json.loads(doc_bytes.decode("utf-8"))
    check_inventory(doc)
    if value_match:
        check_eleven(doc)
    # the §4.4 plant-file hashes are asserted in every run (p0b); the self-test injects the rates themselves
    rec = doc.get("inputs_sha256", {})
    for rel in REPLICA_FILES.values():
        if rec.get(rel) is None or sha((ROOT / rel).read_bytes()) != rec[rel]:
            raise InputStop("sha256 (plant file)")
    rep = replica(doc) if callable(replica) else replica
    classed = {"retained": [], "descriptor": [], "scope": []}
    for grp, gs in doc["gates"].items():
        for g in gs:
            classed[CLASS_OF.get(g["gate"], "retained")].append({**g, "group": g.get("group", grp)})
    classed["retained"] += [dict(g, group="frozen_naive_active") for g in doc["frozen_carried"]["naive_active"]]
    rp = doc["frozen_carried"]["real_plants"]
    classed["retained"] += [dict(gate="P+1", status="ok", group="real_plants",
                                 pass_=bool(rp["P1_pass"]) and rp.get("P1_by_pair", {}).get("strat") is not False),
                            dict(gate="P+2", status="ok", group="real_plants", pass_=bool(rp["P2_pass"]))]
    labels = [SCOPE_LABELS[g["gate"]] for g in classed["scope"]]
    notes = []
    classed["retained"].append(rep["a"])  # (a) in the replica: a retained gate; failure -> K1
    if rep["c"]["pass_"]:
        classed["retained"].append(rep["c"])  # (c) passing joins the retained gates
    else:
        classed["scope"].append(rep["c"])
        labels.append(REPLICA_C_LABEL)
        notes.append("scope label, replica (c)")
    hard, partial, pnotes = [], set(), []
    for g in classed["retained"]:
        if G.computed(g) and not g["pass_"]:
            if g.get("group") in {"species_fa", "verdict_fa_align"} and g.get("kind_set") in G.LARGE:
                partial.add("claims with m > 300: uncertified (species leg)")
                pnotes.append(f"partial certification, {g['gate']}")
            elif g.get("group") in {"species_fa", "verdict_fa_align"} and g.get("atlas") == "dk-ctx":
                partial.add("single-class claims: uncertified")
                pnotes.append(f"partial certification, {g['gate']}")
            else:
                name = "replica (a)" if g["gate"] == REPLICA_NAMES["a"] else g["gate"]
                hard.append(f"retained gate failed, {name}")
        elif not G.computed(g):
            raise InputStop("inventory")
    if hard:
        k1, reason = "fired", "; ".join(hard)
    else:
        k1 = "not fired (partial certification)" if partial else "not fired"
        reason = "; ".join(pnotes + notes) or "none"
    return dict(K1_status=k1, reason=reason, stop=False, partial_certification=sorted(partial), scope_labels=labels,
                classed=classed, replica=rep)


def run(doc_bytes, expected_sha, replica, value_match=True) -> dict:
    try:
        return evaluate(doc_bytes, expected_sha, replica, value_match)
    except InputStop as e:
        return dict(K1_status="fired", reason=str(e), stop=True)


def selftest(doc0: dict) -> list[str]:
    """Amendment 5 §5 plants p0-p13 on planted copies of the JSON (sha256 pointed at each copy's own hash except p0;
    the value match always against §1; the §4.4 rates injected, .06 unless a plant says otherwise)."""
    def one(mut=None, raw=None, rate_a=0.06, rate_c=0.06):
        d = copy.deepcopy(doc0)
        if mut:
            mut(d)
        b = raw if raw is not None else json.dumps(d).encode("utf-8")
        return run(b, sha(b), injected(rate_a, rate_c))

    def gate(d, name):
        return next(g for gs in d["gates"].values() for g in gs if g["gate"] == name)

    def set_(name, **kw):
        return lambda d: gate(d, name).update(kw)

    sp1 = "SPECIES FA aal wmod w=0.5 rand-25"
    sp_ctx = "SPECIES FA dk-ctx mod w=0.5 rand-25"
    sp_big = "SPECIES FA aal wmod w=0.5 multi-1000"
    cases = []
    base = json.dumps(doc0).encode("utf-8")
    b0 = base.replace(b"SPECIES FA", b"SPECIEs FA", 1)  # one byte changed, expected hash kept
    r = run(b0, sha(base), injected())
    cases.append(("p0", (r["K1_status"], r["reason"]), ("fired", "sha256 (gates JSON)")))
    r = one(lambda d: d["inputs_sha256"].update({REPLICA_FILES["c"]: "0" * 64}))
    cases.append(("p0b", (r["K1_status"], r["reason"]), ("fired", "sha256 (plant file)")))
    r = one(set_(sp1, k=60, rate=0.06, pass_=False))
    cases.append(("p1", (r["K1_status"], r["reason"]), ("fired", f"retained gate failed, {sp1}")))
    r = one(set_(sp_ctx, k=60, rate=0.06, pass_=False))
    cases.append(("p1b dk-ctx", (r["K1_status"], r["reason"], r.get("partial_certification")),
                  ("not fired (partial certification)", f"partial certification, {sp_ctx}",
                   ["single-class claims: uncertified"])))
    r = one(set_(sp_big, k=60, rate=0.06, pass_=False))
    cases.append(("p1b m>300", (r["K1_status"], r["reason"], r.get("partial_certification")),
                  ("not fired (partial certification)", f"partial certification, {sp_big}",
                   ["claims with m > 300: uncertified (species leg)"])))
    nm = "ACTIVE dk grad w=.9 (max over kinds)"
    r = one(set_(nm, k=40, rate=0.04, pass_=False))
    cases.append(("p2", (r["K1_status"], r["reason"]), ("fired", f"retained gate failed, {nm}")))
    nm = "PLANT c v2-species aal brain w=.9 brand-300"
    r = one(set_(nm, k=40, rate=0.04, pass_=False))
    cases.append(("p3", (r["K1_status"], r["reason"]), ("fired", f"retained gate failed, {nm}")))
    r = one(set_("VERDICT CATCH aal C-gene a=.9", k=198))
    cases.append(("p4", (r["K1_status"], r["reason"], r["stop"]), ("fired", "value mismatch, gate 1", True)))
    r = one()
    cases.append(("p5", (r["K1_status"], r["reason"]), ("not fired", "none")))
    r = one(lambda d: d["gates"]["species_fa"].pop(0))
    cases.append(("p6", (r["K1_status"], r["reason"], r["stop"]), ("fired", "inventory", True)))
    r = one(lambda d: d["frozen_carried"]["real_plants"].update(P2_pass=False))
    cases.append(("p7", (r["K1_status"], r["reason"]), ("fired", "retained gate failed, P+2")))
    nm = "VERDICT CATCH aal C-sp a=.9"
    r = one(set_(nm, k=237, rate=0.79, pass_=False))
    cases.append(("p8", (r["K1_status"], r["reason"]), ("fired", f"retained gate failed, {nm}")))
    nm = "ACTIVE dk-ctx grad w=.9 (max over kinds)"
    r = one(set_(nm, k=40, rate=0.04, pass_=False))
    cases.append(("p9", (r["K1_status"], r["reason"]), ("fired", f"retained gate failed, {nm}")))
    r = one(set_("ACTIVE aal grad w=.9 (max over kinds)", k=60, rate=0.06, pass_=True))
    cases.append(("p10", (r["K1_status"], r["reason"], r["stop"]), ("fired", "value mismatch, gate 9", True)))
    for rc in (0.04, 0.05):
        r = one(rate_c=rc)
        cases.append((f"p11 c={rc}", (r["K1_status"], r["reason"], REPLICA_C_LABEL in r["scope_labels"]),
                      ("not fired", "scope label, replica (c)", True)))
    r = one(rate_c=0.06)
    cases.append(("p11 c=.06", (r["K1_status"], r["reason"], REPLICA_C_LABEL in r["scope_labels"],
                                any(g["gate"] == REPLICA_NAMES["c"] for g in r["classed"]["retained"])),
                  ("not fired", "none", False, True)))
    for ra in (0.04, 0.05):
        r = one(rate_a=ra)
        cases.append((f"p11b a={ra}", (r["K1_status"], r["reason"]), ("fired", "retained gate failed, replica (a)")))
    r = one(rate_a=0.06)
    cases.append(("p11b a=.06", (r["K1_status"], r["reason"]), ("not fired", "none")))
    r = one(lambda d: d["gates"]["species_fa"].append(dict(d["gates"]["species_fa"][0], gate="SPECIES FA extra")))
    cases.append(("p12", (r["K1_status"], r["reason"], r["stop"]), ("fired", "inventory", True)))
    r = one(set_(sp1, status="not run"))
    cases.append(("p13", (r["K1_status"], r["reason"], r["stop"]), ("fired", "inventory", True)))
    r = one(set_(sp1, status="fail: no computed plants", pass_=False))  # an evaluated failure, not a stop
    cases.append(("p13 fail-status", (r["K1_status"], r["reason"], r["stop"]),
                  ("fired", f"retained gate failed, {sp1}", False)))
    return [f"{a}: got {b}, expected {c}" for a, b, c in cases if b != c]


def main():
    raw = GATES_JSON.read_bytes()
    doc0 = json.loads(raw.decode("utf-8"))
    failed = selftest(doc0)
    if failed:
        raise SystemExit("SELFTEST FAILED:\n  " + "\n  ".join(failed))
    r = run(raw, GATES_SHA, replica_gates)
    out = dict(amendment="prereg_amend_5 (FROZEN 2026-09-24, sha256 023bc880...)", K1_status=r["K1_status"],
               reason=r["reason"], stop=r["stop"], selftest="pass (plants p0-p13)",
               gates_json=dict(path="arcs/audit/results/e3_gates_a3.json", sha256=GATES_SHA),
               script_sha256=sha(Path(__file__).read_bytes()), commit=G.git("rev-parse", "HEAD"),
               dirty=bool(G.git("status", "--porcelain")))
    if not r["stop"]:
        cl = r["classed"]
        out.update(partial_certification=r["partial_certification"], scope_labels=r["scope_labels"],
                   counts={k: len(v) for k, v in cl.items()},
                   failed_as_gates_under_amendment_3=[
                       dict(n=n, gate=name, k=k, n_=nn, rate=k / nn, class_under_amendment_5=cls)
                       for n, name, k, nn, cls in ELEVEN],
                   replica_section_4_4=r["replica"],
                   retained_failures=[g["gate"] for g in cl["retained"] if G.computed(g) and not g["pass_"]],
                   replica_inputs_sha256={rel: sha((ROOT / rel).read_bytes()) for rel in REPLICA_FILES.values()})
    RES.mkdir(parents=True, exist_ok=True)
    (RES / "e3_gates_a5.json").write_text(json.dumps(out, indent=1, default=float), encoding="utf-8")
    L = [f"# E3 gates under prereg_amend_5 — GENERATED by e3_gates_a5.py @ {out['commit'][:7]}; do not hand-edit", "",
         f"**K1 (amendment 5): {out['K1_status']}**; reason: {out['reason']}; self-test: {out['selftest']}", ""]
    if not r["stop"]:
        L += ["## Gates 1–11: failed as gates under amendment 3 (amendment 5 §1)", "",
              "| # | gate | k / n | rate | class under amendment 5 |", "|---|---|---|---|---|"]
        L += [f"| {n} | {name} | {k} / {nn} | {k / nn:.3f} | {cls} |" for n, name, k, nn, cls in ELEVEN]
        L += ["", "## Amendment 5 §4.4: planted legs on the cortex-only replica", "",
              "| gate | k / n | rate | step 0 | step 1 | pass | status | class |", "|---|---|---|---|---|---|---|---|"]
        for leg, g in r["replica"].items():
            bs = g.get("by_step", {})
            cls = "retained" if (leg == "a" or g["pass_"]) else "scope label"
            L.append(f"| {g['gate']} | {g['k']} / {g['n']} | {g['rate']:.3f} | {bs.get('0', {}).get('rate', float('nan')):.3f}"
                     f" | {bs.get('1', {}).get('rate', float('nan')):.3f} | {'PASS' if g['pass_'] else 'FAIL'} | "
                     f"{g['status']} | {cls} |")
        c_all = r["replica"]["c"].get("all_plants_nonok_as_nonrejection")
        if c_all:
            L.append(f"\nReplica (c), all plants with non-ok statuses as non-rejections (reported beside): "
                     f"{c_all['k']} / {c_all['n']} = {c_all['rate']:.3f}")
        L += ["", "## Scope labels in force", ""] + [f"- {x}" for x in out["scope_labels"]]
        L += ["", f"Counts: {out['counts']}; retained failures: {out['retained_failures'] or 'none'}; "
              f"partial certification: {out['partial_certification'] or 'none'}"]
    (RES / "e3_gates_a5.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"K1 (amendment 5): {out['K1_status']}; reason: {out['reason']}")
    if r["stop"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
