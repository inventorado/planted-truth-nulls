"""Paper P1 figures 1-5 and the first-page hero (fig0). Reads only committed result files; asserts each input's sha256; no statistic is computed here
(rates, counts and medians are read or taken as order statistics of values already in the files).
Run: env\\venv\\Scripts\\python.exe arcs/audit/paper1/figures/make_figures.py
"""
import hashlib, json, os, re, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, FancyArrowPatch

HERE = os.path.dirname(os.path.abspath(__file__))
AUD = os.path.abspath(os.path.join(HERE, "..", ".."))  # arcs/audit
MM = 1 / 25.4
W1, W2 = 89 * MM, 183 * MM

INPUTS = {
    "e3_gates": ("results/e3_gates.json", "5c4dfb652d18d4d79e7fb3e506756ef276d0268347c84126c38cae324e2fbecf"),
    "e3_a3": ("results/e3_gates_a3.json", "105e81f1674aaf600af8c22cefd3fc547badd74f2dba27e10f6f8315bfc857b0"),
    "e3_a5": ("results/e3_gates_a5.json", "6d5533b3ce27211fb46788061b4b184aea071e5ddfed22888fb2747c87fbece8"),
    "catch": ("results/e3_catch_curves_a5.json", "b9ff7fed11c8b1905f86e1b77506b5dfa26fd393bd8ee6690bc47aa60921a68a"),
    "diag": ("results/e3_a3_leg_diagnostics.json", "f898c90fc97a1d3c319a58510eb10182688257a9e1f533048d56a8d1f4f1fbdf"),
    "regime": ("probes/regime/results/regime_A.json", "d24af7b4f01801d2a7efa65f15ca71476ca958f01401c418e10ee613ab32e9dc"),
    "headline": ("results/a1_run/G2/headline.json", "82f13b45d7554378db00658d69bbc1abb32fa8f2730ad2331cd9f8194d430ab7"),
    "cells": ("results/a1_run/G2/cells.jsonl", "a8f8b4cf42813f3e6d70f0dd99f9d0f954de28c2b9024a8666c56893bfaaa78a"),
}


def load(key):
    rel, exp = INPUTS[key]
    p = os.path.join(AUD, rel)
    h = hashlib.sha256(open(p, "rb").read()).hexdigest()
    assert h == exp, f"sha256 mismatch for {rel}: {h}"
    print(f"input {rel} sha256 {h}")
    if rel.endswith(".jsonl"):
        return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]
    return json.load(open(p, encoding="utf-8"))


# Okabe-Ito colour-blind-safe palette, one meaning per colour across all figures
C = dict(blue="#0072B2", verm="#D55E00", green="#009E73", orange="#E69F00", sky="#56B4E9", pink="#CC79A7",
         yellow="#F0E442", grey="#7f7f7f", black="#000000", lgrey="#d9d9d9")
# roles
COL_STRAT, COL_JOINT = C["blue"], C["verm"]          # class-stratified (calibrated) vs joint (anticonservative)
COL_G2, COL_G4, COL_G5 = C["pink"], C["orange"], C["green"]
COL_N1, COL_N2, COL_N3 = C["grey"], C["sky"], C["pink"]  # uniform / Cao sampler / our G2 (same hue as G2)
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 7, "axes.labelsize": 7, "axes.titlesize": 7.5,
    "xtick.labelsize": 6.5, "ytick.labelsize": 6.5, "legend.fontsize": 6.5, "axes.linewidth": 0.6,
    "xtick.major.width": 0.6, "ytick.major.width": 0.6, "axes.spines.top": False, "axes.spines.right": False,
    "pdf.fonttype": 42, "ps.fonttype": 42, "svg.hashsalt": "p1",
})
ATLAS = {"aal": "AAL", "dk": "Desikan-Killiany", "cc200": "CC200", "dk-ctx": "DK cortex-only"}


def save(fig, name):
    for ext in ("pdf", "png"):
        p = os.path.join(HERE, f"{name}.{ext}")
        kw = dict(dpi=300, bbox_inches="tight", pad_inches=0.03)
        if ext == "pdf":
            kw["metadata"] = {"CreationDate": None, "Producer": None}
        else:
            kw["metadata"] = {"Software": None}
        fig.savefig(p, **kw)
        assert os.path.getsize(p) > 2000, p
    plt.close(fig)


