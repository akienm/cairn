"""Proof for ticket c24c5310a727 — the casting door refuses a sorted berth fired for another ticket.

Measured 2026-10-18: 05662f9e9bc9 was cast against the sorted berth fired for 6c9db321d638, and
the door admitted it, because its only binding was answers.workflow and answers.node_class, and
two code-seam@v2 casts always match. The stale berth's builder_check then rode onto the new
ticket as D1. A sorted berth carries the title it was fired under (the sorted contract: "the
ticket's name — the identifier it will be filed under"), so the door binds the berth to the cast
by that title, compared by slug as the filename is.

1. a berth titled for another ticket, cast as a ticket with a different title, is refused, and
   the lack names the berth's title;
2. a berth whose title is slug-equal to the doc's (case and punctuation differ) casts;
3. a berth with no title casts as before, judged by workflow and node_class alone.

Every tooth casts into a SCRATCH commons through ``artifact.set_diagnostic_roots``, restored
in ``finally``; ``cast_ticket`` is resolved when a tooth asks, never at import.

Run bare:  PYTHONPATH=. python3 cairn/tools/base/proofs/test_a_cast_refuses_another_tickets_sorted_berth.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {
    "c24c5310a727": {
        "1": "a_berth_titled_for_another_ticket_is_refused",
        "2": "a_berth_whose_title_is_slug_equal_casts",
        "3": "a_berth_with_no_title_casts_as_before",
    },
}

FAILURES: list[str] = []
WORKFLOW = "code-seam@v2: THINKME -> [TICKETME:waiting] -> BUILDME -> PROVEME -> PROVED"


def check(name: str, ok: bool, detail: str = "") -> None:
    # The detail rides its own line: the tester reads the whole PASS/FAIL line as the tooth name.
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    if detail:
        print(f"        {detail[:400]}")
    if not ok:
        FAILURES.append(name)


def _doc(tmp: Path, tid: str, title: str, berth_title: str | None) -> dict:
    """A complete cast whose sorted berth agrees on workflow and node_class, titled as given."""
    sorted_berth = tmp / f"sorted-{tid}.json"
    berth = {"skill": "sorted", "answers": {"workflow": WORKFLOW, "node_class": "code-seam"}}
    if berth_title is not None:
        berth["title"] = berth_title
        berth["answers"]["title"] = berth_title
    sorted_berth.write_text(json.dumps(berth), encoding="utf-8")
    intent_berth = tmp / "intent.json"
    intent_berth.write_text(json.dumps({"skill": "intent"}), encoding="utf-8")
    return {
        "id": tid, "title": title, "date": "2026-10-18",
        "owner": "codemother", "owning_intention": "cairn/tools/base/intention+why.json",
        "intention": "a cast binds its sorted berth", "why": "proof", "traces_to": "Law 7",
        "how": "cast_ticket", "falsifier": "DONE when another ticket's berth is refused",
        "node_class": "code-seam", "workflow_and_state": WORKFLOW,
        "watchme": "none, because cairn/tools/base/transitions.py",
        "sorted_berth": str(sorted_berth), "intent_berth": str(intent_berth),
    }


def _cast(tickets: Path, doc: dict):
    from cairn.tools.base.transitions import cast_ticket
    return cast_ticket(doc, actor="proof-actor", tickets_dir=tickets)


def tooth_1(tmp: Path, tickets: Path) -> None:
    from cairn.tools.base.transitions import CastRefused
    name = PROVES["c24c5310a727"]["1"]
    try:
        doc = _doc(tmp, "c24c0000a001", "berth-bind fixture B casts here",
                   "berth-bind fixture A was sorted here")
        try:
            path = _cast(tickets, doc)
        except CastRefused as exc:
            hit = [x for x in exc.lacks if "berth-bind fixture A was sorted here" in x]
            check(name, bool(hit) and not any(tickets.glob("c24c0000a001-*.json")),
                  json.dumps(exc.lacks))
        else:
            check(name, False, f"cast admitted another ticket's berth: {path.name}")
    except Exception as exc:  # noqa: BLE001 — a tooth's failure is its verdict
        check(name, False, f"{type(exc).__name__}: {exc}")


def tooth_2(tmp: Path, tickets: Path) -> None:
    name = PROVES["c24c5310a727"]["2"]
    try:
        path = _cast(tickets, _doc(tmp, "c24c0000a002", "Berth-bind fixture: it casts!",
                                   "berth bind fixture it casts"))
        check(name, path.is_file(), path.name)
    except Exception as exc:  # noqa: BLE001
        check(name, False, f"{type(exc).__name__}: {exc}")


def tooth_3(tmp: Path, tickets: Path) -> None:
    name = PROVES["c24c5310a727"]["3"]
    try:
        path = _cast(tickets, _doc(tmp, "c24c0000a003", "berth-bind fixture without a title", None))
        check(name, path.is_file(), path.name)
    except Exception as exc:  # noqa: BLE001
        check(name, False, f"{type(exc).__name__}: {exc}")


def main() -> int:
    from cairn.tools.artifact import artifact as A
    from cairn.tools.base.ticket_log import _LIVE_CHARTER
    from cairn.tools.scratch.scratch import scratch_dir
    tmp = scratch_dir("cairn-cast-berth-bind-proof-")
    commons = tmp / "CairnCommons"
    tickets = commons / "tickets"
    tickets.mkdir(parents=True)
    # The hollow's worktree has no CairnCommons beside it, so _LIVE_CHARTER (REPO.parent) is absent
    # there; the charter is then read from the home checkout, as hollow.py resolves the commons.
    charter = _LIVE_CHARTER if _LIVE_CHARTER.is_file() else (
        Path.home() / "dev" / "src" / "CairnCommons" / "tickets" / "_charter+why.json")
    (tickets / "_charter+why.json").write_bytes(charter.read_bytes())
    A.set_diagnostic_roots({"CairnCommons": commons, "cairn": REPO})
    try:
        tooth_1(tmp, tickets)
        tooth_2(tmp, tickets)
        tooth_3(tmp, tickets)
    finally:
        A.set_diagnostic_roots(None)
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    for f in FAILURES:
        print(f"  - {f}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
