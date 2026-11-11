"""P1 derived numbers. Reads only committed result files; no statistics beyond ratios/rounding/counting.
Rounding rule: Python round() (half-even on the binary value) to the stated decimals:
betas, rho, p-values 3 dp (P+1 strat p 4 dp); Psig 4 dp; relative losses are 1 - verdict_rate/site_rate.
Run: env\\venv\\Scripts\\python.exe -X utf8 arcs/audit/paper1/tables/derive_numbers.py"""
import json, hashlib, subprocess, pathlib

AUD = pathlib.Path(__file__).resolve().parents[2]
REPO = AUD.parents[1]
OUT = pathlib.Path(__file__).resolve().parent
R = AUD / "results"


def rel(p):
    return p.relative_to(REPO).as_posix()


def commit_of(p):
    c = subprocess.run(["git", "log", "-1", "--format=%h", "--", rel(p)], cwd=REPO, capture_output=True, text=True).stdout.strip()
    assert c, f"{p} not committed"
    st = subprocess.run(["git", "status", "--porcelain", "--", rel(p)], cwd=REPO, capture_output=True, text=True).stdout.strip()
    assert not st, f"{p} has uncommitted changes"
    return c


inputs = {}


def load(name, jsonl=False):
    p = R / name
    assert p.is_file(), p
    raw = p.read_bytes()
    inputs[rel(p)] = dict(sha256=hashlib.sha256(raw).hexdigest(), last_commit=commit_of(p))
    print(rel(p), inputs[rel(p)]["sha256"], inputs[rel(p)]["last_commit"])
    txt = raw.decode("utf-8")
    return [json.loads(l) for l in txt.splitlines() if l.strip()] if jsonl else json.loads(txt)


out = {}


def put(key, value, src, rule=None):
    out[key] = dict(value=value, src=src, **({"rounding": rule} if rule else {}))


# --- a. price of calibration vs the site leg alone (ARC.md:291-294) ---
cc = load("e3_catch_curves_a5.json")
assert cc["alpha_v"] == 0.025
by = {}
for c in cc["curves"]:
    s = c["legs"]["site"]["rate"]
    assert s > 0
    by[(c["cls"], c["family"], c["a"])] = dict(n=c["n"], verdict=c["rate"], site=s, loss=1 - c["rate"] / s)
assert len(by) == 12
tbl = {f"{k[0]}|{k[1]}|a={k[2]}": dict(n=v["n"], verdict_rate=round(v["verdict"], 4), site_rate=round(v["site"], 4),
                                        rel_loss_pct=round(100 * v["loss"], 1)) for k, v in by.items()}
put("cost_vs_site.curves", tbl, "results/e3_catch_curves_a5.json:curves[].{rate,legs.site.rate}", "rates 4 dp; loss % 1 dp")
g = [by[(k, "C-gene", .9)]["loss"] for k in ("aal", "dk")]
put("cost_vs_site.C_gene_a09_pct_range", [round(100 * min(g)), round(100 * max(g))],
    "results/e3_catch_curves_a5.json (aal, dk; C-gene, a=.9)", "whole %, min-max over 2 atlas classes")
sp = [by[(k, "C-sp", .9)]["loss"] for k in ("aal", "dk")]
put("cost_vs_site.C_sp_a09_pct_max", round(100 * max(sp)), "results/e3_catch_curves_a5.json (aal, dk; C-sp, a=.9)", "whole %, max")
la = load("e3_a3_leg_diagnostics.json")
assert la["alpha_v"] == 0.025
ca = [r for r in la["c_align"] if r["a"] == 0.7]
assert len(ca) == 6 and all(r["n"] == 500 for r in ca)
al = {f"{r['cls']}|{r['kind']}": dict(site=r["site"], verdict=r["verdict"], rel_loss_pct=round(100 * (1 - r["verdict"] / r["site"]), 1)) for r in ca}
put("cost_vs_site.C_align_a07", al, "results/e3_a3_leg_diagnostics.json:c_align[a=.7].{site,verdict}", "loss % 1 dp")
ls_ = [1 - r["verdict"] / r["site"] for r in ca]
put("cost_vs_site.C_align_a07_pct_range", [round(100 * min(ls_)), round(100 * max(ls_))],
    "results/e3_a3_leg_diagnostics.json:c_align (6 class x kind cells at a=.7)", "whole %, min-max")
