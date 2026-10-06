"""Proof for the PreToolUse gate on proofs run by hand outside ``cairn test`` (1af0564c0db3).

WHAT IT PROVES, and the reason is a measured leak, not a design idea: on 2026-10-06 the census
ran every proof under raw pytest with ``strace -f`` and 88 of 290 wrote into live ~/.cairn
(2705 paths — dated emissions, inference tickets, tester run files, appends to bus.log and
last_known). The same day this session's own ``python3 <proof>`` run of e9a2's proof landed 6
fixture inference tickets in the live log. ``cairn test`` runs a proof inside the tester's
instance seal; a hand that skips it runs against the operator's world. ``bin/cmd/proofgate`` is
the physics (Law 4) for CC's hand; this proof is what keeps it from being a sentence.

Teeth, one per falsifier clause (PROVES below):
  (1) python3 BY PATH IS REFUSED, exit 2, and the refusal names ``cairn test`` — the way through
      on the first pass (a gate that only says no gets routed around). Spellings: the path from
      the repo root, ``cd`` then a relative path, env/timeout/strace prefixes, the module form,
      and a loop whose python runs a variable over a proofs/ glob.
  (2) PYTEST IN ANY SPELLING IS REFUSED — nothing in the repo uses pytest
      (cairn/devices/tester/cli.py), so there is no legitimate pytest run to spare.
  (3) THE BOUND: ``cairn test`` itself, reads of a proof (cat, sed, grep — including a grep FOR
      the word python3 in a proof), and unrelated python all pass. A gate that fires on reads is
      one somebody turns off.
  (4) THE WIRING: .claude/settings.json registers the gate under PreToolUse matcher Bash. An
      unregistered gate refuses nothing.
  (5) THE CENSUS'S OWN COMMANDS ARE REFUSED: every per-proof command the census harness ran
      (``strace -f ... python3 -m pytest -q -x -p no:cacheprovider <proof>``, and its
      ``python3 <proof>`` twin), rebuilt for every proof on disk and typed as a CC Bash command,
      exits 2 before any proof starts. The harness run as a script FILE carries no proof path in
      its text and passes; that population is measured at 0 besides codemother's verdict
      (68cef2ddd8ef), census recorded in this ticket's measured_at_build.

    bin/cairn test bin/proofs/test_proof_gate.py
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import shlex
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_GATE = _REPO_ROOT / "bin" / "cmd" / "proofgate"
_SETTINGS = _REPO_ROOT / ".claude" / "settings.json"

PROVES = {"1af0564c0db3": {
    "1": "test_python3_by_path_is_refused_with_the_way_through",
    "2": "test_pytest_in_any_spelling_is_refused",
    "3": "test_cairn_test_reads_and_other_python_pass",
    "4": "test_settings_register_the_gate_under_pretooluse_bash",
    "5": "test_every_census_command_is_refused_before_a_proof_starts",
}}

_HELD: list = []


def _gate():
    """The subject is an extensionless command, loaded by location as bin/cmd subjects are."""
    assert _GATE.is_file(), f"no gate at {_GATE.relative_to(_REPO_ROOT)}"
    if not _HELD:
        spec = importlib.util.spec_from_loader(
            "proofgate", importlib.machinery.SourceFileLoader("proofgate", str(_GATE)))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _HELD.append(mod)
    return _HELD[0]


def _hook(command: str, tool: str = "Bash") -> subprocess.CompletedProcess:
    """The hook contract as Claude Code drives it: JSON on stdin, exit 2 blocks, stderr fed back."""
    assert _GATE.is_file(), f"no gate at {_GATE.relative_to(_REPO_ROOT)}"
    return subprocess.run([sys.executable, str(_GATE)], capture_output=True, text=True, timeout=30,
                          input=json.dumps({"tool_name": tool, "tool_input": {"command": command}}))


P = "cairn/devices/inference_domain/proofs/test_inference_domain.py"

REFUSED_BY_PATH = [
    f"python3 {P}",
    "cd cairn && python3 devices/inference_domain/proofs/test_inference_domain.py",
    f"PYTHONPATH=. python3 {P}",
    f"PYTHONPATH=$PWD timeout 600 python3 -u {P} 2>&1 | tail -5",
    f"strace -f -o /tmp/x.strace python3 {P}",
    f"/usr/bin/python3 {P}",
    f"{_REPO_ROOT}/.venv/bin/python {_REPO_ROOT}/{P}",
    "python3 -m cairn.devices.inference_domain.proofs.test_inference_domain",
    "for p in cairn/devices/inference_domain/proofs/test_*.py; do python3 \"$p\"; done",
    f"git status; python3 {P}",
]

REFUSED_PYTEST = [
    "pytest cairn/tools/base/proofs/",
    "python3 -m pytest -q x.py",
    "py.test -x bin/proofs/test_delete_gate.py",
    f"PYTHONPATH=. pytest -q {P}",
    "python -m pytest",
]

ALLOWED = [
    f"bin/cairn test --seal {P}",
    f"{_REPO_ROOT}/bin/cairn test --hollow 1af0564c0db3",
    f"cairn test -q {P}",
    f"cat {P}",
    f"sed -n 1,40p {P}",
    f"grep -n python3 {P}",
    "python3 -c 'print(1)'",
    "python3 -m skills.chart.live counsel 'x'",
    "PYTHONPATH=$PWD python3 skills/sorted/door.py /tmp/packet.json",
    "git log --oneline -3",
]


def test_python3_by_path_is_refused_with_the_way_through():
    g = _gate()
    leaked = [c for c in REFUSED_BY_PATH if g.verdict(c) is None]
    assert not leaked, f"raw proof runs the gate allowed: {leaked}"
    for c in REFUSED_BY_PATH[:2]:
        r = _hook(c)
        assert r.returncode == 2, f"hook exit {r.returncode} for {c!r}"
        assert "cairn test" in r.stderr, f"the refusal must name `cairn test`: {r.stderr[:300]!r}"


def test_pytest_in_any_spelling_is_refused():
    g = _gate()
    leaked = [c for c in REFUSED_PYTEST if g.verdict(c) is None]
    assert not leaked, f"pytest spellings the gate allowed: {leaked}"
    r = _hook(REFUSED_PYTEST[1])
    assert r.returncode == 2 and "cairn test" in r.stderr, (r.returncode, r.stderr[:300])


def test_cairn_test_reads_and_other_python_pass():
    g = _gate()
    refused = [c for c in ALLOWED if g.verdict(c) is not None]
    assert not refused, f"the gate refused commands outside its bound: {refused}"
    for c in ALLOWED[:1] + ALLOWED[3:4]:
        r = _hook(c)
        assert r.returncode == 0, f"hook exit {r.returncode} for allowed {c!r}: {r.stderr[:200]}"
    r = _hook(f"python3 {P}", tool="Read")
    assert r.returncode == 0, "a non-Bash tool is not this gate's to judge"


def test_settings_register_the_gate_under_pretooluse_bash():
    hooks = json.loads(_SETTINGS.read_text()).get("hooks", {}).get("PreToolUse", [])
    wired = [h for e in hooks if "Bash" in e.get("matcher", "").split("|")
             for h in e.get("hooks", []) if h.get("command", "").endswith("bin/cmd/proofgate")]
    assert wired, "no PreToolUse Bash entry runs bin/cmd/proofgate in .claude/settings.json"


def _proofs_on_disk() -> list[str]:
    out = subprocess.run(["git", "-C", str(_REPO_ROOT), "ls-files", "*/proofs/test_*.py",
                          "*/proofs/*/test_*.py"], capture_output=True, text=True, timeout=60).stdout
    return [p for p in out.splitlines() if p]


def test_every_census_command_is_refused_before_a_proof_starts():
    g = _gate()
    proofs = _proofs_on_disk()
    assert len(proofs) > 100, f"the census population is the corpus; found {len(proofs)}"
    trace = ["strace", "-f", "-qq", "-e", "trace=open,openat,creat,rename,renameat,renameat2,mkdir,mkdirat",
             "-o", "/tmp/census.strace"]
    commands = [shlex.join(trace + [sys.executable, "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider", p])
                for p in proofs] + [shlex.join(trace + [sys.executable, p]) for p in proofs]
    leaked = [c for c in commands if g.verdict(c) is None]
    assert not leaked, f"{len(leaked)} of {len(commands)} census commands allowed, e.g. {leaked[:2]}"
    r = _hook(commands[0])
    assert r.returncode == 2, f"hook exit {r.returncode}: the census command ran"


def test_the_whole_falsifier_holds_end_to_end():
    test_python3_by_path_is_refused_with_the_way_through()
    test_pytest_in_any_spelling_is_refused()
    test_cairn_test_reads_and_other_python_pass()
    test_settings_register_the_gate_under_pretooluse_bash()
    test_every_census_command_is_refused_before_a_proof_starts()


def _main() -> int:
    checks = [
        test_python3_by_path_is_refused_with_the_way_through,
        test_pytest_in_any_spelling_is_refused,
        test_cairn_test_reads_and_other_python_pass,
        test_settings_register_the_gate_under_pretooluse_bash,
        test_every_census_command_is_refused_before_a_proof_starts,
        test_the_whole_falsifier_holds_end_to_end,
    ]
    # EVERY TOOTH PRINTS, red ones too, so a red names which clause fell.
    failed = []
    for check in checks:
        try:
            check()
            print(f"  PASS  {check.__name__}")
        except AssertionError as e:
            failed.append(check.__name__)
            print(f"  FAIL  {check.__name__}: {e}")
    if failed:
        print(f"red — {len(failed)} of {len(checks)} teeth failed")
        return 1
    print("green — proofgate: a proof run by hand outside cairn test is refused at PreToolUse, with the way through")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
