"""Proof: a FIXME answer binds to the kick-back it answers.

Ticket 3d31d968a1a0. The FIXME gate (``inspect_fixme``, lane ``every_fixme_entry_is_answered``)
counted every ``FIXME <n>`` decision the ticket ever carried, so the answer written for an earlier
kick-back satisfied a later kick-back's entry of the same number — measured on 56d1aff4455e, whose
``FIXME 1`` stands answered three times, once per kick-back. A decision now counts only when it
was written at or after the ticket's latest crossing into FIXME recorded in the component's
history; with no such crossing on record the gate reds naming the history it read.

Teeth, one per falsifier clause:

  1. Kicked back, answered, crossed out, kicked back again: the first kick-back's answer does
     not satisfy the second's entry of the same number — the crossing out of FIXME through emit
     is refused naming the entry.
  2. An answer written after the latest kick-back admits it.
  3. No crossing into FIXME on record for the ticket — or no history path at all — is a red,
     never a fallback to counting every decision.
  4. The two clocks compare: the history stamps naive local time, the rehearsal CLI stamps UTC
     with an offset; an answer after the kick-back counts and one before does
     not — an hour either side, each written in the offset that sorts the wrong way as a string.

Fixtures follow cairn/tools/base/proofs/test_fixme.py: the node class is a COPY of the live
code-seam.json with ``repair_summons`` set in the copy, the ticket corpus is repointed for the
length of a tooth, and every build name is resolved inside its tooth so a reverted build reds
teeth instead of crashing the import. Each kick-back is a real back-edge driven through emit.

    python3 cairn/tools/base/proofs/test_a_fixme_answer_binds_to_its_kick_back.py   # exit 0 = green
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402
from cairn.tools.base import transitions  # noqa: E402

PROVES = {
    "3d31d968a1a0": {
        "1": "test_an_earlier_kick_backs_answer_does_not_satisfy_a_later_one",
        "2": "test_an_answer_written_after_the_latest_kick_back_admits_it",
        "3": "test_no_kick_back_record_is_a_red",
        "4": "test_the_two_clocks_compare",
    },
}

# Read where test_fixme.py reads it: beside the repo when the commons is there, else at the home
# path — a hollow worktree in /tmp has no commons beside it.
_COMMONS_CLASSES = (transitions._NODE_CLASSES if transitions._NODE_CLASSES.is_dir()
                    else Path.home() / "dev" / "src" / "CairnCommons" / "node_classes")
_LIVE_CLASS = _COMMONS_CLASSES / "code-seam.json"
_AT_PROVEME = "code-seam@v2: THINKME -> TICKETME -> BUILDME -> [PROVEME] -> PROVED"
_AT_FIXME = "code-seam@v2: THINKME -> TICKETME -> [FIXME] -> BUILDME -> PROVEME -> PROVED"
_NAME = "kick_back_fixture_ticket"


def _class_root() -> Path:
    d = json.loads(_LIVE_CLASS.read_text(encoding="utf-8"))
    d["workflow_versions"]["v2"]["repair_summons"] = {"FIXME": "BUILDME"}
    root = scratch_dir("kick_back_fixture_node_classes_")
    (root / "code-seam.json").write_text(json.dumps(d, indent=2), encoding="utf-8")
    return root


def _component() -> tuple[str, str]:
    # Nested one level: the build gate censuses the parent of the directory holding history.json.
    comp = scratch_dir("kick_back_fixture_component_") / "comp"
    comp.mkdir()
    return str(comp / "history.json"), str(comp / "state.json")


class _Corpus:
    """Repoint the gate's ticket corpus at one fixture ticket for the length of a tooth."""

    def __init__(self, body: dict):
        self._body = body

    def __enter__(self):
        d = scratch_dir("kick_back_fixture_tickets_")
        (d / f"{_NAME}.json").write_text(json.dumps(self._body), encoding="utf-8")
        self._saved = transitions._TICKETS
        transitions._TICKETS = d
        return d

    def __exit__(self, *a):
        transitions._TICKETS = self._saved
        return False


def _kick_back(hist: str, state: str, roots: Path) -> datetime:
    """Send the fixture ticket back to FIXME through emit; return the crossing's stamp, aware."""
    from cairn.tools.charter import projector
    transitions.emit(_AT_PROVEME, "FIXME", history_path=hist, state_path=state,
                     node_class_root=roots, ticket=_NAME, missing=["the fixture lacks a thing"])
    last = projector.read_history(hist)[-1]
    assert last.get("to") == "FIXME" and last.get("ticket") == _NAME, last
    return datetime.fromisoformat(last["at"]).astimezone()


