"""Proof for logger_for_bash — the flight recorder for bash.

Every tooth below kills a defect that was MEASURED in the original (akientools, 2024) or
that this rewrite could plausibly reintroduce. Written defect-first, because the original
was not wrong in design — it was wrong in four specific, invisible ways, and a proof that
did not name them would let the rewrite inherit them.

Teeth a hollow logger could not pass:

  - THE CODE IS THE COMMAND'S. ``logrun false`` records ``= 1`` and RETURNS 1. The
    original piped into tee and read ``$?``, so it recorded tee's code — always 0. A log
    that reports success for everything is worse than no log, because it is believed.
  - STDERR REACHES THE FILE. The original piped stdout only; the failure text you most
    want at 3am hit the terminal and missed the record.
  - THE RECORD KEEPS ARGUMENT BOUNDARIES. ``logrun printf ... 'one two' three`` records a
    line you can paste back and re-run. Caught mid-build: running "$@" fixes execution and
    leaves the RECORD wrong if it is rendered with $*.
  - SOURCING NEVER TRUNCATES. The original's last line was ``echo "" > "$logtarget"`` —
    sourced from .bashrc that wiped the log in every new terminal, which is the exact
    inverse of the retention this tool exists to provide.
  - TRIM KEEPS THE TAIL. Cutting to N must keep the NEWEST N. Keeping the oldest N would
    look identical by line count and be exactly backwards.
  - SOURCING SETS NO ``set -e``/``-u``. It is sourced by ~/.bashrc and by superclaude,
    whose prime directive is that nothing may abort the launch. A leaked ``set -e`` turns
    a logging tool into a way to lose your shell.
  - THE FUNCTIONS SURVIVE ``export -f``. ``export logcmd`` (the original) is a silent
    no-op; no child ever saw it.
  - A DEAD LOG DIRECTORY DOES NOT KILL THE CALLER. If it cannot write, it says so once
    and returns — it never takes down the script it was hired to observe.

Non-vacuity: ``test_the_original_defects_are_real`` runs the ORIGINAL against the same
fixtures and asserts it FAILS them. If that case ever passes, these teeth are measuring
nothing and the whole file is theatre.

    python3 bin/proofs/test_logger_for_bash.py     # exit 0 = green
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

# This proof is documented as runnable bare (see the header), so it cannot lean on an
# externally-set PYTHONPATH to reach cairn.*. bin/proofs -> the repo root.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from cairn.tester.scratch import scratch_dir  # noqa: E402

_LOGGER = Path(__file__).resolve().parents[1] / "logger_for_bash"   # bin/proofs -> bin
_ORIGINAL = Path.home() / "dev/src/akientools/bin/logger_for_bash"  # the graft's source


def _bash(script: str, *, logger: Path | None = None, env: dict | None = None,
          cwd: str | None = None) -> subprocess.CompletedProcess:
    """Run a bash snippet with the logger sourced. Nothing inherits the caller's logtarget."""
    src = logger if logger is not None else _LOGGER
    base = {k: v for k, v in os.environ.items()
            if k not in ("CAIRN_LOGTARGET", "logtarget", "CAIRN_LOGLEN", "loglen")}
    # The trace wire fires once per sourced shell; a proof shell is not a real firing,
    # so its records go to a scratch berth — the live denominator stays honest.
    base["CAIRN_LB_TRACE_ROOT"] = str(scratch_dir("lfb-proof-traces-"))
    base["PYTHONPATH"] = str(_LOGGER.parents[1])
    full = f'source "{src}"\n{script}\n'
    return subprocess.run(["bash", "-c", full], capture_output=True, text=True,
                          env={**base, **(env or {})}, cwd=cwd)


def _log(d: str) -> str:
    return os.path.join(d, "bash")


def _read(path: str) -> str:
    return Path(path).read_text() if os.path.exists(path) else ""


# ── the four measured defects ────────────────────────────────────────────────

def test_the_recorded_code_is_the_commands_not_the_pipes():
    with tempfile.TemporaryDirectory() as d:
        t = _log(d)
        r = _bash('logrun false; echo "RET=$?"', env={"CAIRN_LOGTARGET": t})
        body = _read(t)
        assert "= 1" in body, f"`false` must record its own code 1, not the pipe's 0:\n{body}"
        assert "= 0" not in body, f"a 0 leaked into the record for a failing command:\n{body}"
        assert "RET=1" in r.stdout, (
            f"logrun must RETURN the command's code so `logrun x || repair` works: {r.stdout!r}")


