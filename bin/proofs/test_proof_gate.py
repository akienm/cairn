"""Proof for the PreToolUse gate on proofs run by hand outside ``cairn test`` (1af0564c0db3).

WHAT IT PROVES, and the reason is a measured leak, not a design idea: on 2026-10-06 the census
ran every proof under raw pytest with ``strace -f`` and 88 of 290 wrote into live ~/.cairn
(2705 paths — dated emissions, inference tickets, tester run files, appends to bus.log and
last_known). The same day this session's own ``python3 <proof>`` run of e9a2's proof landed 6
fixture inference tickets in the live log. ``cairn test`` runs a proof inside the tester's
instance seal; a hand that skips it runs against the operator's world. ``bin/cmd/proofgate`` is
the physics (Law 4) for CC's hand. It REWRITES rather than refuses the python3 hand, because 313
files of standing advice say ``python3 <proof>``: a refusal would leave all of them contradicting
the gate and cost a turn per follower, while a rewrite keeps them true in effect.

Teeth, one per falsifier clause (PROVES below):
  (1) python3 BY PATH IS REWRITTEN: exit 0, permissionDecision allow, updatedInput.command is
      ``<repo>/bin/cairn test --exec `` + shlex.quote(original), and the session is told. Spellings:
      the path from the repo root, ``cd`` then a relative path, env/timeout/strace prefixes, the
      module form, and a loop whose python runs a variable over a proofs/ glob.
  (2) PYTEST IN ANY SPELLING IS REFUSED, exit 2, naming ``cairn test`` — there is no sealed
      pytest, and nothing in the repo uses pytest (cairn/devices/tester/cli.py).
  (3) THE BOUND: ``cairn test`` itself, reads of a proof (cat, sed, grep — including a grep FOR the
      word python3 in a proof), and unrelated python exit 0 with no output.
  (4) THE WIRING: .claude/settings.json registers the gate under PreToolUse matcher Bash.
  (5) THE CENSUS'S OWN COMMANDS: every per-proof command the census harness ran (``strace -f ...
      python3 -m pytest ... <proof>`` and its ``python3 <proof>`` twin), rebuilt for every proof on
      disk, is refused or rewritten — never passed bare.
  (6) THE REWRITE LANDS UNDER THE SEAL: a fixture proof that prints CAIRN_TESTER_INSTANCE_SEALED,
      run through the rewritten command, prints 1. The docs say updatedInput replaces the input;
      this measures what the rewritten command does, not what the docs say.
  (7) QUOTING: a rewritten command carrying single quotes, double quotes and a pipe prints the
      same stdout as the bare command it replaced.

The harness run as a script FILE carries no proof path in its text and passes; that population
was measured at 0 executors besides codemother's verdict (68cef2ddd8ef), census recorded in this
ticket's measured_at_build.

    bin/cairn test bin/proofs/test_proof_gate.py
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_GATE = _REPO_ROOT / "bin" / "cmd" / "proofgate"
_SETTINGS = _REPO_ROOT / ".claude" / "settings.json"

PROVES = {"1af0564c0db3": {
    "1": "test_python3_by_path_is_rewritten_under_the_seal",
    "2": "test_pytest_in_any_spelling_is_refused_with_the_way_through",
    "3": "test_cairn_test_reads_and_other_python_pass_untouched",
    "4": "test_settings_register_the_gate_under_pretooluse_bash",
    "5": "test_every_census_command_is_refused_or_rewritten_never_bare",
    "6": "test_a_rewritten_proof_runs_under_the_instance_seal",
    "7": "test_quotes_and_pipes_survive_the_rewrite",
}, "72a37498c601": {
    "1": "test_the_word_as_an_argument_passes_untouched",
    "2": "test_pytest_as_a_command_word_is_still_refused",
    "3": "test_a_separator_inside_an_assignment_hides_no_proof_run",
    "4": "test_a_wrapped_command_is_judged_as_the_command_it_is",
    "5": "test_cairn_test_seals_only_its_own_segment",
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
    """The hook contract as Claude Code drives it: JSON on stdin; exit 2 blocks with stderr fed
    back; exit 0 with a hookSpecificOutput object on stdout allows, possibly with updatedInput."""
    assert _GATE.is_file(), f"no gate at {_GATE.relative_to(_REPO_ROOT)}"
    return subprocess.run([sys.executable, str(_GATE)], capture_output=True, text=True, timeout=30,
                          input=json.dumps({"tool_name": tool, "tool_input": {"command": command}}))


def _wrapped(command: str) -> str:
    return f"{_REPO_ROOT}/bin/cairn test --exec {shlex.quote(command)}"


def _rewritten(command: str) -> str:
    """Drive the hook; assert the rewrite contract; return the command Claude Code would run."""
    r = _hook(command)
    assert r.returncode == 0, f"hook exit {r.returncode} for {command!r}: {r.stderr[:300]}"
    try:
        out = json.loads(r.stdout)["hookSpecificOutput"]
    except (ValueError, KeyError, TypeError):
        raise AssertionError(f"no hookSpecificOutput on stdout for {command!r}: {r.stdout[:300]!r}")
    assert out.get("hookEventName") == "PreToolUse", out
    assert out.get("permissionDecision") == "allow", out
    told = (out.get("permissionDecisionReason", "") + out.get("additionalContext", "")).lower()
    assert "rewr" in told, f"the session must be told the command was rewritten: {out}"
    return out.get("updatedInput", {}).get("command", "")


P = "cairn/devices/inference_domain/proofs/test_inference_domain.py"

BY_PATH = [
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
    f"python3 {P} | PYTHONPATH=. python3 -c \"import sys; print('test_x' in sys.stdin.read())\"",
]

PYTEST = [
    "pytest cairn/tools/base/proofs/",
    "python3 -m pytest -q x.py",
    "py.test -x bin/proofs/test_delete_gate.py",
    f"PYTHONPATH=. pytest -q {P}",
    "python -m pytest",
    f"python3 {P}; pytest {P}",
]

UNTOUCHED = [
    f"bin/cairn test --seal {P}",
    f"{_REPO_ROOT}/bin/cairn test --hollow 1af0564c0db3",
    f"cairn test -q {P}",
    _wrapped(f"python3 {P} | grep 'PASS'"),
    f"cat {P}",
    f"sed -n 1,40p {P}",
    f"grep -n python3 {P}",
    "python3 -c 'print(1)'",
    "python3 -m skills.chart.live counsel 'x'",
    "PYTHONPATH=$PWD python3 skills/sorted/door.py /tmp/packet.json",
    "git log --oneline -3",
]


def test_python3_by_path_is_rewritten_under_the_seal():
    g = _gate()
    wrong = [c for c in BY_PATH if (g.judge(c) or {}).get("command") != _wrapped(c)]
    assert not wrong, f"python3 proof runs not rewritten to the sealed exec: {wrong}"
    for c in BY_PATH[:2] + BY_PATH[-1:]:
        got = _rewritten(c)
        assert got == _wrapped(c), f"updatedInput {got!r} != {_wrapped(c)!r}"


def test_pytest_in_any_spelling_is_refused_with_the_way_through():
    g = _gate()
    leaked = [c for c in PYTEST if (g.judge(c) or {}).get("action") != "refuse"]
    assert not leaked, f"pytest spellings not refused: {leaked}"
    for c in PYTEST[:2]:
        r = _hook(c)
        assert r.returncode == 2, f"hook exit {r.returncode} for {c!r}"
        assert "cairn test" in r.stderr, f"the refusal must name `cairn test`: {r.stderr[:300]!r}"


def test_cairn_test_reads_and_other_python_pass_untouched():
    g = _gate()
    judged = [c for c in UNTOUCHED if g.judge(c) is not None]
    assert not judged, f"the gate touched commands outside its bound: {judged}"
    for c in UNTOUCHED[:1] + UNTOUCHED[3:5]:
        r = _hook(c)
        assert r.returncode == 0 and not r.stdout.strip(), \
            f"allowed {c!r} must pass silently: exit {r.returncode}, stdout {r.stdout[:200]!r}"
    r = _hook(f"python3 {P}", tool="Read")
    assert r.returncode == 0 and not r.stdout.strip(), "a non-Bash tool is not this gate's to judge"


def test_settings_register_the_gate_under_pretooluse_bash():
    hooks = json.loads(_SETTINGS.read_text()).get("hooks", {}).get("PreToolUse", [])
    wired = [h for e in hooks if "Bash" in e.get("matcher", "").split("|")
             for h in e.get("hooks", []) if h.get("command", "").endswith("bin/cmd/proofgate")]
    assert wired, "no PreToolUse Bash entry runs bin/cmd/proofgate in .claude/settings.json"


def _proofs_on_disk() -> list[str]:
    out = subprocess.run(["git", "-C", str(_REPO_ROOT), "ls-files", "*/proofs/test_*.py",
                          "*/proofs/*/test_*.py"], capture_output=True, text=True, timeout=60).stdout
    return [p for p in out.splitlines() if p]


def test_every_census_command_is_refused_or_rewritten_never_bare():
    g = _gate()
    proofs = _proofs_on_disk()
    assert len(proofs) > 100, f"the census population is the corpus; found {len(proofs)}"
    trace = ["strace", "-f", "-qq", "-e", "trace=open,openat,creat,rename,renameat,renameat2,mkdir,mkdirat",
             "-o", "/tmp/census.strace"]
    pytest_cmds = [shlex.join(trace + [sys.executable, "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider", p])
                   for p in proofs]
    python_cmds = [shlex.join(trace + [sys.executable, p]) for p in proofs]
    bare = [c for c in pytest_cmds if (g.judge(c) or {}).get("action") != "refuse"]
    bare += [c for c in python_cmds if (g.judge(c) or {}).get("command") != _wrapped(c)]
    assert not bare, f"{len(bare)} of {len(pytest_cmds) + len(python_cmds)} census commands would run bare, e.g. {bare[:2]}"


_FIXTURE: list = []


def _fixture_proofs() -> Path:
    """Two fixture proofs in a proofs/ directory outside the repo, named so a leak explains itself."""
    if not _FIXTURE:
        d = Path(tempfile.mkdtemp(prefix="proofgate_fixture_proof_")) / "proofs"
        d.mkdir()
        (d / "test_prints_the_seal_marker.py").write_text(
            "import os\nprint('sealed=' + os.environ.get('CAIRN_TESTER_INSTANCE_SEALED', 'absent'))\n")
        (d / "test_prints_quotes.py").write_text(
            "print('tooth \\'single\\' \"double\" line-one')\nprint('tooth other line-two')\n")
        _FIXTURE.append(d)
    return _FIXTURE[0]


def _bash(command: str) -> subprocess.CompletedProcess:
    return subprocess.run(["bash", "-c", command], capture_output=True, text=True, timeout=600,
                          cwd=str(_REPO_ROOT))


def test_a_rewritten_proof_runs_under_the_instance_seal():
    c = f"python3 {_fixture_proofs() / 'test_prints_the_seal_marker.py'}"
    r = _bash(_rewritten(c))
    assert r.returncode == 0, f"the rewritten command failed, exit {r.returncode}: {r.stderr[-400:]}"
    assert "sealed=1" in r.stdout, f"the rewritten run was not sealed: {r.stdout[-300:]!r}"


def test_quotes_and_pipes_survive_the_rewrite():
    c = (f"python3 {_fixture_proofs() / 'test_prints_quotes.py'} | grep 'line-one' "
         f"| sed \"s/double/DOUBLE/\"")
    bare, sealed = _bash(c), _bash(_rewritten(c))
    assert bare.returncode == 0 and "DOUBLE" in bare.stdout, f"the fixture itself broke: {bare.stdout!r} {bare.stderr!r}"
    assert sealed.stdout == bare.stdout, f"stdout changed under the rewrite: {sealed.stdout!r} != {bare.stdout!r} ({sealed.stderr[-300:]})"


# 72a37498c601: the 1af0 gate matched the word anywhere in the text. Measured 2026-10-06 — these
# run no pytest and were refused; the live gate blocked every session's echo, grep and commit.
_W = "py" + "test"
AS_ARGUMENT = [
    f'git commit -m "refuses {_W}\n"',
    f"grep -rn {_W} cairn/",
    f"echo {_W}",
    'cat x | grep "py.test "',
]

AS_COMMAND = PYTEST + [
    f"{_W} x.py",
    f"cd a && {_W}",
    f"timeout 60 {_W} cairn/tools/base/proofs/",
]

# D9 on 1af0564c0db3: the split cut inside the quotes, so the python3 segment never began.
IN_ASSIGNMENT = f'X="a;b" python3 {P}'

# The whole-text match refused these; a per-segment walk that stopped at bash would not.
WRAPPED_REFUSED = [f'bash -c "{_W} x.py"', f"sh -c '{_W} -q {P}'", f'eval "{_W} x.py"']
WRAPPED_REWRITTEN = [f'bash -c "python3 {P}"']
WRAPPED_UNTOUCHED = [f'bash -c "echo {_W}"']

# The whole-text `cairn test` match let a bare proof run ride beside the words.
SEALED_BESIDE = [f'echo "cairn test"; python3 {P}', f"bin/cairn test {P}; python3 {P}"]


def test_the_word_as_an_argument_passes_untouched():
    g = _gate()
    judged = [c for c in AS_ARGUMENT if g.judge(c) is not None]
    assert not judged, f"the word as an argument was judged: {judged}"
    for c in AS_ARGUMENT:
        r = _hook(c)
        assert r.returncode == 0 and not r.stdout.strip(), \
            f"{c!r} must pass silently: exit {r.returncode}, stdout {r.stdout[:200]!r}, stderr {r.stderr[:120]!r}"


def test_pytest_as_a_command_word_is_still_refused():
    g = _gate()
    leaked = [c for c in AS_COMMAND if (g.judge(c) or {}).get("action") != "refuse"]
    assert not leaked, f"command-word spellings not refused: {leaked}"
    for c in AS_COMMAND[-3:]:
        r = _hook(c)
        assert r.returncode == 2 and "cairn test" in r.stderr, f"hook exit {r.returncode} for {c!r}: {r.stderr[:200]!r}"


def test_a_separator_inside_an_assignment_hides_no_proof_run():
    g = _gate()
    got = (g.judge(IN_ASSIGNMENT) or {}).get("command")
    assert got == _wrapped(IN_ASSIGNMENT), f"{IN_ASSIGNMENT!r} judged {got!r}, not the sealed exec"
    assert _rewritten(IN_ASSIGNMENT) == _wrapped(IN_ASSIGNMENT)


def test_a_wrapped_command_is_judged_as_the_command_it_is():
    g = _gate()
    leaked = [c for c in WRAPPED_REFUSED if (g.judge(c) or {}).get("action") != "refuse"]
    assert not leaked, f"wrapped spellings not refused: {leaked}"
    bare = [c for c in WRAPPED_REWRITTEN if (g.judge(c) or {}).get("command") != _wrapped(c)]
    assert not bare, f"wrapped proof runs not rewritten: {bare}"
    judged = [c for c in WRAPPED_UNTOUCHED if g.judge(c) is not None]
    assert not judged, f"a wrapped argument was judged: {judged}"


def test_cairn_test_seals_only_its_own_segment():
    g = _gate()
    bare = [c for c in SEALED_BESIDE if (g.judge(c) or {}).get("command") != _wrapped(c)]
    assert not bare, f"a proof run beside `cairn test` passed bare: {bare}"
    assert _rewritten(SEALED_BESIDE[0]) == _wrapped(SEALED_BESIDE[0])
    once = _wrapped(SEALED_BESIDE[0])
    assert g.judge(once) is None, f"a rewritten command must not rewrite again: {g.judge(once)}"


def test_the_whole_fix_holds_end_to_end():
    test_the_word_as_an_argument_passes_untouched()
    test_pytest_as_a_command_word_is_still_refused()
    test_a_separator_inside_an_assignment_hides_no_proof_run()
    test_a_wrapped_command_is_judged_as_the_command_it_is()
    test_cairn_test_seals_only_its_own_segment()


def test_the_whole_falsifier_holds_end_to_end():
    test_python3_by_path_is_rewritten_under_the_seal()
    test_pytest_in_any_spelling_is_refused_with_the_way_through()
    test_cairn_test_reads_and_other_python_pass_untouched()
    test_settings_register_the_gate_under_pretooluse_bash()
    test_every_census_command_is_refused_or_rewritten_never_bare()
    test_a_rewritten_proof_runs_under_the_instance_seal()
    test_quotes_and_pipes_survive_the_rewrite()


def _main() -> int:
    checks = [
        test_python3_by_path_is_rewritten_under_the_seal,
        test_pytest_in_any_spelling_is_refused_with_the_way_through,
        test_cairn_test_reads_and_other_python_pass_untouched,
        test_settings_register_the_gate_under_pretooluse_bash,
        test_every_census_command_is_refused_or_rewritten_never_bare,
        test_a_rewritten_proof_runs_under_the_instance_seal,
        test_quotes_and_pipes_survive_the_rewrite,
        test_the_whole_falsifier_holds_end_to_end,
        test_the_word_as_an_argument_passes_untouched,
        test_pytest_as_a_command_word_is_still_refused,
        test_a_separator_inside_an_assignment_hides_no_proof_run,
        test_a_wrapped_command_is_judged_as_the_command_it_is,
        test_cairn_test_seals_only_its_own_segment,
        test_the_whole_fix_holds_end_to_end,
    ]
    # EVERY TOOTH PRINTS, red ones too, so a red names which clause fell.
    failed = []
    try:
        for check in checks:
            try:
                check()
                print(f"  PASS  {check.__name__}")
            except AssertionError as e:
                failed.append(check.__name__)
                print(f"  FAIL  {check.__name__}: {e}")
    finally:
        import shutil
        for d in _FIXTURE:
            shutil.rmtree(d.parent, ignore_errors=True)
    if failed:
        print(f"red — {len(failed)} of {len(checks)} teeth failed")
        return 1
    print("green — proofgate: a python3 proof run by hand runs under the seal, pytest is refused with the way through")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
