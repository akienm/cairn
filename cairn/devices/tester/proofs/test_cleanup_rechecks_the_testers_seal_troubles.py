"""Proof for ticket 17b087f2483f — cairn cleanup clears the tester's seal troubles whose proof is proven
or gone.

Measured 2026-11-18 at the akiendelllinux house: bin/cmd/cleanup rechecks only the
inspector's finding troubles, and of 24 live troubles 9 of the tester's had a gone cause:
7 of 7 red-tickets-held-red-* name a proof validation_store.standing() reads proven, and 2 of 4
seal-red-* name a proof file that no longer exists. The tester now rechecks its own kinds and
emits the clear; the trouble device's drain folds it (Law 6, as in ticket 95557c2ed44f), and
that fold is proved at trouble's own address, so these teeth read the clears the recheck emits.

1. a seal-red for a proven proof is cleared;
2. a seal-red naming no proof file is cleared;
3. a seal-red for an existing, never-sealed proof gets no clear and is reported standing;
4. a red-tickets-held-red for a proven proof is cleared;
5. a red-tickets-held-red for an existing, never-sealed proof gets no clear.

The proven proof is chosen at run time: the first proof under cairn/devices/tester/proofs that
standing() reads proven (live data, so the tooth asserts the invariant, never a name). The
never-sealed proof lives in the scratch dir, handed to recheck through proof_roots. The clears
go to a recording raiser, never a store (ticket 0dbb6b5e940a: no trouble-device internals), so
this proof writes nothing outside its scratch dir. The recheck is imported inside ``main``.

Run bare:  PYTHONPATH=. python3 cairn/devices/tester/proofs/test_cleanup_rechecks_the_testers_seal_troubles.py
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
    "17b087f2483f": {
        "1": "a_seal_red_for_a_proven_proof_clears",
        "2": "a_seal_red_naming_no_proof_file_clears",
        "3": "a_seal_red_for_a_never_sealed_proof_stands",
        "4": "a_held_red_for_a_proven_proof_clears",
        "5": "a_held_red_for_a_never_sealed_proof_stands",
    },
}
GONE = "cairn/devices/tester/proofs/test_a_proof_that_was_never_written.py"
FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    if detail:
        print(f"        {detail[:300]}")
    if not ok:
        FAILURES.append(name)


class _Recorder:
    """Records each clear the recheck emits. The fold of a clear into the store is the trouble
    device's own write (Law 6), proved at its own address; a tester proof that built a
    TroubleDevice to read the fold reached past the store tool (ticket 0dbb6b5e940a), so these
    teeth read what the tester EMITS, as test_reseal_door.py's _FakeRaiser does."""

    def __init__(self):
        self.cleared: list[str] = []

    def clear_trouble(self, identity, *, by, what_changed):
        self.cleared.append(identity)


def _a_proven_proof() -> str | None:
    from cairn.tools.validation_store.validation_store import standing
    me = Path(__file__).resolve()
    for p in sorted((REPO / "cairn/devices/tester/proofs").glob("test_*.py")):
        if p.resolve() != me and standing(str(p)).get("proven"):
            return p.relative_to(REPO).as_posix()
    return None


def main() -> int:
    from cairn.tools.validation_store.validation_store import seal_trouble_identity
    try:
        from cairn.devices.tester.recheck import _slug, recheck
    except ImportError as exc:
        recheck, _slug, missing = None, None, f"{type(exc).__name__}: {exc}"

    proven = _a_proven_proof()
    if proven is None:
        check("a_proven_tester_proof_exists", False, "no proof under cairn/devices/tester/proofs reads proven")
        return 1

    with tempfile.TemporaryDirectory(prefix="cairn-seal-recheck-proof-") as tmp:
        here = Path(tmp) / "proofs"
        here.mkdir()
        unsealed = here / "test_never_sealed.py"
        unsealed.write_text("raise SystemExit(0)\n", encoding="utf-8")
        raised = {
            "1": seal_trouble_identity(REPO / proven),
            "2": seal_trouble_identity(REPO / GONE),
            "3": seal_trouble_identity(unsealed),
            "4": f"red_tickets:held:red:{proven}::a_tooth",
            "5": f"red_tickets:held:red:{unsealed}::a_tooth",
        }
        rec = _Recorder()
        if recheck is None:
            ids, got = dict(raised), {"error": missing}
        else:
            ids = {n: _slug(i) for n, i in raised.items()}
            got = recheck(list(raised.values()), proof_roots=[REPO, here], raiser=rec)
        show = json.dumps({"recheck": got, "cleared": rec.cleared})
        cleared = lambda n: ids[n] in rec.cleared
        reported = set((got or {}).get("standing") or []) if isinstance(got, dict) else set()

        check(PROVES["17b087f2483f"]["1"], recheck is not None and cleared("1"), show)
        check(PROVES["17b087f2483f"]["2"], recheck is not None and cleared("2"), show)
        check(PROVES["17b087f2483f"]["3"], recheck is not None and not cleared("3") and ids["3"] in reported, show)
        check(PROVES["17b087f2483f"]["4"], recheck is not None and cleared("4"), show)
        check(PROVES["17b087f2483f"]["5"], recheck is not None and not cleared("5") and ids["5"] in reported, show)

    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    for f in FAILURES:
        print(f"  - {f}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
