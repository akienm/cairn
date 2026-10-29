#!/usr/bin/env python3
"""Proof for ticket 284798998ab0 — the ticket file is nothing but the build plan.

Akien 2026-10-29 (open-c7809a745bf7): *"three parts. record it and reshape the ticket."* A
ticket is three files beside each other: the PLAN ``<id>-<slug>.json`` (what a builder builds
from), the STATE ``<id>-<slug>.state.json`` (what a gate or door reads or writes as the ticket
moves) and the LOG ``<id>-<slug>.log.jsonl`` (everything else). The split is the census
``CairnCommons/measurements/2026-10-29-ticket-fields-plan-state-log.json``.

Teeth (D9), each over a scratch tickets dir whose store charter is the live one with its three
field lists set to the census, so the door, the jurisdiction rule and ticket_file are measured
apart from the migration that narrows the live charter (D11):
  (1) the LIVE charter's plan_fields, state_fields and log_fields equal the census's plan,
      state and log, pairwise disjoint;
  (2) the door writes a state file of state keys only, refuses one holding a plan key, and
      refuses a plan write holding a state key;
  (3) write_ticket then read_ticket returns the doc it was given, every state key in the state
      file and none in the plan;
  (4) plans() over a dir holding a plan, its .state.json, its .log.jsonl and the charter yields
      the plan alone;
  (5) split then reconstruct over a fixture v2 ticket returns the doc it split;
  (6) set_phase changes the state file and leaves the plan's bytes, and design_sha of them,
      unchanged.
The one declared tooth, ``test_the_ticket_is_three_files``, is the six together (the
falsifier carries no numbered clauses). ``--corpus`` instead checks the live store: every plan
carries only plan_fields, every state file only state_fields, every plan has its state file.

    bin/cairn test cairn/tools/base/proofs/test_the_ticket_is_three_files.py
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

COMMONS = REPO.parent / "CairnCommons"
LIVE_CHARTER = COMMONS / "tickets" / "_charter+why.json"
CENSUS = COMMONS / "measurements" / "2026-10-29-ticket-fields-plan-state-log.json"

PROVES = {"284798998ab0": {"all": "test_the_ticket_is_three_files"}}

TEETH = ("test_the_charter_declares_three_disjoint_field_sets",
         "test_the_door_keys_the_state_file_by_state_fields",
         "test_write_then_read_returns_the_doc_split_across_two_files",
         "test_plans_yields_the_plan_alone",
         "test_split_then_reconstruct_returns_the_doc",
         "test_a_crossing_moves_only_the_state_file")
FAILURES: list[str] = []
CURSOR = "code-seam@v2: THINKME -> TICKETME -> [BUILDME:waiting] -> PROVEME -> PROVED"


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def _census() -> dict:
    return json.loads(CENSUS.read_text(encoding="utf-8"))["summary"]


def _tickets(commons: Path) -> Path:
    t = commons / "tickets"
    t.mkdir(parents=True)
    charter = json.loads(LIVE_CHARTER.read_text(encoding="utf-8"))
    c = _census()
    charter["plan_fields"], charter["state_fields"], charter["log_fields"] = c["plan"], c["state"], c["log"]
    (t / "_charter+why.json").write_text(json.dumps(charter, indent=2, ensure_ascii=False) + "\n",
                                          encoding="utf-8")
    return t


def _doc(tid: str) -> dict:
    return {"id": tid, "title": "a proof world ticket", "intention": "a fixture", "why": "a proof",
            "how": "none", "falsifier": "none", "decisions": [{"n": 1, "text": "D1: a line"}],
            "date": "2026-10-29", "owner": "CC", "node_class": "code-seam",
            "workflow_and_state": CURSOR, "watchme": "none, because a fixture",
            "questions": ["open-000000000000"]}


def _state_keys() -> set:
    return set(_census()["state"])


def test_the_charter_declares_three_disjoint_field_sets() -> None:
    charter, c = json.loads(LIVE_CHARTER.read_text(encoding="utf-8")), _census()
    got = {k: charter.get(f"{k}_fields") for k in ("plan", "state", "log")}
    equal = all(got[k] == c[k] for k in got)
    disjoint = equal and not (set(c["plan"]) & set(c["state"]) or set(c["plan"]) & set(c["log"])
                              or set(c["state"]) & set(c["log"]))
    check(TEETH[0], equal and disjoint,
          "; ".join(f"{k}_fields {len(v) if v else v} vs census {len(c[k])}" for k, v in got.items()))


def test_the_door_keys_the_state_file_by_state_fields(A, t: Path) -> None:
    good = t / "aaaa1111bbbb-door.state.json"
    wrote = refused_state = refused_plan = False
    try:
        A.write_json(good, {"workflow_and_state": CURSOR, "owner": "CC"}, verb="phase", why="proof")
        wrote = good.is_file()
    except A.Refused as exc:
        print(f"    a state-only state file was refused: {exc}")
    try:
        A.write_json(t / "aaaa1111bbbb-bad.state.json", {"how": "a plan key"}, verb="phase", why="proof")
    except A.Refused:
        refused_state = not (t / "aaaa1111bbbb-bad.state.json").exists()
    try:
        A.write_json(t / "aaaa1111bbbb-bad.json", {"id": "aaaa1111bbbb", "workflow_and_state": CURSOR},
                     verb="cast", why="proof")
    except A.Refused:
        refused_plan = not (t / "aaaa1111bbbb-bad.json").exists()
    check(TEETH[1], wrote and refused_state and refused_plan,
          f"state file written {wrote}; plan key in state refused {refused_state}; "
          f"state key in plan refused {refused_plan}")


def test_write_then_read_returns_the_doc_split_across_two_files(TF, t: Path) -> None:
    plan = t / "bbbb2222cccc-round.json"
    doc = _doc("bbbb2222cccc")
    TF.write_ticket(plan, doc, False, True, why="proof")
    on_plan = json.loads(plan.read_text(encoding="utf-8"))
    on_state = json.loads(TF.state_path(plan).read_text(encoding="utf-8"))
    back = TF.read_ticket(plan)
    sk = _state_keys()
    ok = (back == doc and not (set(on_plan) & sk) and set(on_state) == set(doc) & sk)
    check(TEETH[2], ok, f"plan keys {sorted(on_plan)}; state keys {sorted(on_state)}; equal {back == doc}")


def test_plans_yields_the_plan_alone(TF, tmp: Path) -> None:
    d = tmp / "plans-world"
    d.mkdir()
    for name in ("cccc3333dddd-p.json", "cccc3333dddd-p.state.json", "cccc3333dddd-p.log.jsonl",
                 "_charter+why.json"):
        (d / name).write_text("{}\n", encoding="utf-8")
    got = [p.name for p in TF.plans(d)]
    found = TF.find_ticket("cccc3333dddd", d)
    check(TEETH[3], got == ["cccc3333dddd-p.json"] and found is not None and found.name == got[0],
          f"plans {got}; find_ticket {found}")


def test_split_then_reconstruct_returns_the_doc(L, TF, t: Path) -> None:
    plan = t / "dddd4444eeee-split.json"
    doc = {**_doc("dddd4444eeee"), "an_ad_hoc_trail_field": {"said": "trail"}}
    plan.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    out = L.split(plan, actor="proof", why="proof: split")
    after = json.loads(plan.read_text(encoding="utf-8"))
    state = json.loads(TF.state_path(plan).read_text(encoding="utf-8"))
    back = L.reconstruct(after, L.read_log(plan), state)
    sk = _state_keys()
    ok = (back == doc and not (set(after) & sk) and set(state) == set(doc) & sk
          and (out.get("moved") or {}).get("state") == len(set(doc) & sk))
    check(TEETH[4], ok, f"moved {out.get('moved')}; plan {sorted(after)}; lossless {back == doc}")


def test_a_crossing_moves_only_the_state_file(T, TF, R, t: Path) -> None:
    plan = t / "eeee5555ffff-phase.json"
    TF.write_ticket(plan, _doc("eeee5555ffff"), False, True, why="proof")
    pb, sb = plan.read_bytes(), TF.state_path(plan).read_bytes()
    saved = TF._TICKETS
    TF._TICKETS = t
    try:
        T.set_phase(CURSOR, "hold", release="CLAUDE.md", actor="proof", ticket="eeee5555ffff")
    finally:
        TF._TICKETS = saved
    ok = (plan.read_bytes() == pb and R.design_sha(plan.read_bytes()) == R.design_sha(pb)
          and TF.state_path(plan).read_bytes() != sb and "workflow_and_state" not in json.loads(pb))
    check(TEETH[5], ok, f"plan unchanged {plan.read_bytes() == pb}; state moved {TF.state_path(plan).read_bytes() != sb}")


def corpus() -> int:
    from cairn.tools.base import ticket_file as TF
    from cairn.tools.base import ticket_log as L
    tickets = COMMONS / "tickets"
    plan_f, state_f = set(L.plan_fields(LIVE_CHARTER)), set(L.state_fields(LIVE_CHARTER))
    bad = []
    for p in TF.plans(tickets):
        extra = set(json.loads(p.read_text(encoding="utf-8"))) - plan_f
        s = TF.state_path(p)
        if extra:
            bad.append(f"{p.name}: plan carries {sorted(extra)}")
        if not s.is_file():
            bad.append(f"{p.name}: no state file")
        elif set(json.loads(s.read_text(encoding="utf-8"))) - state_f:
            bad.append(f"{s.name}: state carries {sorted(set(json.loads(s.read_text(encoding='utf-8'))) - state_f)}")
    for line in bad[:40]:
        print(f"  FAIL  {line}")
    print(f"{'GREEN' if not bad else 'RED — ' + str(len(bad)) + ' finding(s)'} over {len(TF.plans(tickets))} plans")
    return 1 if bad else 0


def main() -> int:
    if "--corpus" in sys.argv[1:]:
        return corpus()
    test_the_charter_declares_three_disjoint_field_sets()
    try:
        from cairn.tools.artifact import artifact as A
        from cairn.tools.base import ticket_file as TF
        from cairn.tools.base import ticket_log as L
        from cairn.tools.base import transitions as T
        from cairn.machines.rehearsal import rehearsal as R
    except Exception as exc:  # noqa: BLE001 — the reverted world is the case this handles
        print(f"the subject does not load: {exc!r}")
        for n in TEETH[1:]:
            check(n, False, "subject absent")
    else:
        teeth = (lambda t, tmp: test_the_door_keys_the_state_file_by_state_fields(A, t),
                 lambda t, tmp: test_write_then_read_returns_the_doc_split_across_two_files(TF, t),
                 lambda t, tmp: test_plans_yields_the_plan_alone(TF, tmp),
                 lambda t, tmp: test_split_then_reconstruct_returns_the_doc(L, TF, t),
                 lambda t, tmp: test_a_crossing_moves_only_the_state_file(T, TF, R, t))
        with tempfile.TemporaryDirectory(prefix="cairn-ticket-three-files-proof-") as d:
            tmp = Path(d)
            commons = tmp / "CairnCommons"
            t = _tickets(commons)
            A.set_diagnostic_roots({"CairnCommons": commons, "cairn": tmp / "cairn",
                                    "parked": tmp / "parked"})
            try:
                for name, tooth in zip(TEETH[1:], teeth):
                    try:
                        tooth(t, tmp)
                    except Exception as exc:  # noqa: BLE001 — the reason is the record
                        check(name, False, f"{type(exc).__name__}: {str(exc)[:200]}")
            finally:
                A.set_diagnostic_roots(None)
    check("test_the_ticket_is_three_files", not FAILURES, f"{len(FAILURES)} of {len(TEETH)} teeth red")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
