"""Proof for ticket 1c1b18bac2eb — an operator's measured clear closes a trouble and stays on
its record.

Measured 2026-10-11: nine who-writes-what clears by Akien landed as cleared_by {by: 'akien'}
and every one stayed OPEN, because their notified set is ['cc'] and a clear closed only when
every notified recipient had cleared. Akien and CC are both operators; a clear whose MEASURED
hand (c2172127d7a4) is an operator's closes it. A gate or unknown hand clears as before.

1. a trouble notified ['cc'], cleared through a clear emission whose hand.class is 'akien',
   is CLEARED after the drain and its cleared_by entry carries that hand;
2. the same with hand.class 'gate' and by 'akien' stays OPEN (today's rule);
3. the 'clears' verb with prefix 'who-writes-what-' answers one row per cleared_by entry with
   hand_class, and no occurrences key.

Scratch world and store. The clear emissions are written with ``emit`` in the shape
c2172127d7a4's clear_trouble writes, so this proof measures the holder alone (RULE 1).
The device is imported inside ``main``.

Run bare:  PYTHONPATH=. python3 cairn/devices/trouble/proofs/test_an_operators_measured_clear_closes.py
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {
    "1c1b18bac2eb": {
        "1": "an_akien_hand_closes_a_cc_notified_trouble",
        "2": "a_gate_hand_by_akien_stays_open",
        "3": "the_clears_verb_answers_one_small_row_per_clear",
    },
}

AKIEN = {"class": "akien", "unit": "a-scope", "ancestry": ["101:a-scope"]}
GATE = {"class": "gate", "unit": "a-unit", "ancestry": ["202:a-unit"]}
FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail[:300]}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def _component(world: Path):
    from cairn.tools.base.diagnostic import DiagnosticBase

    class _Fixture(DiagnosticBase):
        @property
        def diagnostic_device(self) -> str:
            return "a_fixture_component"

    d = _Fixture()
    d.set_diagnostic_roots({k: world for k in ("repo", "commons", "instance")})
    return d


def main() -> int:
    from cairn.devices.trouble.shim import TroubleShim
    from cairn.devices.trouble.trouble import TroubleDevice, CLEARED

    with tempfile.TemporaryDirectory(prefix="cairn-operator-clear-proof-") as tmp:
        world, store = Path(tmp) / "world", Path(tmp) / "store"
        c = _component(world)
        for ident in ("who-writes-what-one", "who-writes-what-two", "another-trouble"):
            c.raise_trouble(ident, why="a proof's trouble", detail={"n": 1})
        shim = TroubleShim(roots={k: world for k in ("repo", "commons", "instance")}, root=str(store))
        shim.drain()
        c.emit("clear_trouble", pointer="who-writes-what-one",
               values={"by": "akien", "what_changed": "the row was taught", "hand": AKIEN})
        c.emit("clear_trouble", pointer="who-writes-what-two",
               values={"by": "akien", "what_changed": "a gate wrote this", "hand": GATE})
        drained = shim.drain()
        dev = TroubleDevice(root=str(store))
        dev.set_diagnostic_receiver(None)
        tickets = {t["id"]: t for t in dev.all()} if hasattr(dev, "all") else {}
        one = tickets.get("who-writes-what-one") or dev._read("who-writes-what-one") or {}
        two = tickets.get("who-writes-what-two") or dev._read("who-writes-what-two") or {}

        last = (one.get("cleared_by") or [{}])[-1]
        check(PROVES["1c1b18bac2eb"]["1"],
              one.get("notified") == ["cc"] and one.get("standing") == CLEARED and last.get("hand") == AKIEN,
              json.dumps({"standing": one.get("standing"), "notified": one.get("notified"),
                          "hand": last.get("hand"), "refused": drained.get("refused")}))
        check(PROVES["1c1b18bac2eb"]["2"],
              two.get("standing") != CLEARED and len(two.get("cleared_by") or []) == 1,
              json.dumps({"standing": two.get("standing"), "cleared_by": len(two.get("cleared_by") or [])}))

        name = PROVES["1c1b18bac2eb"]["3"]
        try:
            verb = dev.declared_verbs()["clears"]
            rows = verb({"body": {"prefix": "who-writes-what-"}})["clears"]
            by_id = {r["id"]: r for r in rows}
            check(name,
                  len(rows) == 2 and set(by_id) == {"who-writes-what-one", "who-writes-what-two"}
                  and by_id["who-writes-what-one"]["hand_class"] == "akien"
                  and by_id["who-writes-what-two"]["hand_class"] == "gate"
                  and all(set(r) == {"id", "standing", "by", "hand_class", "at"} for r in rows)
                  and "occurrences" not in json.dumps(rows),
                  json.dumps(rows))
        except Exception as exc:  # noqa: BLE001
            check(name, False, f"{type(exc).__name__}: {exc}")

    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    for f in FAILURES:
        print(f"  - {f}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
