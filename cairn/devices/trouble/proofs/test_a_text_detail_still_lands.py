"""Proof for ticket 114002d08c46 — the trouble drain folds a raise whose detail is text.

Measured 2026-10-11: a raise emission whose ``values.detail`` is a string (written by hand on
2026-10-09, before the raiser refused one — ticket 93a9cc0f7677) made every drain refuse it
with "TypeError: 'str' object is not a mapping", and the refusal held that home's raise
watermark, so nothing behind it could land. Logs are not edited; the fold reads the emission
as it is.

1. a raise emission with values.detail='some text' drains to folded (no refused), the trouble
   exists, and its detail text equals 'some text' whole;
2. the raise watermark advances past it: a later raise in the same home folds in the same
   drain, and a second drain re-folds nothing.

Scratch roots only. The text emission is written with ``emit`` (the raiser's own lane), not
``raise_trouble``, because after 93a9cc0f7677 the raiser refuses it — exactly the record
already on disk that this fold must still carry. ``TroubleShim`` is imported inside the teeth.

Run bare:  PYTHONPATH=. python3 cairn/devices/trouble/proofs/test_a_text_detail_still_lands.py
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
    "114002d08c46": {
        "1": "a_text_detail_folds_whole",
        "2": "the_watermark_moves_past_it",
    },
}

TEXT = "some text — carried whole, never truncated, " + "x" * 400
FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail[:300]}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def _raiser(world: Path):
    from cairn.tools.base.diagnostic import DiagnosticBase

    class _Fixture(DiagnosticBase):
        @property
        def diagnostic_device(self) -> str:
            return "a_fixture_component"

    d = _Fixture()
    d.set_diagnostic_roots({k: world for k in ("repo", "commons", "instance")})
    return d


def _store(store: Path):
    from cairn.devices.trouble.trouble import TroubleDevice
    dev = TroubleDevice(root=str(store))
    dev.set_diagnostic_receiver(None)
    return dev


def main() -> int:
    from cairn.devices.trouble.shim import TroubleShim
    with tempfile.TemporaryDirectory(prefix="cairn-text-detail-proof-") as tmp:
        world, store = Path(tmp) / "world", Path(tmp) / "store"
        r = _raiser(world)
        # the record already on disk: a raise whose detail is text, then a well-formed one
        r.emit("raise_trouble", pointer="a-text-detail-raise",
               values={"why": "raised by hand with a string detail", "detail": TEXT})
        r.raise_trouble("a-later-raise", why="lands behind the text one", detail={"n": 1})

        roots = {k: world for k in ("repo", "commons", "instance")}
        shim = TroubleShim(roots=roots, root=str(store))
        first = shim.drain()
        live = {t["id"]: t for t in _store(store).live()}
        texts = [o.get("text") for o in (live.get("a-text-detail-raise") or {}).get("occurrences", [])]
        check(PROVES["114002d08c46"]["1"],
              first.get("outcome") == "ok" and not first.get("refused")
              and "a-text-detail-raise" in live and texts == [TEXT],
              json.dumps({"refused": first.get("refused"), "live": sorted(live), "texts_ok": texts == [TEXT]}))
        second = shim.drain()
        check(PROVES["114002d08c46"]["2"],
              "a-later-raise" in live and len(first.get("folded") or []) == 2
              and second.get("folded") == [] and not second.get("refused"),
              json.dumps({"first_folded": len(first.get("folded") or []), "second": second})[:300])
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    for f in FAILURES:
        print(f"  - {f}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