def test_stderr_lands_in_the_file():
    with tempfile.TemporaryDirectory() as d:
        t = _log(d)
        _bash('logrun ls /no-such-path-9f3a >/dev/null 2>&1', env={"CAIRN_LOGTARGET": t})
        body = _read(t)
        assert "No such file" in body or "cannot access" in body, (
            f"stderr must reach the RECORD, not just the terminal:\n{body}")
        assert "= 2" in body, f"ls's real exit code (2) must be recorded:\n{body}"


def test_the_record_keeps_argument_boundaries():
    with tempfile.TemporaryDirectory() as d:
        t = _log(d)
        _bash("""logrun printf '[%s]\\n' 'one two' three >/dev/null""",
              env={"CAIRN_LOGTARGET": t})
        body = _read(t)
        cmd = [ln for ln in body.splitlines() if "$ " in ln]
        assert cmd, f"no command line was recorded at all:\n{body}"
        line = cmd[0]
        # `one two` must survive as ONE argument — as quotes or as an escaped space.
        assert ("'one two'" in line or "one\\ two" in line or '"one two"' in line), (
            f"argument boundaries were flattened; this line cannot be re-run: {line!r}")
        # and the execution itself kept them: two printf invocations, not three
        assert "[one two]" in body, f"the command did not run with argv intact:\n{body}"


def test_the_functions_survive_export_to_a_child():
    with tempfile.TemporaryDirectory() as d:
        r = _bash('export -f logrun lognote _logbash_write _logbash_stamp logtarget_path\n'
                  'bash -c \'declare -F logrun >/dev/null && echo SEEN || echo BLIND\'',
                  env={"CAIRN_LOGTARGET": _log(d)})
        assert "SEEN" in r.stdout, (
            f"a child shell could not see the exported functions: {r.stdout!r} {r.stderr!r}")


def test_sourcing_never_truncates_the_record():
    with tempfile.TemporaryDirectory() as d:
        t = _log(d)
        r = _bash(f'lognote first\nlognote second\n'
                  f'source "{_LOGGER}"\nsource "{_LOGGER}"\n'
                  f'wc -l < "{t}"', env={"CAIRN_LOGTARGET": t})
        body = _read(t)
        assert "first" in body and "second" in body, (
            f"re-sourcing destroyed the record — the .bashrc-wipe defect:\n{body}")
        assert r.stdout.strip().endswith("2"), f"line count changed across sources: {r.stdout!r}"


# ── properties this rewrite must not get backwards ───────────────────────────

def test_trim_keeps_the_newest_lines():
    with tempfile.TemporaryDirectory() as d:
        t = _log(d)
        _bash('for i in $(seq 1 200); do lognote "entry-$i"; done; logtrim',
              env={"CAIRN_LOGTARGET": t, "CAIRN_LOGLEN": "10"})
        lines = _read(t).strip().splitlines()
        assert len(lines) == 10, f"expected exactly 10 lines after trim, got {len(lines)}"
        # The window is the newest 10 LINES, one of which is trim's own mark (written before
        # the cut, so it is the newest thing in the file). What must hold is that the cut
        # came off the OLD end: the last entries survive, the first ones are gone.
        entries = [ln for ln in lines if "entry-" in ln]
        assert "entry-200" in entries[-1], f"the NEWEST entry was cut: {entries[-1]!r}"
        assert "entry-192" in entries[0], f"trim kept the wrong window: {entries[0]!r}"
        assert "entry-1:" not in _read(t) and "entry-1 " not in _read(t), (
            "an oldest-N trim would look identical by line count — the direction is the property")


def test_the_line_cap_actually_bounds_the_file():
    """Amortised trim may drift over the cap, but it must never drift without bound."""
    with tempfile.TemporaryDirectory() as d:
        t = _log(d)
        # 150 runs write 300 lines against a cap of 20 — a 15x overshoot, which is plenty
        # to catch a cap that never fires, and cheap enough that nobody skips this proof.
        _bash('for i in $(seq 1 150); do logrun true >/dev/null 2>&1; done',
              env={"CAIRN_LOGTARGET": t, "CAIRN_LOGLEN": "20"})
        n = len(_read(t).strip().splitlines())
        assert n <= 30, f"300 written lines left {n} on disk — the cap is not holding"
        assert n >= 10, f"only {n} lines survived — the cap is over-cutting"


