"""Proof for ticket 3c62020b0d88 — the trouble store folds what is pending before it answers a read.

Measured 2026-10-10: nothing hosts the drain. The ground loop pulses nothing by design
(bae622881f03), so TroubleShim.on_pulse never runs, and emissions sat unfolded until a hand
drained them. The read is the event that drains: a reader is the consumer asking.

1. an emission written to a fixture source's log home is not in the store until a device that
   names those roots is read; a device over the same store that names no roots folds nothing
   (a scratch store must never fold the live log homes); the named read answers with it;
2. a raise emission whose detail is text folds on the read (as {'text': ...}, 114002d08c46) and a
   later emission from the same source folds in the same read: the lane is not wedged;
3. two processes reading at once over 20 pending emissions leave every count exactly 1.

Scratch roots only. ``TroubleDevice`` is imported inside the teeth.

Run bare:  PYTHONPATH=. python3 cairn/devices/trouble/proofs/test_a_read_folds_what_is_pending.py
"""
from __future__ import annotations

import json
import multiprocessing
import os
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {
    "3c62020b0d88": {
        "1": "a_read_folds_what_is_pending",
        "2": "a_text_detail_does_not_wedge_the_read",
        "3": "two_readers_fold_each_emission_once",
    },
}

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    # The detail rides its own line: the tester reads the whole PASS/FAIL line as the tooth name.
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    if detail:
        print(f"        {detail[:300]}")
    if not ok:
        FAILURES.append(name)


def _roots(world: Path) -> dict:
    return {k: world for k in ("repo", "commons", "instance")}


def _raiser(world: Path):
    from cairn.tools.base.diagnostic import DiagnosticBase

    class _Fixture(DiagnosticBase):
        @property
        def diagnostic_device(self) -> str:
            return "a_fixture_component"

    d = _Fixture()
    d.set_diagnostic_roots(_roots(world))
    return d


def _device(store: Path, world: Path | None):
    from cairn.devices.trouble.trouble import TroubleDevice
    dev = (TroubleDevice(root=str(store)) if world is None
           else TroubleDevice(root=str(store), roots=_roots(world)))
    dev.set_diagnostic_receiver(None)
    return dev


def _read_in_child(store: str, world: str, barrier) -> None:
    barrier.wait()
    _device(Path(store), Path(world)).live()


def test_1(tmp: Path) -> None:
    name = PROVES["3c62020b0d88"]["1"]
    try:
        world, store = tmp / "w1", tmp / "s1"
        _raiser(world).raise_trouble("a-pending-raise", why="emitted, not yet folded", detail={"n": 1})
        unnamed = [t["id"] for t in _device(store, None).live()]
        before = (store / "a-pending-raise.json").exists()
        named = [t["id"] for t in _device(store, world).live()]
        check(name, unnamed == [] and not before and named == ["a-pending-raise"]
              and (store / "a-pending-raise.json").exists(),
              json.dumps({"unnamed": unnamed, "before": before, "named": named}))
    except Exception as exc:  # noqa: BLE001
        check(name, False, f"{type(exc).__name__}: {exc}")


def test_2(tmp: Path) -> None:
    name = PROVES["3c62020b0d88"]["2"]
    try:
        world, store = tmp / "w2", tmp / "s2"
        r = _raiser(world)
        r.emit("raise_trouble", pointer="a-text-detail-raise",
               values={"why": "raised by hand with a string detail", "detail": "some text"})
        r.raise_trouble("a-later-raise", why="lands behind the text one", detail={"n": 1})
        live = {t["id"]: t for t in _device(store, world).live()}
        texts = [o.get("text") for o in (live.get("a-text-detail-raise") or {}).get("occurrences", [])]
        check(name, set(live) == {"a-text-detail-raise", "a-later-raise"} and texts == ["some text"],
              json.dumps({"live": sorted(live), "texts": texts}))
    except Exception as exc:  # noqa: BLE001
        check(name, False, f"{type(exc).__name__}: {exc}")


def test_3(tmp: Path) -> None:
    name = PROVES["3c62020b0d88"]["3"]
    try:
        world, store = tmp / "w3", tmp / "s3"
        r = _raiser(world)
        for i in range(20):
            r.raise_trouble(f"a-raced-raise-{i:02d}", why="twenty pending before two readers", detail={"i": i})
        ctx = multiprocessing.get_context("spawn" if os.name == "nt" else "fork")
        barrier = ctx.Barrier(2)
        procs = [ctx.Process(target=_read_in_child, args=(str(store), str(world), barrier)) for _ in range(2)]
        for p in procs:
            p.start()
        for p in procs:
            p.join(120)
        counts = {p.stem: json.loads(p.read_text(encoding="utf-8")).get("count")
                  for p in sorted(store.glob("*.json"))}
        check(name, [p.exitcode for p in procs] == [0, 0] and len(counts) == 20
              and set(counts.values()) == {1},
              json.dumps({"exit": [p.exitcode for p in procs], "n": len(counts),
                          "counts": sorted(set(counts.values()))}))
    except Exception as exc:  # noqa: BLE001
        check(name, False, f"{type(exc).__name__}: {exc}")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="cairn-read-folds-proof-") as d:
        tmp = Path(d)
        test_1(tmp)
        test_2(tmp)
        test_3(tmp)
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    for f in FAILURES:
        print(f"  - {f}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
