"""Proof for ticket 59f7456dd9f5 — a bare call is a BaseShim hook, so the librarian wakes without
overriding the root-verb resolver.

Measured 2026-11-12: test_root_verb_vocabulary.py's test_every_roster_device_inherits_the_root_verbs
reds over cairn/devices/librarian/shim.py, whose LibrarianShim._resolve (ticket d832a24e5144,
Q#30) overrides BaseShim._resolve to wake the librarian on a bare call and hands every other argv
to super. The behaviour is right; the place is wrong.

1. clause_1_no_roster_shim_overrides_the_resolver: the standing inheritance tooth passes, run as
   written (pytest -k over test_root_verb_vocabulary.py);
2. clause_2_a_bare_librarian_still_wakes: d832a24e5144's proof
   (cairn/devices/librarian/proofs/test_a_bare_librarian_opens_its_chat.py) stays green;
3. clause_3_the_bare_answer_is_a_hook: a BaseShim subclass that overrides only _bare answers a
   bare call with it, and BaseShim's own bare answer is the device/class text it gave before.

Run bare:  PYTHONPATH=. python3 cairn/tools/base/proofs/test_a_bare_call_is_a_shim_hook.py
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {
    "59f7456dd9f5": {
        "1": "clause_1_no_roster_shim_overrides_the_resolver",
        "2": "clause_2_a_bare_librarian_still_wakes",
        "3": "clause_3_the_bare_answer_is_a_hook",
    },
}

FAILURES: list[str] = []
VOCAB = REPO / "cairn" / "tools" / "base" / "proofs" / "test_root_verb_vocabulary.py"
BARE_LIBRARIAN = REPO / "cairn" / "devices" / "librarian" / "proofs" / "test_a_bare_librarian_opens_its_chat.py"


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    if detail and not ok:
        print(f"        {detail[-1200:]}")
    if not ok:
        FAILURES.append(name)


def _env() -> dict:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO) + os.pathsep + env.get("PYTHONPATH", "")
    return env


def tooth_1() -> None:
    name = PROVES["59f7456dd9f5"]["1"]
    try:
        r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", str(VOCAB),
                            "-k", "test_every_roster_device_inherits_the_root_verbs"],
                           cwd=str(VOCAB.parent), env=_env(), capture_output=True, text=True, timeout=600)
        check(name, r.returncode == 0, r.stdout + r.stderr)
    except Exception as exc:  # noqa: BLE001 — a tooth's failure is its verdict
        check(name, False, f"{type(exc).__name__}: {exc}")


def tooth_2() -> None:
    name = PROVES["59f7456dd9f5"]["2"]
    try:
        r = subprocess.run([sys.executable, str(BARE_LIBRARIAN)], cwd=str(REPO), env=_env(),
                           capture_output=True, text=True, timeout=600)
        check(name, r.returncode == 0, r.stdout + r.stderr)
    except Exception as exc:  # noqa: BLE001
        check(name, False, f"{type(exc).__name__}: {exc}")


def tooth_3() -> None:
    name = PROVES["59f7456dd9f5"]["3"]
    try:
        from cairn.tools.base.shim import BaseShim

        class _Plain(BaseShim):
            device_id = "fixture-59f7"

        class _Hooked(_Plain):
            def _bare(self) -> dict:
                return {"exit": 0, "text": "fixture-59f7 bare hook", "data": None, "cached": None}

        plain = _Plain.__new__(_Plain)
        hooked = _Hooked.__new__(_Hooked)
        want_plain = {"exit": 0, "text": "device: fixture-59f7\nclass:  cairn/devices/fixture-59f7/",
                      "data": None, "cached": None}
        got_plain = plain._resolve([])
        got_hooked = hooked._resolve([])
        ok = ("_bare" in vars(BaseShim) and got_plain == want_plain
              and got_hooked.get("text") == "fixture-59f7 bare hook")
        check(name, ok, f"BaseShim has _bare={'_bare' in vars(BaseShim)} plain={got_plain!r} "
                        f"hooked={got_hooked!r}")
    except Exception as exc:  # noqa: BLE001
        check(name, False, f"{type(exc).__name__}: {exc}")


def main() -> int:
    tooth_1()
    tooth_2()
    tooth_3()
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    for f in FAILURES:
        print(f"  - {f}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