def test_sourcing_leaks_no_errexit_or_nounset():
    """Sourced by .bashrc and by superclaude: a leaked `set -e` costs the user a shell."""
    r = _bash('case "$-" in *e*) echo LEAKED_E ;; esac\n'
              'case "$-" in *u*) echo LEAKED_U ;; esac\n'
              'false\necho SURVIVED_A_FAILURE\n'
              'echo "unset=[${THIS_IS_NOT_SET:-}]"\necho DONE')
    assert "LEAKED_E" not in r.stdout, "sourcing turned on errexit in the caller's shell"
    assert "LEAKED_U" not in r.stdout, "sourcing turned on nounset in the caller's shell"
    assert "SURVIVED_A_FAILURE" in r.stdout, "a failing command aborted the sourcing shell"
    assert "DONE" in r.stdout, f"the shell did not survive to the end: {r.stdout!r}"
    assert r.returncode == 0


def test_sourcing_is_silent():
    """A logger that greets you in every new terminal gets commented out of .bashrc."""
    with tempfile.TemporaryDirectory() as d:
        r = _bash('true', env={"CAIRN_LOGTARGET": _log(d)})
        assert r.stdout == "", f"sourcing printed to stdout: {r.stdout!r}"
        assert r.stderr == "", f"sourcing printed to stderr: {r.stderr!r}"


def test_an_unwritable_target_warns_once_and_does_not_kill_the_caller():
    r = _bash('logrun echo hello >/dev/null 2>/dev/null\n'
              'lognote a 2>/dev/null; lognote b 2>/dev/null\n'
              'echo CALLER_SURVIVED',
              env={"CAIRN_LOGTARGET": "/proc/cairn-no-such-dir/bash"})
    assert "CALLER_SURVIVED" in r.stdout, (
        f"an unwritable log took the caller down with it: {r.stdout!r} / {r.stderr!r}")
    assert r.returncode == 0


def test_an_unwritable_target_still_says_so():
    """CP1: it may fail, it may not fail SILENTLY."""
    r = _bash('lognote a\nlognote b\nlognote c\ntrue',
              env={"CAIRN_LOGTARGET": "/proc/cairn-no-such-dir/bash"})
    assert "cannot append" in r.stderr, f"failed silently: {r.stderr!r}"
    assert r.stderr.count("cannot append") == 1, (
        f"warned {r.stderr.count('cannot append')} times — noise on every line is how a "
        f"warning gets ignored: {r.stderr!r}")


def test_every_line_carries_its_pid_so_concurrent_shells_stay_separable():
    with tempfile.TemporaryDirectory() as d:
        t = _log(d)
        _bash('logrun printf "a\\nb\\nc\\n" >/dev/null', env={"CAIRN_LOGTARGET": t})
        lines = [ln for ln in _read(t).splitlines() if ln.strip()]
        assert lines, "nothing was written"
        pids = set()
        for ln in lines:
            head = ln.split(":", 1)[0]
            parts = head.split(".")
            assert len(parts) == 4, f"line is not <date>.<time>.<usec>.<pid>: {ln!r}"
            assert parts[0].isdigit() and len(parts[0]) == 8, f"bad date field: {ln!r}"
            assert parts[2].isdigit(), f"microseconds missing — locale radix bug?: {ln!r}"
            pids.add(parts[3])
        assert len(pids) == 1, f"one shell wrote more than one pid: {pids}"


def test_a_trim_leaves_evidence_that_it_trimmed():
    """The WATCHME probe: a discarded record must not vanish without a trace.

    A retention window is only ever discovered to be wrong in hindsight — someone reaches
    for a boot the file no longer holds. That is measurable only if the discard itself left
    a mark, so each trim records how much it dropped and where the surviving window starts.
    """
    with tempfile.TemporaryDirectory() as d:
        t = _log(d)
        _bash('for i in $(seq 1 200); do lognote "entry-$i"; done; logtrim',
              env={"CAIRN_LOGTARGET": t, "CAIRN_LOGLEN": "10"})
        body = _read(t)
        marks = [ln for ln in body.splitlines() if "logtrim:" in ln]
        assert marks, f"a trim discarded records silently — the window is unmeasurable:\n{body}"
        assert "discarded" in marks[-1] and "window now starts at" in marks[-1], (
            f"the trim mark does not carry what was lost: {marks[-1]!r}")