put("cost_vs_site.definition",
    "relative loss = 1 - (verdict catch rate)/(class-stratified site-leg-alone catch rate), per class and strength; "
    "C-gene and C-sp at a=.9 from e3_catch_curves_a5, C-align at a=.7 from e3_a3_leg_diagnostics. "
    "Reproduces ARC.md:291-294 (28-31 / 43-83 / <=3).", "arcs/audit/ARC.md:291-294")

# --- b. rounded values ---
p1 = load("e3_p1_myelin.json")
ps = load("e3_p1_strat.json")
assert p1["n_parcels"] == 34
put("P1.rho", round(p1["rho"], 3), "results/e3_p1_myelin.json:rho", "3 dp")
put("P1.p_L1_strat", round(ps["p_L1_strat"], 4), "results/e3_p1_strat.json:p_L1_strat", "4 dp")
rp = load("e3_realplants.json")
assert rp["P2_pass"] is True
for k, v in rp["P2_beta_check"].items():
    put(f"P2.beta_{k}", round(v["ours"], 3), f"results/e3_realplants.json:P2_beta_check.{k}.ours", "3 dp")
c1 = rp["C1_beta"]
put("C1.beta_ours", round(c1["ours"], 3), "results/e3_realplants.json:C1_beta.ours", "3 dp")
put("C1.beta_wei", c1["wei"], "results/e3_realplants.json:C1_beta.wei", "as stored")
put("C1.p_G3", round(rp["C1_cascade"]["p_G3"], 3), "results/e3_realplants.json:C1_cascade.p_G3", "3 dp")
put("C1.p_L1_joint", rp["C1_cascade"]["p_L1_joint"], "results/e3_realplants.json:C1_cascade.p_L1_joint", "full precision")
assert rp["C1_pass"] is False
cao = load("e4_r1_cao.json")
d = cao["g2_descriptor"]["psig"]
put("R1.our_sampler_psig_mean", round(d["mean"], 4), "results/e4_r1_cao.json:g2_descriptor.psig.mean", "4 dp")
put("R1.our_sampler_psig_meanabs", round(d["meanabs"], 4), "results/e4_r1_cao.json:g2_descriptor.psig.meanabs", "4 dp")


# --- Table 4 restricted to claims (cell_class == 'claim' with a verdict); counting only ---
def stratum(level):  # copy of report_cells.py:1619-1625
    if level.startswith("gene null only (uniform"):
        return "gene null only (uniform)"
    if level.startswith("gene null only (structured"):
        return "gene null only (structured)"
    return level.split(":")[0].strip()


g2 = load("a1_run/G2/cells.jsonl", True)
ug = load("a1_run/ungated/cells.jsonl", True)
cells = {}
for src in (ug, g2):
    for c in src:
        cells[c["row"]] = c


def hasv(c):
    v = c.get("verdict")
    return isinstance(v, dict) and "kind" in v and not v.get("descriptor_row")


def tab(pred):
    t = {}
    for c in cells.values():
        if not (hasv(c) and pred(c)):
            continue
        s = t.setdefault(stratum(c["inference_level"]), dict(with_verdict=0, survive=0, not_detectable_ok=0, other_status={}))
        v = c["verdict"]
        s["with_verdict"] += 1
        if v.get("survives"):
            s["survive"] += 1
        elif str(v.get("primary_status")) == "ok":
            s["not_detectable_ok"] += 1
        else:
            k = str(v.get("primary_status"))
            s["other_status"][k] = s["other_status"].get(k, 0) + 1
    return dict(sorted(t.items()))


allv = tab(lambda c: True)
clm = tab(lambda c: c["cell_class"] == "claim")
assert sum(s["with_verdict"] for s in allv.values()) == 42, "all-class verdict rows != 42"
n_clm = sum(s["with_verdict"] for s in clm.values())
assert n_clm == 31, n_clm
put("table4.claims_only", clm, "results/a1_run/G2/cells.jsonl + results/a1_run/ungated/cells.jsonl (cell_class=='claim', verdict.kind present, not descriptor_row)", "counts")
put("table4.all_classes_42", allv, "same, all cell classes (42, as headline.json)", "counts")
put("table4.n_claims_with_verdict", n_clm, "same")