def panel(ax, s, x=-0.02, y=1.04):
    ax.text(x, y, s, transform=ax.transAxes, fontsize=9, fontweight="bold", va="bottom", ha="right")


# ---------------------------------------------------------------- fig 1
def fig1():
    fig, ax = plt.subplots(figsize=(W2, 78 * MM))
    ax.set_xlim(0, 183); ax.set_ylim(0, 78); ax.axis("off")

    def box(x, y, w, h, txt, fc="white", ec=C["black"], fs=6.6, bold=False, ls="-"):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.5", fc=fc, ec=ec, lw=0.7, ls=ls))
        ax.text(x + w / 2, y + h / 2, txt, ha="center", va="center", fontsize=fs, fontweight="bold" if bold else "normal",
                linespacing=1.25)

    def arrow(x0, y0, x1, y1, col=C["black"]):
        ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=7, lw=0.8, color=col))

    rng = np.random.RandomState(1)  # decorative only, no data
    ax.text(3, 75, "The claim", fontsize=7.5, fontweight="bold")
    for i in range(6):
        for j in range(4):
            v = (i + j) / 8.0
            ax.add_patch(Rectangle((4 + i * 5.2, 48 + j * 5.2), 5.0, 5.0, fc=plt.cm.Blues(0.25 + 0.65 * v), ec="white", lw=0.5))
    ax.text(19.5, 45.5, "Brain map y\n(one value per parcel)", ha="center", va="top", fontsize=6.3)
    for i in range(6):
        for j in range(5):
            ax.add_patch(Rectangle((44 + i * 4.6, 47 + j * 4.2), 4.4, 4.0, fc=plt.cm.Oranges(0.2 + 0.7 * rng.rand()), ec="white", lw=0.5))
    ax.text(57.5, 45.5, "Gene set S: expression of\nits genes across the parcels", ha="center", va="top", fontsize=6.3)
    ax.text(38, 33, "T = correlation of the map with the set's mean expression", ha="center", va="top", fontsize=6.0)
    # legs
    ax.text(90, 75, "Two nulls, three checks", fontsize=7.5, fontweight="bold")
    box(88, 57, 48, 14, "Spatial leg\nIs T larger than for smooth\nsurrogate maps (class-stratified)?", fc="#dcebf6", ec=COL_STRAT, fs=5.8)
    box(87, 36, 50, 18, "Gene / species leg\nIs T larger than for gene sets\nas coherent\nand as brain-expressed as S?\n(four nulls; weakest result counts)", fc="#fbe4d5", ec=COL_JOINT, fs=5.8)
    box(88, 20, 48, 13, "Level 0\nIs T nonzero against the\nnaive reference?", fc="#eeeeee", ec=C["grey"], fs=5.8)
    for yy in (64, 45, 26.5):
        arrow(82, 52, 87, yy, C["grey"])
    ax.add_patch(Rectangle((81.5, 51.5), 0.8, 1, fc=C["grey"], ec="none"))
    # fourth-corner max test
    ax.text(143, 75, "Fourth-corner max test", fontsize=7.5, fontweight="bold")
    box(142, 40, 39, 30, "Report an association\nonly if all three checks\npass, each at\nalpha = .025:\nlevel 0 AND spatial leg\nAND weakest gene/\nspecies result", fc="white", ec=C["black"], fs=5.8)
    arrow(137, 64, 141, 58, COL_STRAT); arrow(137, 45, 141, 52, COL_JOINT); arrow(137, 26.5, 141, 46, C["grey"])
    box(142, 20, 39, 13, "Verdict: survives, or\nnot detectable at\nthis power", fc="#f2f2f2", fs=5.8)
    arrow(161.5, 39.5, 161.5, 33.8)
    ax.text(3, 15, "Why two legs: a map can match a gene set through shared spatial smoothness (spatial leg) or through gene\n"
                   "coherence and brain-wide expression (gene/species leg). Each null alone is blind to the other route.",
            fontsize=6.2, va="top", linespacing=1.35)
    ax.text(3, 2, "Schematic; no data. The coloured grids are decorative, not results.", fontsize=5.8, color=C["grey"])
    save(fig, "fig1_schematic")


