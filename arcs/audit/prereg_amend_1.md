# PREREG AMENDMENT 1 — A1 `audit`: AHBA computation environment (§3.1 A5, env)

Amends `prereg.md` (frozen 2026-09-23, sha256 a632b852…). Written 2026-09-23 **before any AHBA matrix was
computed**: both attempted runs crashed inside abagen before producing output (tracebacks below), so no
measurement was seen.

## What happened
- Main venv (Python 3.13, pandas 3.0.6, abagen 0.1.3): `abagen/probes_.py:147`
  `DataFrame.groupby(..., axis=1)` → `TypeError: unexpected keyword argument 'axis'` (removed in pandas 3).
- A5 reference venv (Python 3.13, pandas 2.2.3, abagen 0.1.3): `abagen/probes_.py:757`
  `DataFrame.set_axis(..., inplace=False)` → `TypeError: unexpected keyword argument 'inplace'` (removed in
  pandas 2.0).
abagen 0.1.3 therefore runs on neither environment frozen in §3.1; it requires pandas < 2.

## Change
1. **AHBA matrices (§3.1) are computed with abagen 0.1.3 in the environment it was released for**:
   `env/venv_ref` — Python 3.10.20 (uv-managed), pandas 1.5.3, numpy 1.24.4, nibabel 5.2.1, nilearn 0.10.3,
   scipy 1.11.4, scikit-learn 1.3.2 (lock: `env/requirements_ref.lock`). Same script
   (`arcs/audit/src/e4_ahba_matrices.py`), same frozen settings. Everything downstream (engine, plants,
   audit) keeps running in the main Python 3.13 venv and reads the saved matrices; no abagen call happens there.
2. **A5 becomes a cross-version check**: V-DK recomputed with abagen GitHub master @dc4a007e
   (0.1.4+15, 2023-09-29) in `env/venv_pd22` (pandas 2.2.3): max |Δ| < 1e-6 against the venv_ref matrix and
   an identical gene list, else K2 unless reconciled to a documented code difference between 0.1.3 and master.
   If abagen master itself cannot run on pandas 2.2.3, A5 is recorded as "not runnable" with the traceback;
   A2 (exact 15,633 genes) then stands alone as the value check and this is stated in every report.
3. Nothing else in `prereg.md` changes.