# --- B6: per-paper counts of verdict-bearing claims, their reading and power labels (counting only) ---
def is_claim_v(c):
    return hasv(c) and c["cell_class"] == "claim"


pp = {}
for c in cells.values():
    if not is_claim_v(c):
        continue
    s = pp.setdefault(c["target_key"], dict(n=0, frozen11=c["frozen11_row"] != "added", inference_level=set(), reading={},
                                            power_label={}, power_columns=set(), reading_class=set()))
    s["n"] += 1
    s["inference_level"].add(stratum(c["inference_level"]))
    s["reading"][c["reading"]] = s["reading"].get(c["reading"], 0) + 1
    labs = {l for e in (c.get("r27") or {}).values() for l in (e.get("labels") or [])}
    st = {e.get("status") for e in (c.get("r27") or {}).values() if e.get("status")}
    for l in sorted(labs | st) or ["(no label)"]:
        s["power_label"][l] = s["power_label"].get(l, 0) + 1
    for e in (c.get("r27") or {}).values():
        s["power_columns"].update(e.get("power_columns") or [])
        if e.get("reading_class"):
            s["reading_class"].add(e["reading_class"])
pp = {k: dict(v, inference_level=sorted(v["inference_level"]), power_columns=sorted(v["power_columns"]),
              reading_class=sorted(v["reading_class"])) for k, v in sorted(pp.items())}
assert sum(v["n"] for v in pp.values()) == n_clm == 31
put("table4.by_paper", pp, "results/a1_run/{G2,ungated}/cells.jsonl: claims with a verdict; target_key, frozen11_row, reading, "
    "r27[*].{labels,status,power_columns,reading_class}", "counts")
pw = sum(v["power_label"].get("power not measured in this class", 0) for v in pp.values())
put("table4.n_power_not_measured_in_class", pw, "same; claims whose r27 labels include 'power not measured in this class'", "count")
put("table4.max_paper_share", [max(pp, key=lambda k: pp[k]["n"]), max(v["n"] for v in pp.values()), n_clm], "same", "paper, n, of")

# --- B3: in how many C-align a=.7 cells does the gene-side (species) leg bind (lowest of naive, site, species)? ---
bind = {f"{r['cls']}|{r['kind']}": min(("parametric", r["naive"]), ("map-side", r["site"]), ("gene-side", r["species"]),
                                       key=lambda t: t[1])[0] for r in ca}
put("c_align_a07.binding_leg", bind, "results/e3_a3_leg_diagnostics.json:c_align[a=.7].{naive,site,species}", "lowest single-leg catch")
put("c_align_a07.n_gene_side_binds", [sum(v == "gene-side" for v in bind.values()), len(bind)], "same", "count of 6")

# --- B8: missing / blocked plants in the max-test false-alarm gates; worst case with them excluded ---
ga = load("e3_gates_a3.json")
fa = {}
for grp in ("species_fa", "verdict_fa_align", "verdict_fa_existing"):
    L = ga["gates"][grp]
    for x in L:
        assert x["kind"] == "fa" and x["pass_"] is True and abs(x["rate"] - x["k"] / x["n"]) < 1e-12
    w = max(L, key=lambda x: x["k"] / (x["n"] - x["missing_n"] - x["blocked_n"]))
    fa[grp] = dict(n_strata=len(L), max_rate=max(x["rate"] for x in L), missing=sum(x["missing_n"] for x in L),
                   blocked=sum(x["blocked_n"] for x in L), max_missing_or_blocked=max(x["missing_n"] + x["blocked_n"] for x in L),
                   n_per_stratum=sorted({x["n"] for x in L}),
                   worst_excl=dict(gate=w["gate"], k=w["k"], n=w["n"], excluded=w["missing_n"] + w["blocked_n"],
                                   rate4=round(w["k"] / (w["n"] - w["missing_n"] - w["blocked_n"]), 4),
                                   rate3=round(w["k"] / (w["n"] - w["missing_n"] - w["blocked_n"]), 3)))
