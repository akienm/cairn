"""Proof for ticket 99ef0135b9b6: a chart packet deposits by value, so a far box's deposit lands.

MEASURED 2026-11-12 on akienasus, whose bus home is akiendelllinux: e8fe361a5b2f's
a_real_deposit_rides_the_bus reds "no berthed orient packet under .../chart/0/packets".
Codemother berths packets on the box she runs on. Her deposit verb refuses a berth path that is
not on her own disk ("berth %r is not on disk"), so a path sent from another box never lands.

  1. clause_1_a_packet_by_value_lands: the verb over {packet, name, nexus}, with no file on
     codemother's side, berths the packet as <name> under her instance deposits dir and lands
     it; the reply is accepted and names a node;
  2. clause_2_scratch_is_minted_and_dropped_on_her_side: with {scratch}, the orient packet lands
     in a codemother scratch nexus the verb mints itself; the reply names that nexus, and its
     table does not exist once the reply is back;
  3. clause_3_a_bad_body_is_refused_by_name: a name with a path separator, a name with no known
     stage prefix, a packet that is not an object, and scratch on a non-orient name are each
     refused naming the lack, and nothing is berthed.

Clause 4 is e8fe361a5b2f's tooth a_real_deposit_rides_the_bus, in
test_the_chart_deposit_is_a_codemother_verb.py. The device runs in process over a stub bus that
answers embed with a 3-float vector. Every name is prefixed testing-, and the proof removes the
berths it causes.

    bin/cairn test cairn/devices/codemother/proofs/test_a_packet_deposits_by_value.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {"99ef0135b9b6": {
    "1": "clause_1_a_packet_by_value_lands",
    "2": "clause_2_scratch_is_minted_and_dropped_on_her_side",
    "3": "clause_3_a_bad_body_is_refused_by_name",
}}

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "orient-testing-e8fe361a5b2f.json"
SENDER = "testing-99ef0135b9b6-proof"
_VEC = [1.0, 0.0, 0.0]


class _EmbedBus:
    """Answers inference_domain's embed resolve with a fixed vector."""

    def request(self, **kw):
        return {"body": {"answer": {"vector": list(_VEC)}, "hit": False,
                         "provenance": {"counters": {"prompt_eval_count": 1}}}}

    def post(self, **kw):
        return {"id": "post"}


def _packet() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _deposits() -> Path:
    from cairn.tools.base.address import instance_path
    return instance_path("codemother", 0) / "deposits"


def _ask(body: dict) -> dict:
    from cairn.devices.codemother.shim import CodeMotherDevice
    verb = CodeMotherDevice(bus=_EmbedBus()).declared_verbs()["deposit"]
    return verb({"sender": SENDER, "verb": "deposit", "body": body})


def _forget(*names: str) -> None:
    for n in names:
        (_deposits() / n).unlink(missing_ok=True)


def clause_1_a_packet_by_value_lands():
    from cairn.tools.tree.tree import scratch_nexus
    name = "orient-testing-99ef0135b9b6-one.json"
    _forget(name)
    try:
        with scratch_nexus("testing_99ef_one", owner="codemother") as nexus:
            got = _ask({"packet": _packet(), "name": name, "nexus": nexus})
            assert got.get("accepted") is True, f"the by-value deposit was refused: {got}"
            assert got.get("nexus") == nexus, f"landed in {got.get('nexus')!r}, not {nexus!r}"
            learned = got.get("learn") or {}
            assert learned.get("id") or learned.get("node_id") or learned.get("node_ids"), \
                f"the reply names no node: {got}"
        berthed = _deposits() / name
        assert berthed.is_file(), f"nothing berthed at {berthed}"
        assert json.loads(berthed.read_text(encoding="utf-8")) == _packet(), \
            "the berthed packet differs from the one sent"
        assert got.get("berth") == str(berthed), f"deposited from {got.get('berth')!r}, not {berthed}"
    finally:
        _forget(name)


def clause_2_scratch_is_minted_and_dropped_on_her_side():
    from cairn.devices.db_domain.tools.client import store
    from cairn.tools.tree.tree import nexus_table
    name = "orient-testing-99ef0135b9b6-two.json"
    _forget(name)
    try:
        got = _ask({"packet": _packet(), "name": name, "scratch": "testing_99ef_two"})
        assert got.get("accepted") is True, f"the scratch deposit was refused: {got}"
        nexus = got.get("nexus") or ""
        assert nexus.startswith("testing_99ef_two"), f"the reply names nexus {nexus!r}"
        learned = got.get("learn") or {}
        assert learned.get("id") or learned.get("node_id") or learned.get("node_ids"), \
            f"the reply names no node: {got}"
        table = nexus_table(nexus, owner="codemother")
        assert store.owner_of(table) is None, f"{table} still stands after the reply"
    finally:
        _forget(name)


def clause_3_a_bad_body_is_refused_by_name():
    before = set(p.name for p in _deposits().glob("*")) if _deposits().is_dir() else set()
    cases = [
        ({"packet": _packet(), "name": "../orient-testing-99ef0135b9b6-up.json"}, "name"),
        ({"packet": _packet(), "name": "testing-99ef0135b9b6-nostage.json"}, "stage"),
        ({"packet": ["not", "an", "object"], "name": "orient-testing-99ef0135b9b6-list.json"}, "packet"),
        ({"packet": _packet(), "name": "survey-testing-99ef0135b9b6-scr.json",
          "scratch": "testing_99ef_bad"}, "scratch"),
    ]
    for body, lack in cases:
        got = _ask(body)
        assert got.get("accepted") is False, f"{body.get('name')!r} was accepted: {got}"
        assert lack in str(got.get("reason", "")), \
            f"the refusal of {body.get('name')!r} does not name {lack!r}: {got.get('reason')!r}"
    after = set(p.name for p in _deposits().glob("*")) if _deposits().is_dir() else set()
    assert after == before, f"a refused body berthed {sorted(after - before)}"
    assert not (_deposits().parent / "orient-testing-99ef0135b9b6-up.json").exists(), \
        "the separator name escaped the deposits dir"


TEETH = [clause_1_a_packet_by_value_lands, clause_2_scratch_is_minted_and_dropped_on_her_side,
         clause_3_a_bad_body_is_refused_by_name]


if __name__ == "__main__":
    failed = 0
    for fn in TEETH:
        try:
            fn()
        except Exception as exc:  # noqa: BLE001 — a proof reports, never hides
            failed += 1
            print(f"  RED   {fn.__name__}: {type(exc).__name__}: {exc}")
        else:
            print(f"  green {fn.__name__}")
    raise SystemExit(1 if failed else 0)
