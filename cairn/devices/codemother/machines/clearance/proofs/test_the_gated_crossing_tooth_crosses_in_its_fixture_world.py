"""Proof for ticket 9996bf7186e3 — test_clearance's gated-crossing tooth crosses PROVED in
a CodeMother launched over its fixture registry, so the_stones_are_pushed never reads the
commons beside the code.

Measured 2026-11-19: with that commons one commit ahead, the tooth redded with ExitGateRed
[the_stones_are_pushed]. The judge answers in another process; the tooth's in-process patch
of ``_tfile._TICKETS`` never reached it, so ``find_ticket`` globbed the boat's live ticket and
``_durability_roots`` took its directory. Each tooth below asks the lane in the tooth's own
world (``test_clearance._gated_crossing``, imported inside the tooth) and reads where its roots
point — a reading about the world the proof built, true whatever the push state is.

    python3 cairn/devices/codemother/machines/clearance/proofs/test_the_gated_crossing_tooth_crosses_in_its_fixture_world.py
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[6]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402 (after the repo joins sys.path)

PROVES = {
    "9996bf7186e3": {
        "1": "test_no_durability_root_lies_in_the_commons_beside_the_code",
        "2": "test_the_ticket_root_is_the_fixture_registry",
    },
}

_TC = None


def _tc():
    """test_clearance, loaded once by path (its proofs folder is not a package)."""
    global _TC
    if _TC is None:
        path = Path(__file__).resolve().parent / "test_clearance.py"
        spec = importlib.util.spec_from_file_location("_clearance_proof_tc", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _TC = mod
    return _TC


def _beside() -> set[Path]:
    """The commons beside the code, both spellings a judge could reach it by."""
    import cairn
    tc = _tc()
    return {Path(tc._clearance.COMMONS_ROOT).resolve(),
            (Path(cairn.__file__).resolve().parents[1].parent / "CairnCommons").resolve()}


def _under(p: Path, roots) -> bool:
    return any(p == r or r in p.parents for r in roots)


def _crossing():
    tc = _tc()
    gated = tc._gated_crossing  # absent before this ticket: the tooth reds by name
    tmp = str(scratch_dir("gated-world-"))  # ticket 0d98f7325181: through the scratch door
    return tc, tmp, gated(tmp)


def test_no_durability_root_lies_in_the_commons_beside_the_code():
    tc, tmp, got = _crossing()
    repos = got["repos"]
    assert repos, f"the lane read no roots at all: {got}"
    beside = _beside()
    world = {Path(tmp).resolve(), Path(tc._FIXTURE_TICKETS).resolve(),
             Path(got["hp"]).resolve().parent}
    for r in repos:
        root = Path(r["root"]).resolve()
        assert not _under(root, beside), f"a root lies in the commons beside the code: {r}"
        if r.get("toplevel"):
            top = Path(r["toplevel"]).resolve()
            assert top not in beside, f"a toplevel is the commons beside the code: {r}"
        assert _under(root, world), f"a root lies outside the tooth's world {world}: {r}"


def test_the_ticket_root_is_the_fixture_registry():
    tc, _tmp, got = _crossing()
    fixture = Path(tc._FIXTURE_TICKETS).resolve()
    roots = [Path(r["root"]).resolve() for r in got["repos"]]
    assert fixture in roots, f"the ticket root is not the fixture registry {fixture}: {roots}"
    hist = Path(got["hp"]).resolve().parent
    assert [r for r in roots if r != hist] == [fixture], (
        f"the one non-history root must be the fixture registry {fixture}: {roots}")


if __name__ == "__main__":
    failed = 0
    for _name, _fn in list(globals().items()):
        if _name.startswith("test_") and callable(_fn):
            try:
                _fn()
                print(f"PASS {_name}")
            except Exception as exc:  # noqa: BLE001 — every tooth reports, red or raising
                failed += 1
                print(f"FAIL {_name}: {type(exc).__name__}: {exc}")
    sys.exit(1 if failed else 0)
