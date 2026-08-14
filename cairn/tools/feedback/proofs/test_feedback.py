#!/usr/bin/env python3
"""Proof for cairn/tools/feedback — the -2- edge and the physics that it exists.

TEETH A HOLLOW BUILD COULD NOT PASS (Law 8):

  1. THE WHY IS FORCED BY THE SCHEMA, NOT BY ASKING NICELY. A build that accepts
     {"to": "..."} with no "why" passes every other tooth here and still ships the
     fillable field this corpus keeps catching. Case 3 requires the refusal.

  2. THE ROUTE MUST RESOLVE. A destination that is not on disk is indistinguishable
     from no destination the moment anyone delivers to it, so a build that stores the
     string and never checks it has built prose, not physics. Case 4 routes to a path
     that does not exist and requires NoRoute.

  3. USE vs MENTION, AND IT IS WHY THIS PARSES INSTEAD OF GREPPING. The population is
     "components that construct findings". A substring scan counts this very docstring —
     which says proved( and inspected( — and would enrol every module that merely
     DISCUSSES the rule. Case 6 is a module whose only occurrence is inside a string,
     and it must not be a producer.

  4. THE AUTHORING HAZARD, MEASURED n=4 IN ONE DAY (2026-08-13). A lane whose expected
     and actual cannot be == when it passes reds every HEALTHY subject. Case 8 builds a
     fixture where every producer IS routed and requires an all-passing record and an
     OPEN gate. Without it this tool could ship reddening the whole corpus forever and
     read as strict.

  5. ABSENT, NOT PASSED. A component that stops constructing findings leaves the record
     SHORTER, never cleaner. Case 9 removes the constructor and requires the entry to
     disappear rather than turn green.

INVARIANTS, NEVER SNAPSHOTS. Case 10 runs the live corpus, which grows. It asserts the
population is non-empty and every entry names a real directory — never "17", which would
red the day anyone adds or converts a component.

    python3 cairn/tools/feedback/proofs/test_feedback.py     # exit 0 = green
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from cairn.tools.feedback import feedback  # noqa: E402
from cairn.tools.gate import gate  # noqa: E402

FAILURES: list[str] = []
CHECKS = 0

GOOD = {"to": "cairn/tools/feedback", "why": "the tool that owns the edge"}


def check(label: str, condition: bool, detail: str = "") -> None:
    global CHECKS
    CHECKS += 1
    if condition:
        print(f"  ok   {label}")
    else:
        print(f"  RED  {label}" + (f"  — {detail}" if detail else ""))
        FAILURES.append(label)


def _expect_red(fn):
    try:
        fn()
    except feedback.NoRoute as e:
        return e
    return None


def _world(tmp: str, *, block=GOOD, body: str = "from x import gate\ngate.proved(a=1)\n",
           component: str = "cairn/tools/widget") -> str:
    """A fixture root carrying one component with a charter and one module."""
    root = Path(tmp)
    d = root / component
    d.mkdir(parents=True, exist_ok=True)
    charter = {"component": "widget", "role": "charter", "what": "x", "why": "y"}
    if block is not None:
        charter[feedback.FIELD] = block
    (d / feedback.CHARTER).write_text(json.dumps(charter), encoding="utf-8")
    (d / "widget.py").write_text(body, encoding="utf-8")
    # The route must resolve against THIS root, so give it something to resolve to.
    (root / "cairn" / "tools" / "feedback").mkdir(parents=True, exist_ok=True)
    return str(root)


def main() -> int:
    print("feedback — the edge a finding travels along\n")

    # ── 1-2. a declared, resolvable route ────────────────────────────────────
    with tempfile.TemporaryDirectory() as tmp:
        root = _world(tmp)
        check("a component with a resolvable route reports it",
              feedback.route("cairn/tools/widget", root) == "cairn/tools/feedback",
              feedback.route("cairn/tools/widget", root))
        check("and the block is readable on its own",
              feedback.declared("cairn/tools/widget", root) == GOOD)

    with tempfile.TemporaryDirectory() as tmp:
        root = _world(tmp, block=None)
        e = _expect_red(lambda: feedback.route("cairn/tools/widget", root))
        check("no declaration at all is NoRoute, and the refusal names the fix",
              e is not None and "declares no 'feedback'" in str(e) and '"to"' in str(e),
              f"got {e}")

    # ── 3. the why is forced by the schema ───────────────────────────────────
    with tempfile.TemporaryDirectory() as tmp:
        root = _world(tmp, block={"to": "cairn/tools/feedback"})
        e = _expect_red(lambda: feedback.route("cairn/tools/widget", root))
        check("a route with no WHY is refused — the field cannot be left blank",
              e is not None and "'why'" in str(e) and "missing" in str(e), f"got {e}")
        root = _world(tmp, block={"to": "cairn/tools/feedback", "why": "   "})
        e = _expect_red(lambda: feedback.route("cairn/tools/widget", root))
        check("and whitespace is not a why", e is not None, f"got {e}")

    # ── 4. the route must resolve ────────────────────────────────────────────
    with tempfile.TemporaryDirectory() as tmp:
        root = _world(tmp, block={"to": "cairn/tools/nowhere", "why": "invented"})
        e = _expect_red(lambda: feedback.route("cairn/tools/widget", root))
        check("a route to a path that does not exist is refused",
              e is not None and "does not resolve" in str(e), f"got {e}")

    # ── 5. resolves() on the real corpus ─────────────────────────────────────
    check("resolves() accepts a real component directory",
          feedback.resolves("cairn/tools/gate"))
    check("and rejects one nobody built", not feedback.resolves("cairn/tools/unicorn"))
    check("and rejects the empty string", not feedback.resolves(""))

    # ── 6. use vs mention — parsed, not grepped ──────────────────────────────
    with tempfile.TemporaryDirectory() as tmp:
        mention = '"""This module explains proved( and inspected( without calling them."""\nX = 1\n'
        root = _world(tmp, body=mention)
        check("a module that only MENTIONS the constructors is not a producer",
              feedback.producers(root) == [],
              f"got {feedback.producers(root)}")
        root = _world(tmp, body="from cairn.tools.gate import gate\nr = gate.proved(identity='x')\n")
        check("a module that CALLS one is",
              feedback.producers(root) == ["cairn/tools/widget"],
              f"got {feedback.producers(root)}")

    # ── 7. proofs are not segments ───────────────────────────────────────────
    with tempfile.TemporaryDirectory() as tmp:
        root = _world(tmp, body="X = 1\n")
        p = Path(root) / "cairn/tools/widget/proofs"
        p.mkdir(parents=True, exist_ok=True)
        (p / "test_widget.py").write_text("from x import gate\ngate.proved(a=1)\n",
                                          encoding="utf-8")
        check("a finding built inside proofs/ does not make the component a producer",
              feedback.producers(root) == [],
              "a proof builds fixture findings to test a door; it is not a segment "
              f"with an output anyone consumes — got {feedback.producers(root)}")

    # ── 8. THE AUTHORING HAZARD — a healthy world must go all-green ──────────
    with tempfile.TemporaryDirectory() as tmp:
        root = _world(tmp)
        record = feedback.corpus_record(root)
        check("a HEALTHY world produces a non-empty, all-passing record",
              bool(record) and all(gate.passed(e) for e in record),
              f"record={record}")
        check("and its gate OPENS", gate.opens(record))
        check("the passing entry states WHERE it routes, not merely that it does",
              record and record[0].get("values", {}).get("routes_to") == "cairn/tools/feedback",
              f"got {record[0] if record else None}")

    with tempfile.TemporaryDirectory() as tmp:
        root = _world(tmp, block=None)
        record = feedback.corpus_record(root)
        check("an unrouted producer yields exactly ONE failing entry, carrying its lack",
              len(record) == 1 and not gate.passed(record[0])
              and record[0]["values"]["lack"], f"record={record}")
        check("and the gate is CLOSED", not gate.opens(record))

    # ── 9. absent, not passed ────────────────────────────────────────────────
    with tempfile.TemporaryDirectory() as tmp:
        root = _world(tmp, block=None, body="X = 1\n")
        check("a component that stops constructing findings leaves NO entry, not a green one",
              feedback.corpus_record(root) == [],
              "the record must get SHORTER, never cleaner")

    # ── 10. the live corpus — invariants, never today's count ────────────────
    live = feedback.producers()
    check("the live corpus has finding-producers (the rule is not vacuous)", bool(live))
    check("every producer names a directory that exists and carries a charter",
          all((Path(feedback.CAIRN_ROOT) / c / feedback.CHARTER).is_file() for c in live),
          f"live={live}")
    rec = feedback.corpus_record()
    check("the live record has exactly one entry per producer",
          len(rec) == len(live), f"{len(rec)} entries for {len(live)} producers")
    check("and every entry carries the compare's preconditions",
          all(all(k in e for k in gate.REQUIRED) for e in rec))

    print()
    print(f"{CHECKS - len(FAILURES)}/{CHECKS} green")
    if FAILURES:
        print("RED:")
        for f in FAILURES:
            print(f"  - {f}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