def test_a_multiline_message_is_still_one_record():
    """The invariant is per-RECORD, so it has to survive a message carrying captured output.

    Caught while wiring the boot probe: superclaude logged an exec line whose argv held a
    multi-line preflight report, and every line after the first landed unstamped — no pid to
    attribute it to, and invisible to a cap that counts lines. The single-line cases above
    all passed while this was broken, which is what makes it worth its own tooth.
    """
    with tempfile.TemporaryDirectory() as d:
        t = _log(d)
        # $'...' (ANSI-C quoting), NOT "$(printf '\n')". Command substitution STRIPS trailing
        # newlines, so the obvious spelling produced 'headmiddletail' — a single-line fixture
        # that never reached the code under test, and the case passed with the fix deleted.
        # The FIXTURE_LINES probe below exists so that can never go unnoticed again: it fails
        # loudly if the input stopped being multi-line, instead of quietly measuring nothing.
        r = _bash("""msg=$'head\\nmiddle\\ntail'\n"""
                  """echo "FIXTURE_LINES=$(printf '%s' "$msg" | wc -l)" >&2\n"""
                  """lognote "$msg" """, env={"CAIRN_LOGTARGET": t})
        assert "FIXTURE_LINES=2" in r.stderr, (
            f"the fixture is not multi-line, so this case measures nothing: {r.stderr!r}")
        lines = [ln for ln in _read(t).splitlines() if ln.strip()]
        assert len(lines) == 1, f"a 3-line message became {len(lines)} records:\n{_read(t)}"
        assert "head" in lines[0] and "tail" in lines[0], (
            f"collapsing the newlines lost content: {lines[0]!r}")
        for ln in lines:
            assert len(ln.split(":", 1)[0].split(".")) == 4, f"record lost its stamp: {ln!r}"


def test_two_shells_writing_at_once_keep_both_records():
    with tempfile.TemporaryDirectory() as d:
        t = _log(d)
        procs = [subprocess.Popen(
            ["bash", "-c", f'source "{_LOGGER}"; for i in $(seq 1 40); do lognote "s{n}-$i"; done'],
            env={**os.environ, "CAIRN_LOGTARGET": t, "CAIRN_LOGLEN": "100000"},
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) for n in range(4)]
        for p in procs:
            p.wait()
        body = _read(t)
        for n in range(4):
            got = body.count(f"s{n}-")
            assert got == 40, f"shell {n} lost records under concurrency: {got}/40"


def test_a_child_process_renames_the_namespace_without_touching_the_parents():
    """'a new process can set its own log target ... until that process completes.'"""
    with tempfile.TemporaryDirectory() as d:
        parent, child = _log(d), os.path.join(d, "child")
        _bash(f'lognote parent-before\n'
              f'CAIRN_LOGTARGET="{child}" bash -c \'source "{_LOGGER}"; lognote child-only\'\n'
              f'lognote parent-after', env={"CAIRN_LOGTARGET": parent})
        p, c = _read(parent), _read(child)
        assert "parent-before" in p and "parent-after" in p, f"parent lost its own lines:\n{p}"
        assert "child-only" not in p, f"the child's namespace leaked into the parent:\n{p}"
        assert "child-only" in c, f"the child did not write its own namespace:\n{c}"
        assert "parent-" not in c, f"the parent's lines leaked into the child:\n{c}"


def test_the_install_is_idempotent_and_reversible():
    with tempfile.TemporaryDirectory() as d:
        rc = os.path.join(d, "bashrc")
        Path(rc).write_text("# hand-tuned for a decade\nexport PATH=/opt/bin:$PATH\n")
        r = _bash(f'cairn_logger_install "{rc}"; cairn_logger_install "{rc}"; '
                  f'cairn_logger_installed "{rc}" && echo INSTALLED',
                  env={"CAIRN_LOGTARGET": _log(d)})
        body = Path(rc).read_text()
        assert "INSTALLED" in r.stdout, f"install did not report itself installed: {r.stdout!r}"
        assert body.count("cairn logger_for_bash >>>") == 1, (
            f"a second install duplicated the block:\n{body}")
        assert "hand-tuned for a decade" in body, "the install ate the user's own content"
        assert os.path.exists(rc + ".pre-cairn-logger"), "no backup was taken before editing"
        _bash(f'cairn_logger_uninstall "{rc}"', env={"CAIRN_LOGTARGET": _log(d)})
        after = Path(rc).read_text()
        assert "cairn logger_for_bash" not in after, f"uninstall left residue:\n{after}"
        assert "hand-tuned for a decade" in after, "uninstall ate the user's own content"


