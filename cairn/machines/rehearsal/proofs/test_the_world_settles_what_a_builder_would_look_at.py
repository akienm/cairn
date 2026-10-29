"""Proof for ticket 7a31059daa23 — the world settles what a builder would look at.

Akien, 2026-10-29: *"when we have a failure to cross, it does not automatically mean that the
ticket or other artifact is wrong. it might mean the sieve is wrong"* — and the question to ask
is *"why is this sieve here? what is the goal it's serving, and is it failing to serve it's
overall goal in this case?"* The rehearsal is here to find what a builder would GUESS at; a
builder does not guess whether a file exists, it looks. So a reader may name, on a
builds_under_assumption node, the paths and python modules it would look at (``looks_at``); the
machine stats them after the read, never importing, and a node whose every named thing exists
raises no gap. An absent thing keeps the gap and the gap says what was measured absent.

Fixtures are the sibling proof's (``test_rehearsal.World`` and friends — the fixture ticket
carries D1 and D2); no tooth reads the live commons or calls the live reader. The machine is
resolved at CALL time inside each tooth, so a reverted build reds teeth instead of killing
the import.
"""
from __future__ import annotations

import importlib
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from cairn.machines.rehearsal.proofs.test_rehearsal import World, Stub, TID, _kw, _node  # noqa: E402
from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROVES = {
    "7a31059daa23": {
        "1": "test_a_present_path_settles_the_step",
        "2": "test_an_absent_path_stays_a_gap_with_the_absence_measured",
        "3": "test_a_present_module_settles_without_importing_it",
        "4": "test_a_node_naming_nothing_is_unchanged",
        "5": "test_cannot_proceed_never_settles_by_the_world",
        "6": "test_validate_and_the_schema_agree_on_looks_at",
        "7": "test_a_rehearsal_over_a_present_path_is_clean_and_says_what_it_looked_at",
        "8": "test_the_prompt_teaches_looks_at",
    },
}

IDS = {1, 2}
DOUBT = ["the draft exists", "assumes the draft file is on disk", "the draft is already written"]
BOOM = "rehearsal_world_look_boom_7a31"


def _R():
    return importlib.import_module("cairn.machines.rehearsal.rehearsal")


def _looking(state, looks):
    return [{"read": i + 1, "nodes": [_node("D1"), dict(_node("D2", state, DOUBT[i]), looks_at=looks)]}
            for i in range(3)]


def _kinds(found):
    return {(g["kind"], g["step"]) for g in found}


def _scratch():
    return scratch_dir("rehearsal-world-look-")