# ---------------------------------------------------------------- fig 2
def fig2(E):
    g = E["gates"]
    pat = re.compile(r"FA Level1\[(joint|strat)\] (\S+) (F-\S+) step=(\d)")
    L1 = {}
    for kind in ("level1_joint", "level1_strat"):
        for x in g[kind]:
            m = pat.match(x["gate"])
            if not m or x["kind"] != "fa":
                continue
            pair, at, fam, st = m.groups()
            L1.setdefault((pair, at, int(st)), {})[fam] = x["k"] / x["n"]
    assert len(L1) == 12, len(L1)
    assert sum(len(v) for v in L1.values()) == 36
    fig, axs = plt.subplots(1, 2, figsize=(W2, 64 * MM), gridspec_kw=dict(width_ratios=[1.15, 1], wspace=0.28))
    ax = axs[0]
    ats = ["aal", "dk", "cc200"]
    xs = {}
    for i, at in enumerate(ats):
        for st in (0, 1):
            xs[(at, st)] = i * 3 + st
    for pair, col, off, lab in (("joint", COL_JOINT, -0.17, "joint spatial pair (no class stratification)"),
                                ("strat", COL_STRAT, 0.17, "class-stratified pair")):
        for (at, st), x in xs.items():
            v = list(L1[(pair, at, st)].values())
            ax.scatter([x + off] * len(v), v, s=14, color=col, zorder=3, edgecolor="white", linewidth=0.3,
                       label=lab if (at, st) == ("aal", 0) else None)
    ax.axhline(0.05, color=C["black"], lw=0.7, ls="--")
    ax.text(7.55, 0.052, "nominal .05", fontsize=6, ha="right", va="bottom")
    ax.set_xticks(list(xs.values()))
    ax.set_xticklabels([str(s) for _ in ats for s in (0, 1)])
    for i, at in enumerate(ats):
        ax.text(i * 3 + 0.5, -0.115, ATLAS[at], ha="center", va="top", fontsize=6.8, transform=ax.get_xaxis_transform())
    ax.set_xlabel("class step (0 = tissue classes equal in mean, 1 = classes differ)", labelpad=16)
    ax.set_ylabel("false-alarm rate (one point per map family)")
    ax.set_ylim(0, 0.14); ax.set_xlim(-0.6, 7.6)
    ax.legend(frameon=False, loc="upper left", handlelength=0.8, borderaxespad=0.1)
    ax.set_title("Spatial nulls: joint pair fails at step 1", loc="left", fontsize=7)
    panel(ax, "a")

    ax = axs[1]
    G = {}
    for x in g["gene_fa"]:
        m = re.match(r"FA (G2|G4|G5) (\S+) (F-\S+)", x["gate"])
        if m:
            G[(m.group(1), m.group(2))] = (x["k"] / x["n"], x["missing_frac"])
    assert len(G) == 9
    cols = {"G2": COL_G2, "G4": COL_G4, "G5": COL_G5}
    labs = {"G2": "coexpression-matched gene null (G2)",
            "G4": "brain-background coexpression-matched null (G4)",
            "G5": "trajectory + coexpression-matched null (G5)"}
    for j, gn in enumerate(("G2", "G4", "G5")):
        for i, at in enumerate(ats):
            r, mf = G[(gn, at)]
            ax.bar(i + (j - 1) * 0.27, r, width=0.25, color=cols[gn], label=labs[gn] if i == 0 else None)
            ax.text(i + (j - 1) * 0.27, r + 0.008, f"{r:.2f}".lstrip("0"), ha="center", va="bottom", fontsize=5.8)
    ax.axhline(0.05, color=C["black"], lw=0.7, ls="--")
    ax.set_xticks(range(3)); ax.set_xticklabels([ATLAS[a] for a in ats])
    ax.set_ylabel("false-alarm rate, independent smooth fields")
    ax.set_ylim(0, 0.78)
    ax.legend(frameon=False, loc="upper left", fontsize=5.6, handlelength=0.8, borderaxespad=0.0)
    ax.set_title("Gene nulls, coherent modules (trajectory modules for G5)", loc="left", fontsize=6.6)
    panel(ax, "b")
    save(fig, "fig2_e3_false_alarm")
    return {"level1_strata": 36, "gene_cells": 9}