def _answer(step: str, at: datetime, tz: timezone = timezone.utc) -> dict:
    return {"step": step, "text": "answered", "at": at.astimezone(tz).isoformat(timespec="seconds")}


def _kicked_twice() -> tuple[str, str, Path, dict, datetime]:
    """Kick back, answer FIXME 1, cross out through the FIXME gate, kick back again.

    The crossing out is the FIXME gate called directly, as test_fixme.py's tooth 3 does: emit's
    BUILDME entry gate behind it reds any fixture ticket that has no chart. Returns the first
    answer and the second kick-back's stamp."""
    hist, state = _component()
    roots = _class_root()
    first = _kick_back(hist, state, roots)
    old = _answer("FIXME 1", first)
    with _Corpus({"fixme": ["a"], "decisions": [old]}):
        _note, record = transitions._fixme_gate(_NAME, history_path=hist)
    assert all(r.get("expected") == r.get("actual") for r in record), record
    while datetime.now().astimezone().replace(microsecond=0) <= first:
        time.sleep(0.1)
    second = _kick_back(hist, state, roots)
    assert second > first, (first, second)
    return hist, state, roots, old, second


def test_an_earlier_kick_backs_answer_does_not_satisfy_a_later_one():
    from cairn.tools.base.transitions import FixmeGateRed, emit
    hist, state, roots, old, _second = _kicked_twice()
    with _Corpus({"fixme": ["a"], "decisions": [old]}):
        try:
            emit(_AT_FIXME, "BUILDME", history_path=hist, state_path=state,
                 node_class_root=roots, ticket=_NAME)
        except FixmeGateRed as e:
            assert "[1]" in str(e), f"the refusal must name the entry the old answer left open: {e}"
            assert "kick-back seq" in str(e), f"the refusal must name the kick-back counted from: {e}"
            return
    raise AssertionError("FIXME -> BUILDME was not refused by the FIXME gate although entry 1's only "
                         "answer was written for the earlier kick-back")


def test_an_answer_written_after_the_latest_kick_back_admits_it():
    hist, _state, _roots, old, second = _kicked_twice()
    body = {"fixme": ["a"], "decisions": [old, _answer("FIXME 1", second + timedelta(seconds=5))]}
    with _Corpus(body):
        note, record = transitions._fixme_gate(_NAME, history_path=hist)
    assert record and all(r.get("expected") == r.get("actual") for r in record), record


def test_no_kick_back_record_is_a_red():
    from cairn.tools.base.transitions import FixmeGateRed, _fixme_gate
    hist, _state = _component()
    Path(hist).write_text("[]", encoding="utf-8")
    body = {"fixme": ["a"], "decisions": [_answer("FIXME 1", datetime.now().astimezone())]}
    for path in (hist, None):
        with _Corpus(body):
            try:
                _fixme_gate(_NAME, history_path=path)
            except FixmeGateRed as e:
                assert "no crossing into FIXME" in str(e), f"history_path={path!r}: {e}"
                continue
        raise AssertionError(f"history_path={path!r} holds no kick-back for {_NAME!r}, yet the "
                             "FIXME gate passed by counting every decision")


def test_the_two_clocks_compare():
    from cairn.tools.base.transitions import FixmeGateRed, _fixme_gate
    hist, state = _component()
    kicked = _kick_back(hist, state, _class_root())
    # Written in the offsets that sort the wrong way as strings against a naive local stamp, in
    # any local zone: the answer an hour later at -12:00, the answer an hour earlier at +12:00.
    body = {"fixme": ["a", "b"],
            "decisions": [_answer("FIXME 1", kicked + timedelta(hours=1), timezone(timedelta(hours=-12))),
                          _answer("FIXME 2", kicked - timedelta(hours=1), timezone(timedelta(hours=12)))]}
    with _Corpus(body):
        try:
            _fixme_gate(_NAME, history_path=hist)
        except FixmeGateRed as e:
            assert "[2]" in str(e), f"only entry 2's answer predates the kick-back: {e}"
            return
    raise AssertionError("an answer an hour before the kick-back, written at +12:00, was counted")


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