# ── non-vacuity: the defects are real, and this file measures them ───────────

def test_the_original_defects_are_real():
    """Run the ORIGINAL against these fixtures. If it passes them, these teeth are theatre.

    This is the case that keeps the rest honest. A rewrite is only justified by defects
    that exist; asserting the new build is correct proves nothing unless the old one is
    demonstrably not. Skips honestly if the graft source is not on this box (CP1 — an
    unmeasurable claim is INDETERMINATE, never a quiet green).
    """
    if not _ORIGINAL.exists():
        print(f"  SKIP  {test_the_original_defects_are_real.__name__} "
              f"— graft source absent at {_ORIGINAL} (INDETERMINATE, not green)")
        return
    with tempfile.TemporaryDirectory() as d:
        t = _log(d)
        # The original has no default target and truncates on source; give it what it wants.
        _bash('logcmd false >/dev/null 2>&1', logger=_ORIGINAL, env={"logtarget": t})
        body = _read(t)
        assert "result_code=0" in body, (
            "the original was expected to record tee's 0 for `false` and did not — "
            "either it was fixed upstream or this fixture no longer exercises it; "
            f"re-measure before trusting the rewrite's teeth:\n{body}")

        _bash('logcmd ls /no-such-path-9f3a >/dev/null 2>&1', logger=_ORIGINAL,
              env={"logtarget": t})
        body = _read(t)
        assert "No such file" not in body, (
            f"the original was expected to drop stderr from the record and did not:\n{body}")

        # and the truncate-on-source defect
        pre = os.path.join(d, "pre")
        _bash(f'logecho keepme', logger=_ORIGINAL, env={"logtarget": pre})
        assert "keepme" in _read(pre)
        _bash('true', logger=_ORIGINAL, env={"logtarget": pre})
        assert "keepme" not in _read(pre), (
            "the original was expected to wipe its log on source and did not")


# ── the attached tier: an interactive shell records only what IT ran ──────────

def _interactive(script: str, *, logdir: str, histfile: str | None = None) -> None:
    """Drive a REAL interactive shell — ``bash -i`` with commands on stdin — because
    PROMPT_COMMAND is the whole mechanism and ``bash -c`` never prints a prompt. Proving the
    attached tier with -c would prove nothing at all, which is how a hook gets a green test
    and still does not fire."""
    base = {k: v for k, v in os.environ.items()
            if k not in ("CAIRN_LOGTARGET", "logtarget", "CAIRN_LOGLEN", "loglen")}
    rc = Path(logdir) / "rcfile"
    rc.write_text(f'source "{_LOGGER}"\nexport CAIRN_LOGDIR="{logdir}"\nlogbash_attach\n')
    env = {**base, "HISTFILE": histfile or os.path.join(logdir, "history")}
    # --rcfile BEFORE -i: bash requires long options first and answers "--: invalid option"
    # otherwise, exiting 1 and writing no log at all — a silently empty record that reads
    # exactly like "the hook does not fire", which is why the assertions below name the
    # command they expected rather than just asserting non-empty.
    subprocess.run(["bash", "--rcfile", str(rc), "-i"], input=script, text=True,
                   capture_output=True, env=env, timeout=60)


def test_an_attached_shell_records_what_it_ran_with_real_exit_codes():
    with tempfile.TemporaryDirectory() as d:
        _interactive("echo one\nfalse\nexit\n", logdir=d)
        body = _read(os.path.join(d, "bash"))
        assert "$ echo one" in body and "$ false" in body, body
        assert "= 1" in body, f"the failing command's real exit code is missing:\n{body}"


def test_the_first_prompt_does_not_record_the_history_it_inherited():
    """THE FABRICATED OPENING RECORD, pinned. Measured on the first real install, 2026-07-30:
    a fresh login shell wrote `$ nohup plasmashell ...` / `= 0` as its very first entry — the
    last line of ~/.bash_history, a command that shell never ran, with an exit code it never
    produced. Bash prints prompt #1 before anything is typed and HISTFILE is loaded by then,
    so the first PROMPT_COMMAND sees somebody else's command. Seeding at attach time cannot
    fix it: bash reads the rc file BEFORE loading history, so `history 1` is empty there."""
    with tempfile.TemporaryDirectory() as d:
        hist = os.path.join(d, "inherited-history")
        Path(hist).write_text("nohup plasmashell </dev/null >/dev/null 2>&1 &\n")
        _interactive("echo mine\nexit\n", logdir=d, histfile=hist)
        body = _read(os.path.join(d, "bash"))
        assert "plasmashell" not in body, (
            f"the record opens with a command this shell never ran:\n{body}")
        assert "$ echo mine" in body, f"and it lost the real command too:\n{body}"


