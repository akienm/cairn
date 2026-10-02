"""The teeth that measure the tester's own code, moved home (ticket 67b78ae59c1d, RULE 1).

Four teeth that once lived in other components' proofs and reached into the tester to measure
it. RULE 1 says a component's proofs measure only that component, so each moved here bodily —
assertions unchanged, names unchanged, PROVES keys unchanged — and was deleted where it stood:

  (a) d2ecdb867bc9 "d" — from cairn/tools/base/proofs/test_crossings_are_derived.py
  (b) e3cf75c6dc8f "8" — from cairn/tools/system_word/proofs/test_system_word.py (with _drive)
  (c) c5b6b128a376 "4" — part (c) of the self-reference tooth in
      cairn/tools/proof_coverage/proofs/test_call_time_binding.py, which keeps (a)(b)(d) and
      declares the same key: that clause is now proved on both sides of the seam
  (d) 201a37bf1613 "1" — the tester half of
      cairn/devices/db_domain/proofs/test_scratch_cannot_outlive_its_process.py, whose tooth
      keeps only the one-time sweep; the minter here forks through db_domain's published store
      client, no bus

Run: python3 cairn/devices/tester/proofs/test_the_teeth_that_measure_the_tester.py
"""
from __future__ import annotations

import io
import json
import os
import signal
import subprocess
import sys
import tempfile
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cairn.devices.db_domain.tools.client import store  # noqa: E402

PROVES = {
    "d2ecdb867bc9": {"d": "test_THE_BUILDME_TIME_HAS_NO_COARSER_FALLBACK_LEFT_TO_BE_WRONG"},
    "e3cf75c6dc8f": {"8": "test_tester_cli_takes_uppercase_flags"},
    "c5b6b128a376": {"4": "test_hollow_reads_unran_exactly_the_file_the_sieve_names"},
    "201a37bf1613": {"1": "test_a_seal_sweeps_first_and_says_so"},
}


# --- (a) d2ecdb867bc9 "d" ----------------------------------------------------------------

def test_THE_BUILDME_TIME_HAS_NO_COARSER_FALLBACK_LEFT_TO_BE_WRONG():
    """CLAUSE (d) — hollow resolves the pre-build moment to the second or refuses to guess.

    The retired branch read the stored crossing's ``date``, which is a DAY. ``git rev-list -1
    --before=2026-09-07`` resolves a bare date to the last commit before that day STARTED, so a
    ticket built and committed on one day reverted to a whole day earlier and the hollow reading
    measured a world the build never stood in — a wrong answer delivered with no sign it was
    wrong, which Law 3 calls a hypothesis wearing a measurement's clothes.

    Deriving from the journal means every crossing carries an ``at`` with a time, so the branch
    that could be wrong has nothing left to be wrong about. At the pre-build commit this same
    call returned ``"2026-09-01"``; now it refuses.
    """
    from cairn.devices.tester.hollow import HollowUnmeasurable, _buildme_at
    ticket = {"id": "t1", "crossings": [{"to": "BUILDME", "date": "2026-09-01"}]}
    crossing = {"to": "BUILDME", "date": "2026-09-01"}   # a day, and no 'at'
    with pytest.raises(HollowUnmeasurable) as red:
        _buildme_at(ticket, crossing)
    assert "at" in str(red.value), (
        "hollow refused, but not for the missing time — the message must name what is absent")


# --- (b) e3cf75c6dc8f "8" ----------------------------------------------------------------

def _drive(fn, argv, **env):
    out, err = io.StringIO(), io.StringIO()
    old = {k: os.environ.get(k) for k in env}
    os.environ.update(env)
    try:
        with redirect_stdout(out), redirect_stderr(err):
            try:
                rc = fn(argv)
            except SystemExit as exc:
                rc = exc.code
    finally:
        for k, v in old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    return rc, out.getvalue(), err.getvalue()


def test_tester_cli_takes_uppercase_flags():
    from cairn.devices.tester.cli import main
    with tempfile.TemporaryDirectory() as d:
        rc, out, err = _drive(main, ["--SEAL", "-Q", d])
    assert rc == 2 and "found no proofs" in err, (
        f"the flags parse folded and the run reaches discovery: rc={rc} {err!r}")


# --- (c) c5b6b128a376 "4" ----------------------------------------------------------------