# ---------------------------------------------------------------- fig 3
def fig3(R):
    cells, si = R["cells"], R["set_info"]
    spaces = ["A", "A'", "A''"]
    sname = {"A": "A: Cao's own data and processing", "A'": "A': our V-DK matrix", "A''": "A'': A' on Cao's gene universe"}
    stats = [("C1+", "Mean statistic"), ("C3+", "Map-by-set correlation (T)")]
    types = ["A1r", "A2m", "A2"]
    nulls = [("N1", COL_N1, "uniform random gene sets (G1)"), ("N2", COL_N2, "Cao's rejection sampler"),
             ("N3", COL_N3, "coexpression-matched gene null (G2)")]
    fig, axs = plt.subplots(2, 3, figsize=(W2, 100 * MM), sharey=True, sharex=True,
                            gridspec_kw=dict(wspace=0.07, hspace=0.32))
    used = 0
    for r, (st, stname) in enumerate(stats):
        for c, sp in enumerate(spaces):
            ax = axs[r, c]
            for nn, col, lab in nulls:
                for m, ls, mk, fill in ((25, "-", "o", col), (100, ":", "o", "white")):
                    xs, ys, lo, hi = [], [], [], []
                    for t in types:
                        k = f"{sp}|{t}|m{m}|B2|{nn}|{st}"
                        if k not in cells or cells[k]["n_sets"] == 0:
                            continue
                        co = [d["coexp"] for d in si[f"{sp}|{t}"] if d["m"] == m]
                        assert len(co) == 50, (k, len(co))
                        x = float(np.median(co))
                        a = cells[k]["a0.05"]
                        xs.append(x); ys.append(a["rate"]); lo.append(a["rate"] - a["ci99"][0]); hi.append(a["ci99"][1] - a["rate"])
                        used += 1
                    if xs:
                        ax.errorbar(xs, ys, yerr=[lo, hi], color=col, ls=ls, lw=0.9, marker=mk, ms=3.6, mfc=fill,
                                    mec=col, elinewidth=0.5, capsize=0)
            if sp == "A":
                k = f"A|A1|mall|B1|N2|{st}"
                a = cells[k]["a0.05"]
                x = float(np.median([d["coexp"] for d in si["A|A1"]]))
                ax.errorbar([x], [a["rate"]], yerr=[[a["rate"] - a["ci99"][0]], [a["ci99"][1] - a["rate"]]], fmt="*",
                            color=C["black"], ms=8, mfc=C["yellow"], mec=C["black"], elinewidth=0.6, zorder=5)
                used += 1
            ax.axhline(0.05, color=C["black"], lw=0.6, ls="--")
            ax.set_xscale("symlog", linthresh=0.05, linscale=0.6)
            ax.set_xlim(-0.04, 1.0); ax.set_ylim(0, 0.5)
            ax.set_xticks([0, 0.05, 0.2, 0.5, 1.0]); ax.set_xticklabels(["0", ".05", ".2", ".5", "1"])
            if r == 0:
                ax.set_title(sname[sp], fontsize=6.6)
            if c == 0:
                ax.set_ylabel(f"{stname}\nfalse-alarm rate at nominal .05")
    assert used > 60, used
    fig.supxlabel("set coherence (median mean coexpression of the set type; symmetric log scale)", fontsize=7, y=-0.01)
    from matplotlib.lines import Line2D
    h = [Line2D([], [], color=col, marker="o", ms=3.6, lw=0.9, label=lab) for _, col, lab in nulls]
    h += [Line2D([], [], color=C["black"], marker="o", ms=3.6, mfc="white", ls=":", lw=0.9, label="hollow/dotted: 100 genes (solid: 25)"),
          Line2D([], [], color=C["black"], marker="*", ms=8, mfc=C["yellow"], ls="", label="Cao 2024 calibrated cell")]
    fig.legend(handles=h, loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(0.5, -0.13), fontsize=6.2)
    save(fig, "fig3_regime_coherence")
    return {"plotted_points": used}


