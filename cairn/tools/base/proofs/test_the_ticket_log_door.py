#!/usr/bin/env python3
"""Proof that a ticket's trail is appended to its log through one door (76da3a283277).

A ticket is two files (Akien 2026-10-10, "Flat plan + .log.jsonl"): the plan, "always the
'current what to do'", and the log beside it, "the questions and the answering of them".
``cairn.tools.base.ticket_log`` is the log's one door; the store charter declares the plan's
fields and the log's kinds once.

Teeth, one per falsifier clause (PROVES below), on a scratch tickets dir holding a copy of
the LIVE store charter (so the declared sets under proof are the real ones):
  (1) append_log twice lands two lines in order, each {kind, at, actor, **body}; read_log
      returns both; an undeclared kind and a body key 'kind' raise ValueError and write nothing;
  (2) split over a fixture v1 ticket (an ad-hoc field, two phase_writes, a rehearsal pointer,
      one retired and one live decision) leaves a plan of plan_fields only, no phase_writes,
      no rehearsal, only the live decision — and plan + log reconstructs the v1 doc exactly;
  (3) a second split is a no-op: both files byte-identical;
  (4) set_phase on a fixture ticket appends one 'phase_write' line whose record.workflow is
      the plan's new workflow_and_state, and the plan carries no phase_writes key;
  (5) cast_ticket with an extra non-plan field is refused naming it; without it, it casts.
29569fca68a3 (1), the plan keeps its one statement of intent:
  a v1 plan with no 'intention' splits into a plan whose 'intention' is its string 'intent'
  (over 'what'), else its string 'what' — a blank 'intention' counts as none and one that
  states something is kept; a dict 'intent' is never promoted; a plan split before
  the rename takes it from its log on the next split; each rename is one 'renamed' line; every
  plan + log still reconstructs its v1 doc exactly, and a further split is a no-op.

    bin/cairn test cairn/tools/base/proofs/test_the_ticket_log_door.py
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

LIVE_CHARTER = REPO.parent / "CairnCommons" / "tickets" / "_charter+why.json"

PROVES = {"76da3a283277": {
    "1": "test_append_log_lands_lines_in_order_and_refuses_what_it_must",
    "2": "test_split_moves_the_trail_and_reconstructs_the_v1_doc",
    "3": "test_a_second_split_is_a_no_op",
    "4": "test_set_phase_appends_its_record_to_the_log",
    "5": "test_cast_ticket_refuses_a_field_outside_the_plan",
}, "29569fca68a3": {
    "1": "test_split_names_the_plans_one_intention",
}}

FAILURES: list[str] = []
CURSOR = "code-seam@v2: THINKME -> TICKETME -> [BUILDME:waiting] -> PROVEME -> PROVED"


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def _tickets(tmp: Path) -> Path:
    t = tmp / "tickets"
    t.mkdir()
    shutil.copyfile(LIVE_CHARTER, t / "_charter+why.json")
    return t


def _v1(tid: str) -> dict:
    return {
        "id": tid, "title": "a proof world v1 ticket", "date": "2026-10-10", "owner": "CC",
        "intention": "a fixture", "why": "a proof", "how": "none", "falsifier": "none",
        "node_class": "code-seam", "workflow_and_state": CURSOR,
        "an_ad_hoc_trail_field": {"said": "something only a reader-mind opens"},
        "phase_writes": [
            {"act": "set_phase", "actor": "CC", "phase": "hold", "release": "x",
             "standing": "BUILDME", "workflow": CURSOR, "at": "2026-10-01T09:00:00"},
            {"act": "set_phase", "actor": "CC", "phase": "waiting", "release": None,
             "standing": "BUILDME", "workflow": CURSOR, "at": "2026-10-02T09:00:00"}],
        "rehearsal": "rehearsals/abc123def456-20261010T000000.json",
        "decisions": [
            {"n": 1, "text": "the retired line", "retired": {"by": "CC", "at": "2026-10-03",
                                                             "because": "folded", "into": 2}},
            {"n": 2, "text": "the live line"}],
    }


def _write(path: Path, doc: dict) -> None:
    path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def test_append_log_lands_lines_in_order_and_refuses_what_it_must(L, t: Path) -> None:
    plan = t / "aaa111bbb222-append.json"
    _write(plan, {"id": "aaa111bbb222", "workflow_and_state": CURSOR})
    kinds = sorted(L.log_kinds(plan))
    k = "field" if "field" in kinds else kinds[0]
    L.append_log(plan, k, {"field": "one", "value": 1}, actor="proof", why="proof: line 1")
    L.append_log(plan, k, {"field": "two", "value": 2}, actor="proof", why="proof: line 2")
    lines = L.read_log(plan)
    shaped = (len(lines) == 2 and [x["value"] for x in lines] == [1, 2]
              and all({"kind", "at", "actor"} <= set(x) and x["actor"] == "proof" for x in lines))
    before = L.log_path(plan).read_bytes()
    refused = []
    for kind, body in (("no_such_kind", {"x": 1}), (k, {"kind": "smuggled"})):
        try:
            L.append_log(plan, kind, body, actor="proof", why="proof: must refuse")
        except ValueError:
            refused.append(L.log_path(plan).read_bytes() == before)
    check("test_append_log_lands_lines_in_order_and_refuses_what_it_must",
          shaped and refused == [True, True], f"lines {lines!r:.160} refusals {refused}")


def _state(plan: Path) -> dict | None:
    """The state file split moved the state keys into (ticket 284798998ab0), when one stands."""
    from cairn.tools.base.ticket_file import state_path
    sp = state_path(plan)
    return json.loads(sp.read_text(encoding="utf-8")) if sp.is_file() else None


def test_split_moves_the_trail_and_reconstructs_the_v1_doc(L, t: Path) -> None:
    plan = t / "abc123def456-v1.json"
    v1 = _v1("abc123def456")
    _write(plan, v1)
    out = L.split(plan, actor="proof", why="proof: split")
    after = json.loads(plan.read_text(encoding="utf-8"))
    fields = set(L.plan_fields(plan))
    clean = (set(after) <= fields and "phase_writes" not in after and "rehearsal" not in after
             and after.get("decisions") == [{"n": 2, "text": "the live line"}])
    back = L.reconstruct(after, L.read_log(plan), _state(plan))
    check("test_split_moves_the_trail_and_reconstructs_the_v1_doc", clean and back == v1,
          f"moved {out.get('moved')}; plan keys outside: {sorted(set(after) - fields)}; "
          f"lossless {back == v1}")


def test_a_second_split_is_a_no_op(L, t: Path) -> None:
    plan = t / "abc123def456-v1.json"
    log = L.log_path(plan)
    pb, lb = plan.read_bytes(), log.read_bytes()
    out = L.split(plan, actor="proof", why="proof: split again")
    check("test_a_second_split_is_a_no_op",
          plan.read_bytes() == pb and log.read_bytes() == lb and not out.get("moved"),
          f"moved {out.get('moved')}")


def test_set_phase_appends_its_record_to_the_log(L, T, t: Path) -> None:
    plan = t / "cafe00beef00-phase.json"
    _write(plan, {"id": "cafe00beef00", "title": "phase", "workflow_and_state": CURSOR})
    from cairn.tools.base import ticket_file as TF
    saved = TF._TICKETS
    TF._TICKETS = t
    try:
        new = T.set_phase(CURSOR, "hold", release="CLAUDE.md", actor="proof", ticket="cafe00beef00")
    finally:
        TF._TICKETS = saved
    doc = TF.read_ticket(plan)  # the cursor and release are state fields (284798998ab0)
    pw = L.read_log(plan, "phase_write")
    ok = (len(pw) == 1 and pw[0]["record"]["workflow"] == doc["workflow_and_state"] == new
          and "phase_writes" not in doc and doc.get("release") == "CLAUDE.md")
    check("test_set_phase_appends_its_record_to_the_log", ok,
          f"log phase_writes {len(pw)}; plan keys {sorted(doc)}")


def test_cast_ticket_refuses_a_field_outside_the_plan(T, t: Path, tmp: Path) -> None:
    sorted_b = tmp / "sorted.json"
    sorted_b.write_text(json.dumps({"skill": "sorted", "answers": {
        "workflow": CURSOR, "node_class": "code-seam"}}))
    doc = {"id": "0123456789ab", "title": "a cast", "date": "2026-10-10", "owner": "CC",
           "owning_intention": "x", "intention": "x", "why": "x", "traces_to": "x",
           "how": "x", "falsifier": "x", "node_class": "code-seam",
           "workflow_and_state": CURSOR, "watchme": "x", "sorted_berth": str(sorted_b),
           "intent_berth": str(sorted_b), "an_ad_hoc_trail_field": "trail"}
    named = False
    try:
        T.cast_ticket(dict(doc), actor="proof", tickets_dir=t)
    except T.CastRefused as exc:
        named = "an_ad_hoc_trail_field" in str(exc)
    landed_bad = list(t.glob("0123456789ab-*.json"))
    doc.pop("an_ad_hoc_trail_field")
    try:
        p = T.cast_ticket(dict(doc), actor="proof", tickets_dir=t)
        cast_ok = p.is_file()
    except T.CastRefused as exc:
        cast_ok = False
        named = named and False
        print(f"    the clean cast was refused: {exc}")
    check("test_cast_ticket_refuses_a_field_outside_the_plan",
          named and not landed_bad and cast_ok,
          f"refusal named the field {named}; extra cast landed {bool(landed_bad)}; clean cast {cast_ok}")


def test_split_names_the_plans_one_intention(L, t: Path) -> None:
    base = {k: v for k, v in _v1("x").items() if k != "intention"}
    cases = {  # id: (v1 extras, the intention the plan must carry, the renamed-from key)
        "feed00000001": ({"intent": "the intent", "what": "the what"}, "the intent", "intent"),
        "feed00000002": ({"intent": {"challenge": "trail"}, "what": "the what"}, "the what", "what"),
        "feed00000003": ({"intent": {"challenge": "trail"}}, None, None),
        "feed00000005": ({"intention": "", "what": "the what"}, "the what", "what"),
        "feed00000006": ({"intention": "kept", "intent": "not this"}, "kept", None),
    }
    bad = []
    for tid, (extra, want, frm) in cases.items():
        plan = t / f"{tid}-intent.json"
        v1 = {**base, "id": tid, **extra}
        _write(plan, v1)
        L.split(plan, actor="proof", why="proof: split names the intention")
        doc = json.loads(plan.read_text(encoding="utf-8"))
        ren = L.read_log(plan, "renamed")
        pb, lb = plan.read_bytes(), L.log_path(plan).read_bytes()
        again = L.split(plan, actor="proof", why="proof: split again")
        ok = (doc.get("intention") == want
              and [(x["from"], x["to"]) for x in ren] == ([(frm, "intention")] if frm else [])
              and L.reconstruct(doc, L.read_log(plan), _state(plan)) == v1
              and not again.get("moved") and plan.read_bytes() == pb
              and L.log_path(plan).read_bytes() == lb)
        if not ok:
            bad.append(f"{tid}: intention {doc.get('intention')!r} renamed {ren!r:.120}")
    # a plan split before the rename existed: v2-clean, its 'what' only in the log
    plan = t / "feed00000004-presplit.json"
    v1 = {**base, "id": "feed00000004", "what": "the old what"}
    _write(plan, {k: v for k, v in v1.items() if k not in ("what", "phase_writes", "rehearsal")})
    L.append_log(plan, "field", {"field": "what", "value": "the old what"}, actor="proof",
                 why="proof: the trail an earlier split left")
    L.split(plan, actor="proof", why="proof: the rename reaches a split plan")
    doc = json.loads(plan.read_text(encoding="utf-8"))
    want = {k: v for k, v in v1.items() if k not in ("phase_writes", "rehearsal")}
    if not (doc.get("intention") == "the old what"
            and L.reconstruct(doc, L.read_log(plan), _state(plan)) == want):
        bad.append(f"feed00000004: intention {doc.get('intention')!r}")
    check("test_split_names_the_plans_one_intention", not bad, "; ".join(bad))


def main() -> int:
    try:
        from cairn.tools.base import ticket_log as L
        from cairn.tools.base import transitions as T
        from cairn.tools.artifact import artifact as A
    except Exception as exc:  # noqa: BLE001 — the reverted world is the case this handles
        print(f"the subject does not load: {exc!r}")
        for n in [*PROVES["76da3a283277"].values(), *PROVES["29569fca68a3"].values()]:
            check(n, False, "subject absent")
        return 1
    try:
        with tempfile.TemporaryDirectory(prefix="cairn-ticket-log-door-proof-") as d:
            tmp = Path(d)
            commons = tmp / "CairnCommons"
            commons.mkdir()
            t = _tickets(commons)
            A.set_diagnostic_roots({"CairnCommons": commons, "cairn": tmp / "cairn",
                                    "parked": tmp / "parked"})
            try:
                test_append_log_lands_lines_in_order_and_refuses_what_it_must(L, t)
                test_split_moves_the_trail_and_reconstructs_the_v1_doc(L, t)
                test_a_second_split_is_a_no_op(L, t)
                test_set_phase_appends_its_record_to_the_log(L, T, t)
                test_cast_ticket_refuses_a_field_outside_the_plan(T, t, tmp)
                test_split_names_the_plans_one_intention(L, t)
            finally:
                A.set_diagnostic_roots(None)
    except Exception as exc:  # noqa: BLE001
        print(f"the teeth could not run to the end: {exc!r}")
        for n in [*PROVES["76da3a283277"].values(), *PROVES["29569fca68a3"].values()]:
            if n not in FAILURES:
                check(n, False, f"aborted: {type(exc).__name__}")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