assert fa["species_fa"]["n_strata"] == fa["verdict_fa_align"]["n_strata"] == 372 and fa["verdict_fa_existing"]["n_strata"] == 18
put("fa_a3.by_group", fa, "results/e3_gates_a3.json:gates.{species_fa,verdict_fa_align,verdict_fa_existing}[].{k,n,missing_n,blocked_n,rate}",
    "rate = k/n with missing/blocked kept in n (non-rejections, e3_gates_a3.py:151); worst_excl = max k/(n - missing - blocked)")
put("fa_a3.n_verdict_strata", fa["verdict_fa_align"]["n_strata"] + fa["verdict_fa_existing"]["n_strata"], "same", "count")

# --- A4: the preregistered Level-3 null J1 (prereg.md:156-162, :264-265) under the first gate battery ---
eg = load("e3_gates.json")
_pg = AUD / "src" / "e3_gates.py"
src_g = _pg.read_text(encoding="utf-8")
inputs[rel(_pg)] = dict(sha256=hashlib.sha256(_pg.read_bytes()).hexdigest(), last_commit=commit_of(_pg))
assert "\nALPHA = 0.05\n" in src_g
j1 = {"adopted_pair": eg["adopted_level1_pair"], "adopted": eg["j1_adopted"], "state": eg["j1_state"], "alpha": 0.05}
assert j1["adopted_pair"] == "strat" and j1["adopted"] is False
for pair in ("joint", "strat"):
    L = eg["gates"][f"j1_{pair}"]
    f_ = [x for x in L if x["kind"] == "fa"]
    k_ = [x for x in L if x["kind"] == "catch"]
    assert len(f_) == 6 and len(k_) == 2
    j1[pair] = dict(fa_range3=[round(min(x["rate"] for x in f_), 3), round(max(x["rate"] for x in f_), 3)],
                    fa_all_pass=all(x["pass_"] for x in f_),
                    catch={x["gate"]: dict(k=x["k"], n=x["n"], rate3=round(x["rate"], 3), pass_=x["pass_"], status=x["status"]) for x in k_})
j1["verdict_catch_alpha_025"] = {k: round(by[(k, "C-gene", .9)]["verdict"], 3) for k in ("aal", "dk")}
put("J1", j1, "results/e3_gates.json:{adopted_level1_pair,j1_adopted,j1_state,gates.j1_joint,gates.j1_strat}; alpha from src/e3_gates.py:52; "
    "verdict catch from results/e3_catch_curves_a5.json (C-gene a=.9)", "3 dp")

# --- observed map-set correlation of the catch plants (v1.1; POST HOC descriptor, src/e3_observed_r_a5.py) ---
orr = load("e3_observed_r_a5.json")
assert orr["alpha_v"] == 0.025 and len(orr["cells"]) == 12 and len(orr["c_align_cells"]) == 18
for c in orr["cells"]:  # the same cells as Table 2: verdict catch must agree with e3_catch_curves_a5.json
    assert abs(c["rate"] - by[(c["cls"], c["family"], c["a"])]["verdict"]) < 1e-12 and c["n"] == by[(c["cls"], c["family"], c["a"])]["n"]
put("observed_r.by_a", {f"{c['cls']}|{c['family']}|a={c['a']}": dict(median=round(c["r"]["median"], 3), q25=round(c["r"]["q25"], 3),
                                                                      q75=round(c["r"]["q75"], 3), verdict_rate=round(c["rate"], 3))
                        for c in orr["cells"]},
    "results/e3_observed_r_a5.json:cells[].{r.median,r.q25,r.q75,rate}", "3 dp")
for fam in ("C-sp", "C-gene"):
    for a_ in (.3, .6, .9):
        put(f"observed_r.median.{fam}.a={a_}", {k: round(next(c["r"]["median"] for c in orr["cells"]
                                                              if (c["cls"], c["family"], c["a"]) == (k, fam, a_)), 3) for k in ("aal", "dk")},
            f"results/e3_observed_r_a5.json:cells[family={fam}, a={a_}].r.median (aal, dk)", "3 dp")
for a_ in (.3, .5, .7):
    m_ = [c["r"]["median"] for c in orr["c_align_cells"] if c["a"] == a_]
    assert len(m_) == 6
    put(f"observed_r.median_range.C-align.a={a_}", [round(min(m_), 3), round(max(m_), 3)],
        f"results/e3_observed_r_a5.json:c_align_cells[a={a_}].r.median (2 classes x 3 set kinds)", "3 dp, min-max over 6 cells")