# ---------------------------------------------------------------- fig 4
def fig4(A3, CC, DG):
    G = A3["gates"]
    strata = G["species_fa"] + G["verdict_fa_align"] + G["verdict_fa_existing"]
    assert len(strata) == 762
    mx = max(x["k"] / x["n"] for x in strata)
    assert mx <= 0.022 + 1e-9
    mxv = max(x["k"] / x["n"] for x in G["verdict_fa_align"] + G["verdict_fa_existing"])
    assert mxv <= 0.019 + 1e-9
    fig = plt.figure(figsize=(W2, 98 * MM))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.55, 1, 1], wspace=0.45)
    # (a) calibration map, verdict leg of the mirror-null plants: rows = set kind, cols = atlas/target/w
    axa = fig.add_subplot(gs[0])
    V = G["verdict_fa_align"]
    kinds = sorted(set(x["kind_set"] for x in V))
    order = {"rand": 0, "fill": 1, "brand": 2, "clus": 3, "multi": 4}
    kinds.sort(key=lambda s: (order[s.split("-")[0]], int(s.split("-")[1])))
    cols = sorted(set((x["atlas"], x["target"], x["w"]) for x in V), key=lambda t: (list(ATLAS).index(t[0]), t[1], t[2]))
    M = np.full((len(kinds), len(cols)), np.nan)
    for x in V:
        M[kinds.index(x["kind_set"]), cols.index((x["atlas"], x["target"], x["w"]))] = x["k"] / x["n"]
    cm = plt.cm.Blues.copy(); cm.set_bad(C["lgrey"])
    im = axa.imshow(M, aspect="auto", cmap=cm, vmin=0, vmax=0.025, interpolation="nearest")
    axa.set_yticks(range(len(kinds))); axa.set_yticklabels(kinds, fontsize=5.5)
    axa.set_xticks(range(len(cols)))
    axa.set_xticklabels([f"{ {'aal':'AAL','dk':'DK','cc200':'CC200','dk-ctx':'DKctx'}[a]} {t} {w}" for a, t, w in cols], rotation=90, fontsize=4.6)
    axa.set_xlabel("parcellation, planted target, weight w", fontsize=6); axa.set_ylabel("planted gene-set kind (size)")
    cb = fig.colorbar(im, ax=axa, orientation="horizontal", fraction=0.035, pad=0.5)
    cb.set_label("verdict false-alarm rate (nominal .025)", fontsize=6); cb.ax.tick_params(labelsize=5.5)
    axa.spines[:].set_visible(False)
    axa.set_title(f"Calibration: {len(strata)} strata, max {mx:.3f}\n(verdict max {mxv:.3f}); grey = no stratum", loc="left", fontsize=6.8)
    panel(axa, "a", x=0.0)
    # (b)(c): power
    cur = {(x["cls"], x["family"], x["a"]): x for x in CC["curves"]}
    ca = {}
    for x in DG["c_align"]:
        ca.setdefault((x["cls"], x["a"]), []).append(x)
    pal = {"aal": C["blue"], "dk": C["verm"]}
    for idx, (fam, ttl) in enumerate((("C-sp", "Spatial signal (C-sp)"), ("C-gene", "Gene-set signal (C-gene)"))):
        pass
    axb = fig.add_subplot(gs[1]); axc = fig.add_subplot(gs[2])
    for at in ("aal", "dk"):
        for fam, ls, mk in (("C-sp", "-", "o"), ("C-gene", "-", "s")):
            a_ = [0.3, 0.6, 0.9]
            ver = [cur[(at, fam, a)]["rate"] for a in a_]
            site = [cur[(at, fam, a)]["legs"]["site"]["rate"] for a in a_]
            axb.plot(a_, ver, color=pal[at], ls=ls, marker=mk, ms=3.5, lw=1.0,
                     label=f"{ATLAS[at]}, {'spatial' if fam=='C-sp' else 'gene-set'} signal" if True else None)
            axb.plot(a_, site, color=pal[at], ls=":", marker=mk, ms=3.0, mfc="white", lw=0.8)
        a_ = [0.3, 0.5, 0.7]
        lo = [min(x["verdict"] for x in ca[(at, a)]) for a in a_]
        hi = [max(x["verdict"] for x in ca[(at, a)]) for a in a_]
        stl = [max(x["site"] for x in ca[(at, a)]) for a in a_]
        axc.fill_between(a_, lo, hi, color=pal[at], alpha=0.35, lw=0)
        axc.plot(a_, hi, color=pal[at], lw=0.8)
        axc.plot(a_, [np.mean([x["site"] for x in ca[(at, a)]]) for a in a_], color=pal[at], ls=":", marker="o", mfc="white", ms=3, lw=0.8)
        for a in a_:
            assert len(ca[(at, a)]) == 3
    axb.axhline(0.025, color=C["black"], lw=0.5, ls="--")
    axb.set_xlabel("signal strength a"); axb.set_ylabel("catch rate (power)")
    axb.set_ylim(0, 1.02); axb.set_xticks([0.3, 0.6, 0.9])
    axb.set_title("Power, signal planted\nin map or gene set", loc="left", fontsize=6.8)
    from matplotlib.lines import Line2D
    axb.legend(handles=[Line2D([], [], color=C["blue"], marker="o", ms=3.5, label="AAL: spatial signal"),
                        Line2D([], [], color=C["blue"], marker="s", ms=3.5, label="AAL: gene-set signal"),
                        Line2D([], [], color=C["verm"], marker="o", ms=3.5, label="DK: spatial signal"),
                        Line2D([], [], color=C["verm"], marker="s", ms=3.5, label="DK: gene-set signal"),
                        Line2D([], [], color=C["grey"], ls=":", marker="o", mfc="white", ms=3, label="site leg alone"),
                        Line2D([], [], color=C["grey"], ls="-", label="full verdict")],
               frameon=False, fontsize=5.2, loc="upper left", handlelength=1.5, borderaxespad=0.0, labelspacing=0.25)
    axb.set_ylim(0, 1.25); axb.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    axc.set_xlabel("signal strength a"); axc.set_ylabel("catch rate (power)")
    axc.set_ylim(0, 1.02); axc.set_xticks([0.3, 0.5, 0.7])
    axc.set_title("Power, map aligned to\ngene-set (C-align); band = 3 set kinds", loc="left", fontsize=6.8)
    axc.text(0.31, 0.93, "AAL (blue), DK (vermillion)", fontsize=5.4, va="top")
    axc.text(0.31, 0.86, "band/solid = full verdict (range)", fontsize=5.4, va="top")
    axc.text(0.31, 0.79, "dotted = site leg alone (mean)", fontsize=5.4, va="top")
    panel(axb, "b", x=0.0); panel(axc, "c", x=0.0)
    save(fig, "fig4_calibration_power")
    return {"strata": len(strata), "max_rate": mx, "verdict_max": mxv}


