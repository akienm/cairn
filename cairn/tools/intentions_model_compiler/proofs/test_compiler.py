"""Proof for intentions_model_compiler — ``intentions-congruency-lab/`` is a folder of COPIES
of every intention+why, and it cannot drift from what it copies.

Teeth a hollow copier could not pass:

  - A COPY IS BYTE-IDENTICAL TO ITS SOURCE (Law 8). Not "contains the content", not
    "embeds it in an envelope" — the same bytes. A build that re-serialised a json charter
    (reordering keys, changing indentation) trips this. This is the tooth that makes the
    lab readable by anything that reads the originals, which is the whole point.
  - EVERY intention+why IN THE REPO IS COPIED, not just ``cairn/*/``. Measured 2026-07-31:
    the old scan reached 19 of 32, silently leaving all nine ``skills/*/`` plus ``bin/``,
    ``learning/``, ``launchers/`` and ``press_office/`` out of the folder whose stated job
    is to regrow the system. A build that walks only the package dir trips this.
  - A REMOVED SOURCE REMOVES ITS COPY. The lab is regenerated whole. A build that only ever
    writes — the easy build — leaves a deleted intention standing in the lab forever, which
    is exactly the stale-record failure (Law 7). This is the tooth most likely to be missing.
  - A NAME COLLISION IS LOUD, NEVER LAST-WRITE-WINS. Two charters both named
    ``intention+why.json`` must not silently overwrite each other in a flat folder. A build
    that keyed on the bare filename trips this by losing one.
  - THE ``_``-PREFIXED STORE RECORDS ARE NEVER TOUCHED (Law 6). ``_charter+why.json`` is a
    hand-authored source that happens to live in the lab; a copier that regenerates the
    folder "whole" without excluding it deletes the store's own charter.
  - DETERMINISTIC (Law 1). Same sources -> same plan, whatever order they arrive in.

Self-contained (synthetic sources in a temp dir) except the reach tooth, which reads the
real repo. Self-cleaning.

    python3 cairn/tools/intentions_model_compiler/proofs/test_compiler.py     # exit 0 = green
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# The trace wire fires on every copy_to_lab call; a proof run is not a real firing,
# so its records go to a scratch berth — the live denominator stays honest.
from cairn.devices.tester.scratch import scratch_dir  # noqa: E402
os.environ["CAIRN_LB_TRACE_ROOT"] = str(scratch_dir("imc-proof-traces-"))

from cairn.tools.intentions_model_compiler import compiler


def _tree(d: str) -> tuple[str, str]:
    """A minimal two-tree source layout: commons homeless dir + a repo with charters."""
    commons = os.path.join(d, "CairnCommons")
    code = os.path.join(d, "cairn")
    os.makedirs(os.path.join(commons, "intentions-not-beside-code"))
    os.makedirs(os.path.join(commons, "intentions-congruency-lab"))
    os.makedirs(os.path.join(code, "cairn", "tools", "base"))
    os.makedirs(os.path.join(code, "skills", "intent"))
    with open(os.path.join(commons, "intentions-not-beside-code", "telos.md"), "w") as f:
        f.write("the frame\n")
    # Deliberately awkward json: unsorted keys, 3-space indent, a trailing newline. A copy
    # keeps it exactly; anything that parses-and-rewrites does not.
    with open(os.path.join(code, "cairn", "tools", "base", "intention+why.json"), "w") as f:
        f.write('{\n   "what": "substrate",\n   "a_later_key": 1,\n   "b": 2\n}\n')
    with open(os.path.join(code, "skills", "intent", "intention+why.json"), "w") as f:
        f.write('{"what": "the skill"}')
    return commons, code


def test_a_copy_is_byte_identical_to_its_source():
    with tempfile.TemporaryDirectory() as d:
        commons, code = _tree(d)
        lab = os.path.join(commons, "intentions-congruency-lab")
        compiler.copy_to_lab(commons_root=commons, code_root=code, out_dir=lab)

        src = Path(code, "cairn", "tools", "base", "intention+why.json").read_bytes()
        cp = Path(lab, "cairn-tools-base--intention+why.json").read_bytes()
        assert cp == src, "the copy is the same BYTES — not a re-serialisation of the same data"
        assert Path(lab, "telos.md").read_bytes() == Path(
            commons, "intentions-not-beside-code", "telos.md").read_bytes()


def test_every_charter_in_the_repo_is_copied_not_just_the_package():
    with tempfile.TemporaryDirectory() as d:
        commons, code = _tree(d)
        lab = os.path.join(commons, "intentions-congruency-lab")
        r = compiler.copy_to_lab(commons_root=commons, code_root=code, out_dir=lab)
        assert "skills-intent--intention+why.json" in r["copied"], (
            "a charter OUTSIDE cairn/*/ is copied — this is the 19-of-32 defect, measured "
            f"2026-07-31 and fixed here; got {r['copied']}")
        assert r["count"] == 3, r["copied"]


def test_a_removed_source_removes_its_copy():
    with tempfile.TemporaryDirectory() as d:
        commons, code = _tree(d)
        lab = os.path.join(commons, "intentions-congruency-lab")
        compiler.copy_to_lab(commons_root=commons, code_root=code, out_dir=lab)
        assert os.path.exists(os.path.join(lab, "skills-intent--intention+why.json"))

        os.remove(os.path.join(code, "skills", "intent", "intention+why.json"))
        r = compiler.copy_to_lab(commons_root=commons, code_root=code, out_dir=lab)

        assert not os.path.exists(os.path.join(lab, "skills-intent--intention+why.json")), (
            "a write-only copier leaves a deleted intention standing in the lab forever")
        assert r["removed"] == ["skills-intent--intention+why.json"], r["removed"]


def test_a_hand_edited_copy_is_overwritten():
    with tempfile.TemporaryDirectory() as d:
        commons, code = _tree(d)
        lab = os.path.join(commons, "intentions-congruency-lab")
        compiler.copy_to_lab(commons_root=commons, code_root=code, out_dir=lab)
        Path(lab, "telos.md").write_text("HAND-EDITED GARBAGE")
        compiler.copy_to_lab(commons_root=commons, code_root=code, out_dir=lab)
        assert Path(lab, "telos.md").read_text() == "the frame\n", (
            "the lab is a view, never a record of truth (Law 7)")


def test_the_store_charter_is_never_touched():
    with tempfile.TemporaryDirectory() as d:
        commons, code = _tree(d)
        lab = os.path.join(commons, "intentions-congruency-lab")
        charter = os.path.join(lab, "_charter+why.json")
        Path(charter).write_text("HAND-AUTHORED — do not touch")
        r = compiler.copy_to_lab(commons_root=commons, code_root=code, out_dir=lab)
        assert Path(charter).read_text() == "HAND-AUTHORED — do not touch", (
            "regenerating the folder 'whole' must not eat the store's own charter (Law 6)")
        assert "_charter+why.json" not in r["removed"]


def test_a_name_collision_is_loud_never_last_write_wins():
    a = {"id": "dup", "kind": "component-charter", "source": "x/intention+why.json",
         "path": "/one/intention+why.json"}
    b = {"id": "dup", "kind": "component-charter", "source": "y/intention+why.json",
         "path": "/two/intention+why.json"}
    try:
        compiler.plan_copies([a, b])
    except ValueError as exc:
        assert "collision" in str(exc)
    else:
        raise AssertionError("two sources claiming one lab filename must RAISE, not silently "
                             "drop one — a flat folder makes this reachable")


def test_the_plan_is_deterministic():
    with tempfile.TemporaryDirectory() as d:
        commons, code = _tree(d)
        s = compiler.gather_sources(commons, code)
        assert compiler.plan_copies(s) == compiler.plan_copies(list(reversed(s))), (
            "same sources, any input order -> same plan")


def test_the_real_repo_reaches_both_trees_and_every_charter():
    commons = str(Path(_REPO_ROOT).parent / "CairnCommons")
    sources = compiler.gather_sources(commons_root=commons, code_root=str(_REPO_ROOT))
    ids = {s["id"] for s in sources}
    kinds = {s["kind"] for s in sources}
    assert "telos" in ids and "core-values" in ids, "the homeless roots are gathered"
    assert "cairn-tools-base" in ids, "a package charter is gathered"
    assert "skills-intent" in ids, "a charter outside the package is gathered"
    assert kinds == {"homeless", "component-charter"}, "both source kinds present"
    assert not any(os.path.basename(s["source"]).startswith("_") for s in sources), (
        "the _-prefixed store charter is not copied")
    # Invariant, not a snapshot: the corpus grows. Every intention+why on disk is reached.
    on_disk = sum(1 for p in Path(_REPO_ROOT).rglob("intention+why.json")
                  if not any(part in compiler._SKIP_DIRS for part in p.parts))
    gathered = sum(1 for s in sources if s["kind"] == "component-charter")
    assert gathered == on_disk, f"gathered {gathered} of {on_disk} charters on disk"


def _main() -> int:
    checks = [
        test_a_copy_is_byte_identical_to_its_source,
        test_every_charter_in_the_repo_is_copied_not_just_the_package,
        test_a_removed_source_removes_its_copy,
        test_a_hand_edited_copy_is_overwritten,
        test_the_store_charter_is_never_touched,
        test_a_name_collision_is_loud_never_last_write_wins,
        test_the_plan_is_deterministic,
        test_the_real_repo_reaches_both_trees_and_every_charter,
    ]
    for check in checks:
        check()
        print(f"  PASS  {check.__name__}")
    print("green — intentions_model_compiler: intentions-congruency-lab/ holds a BYTE-IDENTICAL "
          "copy of every intention+why in both trees (all of them, not just cairn/*/); a removed "
          "source removes its copy; a hand-edit is overwritten; a name collision raises; the "
          "store's own _charter+why.json is never touched (Law 6/7)")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
