"""Proof: the seal's reach mapping asks component_of once per distinct file, not once per log entry.

Ticket aa7a1d7fa671, child of 2b3d842bc118. Measured 2026-11-06: a nested `bin/cairn test` run
inside 2b3d842bc118's hollow worktree logged 68,388 reach entries over 278 distinct files (one
`files` list per python process, 246 processes). `_reached` called `address.component_of` once
per ENTRY, and every call re-walks the whole component tree (component_dirs), so mapping one
proof took minutes (3,000 raw entries: 7.2 s; the 278 unique: 0.8 s), the eleven-proof suite
inside clause 6 blew its 1500 s budget, and the hollow reading of 2b3d842bc118 could not seal.

Two teeth, one per falsifier clause:

  1. _reached over 1,200 entries naming two distinct cairn files (one spelled three ways: plain,
     with a '..' hop, through a symlink) calls component_of exactly three times — the proof's own
     component once, then once per distinct real path.
  2. the map it returns equals the map over the two files given once each: the dedup changes
     the cost, never the answer (a guard).

    python3 cairn/devices/tester/proofs/test_reach_mapping_walks_each_file_once.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {
    "aa7a1d7fa671": {
        "1": "tooth_1_each_distinct_file_is_mapped_once",
        "2": "tooth_2_the_map_is_unchanged",
    },
}

FAILURES: list[str] = []
_PROOF = Path(__file__).resolve()
_ADDRESS = REPO / "cairn" / "tools" / "base" / "address.py"
_DEVICE = REPO / "cairn" / "devices" / "tester" / "device.py"


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}", flush=True)
    if detail:
        print(f"        {detail[:900]}", flush=True)
    if not ok:
        FAILURES.append(name)


def _spellings() -> list[str]:
    """address.py three ways: plain, through a '..' hop, through a symlink in a scratch dir."""
    from cairn.tools.scratch.scratch import scratch_dir
    link = scratch_dir("testing-aa7a1d7fa671-") / "address_link.py"
    if not link.exists():
        os.symlink(_ADDRESS, link)
    hop = REPO / "cairn" / "tools" / "base" / ".." / "base" / "address.py"
    return [str(_ADDRESS), str(hop), str(link)]


def _counted(files: list[str]) -> tuple[dict | None, int]:
    import cairn.tools.base.address as address
    from cairn.devices.tester import device
    real = address.component_of
    calls = [0]

    def counting(*a, **kw):
        calls[0] += 1
        return real(*a, **kw)

    address.component_of = counting
    try:
        got = device._reached(files, _PROOF)
    finally:
        address.component_of = real
    return got, calls[0]


def tooth_1() -> None:
    name = PROVES["aa7a1d7fa671"]["1"]
    try:
        spell = _spellings()
        files = (spell * 300) + ([str(_DEVICE)] * 300)  # 1,200 entries, two distinct real paths
        got, calls = _counted(files)
        check(name, calls == 3, f"{len(files)} entries, 2 distinct files: component_of called "
                                f"{calls} times (want 3: own + one per distinct file); map={got}")
    except Exception as exc:  # noqa: BLE001 — a tooth's failure is its verdict
        check(name, False, f"{type(exc).__name__}: {exc}")


def tooth_2() -> None:
    name = PROVES["aa7a1d7fa671"]["2"]
    try:
        spell = _spellings()
        many, _ = _counted((spell * 300) + ([str(_DEVICE)] * 300))
        once, _ = _counted([str(_ADDRESS), str(_DEVICE)])
        ok = many == once and isinstance(once, dict) and "cairn/tools/base" in once \
            and not any(k.startswith("cairn/devices/tester") for k in once)
        check(name, ok, f"many={many} once={once}")
    except Exception as exc:  # noqa: BLE001
        check(name, False, f"{type(exc).__name__}: {exc}")


def main() -> int:
    tooth_1()
    tooth_2()
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    for f in FAILURES:
        print(f"  - {f}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
