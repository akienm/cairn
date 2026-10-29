"""Proof for ticket c9897770efe6 — the rehearsal is a build simulator.

Akien, 2026-10-29: *"You are a build simulator here to identify what's missing"* — the reader
*"doesn't need to 'fit in to our build process' it just needs to say 'i got stopped here' or
'xyz is missing'"*; *"we should be telling it what exists and what doesn't before hand"*; and
*"the ticket becomes nothing but the build plan. that's what makes this work."* So the reader
is handed THE PLAN (the ticket's live steps) and WHAT EXISTS (measured before the read, never
imported), and each node is {step, state: builds|stopped, missing, confidence}. ``decide`` at a
D<n> step rewrites that step in place and logs the old line.

Fixtures are the sibling proof's (``test_rehearsal.World`` and its fixture ticket carrying D1
and D2); the node helper is this file's own, in the new shape. Only tooth 7 reads the live
commons, and it asserts an invariant (size, headings), never a snapshot. The machine is resolved
at CALL time inside each tooth, so a reverted build reds teeth instead of killing the import.
"""
from __future__ import annotations

import importlib
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from cairn.machines.rehearsal.proofs.test_rehearsal import World, TID  # noqa: E402
from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROVES = {"c9897770efe6": {"all": "the_rehearsal_is_a_build_simulator"}}

OLD_HEADINGS = ("# VOYAGE CRAFT", "# ALREADY LANDED", "# CHART", "# CHARTER")
WIRING = "where the widget is wired"
BOOM = "rehearsal_what_exists_boom_c989"


def _R():
    return importlib.import_module("cairn.machines.rehearsal.rehearsal")


def _node(step, state="builds", missing="", confidence=0.9):
    return {"step": step, "state": state, "missing": missing, "confidence": confidence}


def _headings(text):
    return {line.strip() for line in text.splitlines() if line.startswith("# ")}


def test_the_prompt_opens_as_a_build_simulator():
    text = _R().prompt()
    assert text.splitlines()[0].strip() == "You are a build simulator here to identify what's missing.", \
        text.splitlines()[:2]
    assert "stopped" in text and "legal" in text, text[:800]
    for gone in ("looks_at", "ALREADY LANDED", "VOYAGE CRAFT"):
        assert gone not in text, gone


def test_render_hands_only_the_plan_and_what_exists():
    w = World()
    try:
        text = _R().render(TID, root=w.commons, repo=w.dir / "no-repo")[0]
        heads = _headings(text)
        assert {"# THE PLAN", "# WHAT EXISTS"} <= heads, heads
        assert not heads & set(OLD_HEADINGS), heads & set(OLD_HEADINGS)
        assert "THINKME -> TICKETME" not in text, "the cursor was handed to the reader"
        assert '"D1"' in text and '"D2"' in text, "the plan steps are not keyed by step id"
    finally:
        w.close()


def test_what_exists_measures_paths_and_modules_without_importing():
    base = scratch_dir("rehearsal-what-exists-")
    try:
        commons = base / "CairnCommons"
        (commons / "tickets").mkdir(parents=True)
        (commons / "tickets" / "here.json").write_text("{}\n")
        (base / "Other" / "tickets").mkdir(parents=True)
        (base / "Other" / "tickets" / "here.json").write_text("{}\n")
        repo = base / "repo"
        (repo / "cairn" / BOOM).mkdir(parents=True)
        (repo / "cairn" / "__init__.py").write_text("")
        (repo / "cairn" / BOOM / "__init__.py").write_text("raise RuntimeError('a measure must never import')\n")
        (repo / "cairn" / BOOM / "mod.py").write_text("def fn(): pass\n")
        sys.modules.pop(f"cairn.{BOOM}", None)
        texts = ["write tickets/here.json and drafts/gone.md;",
                 "read CairnCommons/tickets/here.json, not Other/tickets/here.json.",
                 f"call cairn.{BOOM}.mod.fn there"]
        got = {e["name"]: e for e in _R().what_exists(texts, [repo, commons])}
        assert got["tickets/here.json"]["found"] is True, got
        assert got["drafts/gone.md"]["found"] is False, got
        assert got["CairnCommons/tickets/here.json"]["found"] is True, got
        assert got["Other/tickets/here.json"]["found"] is False, got
        fn = got[f"cairn.{BOOM}.mod.fn"]
        assert fn["kind"] == "module" and fn["found"] is True and fn["module"] == f"cairn.{BOOM}.mod", fn
        assert f"cairn.{BOOM}" not in sys.modules, "what_exists imported the module it measured"
        assert len(got) == 5 and all(set(e) <= {"kind", "name", "found", "module"} for e in got.values()), got
    finally:
        shutil.rmtree(base, ignore_errors=True)


