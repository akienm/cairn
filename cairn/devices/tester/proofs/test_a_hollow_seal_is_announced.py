"""A hollow seal that lands evidence on a green proof tells codemother, and only then.

Charter + why: cairn/devices/tester/intention+why.json
Ticket:        CairnCommons/tickets/9bdbeeaa1f8b-a-hollow-seal-is-announced.json

WHAT BORE IT, measured n=2 on 2026-10-02 (e8fe361a5b2f, 56d1aff4455e). A sealing run announces
every green seal (``_announce_seals``, ticket 1accdc1781aa), and codemother crosses each boat
that named the proof. But the hollow reading can only be taken AFTER a seal stands, and
``cairn test --hollow <ticket> --seal`` landed it silently. So codemother heard the seal that
came before the reading and never the one that completed it, and the crossing always fired on
the incomplete record. Each time it was refused hollow_evidence_absent, and an unchanged build
went to FIXME.

WHAT IS SUBSTITUTED: the bus (a scratch table, so codemother is never wired here and nothing
live crosses) and ``hollow.measure`` (a fixed finding, so no worktree is reverted). The CLI,
the store's door (``record_hollow``) and the announcement are the real ones.

One tooth per numbered falsifier clause:

  1. A --hollow --seal run that lands evidence on a proof whose standing validation is green
     posts exactly one more ``sealed`` message naming that proof, carrying the four fields
     the sealing run posts (proof, verdict, source_fingerprint, validations_path).
  2. A --hollow run without --seal, or one whose record_hollow lands nothing, posts none.
  3. With codemother unwired (reach raises), the hollow evidence still stands after the run.

    python3 cairn/devices/tester/proofs/test_a_hollow_seal_is_announced.py   # exit 0 = green
"""

from __future__ import annotations

import contextlib
import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.devices.cairn.machines.bus.bus import BusDevice
from cairn.tools import bus_client
from cairn.tools.scratch.scratch import scratch_dir
from cairn.tools.validation_store.validation_store import read_validations, validations_path_for

PROVES = {"9bdbeeaa1f8b": {
    "1": "a_hollow_seal_on_a_green_proof_is_announced_once",
    "2": "a_diagnostic_or_empty_hollow_run_announces_nothing",
    "3": "an_unwired_codemother_costs_the_evidence_nothing",
}}

TID = "testing9bdbe"        # the ticket the fixture finding names: never a live ticket
_TOOTH = "test_nothing_is_nothing"
_SCRATCH = contextlib.ExitStack()

PASS = 0
FAIL = 0


def _tooth(name, fn):
    global PASS, FAIL
    try:
        fn()
    except Exception as exc:  # noqa: BLE001 — a proof reports, never hides
        FAIL += 1
        print(f"  RED   {name}: {type(exc).__name__}: {exc}")
    else:
        PASS += 1
        print(f"  green {name}")


def _fixture_proof(tag: str) -> Path:
    """A component-shaped scratch directory holding one trivially green proof."""
    comp = scratch_dir(f"testing-9bdbeeaa1f8b-{tag}") / "a_fixture_component"
    (comp / "proofs").mkdir(parents=True, exist_ok=True)
    proof = comp / "proofs" / "test_fixture.py"
    proof.write_text(
        f"def {_TOOTH}():\n"
        "    assert True\n"
        f'    print("PASS: {_TOOTH}")\n\n\n'
        'if __name__ == "__main__":\n'
        f"    {_TOOTH}()\n", encoding="utf-8")
    (comp / "history.json").write_text("[]", encoding="utf-8")
    return proof


def _fixture_bus() -> BusDevice:
    return _SCRATCH.enter_context(BusDevice.scratch("hollow_ann"))


def _finding(proof: Path) -> dict:
    """What hollow.measure returns for one covered file — fixed, so nothing is reverted."""
    return {"ticket": TID, "proofs": [str(proof)], "measured": {"a/file.py": [_TOOTH]},
            "unran": {}, "hollow": [], "skipped": [], "reasons": ["ok  a/file.py (fixture)"],
            "commit": "0" * 40, "verdict": "green"}


