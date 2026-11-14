"""Proof for ticket c058eae40a95 — the scratch_home_goes_through_the_door sieve.

A proof that moves HOME around cairn.tools.scratch's home_env reds at its own row's crossing:
a child env built by hand with a HOME key (scratch_home_bypass), or an in-process HOME move
that leaves USERPROFILE behind (scratch_home_in_process, ticket 4fb37aa5a13f). Provenance:
CC's reading of d95796cdfb9b's USERPROFILE finding (measured 2026-11-13 on akiendell: a child
given only HOME resolved the live ~/.cairn on Windows).

One tooth per falsifier clause:

  1. a row whose proof hand-builds a scratch-HOME child env reds, naming the site;
  2. a row whose proof moves HOME in-process and leaves USERPROFILE reds, naming the site;
  3. a row whose proofs go through home_env, or move both keys, is quiet; a held component's
     offending proof reds at its own row and not its holder's;
  4. the sieve sits in SIEVES and its record carries a why sourced as CC's reading of
     d95796cdfb9b;
  5. THE DONE-MEASURE, AS AN INVARIANT: over every component under cairn/, zero findings.

Fixture sources are f-strings with the keys spelled apart, so neither scan reads this
proof's own text as a move.

    bin/cairn test cairn/machines/build_inspector/proofs/test_scratch_home_goes_through_the_door.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROVES = {"c058eae40a95": {
    "1": "test_a_hand_built_child_env_reds_naming_the_site",
    "2": "test_an_in_process_home_move_without_userprofile_reds",
    "3": "test_the_door_is_quiet_and_a_held_component_answers_at_its_own_row",
    "4": "test_the_sieve_is_seated_and_carries_its_why",
    "5": "test_the_live_corpus_moves_no_home_around_the_door"}}

NAME = "scratch_home_goes_through_the_door"
H, U = "HO" + "ME", "USER" + "PROFILE"

HAND_BUILT = f"import os\n\n\ndef _env(x):\n    return dict(os.environ, {H}=x)\n"
IN_PROCESS = f"import os\n\n\ndef _home(monkeypatch, x):\n    monkeypatch.setenv('{H}', x)\n"
BOTH_KEYS = (f"import os\n\n\ndef _home(monkeypatch, x):\n    monkeypatch.setenv('{H}', x)\n"
             f"    monkeypatch.setenv('{U}', x)\n")
THE_DOOR = ("from cairn.tools.scratch.scratch import home_env\n\n\n"
            "def _env(x):\n    return home_env(x)\n")


def _inspector():
    """Bound when a tooth asks, so a reverted inspector reds each tooth by name."""
    from cairn.machines.build_inspector import inspector
    return inspector


def _sieve(row, comp_dir):
    return _inspector().scratch_home_goes_through_the_door(row, comp_dir)


def _row(name):
    return {"component": name, "dir": name}


def _component(root: Path, rel: str, proofs: dict) -> Path:
    comp = root / rel
    (comp / "proofs").mkdir(parents=True)
    (comp / "intention+why.json").write_text("{}\n", encoding="utf-8")
    for name, src in proofs.items():
        (comp / "proofs" / f"test_{name}.py").write_text(src, encoding="utf-8")
    return comp


def _sites(found):
    assert all(f["method"] == NAME for f in found), found
    return sorted(f["values"]["site"] for f in found)


def test_a_hand_built_child_env_reds_naming_the_site():
    comp = _component(Path(scratch_dir("testing-c058-hand-")), "hand", {"hand": HAND_BUILT})
    assert _sites(_sieve(_row("hand"), comp)) == ["proofs/test_hand.py:4 _env"]


def test_an_in_process_home_move_without_userprofile_reds():
    comp = _component(Path(scratch_dir("testing-c058-inproc-")), "inproc", {"inproc": IN_PROCESS})
    assert _sites(_sieve(_row("inproc"), comp)) == ["proofs/test_inproc.py:4 _home"]


def test_the_door_is_quiet_and_a_held_component_answers_at_its_own_row():
    root = Path(scratch_dir("testing-c058-quiet-"))
    holder = _component(root, "holder", {"door": THE_DOOR, "both": BOTH_KEYS})
    held = _component(root, "holder/machines/held", {"inproc": IN_PROCESS})
    assert _sites(_sieve(_row("holder"), holder)) == [], "the holder red over the door or its held machine"
    assert _sites(_sieve(_row("held"), held)) == ["proofs/test_inproc.py:4 _home"], (
        "the held machine's own row did not red")


def test_the_sieve_is_seated_and_carries_its_why():
    insp = _inspector()
    assert insp.SIEVES.get(NAME) is insp.scratch_home_goes_through_the_door, sorted(insp.SIEVES)
    rec = json.loads((Path(insp.__file__).parent / "sieves" / f"{NAME}.json").read_text(encoding="utf-8"))
    assert rec["name"] == NAME and rec.get("why", "").strip(), rec
    assert rec.get("why_source") == {"kind": "cc_reading", "of": "d95796cdfb9b"}, rec


def test_the_live_corpus_moves_no_home_around_the_door():
    """Every directory under cairn/ that carries a charter is a component row; the walk's
    denominator is asserted, so a walk that saw nothing cannot pass, and a control component
    must red first, so a sieve that names nothing cannot pass either."""
    control = _component(Path(scratch_dir("testing-c058-control-")), "control",
                         {"hand": HAND_BUILT, "inproc": IN_PROCESS})
    assert len(_sieve(_row("control"), control)) == 2, "the control did not red: the sieve is hollow"
    cairn = _REPO_ROOT / "cairn"
    rows = sorted(p.parent for p in cairn.rglob("intention+why.json") if "__pycache__" not in p.parts)
    assert len(rows) > 50, f"the walk found only {len(rows)} components — it did not see the corpus"
    sites = []
    for comp in rows:
        rel = comp.relative_to(cairn).as_posix()
        sites += [f"{rel}/{s}" for s in _sites(_sieve(_row(rel), comp))]
    print(f"  live corpus: {len(sites)} HOME move(s) around the door over {len(rows)} components")
    assert sites == [], f"{len(sites)} proof scope(s) move HOME around the door:\n  " + "\n  ".join(sites)


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