# ---------------------------------------------------------------- fig 5
def fig5(H, cells):
    assert H["inputs"]["cells.jsonl"] == INPUTS["cells"][1]
    comp = H["composition"]["composition"]
    units = [u for u in H["units"] if not u.get("out_of_population")]
    assert len(units) == 16 == H["composition"]["population_units"], len(units)
    cat = {}
    for u in units:
        cat.setdefault(u["category"], []).append(u["cell_id"])
    assert {k: len(v) for k, v in cat.items()} == comp, ({k: len(v) for k, v in cat.items()}, comp)
    assert H["composition"]["survivals"] == 0 and H["composition"]["tested_units"] == 1
    la = H["sentences"]["listed_apart"]
    n_g1 = int(re.search(r"G1's (\d+) population", la).group(1))
    n_dear = int(re.search(r"Dear's (\d+) rows", la).group(1))
    n_vr = int(re.search(r"Roy's (\d+) rows", la).group(1))
    assert (n_g1, n_dear, n_vr) == (196, 3, 6)
    rows = [("survives", 0, [], C["green"]),
            ("tested, not detectable\nat this power", 1, cat["tested (full verdict)"], C["blue"]),
            ("no calibrated test", 2, cat["no calibrated test"], C["sky"]),
            ("not testable as stated", 6, cat["not testable as stated"], C["orange"]),
            ("not auditable", 7, cat["not auditable"], C["grey"])]
    for _, n, ids, _c in rows:
        assert len(ids) == n
    fig, axs = plt.subplots(1, 2, figsize=(W2, 62 * MM), gridspec_kw=dict(width_ratios=[1.9, 1], wspace=0.1))
    ax = axs[0]
    for i, (lab, n, ids, col) in enumerate(rows):
        y = len(rows) - 1 - i
        ax.barh(y, n, color=col, height=0.62)
        ax.text(n + 0.15, y, f"{n}  " + (", ".join(ids) if ids else "none"), va="center", fontsize=5.4)
    ax.set_yticks(range(len(rows))); ax.set_yticklabels([r[0] for r in rows][::-1])
    ax.set_xlim(0, 17); ax.set_xlabel("population units (of 16)")
    ax.set_title("Interim headline (ungated + G2 gene null): 0 of 16 survive", loc="left", fontsize=6.8)
    panel(ax, "a", x=-0.38)
    ax = axs[1]
    ax.axis("off"); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.set_title("Listed apart, counted neither way", loc="left", fontsize=6.8, x=0.05)
    items = [(f"{n_g1}", "G1 population units", "gate not run"), (f"{n_dear}", "Dear rows", "deferred pending provenance"),
             (f"{n_vr}", "Vairam / Roy rows", "deferred")]
    for i, (n, a, b) in enumerate(items):
        y = 0.72 - i * 0.27
        ax.add_patch(Rectangle((0.02, y), 0.96, 0.21, fc="white", ec=C["grey"], hatch="////", lw=0.6))
        ax.add_patch(Rectangle((0.2, y + 0.03), 0.76, 0.15, fc="white", ec="none"))
        ax.text(0.11, y + 0.105, n, ha="center", va="center", fontsize=9, fontweight="bold", bbox=dict(fc="white", ec="none", pad=1))
        ax.text(0.22, y + 0.14, a, va="center", fontsize=6.5)
        ax.text(0.22, y + 0.06, "not run / " + b if i == 0 else b, va="center", fontsize=5.8, color=C["grey"])
    panel(ax, "b", x=0.0)
    save(fig, "fig5_audit_demo")
    return {"composition": comp, "listed_apart": [n_g1, n_dear, n_vr]}