@contextlib.contextmanager
def _wired(bus, *, finding=None, unwired=False):
    """Point the CLI's bus at ``bus`` (or make reaching fail) and its measure at ``finding``."""
    from cairn.devices.tester import hollow
    saved_reach, saved_measure = bus_client.reach, hollow.measure

    def _reach(*_devices):
        if unwired:
            raise ConnectionError("testing: codemother is not wired on this bus")
        return bus

    bus_client.reach = _reach
    if finding is not None:
        hollow.measure = lambda *_a, **_k: finding
    try:
        yield
    finally:
        bus_client.reach, hollow.measure = saved_reach, saved_measure


def _sealed(bus: BusDevice) -> list[dict]:
    return [env for env in bus.read(to="codemother", channel="personal")
            if env.get("verb") == "sealed"]


def _cli(argv):
    from cairn.devices.tester import cli
    return cli.main(argv)


def _seal_green(proof: Path, bus: BusDevice) -> None:
    with _wired(bus):
        rc = _cli(["--seal", str(proof)])
    assert rc == 0, f"the fixture proof did not seal green (rc={rc})"


def a_hollow_seal_on_a_green_proof_is_announced_once():
    proof, bus = _fixture_proof("one"), _fixture_bus()
    _seal_green(proof, bus)
    before = len(_sealed(bus))
    with _wired(bus, finding=_finding(proof)):
        _cli(["--hollow", TID, "--seal"])
    after = _sealed(bus)
    assert len(after) == before + 1, (
        f"a hollow seal over a green proof posted {len(after) - before} sealed message(s), "
        "not exactly one")
    body = after[-1].get("body") or {}
    assert body.get("proof") == str(proof), f"the message names {body.get('proof')!r}, not {proof}"
    assert body.get("verdict") == "green", f"the message says verdict {body.get('verdict')!r}"
    landed = read_validations(str(proof))[-1]
    assert isinstance(((landed.get("evidence") or {}).get("hollow") or {}).get(TID), dict), \
        "the hollow reading did not land on the standing validation"
    assert body.get("source_fingerprint") == landed["evidence"]["source_fingerprint"], \
        "the message's fingerprint is not the standing record's"
    where = body.get("validations_path") or ""
    assert where == validations_path_for(str(proof)) and os.path.isfile(where), \
        f"the message points at {where!r}, not the seal's address"


def a_diagnostic_or_empty_hollow_run_announces_nothing():
    proof, bus = _fixture_proof("diag"), _fixture_bus()
    _seal_green(proof, bus)
    before = len(_sealed(bus))
    with _wired(bus, finding=_finding(proof)):
        _cli(["--hollow", TID])
    assert len(_sealed(bus)) == before, "a diagnostic hollow run (no --seal) announced a seal"

    unsealed, bus2 = _fixture_proof("empty"), _fixture_bus()   # never sealed: record_hollow lands nothing
    with _wired(bus2, finding=_finding(unsealed)):
        _cli(["--hollow", TID, "--seal"])
    assert not _sealed(bus2), "a hollow run that landed nothing announced a seal"


def an_unwired_codemother_costs_the_evidence_nothing():
    proof, bus = _fixture_proof("unwired"), _fixture_bus()
    _seal_green(proof, bus)
    with _wired(bus, finding=_finding(proof), unwired=True):
        _cli(["--hollow", TID, "--seal"])
    landed = read_validations(str(proof))[-1]
    assert isinstance(((landed.get("evidence") or {}).get("hollow") or {}).get(TID), dict), \
        "with codemother unwired the hollow evidence did not stand"
    assert landed.get("verdict") == "green", "the standing verdict changed under the hollow seal"


TEETH = [a_hollow_seal_on_a_green_proof_is_announced_once,
         a_diagnostic_or_empty_hollow_run_announces_nothing,
         an_unwired_codemother_costs_the_evidence_nothing]

if __name__ == "__main__":
    try:
        for fn in TEETH:
            _tooth(fn.__name__, fn)
    finally:
        _SCRATCH.close()
    print(f"{PASS} passed, {FAIL} failed out of {PASS + FAIL}")
    sys.exit(1 if FAIL else 0)
