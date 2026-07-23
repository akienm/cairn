"""Proof for intentions_model_compiler — the ``intentions/`` MODEL is COMPILED from its
sources and cannot drift.

Teeth a hollow compiler could not pass:

  - LOSSLESS + INVENTS NOTHING (Law 8). Every source lands in the model with its content
    verbatim; the model holds exactly the sources' ids, no more. A hollow build that
    dropped a source or fabricated one trips this.
  - ROOTS SURFACE FIRST BY PHYSICS (Law 4). Ordered by born timestamp, the oldest source
    sorts to the top — the frame is first by construction, not a special case. A hollow
    build that ordered by name or insertion trips this.
  - A CHANGED SOURCE CHANGES THE MODEL / A REMOVED SOURCE LEAVES NO TRACE. The projection
    is regenerated whole, so drift and removal both propagate. A hollow build that carried
    stale output trips this.
  - DETERMINISTIC (no drift, Law 1). Same sources -> byte-identical model. A hollow build
    with nondeterministic ordering trips this.
  - ONE WRITE-DOOR, HAND-EDIT REVERTED (Law 6 / Law 7). A hand-edited model is overwritten
    by the next compile; the store's ``_charter+why.json`` (a hand-authored source) is
    NEVER touched. A hollow build that trusted on-disk model, or clobbered the charter,
    trips this.
  - READS BOTH SOURCE TREES (the seed claim). ``gather_sources`` on the real repo picks up
    intentions-other/ AND the beside-code charters, and excludes the ``_``-prefixed store
    charter. A hollow build that compiled only one tree regrows a repo that does not run.

Self-contained (synthetic sources in a temp dir) except the last tooth, which reads the
real repo. Self-cleaning.

    python3 cairn/intentions_model_compiler/proofs/test_compiler.py     # exit 0 = green
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.intentions_model_compiler import compiler


def _src(id, born, content, kind="homeless"):
    return {"id": id, "kind": kind, "source": f"intentions-other/{id}.md",
            "born": born, "content": content}


def test_lossless_and_invents_nothing():
    sources = [
        _src("telos", "2026-07-14T09:00:00+00:00", "the charter everything traces to"),
        _src("base", "2026-07-20T09:00:00+00:00", {"what": "the substrate"}, kind="component-charter"),
    ]
    model = compiler.compile_model(sources)
    assert model["count"] == 2
    ids = {i["id"] for i in model["intentions"]}
    assert ids == {"telos", "base"}, "exactly the sources' ids — nothing dropped or invented"
    by_id = {i["id"]: i for i in model["intentions"]}
    assert by_id["telos"]["content"] == "the charter everything traces to", "content carried verbatim"
    assert by_id["base"]["content"] == {"what": "the substrate"}, "a json source is carried as its object"
    assert by_id["base"]["kind"] == "component-charter"


def test_roots_surface_first_by_born_timestamp():
    # Deliberately hand the compiler the roots LAST and out of name order — physics, not order-in.
    sources = [
        _src("web-server", "2026-07-21T00:00:00+00:00", "a late arrival"),
        _src("core-values", "2026-07-14T00:00:01+00:00", "the six"),
        _src("telos", "2026-07-14T00:00:00+00:00", "the frame"),
    ]
    model = compiler.compile_model(sources)
    top_two = [i["id"] for i in model["intentions"][:2]]
    assert top_two == ["telos", "core-values"], f"the oldest (the roots) surface first, got {top_two}"


def test_a_changed_source_changes_the_model():
    base = [_src("x", "2026-07-15T00:00:00+00:00", "before")]
    changed = [_src("x", "2026-07-15T00:00:00+00:00", "after")]
    assert compiler.compile_model(base) != compiler.compile_model(changed), "content change flows through"


def test_a_removed_source_leaves_no_trace():
    two = [_src("a", "2026-07-15T00:00:00+00:00", "A"), _src("b", "2026-07-16T00:00:00+00:00", "B")]
    one = [two[0]]
    ids = {i["id"] for i in compiler.compile_model(one)["intentions"]}
    assert ids == {"a"}, "the removed source 'b' is absent — regenerated whole, no stale carry-over"


def test_deterministic_to_the_byte():
    sources = [
        _src("b", "2026-07-16T00:00:00+00:00", "B"),
        _src("a", "2026-07-15T00:00:00+00:00", "A"),
    ]
    a = json.dumps(compiler.compile_model(sources), ensure_ascii=False, indent=2, sort_keys=False)
    b = json.dumps(compiler.compile_model(list(reversed(sources))), ensure_ascii=False, indent=2, sort_keys=False)
    assert a == b, "same sources (any input order) -> byte-identical model"


def test_one_write_door_reverts_a_hand_edit_and_spares_the_charter():
    with tempfile.TemporaryDirectory() as d:
        commons = os.path.join(d, "CairnCommons")
        code = os.path.join(d, "cairn")
        # a minimal source tree
        os.makedirs(os.path.join(commons, "intentions-other"))
        os.makedirs(os.path.join(commons, "intentions"))
        os.makedirs(os.path.join(code, "base"))
        with open(os.path.join(commons, "intentions-other", "telos.md"), "w") as f:
            f.write("the frame")
        with open(os.path.join(code, "base", "intention+why.json"), "w") as f:
            json.dump({"what": "substrate"}, f)
        # a hand-authored store charter that must be left ALONE, and a junk model to be reverted
        charter_path = os.path.join(commons, "intentions", "_charter+why.json")
        with open(charter_path, "w") as f:
            f.write("HAND-AUTHORED — do not touch")
        out = os.path.join(commons, "intentions", "_model.json")
        with open(out, "w") as f:
            f.write("HAND-EDITED GARBAGE")

        model = compiler.compile_to_disk(commons_root=commons, code_root=code, out_path=out)

        with open(out, encoding="utf-8") as f:
            on_disk = json.load(f)
        assert on_disk == model, "the hand-edit is gone — the door rewrote the model from the sources"
        assert {i["id"] for i in on_disk["intentions"]} == {"telos", "base"}, "both trees compiled in"
        with open(charter_path, encoding="utf-8") as f:
            assert f.read() == "HAND-AUTHORED — do not touch", "the store charter was NOT clobbered"


def test_gather_reads_both_trees_on_the_real_repo():
    commons = str(Path(_REPO_ROOT).parent / "CairnCommons")
    code = str(Path(_REPO_ROOT) / "cairn")     # the package dir where components berth
    sources = compiler.gather_sources(commons_root=commons, code_root=code)
    ids = {s["id"] for s in sources}
    kinds = {s["kind"] for s in sources}
    assert "telos" in ids and "core-values" in ids, "the homeless roots are gathered"
    assert "base" in ids, "the beside-code charters are gathered"
    assert kinds == {"homeless", "component-charter"}, "both source kinds present"
    assert not any(s["id"].startswith("_") for s in sources), "the _-prefixed store charter is excluded"


def _main() -> int:
    checks = [
        test_lossless_and_invents_nothing,
        test_roots_surface_first_by_born_timestamp,
        test_a_changed_source_changes_the_model,
        test_a_removed_source_leaves_no_trace,
        test_deterministic_to_the_byte,
        test_one_write_door_reverts_a_hand_edit_and_spares_the_charter,
        test_gather_reads_both_trees_on_the_real_repo,
    ]
    for check in checks:
        check()
        print(f"  PASS  {check.__name__}")
    print("green — intentions_model_compiler: the intentions/ model is a deterministic, lossless "
          "projection of BOTH source trees; roots surface first by born timestamp (Law 4); one "
          "write-door reverts a hand-edit and spares the store charter (Law 6/7)")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