bins_ = {}
for src_key in ("catch_by_observed_r", "c_align_catch_by_observed_r"):
    for key, bs in orr[src_key].items():
        assert [b["bin"] for b in bs] == orr["bin_labels"]
        bins_[key] = {b["bin"]: dict(k=b["k"], n=b["n"], rate=(None if b["rate"] is None else round(b["rate"], 3))) for b in bs}
assert set(bins_) == {"aal|C-sp", "aal|C-gene", "dk|C-sp", "dk|C-gene", "aal|C-align", "dk|C-align"}
put("observed_r.catch_by_bin", bins_, "results/e3_observed_r_a5.json:{catch_by_observed_r,c_align_catch_by_observed_r}[class|family][].{k,n,rate}",
    "rate 3 dp; bins of signed observed r, pooled over a")
MERGE = {".3-.4": [".3-.4"], ".4-.5": [".4-.5"], ".5-.6": [".5-.6"], ".6+": [".6-.7", ">= .7"]}
cg = {}
for cls_ in ("aal", "dk"):
    rows_ = {f"a={c['a']}": c["bins"] for c in orr["cells"] if (c["cls"], c["family"]) == (cls_, "C-gene")}
    assert sorted(rows_) == ["a=0.3", "a=0.6", "a=0.9"]
    rows_["pooled"] = orr["catch_by_observed_r"][f"{cls_}|C-gene"]
    cg[cls_] = {}
    for name_, bs in rows_.items():
        d_ = {b["bin"]: b for b in bs}
        cg[cls_][name_] = {}
        for lab_, parts_ in MERGE.items():
            k_, n_ = sum(d_[x]["k"] for x in parts_), sum(d_[x]["n"] for x in parts_)
            cg[cls_][name_][lab_] = dict(k=k_, n=n_, rate=round(k_ / n_, 3))
    for lab_ in MERGE:  # the split rows add up to the pooled row
        assert sum(cg[cls_][f"a={a_}"][lab_]["k"] for a_ in (.3, .6, .9)) == cg[cls_]["pooled"][lab_]["k"]
        assert sum(cg[cls_][f"a={a_}"][lab_]["n"] for a_ in (.3, .6, .9)) == cg[cls_]["pooled"][lab_]["n"]
put("observed_r.C-gene.by_a_bins", cg,
    "results/e3_observed_r_a5.json:cells[family=C-gene].bins and catch_by_observed_r[class|C-gene]; bins .6-.7 and >= .7 summed",
    "k / n; rate 3 dp")
put("observed_r.parametric_floor", {c_: dict(largest_r_not_rejecting=round(v_["largest_r_not_rejecting"], 3),
                                             smallest_r_rejecting=round(v_["smallest_r_rejecting"], 3))
                                    for c_, v_ in orr["parametric_floor"].items()},
    "results/e3_observed_r_a5.json:parametric_floor (from the stored one-sided parametric p of every catch plant)", "3 dp")
put("observed_r.definition",
    "POST HOC descriptor: r = Pearson correlation of the planted map with the set's raw mean-expression score (the statistic a study "
    "reports), from the stored plant records; verdict catch per cell asserted equal to the registered descriptors. A bin pools plants "
    "of different planted strength; every plant in it carries a true signal.",
    "src/e3_observed_r_a5.py docstring")

(OUT / "derived_numbers.json").write_text(json.dumps(dict(inputs=inputs, numbers=out), indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
md = ["# Derived numbers (generated by derive_numbers.py; do not edit)", "", "| key | value | source | rounding |", "|---|---|---|---|"]
for k, v in out.items():
    val = json.dumps(v["value"], ensure_ascii=False)
    val = val if len(val) < 160 else val[:157] + "..."
    md.append(f"| {k} | {val} | {v['src']} | {v.get('rounding', '')} |")
md += ["", "## Inputs", "", "| file | sha256 | last commit |", "|---|---|---|"] + [f"| {f} | {i['sha256']} | {i['last_commit']} |" for f, i in inputs.items()]
(OUT / "derived_numbers.md").write_text("\n".join(md) + "\n", encoding="utf-8")
rb = json.loads((OUT / "derived_numbers.json").read_text(encoding="utf-8"))
assert rb["numbers"].keys() == out.keys()
print("OK", len(out), "keys")
