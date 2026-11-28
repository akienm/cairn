"""Proof for ticket 3f544e08a783: the outline check loses no conflict a read names.

TOOTH DECISION (outline 9.4.2.3.7.6, corrosion 17.11.6; Akien 2026-10-27, outline 9.3.5.1.3: "the point
is not to make sure the cheap models produce the same output each time ... The point is to get as many
questions as possible answered before it goes to the building process"). This file was ticket
0f4448fdb930's proof that the check finds THE SAME conflict on EVERY read, and that no read of the
control names one. Those teeth measured the wrong thing: a repeatable read is not the aim, and a
conflict one read names that another does not is a question gained, never noise to filter out. The code
was not wrong, the tooth was. Retired: "every check names the line" and "no read of the control names a
conflict". Kept and rewritten as what the outline asks:

Measured 2026-11-20 on akiendelllinux over 784eb1e92866's ticket frozen beside this proof: one live
read named the 4.3.1.5.1.5.2 contradiction on 2 of 5 reads with the old prompt, 4 of 5 with the
clause-by-clause prompt. One check is the union of UNION valid reads (0f4448fdb930, D1 option (b)).

These teeth call the LIVE reader (about $0.17 a read, measured), N=3 checks per ticket, inside a
scratch commons whose outline is a copy of today's requirements folder, so nothing they open
lands in the house commons. The testing line is found by its words, never by its number alone.

  1. across N=3 checks of 784eb1e92866 frozen, the testing-database line is named by at least one, so
     the contradiction is not lost in aggregate;
  2. every conflict any check of the control 6cd13a3a5f42 frozen names stands on a real outline line, so
     a conflict named there is a question to answer, never a failure and never dropped.

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

PROVES = {"3f544e08a783": {
    "1": "test_the_union_of_the_checks_of_784eb_names_the_testing_database_line",
    "2": "test_every_conflict_the_control_is_named_stands_on_a_real_outline_line",
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


def test_the_union_of_the_checks_of_784eb_names_the_testing_database_line():
    with World() as w:
        line = w.testing_line()
        recs = w.reads("784eb1e92866")
        named = [_named(r) for r in recs]
        print(f"    [{sys.platform}] 784eb conflicts per check: {named}; "
              f"cost ${sum(m.get('cost_usd') or 0 for r in recs for m in r['meta']):.2f}")
        assert any(line in n for n in named), f"no check of {N} named {line}: {named}"


def test_every_conflict_the_control_is_named_stands_on_a_real_outline_line():
    with World() as w:
        numbers = {e["number"] for e in OC.parse(OC.outline_bytes(w.cairn / REQUIREMENTS).decode("utf-8"))}
        named = [_named(r) for r in w.reads("6cd13a3a5f42")]
        print(f"    [{sys.platform}] control conflicts per check: {named}")
        stray = [n for ns in named for n in ns if n not in numbers]
        assert not stray, f"the control named a line the outline does not carry: {stray}"


def main() -> int:
    fails = 0
    for name in dict.fromkeys(PROVES["3f544e08a783"].values()):
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
