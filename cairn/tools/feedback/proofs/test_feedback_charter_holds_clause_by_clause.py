"""Proof for ticket 312be610152e — feedback's charter is proved clause by clause.

The plan names seven ways the tool would be wrong, one tooth each, keyed by its number.
The charter's eighth, "a route is accepted as a keyword argument at a finding-construction
site", was asked of Akien at outline 17.10.1 (Q#116, open-17442cfc2096) and retired
2026-11-18: "we don't have charters anymore. tooth measures the wrong thing, and was on your
side of the design divide." It never had a tooth here. The no-default-route clause, which
was 8, is outcome 7 since the renumbering, so its key moved from "8" to "7"; no tooth was
removed.

Every tooth runs feedback's public functions over a scratch root, never the live corpus, so
a tooth reds on the tool's behaviour and not on the day's population.

    python3 cairn/tools/feedback/proofs/test_feedback_charter_holds_clause_by_clause.py
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
    "312be610152e": {
        "1": "a_route_with_no_why_is_refused",
        "2": "a_route_that_does_not_resolve_is_refused",
        "3": "a_mention_is_not_a_producer_a_call_is",
        "4": "a_finding_built_in_proofs_enrols_no_one",
        "5": "a_healthy_world_passes_every_entry_and_opens",
        "6": "a_component_that_stops_constructing_leaves_no_entry",
        "7": "a_component_that_declares_no_route_gets_no_default",
    },
}

CALLS = "from cairn.tools.gate import gate\ngate.proved(identity='x', expected=1, actual=1)\n"
GOOD = {"to": "cairn/tools/feedback", "why": "the tool that owns the edge"}


def _fb():
    from cairn.tools.feedback import feedback
    return feedback


def _world(d: str, *, block=GOOD, body: str = CALLS, component: str = "cairn/tools/widget",
           extra: dict | None = None) -> str:
    """A scratch root: one component with a charter and one module, plus a route target."""
    fb = _fb()
    root = Path(d)
    comp = root / component
    comp.mkdir(parents=True, exist_ok=True)
    charter = {"component": comp.name, "role": "charter", "what": "x", "why": "y"}
    if block is not None:
        charter[fb.FIELD] = block
    (comp / fb.CHARTER).write_text(json.dumps(charter), encoding="utf-8")
    (comp / "widget.py").write_text(body, encoding="utf-8")
    for rel, text in (extra or {}).items():
        p = comp / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    (root / "cairn" / "tools" / "feedback").mkdir(parents=True, exist_ok=True)
    return str(root)


def _refused(fn) -> str | None:
    """The NoRoute message, or None when fn did not refuse."""
    try:
        fn()
    except _fb().NoRoute as e:
        return str(e)
    return None


# ── clause 1 ─────────────────────────────────────────────────────────────────

def a_route_with_no_why_is_refused():
    fb = _fb()
    for why in (None, "", "   "):
        block = {"to": GOOD["to"]} if why is None else {"to": GOOD["to"], "why": why}
        with tempfile.TemporaryDirectory() as d:
            root = _world(d, block=block)
            msg = _refused(lambda: fb.probes("cairn/tools/widget", root))
            assert msg and "why" in msg, f"a route with why={why!r} was accepted: {msg!r}"
            entry = fb.corpus_record(root)[0]
            assert entry["actual"] == "none", f"the record passed a why-less route: {entry}"


# ── clause 2 ─────────────────────────────────────────────────────────────────

def a_route_that_does_not_resolve_is_refused():
    fb = _fb()
    with tempfile.TemporaryDirectory() as d:
        root = _world(d, block={"to": "cairn/tools/nowhere_at_all", "why": "a place"})
        msg = _refused(lambda: fb.route("cairn/tools/widget", root))
        assert msg and "does not resolve" in msg, f"an unresolvable route was stored: {msg!r}"
        assert fb.corpus_record(root)[0]["actual"] == "none"


# ── clause 3 ─────────────────────────────────────────────────────────────────

def a_mention_is_not_a_producer_a_call_is():
    fb = _fb()
    mention = '"""This module discusses gate.proved( and inspected( but calls neither."""\nX = "gate.proved(a=1)"\n'
    with tempfile.TemporaryDirectory() as d:
        root = _world(d, body=mention)
        assert fb.producers(root) == [], f"a mention enrolled a producer: {fb.producers(root)}"
    with tempfile.TemporaryDirectory() as d:
        root = _world(d, body=CALLS)
        assert fb.producers(root) == ["cairn/tools/widget"], fb.producers(root)


# ── clause 4 ─────────────────────────────────────────────────────────────────

def a_finding_built_in_proofs_enrols_no_one():
    fb = _fb()
    with tempfile.TemporaryDirectory() as d:
        root = _world(d, block=None, body="X = 1\n", extra={"proofs/test_widget.py": CALLS})
        assert fb.producers(root) == [], f"a proof's fixture finding enrolled: {fb.producers(root)}"


# ── clause 5 ─────────────────────────────────────────────────────────────────

def a_healthy_world_passes_every_entry_and_opens():
    fb = _fb()
    from cairn.tools.gate import gate
    with tempfile.TemporaryDirectory() as d:
        root = _world(d)
        _world(d, component="cairn/machines/other")
        record = fb.corpus_record(root)
        assert len(record) == 2, f"one entry per producer expected: {record}"
        bad = [e for e in record if not gate.passed(e)]
        assert not bad, f"a healthy world carries a failing entry: {bad}"
        assert gate.opens(record), "a healthy world's gate stayed shut"


# ── clause 6 ─────────────────────────────────────────────────────────────────

def a_component_that_stops_constructing_leaves_no_entry():
    fb = _fb()
    with tempfile.TemporaryDirectory() as d:
        root = _world(d, block=None)
        _world(d, component="cairn/machines/other")
        before = {e["location"]: e["actual"] for e in fb.corpus_record(root)}
        assert before.get("cairn/tools/widget") == "none", before
        (Path(root) / "cairn/tools/widget/widget.py").write_text("X = 1\n", encoding="utf-8")
        after = [e["location"] for e in fb.corpus_record(root)]
        assert "cairn/tools/widget" not in after, f"the entry stayed instead of leaving: {after}"
        assert after == ["cairn/machines/other"], after


# ── clause 7 ─────────────────────────────────────────────────────────────────

def a_component_that_declares_no_route_gets_no_default():
    fb = _fb()
    with tempfile.TemporaryDirectory() as d:
        root = _world(d, block=None)
        assert fb.declared("cairn/tools/widget", root) is None
        msg = _refused(lambda: fb.route("cairn/tools/widget", root))
        assert msg and "declares no" in msg, f"route() answered without a declaration: {msg!r}"
        assert _refused(lambda: fb.probes("cairn/tools/widget", root)), "probes() defaulted a destination"
        entry = fb.corpus_record(root)[0]
        assert entry["actual"] == "none", entry
        assert "routes_to" not in entry.get("values", {}), f"the record named a default: {entry}"


TEETH = [a_route_with_no_why_is_refused, a_route_that_does_not_resolve_is_refused,
         a_mention_is_not_a_producer_a_call_is, a_finding_built_in_proofs_enrols_no_one,
         a_healthy_world_passes_every_entry_and_opens, a_component_that_stops_constructing_leaves_no_entry,
         a_component_that_declares_no_route_gets_no_default]


def main() -> int:
    failed = 0
    for t in TEETH:
        try:
            t()
            print(f"  green  {t.__name__}")
        except BaseException as e:  # noqa: BLE001
            failed += 1
            print(f"  RED    {t.__name__}: {type(e).__name__}: {str(e)[:400]}")
    print(f"\n{len(TEETH) - failed}/{len(TEETH)} teeth green")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
