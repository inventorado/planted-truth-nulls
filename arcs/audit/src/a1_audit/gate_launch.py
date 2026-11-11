"""Gate launcher (arcs/audit/RUN_PLAN.md v3.1 section 2.2, "Gate launcher"; L14, L15).

    python -X utf8 -m a1_audit.gate_launch <G1|G2> [--repo PATH] -- <command ...>
    python -X utf8 -m a1_audit.gate_launch G1 [--repo PATH] --carrier-test [<carrier_test.py args ...>]

Runs the gate's check against the repository (default: the git toplevel of the current directory) -- G1:
require_g1_open(), G2: step3v_open() -- and only then starts the command in a subprocess, returning its exit code.
A closed gate means a refusal: a non-zero exit code and no subprocess. `--carrier-test` resolves to
<repo>/arcs/audit/src_register/carrier_test.py run by this interpreter, under the G1 check only (the frozen carrier
engine holds no gate check of its own and is started only through this launcher).

Prints fixed-vocabulary lines only: the gate, open / CLOSED with the check's reason label, the command's basename and
the exit code. Never the command's arguments.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

from a1_audit import gates

CARRIER_TEST_REL = "arcs/audit/src_register/carrier_test.py"
EXIT_USAGE = 2
EXIT_REFUSED = 3
EXIT_NOT_STARTED = 4
_SAFE_NAME = re.compile(r"[A-Za-z0-9._+-]{1,64}")


def _say(line: str) -> None:
    print("gate_launch: " + line, flush=True)


def _basename(arg: str) -> str:
    name = Path(arg).name
    return name if _SAFE_NAME.fullmatch(name) else "<unprintable-name>"


def _spawn(cmd: list[str]) -> int:
    """The only place a subprocess is started (tests replace it to prove a refusal starts nothing)."""
    return subprocess.run(cmd).returncode


def parse(argv: list[str]) -> tuple[str, Path | None, list[str], bool]:
    """(gate, repo or None, command, carrier_test?). Raises ValueError on a malformed command line."""
    if not argv or argv[0] not in ("G1", "G2"):
        raise ValueError("gate")
    gate, rest, repo = argv[0], argv[1:], None
    while rest and rest[0] == "--repo":
        if len(rest) < 2 or repo is not None:
            raise ValueError("repo")
        repo, rest = Path(rest[1]), rest[2:]
    if rest and rest[0] == "--carrier-test":
        args = rest[1:]
        if args and args[0] == "--":
            args = args[1:]
        if gate != "G1":
            raise ValueError("carrier test is G1 only")
        return gate, repo, args, True
    if not rest or rest[0] != "--" or len(rest) < 2:
        raise ValueError("command")
    return gate, repo, rest[1:], False


def check(gate: str, repo: Path) -> tuple[bool, str]:
    """(open?, reason label). G1 through require_g1_open (the plan's named call), G2 through step3v_open."""
    if gate == "G1":
        try:
            gates.require_g1_open("gate_launch", repo)
        except PermissionError:
            return False, gates.g1_check(repo)[1]
        return True, "open"
    if gate == "G2":
        ok, reason, _ = gates.step3v_check(repo)
        return (ok is True and gates.step3v_open(repo) is True), reason
    return False, "unknown_gate"


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        gate, repo, command, carrier = parse(argv)
    except ValueError:
        _say("usage: gate_launch <G1|G2> [--repo PATH] -- <command ...> | G1 [--repo PATH] --carrier-test [args]")
        return EXIT_USAGE
    if repo is None:
        repo = gates.git_toplevel()
        if repo is None:
            _say(f"gate {gate} CLOSED (reason no_repository); command not started")
            return EXIT_REFUSED
    ok, reason = check(gate, repo)
    if not ok:
        _say(f"gate {gate} CLOSED (reason {reason}); command not started")
        return EXIT_REFUSED
    _say(f"gate {gate} open")
    if carrier:
        command = [sys.executable, "-X", "utf8", str(Path(repo) / CARRIER_TEST_REL), *command]
        shown = Path(CARRIER_TEST_REL).name
    else:
        shown = _basename(command[0])
    _say(f"starting {shown}")
    try:
        code = _spawn(command)
    except OSError:
        _say(f"{shown} could not be started")
        return EXIT_NOT_STARTED
    _say(f"{shown} exit code {code}")
    return code


if __name__ == "__main__":
    sys.exit(main())
