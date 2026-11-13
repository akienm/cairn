"""Teeth for ticket 61416fbb8013 — the build's tool calls are evidence about the chart.

Every tooth builds a fixture transcript (raw JSONL, written the way Claude Code writes it:
``json.dumps`` with ``/`` left alone or escaped as the tooth needs) and a fixture ticket doc
with bounds and decisions, then asks skills/sail/toolcalls. Hermetic: nothing reads the live
transcript or the live commons. toolcalls is imported INSIDE each tooth, so a missing module
reds teeth instead of breaking the import.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.proof_coverage.proof_coverage import print_teeth_main  # noqa: E402

PROVES = {
    "61416fbb8013": {
        "1": "test_a_write_outside_bounds_in_is_a_surprise",
        "2": "test_a_write_into_bounds_out_is_a_contradiction",
        "3": "test_every_call_is_counted_and_a_foreseen_read_makes_no_finding",
        "4": "test_an_escaped_path_is_read_by_parsing",
        "5": "test_the_merged_packet_passes_the_reflection_door",
    },
}

TID = "abcdef012345"
ROOT = "/repo/cairn/"
TICKET = {
    "id": TID,
    "bounds": {"in": ["skills/x/mod.py", "skills/x/proofs/test_mod.py"],
               "out": ["cairn/devices/codemother"]},
    "decisions": [{"n": 1, "text": "D1", "writes_to": ["skills/x/mod.py"], "reads": ["skills/x/README.md"]}],
}


def _rec(name: str, inp: dict, at: str) -> dict:
    return {"type": "assistant", "timestamp": at,
            "message": {"role": "assistant", "content": [
                {"type": "text", "text": "working"},
                {"type": "tool_use", "id": "t", "name": name, "input": inp}]}}


def _transcript(records: list[dict], *, escape_slash: bool = False) -> Path:
    d = Path(tempfile.mkdtemp(prefix="toolcalls-"))
    p = d / "session.jsonl"
    lines = []
    for r in records:
        s = json.dumps(r)
        if escape_slash:
            s = s.replace("/", "\\u002f")
        lines.append(s)
    lines.insert(1, json.dumps({"type": "user", "message": {"role": "user", "content": "hi"}}))
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return p


def _voyage(extra: list[dict]) -> list[dict]:
    return ([_rec("Bash", {"command": f"cairn codemother show artifact {TID}"}, "2026-11-13T10:00:00Z")]
            + extra
            + [_rec("Bash", {"command": f"git commit -m '{TID}: done'"}, "2026-11-13T10:09:00Z")])


def _observe(records, **kw):
    from skills.sail import toolcalls
    calls = toolcalls.tool_calls(_transcript(records, **kw))
    win = toolcalls.window(calls, TID)
    assert win is not None, "the voyage names its ticket and was not windowed"
    return toolcalls.observe(TICKET, win, roots={ROOT: ""})


def test_a_write_outside_bounds_in_is_a_surprise():
    obs = _observe(_voyage([
        _rec("Write", {"file_path": ROOT + "skills/x/mod.py", "content": ""}, "2026-11-13T10:01:00Z"),
        _rec("Edit", {"file_path": ROOT + "skills/y/other.py", "old_string": "a", "new_string": "b"},
             "2026-11-13T10:02:00Z")]))
    s = [f for f in obs["findings"] if f["kind"] == "surprise"]
    assert len(s) == 1, f"expected exactly one surprise, got {obs['findings']}"
    assert s[0]["field"] == "bounds.in" and s[0]["path"] == "skills/y/other.py", s[0]
    assert s[0]["at"] == "2026-11-13T10:02:00Z" and s[0]["tool"] == "Edit", s[0]


def test_a_write_into_bounds_out_is_a_contradiction():
    obs = _observe(_voyage([
        _rec("Edit", {"file_path": ROOT + "cairn/devices/codemother/ingest.py"}, "2026-11-13T10:03:00Z")]))
    c = [f for f in obs["findings"] if f["kind"] == "contradiction"]
    assert len(c) == 1 and c[0]["field"] == "bounds.out", obs["findings"]
    assert not [f for f in obs["findings"] if f["kind"] == "surprise"], \
        "a contradiction is not also a surprise: one call, one finding"


def test_every_call_is_counted_and_a_foreseen_read_makes_no_finding():
    obs = _observe(_voyage([
        _rec("Read", {"file_path": ROOT + "skills/x/README.md"}, "2026-11-13T10:01:00Z"),
        _rec("Read", {"file_path": ROOT + "skills/x/mod.py"}, "2026-11-13T10:02:00Z"),
        _rec("Grep", {"pattern": "x"}, "2026-11-13T10:03:00Z"),
        _rec("Read", {"file_path": ROOT + "skills/z/elsewhere.py"}, "2026-11-13T10:04:00Z"),
        _rec("Write", {"file_path": "/tmp/scratch/edit.py"}, "2026-11-13T10:05:00Z")]))
    assert obs["calls"] == 7, f"7 tool_use blocks in the window, counted {obs['calls']}"
    assert obs["by_tool"] == {"Bash": 2, "Read": 3, "Grep": 1, "Write": 1}, obs["by_tool"]
    assert [(f["kind"], f["path"]) for f in obs["findings"]] == [("miss", "skills/z/elsewhere.py")], \
        f"only the unforeseen read is a finding (a scratch write outside the repos is not): {obs['findings']}"
    from skills.sail import toolcalls
    before = toolcalls.tool_calls(_transcript(
        [_rec("Read", {"file_path": "/etc/hosts"}, "2026-11-13T09:00:00Z")] + _voyage([])))
    assert len(toolcalls.window(before, TID)) == 2, "a call before the ticket is named is outside the window"
    listed = toolcalls.tool_calls(_transcript(
        [_rec("SendMessage", {"message": f"next: {TID} or another"}, "2026-11-13T08:00:00Z"),
         _rec("Read", {"file_path": "/etc/hosts"}, "2026-11-13T09:00:00Z")] + _voyage([])))
    assert len(toolcalls.window(listed, TID)) == 2, \
        "the window opens at the voyage's show-artifact call, not at an earlier mention in a list"
    assert toolcalls.window(toolcalls.tool_calls(_transcript(
        [_rec("Bash", {"command": "ls"}, "2026-11-13T09:00:00Z")])), TID) is None, \
        "a transcript that never names the ticket is unwindowed, not counted whole"


def test_an_escaped_path_is_read_by_parsing():
    recs = _voyage([_rec("Write", {"file_path": ROOT + "skills/y/other.py"}, "2026-11-13T10:02:00Z")])
    raw = _transcript(recs, escape_slash=True)
    assert "skills/y/other.py" not in raw.read_text(), "the fixture stores the path escaped"
    from skills.sail import toolcalls
    obs = toolcalls.observe(TICKET, toolcalls.window(toolcalls.tool_calls(raw), TID), roots={ROOT: ""})
    assert [f["path"] for f in obs["findings"] if f["kind"] == "surprise"] == ["skills/y/other.py"], obs


def test_the_merged_packet_passes_the_reflection_door():
    from skills.sail import reflection, toolcalls
    obs = _observe(_voyage([
        _rec("Edit", {"file_path": ROOT + "skills/y/other.py"}, "2026-11-13T10:02:00Z"),
        _rec("Read", {"file_path": ROOT + "skills/z/elsewhere.py"}, "2026-11-13T10:04:00Z")]))
    packet = toolcalls.merge(obs, {"at_par": False, "stratum": "code"})
    lacks = reflection.check(packet)
    assert not lacks, f"the merged packet is refused by the reflection door: {lacks}"
    assert packet["ticket"] == TID
    assert packet["cost_estimate"].startswith("4 tool calls"), packet["cost_estimate"]
    assert "skills/z/elsewhere.py" in packet["cost_estimate"], "the miss is summed in cost_estimate"
    flags = [f for f in packet["findings"] if f["kind"] == "flag"]
    assert len(flags) == 1 and flags[0]["artifact"] == "ticket" and flags[0]["field"] == "bounds.in", flags


if __name__ == "__main__":
    raise SystemExit(print_teeth_main(__file__))
