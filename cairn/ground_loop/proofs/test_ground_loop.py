"""Proof for ground_loop — the generic driver-executor, composing the spine.

This is the first proof that exercises THREE devices together: the tester (defines
proven-space), db_domain (the owned target), and the ground_loop that wires them under a
driver's why. It confirms the hypothesis for the simple case and shows both guards as
physics, not prose.

Teeth a hollow ground_loop could not pass:
  - THE HYPOTHESIS HOLDS (happy path). A driver wiring a proven method to an owned target
    runs: the method's row lands in the target (read back through db_domain) and a run-record
    comes out. A hollow executor that ran nothing, or wrote nothing, trips this.
  - UNPROVEN CODE CANNOT RUN (Law 8). A driver whose method is not in proven-space is refused;
    a method whose proof REDS under the tester is refused admission. An executor that ran
    unregistered/unproven code trips these.
  - A NON-OWNER CANNOT WRITE (Law 6). A driver whose target owner is not the table's owner is
    refused BY db_domain's gate, through the ground_loop. An executor that wrote ambiently
    trips this.
  - A MALFORMED DRIVER IS REFUSED LOUDLY (CP1) before anything runs.
  - IT IS A DEVICE (Law 2 / Form v0 #2).

Requires Postgres (db_domain's one-time role) and runs the tester (subprocess proofs).
Self-cleaning: the ephemeral target table is dropped on the way out.

    python3 cairn/ground_loop/proofs/test_ground_loop.py     # exit 0 = green
"""

from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.base.core_values import CoreValuesMixin
from cairn.db_domain import store
from cairn.db_domain.store import OwnershipError
from cairn.ground_loop.loop import GroundLoopDevice
from cairn.ground_loop.registry import MethodRegistry, UnprovenMethod
from cairn.ground_loop.proofs.fixtures.collect import collect

_FIXTURES = _REPO_ROOT / "cairn" / "ground_loop" / "proofs" / "fixtures"
_PROOF_COLLECT = _FIXTURES / "proof_collect.py"
_RED_PROOF = _REPO_ROOT / "cairn" / "tester" / "proofs" / "fixtures" / "red_proof.py"

_NONCE = f"{os.getpid()}_{datetime.now().strftime('%H%M%S%f')}"
_TARGET = f"_gl_target_{_NONCE}"     # the owned target table this driver writes to
_OWNER = "sensor"                     # the target's owner (on whose behalf the driver writes)


def _fresh_device() -> GroundLoopDevice:
    """A ground_loop whose registry already admits `collect` (its proof passed under the tester)."""
    reg = MethodRegistry()
    reg.register("collect", collect, _PROOF_COLLECT)
    return GroundLoopDevice(registry=reg)


def _driver(method="collect", owner=_OWNER):
    return {
        "name": "collect-driver",
        "method": method,
        "why": "collect the reading into the owned target — the canonical sensor driver",
        "target": {"table": _TARGET, "owner": owner},
    }


def test_the_hypothesis_holds_end_to_end():
    dev = _fresh_device()
    # The target's owner provisions its table first (the ground_loop wires, it does not own).
    store.create_owned_table(_TARGET, _OWNER, {"value": "text"})

    record = dev.run_driver(_driver())

    # The run-record is legible evidence (LEARNING, not silent RUNNING).
    assert record["outcome"] == "ok"
    assert record["driver"] == "collect-driver" and record["wrote"] == {"value": "42"}

    # The method's row actually landed in the owned target — through db_domain.
    rows = store.read(_TARGET, where="value = %s", params=("42",))
    assert len(rows) == 1 and rows[0]["value"] == "42", "the driver's row must land in its target"
    assert dev.state()["drivers_run"] == 1


def test_unproven_method_cannot_run():
    dev = _fresh_device()
    # (a) a method-pointer not in proven-space → the ground_loop refuses to run it (Law 8).
    try:
        dev.run_driver(_driver(method="never-registered"))
        raise AssertionError("a driver wiring an unregistered method must be refused (Law 8)")
    except UnprovenMethod:
        pass
    # (b) admission itself is gated: a method whose proof REDS under the tester is not admitted.
    try:
        MethodRegistry().register("bad", collect, _RED_PROOF)
        raise AssertionError("a method whose proof reds must be refused admission (Law 8)")
    except UnprovenMethod:
        pass


def test_a_non_owner_target_write_is_refused():
    dev = _fresh_device()
    store.create_owned_table(_TARGET, _OWNER, {"value": "text"})
    # The driver claims an owner that does not own the target → db_domain's gate refuses (Law 6),
    # and the ground_loop propagates it loudly (a kick-back, not a success-shaped silence).
    try:
        dev.run_driver(_driver(owner="impostor"))
        raise AssertionError("a write by a non-owner of the target must be refused (Law 6)")
    except OwnershipError:
        pass


def test_a_malformed_driver_is_refused():
    dev = _fresh_device()
    for bad in ({"method": "collect"}, {"name": "x", "method": "collect", "why": "w", "target": {"table": _TARGET}}):
        try:
            dev.run_driver(bad)
            raise AssertionError(f"a malformed driver must be refused before running: {bad}")
        except ValueError:
            pass


def test_it_is_a_device():
    dev = _fresh_device()
    assert isinstance(dev, CoreValuesMixin), "a device must compose the core values (Law 2)"
    assert [v.id for v in dev.CORE_VALUES] == ["CP1", "CP2", "CP3", "CP4", "CP5", "CP6"]
    assert list(dev.introspect()) == ["intention", "state", "settings", "other"], "Form v0 #2 order"


def _cleanup():
    conn = store.connect()
    try:
        with conn.cursor() as cur:
            cur.execute(f'DROP TABLE IF EXISTS "{_TARGET}"')
            cur.execute(f'DELETE FROM "{store._REGISTRY}" WHERE table_name = %s', (_TARGET,))
    finally:
        conn.close()


def _main() -> int:
    checks = [
        test_the_hypothesis_holds_end_to_end,
        test_unproven_method_cannot_run,
        test_a_non_owner_target_write_is_refused,
        test_a_malformed_driver_is_refused,
        test_it_is_a_device,
    ]
    try:
        for check in checks:
            check()
            print(f"  PASS  {check.__name__}")
    finally:
        _cleanup()
    print("green — ground_loop: one executor wires a proven method to an owned target; "
          "unproven code can't run, a non-owner can't write, the run is legible")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
