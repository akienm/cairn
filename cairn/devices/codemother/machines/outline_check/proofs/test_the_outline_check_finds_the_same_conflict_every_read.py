"""Proof for ticket 0f4448fdb930: the outline check finds the same conflict on every read.

Measured 2026-11-20 on akiendelllinux over 784eb1e92866's ticket frozen beside this proof: one
live read named the 4.3.1.5.1.5.2 contradiction (a proof marking its rows as testing and deleting
them by hand, against "isolation comes from the store") on 2 of 5 reads with the old prompt,
once more under the clause suffix "4.3.1.5.1.5.2(5)" that the check then dropped as unresolved,
and on 4 of 5 with the clause-by-clause prompt. So one check could clear a real contradiction
by chance. The kept reader (D1, option (b)): the prompt names the clause-level test, a clause
suffix resolves to its line, and one check is the union of UNION valid reads.

These teeth call the LIVE reader (about $0.17 a read, measured), N=3 checks per ticket, inside a
scratch commons whose outline is a copy of today's requirements folder, so nothing they open
lands in the house commons. The testing line is found by its words, never by its number alone.

  1. on Linux, each of N=3 checks of 784eb1e92866 frozen names 4.3.1.5.1.5.2 among its conflicts;
  2. the same on Windows (akiendell);
  3. each of N=3 checks of the control 6cd13a3a5f42 frozen names no conflict.

    bin/cairn test cairn/devices/codemother/machines/outline_check/proofs/test_the_outline_check_finds_the_same_conflict_every_read.py
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parents[5]
sys.path.insert(0, str(_REPO))

PROOF_TIMEOUT_S = 1800   # 6 checks x 3 reads, about 25 s a read (measured), plus margin


class _CallTime:
    """The machine under proof, bound at CALL time, never at import: the hollow reading takes
    outline_check.py away, and a module-level import would die before the first tooth printed."""

    def __getattr__(self, name):
        import importlib
        return getattr(importlib.import_module(
            "cairn.devices.codemother.machines.outline_check.outline_check"), name)


OC = _CallTime()
from cairn.tools.artifact import artifact as door             # noqa: E402
from cairn.tools.scratch.scratch import scratch_dir          # noqa: E402

PROVES = {"0f4448fdb930": {
    "1": "test_every_read_of_784eb_names_the_testing_database_line",
    "2": "test_every_read_of_784eb_names_the_testing_database_line",
    "3": "test_no_read_of_the_control_names_a_conflict",
}}
N = 3
FIXTURES = _HERE / "fixtures"
REQUIREMENTS = "cairn/devices/cairn/requirements"
TESTING_LINE = "How the TESTING database works"


class World:
    """A scratch commons holding the two frozen tickets, beside a copy of today's outline."""

    def __init__(self):
        self.dir = scratch_dir("outline-check-every-read-")
        self.commons = self.dir / "CairnCommons"
        self.cairn = self.dir / "cairn"
        for d in ("tickets", "questions", "outline_checks"):
            (self.commons / d).mkdir(parents=True)
        # The check writes the questions it opens back onto the ticket through the door, which
        # refuses a key the charter does not declare; so the scratch charter declares every key
        # the frozen tickets carry (measured 2026-11-20: a five-field charter refused 784eb's).
        keys = {"questions"}
        for f in FIXTURES.glob("*.ticket.json"):
            keys.update(json.loads(f.read_text(encoding="utf-8")))
        (self.commons / "tickets" / "_charter+why.json").write_text(json.dumps({
            "plan_fields": sorted(keys),
            "log_kinds": {"field": {}, "phase_write": {}, "rehearsal": {}, "decision_retired": {}}}) + "\n")
        shutil.copytree(_REPO / REQUIREMENTS, self.cairn / REQUIREMENTS)
        for f in FIXTURES.glob("*.ticket.json"):
            tid = f.name.split(".")[0]
            shutil.copy2(f, self.commons / "tickets" / f"{tid}-frozen-fixture.json")
        door.set_diagnostic_roots({"cairn": self.cairn, "CairnCommons": self.commons})

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        door.set_diagnostic_roots(None)
        shutil.rmtree(self.dir, ignore_errors=True)

    def testing_line(self) -> str:
        entries = OC.parse(OC.outline_bytes(self.cairn / REQUIREMENTS).decode("utf-8"))
        hits = [e["number"] for e in entries if e["text"].startswith(TESTING_LINE)]
        assert len(hits) == 1, f"the outline carries {len(hits)} lines starting {TESTING_LINE!r}"
        return hits[0]

    def reads(self, tid: str) -> list[dict]:
        out = []
        for _ in range(N):
            rec = OC.check(tid, root=self.commons)["record"]
            assert rec["ran"], f"check of {tid} did not read: {rec.get('lacks')}"
            out.append(rec)
        return out


def _named(rec: dict) -> list[str]:
    return [c["number"] for c in rec["conflicts"]]


def test_every_read_of_784eb_names_the_testing_database_line():
    with World() as w:
        line = w.testing_line()
        recs = w.reads("784eb1e92866")
        named = [_named(r) for r in recs]
        missed = [i for i, n in enumerate(named) if line not in n]
        print(f"    [{sys.platform}] 784eb conflicts per check: {named}; "
              f"cost ${sum(m.get('cost_usd') or 0 for r in recs for m in r['meta']):.2f}")
        assert not missed, f"checks {missed} of {N} did not name {line}: {named}"


def test_no_read_of_the_control_names_a_conflict():
    with World() as w:
        recs = w.reads("6cd13a3a5f42")
        named = [_named(r) for r in recs]
        print(f"    [{sys.platform}] control conflicts per check: {named}")
        assert all(not n for n in named), f"the control named a conflict: {named}"


def main() -> int:
    fails = 0
    for name in dict.fromkeys(PROVES["0f4448fdb930"].values()):
        try:
            globals()[name]()
            print(f"  PASS  {name}")
        except Exception as exc:  # noqa: BLE001 — every tooth reports, none hides
            fails += 1
            print(f"  FAIL  {name}: {type(exc).__name__}: {exc}")
    print("red" if fails else "green")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
