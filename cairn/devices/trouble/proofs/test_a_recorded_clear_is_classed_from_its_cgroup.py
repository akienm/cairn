"""Proof for ticket 4f8d11706516 — a recorded clear is classed from the cgroup it stored.

Measured 2026-10-12: Akien's nine who-writes-what clears from his Konsole tab are on the
record with by 'akien', the kernel-measured cgroup
.../app-org.kde.konsole-78471.scope/tab(3360690).scope, and class 'unknown' (the leaf-only
classifier b63f5bbbef89 fixes). _handle_clears served hand_class from the STORED class, so
the counting block never learned those rows. It now derives the class from the stored
cgroup when the stored class is 'unknown', and serves every other stored class as stored.

1. a clear stored {by: akien, hand: {class: unknown, cgroup: <the tab path>}} is served
   hand_class akien;
2. a stored cc with an app-*.scope cgroup is served cc, and an unknown with no cgroup is
   served unknown;
3. the trouble file's bytes are unchanged after the read.

Scratch store, written as files. The device is reached at call time, so a reverted build
reds a tooth rather than crashing the import.

Run bare:  PYTHONPATH=. python3 cairn/devices/trouble/proofs/test_a_recorded_clear_is_classed_from_its_cgroup.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {
    "4f8d11706516": {
        "1": "an_unknown_clear_with_a_tab_cgroup_is_served_akien",
        "2": "a_stored_cc_and_a_cgroupless_unknown_are_served_as_stored",
        "3": "the_trouble_file_is_not_rewritten",
    },
}

APP = "/user.slice/user-1000.slice/user@1000.service/app.slice"
TAB = f"{APP}/app-org.kde.konsole-78471.scope/tab(3360690).scope"
FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    # The detail rides its own line: the tester reads the whole PASS/FAIL line as the tooth name.
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    if detail:
        print(f"        {detail[:300]}")
    if not ok:
        FAILURES.append(name)


def _trouble(ident: str, cleared_by: list[dict]) -> dict:
    return {"id": ident, "standing": "CLEARED", "count": 1, "why": "a proof's trouble",
            "notified": ["cc"], "cleared_by": cleared_by}


def _store(store: Path) -> dict[str, Path]:
    store.mkdir(parents=True, exist_ok=True)
    files = {
        "tab": _trouble("recorded-clear-proof-tab", [
            {"by": "akien", "at": "2026-10-12T22:00:00+00:00", "hand": {"class": "unknown", "cgroup": TAB}}]),
        "cc": _trouble("recorded-clear-proof-cc", [
            {"by": "cc", "at": "2026-10-12T22:00:00+00:00",
             "hand": {"class": "cc", "cgroup": f"{APP}/app-org.kde.konsole-7e5c.scope"}}]),
        "bare": _trouble("recorded-clear-proof-bare", [
            {"by": "akien", "at": "2026-10-12T22:00:00+00:00", "hand": {"class": "unknown"}}]),
    }
    out = {}
    for key, t in files.items():
        p = store / f"{t['id']}.json"
        p.write_text(json.dumps(t, indent=2) + "\n", encoding="utf-8")
        out[key] = p
    return out


def _served(store: Path) -> dict[str, str]:
    from cairn.devices.trouble.trouble import TroubleDevice
    dev = TroubleDevice(root=str(store))
    dev.set_diagnostic_receiver(None)
    rows = dev.declared_verbs()["clears"]({"sender": "proof", "body": {"prefix": "recorded-clear-proof-"}})["clears"]
    return {r["id"]: r["hand_class"] for r in rows}


def main() -> int:
    from cairn.tools.scratch.scratch import scratch_dir
    store = scratch_dir("cairn-proof-recorded-clear-class-") / "store"
    paths = _store(store)
    before = {k: p.read_bytes() for k, p in paths.items()}
    served: dict[str, str] = {}
    try:
        served = _served(store)
    except Exception as exc:  # noqa: BLE001 — a read that cannot run reds every tooth, loudly
        print(f"  the clears read raised {type(exc).__name__}: {exc}")
    ids = {k: f"recorded-clear-proof-{k}" for k in paths}
    check(PROVES["4f8d11706516"]["1"], served.get(ids["tab"]) == "akien", json.dumps(served))
    check(PROVES["4f8d11706516"]["2"],
          served.get(ids["cc"]) == "cc" and served.get(ids["bare"]) == "unknown", json.dumps(served))
    after = {k: p.read_bytes() for k, p in paths.items()}
    check(PROVES["4f8d11706516"]["3"], bool(served) and after == before,
          f"changed: {[k for k in paths if after[k] != before[k]]}")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    for f in FAILURES:
        print(f"  - {f}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