# ---------------------------------------------------------------- fig 0: first-page hero (graphical abstract)
def hero(E, A3, CC, H):
    """Three results in one strip. Every value is read from the same files and keys as figs 2, 4 and 5."""
    g = E["gates"]
    joint1 = [x["k"] / x["n"] for x in g["level1_joint"]
              if x["kind"] == "fa" and re.match(r"FA Level1\[joint\] \S+ F-\S+ step=1", x["gate"])]
    strat = [x["k"] / x["n"] for x in g["level1_strat"]
             if x["kind"] == "fa" and re.match(r"FA Level1\[strat\] \S+ F-\S+ step=\d", x["gate"])]
    gn = {k: [x["k"] / x["n"] for x in g["gene_fa"] if re.match(rf"FA {k} \S+ F-\S+", x["gate"])] for k in ("G2", "G4")}
    assert len(joint1) == 9 and len(strat) == 18 and len(gn["G2"]) == len(gn["G4"]) == 3
    G = A3["gates"]
    ver = [x["k"] / x["n"] for x in G["verdict_fa_align"] + G["verdict_fa_existing"]]
    assert len(ver) == 390 and max(ver) <= 0.019 + 1e-9
    cur = {(x["cls"], x["family"], x["a"]): x for x in CC["curves"]}
    comp = H["composition"]
    assert comp["survivals"] == 0 and comp["population_units"] == 16

    fig, axs = plt.subplots(1, 3, figsize=(W2, 52 * MM), gridspec_kw=dict(width_ratios=[1.55, 0.9, 1.15], wspace=0.55))
    # (a) worst-case false alarm
    ax = axs[0]
    rows = [("joint spatial surrogates,\ntissue classes differ", max(joint1), COL_JOINT, 0.05),
            ("class-stratified surrogates", max(strat), COL_STRAT, 0.05),
            ("coexpression-matched\ngene null, coherent sets", max(gn["G2"]), COL_G2, 0.05),
            ("same, brain background", max(gn["G4"]), COL_G4, 0.05),
            ("fourth-corner max test", max(ver), C["green"], 0.025)]
    for i, (lab, v, col, nom) in enumerate(rows):
        y = len(rows) - 1 - i
        ax.barh(y, v, color=col, height=0.62)
        ax.plot([nom, nom], [y - 0.42, y + 0.42], color=C["black"], lw=0.8, ls="--")
        ax.text(v + 0.008, y, f"{v:.3f}".lstrip("0"), va="center", fontsize=6.2)
    ax.set_yticks(range(len(rows))); ax.set_yticklabels([r[0] for r in rows][::-1], fontsize=6)
    ax.set_xlim(0, 0.5); ax.set_xticks([0, 0.05, 0.25, 0.5]); ax.set_xticklabels(["0", ".05", ".25", ".5"])
    ax.set_xlabel("worst false-alarm rate, planted negatives\n(dashes = nominal level)")
    ax.set_title("Standard nulls fail", loc="left", fontsize=7.5, fontweight="bold")
    panel(ax, "a", x=-0.62)
    # (b) the price, strongest gene-specific signal
    ax = axs[1]
    for i, at in enumerate(("aal", "dk")):
        c = cur[(at, "C-gene", 0.9)]
        for j, (v, col, lab) in enumerate(((c["legs"]["site"]["rate"], C["lgrey"], "map-side leg alone"),
                                           (c["rate"], C["green"], "max test"))):
            x = i + (j - 0.5) * 0.36
            ax.bar(x, v, width=0.34, color=col, label=lab if i == 0 else None)
            ax.text(x, v + 0.02, f"{v:.3f}".lstrip("0"), ha="center", va="bottom", fontsize=6)
    ax.set_xticks([0, 1]); ax.set_xticklabels(["AAL", "Desikan-\nKilliany"])
    ax.set_ylim(0, 1.45); ax.set_yticks([0, 0.5, 1.0]); ax.set_ylabel("catch rate, strong gene-set signal")
    ax.legend(frameon=False, loc="upper center", fontsize=5.6, handlelength=0.8, borderaxespad=0.0)
    ax.set_title("Calibration costs power", loc="left", fontsize=7.5, fontweight="bold")
    panel(ax, "b", x=-0.3)
    # (c) interim audit composition
    ax = axs[2]
    order = [("not auditable", C["grey"]), ("not testable as stated", C["orange"]),
             ("no calibrated test", C["sky"]), ("tested (full verdict)", C["blue"])]
    left, handles = 0, []
    for k, col in order:
        n = comp["composition"][k]
        ax.barh(0, n, left=left, color=col, height=0.5, edgecolor="white", lw=0.6)
        ax.text(left + n / 2, 0, str(n), ha="center", va="center", fontsize=7, color="white", fontweight="bold")
        handles.append(Rectangle((0, 0), 1, 1, color=col, label=k.replace(" (full verdict)", ", not detectable")))
        left += n
    assert left == 16
    ax.legend(handles=handles, frameon=False, loc="upper left", bbox_to_anchor=(0, 0.36), ncol=2, fontsize=5.4,
              handlelength=0.9, columnspacing=0.8, borderaxespad=0.0)
    ax.text(0, 0.42, f"{comp['survivals']} of {comp['population_units']} published-claim units survive",
            fontsize=7, fontweight="bold", va="bottom")
    ax.text(0, -0.42, "interim: 2 of 3 release batches;\n196 units not run, 9 rows deferred",
            fontsize=5.4, color=C["grey"], va="top")
    ax.set_xlim(0, 16); ax.set_ylim(-2.6, 1.3); ax.axis("off")
    ax.set_title("Preregistered autism audit", loc="left", fontsize=7.5, fontweight="bold")
    panel(ax, "c", x=-0.04)
    save(fig, "fig0_hero")
    return {"joint1_max": max(joint1), "strat_max": max(strat), "G2_max": max(gn["G2"]), "G4_max": max(gn["G4"]),
            "verdict_max": max(ver)}


def main():
    E, A3, A5, CC, DG, R, H, CL = (load(k) for k in ("e3_gates", "e3_a3", "e3_a5", "catch", "diag", "regime", "headline", "cells"))
    assert A5["gates_json"]["sha256"] == INPUTS["e3_a3"][1]
    fig1()
    r = {"hero": hero(E, A3, CC, H), "fig2": fig2(E), "fig3": fig3(R), "fig4": fig4(A3, CC, DG), "fig5": fig5(H, CL)}
    print(json.dumps(r, sort_keys=True))
    names = ["fig0_hero", "fig1_schematic", "fig2_e3_false_alarm", "fig3_regime_coherence", "fig4_calibration_power", "fig5_audit_demo"]
    for n in names:
        for ext in ("pdf", "png"):
            p = os.path.join(HERE, f"{n}.{ext}")
            assert os.path.exists(p) and os.path.getsize(p) > 2000, p
    print("ok: 12 files")


if __name__ == "__main__":
    main()