def test_validate_and_the_schema_speak_builds_and_stopped():
    R = _R()
    assert R.validate({"nodes": [_node("D1"), _node("D2", "stopped", WIRING)]}) == []
    assert R.validate({"nodes": [dict(_node("D1"), looks_at=[])]}) != []
    assert R.validate({"nodes": [dict(_node("D1"), assumption="x")]}) != []
    assert R.validate({"nodes": [_node("D1", "cannot_proceed", "x")]}) != []
    assert R.validate({"nodes": [_node("D1", "stopped", "")]}) != []
    node = json.loads(R.SCHEMA_PATH.read_text())["properties"]["nodes"]["items"]
    assert set(node["properties"]) == set(node["required"]) == {"step", "state", "missing", "confidence"}, node
    assert node["properties"]["state"]["enum"] == list(R.STATES) == ["builds", "stopped"], node
    assert R.GAP_KINDS == ("stopped", "step_absent", "unlisted"), R.GAP_KINDS


def test_a_stopped_read_is_a_gap_naming_what_is_missing():
    R = _R()
    one = [{"read": i + 1, "nodes": [_node("D1"), _node("D2", "stopped", WIRING) if i == 1 else _node("D2")]}
           for i in range(3)]
    found = R.gaps(one, {1, 2})
    assert [(g["kind"], g["step"]) for g in found] == [("stopped", "D2")], found
    assert WIRING in found[0]["missing"], found
    clean = [{"read": i + 1, "nodes": [_node("D1"), _node("D2")]} for i in range(3)]
    assert R.gaps(clean, {1, 2}) == []
    unl = [{"read": i + 1, "nodes": [_node("D1"), _node("D2"), _node("unlisted: wire it", "stopped", WIRING)]}
           for i in range(3)]
    assert all(g["kind"] in R.GAP_KINDS for g in R.gaps(one + unl, {1, 2})), R.gaps(unl, {1, 2})


def test_decide_rewrites_the_step_it_settles_and_logs_the_old_line():
    from cairn.tools.base.ticket_log import read_log
    w = World()
    try:
        R = _R()
        R.decide(TID, "D2", "prove the widget wired at the rack", by="the proof", root=w.commons)
        plan = json.loads(w.ticket.read_text())["decisions"]
        twos = [d for d in plan if d["n"] == 2]
        assert len(twos) == 1 and twos[0]["text"] == "prove the widget wired at the rack", plan
        logged = read_log(w.ticket, "decision_retired")
        assert [x["decision"]["text"] for x in logged] == ["prove the widget"], logged
        before = w.ticket.read_bytes()
        try:
            R.decide(TID, "D2", "someone else's words", by="not the proof", root=w.commons)
        except R.Refused:
            pass
        else:
            raise AssertionError("another author rewrote a line that is not theirs")
        assert w.ticket.read_bytes() == before, "a refused decide wrote the plan"
        R.decide(TID, "FIXME 1", "the first repair", by="the proof", root=w.commons)
        R.decide(TID, "FIXME 1", "the first repair, rewritten", by="the proof", root=w.commons)
        fix = [d for d in json.loads(w.ticket.read_text())["decisions"] if d.get("step") == "FIXME 1"]
        assert [d["text"] for d in fix] == ["the first repair, rewritten"], fix
    finally:
        w.close()


def test_the_live_render_is_small_and_carries_no_old_heading():
    # the bound is on what rides BESIDE the plan: the plan is as long as its steps (7a31's are
    # 12,993 chars, measured 2026-10-29), and what the old render added was 45,000 more
    # the live commons sits beside the repo, else under $HOME (hollow's worktree has no sibling)
    beside = Path(__file__).resolve().parents[4].parent / "CairnCommons"
    live = beside if beside.is_dir() else Path.home() / "dev" / "src" / "CairnCommons"
    text = _R().render("7a31059daa23", root=live)[0]
    plan = text[text.index("# THE PLAN"):text.index("# WHAT EXISTS")]
    assert len(text) - len(plan) < 5000, (len(text), len(plan))
    assert not _headings(text) & set(OLD_HEADINGS), _headings(text)
    assert "# WHAT EXISTS" in _headings(text)


def main() -> int:
    teeth = [fn for name, fn in globals().items() if name.startswith("test_") and callable(fn)]
    failed = []
    for tooth in teeth:
        try:
            tooth()
        except Exception as e:                       # noqa: BLE001 — the reason is the record
            failed.append(tooth.__name__)
            print(f"  FAIL  {tooth.__name__}: {type(e).__name__}: {str(e)[:300]}")
            continue
        print(f"  PASS  {tooth.__name__}")
    if failed:
        print(f"red — {len(failed)} of {len(teeth)} teeth: {', '.join(failed)}")
        return 1
    print(f"green — {len(teeth)} teeth: the prompt opens as a build simulator; the reader is handed "
          "only the plan and what exists; existence is measured without importing; nodes are "
          "builds|stopped with what is missing; decide rewrites the step it settles")
    return 0


if __name__ == "__main__":
    sys.exit(main())
