"""Proof for ticket 32f500e517d7 — a certification reaches CC's bus address.

A gate's certification is a gated, ticket-carrying crossing journaled by emit. When one lands in
class-space, the probes standing in that gate's folder
(``<instance>/devices/codemother/0/machines/gate/<gate>/probes/*.json``) fire as 'personal' bus
envelopes. The teeth:

  1. envelope shape — one personal envelope per certified probe, sender 'cairn', addressed to the
     probe's ``to``, verb 'certified', ``why`` the rendered message, the body carrying ticket,
     component, from, to, direction, fingerprint, probe and message.
  2. unreachable bus — a bus that refuses the connection raises nothing out of fire, and emit
     still journals and returns its new string when the firing itself raises (D5).
  3. testing mark — with CAIRN_TESTER_TEST_ID set the body carries ``testing``: mark(id).
  4. a missing or empty probe folder posts nothing.
  5. a malformed probe is skipped with a stderr line while a good sibling still fires.
  6. seed writes one probe into each of the six gates and a second seed rewrites nothing.
  7. clear removes only the named device's probes.
  8. a crossing outside class-space (a proof's temp history) fires nothing (D12).
  9. emit calls the firing after the journal is written, with the crossing's own record.

The subject (``cairn.tools.base.gate_probes``) is bound at call time inside each tooth, so a
hollow build reds tooth by tooth instead of crashing the import.

    bin/cairn test cairn/tools/base/proofs/test_a_certification_fires_the_gates_probes.py
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROVES = {"32f500e517d7": {
    "1": "tooth_a_certified_probe_posts_one_personal_envelope",
    "2": "tooth_an_unreachable_bus_never_gates_the_crossing",
    "3": "tooth_a_test_run_marks_the_envelope",
}}

PASS = 0
FAIL = 0

_CODE_SEAM = "code-seam@v2: THINKME -> TICKETME -> [BUILDME] -> PROVEME -> PROVED"
_CROSSING = dict(ticket="aaaaaaaaaaaa", component="cairn/tools/example", from_="BUILDME",
                 to="PROVEME", direction="forward", fingerprint="f" * 64)


class _Bus:
    """The stand-in bus: records every post, or refuses the connection like a dead socket."""

    def __init__(self, refuse: bool = False) -> None:
        self.posts: list[dict] = []
        self.refuse = refuse

    def post(self, **kw):
        if self.refuse:
            raise ConnectionRefusedError("no bus process listens (proof stand-in)")
        self.posts.append(kw)
        return {"id": len(self.posts)}


def _roots() -> dict:
    d = scratch_dir("cairn-gate-probes-proof-")
    return {"repo": d / "repo", "commons": d / "commons", "instance": d / "instance"}


def _probe_file(roots: dict, gate: str, stem: str, payload) -> Path:
    from cairn.tools.base import gate_probes
    folder = gate_probes.probes_dir(gate, roots)
    folder.mkdir(parents=True, exist_ok=True)
    p = folder / f"{stem}.json"
    p.write_text(payload if isinstance(payload, str) else json.dumps(payload))
    return p


def _fire(roots, bus, **over):
    from cairn.tools.base import gate_probes
    kw = {**_CROSSING, **over}
    return gate_probes.fire(**kw, roots=roots, bus=bus)


def tooth_a_certified_probe_posts_one_personal_envelope():
    roots, bus = _roots(), _Bus()
    _probe_file(roots, "prove", "cc", {"to": "cc", "event": "certified", "message": "{event} on {ticket}"})
    _probe_file(roots, "prove", "other", {"to": "x", "event": "watched", "message": "{event}"})
    _fire(roots, bus)
    assert len(bus.posts) == 1, f"expected one post for one certified probe, got {bus.posts}"
    env = bus.posts[0]
    want = {"sender": "cairn", "to": "cc", "channel": "personal", "verb": "certified",
            "why": "certified on aaaaaaaaaaaa"}
    for k, v in want.items():
        assert env.get(k) == v, f"envelope {k}={env.get(k)!r}, want {v!r}"
    body = env.get("body") or {}
    want_body = {"ticket": "aaaaaaaaaaaa", "component": "cairn/tools/example", "from": "BUILDME",
                 "to": "PROVEME", "direction": "forward", "fingerprint": "f" * 64,
                 "probe": "cc", "message": "certified on aaaaaaaaaaaa"}
    for k, v in want_body.items():
        assert body.get(k) == v, f"body {k}={body.get(k)!r}, want {v!r}"


def tooth_an_unreachable_bus_never_gates_the_crossing():
    roots = _roots()
    _probe_file(roots, "prove", "cc", {"to": "cc", "event": "certified", "message": "{event} on {ticket}"})
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        _fire(roots, _Bus(refuse=True))
    assert "aaaaaaaaaaaa" in err.getvalue() and "ConnectionRefusedError" in err.getvalue(), \
        f"a refused post must leave one stderr line naming the ticket and the error; got {err.getvalue()!r}"

    from cairn.tools.base import gate_probes, transitions
    from cairn.tools.charter import projector
    d = scratch_dir("cairn-gate-probes-emit-")
    hist, state = f"{d}/history.json", f"{d}/state.json"

    def boom(*a, **k):
        raise RuntimeError("the firing exploded (proof stand-in)")

    real = gate_probes.fire_crossing
    gate_probes.fire_crossing = boom
    try:
        with contextlib.redirect_stderr(io.StringIO()) as e2:
            new = transitions.emit(_CODE_SEAM, "PROVEME", history_path=hist, state_path=state)
    finally:
        gate_probes.fire_crossing = real
    assert "[PROVEME" in new, f"emit's return changed under a failing firing: {new!r}"
    assert len(projector.read_history(hist)) == 1, "the journal must stand when the firing fails"
    assert "RuntimeError" in e2.getvalue(), f"a failing firing must be loud on stderr; got {e2.getvalue()!r}"


def tooth_a_test_run_marks_the_envelope():
    from cairn.tools.base.testing_mark import FIELD, mark
    roots, bus = _roots(), _Bus()
    _probe_file(roots, "build", "cc", {"to": "cc", "event": "certified", "message": "{event} on {ticket}"})
    old = os.environ.get("CAIRN_TESTER_TEST_ID")
    os.environ["CAIRN_TESTER_TEST_ID"] = "proof-run-1"
    try:
        _fire(roots, bus, from_="TICKETME", to="BUILDME")
    finally:
        if old is None:
            os.environ.pop("CAIRN_TESTER_TEST_ID", None)
        else:
            os.environ["CAIRN_TESTER_TEST_ID"] = old
    assert len(bus.posts) == 1, f"expected one post, got {bus.posts}"
    got = (bus.posts[0].get("body") or {}).get(FIELD)
    assert got == mark("proof-run-1"), f"body {FIELD}={got!r}, want {mark('proof-run-1')!r}"


def tooth_a_missing_or_empty_folder_posts_nothing():
    from cairn.tools.base import gate_probes
    roots, bus = _roots(), _Bus()
    _fire(roots, bus)
    gate_probes.probes_dir("prove", roots).mkdir(parents=True)
    _fire(roots, bus)
    assert bus.posts == [], f"no probe stands, yet the bus saw {bus.posts}"


def tooth_a_malformed_probe_is_skipped_loudly():
    roots, bus = _roots(), _Bus()
    _probe_file(roots, "prove", "a-not-json", "{nope")
    _probe_file(roots, "prove", "b-bad-key", {"to": "cc", "event": "certified", "message": "{secret}"})
    _probe_file(roots, "prove", "c-no-to", {"event": "certified", "message": "{event}"})
    _probe_file(roots, "prove", "d-good", {"to": "cc", "event": "certified", "message": "{event} on {ticket}"})
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        _fire(roots, bus)
    assert [p["to"] for p in bus.posts] == ["cc"] and bus.posts[0]["body"]["probe"] == "d-good", \
        f"only the good sibling fires; bus saw {bus.posts}"
    for stem in ("a-not-json", "b-bad-key", "c-no-to"):
        assert stem in err.getvalue(), f"malformed {stem} skipped silently; stderr {err.getvalue()!r}"


def tooth_seed_writes_six_and_is_idempotent():
    from cairn.tools.base import gate_probes
    roots = _roots()
    written = gate_probes.seed("cc", roots)
    files = sorted(p for g in gate_probes.GATES for p in gate_probes.probes_dir(g, roots).glob("*.json"))
    assert len(gate_probes.GATES) == 6 and len(files) == 6, f"want 6 probe files, got {files}"
    assert sorted(written) == files, f"seed reports {written}, disk holds {files}"
    for f in files:
        assert json.loads(f.read_text()) == {"to": "cc", "event": "certified", "message": "{event} on {ticket}"}
    before = {f: f.stat().st_mtime_ns for f in files}
    again = gate_probes.seed("cc", roots)
    assert again == [] and {f: f.stat().st_mtime_ns for f in files} == before, "a second seed rewrote a probe"


def tooth_clear_removes_only_the_named_device():
    from cairn.tools.base import gate_probes
    roots = _roots()
    gate_probes.seed("cc", roots)
    keep = _probe_file(roots, "build", "librarian", {"to": "librarian", "event": "certified", "message": "{event}"})
    removed = gate_probes.clear("cc", roots)
    assert len(removed) == 6, f"clear removed {removed}"
    left = [p for g in gate_probes.GATES for p in gate_probes.probes_dir(g, roots).glob("*.json")]
    assert left == [keep], f"clear must leave exactly the other device's probe; left {left}"


def tooth_a_crossing_outside_class_space_fires_nothing():
    from cairn.tools.base import gate_probes
    roots, bus = _roots(), _Bus()
    _probe_file(roots, "prove", "cc", {"to": "cc", "event": "certified", "message": "{event} on {ticket}"})
    record = {"from": "BUILDME", "to": "PROVEME", "direction": "forward", "fingerprint": "f" * 64}
    outside = scratch_dir("cairn-gate-probes-outside-") / "history.json"
    gate_probes.fire_crossing(record, str(outside), "aaaaaaaaaaaa", roots=roots, bus=bus)
    gate_probes.fire_crossing(record, None, "aaaaaaaaaaaa", roots=roots, bus=bus)
    inside = roots["repo"] / "cairn/tools/example/history.json"
    gate_probes.fire_crossing(record, str(inside), None, roots=roots, bus=bus)
    assert bus.posts == [], f"a temp-dir, pathless or ticketless crossing posted {bus.posts}"
    gate_probes.fire_crossing(record, str(inside), "aaaaaaaaaaaa", roots=roots, bus=bus)
    assert len(bus.posts) == 1 and bus.posts[0]["body"]["component"] == "cairn/tools/example", \
        f"a class-space crossing must post once, naming its component; got {bus.posts}"


def tooth_emit_fires_after_the_journal():
    from cairn.tools.base import gate_probes, transitions
    from cairn.tools.charter import projector
    d = scratch_dir("cairn-gate-probes-emit-")
    hist, state = f"{d}/history.json", f"{d}/state.json"
    seen = []

    def spy(record, history_path, ticket, **kw):
        seen.append((dict(record), history_path, ticket, len(projector.read_history(history_path))))

    real = gate_probes.fire_crossing
    gate_probes.fire_crossing = spy
    try:
        transitions.emit(_CODE_SEAM, "PROVEME", history_path=hist, state_path=state)
    finally:
        gate_probes.fire_crossing = real
    assert len(seen) == 1, f"emit must call the firing once per journaled crossing; saw {seen}"
    record, path, _ticket, journaled = seen[0]
    assert path == hist and journaled == 1, "the firing must come after the journal append"
    assert record.get("fingerprint") == projector.read_history(hist)[0]["fingerprint"], \
        "the firing must receive the crossing's own journaled record"


def _tooth(name, fn):
    global PASS, FAIL
    try:
        fn()
        PASS += 1
        print(f"  GREEN {name}")
    except Exception as exc:  # noqa: BLE001 — a tooth's failure is its verdict
        FAIL += 1
        print(f"  RED   {name}: {type(exc).__name__}: {str(exc)[:300]}")


TEETH = [
    tooth_a_certified_probe_posts_one_personal_envelope,
    tooth_an_unreachable_bus_never_gates_the_crossing,
    tooth_a_test_run_marks_the_envelope,
    tooth_a_missing_or_empty_folder_posts_nothing,
    tooth_a_malformed_probe_is_skipped_loudly,
    tooth_seed_writes_six_and_is_idempotent,
    tooth_clear_removes_only_the_named_device,
    tooth_a_crossing_outside_class_space_fires_nothing,
    tooth_emit_fires_after_the_journal,
]


if __name__ == "__main__":
    for t in TEETH:
        _tooth(t.__name__, t)
    print(f"\n{PASS} passed, {FAIL} failed out of {len(TEETH)}")
    raise SystemExit(1 if FAIL else 0)
