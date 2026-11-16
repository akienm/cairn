#!/usr/bin/env python3
"""Proof that the librarian's proofs reach no other device (ticket a16c4d4ff4bd).

Measured 2026-11-10: encapsulation_breaches listed three rows whose source is the librarian —
test_librarian_chat.py:396 and :409 (inferenceproxy's domain module patched behind a
scratch BusDevice and the inference shim) and test_librarian_loop.py:55 (inferenceproxy's
canonicalize). RULE 1: a component's proofs measure only that component. The chat stamp tooth
now drives dual_seam over a recording bus and reads what the seam sends; the loop's livelock
tooth keeps the librarian's half (the prompt changed) and leaves the cache key to
inferenceproxy's own proofs.

Teeth, one per falsifier clause (PROVES below):
  (1) encapsulation_breaches lists no row whose source is cairn/devices/librarian;
  (2) neither proof names a cairn.devices.inferenceproxy or cairn.devices.cairn module, and
      each, run as its own process, is green.

    PYTHONPATH=. python3 cairn/devices/librarian/proofs/test_the_librarian_proofs_reach_no_device.py
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

_SOURCE = "cairn/devices/librarian"
_PROOFS = (_REPO / "cairn/devices/librarian/proofs/test_librarian_chat.py",
           _REPO / "cairn/devices/librarian/proofs/test_librarian_loop.py")
_FORBIDDEN = ("cairn.devices.inferenceproxy", "cairn.devices.cairn")

PROVES = {"9f7f587fe314": {"1": "test_the_sieve_names_a_planted_breach", "2": "test_no_librarian_row"}, "a16c4d4ff4bd": {
    "1": "test_no_librarian_row",
    "2": "test_the_two_proofs_name_no_other_device_and_run_green",
}}

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def test_the_sieve_names_a_planted_breach() -> None:
    """Not blind (ticket 9f7f587fe314): over a scratch tree holding one planted import from
    this component into cairn/devices/inferenceproxy, the sieve names exactly that row. Until this ticket the live tooth
    proved the sieve could see by requiring a breach somewhere else in the live tree, so it
    went red the day the tree came clean (measured 2026-11-16: 0 breaches at 07:45)."""
    from cairn.tools.inspect_wire.inspect_wire import ask
    from cairn.tools.scratch.scratch import scratch_dir
    root = Path(scratch_dir("testing-9f7f587fe314-planted-breach-"))
    tgt = "cairn/devices/inferenceproxy"
    for comp in (_SOURCE, tgt):
        parts = comp.split("/")
        for i in range(1, len(parts) + 1):
            d = root.joinpath(*parts[:i])
            d.mkdir(exist_ok=True)
            (d / "__init__.py").touch()
        (root / comp / "intention+why.json").write_text("{}\n", encoding="utf-8")
    (root / _SOURCE / "planted.py").write_text("from cairn.devices.inferenceproxy import x\n", encoding="utf-8")
    found = [(b["file"], b["line"], b["source"], b["target"])
             for b in ask('encapsulation_breaches', str(root))]
    want = [(_SOURCE + "/planted.py", 1, _SOURCE, tgt)]
    check("test_the_sieve_names_a_planted_breach", found == want, f"found {found!r}")


def test_no_librarian_row() -> None:
    from cairn.tools.inspect_wire.inspect_wire import ask
    breaches = ask('encapsulation_breaches', str(_REPO))
    rows = [r for r in breaches if r.get("source") == _SOURCE]
    # Not blind is test_the_sieve_names_a_planted_breach's job (ticket 9f7f587fe314): a clean live tree is the
    # goal, so this tooth no longer needs a breach elsewhere to pass.
    check("test_no_librarian_row", not rows,
          f"{len(breaches)} breach(es) in all; "
          + "; ".join(f"{r['file']}:{r.get('line')} -> {r.get('module')}" for r in rows))


def test_the_two_proofs_name_no_other_device_and_run_green() -> None:
    lacks = []
    for proof in _PROOFS:
        text = proof.read_text(encoding="utf-8")
        for mod in _FORBIDDEN:
            if mod in text:
                lacks.append(f"{proof.name} still names {mod}")
    if not lacks:
        env = {**os.environ, "PYTHONPATH": str(_REPO)}
        for proof in _PROOFS:
            run = subprocess.run([sys.executable, str(proof)], cwd=str(_REPO), env=env,
                                 capture_output=True, text=True, timeout=600)
            if run.returncode != 0:
                tail = (run.stdout + run.stderr).strip().splitlines()[-6:]
                lacks.append(f"{proof.name} exited {run.returncode}: {' | '.join(tail)}")
    check("test_the_two_proofs_name_no_other_device_and_run_green", not lacks, "; ".join(lacks))


def main() -> int:
    os.chdir(_REPO)
    for tooth in (test_the_sieve_names_a_planted_breach, test_no_librarian_row, test_the_two_proofs_name_no_other_device_and_run_green):
        try:
            tooth()
        except Exception as exc:  # noqa: BLE001 — a tooth that cannot run is a red, loudly
            check(tooth.__name__, False, f"raised {type(exc).__name__}: {exc}")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