def test_a_shell_with_no_history_still_records_its_first_command():
    """The other side of the same trade, and the reason priming is keyed on a flag rather
    than on 'the last number is empty': a shell with nothing to inherit has nothing to
    swallow, and skipping its first real command would trade a fabricated record for a
    missing one — the same lie facing the other way."""
    with tempfile.TemporaryDirectory() as d:
        _interactive("echo only-command\nexit\n", logdir=d, histfile="/dev/null")
        body = _read(os.path.join(d, "bash"))
        assert "$ echo only-command" in body, (
            f"a shell with no inherited history lost its first real command:\n{body}")


def test_the_trace_wire_fires_once_per_shell_green_and_red():
    """Deploy pass 2026-08-01: first successful write traces door_pass, an unwritable
    target traces send_back naming the target — once per shell each, backgrounded,
    never fatal. The wire is asynchronous, so the tooth waits for the record."""
    import json
    import time

    def _wait_records(root: str, want: int, timeout: float = 10.0) -> list:
        path = Path(root) / "logger_for_bash.jsonl"
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if path.exists():
                recs = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
                if len(recs) >= want:
                    return recs
            time.sleep(0.1)
        return []

    with tempfile.TemporaryDirectory() as d:
        troot = str(scratch_dir("lfb-wire-green-"))
        r = _bash('lognote one; lognote two; wait',
                  env={"CAIRN_LOGTARGET": _log(d), "CAIRN_LB_TRACE_ROOT": troot})
        assert r.returncode == 0
        recs = _wait_records(troot, 1)
        assert [x["event"] for x in recs] == ["door_pass"], \
            f"two writes, ONE door_pass (grain is the shell, not the line): {recs}"

    troot = str(scratch_dir("lfb-wire-red-"))
    r = _bash('lognote will-fail; lognote again; wait',
              env={"CAIRN_LOGTARGET": "/proc/no-such/impossible",
                   "CAIRN_LB_TRACE_ROOT": troot})
    assert r.returncode == 0, "an unwritable target must still never kill the caller"
    recs = _wait_records(troot, 1)
    assert [x["event"] for x in recs] == ["send_back"], \
        f"the refusal is counted once: {recs}"
    assert "/proc/no-such/impossible" in recs[0]["data"]["lacks"][0], \
        "the send_back names what could not be written"


def _main() -> int:
    checks = [
        test_the_original_defects_are_real,          # non-vacuity first
        test_the_recorded_code_is_the_commands_not_the_pipes,
        test_stderr_lands_in_the_file,
        test_the_record_keeps_argument_boundaries,
        test_the_functions_survive_export_to_a_child,
        test_sourcing_never_truncates_the_record,
        test_trim_keeps_the_newest_lines,
        test_the_line_cap_actually_bounds_the_file,
        test_an_attached_shell_records_what_it_ran_with_real_exit_codes,
        test_the_first_prompt_does_not_record_the_history_it_inherited,
        test_a_shell_with_no_history_still_records_its_first_command,
        test_sourcing_leaks_no_errexit_or_nounset,
        test_sourcing_is_silent,
        test_an_unwritable_target_warns_once_and_does_not_kill_the_caller,
        test_an_unwritable_target_still_says_so,
        test_every_line_carries_its_pid_so_concurrent_shells_stay_separable,
        test_a_multiline_message_is_still_one_record,
        test_a_trim_leaves_evidence_that_it_trimmed,
        test_two_shells_writing_at_once_keep_both_records,
        test_a_child_process_renames_the_namespace_without_touching_the_parents,
        test_the_install_is_idempotent_and_reversible,
        test_the_trace_wire_fires_once_per_shell_green_and_red,
    ]
    for check in checks:
        check()
        if check is not test_the_original_defects_are_real or _ORIGINAL.exists():
            print(f"  PASS  {check.__name__}")
    print("green — logger_for_bash: the recorded exit code is the command's (not the pipe's), "
          "stderr reaches the file, the record keeps argument boundaries, sourcing neither "
          "truncates nor leaks a `set`, trim keeps the newest N, every line carries its pid so "
          "concurrent shells stay separable, and the four defects it was grafted to fix are "
          "measured still present in the original")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