def test_a_present_path_settles_the_step():
    root = _scratch()
    try:
        (root / "drafts").mkdir()
        (root / "drafts" / "close.md").write_text("## one\n")
        R = _R()
        found = R.gaps(_looking("builds_under_assumption", [{"kind": "path", "name": "drafts/close.md"}]),
                       IDS, R.world_looker([root]))
        assert found == [], found
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_an_absent_path_stays_a_gap_with_the_absence_measured():
    root = _scratch()
    try:
        R = _R()
        found = R.gaps(_looking("builds_under_assumption", [{"kind": "path", "name": "drafts/close.md"}]),
                       IDS, R.world_looker([root]))
        g = [x for x in found if (x["kind"], x["step"]) == ("assumes", "D2")]
        assert g and g[0].get("measured_absent") == ["drafts/close.md"], found
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_a_present_module_settles_without_importing_it():
    root = _scratch()
    try:
        (root / BOOM).mkdir()
        (root / BOOM / "__init__.py").write_text("raise RuntimeError('a look must never import')\n")
        R = _R()
        sys.modules.pop(BOOM, None)
        found = R.gaps(_looking("builds_under_assumption", [{"kind": "module", "name": BOOM}]),
                       IDS, R.world_looker([root]))
        assert found == [], found
        assert BOOM not in sys.modules, "the look imported the module it named"
        bad = R.world_looker([root])(dict(_node("D2", "builds_under_assumption", "x"),
                                          looks_at=[{"kind": "module", "name": "not a module"}]))
        assert bad == {"looked_at": [{"kind": "module", "name": "not a module", "found": False}],
                       "settled": False}, bad
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_a_node_naming_nothing_is_unchanged():
    root = _scratch()
    try:
        R = _R()
        reads = [{"read": i + 1, "nodes": [_node("D1"), _node("D2", "builds_under_assumption", DOUBT[i])]}
                 for i in range(3)]
        bare = R.gaps(reads, IDS)
        looked = R.gaps(reads, IDS, R.world_looker([root]))
        assert bare == looked and ("assumes", "D2") in _kinds(bare), (bare, looked)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_cannot_proceed_never_settles_by_the_world():
    root = _scratch()
    try:
        (root / "here.md").write_text("x\n")
        R = _R()
        found = R.gaps(_looking("cannot_proceed", [{"kind": "path", "name": "here.md"}]),
                       IDS, R.world_looker([root]))
        assert ("cannot_proceed", "D2") in _kinds(found), found
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_validate_and_the_schema_agree_on_looks_at():
    R = _R()
    node = json.loads(R.SCHEMA_PATH.read_text())["properties"]["nodes"]["items"]
    la = node["properties"]["looks_at"]
    assert la["items"]["properties"]["kind"]["enum"] == list(R.LOOK_KINDS), la
    assert "looks_at" not in node["required"], node["required"]

    def lacks(looks):
        return R.validate({"nodes": [dict(_node("unlisted: x"), looks_at=looks)]})

    assert lacks([{"kind": "path", "name": "a/b.md"}, {"kind": "module", "name": "a.b"}]) == []
    assert lacks("a/b.md") == ["nodes[0].looks_at: a list is required"]
    assert lacks([{"kind": "path", "name": "a", "why": 1}]) == [
        "nodes[0].looks_at[0]: an object with exactly kind and name is required"]
    assert lacks([{"kind": "url", "name": "a"}]) == [
        f"nodes[0].looks_at[0].kind: 'url' is not one of {R.LOOK_KINDS}"]
    assert lacks([{"kind": "path", "name": ""}]) == [
        "nodes[0].looks_at[0].name: a non-empty string is required"]


def test_a_rehearsal_over_a_present_path_is_clean_and_says_what_it_looked_at():
    w = World()
    try:
        here = next(p.relative_to(w.commons).as_posix() for p in (w.commons / "tickets").glob(f"{TID}-*.json"))
        trees = [{"nodes": [_node("D1"), dict(_node("D2", "builds_under_assumption", t),
                                              looks_at=[{"kind": "path", "name": here}])]} for t in DOUBT]
        rec = _R().rehearse(TID, reader=Stub(trees), **_kw(w))
        assert rec["clean"] and rec["gaps"] == [], rec["gaps"]
        sbw = rec.get("settled_by_world")
        assert sbw and {s["step"] for s in sbw} == {"D2"} and [s["read"] for s in sbw] == [1, 2, 3], sbw
        assert all(s["looked_at"] == [{"kind": "path", "name": here, "found": True}] for s in sbw), sbw
        plain = [{"nodes": [_node("D1"), _node("D2")]}]
        rec2 = _R().rehearse(TID, reader=Stub(plain), **_kw(w))
        assert rec2["clean"] and "settled_by_world" not in rec2, rec2
    finally:
        w.close()


def test_the_prompt_teaches_looks_at():
    text = _R().prompt()
    assert "`looks_at`" in text and "is not a guess" in text, text[-600:]
    assert "unless it is a file or module a builder would simply look at" in text


def main() -> int:
    teeth = [fn for name, fn in sorted(globals().items()) if name.startswith("test_") and callable(fn)]
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
    print(f"green — {len(teeth)} teeth: a present path or module settles its step without being "
          "imported; an absent one stays a gap naming what was measured absent; nothing named, "
          "nothing changes; cannot_proceed never settles; validate mirrors the schema; the record "
          "says what was looked at; the prompt teaches looks_at")
    return 0


if __name__ == "__main__":
    sys.exit(main())
