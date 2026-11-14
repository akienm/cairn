"""Proof for ticket ad6f3d0b265c, clause 3: his_case_never_bites reads "no bite" only over a
command that ran.

The probe drives ``cairn codemother harbor_master show map --filter open`` beside its OPEN
form and calls it a bite when the two answer differently. Two commands that both exit
non-zero print the same error, so before this a call site whose command could not run (a
reverted one asks ``harbor_master show map open``, which exits 127) read "no bite". Now a
non-zero exit is reported as a failure naming the command.

One tooth, two worlds, each the probe's own call site driven through bin/cairn:

  * a world where the word answers: a scratch CAIRN_INSTANCE_ROOT (so bin/cairn dispatches the
    word beside this code) and a scratch bus process holding harbor_master from this checkout
    (scratch_bus.launch), waited out after. The harbor entry is present and does not bite.
  * a world where the word cannot answer: a scratch instance root whose codemother word
    harbor_master is a stub exiting 3. The harbor entry bites, and its name says the command
    exited 3.

    bin/cairn test cairn/tools/system_word/proofs/test_his_case_never_bites_reads_only_a_command_that_ran.py
"""
from __future__ import annotations

import contextlib
import os
import sys
import time
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"ad6f3d0b265c": {
    "3": "test_the_bite_check_reads_only_a_command_that_ran",
}}

PROOF_TIMEOUT_S = 900

_ENTRY = "harbor_master show map OPEN"


@contextlib.contextmanager
def _environ(**values: str):
    saved = {k: os.environ.get(k) for k in values}
    os.environ.update(values)
    try:
        yield
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def _harbor_entries() -> list[tuple[str, bool]]:
    # bound at call time: a hollow reading reverts the probe, and the tooth must still run
    from cairn.tools.system_word.probes import his_case_never_bites as probe
    return [(name, bit) for name, bit in probe._drive_python() if name.startswith(_ENTRY)]


def _wait_gone(home: str, deadline_s: float = 20.0) -> None:
    """launch's shutdown is a request; wait until the scratch bus stops answering."""
    from cairn.tools.bus_client.remote import exchange
    end = time.monotonic() + deadline_s
    while time.monotonic() < end:
        try:
            exchange({"op": "ping"}, home, timeout=1)
        except (OSError, ValueError):
            return
        time.sleep(0.2)


def test_the_bite_check_reads_only_a_command_that_ran():
    from cairn.devices.cairn.tools.scratch_bus.scratch_bus import launch
    from cairn.tools.scratch.scratch import scratch_dir

    instances = scratch_dir("testing-ad6f-instances-")
    with launch("harbor_master", prefix="testing-ad6f") as bus:
        home = str(bus._home)
        with _environ(CAIRN_BUS_HOME=home, CAIRN_INSTANCE_ROOT=str(instances)):
            ran = _harbor_entries()
    _wait_gone(home)
    assert ran == [(_ENTRY, False)], f"where the word answers, the harbor entry reads {ran}"

    stubbed = scratch_dir("testing-ad6f-stubbed-")
    word = stubbed / "codemother" / "0" / "bin" / "harbor_master"
    word.parent.mkdir(parents=True)
    word.write_text('#!/usr/bin/env bash\necho "testing-ad6f: a word that cannot answer" >&2\n'
                    "exit 3\n", encoding="utf-8")
    word.chmod(0o755)
    with _environ(CAIRN_INSTANCE_ROOT=str(stubbed)):
        failed = _harbor_entries()
    assert len(failed) == 1 and failed[0][1] is True and "exited 3" in failed[0][0], (
        f"where the word cannot answer, the harbor entry reads {failed}: a failure must bite "
        f"and name the command, never read 'no bite'")


TEETH = [test_the_bite_check_reads_only_a_command_that_ran]


def main() -> int:
    failed = 0
    for fn in TEETH:
        try:
            fn()
        except Exception as exc:  # noqa: BLE001 — a proof reports, never hides
            failed += 1
            print(f"  FAIL  {fn.__name__}: {type(exc).__name__}: {exc}")
        else:
            print(f"  PASS  {fn.__name__}")
    print(f"{len(TEETH) - failed} passed, {failed} failed out of {len(TEETH)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