def test_hollow_reads_unran_exactly_the_file_the_sieve_names():
    """Hollow, run over the world the sieve reads, reads exactly the sieve's file UNRAN."""
    from cairn.tools import proof_coverage as pc
    from cairn.tools.proof_coverage.proofs.fixtures import historical_instances as H
    from cairn.devices.tester import hollow
    with tempfile.TemporaryDirectory() as tmp:
        world = H.direct_added_file(Path(tmp))
        binding = [l for l in pc.lacks(world.ticket, repo_root=world.repo, roots=world.roots)
                   if l["kind"] == "proof_binds_its_subject_at_call_time"]
        assert len(binding) == 1, binding
        predicted = binding[0]["values"]["file"]
        reading = hollow.measure(world.ticket["id"], repo_root=world.repo, commons=world.commons,
                                 berths_root=world.roots["berths"], timeout=120,
                                 log=lambda *_: None)
        unran = reading.get("unran") or {}
        assert predicted in unran, (predicted, reading.get("verdict"), reading.get("reasons"))
        assert any(p.endswith(world.proof) for p in unran[predicted]), unran
        assert reading.get("verdict") == "red", reading.get("verdict")


# --- (d) 201a37bf1613 "1" ----------------------------------------------------------------

_OWNER = "tester"
_COLUMNS = {"x": "text"}


def _pg_tables() -> set[str]:
    with store.connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
        return {r[0] for r in cur.fetchall()}


def _fork_minter(prefix: str) -> tuple[int, str]:
    """Fork a child that mints a scratch table, reports the name up a pipe, then sleeps inside
    the ``with`` — never reaching its ``finally``. Returns (pid, table)."""
    r, w = os.pipe()
    pid = os.fork()
    if pid == 0:  # the child
        os.close(r)
        try:
            with store.scratch(_OWNER, prefix, _COLUMNS) as table:
                os.write(w, table.encode())
                os.close(w)
                signal.pause()
        finally:
            os._exit(0)
    os.close(w)
    table = os.read(r, 256).decode()
    os.close(r)
    assert table, "the child minted nothing"
    return pid, table


def _kill(pid: int) -> None:
    os.kill(pid, signal.SIGKILL)
    os.waitpid(pid, 0)


def _tiny_proof(dirpath: Path) -> Path:
    """A one-line green proof under a scratch component: ``<d>/proofs/test_tiny_201a.py``,
    so its seal lands at ``<d>/validations/test_tiny_201a.json`` the way every seal does."""
    (dirpath / "proofs").mkdir()
    p = dirpath / "proofs" / "test_tiny_201a.py"
    p.write_text("print('ok test_tiny')\n", encoding="utf-8")
    return p


def test_a_seal_sweeps_first_and_says_so() -> None:
    from cairn.devices.tester.device import TesterDevice
    from cairn.devices.tester.scratch_sweep import sweep
    with tempfile.TemporaryDirectory(prefix="201a-seal-") as d:
        tiny = _tiny_proof(Path(d))
        tester = TesterDevice()
        # a seal without a sweep is refused at the run door, like a seal without a sink
        try:
            tester.run_proof(tiny, sink="validations", caller="proof 201a")
            raise AssertionError("run_proof sealed without a scratch sweep")
        except ValueError as exc:
            assert "scratch_sweep" in str(exc), exc
        # a run that seals nothing records that it swept nothing — never a made-up zero
        rec = tester.run_proof(tiny, sink="none", caller="proof 201a")
        assert rec["evidence"]["scratch_sweep"] == {"skipped": "the caller sealed nothing and swept nothing"}, rec["evidence"]
        # the seal's evidence carries what the sweep dropped, by name
        pid, table = _fork_minter("scratch_seal")
        _kill(pid)
        swept = sweep()
        assert swept.get("dropped", 0) >= 1 and table in swept["tables"], swept
        rec = tester.run_proof(tiny, sink="validations", caller="proof 201a", scratch_sweep=swept)
        assert rec["evidence"]["scratch_sweep"] == swept, rec["evidence"]
        sealed = json.loads((Path(d) / "validations" / "test_tiny_201a.json").read_text())[-1]
        assert sealed["evidence"]["scratch_sweep"]["tables"] == swept["tables"], sealed["evidence"]
        # the CLI names the count on the way past
        pid, table = _fork_minter("scratch_cli")
        _kill(pid)
        r = subprocess.run([sys.executable, "-m", "cairn.devices.tester.cli", "--seal", str(tiny)],
                           cwd=str(ROOT), env={**os.environ, "PYTHONPATH": str(ROOT)},
                           capture_output=True, text=True, timeout=300)
        assert r.returncode == 0, (r.stdout, r.stderr)
        line = next((ln for ln in r.stdout.splitlines() if ln.strip().startswith("swept ")), None)
        assert line and table in line and "1 scratch table(s)" in line, r.stdout
    assert table not in _pg_tables() and not store.is_scratch(table)
    print("ok test_a_seal_sweeps_first_and_says_so")


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
