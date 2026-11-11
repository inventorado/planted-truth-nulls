"""A1 audit runner (arcs/audit/RUN_PLAN.md v3.1, FROZEN 2026-10-01, sha256 16c60232...).

Runs the frozen claims register (v6.11) under the plan's readings. New code lives here, never in src_register/
(RUN_PLAN §3 placement rule). A3 helpers are copied into a3_port.py, never imported by runner code (§3, R1).
Run from arcs/audit/src:  ../../../env/venv/Scripts/python.exe -X utf8 -m a1_audit.<module>
Tests are plain scripts (no pytest in the programme venv): python -X utf8 -m a1_audit.tests.<test_module>;
each exits non-zero on failure.

Modules (WP1): launch (L1-L15, provenance), loader (TSV), seeds (R7, R24), gates (step3v_open, g1_open,
require_g1_open), gate_launch (CLI), a3_port (copied A3 helpers), adapters (T forms, R3), verdict (form-generic
verdict driver), descriptors (descriptor legs), run (dispatch, sources interface, checkpoints, results writer, --plant),
plant_mode (amendment 3's plant-mode G6l), l14_glue (the gate launcher's carrier self-test output into L14).
"""
