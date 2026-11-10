"""CC's cross helper asks the harbor over the bus (ticket 5e11fadd63b3) — teeth a hollow build could not pass.

RULE 1 (outline 17.13.1): a device is reached through the bus. cairn/devices/cc/scripts/cross.py
imported the harbor master's clearance module and called it in CC's own process. It now asks the
harbor's clear verb (cairn/devices/cairn/machines/harbor_master/device.py _handle_clear), whose
actor is the envelope's sender. These teeth drive cross() with a recording bus and a recording
writer, so no live harbor is asked and no live ticket is written.
"""

from __future__ import annotations

import ast
import importlib.util
import io
import json
import sys
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROVES = {
    "5e11fadd63b3": {
        "1": "test_cross_imports_no_device",
        "2": "test_a_crossing_is_one_clear_request_sent_as_cc",
        "3": "test_a_refusal_exits_one_with_the_reason_and_writes_nothing",
        "4": "test_an_accepted_cursor_is_written_back_once",
        "5": "test_the_live_sieve_reads_no_row_for_cross",
    },
}

_CROSS = _REPO_ROOT / "cairn" / "devices" / "cc" / "scripts" / "cross.py"
_REL = "cairn/devices/cc/scripts/cross.py"
_ID = "aaaaaaaaaaaa"
_WF = "code-seam@v2: THINKME -> TICKETME -> [BUILDME:waiting] -> PROVEME -> PROVED"
_NEXT = "code-seam@v2: THINKME -> TICKETME -> BUILDME -> [PROVEME:waiting] -> PROVED"
_PROOF = "cairn/devices/cc/proofs/test_cross_asks_the_harbor_over_the_bus.py"


def _load():
    """cross.py as a module. argv is emptied first so a module that still crosses at import
    time raises instead of reaching for a live ticket."""
    saved = sys.argv
    sys.argv = [str(_CROSS)]
    try:
        spec = importlib.util.spec_from_file_location("cc_cross_under_proof", _CROSS)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    finally:
        sys.argv = saved
    assert callable(getattr(mod, "cross", None)), "cross.py has no cross() function"
    return mod


def _tickets() -> Path:
    d = scratch_dir("cross-proof") / "tickets"
    d.mkdir(parents=True)
    (d / f"{_ID}-a-boat.json").write_text(json.dumps({
        "id": _ID, "title": "a boat", "owner": "CC",
        "owning_intention": "cairn/devices/cc/intention+why.json",
        "workflow_and_state": _WF}), encoding="utf-8")
    return d


class _Bus:
    def __init__(self, body: dict):
        self.body, self.asked = body, []

    def request(self, **kw):
        self.asked.append(kw)
        return {"body": self.body}


class _Writer:
    def __init__(self):
        self.calls = []

    def __call__(self, plan, doc, **kw):
        self.calls.append((Path(plan), dict(doc), kw))


def _run(reply: dict):
    mod, bus, write = _load(), _Bus(reply), _Writer()
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        rc = mod.cross(_ID, "PROVEME", "a crossing under proof", [_PROOF],
                       bus=bus, tickets_dir=_tickets(), write=write)
    return rc, bus, write, out.getvalue(), err.getvalue()


def test_cross_imports_no_device():
    tree = ast.parse(_CROSS.read_text(encoding="utf-8"), filename=str(_CROSS))
    reach = []
    for node in ast.walk(tree):
        names = ([node.module] if isinstance(node, ast.ImportFrom) and node.module
                 else [a.name for a in node.names] if isinstance(node, ast.Import) else [])
        reach += [f"line {node.lineno}: {n}" for n in names if n.startswith("cairn.devices")]
    assert not reach, f"{_REL} imports a device: {reach}"


def test_a_crossing_is_one_clear_request_sent_as_cc():
    rc, bus, _w, _o, _e = _run({"accepted": True, "workflow": _NEXT})
    assert rc == 0
    assert len(bus.asked) == 1, f"expected one request, saw {len(bus.asked)}"
    kw = bus.asked[0]
    assert (kw.get("sender"), kw.get("to"), kw.get("verb")) == ("CC", "harbor_master", "clear"), kw
    body = kw.get("body") or {}
    dev = _REPO_ROOT / "cairn" / "devices" / "cc"
    assert body.get("workflow") == _WF
    assert body.get("target") == "PROVEME"
    assert body.get("boat_id") == _ID
    assert body.get("proven_by") == [_PROOF]
    assert Path(body.get("history_path", "")) == dev / "history.json"
    assert Path(body.get("state_path", "")) == dev / "state.json"
    assert "actor" not in body, "the actor is the envelope's sender; the body must not name one"


def test_a_refusal_exits_one_with_the_reason_and_writes_nothing():
    rc, _b, write, _o, err = _run({"accepted": False, "reason": "the proof does not cover it"})
    assert rc == 1, f"a refusal returned {rc}"
    assert "the proof does not cover it" in err
    assert write.calls == []


def test_an_accepted_cursor_is_written_back_once():
    rc, _b, write, out, _e = _run({"accepted": True, "workflow": _NEXT})
    assert rc == 0 and _NEXT in out
    assert len(write.calls) == 1, f"expected one write, saw {len(write.calls)}"
    _plan, doc, _kw = write.calls[0]
    assert doc["workflow_and_state"] == _NEXT
    rc2, _b2, write2, _o2, _e2 = _run({"accepted": True, "workflow": _WF})
    assert rc2 == 0 and write2.calls == [], "an unchanged cursor was written"


def test_the_live_sieve_reads_no_row_for_cross():
    from cairn.machines.build_inspector.inspector import encapsulation_breaches
    rows = [r for r in encapsulation_breaches(str(_REPO_ROOT)) if r.get("file") == _REL]
    assert not rows, f"the RULE 1 sieve reads {rows}"


if __name__ == "__main__":
    failed = 0
    for _name, _fn in list(globals().items()):
        if _name.startswith("test_") and callable(_fn):
            try:
                _fn()
                print(f"PASS {_name}")
            except BaseException as exc:  # noqa: BLE001 — every tooth reports, red or raising
                failed += 1
                print(f"FAIL {_name}: {type(exc).__name__}: {str(exc)[:300]}")
    sys.exit(1 if failed else 0)
