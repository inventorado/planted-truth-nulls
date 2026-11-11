"""Pre-freeze work (claims register v4 sections 1.8 and 1.10 (0)): the carrier tests of the four conditional targets
(Rasero, Buch, Mamat, Romero-Garcia), with every required label list taken from a PUBLIC ATLAS, never from a carrier:

- Rasero (target 6): abagen's Desikan-Killiany atlas info (bundled `atlas-desikankilliany.csv`): 34 left cortical
  labels, and 34 + 7 left subcortical (variant fixed from notebook 08 / the journal Methods before the test runs);
- Buch (target 7): Power et al. 2011 264 ROI ids and MNI coordinates (nilearn's bundled `power_2011.csv`);
- Mamat (target 8): Schaefer 2018 400-parcel 17-network label names (the CBIG release file fetched by nilearn's
  `fetch_atlas_schaefer_2018(n_rois=400, yeo_networks=17, resolution_mm=1)`, register 1.7);
- Romero-Garcia (target 4): DK-308 label names from `lh.500.aparc.annot` / `rh.500.aparc.annot` of the paper's
  subParcellation repository @e351b3cf (public atlas files, not target carriers), cross-checked with the repository's
  `308_regions_names.txt`.

Writes arcs/audit/register_maps/carrier_tests.json (the spec that arcs/audit/src_register/carrier_test.py applies).
Prints counts and hashes only. Run: env\\venv\\Scripts\\python.exe -X utf8 arcs\\audit\\src_register\\carrier_labels.py

Register DRAFT v5 section 1.11 item 8 fixed three readings before the freeze (Romero-Garcia: the 152 LEFT DK-308 labels,
a left-only carrier qualifies; Buch: >= 230 usable ROIs = coordinates + a numeric value, no ROI id needed; Mamat: 400
parcels by name OR by index 1 ... 400). They were first hand-applied to carrier_tests.json (its "amendments" record) and
are now encoded here (V5_*; apply_v5), so a regeneration keeps them. The spec is frozen with the register (its sha256 is
pinned on every conditional TSV row and in carrier_tests_selftest.json), so this script never overwrites it silently:
  (no flag)     writes the spec only if it does not exist; otherwise refuses (exit 3) and writes nothing;
  --check       rebuilds the spec in memory and compares it with the file on disk, run stamps ('built_utc', 'script')
                and the 'amendments' record aside; prints EQUAL (exit 0) or the differing key paths (exit 4); writes nothing;
  --overwrite   rewrites the spec (v5 readings included; the 'amendments' record carried forward plus one entry for this
                regeneration); afterwards carrier_test.py selftest and the TSV build must be re-run (the builder refuses a
                self-test record of another spec).

Register DRAFT v6 R9 (orchestrator under the operator's standing delegation, 2026-09-26; apply_v6): Mamat's index-only
tables qualify only if the carrier itself names the 17-network order file (Schaefer2018_400Parcels_17Networks_order);
else not auditable (carrier test failed).

Register DRAFT v6.1 Q1 / Q8, v6.2 P1 / P2 / P6 / P7 (b) and v6.3 O1-O4 / O6 (orchestrator under the operator's standing
delegation): the
source-1 criterion (source1_lists: positive -- input wording in the list's sheet name, table title or caption; map / subgroup
/ cohort headings refused; checks on the list's own title and the caption only) with per-cell entries keyed by cell id
(source1_cells: names and printed sizes; the Buch Fig. 5h labels read from register_maps/buch_fig5h_grid.json); the pinned
PDF adapter (pdf_adapter).
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import abagen
import nibabel as nib
import nilearn
import pandas as pd
from nilearn import datasets

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "arcs" / "audit" / "register_maps" / "carrier_tests.json"
IDENT = ROOT / "arcs" / "audit" / "register_maps" / "IDENTITY_prefreeze.json"
ATL = Path("E:/data/asdg/atlases")
SUBP = Path("E:/data/asdg/romerogarcia2019synaptic/repos/subParcellation/500mm parcellation (308 regions)")


def sha256_file(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def dk_labels():
    a = abagen.fetch_desikan_killiany()
    info = pd.read_csv(a["info"])
    left_ctx = info[(info["hemisphere"] == "L") & (info["structure"] == "cortex")]
    left_sub = info[(info["hemisphere"] == "L") & (info["structure"] == "subcortex/brainstem")]
    assert len(left_ctx) == 34 and len(left_sub) == 7, (len(left_ctx), len(left_sub))
    src = {"source": "abagen %s fetch_desikan_killiany() info CSV (bundled)" % abagen.__version__,
           "path_basename": Path(a["info"]).name, "sha256": sha256_file(a["info"])}
    ctx = [{"key": "L:" + l, "hemisphere": "L", "name": l, "structure": "cortex", "abagen_id": int(i)}
           for i, l in zip(left_ctx["id"], left_ctx["label"])]
    sub = [{"key": "L:" + l, "hemisphere": "L", "name": l, "structure": "subcortex", "abagen_id": int(i)}
           for i, l in zip(left_sub["id"], left_sub["label"])]
    return src, ctx, sub


def power_labels():
    p = datasets.fetch_coords_power_2011()
    rois = p.rois
    assert rois.shape == (264, 4) and list(rois["roi"]) == list(range(1, 265))
    f = Path(datasets.__file__).parent / "data" / "power_2011.csv"
    src = {"source": "Power et al. 2011 (Neuron 72:665) 264 ROI MNI coordinates, nilearn %s fetch_coords_power_2011() "
                     "(bundled power_2011.csv)" % nilearn.__version__, "sha256": sha256_file(f) if f.exists() else None}
    return src, [{"key": "P:%d" % int(r.roi), "roi": int(r.roi), "mni_xyz": [float(r.x), float(r.y), float(r.z)]}
                 for r in rois.itertuples()]


def schaefer_labels(write_source: bool = True):
    d = ATL / "nilearn"
    d.mkdir(parents=True, exist_ok=True)
    b = datasets.fetch_atlas_schaefer_2018(n_rois=400, yeo_networks=17, resolution_mm=1, data_dir=str(d), verbose=0)
    labs = [l.decode() if isinstance(l, bytes) else str(l) for l in b["labels"]]
    labs = [l for l in labs if l.startswith("17Networks_")]
    assert len(labs) == 400 and len(set(labs)) == 400, len(labs)
    sdir = Path(b["maps"]).parent
    txt = sdir / "Schaefer2018_400Parcels_17Networks_order.txt"
    src = {"source": "Schaefer 2018 400 parcels 17 networks, CBIG release tag v0.14.3-Update_Yeo2011_Schaefer2018_labelname, via "
                     "nilearn %s fetch_atlas_schaefer_2018(n_rois=400, yeo_networks=17, resolution_mm=1)" % nilearn.__version__,
           "url_base": ("https://raw.githubusercontent.com/ThomasYeoLab/CBIG/v0.14.3-Update_Yeo2011_Schaefer2018_labelname/"
                        "stable_projects/brain_parcellation/Schaefer2018_LocalGlobal/Parcellations/MNI/"),
           "labels_file": str(txt), "labels_file_sha256": sha256_file(txt) if txt.exists() else None,
           "maps_file": str(b["maps"]), "maps_file_sha256": sha256_file(b["maps"])}
    srcmd = sdir / "SOURCE.md"
    if write_source and not srcmd.exists():
        lines = ["# SOURCE: Schaefer 2018 400 parcels, 17 networks (CBIG release)", "",
                 "- **date fetched**: %s" % dt.date.today().isoformat(),
                 "- **url(s)**: %s{%s, %s}" % (src["url_base"], txt.name, Path(b["maps"]).name),
                 "- **fetched by**: nilearn %s datasets.fetch_atlas_schaefer_2018(n_rois=400, yeo_networks=17, resolution_mm=1), "
                 "via arcs/audit/src_register/carrier_labels.py (claims register v4 1.7 / 1.8; public atlas, ungated)" % nilearn.__version__,
                 "- **licence**: MIT (CBIG repository)", "",
                 "| file | bytes | sha256 |", "|---|---|---|"]
        for f in (txt, Path(b["maps"])):
            lines.append("| %s | %d | %s |" % (f.name, f.stat().st_size, sha256_file(f)))
        srcmd.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return src, [{"key": "S:" + l[len("17Networks_"):].lower(), "name": l, "index": i + 1} for i, l in enumerate(labs)]


def dk308_labels():
    out, src = [], {"source": "RafaelRomeroGarcia/subParcellation @e351b3cf03fac04713eb915b5754e6144998f757, folder '500mm "
                              "parcellation (308 regions)' (public atlas; local copy under E:\\data\\asdg\\romerogarcia2019synaptic\\repos)"}
    for hemi, fn in (("L", "lh.500.aparc.annot"), ("R", "rh.500.aparc.annot")):
        p = SUBP / fn
        labels, ctab, names = nib.freesurfer.read_annot(str(p))
        names = [n.decode() if isinstance(n, bytes) else n for n in names]
        used = set(int(v) for v in set(labels.tolist()))
        # the annot names its non-cortical labels 'unknown_part1' and 'corpuscallosum_part1'; they are excluded by parent
        keep = [n for k, n in enumerate(names)
                if n.rsplit("_part", 1)[0] not in ("unknown", "corpuscallosum") and k in used]
        src[fn] = {"sha256": sha256_file(p), "n_names_in_ctab": len(names), "n_kept": len(keep),
                   "excluded": sorted(set(names) - set(keep))}
        out += [{"key": "%s:%s" % (hemi, n.lower()), "hemisphere": hemi, "name": n,
                 "dk_parent": n.rsplit("_part", 1)[0] if "_part" in n else n} for n in keep]
    names_txt = SUBP / "308_regions_names.txt"
    txt_names = [l.strip() for l in names_txt.read_text(encoding="utf-8").splitlines() if l.strip()]
    txt_keys = set()
    for n in txt_names:
        h = "L" if n.lower().startswith("lh") else ("R" if n.lower().startswith("rh") else "?")
        txt_keys.add("%s:%s" % (h, n.split("_", 1)[1].lower() if "_" in n else n.lower()))
    src["308_regions_names.txt"] = {"sha256": sha256_file(names_txt), "n": len(txt_names),
                                    "equals_annot_names": txt_keys == {d["key"] for d in out}}
    return src, out


def ident_refs(target):
    j = json.loads(IDENT.read_text(encoding="utf-8"))
    refs = []
    for r in j["records"]:
        if r["target"] != target:
            continue
        for p in r["probes"]:
            refs.append({"object": r["object"], "url": p.get("url") or p.get("file_url") or p.get("path"),
                         "size": p.get("content_length", p.get("size")),
                         "etag_or_blob": p.get("etag") or p.get("blob_sha") or p.get("checksum"), "status": p.get("status"),
                         "listed_utc": p.get("listed_utc")})
    return refs


RULES = {
    "normalisation_dk": ("lower-case; strip; hemisphere read from a leading token (ctx-lh-, ctx_lh_, lh_, lh-, lh., lh , left-, "
                         "left_, l_, l-) or a trailing token (_lh, -lh, _l, _left, ' (l)', ' left') or, if absent, from a separate "
                         "column of the same table whose cells are all hemisphere tokens (l, r, lh, rh, left, right); the token "
                         "removed; then every non-alphanumeric character removed; aliases: thalamus -> thalamusproper, accumbens -> "
                         "accumbensarea (FreeSurfer 7 names). A name with no hemisphere matches nothing (reported as "
                         "n_unlateralised)."),
    "normalisation_dk308": ("as normalisation_dk (hemisphere token required); the remainder is compared with the annot name "
                            "lower-cased (e.g. 'ctx-lh-bankssts_part1', 'lh_bankssts_part1', 'lh.bankssts_part1' -> "
                            "L:bankssts_part1); non-alphanumerics other than '_' removed on both sides."),
    "normalisation_schaefer": ("lower-case; strip; a leading '17networks_' (or '17networks-') removed; '-', ' ' and '.' turned "
                               "into '_'; compared with the CBIG name after the same steps (e.g. '17Networks_LH_VisCent_ExStr_1' "
                               "-> lh_viscent_exstr_1). Integer parcel indices without names do not qualify (reported as "
                               "n_index_only_tables)."),
    "power_matching": ("a carrier row is a Power ROI iff it carries an integer id and three numeric MNI coordinates; it is "
                       "'Power-matched' iff its coordinates lie within 2.0 mm (Euclidean) of the Power 2011 ROI of the same id, "
                       "else of any Power 2011 ROI (then matched by coordinates); a row with numeric coordinates that matches "
                       "no Power ROI is 'extra' (Buch's 277-ROI set exceeds Power's 264) and is usable, because the sphere rule "
                       "of register 1.7 uses the carrier's own coordinates. Coordinates: three columns headed x / y / z (optional "
                       "'mni', '(mm)'), or one column holding 'x, y, z' / '(x y z)' triples."),
    "numeric_parse": ("a value parses iff it is an int / float cell, or a string that after stripping and replacing U+2212 by "
                      "'-' matches ^[+-]?(\\d+(\\.\\d*)?|\\.\\d+)([eE][+-]?\\d+)?$; the number must be finite. Empty cells, "
                      "'NA', 'n.s.', '-', '*'-suffixed or bracketed values do not parse. EVERY required label's value must parse."),
    "tables": ("every table of the carrier is searched: xlsx / xls sheets (openpyxl, values only), csv / tsv, docx w:tbl tables "
               "(XML, no macros), ipynb output tables (text/html <table>), PDF tables (pdfplumber page.extract_tables(), "
               "installed under the gate; untested here). A table's label column is the column whose cells match the most "
               "required labels; a hemisphere column is paired with it when its names carry no hemisphere."),
    "map_identification": ("a value column belongs to map M iff its header text (every non-numeric cell above the first "
                           "label-matched row, joined) matches M's tier-1 pattern (map token AND object token); if no column "
                           "of the carrier does, tier 2 (map token alone); if still none, a table whose sheet / table name "
                           "matches M's map token and that holds exactly one numeric-for-all-matched-rows column. Exactly one "
                           "column per map across the carrier at the tier used, else 'ambiguous' (fail) or 'no map column' "
                           "(fail). Patterns are case-insensitive regular expressions."),
    "duplicates": "a required label present twice in the chosen label column with different values -> fail (duplicate labels)",
    "output": "pass / fail per map with a reason code and counts only; no label, header, value or file content is printed",
    "partial": "partial or figure-only content does not qualify (register 1.8): a missing required label is a fail",
}


# register DRAFT v5 section 1.11 item 8: the readings fixed before the freeze (verbatim as first hand-applied to the spec)
V5_RULES = {
    "normalisation_schaefer": (
        "lower-case; strip; a leading '17networks_' (or '17networks-') removed; '-', ' ' and '.' turned into '_'; compared "
        "with the CBIG name after the same steps (e.g. '17Networks_LH_VisCent_ExStr_1' -> lh_viscent_exstr_1). Where the "
        "target's 'index_labels' reading applies (Mamat), a table without names also qualifies through a column of integer "
        "parcel indices: index i = the i-th parcel of the Schaefer 2018 400-parcel 17-network order file (labels_detail "
        "'index'); names are tried first and win a tie; an index table is subject to every other rule (all 400 indices "
        "present once, every value numeric) (register v5 section 1.11 item 8)."),
    "power_matching": (
        "a carrier row is a USABLE ROI for map M iff it has three numeric MNI coordinates -- in the row itself, or joined "
        "through its integer ROI id to coordinates given elsewhere in the carrier -- and a numeric value in M's column; an ROI "
        "id is NOT required (the sphere rule of register 1.7 uses the carrier's own coordinates, not an id list; register v5 "
        "section 1.11 item 8). Rows are keyed by their id where one is given, else by their coordinates; a key present twice "
        "with different values -> fail (duplicate labels). Power 2011 matching is a diagnostic only: an ROI is "
        "'Power-matched' iff its coordinates lie within 2.0 mm (Euclidean) of the Power 2011 ROI of the same id, else of any "
        "Power 2011 ROI (then matched by coordinates); a row with numeric coordinates that matches no Power ROI is 'extra' "
        "(Buch's 277-ROI set exceeds Power's 264) and is usable. Coordinates: three columns headed x / y / z (optional "
        "'mni', '(mm)'), or one column holding 'x, y, z' / '(x y z)' triples."),
}
V5_BUCH = {
    "label_space": ("ROIs with MNI coordinates (the carrier's own ROI set; Power 2011's 264 ROIs are the matching reference, a "
                    "diagnostic only: Buch reports 277 ROIs)"),
    "required_comparison": ">= (usable ROIs per map: three numeric coordinates and a numeric value; an ROI id is not required)",
    "pass_rule": ("all four maps pass: >= 230 usable ROIs each, an ROI being usable iff it has numeric coordinates and a numeric "
                  "value on that map (register v5 section 1.11 item 8; the sphere rule of 1.7 uses coordinates, not an id list)"),
}
V5_MAMAT = {
    "pass_rule": ("per map: the 400 Schaefer-400 / 17-network parcels present once, by name or by index 1 ... 400 (declared "
                  "reading, index_labels), every value numeric; C1 / C2 need the ABIDE I map, C3 the ABIDE II map, every "
                  "enrichment claim both (register 2.8); the carrier set (files 1-4) is searched as one"),
    "index_labels": {"allowed": True, "range": [1, 400],
                     "reading": ("declared (register v5 section 1.11 item 8): parcels may be given by name OR by index 1 ... 400 "
                                 "in the order the paper names; it qualifies because Mamat names the Schaefer-400, 17-network "
                                 "parcellation (register 2.8), whose order file (labels_source) fixes index i -> "
                                 "labels_detail[i - 1]")},
}
V5_RG_PASS = ("per map, each searched separately (discovery, Validation 1, Validation 2): the 152 LEFT DK-308 labels present "
              "once, every value numeric; right-hemisphere labels are neither required nor checked, so a left-only carrier "
              "qualifies (register v5 section 1.11 item 8)")
V5_RG_SPACE = "DK-308 left hemisphere: the 152 lh labels (the route uses only the left hemisphere, register 1.7)"
# register DRAFT v6 R9 (orchestrator under the operator's standing delegation, 2026-09-26): Mamat's index-only tables qualify
# only if the carrier itself names the 17-network order file; else the map fails (not auditable, carrier test failed)
V6_RULES = {
    "normalisation_schaefer": (
        "lower-case; strip; a leading '17networks_' (or '17networks-') removed; '-', ' ' and '.' turned into '_'; compared "
        "with the CBIG name after the same steps (e.g. '17Networks_LH_VisCent_ExStr_1' -> lh_viscent_exstr_1). Where the "
        "target's 'index_labels' reading applies (Mamat), a table without names also qualifies through a column of integer "
        "parcel indices -- index i = the i-th parcel of the Schaefer 2018 400-parcel 17-network order file (labels_detail "
        "'index') -- ONLY IF the carrier itself names that order file (index_labels.requires_order_file_named: its 17-network "
        "pattern found in the carrier's text -- any table cell, sheet or table name, or document / page text -- and no other "
        "Schaefer order file named); else index-only tables do not qualify (register v6 R9). Names are tried first and win a "
        "tie; an index table is subject to every other rule (all 400 indices present once, every value numeric)."),
}
V6_MAMAT_INDEX = {
    "allowed": True, "range": [1, 400],
    "requires_order_file_named": {
        "pattern_17": r"schaefer[\s_-]*2018[\s_-]*400[\s_-]*parcels?[\s_-]*17[\s_-]*networks?[\s_-]*order",
        "pattern_any_order_file": r"schaefer[\s_-]*2018[\s_-]*\d+[\s_-]*parcels?[\s_-]*\d+[\s_-]*networks?[\s_-]*order",
        "rule": ("the carrier (all its files, searched as one) names the 17-network order file (pattern_17, case-insensitive) and "
                 "names no other Schaefer order file (a match of pattern_any_order_file that is not a match of pattern_17, e.g. "
                 "'Schaefer2018_400Parcels_7Networks_order'); else index-only tables do not qualify")},
    "reading": ("register v6 R9 (revising v5 section 1.11 item 8's declared reading): parcels may be given by index 1 ... 400 "
                "only if the carrier itself names the 17-network order file (Schaefer2018_400Parcels_17Networks_order), which "
                "fixes index i -> labels_detail[i - 1]; a carrier that names no order file, or another one (e.g. the "
                "7-network order), gives index-only tables that do not qualify -> not auditable (carrier test failed)"),
}
V6_MAMAT_PASS = ("per map: the 400 Schaefer-400 / 17-network parcels present once, by name, or by index 1 ... 400 only if the "
                 "carrier names the 17-network order file (index_labels, register v6 R9), every value numeric; C1 / C2 need the "
                 "ABIDE I map, C3 the ABIDE II map, every enrichment claim both (register 2.8); the carrier set (files 1-4) is "
                 "searched as one")
# register DRAFT v6.2 (orchestrator under the operator's standing delegation, 2026-09-26; decisions P1, P2, P6, P7 (b)): the one
# source-1 criterion (v6.1 Q1) made positive (P1), keyed by cell id (P2), its checks confined to the list's own title and the
# table's caption (P6); ["dysregulated", "validation"] dropped (P7 (b))
_BUCH_C_E = [  # (panel, token, name alternatives): Fig. 5c-e row labels as the draft transcribes them (register_work/buch...md)
    ("c", "ASDdown", [["asd", "downregulated"], ["asdm12"]]), ("c", "ASDup", [["asd", "upregulated"], ["asdm16"]]),
    ("c", "FMRP", [["fmrp"]]), ("c", "SFARIsyn", [["syndromic", "sfari"]]), ("c", "SPARK", [["spark"]]),
    ("c", "RDNV", [["rdnv"], ["rare", "de novo"]]), ("c", "Grove", [["grove"]]),
    ("d", "CNSauto", [["cns", "autoimmune"]]), ("d", "Osteo", [["osteoarthritis"]]),
    ("d", "MSA", [["multiple system atrophy"], ["msa"]]), ("d", "Dementia", [["dementia"]]),
    ("d", "HeartDisease", [["heart disease"]]), ("d", "Psoriasis", [["psoriasis"]]),
    ("e", "Vocal", [["vocal learning"]]), ("e", "ADHD", [["adhd"]]), ("e", "TS", [["tourette"]]),
    ("e", "SZ", [["schizophrenia"]]), ("e", "MDD", [["mdd"], ["major depressive"]]),
    ("e", "GAD", [["gad"], ["generalized anxiety"]]), ("e", "ID", [["intellectual disability"]]), ("e", "Aphasia", [["aphasia"]]),
    ("e", "ConductDisorder", [["conduct disorder"]]), ("e", "AntisocialPD", [["antisocial"]]),
    ("e", "NeuroticDisorder", [["neurotic"]]),
]
_BUCH_F_G = [  # Fig. 5f / 5g labels as printed (the draft's transcription; the builder's SYN / IMM lists, asserted equal by it)
    ("f", "SecVesicle", "Secretory vesicle"), ("f", "PresynActiveZone", "Presynaptic active zone"),
    ("f", "PostsynMembrane", "Postsynaptic membrane"), ("f", "IonChannelComplex", "Ion channel complex"),
    ("f", "ChemSynTransmission", "Chemical synaptic transmission"), ("f", "MembranePotential", "Regulation of membrane potential"),
    ("f", "NTSecretion", "Neurotransmitter secretion"), ("f", "GPCR", "GPCR signaling pathway"),
    ("f", "SynapseOrg", "Synapse organization"), ("f", "cAMP", "cAMP-mediated signaling"),
    ("f", "GluRSignaling", "Glutamate receptor signaling pathway"),
    ("g", "CytokineReceptorBinding", "Cytokine receptor binding"), ("g", "CytokineActivity", "Cytokine activity"),
    ("g", "CytokineBinding", "Cytokine binding"), ("g", "CytokineReceptorActivity", "Cytokine receptor activity"),
    ("g", "ProteaseBinding", "Protease binding"), ("g", "LeukocyteChemotaxis", "Leukocyte chemotaxis"),
    ("g", "ResponseToxicSubstance", "Response to toxic substance"), ("g", "CytokineProduction", "Cytokine production"),
    ("g", "TCRSignaling", "T cell receptor signaling pathway"), ("g", "ResponseToCytokine", "Response to cytokine"),
    ("g", "ImmuneActivatingST", "Immune response-activating signal transduction"), ("g", "ImmuneResponse", "Immune response"),
]
_BUCH_H = ["StructConstRibosome", "RibosomalSubunit", "Ribosome", "CytosolicRibosome", "CytoplasmicTranslation"]  # Fig. 5h, top down
_PAGANI = [  # the set names the paper prints (Fig. 5a-c, Results); Supplementary Table 3 itself is sealed (G1)
    ("PAG-C1", [["asd de genes"], ["asd", "differentially expressed"]]),
    ("PAG-C2", [["asd de genes"], ["asd", "differentially expressed"]]),
    ("PAG-C3", [["transmission across chemical synapses"]]), ("PAG-C4", [["syngo"]]),
    ("PAG-C5", [["protein-protein interaction at synapses"]]), ("PAG-C6", [["membrane trafficking"]]),
    ("PAG-C7", [["cytokine signaling in immune system"]]), ("PAG-C8", [["innate immune system"]]),
    ("PAG-C9", [["vesicle transport and release"]]), ("PAG-C10", [["synaptic vesicles and plasticity"]]),
    ("PAG-C11", [["immune response"]]), ("PAG-C12", [["reactive microglia"]]),
]
_ZHANG = {"RG-04": "neuron", "RG-V08": "neuron", "RG-V09": "neuron", "RG-N04": "astrocyte", "RG-N05": "oligodendrocyte",
          "RG-N06": "microglia", "RG-N07": "vascular"}
_RG_KEGG = {"RG-03": "Table S2", "RG-V06": "Supplementary Table S3", "RG-V07": "Supplementary Table S4"}
_RG_CARRIER = "Romero-Garcia's mixed supplements (gate G1)"


def source1_cells() -> dict:
    """register v6.2 P2: per cell id, the target, the name alternatives (each a list of phrases that must all appear), where they come
    from, and the printed size (None where the paper prints none)."""
    grid = json.loads((ROOT / "arcs" / "audit" / "register_maps" / "buch_fig5h_grid.json").read_text(encoding="utf-8"))
    h_rows = grid["rows_top_to_bottom_as_printed"]
    assert len(h_rows) == len(_BUCH_H) and h_rows[0].startswith("*")
    cells = {}
    buch = [(p, t, alts, "Fig. 5%s row label as the draft transcribes it (register_work/buch2023asdsubgroups.md)" % p)
            for p, t, alts in _BUCH_C_E]
    buch += [(p, ("Syn-" if p == "f" else "Imm-") + t, [[lab]],
              "Fig. 5%s label as printed (the draft's transcription; the builder's list, asserted equal)" % p)
             for p, t, lab in _BUCH_F_G]
    buch += [("h", "Trans-" + t, [[lab.lstrip("*").strip()]], "Fig. 5h row as printed (register_maps/buch_fig5h_grid.json, re-read "
              "before the freeze; a leading asterisk is a mark, not the name)") for t, lab in zip(_BUCH_H, h_rows)]
    pins = comparator_pins()  # v6.6 B1 / B2: every external comparator pinned by set id, file sha256 and members sha256
    nm_pins = near_miss_pins()  # v6.7: the registered secondary view
    for p, tok, alts, src in buch:
        for k in (1, 2, 3, 4):
            cid = "BUCH-E-%s-S%d" % (tok, k)
            if cid in pins:
                cor = dict(pins[cid])
            elif tok == "Trans-StructConstRibosome":
                cor = {"mode": "none", "why": ("no external definition ('*Ribosomal structure' reaches no PANTHER 16.0 GO-slim "
                                               "term by the name rule) and no printed size: not auditable (S undefined: source 1 "
                                               "uncorroborated)")}
            else:
                raise SystemExit("%s: no comparator outcome in register_sets/MANIFEST.json (run s_build.py)" % cid)
            cells[cid] = {"target": "buch2023asdsubgroups", "names": alts, "names_source": src, "printed_size": None,
                          "carrier": "MOESM3.xlsx (Supplementary Tables 4-5)", "corroboration": cor}
            if cid in nm_pins:  # v6.7: the near-miss view's own comparator (never the primary)
                cells[cid]["corroboration_views"] = {"near_miss": nm_pins[cid]}
    for cid, alts in _PAGANI:
        cells[cid] = {"target": "pagani2026crossspecies", "names": alts,
                      "names_source": ("the set name the paper prints (Fig. 5a-c, Results); Supplementary Table 3's own labels are "
                                       "sealed (G1) and were not seen"),
                      "printed_size": None, "carrier": "Supplementary Table 3 (MOESM4_ESM.xlsx)",
                      "corroboration": dict(pins[cid])}
        if cid in nm_pins:  # v6.7 N6: PAG-C9 / C10's near-miss comparators (never the primary)
            cells[cid]["corroboration_views"] = {"near_miss": nm_pins[cid]}
    for cid, cls in _ZHANG.items():  # v6.3 N3: 'enriched' is part of the name (e.g. 'Neuron enriched'); N2: the Zhang family
        cells[cid] = {"target": "romerogarcia2019synaptic",
                      "names": [[cls, "specific"], [cls, "top 500"], [cls, "zhang"], [cls, "enriched"]],
                      "names_source": "Romero-Garcia's Methods: the top 500 %s-specific genes of Zhang 2014 (R2 row)" % cls,
                      "printed_size": 500, "carrier": _RG_CARRIER, "family": "zhang2014_top500",
                      "corroboration": {"mode": "printed_size", "printed_size": 500, "class": "dk-ctx",
                                        "count": "distinct approved HGNC symbols (v6.6 C1)",
                                        "printed_size_source": RG_PRINTED_500}}
    cells["RG-N03"] = {"target": "romerogarcia2019synaptic", "names": [["common variant"], ["magma"], ["pgc"]],
                       "names_source": "Romero-Garcia's Methods: common-variant genes, PGC ASD MAGMA (R2 row)", "printed_size": None,
                       "carrier": _RG_CARRIER,
                       "corroboration": {"mode": "none", "why": "no external definition (no published gene list) and no printed size"}}
    for cid in ("RG-15", "RG-V23"):
        cells[cid] = {"target": "romerogarcia2019synaptic", "names": [["second", "dysregulated"]],
                      "names_source": ("the Methods' 'second list of genes dysregulated in autism' (v6.2 P7 (b): the alternative "
                                       "['dysregulated', 'validation'] is dropped -- it could match the Parikshak 2016 list)"),
                      "printed_size": None, "carrier": _RG_CARRIER,
                      "own_title_only": True,  # v6.4 N2: both phrases in the list's own title (no caption naming)
                      "corroboration": {"mode": "none", "why": ("no external definition (the list is identified only in the "
                                                                "supplement) and no printed size")}}
    for cid, tab in _RG_KEGG.items():
        cells[cid] = {"target": "romerogarcia2019synaptic", "names": None,
                      "names_from_carrier": ("each KEGG pathway name as %s prints it, one alternative per pathway (the printed name as "
                                             "one phrase), passed with --name under G1, one run per pathway; the table's other "
                                             "printed pathway names passed with --rival as rival-only names (v6.4 N4)" % tab),
                      "names_source": "the gated table naming the family's cells (%s)" % tab, "printed_size": None,
                      "carrier": _RG_CARRIER,
                      "corroboration": {"mode": "kegg_family_recipe", "class": "dk-ctx", "recipe": KEGG_RECIPE}}
    return dict(sorted(cells.items()))


RG_PRINTED_500 = {  # v6.6 C1: the one '500' Romero-Garcia prints for the Zhang cells, verbatim, with its location
    "sentence": ("We defined cell-type specific genes as the top 500 genes with higher expression in the cell-type compared to "
                 "the remaining five genes."),
    "section": "Materials and methods, 'Genetic modules and enrichment analyses'",
    "page": "Mol Psychiatry 24:1053-1064 (2019), p. 1056 (PDF page 4 of 12); the only '500' in the article's text",
    "pdf": {"url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC6755982/pdf/41380_2018_Article_23.pdf",
            "path": "E:\\data\\asdg\\register_sets_src\\romerogarcia2019_article\\41380_2018_Article_23.pdf",
            "sha256": "130a9b6ca2171563292f27dd79462ceb103c8ce56315f71efa6171d915696621"},
    "note": "the PDF sets 'defined', 'specific' and 'five' with fi-ligatures; quoted here with plain letters"}
KEGG_RECIPE = {  # v6.6 B1: the RG KEGG families' comparator, built by the engine itself from the pinned libraries
    "recipe": "enrichr_kegg_family_v6_6",
    "libraries": {"KEGG_2015": {"key": "enrichr_kegg_2015",
                                "sha256": "ac721aed19bbc618c766cf1a76cc3dfa99c1df13055073ebc3d3e112fbf69369"},
                  "KEGG_2016": {"key": "enrichr_kegg_2016",
                                "sha256": "a501968146264e4a7ba2b2fb06ff8b9c0cb9a209655f31c095ece502e04d61f5"}},
    "rule": ("the library chosen by register 1.6's KEGG family rule (s_build.kegg_family_choice) over the run's --name and --rival "
             "names (the gated table's printed pathway names); the pathway the --name reaches in it by the name rule (a printed "
             "'Homo sapiens hsaNNNNN' suffix split off); its genes mapped to HGNC by the S-build's rule; a library whose sha256 "
             "differs, a name reaching no pathway, or any read / parse error -> not corroborated (the else branch, reason recorded); "
             "no file is accepted from outside (v6.6 B1: --external withdrawn)")}


def comparator_pins() -> dict:
    """register v6.6 (B1 / B2): cell -> its pinned corroboration entry -- Buch's GO-slim fallback sets (v6.5) and the v6.6
    comparators (built: mode external with the set id, the per-set JSON's sha256 and the members' sha256; not buildable: mode
    none with the reason), from register_sets/MANIFEST.json (the S-build's output)."""
    man = json.loads((ROOT / "arcs" / "audit" / "register_sets" / "MANIFEST.json").read_text(encoding="utf-8"))
    out = {}

    def ext(sid, js, cls="V-AAL"):
        body = json.loads((ROOT / "arcs" / "audit" / "register_sets" / js).read_text(encoding="utf-8"))
        assert body["set_id"] == sid
        return {"mode": "external", "set_id": sid, "class": cls,
                "json_sha256": hashlib.sha256((ROOT / "arcs" / "audit" / "register_sets" / js).read_bytes()).hexdigest(),
                "members_sha256": hashlib.sha256("\n".join(body["members_hgnc"]).encode("utf-8")).hexdigest()}
    for e in man["sets"]:
        if e["set_id"].startswith("buch_goslim_fallback_"):
            for c in e["cells"]:
                out[c] = ext(e["set_id"], e["json"])
    for e in man["comparators_v6_6"]["sets"]:
        for c in e["cells"]:
            assert c not in out, c
            out[c] = (ext(e["set_id"], e["json"]) if e["outcome"] == "built" else
                      {"mode": "none", "why": "comparator not buildable pre-freeze (register 1.6, v6.6): " + e["why"]})
    return out


def near_miss_pins() -> dict:
    """register v6.7 (1): cell -> the near-miss view's pinned comparator (a secondary view, labelled 'comparator from a near-miss
    source (not the cited reference) / normalised name / name bridge / note reading' (v6.9 C3: '/ name bridge' added; v6.10:
    '/ note reading'); built: mode external
    with the set id and both sha256; not buildable:
    mode none), from register_sets/MANIFEST.json comparators_v6_6.near_miss_view_v6_7."""
    man = json.loads((ROOT / "arcs" / "audit" / "register_sets" / "MANIFEST.json").read_text(encoding="utf-8"))
    out = {}
    for e in man["comparators_v6_6"]["near_miss_view_v6_7"]["sets"]:
        for c in e["cells"]:
            if e["outcome"] == "built":
                body = json.loads((ROOT / "arcs" / "audit" / "register_sets" / e["json"]).read_text(encoding="utf-8"))
                out[c] = {"mode": "external", "set_id": e["set_id"], "class": "V-AAL",
                          "json_sha256": hashlib.sha256((ROOT / "arcs" / "audit" / "register_sets" / e["json"]).read_bytes())
                          .hexdigest(),
                          "members_sha256": hashlib.sha256("\n".join(body["members_hgnc"]).encode("utf-8")).hexdigest(),
                          "label": e["label"]}
            else:
                out[c] = {"mode": "none", "why": "near-miss comparator not buildable either (register 1.6, v6.7): " + e["why"],
                          "label": e["label"]}
    return out


def buch_fallback_sets() -> dict:
    """register v6.5 (1): Buch's GO-slim cells -> their pinned fallback set (register_sets/MANIFEST.json, the S-build's output)."""
    man = json.loads((ROOT / "arcs" / "audit" / "register_sets" / "MANIFEST.json").read_text(encoding="utf-8"))
    return {c: e["set_id"] for e in man["sets"] if e["set_id"].startswith("buch_goslim_fallback_") for c in e["cells"]}


_LB, _RB = r"(?<![a-z])", r"(?![a-z])"  # register v6.3 O1 (b): letter boundaries (after '_' and '.' are read as spaces)
V65_SOURCE1 = {
    "what": ("the source-1 criterion (register 1.6; v6.1 Q1 made positive by v6.2 P1, keyed by cell id by P2, its checks confined by "
             "P6; v6.3 O1-O4 and O6; v6.4 N1-N4): a carrier list qualifies only if the carrier presents it as the set's membership "
             "used as input to the enrichment -- its own sheet name, table title, caption or its own (forward-filled) title carries "
             "input wording -- and no cell of its sheet (docx / pdf: its table and caption), other than the lists' own genes, "
             "carries statistics, result or map wording; where the paper prints a set size, the list length must equal it; "
             "otherwise the else branch applies"),
    "applies_to": ["Buch MOESM3 (every Buch enrichment and descriptor cell)", "the R2 rows (RG-04, RG-V08, RG-V09, RG-N03 ... N07, "
                   "BUCH-E-Trans-StructConstRibosome-S1 ... S4)", "the Romero-Garcia families RG-03, RG-15, RG-V06, RG-V07, RG-V23",
                   "Pagani Supplementary Table 3 (PAG-C1 ... C12)"],
    "rule": ("(0) text: every heading is read after the name rule's normalisation (case, UK / US spelling, singular / plural) with "
             "'_' and '.' read as spaces (v6.3 O1 (b)); markers match at letter boundaries, so 'PLS1', 'core_enrichment', "
             "'GSEA_results', 'SG1', 'top_genes', 'hit_gene', 'urg_list' are read. (1) candidates: (A) a column of gene symbols "
             "(symbol_pattern) below its title, or (B) a delimited list of >= 2 gene symbols in a row whose first cell names the set. "
             "A column's first data row is its first cell that is a gene symbol or a delimited symbol list and is followed (next "
             "filled cell below) by another such cell or by nothing (v6.3: a symbol-shaped header such as 'NES' over numbers is a "
             "title); a cell equal to a registered set name is a title, not data ('SYNGO'). A table's caption = its sheet name (xlsx) "
             "or file name (csv / txt), the paragraph just before it (docx) or the text line just above it (pdf), and its title rows "
             "(rows above its first data row with exactly one filled cell, in a table of >= 2 filled columns); a column's own title "
             "= its cells above ITS first data row (header rows forward-filled across merged cells; title rows excluded); for (B) the "
             "row's first cell is also part of the list's own title; the table's column titles = every column's cells in the header "
             "rows above the table's first data row. (2) naming: a heading names the set iff every phrase of one of the cell's name "
             "alternatives (cells) appears in it as whole words; (A) is named by its own title, by its own title and the caption "
             "together (at least one phrase in its own title; v6.3, for a table with one column per set under a caption naming the "
             "family, e.g. 'Top 500 cell-type-specific genes (Zhang 2014)' over 'Neuron' ...), or by the caption alone where the "
             "table has <= 2 titled columns; a heading naming another registered set of the target, or one of the target's rival "
             "names (rival_names: v6.3 O6), whose name contains the cell's names the more specific one ('Cytosolic ribosome' and "
             "'Structural constituent of ribosome' are not 'Ribosome'). (3) refusals, after every phrase of the cell's own "
             "alternatives is removed wherever it appears (v6.3 O3) and 'top N' with N = the cell's printed size is exempt: result "
             "wording (result_markers) in the list's own title or the caption -> 'result list (result wording)'; statistics wording "
             "(statistics_headers, per heading part) in the list's own title, the caption or ANY column title of its table (v6.3 O1 "
             "(a)) -> 'result list (statistics wording)'; a name of one of the paper's maps, subgroups or cohorts (map_names: general "
             "and the cell's target) in its own title or the caption -> 'result list (the heading names a map, subgroup or cohort)'; "
             "no input wording (input_markers) in the caption or the list's own forward-filled title (v6.3 O2) -> 'not presented as "
             "input'; a column with non-symbol cells -> 'not a list of gene symbols'. (4) size: the cell's printed_size, else a size "
             "in the list's own heading ('n = N', '(N genes)', 'top N'), must equal the list's length. Exactly one qualifying list "
             "(identical duplicates merge) -> source 1; none, two or more distinct, or a size mismatch -> the else branch. (5) a "
             "family cell whose names come from the gated table (RG-03, RG-V06, RG-V07): one run per pathway with exactly one --name "
             "(the printed name as one phrase; a printed '[ _]Homo sapiens[ _]hsaNNNNN' suffix split off; several names for one run "
             "are refused, so no alternative accumulates across pathways; v6.3 O4); the table's other printed pathway names are "
             "passed as rival-only names (--rival; never alternatives; v6.4 N4). v6.4 (N1-N3) on top of (0)-(5): (6) SHEET-LEVEL "
             "REFUSAL (N1 (1)): if any cell of the list's sheet (xlsx; the whole csv / txt; for docx / pdf the whole table), other "
             "than the cells of the lists' own gene runs, or its caption carries statistics, result or map wording after the same "
             "reading (the phrases of the cell's own family removed, 'top N' = its printed size exempt), every list on that sheet "
             "is refused -> 'result list (statistics, result or map wording on the sheet)'; a cell that reads as ONE token counts "
             "only when the whole token equals a registered header (whole_tokens: fullmatch), a cell of several words by the phrase "
             "wording (statistics_headers, result_markers, map_names); the table-level and header-zone checks stay as a second "
             "layer. (7) a single-token cell is never data (never a gene of a list) if it is NA / NS / ND / NAN / N/A (na_like) or "
             "if, as read, the WHOLE token equals a registered statistics header, result marker or map name (whole_tokens; N1 (2) "
             "as refined in v6.4: not by substring or prefix, so P2RY12, P4HB, S100P, TOP1 or a pseudogene '...P1' are data) -- so "
             "'NES' over 'NA', 'FDR' over 'NS', 'P' over 'NS', 'PLS1', 'CORE' or 'SG1' as titles stay titles; the cost, counted "
             "(non_data_cost): the approved HGNC symbols equal to a registered token, which fall into a list's title when they are "
             "its first gene(s), so that list is refused as a whole. "
             "(8) naming (N2): own title and caption together name a set only for a family with caption_phrases (the Zhang cells: "
             "the phrases the caption supplies must be 'zhang' or 'top 500'); a cell with own_title_only (RG-15, RG-V23) is named "
             "only by its own title. (9) 'weighted gene co-expression' is not the 'weight' marker (N3). v6.5: (10) CORROBORATION "
             "(the orchestrator's decision after five review rounds, v6.0 -> v6.4, showed that the text criterion alone could not "
             "exclude result lists; the text criterion stays as a first filter): the one list the text criterion admits is source 1 "
             "only if corroborated -- (a) mode 'external' / 'external_under_gate': Jaccard(the list's HGNC genes in the cell's class "
             "universe, the external set's HGNC genes in that universe) >= corroboration.threshold (.80); the external set is the "
             "pinned register_sets set (external) or the sources 2-3 set built under the gate and passed with --external; (b) mode "
             "'printed_size': the list's length equals the printed size; (c) mode 'none': never corroborated -> the else branch, "
             "'not auditable (S undefined: source 1 uncorroborated)'. A leading-edge, overlap, hit or core-enrichment list is a "
             "strict subset of its set, so it fails (a) and (b) by construction. (11) M1: a cell of words separated by spaces is a "
             "gene list only if no word is NA-like or a registered whole token, the cell carries no statistics / result / map "
             "phrase, it is not a generic title (generic_titles), and it does not stand directly over a column of single symbols "
             "(then it is that column's title); M2: dashes (ASCII and Unicode) read as spaces, 'leading-edge' in every form; M3: a "
             "single token that is not gene-symbol-shaped is also split on punctuation and camelCase and each piece matched against "
             "the whole-token registry (pieces 't', 'es', 'or', 'se' excepted); M4: NA-like cells are dropped from a list's members"),
    "input_markers": (r"gene\s*(sets?|lists?)\s*(used|tested)" + _RB + r"|gene\s*sets?\s*lists?" + _RB + r"|" + _LB + r"inputs?" + _RB
                      + r"|" + _LB + r"definitions?" + _RB + r"|" + _LB + r"membership" + _RB),
    "input_markers_note": ("P1's wording ('gene set(s) used / tested', 'input', 'definition', 'membership', 'gene set list'); 'gene "
                           "list(s) used / tested' admitted as the same wording (Pagani's Supplementary Table 3 is titled '... gene "
                           "lists used in enrichment analyses ...'); read in the caption and, since v6.3 O2, in the list's own "
                           "forward-filled title (a merged super-header over the input columns)"),
    "result_markers": ("leading[\\s\\-\u2010-\u2015\u2212]*edge|" + _LB + "core" + _RB + "|overlap|" + _LB + "hits?" + _RB
                       + "|intersect|"
                       + _LB + "enriched" + _RB + "|significant\\s+genes?|decoded|selected\\s+genes?|" + _LB + "results?" + _RB
                       + "|" + _LB + "urgs?" + _RB + "|" + _LB + "drgs?" + _RB + "|" + _LB + "driv|" + _LB + "contribut|" + _LB
                       + "top" + _RB + "|" + _LB + "pls" + _RB + "|" + _LB + "loading|" + _LB
                       + r"weight(?!ed\s+gene\s+co\s*-?\s*expression)"),
    "result_markers_note": ("v6.3 O1 (b): letter boundaries; 'enriched' alone added (a caption 'KEGG pathways enriched in ...' is a "
                            "result: the reviewer's GAP3); v6.4 N3: 'weighted gene co-expression' (WGCNA) is not the 'weight' "
                            "marker, and 'enriched' is part of the Zhang cells' names (stripped as such)"),
    "na_like": ["NA", "NS", "ND", "NAN", "N/A"],
    "generic_titles": ["GENE", "GENES", "SYMBOL", "SYMBOLS", "GENE SYMBOL", "GENE SYMBOLS", "MEMBER", "MEMBERS"],
    "corroboration": {
        "threshold": 0.80,
        "universe_genes": "arcs/audit/register_sets/UNIVERSE_GENES.json",
        "hgnc_rule": "carrier symbols -> HGNC by the S-build's rule (approved, then previous, then alias; ambiguous dropped)",
        "rule": ("v6.5 (1) (orchestrator under the operator's standing delegation): a list the text criterion admits is source 1 "
                 "only if corroborated (per cell: cells[<id>].corroboration) -- external: Jaccard >= .80 with the pinned set, by "
                 "HGNC gene within the class universe; external_under_gate: the same against the sources 2-3 set built under the "
                 "gate (--external <per-set JSON>); printed_size: length = the printed size; none: never (not auditable, S "
                 "undefined: source 1 uncorroborated). Supersedes v6.1-v6.4's statement that 'a results table is refused whatever "
                 "its caption says'")},
    "whole_tokens": {  # v6.4 N1 (2) refined: fullmatch on the token as read ('_', '.' and dashes -> space; the name rule's reading)
        "statistics": (r"p|q|fdr|nes|es|or|z|t|se|fc|lfc|beta|stat|statistic|score|rank|ratio|odds?|fwer|padj|pval(ue)?|qval(ue)?|"
                       r"zstat|zscore|logfc|log2fc|p\s*val(ue)?|q\s*val(ue)?|p\s*adj(usted)?|adj\s*p|z\s*score|z\s*stat|"
                       r"log\s*2?\s*fc|nom\s*p|logp|log\s*10\s*p|log\s*10\s*fdr|log\s*q\s*value|enrichmentscore|"
                       r"normalizedenrichmentscore|enrichmentratio|generatio|bgratio|setsize|log2foldchange|log2err|fold|"
                       r"bonferroni|benjamini|enrichment|rho|false\s*discovery\s*rate"),
        "result": (r"core|top|plsr?\d*|hit|result|overlap|intersect(ion)?|decoded|enriched|urg|drg|loading|weight|contribution|"
                   r"driver|leading\s*edge|leadingedge|core\s*enrichment"),
        "map": (r"sg\s*\d+|subgroup\s*\d*|subtype\s*\d*|cluster\s*\d+|cohort|hypo|hyper|discovery|validation\s*\d*|val\s*\d+|"
                r"gu|kki|abide(\s*(i|ii|1|2))?|case\s*control"),
        "pieces_excepted": ["t", "es", "or", "se"],
        "note": ("v6.4 N1 (2) refined (orchestrator under the operator's standing delegation): a single cell counts as statistics / "
                 "result / map wording for the never-data rule and the sheet-level scan only when the WHOLE token, as read, equals "
                 "one of these (Python re.fullmatch; the reading singularises, so 'hits', 'results', 'cohorts' read as 'hit', "
                 "'result', 'cohort'); a heading of several words keeps the phrase matching"),
    },
    "families": {"zhang2014_top500": {"cells": ["RG-04", "RG-V08", "RG-V09", "RG-N04", "RG-N05", "RG-N06", "RG-N07"],
                                      "caption_phrases": ["zhang", "top 500"],
                                      "note": ("v6.4 N2: the only family named by its own title and the caption together; the "
                                               "caption may supply only these phrases; the sheet-level scan removes the phrases of "
                                               "every cell of the family (the other classes' columns, e.g. 'Astrocyte enriched')")}},
    "statistics_headers": (_LB + r"(p|q)(\s*(val(ue)?|adj(usted)?|fdr))?" + _RB + r"|fdr|" + _LB + r"nes" + _RB + r"|^\s*es\s*$|odds|"
                           r"false\s*discovery\s*rate|bonferroni|benjamini|" + _LB + r"rho" + _RB + r"|"
                           r"^\s*or\s*$|enrichment\s*score|" + _LB + r"z\s*score|" + _LB + r"score" + _RB + r"|" + _LB + r"fold"
                           + _RB + r"|fold\s*change|" + _LB + r"log\s*2?\s*fc" + _RB + r"|" + _LB + r"ratio" + _RB + r"|" + _LB
                           + r"rank" + _RB + r"|statistic|^\s*beta\s*$|" + _LB + r"[zt]\s*[<>=≥≤]"),
    "statistics_note": ("applied to each heading part separately (a sheet name, a caption line, a title cell) -- to the list's own "
                        "title, the caption and, since v6.3 O1 (a), every column title of the list's table; 'OR', 'ES' and 'beta' "
                        "count only as a whole part (P6); a threshold 'Z > 3' / 't >= 2' counts (v6.3)"),
    "map_names": {
        "general": _LB + r"sub\s*groups?" + _RB + "|" + _LB + r"sub\s*types?" + _RB + "|" + _LB + r"cohorts?" + _RB + "|" + _LB
                   + r"clusters?\s*\d",
        "buch2023asdsubgroups": _LB + r"sub\s*group|" + _LB + r"sg\s*\d|" + _LB + r"cluster\s*\d",
        "pagani2026crossspecies": _LB + r"hypo" + _RB + "|" + _LB + r"hyper" + _RB + "|" + _LB + r"hypo\s*-?\s*connect|" + _LB
                                  + r"hyper\s*-?\s*connect",
        "romerogarcia2019synaptic": (r"discovery|validation|" + _LB + r"val\s*\d|" + _LB + r"gu" + _RB + r"|georgetown|" + _LB + r"kki"
                                     + _RB + r"|kennedy|" + _LB + r"abide|case\s*-?\s*control"),
    },
    "symbol_pattern": r"^[A-Z][A-Z0-9]*(?:orf[0-9]+)?(?:[-.][A-Z0-9]+)*$",
    "kegg_suffix": r"^(.*?)[ _]+Homo[ _]+sapiens[ _]+(hsa\d{5})\s*$",
    "cells_note": ("keyed by cell id (P2): carrier_test.py source1 --cell <id> reads the names and the printed size from here; the "
                   "TSV builder asserts that every Buch, Pagani, R2 and Romero-Garcia family row has an entry and no other row does"),
    "cells": None,  # filled by apply_v6 (source1_cells)
    "rival_names_note": ("v6.3 O6: names that are not cells of the target but can head a list in its carrier -- for Buch, the PANTHER "
                         "16.0 GO-slim names its printed labels reach by the name rule (the builder asserts they equal "
                         "register_sets/NAME_MATCHES.json) and 'structural constituent of ribosome'; a heading naming a rival whose "
                         "name contains the cell's (longer) names the rival, not the cell"),
    "rival_names": None,  # filled by apply_v6 (source1_rivals)
    "output": "qualifies / else branch with a reason code and counts only; no gene, heading or value is printed",
}


V66_RULE = (
    "v6.6 (the orchestrator under the operator's standing delegation, 2026-09-27; the v6.5 re-check's B1, B2, C1-C3, C6): "
    "(12) B1 -- every comparator is pinned per cell (corroboration.set_id with the committed per-set JSON's sha256 and its "
    "members' sha256, or, for the Romero-Garcia KEGG families, the recipe with its libraries' sha256); the engine reads the "
    "comparator only from the committed register_sets folder, refuses a file whose set id, class or either sha256 differs, "
    "records the set id and hashes it used, and sends every read / parse / mismatch error to the else branch with its reason; "
    "no comparator file is accepted from outside (--external withdrawn). (13) B2 -- Buch's and Pagani's comparators are built "
    "before the freeze (register 1.6 resolution rule); a set the rule cannot build is 'not auditable (S undefined: "
    "comparator not buildable pre-freeze)' and its cells take mode none. (14) C1 -- the printed-size check counts DISTINCT "
    "APPROVED HGNC symbols of the list (the S-build's HGNC rule: approved, previous, alias), not rows. (15) C2 -- an approved, "
    "previous or alias HGNC symbol is never split into pieces (M3's split applies to other tokens only); a whole token equal to "
    "a registered header stays never-data (cost counted: non_data_cost). (16) C3 -- a generic title (generic_titles) is a "
    "title before the symbol test ('GENES', 'SYMBOL' over a list are its title, not its first gene). (17) C6 -- statistics "
    "wording also as a whole cell: the single tokens 'r', 't', 'corr', 'correlation' (whole_tokens) and the cells 't value' / "
    "'t-value' and 'OR (95% CI)' (whole_cells: the whole cell, as read, must match; no gene symbol is affected). v6.7: (18) a "
    "registered SECONDARY VIEW, 'near-miss comparator' (cells[<id>].corroboration_views.near_miss, run with source1 --view "
    "near_miss): for the Buch and Pagani cells whose comparator is not buildable, a comparator from a near-miss source (not the "
    "cited reference) or reached by a declared name normalisation (v6.8: or the cited source's list reached through a name "
    "bridge from a reference not cited for the set -- asdM12; v6.9: or a list reached by a semantic reading of a column "
    "note, not its title -- ASD rare de novo, Sanders 2019's ASD65; v6.10: the label names these 'note reading', PAG-C9 / C10's "
    "modules read from Gandal 2022's text among them); the view never changes the primary run. v6.7 N3: the "
    "class universes and the HGNC table are pinned by sha256 (corroboration.universe_genes_sha256, hgnc_table), asserted by the "
    "engine inside the try / except that sends every read / parse / pin mismatch to the else branch")
V66_WHOLE_CELLS = r"t\s*value|or\s*\(\s*95\s*%?\s*ci\s*\)"
V66_CORROBORATION_RULE = (
    "v6.5 (1) as pinned by v6.6 B1 (orchestrator under the operator's standing delegation): a list the text criterion admits is "
    "source 1 only if corroborated (per cell: cells[<id>].corroboration) -- external: Jaccard >= .80 with the cell's comparator, "
    "by HGNC gene within the class universe, the comparator read ONLY from sets_dir/<set_id>.json and only if its set_id, its "
    "file sha256 (json_sha256), its members' sha256 (members_sha256, the SHA-256 of the sorted members_hgnc joined by LF) and "
    "the class universe match the pins; kegg_family_recipe: the same Jaccard against the pathway the engine builds from the "
    "pinned Enrichr library (recipe); printed_size: the number of DISTINCT APPROVED HGNC symbols of the list equals the printed "
    "size (v6.6 C1); none: never (not auditable, S undefined). Every refusal of a comparator (missing, unreadable, malformed, "
    "set id / class / sha256 mismatch) is an else branch with its reason; the record names the set id and the hashes used")


def v66_spec(s1: dict) -> dict:
    """register v6.6 on top of the v6.5 source-1 spec (B1 pins, C1 distinct approved symbols, C2 no pieces for HGNC symbols,
    C3 generic titles first, C6 whole-cell statistics wording)."""
    s1 = json.loads(json.dumps(s1))
    old10 = "pinned register_sets set (external) or the sources 2-3 set built under the gate and passed with --external"
    assert old10 in s1["rule"]
    s1["rule"] = s1["rule"].replace(old10, "pinned register_sets set (external; v6.6 B1: pinned by set id and sha256) or, for "
                                    "the Romero-Garcia KEGG families, the pathway the engine builds by the recipe (v6.6 B1; "
                                    "v6.5's --external withdrawn)") + ". " + V66_RULE
    s1["whole_tokens"]["statistics"] = s1["whole_tokens"]["statistics"] + r"|r|corr|correlation"
    s1["whole_tokens"]["note"] = s1["whole_tokens"]["note"] + (
        "; v6.6 C2: an approved / previous / alias HGNC symbol is matched as a whole token only, never split into pieces; "
        "v6.6 C6: 'r', 'corr', 'correlation' added (the lone 't' was already registered)")
    s1["whole_cells"] = {"statistics": V66_WHOLE_CELLS,
                         "note": ("v6.6 C6: a cell of several words counts as statistics wording when the WHOLE cell, as read "
                                  "('_', '.', dashes -> spaces; case, spelling, number normalised), matches (fullmatch): 't value' "
                                  "(also 't-value', 'T VALUE'), 'OR (95% CI)'; checked in the sheet-level scan and on every column "
                                  "title of the list's table; no gene symbol is a cell of several words")}
    s1["generic_titles_note"] = "v6.6 C3: a generic title is a title before the symbol test (it is never the list's first gene)"
    s1["hgnc_symbols_note"] = ("v6.6 C2: the approved, previous and alias symbols of the pinned HGNC file are exempt from M3's "
                               "piece split (they are matched as whole tokens only); an HGNC symbol that is not symbol-shaped "
                               "(symbol_pattern) is still not a list member (counted in non_data_cost)")
    c = s1["corroboration"]
    c["rule"] = V66_CORROBORATION_RULE
    c["sets_dir"] = "arcs/audit/register_sets"
    c["members_sha256"] = "sha256 of '\\n'.join(members_hgnc) (the per-set JSON's sorted HGNC members), UTF-8"
    c["printed_size_count"] = "distinct approved HGNC symbols of the list (the S-build's HGNC rule), v6.6 C1"
    # register v6.7 N3: the class universes and the HGNC table the engine reads, pinned by sha256 (asserted and recorded by the
    # engine inside the try / except that routes every read / parse / mismatch to the else branch)
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import s_build as SB
    uf = ROOT / c["universe_genes"]
    c["universe_genes_sha256"] = hashlib.sha256(uf.read_bytes()).hexdigest()
    c["universe_min_genes"] = 10000
    assert min(len(v) for v in json.loads(uf.read_text(encoding="utf-8"))["classes"].values()) >= c["universe_min_genes"]
    c["hgnc_table"] = {"path": str(SB.PIN["hgnc"][0]), "sha256": SB.PIN["hgnc"][1]}
    assert hashlib.sha256(Path(SB.PIN["hgnc"][0]).read_bytes()).hexdigest() == SB.PIN["hgnc"][1]
    c["pins_note_v6_7"] = ("N3: universe_genes_sha256 and hgnc_table.sha256 are asserted by the engine before any corroboration "
                           "(a mismatch, a missing or unreadable file, or a universe under universe_min_genes genes in a class "
                           "-> the else branch, recorded); the S-build's universe holds > 15,000 genes per class")
    return s1


def non_data_cost(s1: dict) -> dict:
    """register v6.4 N1 (2) as refined (whole tokens), its cost counted: the approved HGNC symbols (the pinned HGNC file) that the
    non-data rule excludes (NA-like, or the whole token equal to a registered header) -- a list whose first genes include one of
    them has them fall into its title and is refused."""
    import re as _re
    from collections import Counter
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import pandas as pd_
    import carrier_test as CT
    import s_build as SB
    cs = pd_.read_csv(SB.pinned("hgnc"), sep="\t", dtype=str, keep_default_na=False)
    sym = _re.compile(s1["symbol_pattern"])
    wt = {k: _re.compile(v, _re.I) for k, v in s1["whole_tokens"].items() if k not in ("note", "pieces_excepted")}
    na = {x.upper() for x in s1["na_like"]}
    gen = {x.upper() for x in s1["generic_titles"]}
    hits, rules, shapeless = {}, Counter(), {}
    for symb, grp in zip(cs["symbol"], cs["locus_group"]):
        if not sym.match(symb):
            shapeless[symb] = grp  # v6.6 C2: never a list member (not symbol-shaped), never split into pieces
            continue
        t = CT._tx(symb).strip()
        k = [n for n, c in (("na_like", symb.upper() in na), ("statistics", wt["statistics"].fullmatch(t)),
                            ("result", wt["result"].fullmatch(t)), ("map", wt["map"].fullmatch(t)),
                            ("generic_title", symb.upper() in gen)) if c]
        if k:
            hits[symb] = grp
            rules[" + ".join(k)] += 1
    # v6.5 M4: previous / alias symbols a carrier may print, equal to a registered token (they are never data either)
    old = {}
    for col in ("prev_symbol", "alias_symbol"):
        for symb, lst in zip(cs["symbol"], cs[col]):
            for a in [x.strip() for x in str(lst).split("|") if x.strip()]:
                t = CT._tx(a).strip()
                if sym.match(a) and (a.upper() in na or a.upper() in gen or any(wt[r].fullmatch(t) for r in wt)):
                    old.setdefault(a, set()).add(symb)
    return {"what": ("v6.4 N1 (2) as refined (whole tokens), counted as v6.6 C2 reads it (an HGNC symbol is matched as a WHOLE "
                     "token only, never split into pieces): the approved HGNC symbols (the pinned HGNC file, %s) the non-data "
                     "rule excludes; a list whose first gene(s) are among them has them fall into its title zone and is refused "
                     "as a whole (the safe direction); deeper in a list they stay genes; and, apart, the approved symbols that are "
                     "not symbol-shaped (never list members)" % SB.PIN["hgnc"][1][:12]),
            "n_symbols": len(hits), "by_locus_group": dict(sorted(Counter(hits.values()).items())),
            "n_not_symbol_shaped": len(shapeless),
            "not_symbol_shaped_by_locus_group": dict(sorted(Counter(shapeless.values()).items())),
            "by_rule": dict(sorted(rules.items())),
            "protein_coding": sorted(k for k, v in hits.items() if v == "protein-coding gene"), "symbols": sorted(hits),
            "previous_or_alias_symbols": {a: sorted(v) for a, v in sorted(old.items())},
            "n_previous_or_alias_symbols": len(old),
            "sheet_wide_effect": ("v6.5 M4: such a symbol is never a gene of a list; as the first gene(s) of a column it falls into the "
                                  "title (the list refused); inside a space-separated list it makes the cell a non-list; anywhere "
                                  "outside a list's gene run it is scanned by the sheet-level rule, so a sheet holding it there has "
                                  "every list refused")}


def source1_rivals() -> dict:
    """register v6.3 O6: Buch's rival names -- the PANTHER 16.0 GO-slim names its printed Fig. 5f-h labels reach by the name rule
    (the pinned PANTHERGOslim.obo, as the S-build maps them) and 'structural constituent of ribosome'."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import name_match as NM
    import s_build as SB
    terms, _ = SB.read_obo(SB.pinned("panther_16.0_goslim"))
    cands = SB.obo_candidates(terms, None)
    grid = json.loads((ROOT / "arcs" / "audit" / "register_maps" / "buch_fig5h_grid.json").read_text(encoding="utf-8"))
    labels = [lab for _, _, lab in _BUCH_F_G] + [lab.lstrip("*").strip() for lab in grid["rows_top_to_bottom_as_printed"]]
    names = set()
    for lab in labels:
        rec = NM.match(lab, cands)
        if rec["id"]:
            names.add(rec["name"])
    names.add("structural constituent of ribosome")
    return {"buch2023asdsubgroups": [[n] for n in sorted(names)]}


# Q8: the PDF adapter, pinned; installed and plant-tested before the freeze (2026-09-26)
V61_PDF = {
    "package": "pdfplumber", "version": "0.11.10",
    "dependencies": {"pdfminer.six": "20260107", "pypdfium2": "5.13.0"},
    "requirement": ("under the gate, before the adapter's first use on a carrier, pdfplumber is installed at this version (the "
                    "engine refuses another version: the file counts as 'adapter unavailable') and carrier_test.py selftest runs "
                    "its synthetic-PDF plants, a misaligned label / value case among them, which must be caught; installed in the "
                    "programme venv and run before the freeze, 2026-09-26 (carrier_tests_selftest.json)"),
    "extraction": ("page.extract_tables() per page, a page's first table continuing the previous page's last table when the column "
                   "counts are equal (a repeated header row dropped); page.extract_text() lines as carrier text (the R9 order-file "
                   "search)"),
}
RUN_STAMPS = ("built_utc", "script", "amendments")  # not compared by --check


def apply_v5(spec: dict, rg: list[dict]) -> dict:
    """register v5 section 1.11 item 8, applied in the key order of the hand-applied v5 spec (changed keys in place, new keys
    appended)."""
    spec["rules"].update(V5_RULES)
    t = spec["targets"]
    t["buch2023asdsubgroups"].update(V5_BUCH)
    t["mamat2025molecular"].update(V5_MAMAT)
    rgt = t["romerogarcia2019synaptic"]
    left = [d["key"] for d in rg if d["hemisphere"] == "L"]
    assert len(left) == 152 == rgt["required_count_left_route"], len(left)
    rgt["required_count"] = len(left)
    rgt["pass_rule"] = V5_RG_PASS
    rgt["required_label_space"] = V5_RG_SPACE
    rgt["required_labels"] = left
    return spec


def apply_v6(spec: dict) -> dict:
    """register v6 R9: Mamat's index-only tables need the carrier to name the 17-network order file; v6.1 Q1 / Q8: the
    source-1 criterion and the pinned PDF adapter; v6.2 P1 / P2 / P6 / P7 (b): the criterion positive, keyed by cell id; v6.3
    O1-O4 / O6: table-level statistics, letter boundaries, input wording in the list's own title, own phrases stripped, one
    --name per family run, rival names; v6.4 N1-N4: sheet-level refusal, non-data tokens, family-limited split naming, rival-only
    names."""
    spec["rules"].update(V6_RULES)
    t = spec["targets"]["mamat2025molecular"]
    t["index_labels"] = V6_MAMAT_INDEX
    t["pass_rule"] = V6_MAMAT_PASS
    s1 = v66_spec(dict(V65_SOURCE1))  # register v6.6
    s1["cells"] = source1_cells()  # register v6.2 P2
    s1["rival_names"] = source1_rivals()  # register v6.3 O6
    s1["non_data_cost"] = non_data_cost(s1)  # register v6.4 N1 (2)
    spec["source1_lists"] = s1
    spec["pdf_adapter"] = V61_PDF
    return spec


def diff_paths(a, b, path="", out=None) -> list[str]:
    """key paths where two JSON values differ (paths only: no content is printed)."""
    out = [] if out is None else out
    if isinstance(a, dict) and isinstance(b, dict):
        if list(a) != list(b):
            out.append((path or "/") + " (keys or key order)")
        for k in a:
            if k in b:
                diff_paths(a[k], b[k], "%s/%s" % (path, k), out)
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            out.append("%s (length %d vs %d)" % (path, len(a), len(b)))
        for i, (x, y) in enumerate(zip(a, b)):
            diff_paths(x, y, "%s[%d]" % (path, i), out)
    elif a != b or type(a) is not type(b):
        out.append(path)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="carrier_tests.json (register v4 1.8, v5 1.11 item 8); see the module docstring")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--check", action="store_true", help="compare a rebuild with the file on disk; write nothing")
    g.add_argument("--overwrite", action="store_true", help="rewrite an existing spec (then re-run the self-test and the TSV build)")
    a = ap.parse_args()
    if OUT.exists() and not (a.check or a.overwrite):
        print("REFUSED: %s exists (sha256 %s) and holds the register v5 readings frozen with the register; nothing written. "
              "Use --check to compare a rebuild with it, --overwrite to replace it." % (OUT.relative_to(ROOT).as_posix(),
                                                                                          sha256_file(OUT)))
        return 3
    dk_src, dk_ctx, dk_sub = dk_labels()
    pw_src, pw = power_labels()
    sc_src, sc = schaefer_labels(write_source=not a.check)
    rg_src, rg = dk308_labels()
    n_l = sum(1 for d in rg if d["hemisphere"] == "L")
    n_r = sum(1 for d in rg if d["hemisphere"] == "R")
    spec = {
        "what": ("Carrier tests of claims register v4 section 1.8 for every conditional target (TSV status 'conditional'): "
                 "Rasero (24 rows), Buch (212), Mamat (28), Romero-Garcia (48). Pre-registered before the freeze; run under each "
                 "target's gate by arcs/audit/src_register/carrier_test.py, which prints pass / fail and counts only."),
        "built_utc": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "rules": RULES,
        "targets": {
            "rasero2023neurogenetics": {
                "target_no": 6, "gate": "G1",
                "carriers": ["repo notebook 05-mdmr_subtypes_vs_TDC.ipynb (outputs)", "journal mmc1.pdf"],
                "carrier_identity": ident_refs("rasero2023neurogenetics"),
                "rule": ("either carrier qualifies (register 2.6); the per-gene-step variant (dk34 or dk41) is fixed from notebook "
                         "08-calculate_gen_pvals.ipynb or the journal Methods BEFORE the carrier test runs, and recorded; "
                         "undeterminable -> not auditable (definition not applicable)"),
                "label_space": "abagen DK (left hemisphere)", "label_source": dk_src, "normalisation": "normalisation_dk",
                "variants": {"dk34": {"labels": [d["key"] for d in dk_ctx], "required_count": 34},
                             "dk41": {"labels": [d["key"] for d in dk_ctx + dk_sub], "required_count": 41}},
                "labels_detail": dk_ctx + dk_sub,
                "maps": [
                    {"map_id": "y_S1", "needed_by": "RA-13, RA-14, RA-N3 (descriptor)",
                     "map_token": r"subtype[\s_-]*1(?!\d)|\bs1\b|hypo[\s_-]*connect", "object_token": r"pseudo|r\s*\^?\s*2|r²|mdmr"},
                    {"map_id": "y_S2", "needed_by": "RA-01 ... RA-12",
                     "map_token": r"subtype[\s_-]*2(?!\d)|\bs2\b|hyper[\s_-]*connect", "object_token": r"pseudo|r\s*\^?\s*2|r²|mdmr"}],
                "pass_rule": "both maps pass (every required label of the variant present once, every value numeric)",
                "statuses_if_fail": "RA-01 ... RA-14 and RA-N3 -> not auditable (carrier test failed: <reason>)",
            },
            "buch2023asdsubgroups": {
                "target_no": 7, "gate": "G1",
                "carriers": ["MOESM3.xlsx (Supplementary Tables 4-5)"],
                "carrier_identity": ident_refs("buch2023asdsubgroups"),
                "label_space": "Power 2011 264 ROIs (ids and MNI coordinates)", "label_source": pw_src,
                "normalisation": "power_matching",
                "labels": [d["key"] for d in pw], "labels_detail": pw,
                "required_count": 230, "required_comparison": ">= (usable ROIs per map: numeric id, x, y, z and value)",
                "maps": [{"map_id": "y_%d" % k, "needed_by": "BUCH-C%d and every subgroup-%d enrichment / descriptor cell" % (k, k),
                          "map_token": r"sub[\s_-]*group[\s_-]*%d(?!\d)|\bsg[\s_-]*%d(?!\d)|cluster[\s_-]*%d(?!\d)|\bs%d\b" % (k, k, k, k),
                          "object_token": r"atypical|connectivity|rsfc|\bfc\b|net"} for k in (1, 2, 3, 4)],
                "pass_rule": "all four maps pass (>= 230 usable ROIs each, every value and coordinate numeric)",
                "statuses_if_fail": ("every Buch row -> not auditable (carrier test failed: <reason>); coordinates absent -> "
                                     "'not auditable (ROI coordinates unpublished)' (register 1.7)"),
            },
            "mamat2025molecular": {
                "target_no": 8, "gate": "G1",
                "carriers": ["Additional file 1 (PDF)", "Additional files 2-4 (xlsx)"],
                "carrier_identity": ident_refs("mamat2025molecular"),
                "label_space": "Schaefer 2018 400 parcels, 17 networks", "label_source": sc_src,
                "normalisation": "normalisation_schaefer",
                "labels": [d["key"] for d in sc], "labels_detail": sc, "required_count": 400,
                "maps": [
                    {"map_id": "ABIDE I FD t-map", "needed_by": "MAMAT-C1, MAMAT-C2 and every enrichment claim (both maps)",
                     "map_token": r"abide[\s_-]*(i|1)(?![i\d])", "object_token": r"\bt\b|t[\s_-]*(map|value|stat)|\bfd\b|fractal"},
                    {"map_id": "ABIDE II FD t-map", "needed_by": "MAMAT-C3 and every enrichment claim (both maps)",
                     "map_token": r"abide[\s_-]*(ii|2)(?![i\d])", "object_token": r"\bt\b|t[\s_-]*(map|value|stat)|\bfd\b|fractal"}],
                "pass_rule": ("per map; C1 / C2 need the ABIDE I map, C3 the ABIDE II map, every enrichment claim both "
                              "(register 2.8); the carrier set (files 1-4) is searched as one"),
                "statuses_if_fail": "claims needing a failed map -> not auditable (carrier test failed: <reason>)",
            },
            "romerogarcia2019synaptic": {
                "target_no": 4, "gate": "G1",
                "carriers": ["MOESM1 docx", "MOESM2 docx", "Apollo SI .txt", "Apollo Figures_Tables.zip (each table file inside)"],
                "carrier_identity": ident_refs("romerogarcia2019synaptic"),
                "label_space": "DK-308 (152 lh + 156 rh)", "label_source": rg_src, "normalisation": "normalisation_dk308",
                "labels": [d["key"] for d in rg], "labels_detail": rg,
                "required_count": 308, "required_count_left_route": n_l,
                "maps": [
                    {"map_id": "discovery DeltaCT", "needed_by": "RG-01 and the discovery descriptors",
                     "map_token": r"discovery|abide[\s_-]*(i|1)(?![i\d])", "object_token": r"delta|Δ|ct\b|thickness|difference|case"},
                    {"map_id": "Validation 1 DeltaCT", "needed_by": "RG-V01 and the Val1 descriptors",
                     "map_token": r"validation[\s_-]*(1|i)(?![i\d])|\bval[\s_-]*1(?!\d)|\bgu\b|georgetown",
                     "object_token": r"delta|Δ|ct\b|thickness|difference|case"},
                    {"map_id": "Validation 2 DeltaCT", "needed_by": "RG-V02 and the Val2 descriptors",
                     "map_token": r"validation[\s_-]*(2|ii)(?![i\d])|\bval[\s_-]*2(?!\d)|\bkki\b|kennedy",
                     "object_token": r"delta|Δ|ct\b|thickness|difference|case"}],
                "pass_rule": "per map, each searched separately: all 308 labels present once, every value numeric (TSV text)",
                "statuses_if_fail": "cells needing a failed map -> not auditable (carrier test failed: <reason>)",
            },
        },
        "sources_checked": {"dk308_names_txt_equals_annots": rg_src["308_regions_names.txt"]["equals_annot_names"],
                            "dk308_counts": {"L": n_l, "R": n_r}},
        "script": {"path": "arcs/audit/src_register/carrier_labels.py", "sha256": sha256_file(Path(__file__)),
                   "repo_head_at_run": subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True,
                                                      text=True).stdout.strip()},
    }
    apply_v5(spec, rg)
    apply_v6(spec)
    print("DK left ctx %d + sub %d; Power %d; Schaefer %d; DK-308 L %d R %d (names.txt equal: %s)"
          % (len(dk_ctx), len(dk_sub), len(pw), len(sc), n_l, n_r, rg_src["308_regions_names.txt"]["equals_annot_names"]))
    old = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else None
    if a.check:
        if old is None:
            print("CHECK: %s does not exist" % OUT.relative_to(ROOT).as_posix())
            return 4
        d = diff_paths({k: v for k, v in spec.items() if k not in RUN_STAMPS}, {k: v for k, v in old.items() if k not in RUN_STAMPS})
        if d:
            print("CHECK: DIFFERS from %s at %d key paths (run stamps %s aside): %s"
                  % (OUT.relative_to(ROOT).as_posix(), len(d), ", ".join(RUN_STAMPS), "; ".join(d[:20])))
            return 4
        print("CHECK: EQUAL -- a rebuild equals %s (sha256 %s) except its run stamps (%s); nothing written"
              % (OUT.relative_to(ROOT).as_posix(), sha256_file(OUT), ", ".join(RUN_STAMPS)))
        return 0
    if old is not None:  # --overwrite: carry the amendments record forward, add this regeneration
        spec["amendments"] = list(old.get("amendments", [])) + [{
            "date": dt.date.today().isoformat(),
            "register": "claims register DRAFT v6.11 (text fixes of the v6.10 re-check; the spec's content unchanged) on top of "
                        "DRAFT v6.10 (C3 / C5: the view's label adds '/ note reading' -- RDNV's column note, "
                        "PAG-C9 / C10's Results text; C1: the privacy guard reads sheets by their cells) on top of "
                        "DRAFT v6.9 (C5: Buch's 'ASD rare de novo' moved to the near-miss view by reading "
                        "(iii) applied uniformly -- BUCH-E-RDNV-S1 ... S4, descriptor cells, mode none in the primary run, "
                        "their near-miss pin Sanders 2019's ASD65 set; C3: the view's label adds '/ name bridge') on top of "
                        "DRAFT v6.8 (B S1: asdM12 moved to the near-miss view -- BUCH-E-ASDdown-S1 ... S4 mode "
                        "none in the primary run, their near-miss pin Voineagu 2011's Table 14 set; C: the PAG near-miss sets "
                        "found by a content-word search) on top of DRAFT v6.7 "
                        "(the registered secondary view 'near-miss comparator' pinned per cell in "
                        "corroboration_views; the uniform archive rule re-pins the RGD / CTD comparators) on top of DRAFT v6.6 "
                        "(B1: every comparator pinned by set id + file / members sha256, or by the KEGG "
                        "family recipe; the engine refuses anything else and sends every read / parse / mismatch error to the "
                        "else branch; --external withdrawn; B2: Buch's non-GO and Pagani's comparators built before the freeze, "
                        "the unbuildable ones mode none; C1: the printed size counts distinct approved HGNC symbols; C2: HGNC "
                        "symbols never split into pieces; C3: generic titles before the symbol test; C6: whole-cell statistics "
                        "wording) on top of "
                        "claims register DRAFT v6.5 ((1) corroboration: Jaccard >= .80 with the pinned external set, else the "
                        "printed size, else never; (2)-(3) M1-M4: space-separated cells, dashes, camelCase pieces, generic titles, "
                        "NA-like members dropped) on top of DRAFT v6.4 (N1: sheet-level refusal on statistics / result / map wording anywhere on the "
                        "list's sheet; NA / NS / ND / NAN / N/A and marker-shaped single tokens are never data; N2: split naming "
                        "only for the Zhang family (caption phrases 'zhang' / 'top 500'), RG-15 / RG-V23 named by their own title "
                        "only; N3: 'enriched' in the Zhang names, 'weighted gene co-expression' not 'weight'; N4: --rival names "
                        "for family runs; N1 (2) refined: a single cell counts only as a whole registered token, whole_tokens) "
                        "on top of v6.3 (O1: statistics wording in any column title of the list's table refuses it; "
                        "'_' / '.' read as spaces and letter-bounded markers; 'enriched' a result word; O2: input wording also in "
                        "the list's own forward-filled title; O3: the cell's own phrases stripped wherever they appear, 'top N' "
                        "with N = the printed size exempt; O4: a printed KEGG '[ _]Homo sapiens[ _]hsaNNNNN' suffix split off, one "
                        "--name per family run; O6: rival_names (Buch's PANTHER names and 'structural constituent of ribosome'); "
                        "v6.2 P1 / P2 / P6, v6.1 Q8 and v6 R9 kept)",
            "how": "regenerated by carrier_labels.py --overwrite; the v5 and v6 readings are encoded in the script (apply_v5, "
                   "apply_v6)",
            "replaced_sha256": sha256_file(OUT)}]
    txt = json.dumps(spec, indent=1, ensure_ascii=False)
    OUT.write_text(txt, encoding="utf-8", newline="\n")
    assert json.loads(OUT.read_text(encoding="utf-8")) == json.loads(txt)
    print("output %s sha256 %s" % (OUT.relative_to(ROOT).as_posix(), sha256_file(OUT)))
    if old is not None:
        print("NOTE: the spec changed; re-run carrier_test.py selftest and claims_register_tsv_build.py (the builder refuses a "
              "self-test record of another spec; the TSV pins the spec's sha256 on every conditional row)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
