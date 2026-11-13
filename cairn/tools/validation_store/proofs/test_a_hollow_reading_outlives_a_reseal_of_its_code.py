"""Proof for ticket 404d3f6f3d9b: a hollow reading outlives a reseal of the code it measured.

MEASURED 2026-11-13 on 5a37dd56fa45. Its Linux hollow reading landed on a standing seal taken on
Windows (fingerprint 1330...), while the Linux tree hashed 8318... over the same committed closure.
The pre-commit reseal at cairn 7bb6d6811 compared the new fingerprint with the PRIOR SEAL's, found
them different, and dropped a reading taken over exactly the code it measured. PROVED clearance then
refused hollow_evidence_absent and sent the boat to FIXME.

The carry now keys a reading's expiry to the code the reading measured: ``record_hollow`` stamps
the tree's fingerprint beside the reading (``hollow_fingerprint[t]``), and a new seal
carries each ticket's reading whose stamp, or the prior seal's fingerprint, equals its own.

This proof measures only cairn/tools/validation_store (RULE 1). It runs the store against a
scratch repo holding one fixture component; never the live validations.

  1. A READING ON A STALE SEAL SURVIVES A RESEAL OF THE SAME CODE.
  2. A READING OVER CODE THAT SINCE MOVED IS DROPPED.
  3. PER TICKET: A read before an edit and B after it; the reseal keeps B and drops A.

    bin/cairn test cairn/tools/validation_store/proofs/test_a_hollow_reading_outlives_a_reseal_of_its_code.py
"""
import shutil
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"404d3f6f3d9b": {"1": "a_reading_on_a_stale_seal_survives_a_reseal_of_the_same_code",
                           "2": "a_reading_over_code_that_since_moved_is_dropped",
                           "3": "the_carry_is_per_ticket"}}

COMP = "cairn/tools/fixture_hollow_carry"
CODE = f"{COMP}/code.py"
PROOF = f"{COMP}/proofs/test_fx.py"
PASS = 0
FAIL = 0


class _NoTrouble:
    """A trouble device that hears nothing: the fixture's verdicts never change, and if one did
    the live trouble store must not hear about a scratch component."""
    def raise_trouble(self, *a, **k):
        return None

    def clear_trouble(self, *a, **k):
        return None


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


class _World:
    """One scratch repo, the store's root repointed at it for the life of the world."""

    def __enter__(self):
        from cairn.tools.scratch.scratch import scratch_dir
        from cairn.tools.validation_store import validation_store as vs
        self.vs = vs
        self.base = scratch_dir("testing-404d3f6f3d9b-")
        (self.base / COMP / "proofs").mkdir(parents=True)
        (self.base / COMP / "validations").mkdir()
        (self.base / CODE).write_text("X = 1\n")
        (self.base / PROOF).write_text("from cairn.tools.fixture_hollow_carry.code import X\n")
        self._saved = vs._REPO_ROOT
        vs._REPO_ROOT = str(self.base)
        return self

    def __exit__(self, *exc):
        self.vs._REPO_ROOT = self._saved
        shutil.rmtree(self.base, ignore_errors=True)
        return False

    @property
    def proof(self) -> str:
        return str(self.base / PROOF)

    def edit(self, text: str) -> None:
        (self.base / CODE).write_text(text)

    def fp_now(self) -> str:
        return self.vs.source_fingerprint(self.proof, closure=[CODE, PROOF])

    def seal(self, fingerprint: str | None = None) -> None:
        """Persist a green seal over the fixture, at ``fingerprint`` (default: the tree's now)."""
        record = {
            "claim": "proof test_fx.py passes under python3",
            "caller": "cairn test",
            "date": "2026-11-13T00:00:00",
            "method": "fixture seal for ticket 404d3f6f3d9b",
            "verdict": "green",
            "evidence": {"returncode": 0, "seal": {"verdict": "open", "detail": "fixture"},
                         "source_fingerprint": fingerprint or self.fp_now(),
                         "fingerprint_closure": [CODE, PROOF]},
            "falsifier": "the fixture proof exits non-zero",
            "horizon": "valid until the proof file or the code it proves changes",
        }
        self.vs.persist_validation(record, proof_path=self.proof, trouble_device=_NoTrouble())

    def read(self, ticket: str) -> bool:
        return self.vs.record_hollow(self.proof, ticket, {CODE: ["t1"]},
                                     anchor={"commit": "0" * 40}, trouble_device=_NoTrouble())

    def standing(self) -> dict:
        return (self.vs.read_validations(self.proof)[-1].get("evidence") or {})


def a_reading_on_a_stale_seal_survives_a_reseal_of_the_same_code():
    with _World() as w:
        w.seal(fingerprint="f" * 64)            # a seal taken over bytes this tree no longer holds
        assert w.read("aaaaaaaaaaaa"), "record_hollow found no standing seal"
        w.seal()                                 # the hook's reseal, over the unchanged code
        ev = w.standing()
        assert "aaaaaaaaaaaa" in (ev.get("hollow") or {}), f"reading dropped: hollow={ev.get('hollow')}"
        assert "aaaaaaaaaaaa" in (ev.get("hollow_anchor") or {}), (
            f"anchor dropped: hollow_anchor={ev.get('hollow_anchor')}")


def a_reading_over_code_that_since_moved_is_dropped():
    with _World() as w:
        w.seal()
        assert w.read("aaaaaaaaaaaa"), "record_hollow found no standing seal"
        w.edit("X = 2\n")
        w.seal()
        ev = w.standing()
        assert "aaaaaaaaaaaa" not in (ev.get("hollow") or {}), (
            f"a reading over moved code was carried: hollow={ev.get('hollow')}")


def the_carry_is_per_ticket():
    with _World() as w:
        w.seal()
        assert w.read("aaaaaaaaaaaa"), "record_hollow found no standing seal"
        w.edit("X = 2\n")                        # A's reading is now about a tree that is gone
        assert w.read("bbbbbbbbbbbb"), "record_hollow found no standing seal"
        w.seal()
        hollow = w.standing().get("hollow") or {}
        assert "bbbbbbbbbbbb" in hollow and "aaaaaaaaaaaa" not in hollow, (
            f"want B kept and A dropped, got hollow keys {sorted(hollow)}")


def main() -> int:
    for name in PROVES["404d3f6f3d9b"].values():
        _tooth(name, globals()[name])
    print(f"\n{PASS}/{PASS + FAIL} teeth green")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
