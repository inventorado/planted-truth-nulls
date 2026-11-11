"""A1 pre-freeze enumeration PRE-DG (register §3.4; TSV row PRE-DG, n_cells 'UNDETERMINED: at most 6').

Approved re-read (operator, 2026-09-26) of Pretzsch 2024 Supplement 1 eTables 3-4 (already read 2026-09-25, exposure
declared in register §0). ONLY the row labels and the gene-set identity (which decoded list x which Gandal
direction) are read; no value of either table (k, K, OR, p) is parsed, printed or recorded: every line is used only
as a label token, and numeric tokens are never collected.

Run: C:\\Python313\\python.exe -X utf8 arcs\\audit\\src_register\\pre_dg_rows.py
Writes arcs/audit/register_sets/PRE_DG_ROWS.json (UTF-8, read back).
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[3]
PDF = Path(r"E:\data\asdg\pretzsch2024patterns\supplement\jamapsychiatry-e243194-s001.pdf")
OUT = ROOT / "arcs" / "audit" / "register_sets" / "PRE_DG_ROWS.json"
GANDAL = {"ASD_downregulatedgenes": "down", "ASD_upregulated": "up"}
TABLES = {  # eTable -> (pages, title pattern, sign of the decoded list's association)
    3: ((34, 35), r"Table S(\d) Genes positively associated with a neurotypical maturational pattern", "positive"),
    4: ((36, 37), r"Table S(\d) Genes negatively associated with a neurotypical maturational pattern", "negative"),
}
REGISTERED = {("SA", "negative", "down"): "PRE-D1", ("SA", "negative", "up"): "PRE-D1r"}


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> None:
    doc = fitz.open(str(PDF))
    rows = []
    for tno, (pages, pat, sign) in TABLES.items():
        text = "\n".join(doc[p - 1].get_text() for p in pages)
        m = re.search(pat, text)
        assert m and int(m.group(1)) == tno, f"eTable {tno} title not found on pp. {pages}"
        feature = None
        for line in (x.strip() for x in text.splitlines()):
            if line in ("CT", "SA"):
                feature = line
            elif line in GANDAL:
                assert feature is not None, "Gandal row before any feature section"
                rows.append({"etable": tno, "pages": list(pages), "feature": feature,
                             "decoded_list": f"{feature}-{sign} (genes {sign}ly associated with a neurotypical "
                                             "maturational pattern)",
                             "row_label": line, "gandal_direction": GANDAL[line]})
    keyed = [(r["feature"], r["decoded_list"].split(" ")[0].split("-")[1], r["gandal_direction"]) for r in rows]
    assert len(rows) == 8 and len(set(keyed)) == 8, f"{len(rows)} Gandal rows / {len(set(keyed))} distinct"
    other = []
    for r, k in zip(rows, keyed):
        if k in REGISTERED:
            continue
        other.append({**r, "set_id": f"gandal2018_asd_{r['gandal_direction']}",
                      "set_S": ("Gandal 2018 ASD-" + ("down" if r["gandal_direction"] == "down" else "up")
                                + "regulated genes (register §1.6 pinned: gene-level table, ASD FDR < .05 with log2FC "
                                + ("< 0" if r["gandal_direction"] == "down" else "> 0") + ")"),
                      "direction": "two-sided (register §3.4: every other Gandal up / down row, two-sided)"})
    order = {"CT": 0, "SA": 1}
    other.sort(key=lambda r: (r["etable"], order[r["feature"]], r["gandal_direction"] != "down"))
    for i, r in enumerate(other, 1):
        r["proposed_cell_id"] = f"PRE-DG-{i:02d}"
    out = {"what": "Pretzsch 2024 eTables 3-4: the Gandal 2018 up / down rows other than PRE-D1 (SA-negative x down) "
                   "and PRE-D1r (SA-negative x up); labels and gene-set identity only (no value read)",
           "source": {"path": str(PDF), "sha256": sha256(PDF), "pages": [34, 35, 36, 37]},
           "script": "arcs/audit/src_register/pre_dg_rows.py",
           "n_gandal_rows_total": len(rows), "registered_elsewhere": sorted(REGISTERED.values()),
           "n_other_rows": len(other), "rows": other}
    txt = json.dumps(out, indent=1, ensure_ascii=False) + "\n"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_bytes(txt.encode("utf-8"))
    assert OUT.read_bytes().decode("utf-8") == txt
    print(f"PRE_DG_ROWS.json: {len(other)} rows; sha256 {sha256(OUT)}")
    for r in other:
        print(" ", r["proposed_cell_id"], f"eTable {r['etable']}", r["feature"], r["decoded_list"].split(" ")[0],
              r["row_label"])


if __name__ == "__main__":
    main()
