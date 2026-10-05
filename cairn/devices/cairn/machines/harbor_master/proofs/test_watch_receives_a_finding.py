"""PROOF — harbor_master receives a WATCHME's finding (ticket a88d6a368cfb).

A probe that measures whether its ticket's falsifier still holds posts ``watch`` to
harbor_master with ``{ticket, holds, finding}``. A red finding sends that ticket back to
FIXME with the finding as its one lack; a green one changes nothing. This is the receiver
835b5736bf2b's decision D2 names, built first by Akien's answer to open-291189a9766a
(WATCHME = probe + receiver).

What a hollow build cannot pass (Law 8):
  - A device with no ``watch`` verb fails every tooth: the handler does not exist.
  - A handler that replies "accepted" and moves nothing fails
    test_a_red_finding_sends_the_ticket_to_fixme, which reads the ticket's cursor, its
    fixme list and the journal record beside the probe's charter.
  - A handler that moves on any finding fails test_a_green_finding_writes_nothing and
    test_a_ticket_not_at_rest_is_not_moved, which compare the ticket's bytes.
  - A handler that raises, or accepts a body it cannot act on, fails
    test_a_malformed_watch_is_refused_by_name.
  - A ``_send_to_fixme`` that ignores the ``why`` it is handed fails the red-finding
    tooth, which reads the journal record's why.

Every tooth runs in a fixture world under scratch_dir; ``clearance._crossing_roots`` is
patched to name it (the test_clearance.py ``_fixture_journals`` precedent), so nothing
is written under the live corpus.

    python3 cairn/devices/cairn/machines/harbor_master/proofs/test_watch_receives_a_finding.py   # exit 0 = green
"""

from __future__ import annotations

import contextlib
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[6]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.devices.cairn.machines.harbor_master import clearance as _clearance  # noqa: E402
from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402
from cairn.devices.cairn.machines.harbor_master.device import HarborMasterDevice  # noqa: E402

def _main_tree() -> Path:
    import subprocess
    common = subprocess.run(["git", "-C", str(_REPO_ROOT), "rev-parse", "--path-format=absolute",
                             "--git-common-dir"], capture_output=True, text=True)
    return Path(common.stdout.strip()).parent if common.returncode == 0 else _REPO_ROOT


def _root_the_class_defs_if_this_is_a_worktree() -> None:
    """The hollow runs this proof in a /tmp worktree with no CairnCommons beside it, so
    emit's ``load_class_def`` finds no ``code-seam`` and the red-finding tooth reads red at
    HEAD (measured 2026-10-03). The node classes are read from the main tree's commons —
    the test_clearance.py ``_correct_the_corpus_roots_if_this_is_a_worktree`` precedent,
    narrowed to the one reader this proof reaches; the fixture ticket stays in its world."""
    if _REPO_ROOT.resolve() == _main_tree().resolve():
        return
    from cairn.tools.base import transitions as _t
    classes, real_load = _main_tree().parent / "CairnCommons" / "node_classes", _t.load_class_def

    def _rooted_load(node_class, *, root=None):
        if root is None or not Path(root).is_dir():
            root = classes
        return real_load(node_class, root=root)

    _t.load_class_def = _rooted_load


_root_the_class_defs_if_this_is_a_worktree()

PROVES = {
    "a88d6a368cfb": {
        "all": "test_the_watch_verb_receives_a_finding",
    },
}

TID = "ab12cd34ef56"
AT_REST = "code-seam@v2: THINKME -> TICKETME -> BUILDME -> PROVEME -> [PROVED]"
NOT_AT_REST = "code-seam@v2: THINKME -> TICKETME -> [BUILDME] -> PROVEME -> PROVED"


def _world(workflow: str = AT_REST, *, watchme=None) -> Path:
    world = scratch_dir("watch-receives-a-finding-")
    tickets = world / "commons" / "tickets"
    tickets.mkdir(parents=True)
    doc = {"id": TID, "title": "fixture-watched", "workflow_and_state": workflow,
           "watchme": {"probe": "comp/probes/p.py"} if watchme is None else watchme}
    (tickets / f"{TID}-fixture-watched.json").write_text(json.dumps(doc, indent=2), "utf-8")
    (world / "comp" / "probes").mkdir(parents=True)
    (world / "comp" / "intention+why.json").write_text("{}", "utf-8")
    (world / "comp" / "probes" / "p.py").write_text("", "utf-8")
    return world


def _ticket(world: Path) -> Path:
    return world / "commons" / "tickets" / f"{TID}-fixture-watched.json"


@contextlib.contextmanager
def _standing(world: Path):
    real = _clearance._crossing_roots
    _clearance._crossing_roots = lambda: {"repo": world, "commons": world / "commons",
                                          "instance": world / "instance"}
    try:
        yield
    finally:
        _clearance._crossing_roots = real


def _watch(body: dict, sender: str | None = "fixture_prober") -> dict:
    env = {"id": "fixture-watch", "to": "harbor_master", "verb": "watch",
           "why": "fixture WATCHME finding", "body": body}
    if sender is not None:
        env["sender"] = sender
    return HarborMasterDevice()._handle_watch(env)


# --- teeth ------------------------------------------------------------------

def test_a_red_finding_sends_the_ticket_to_fixme():
    world = _world()
    with _standing(world):
        reply = _watch({"ticket": TID, "holds": False, "finding": "fixture finding"})
    assert reply.get("accepted") is True and reply.get("acted") == "fixme", reply
    doc = json.loads(_ticket(world).read_text("utf-8"))
    assert "[FIXME:waiting]" in doc["workflow_and_state"], doc["workflow_and_state"]
    assert doc.get("fixme") == [{"n": 1, "kind": "watchme", "missing": "fixture finding"}], \
        doc.get("fixme")
    hist = world / "comp" / "history.json"
    assert hist.is_file(), "no crossing was journaled beside the probe's charter"
    raw = json.loads(hist.read_text("utf-8"))
    records = raw.get("entries", raw) if isinstance(raw, dict) else raw
    last = records[-1]
    assert last.get("to") == "FIXME", last
    assert "WATCHME finding" in json.dumps(last), \
        f"the journal record does not say it is a WATCHME finding: {last}"


def test_a_green_finding_writes_nothing():
    world = _world()
    before = _ticket(world).read_bytes()
    with _standing(world):
        reply = _watch({"ticket": TID, "holds": True, "finding": ""})
    assert reply.get("accepted") is True and reply.get("acted") == "none", reply
    assert _ticket(world).read_bytes() == before, "a green finding changed the ticket"
    assert not (world / "comp" / "history.json").exists(), "a green finding journaled a crossing"


def test_a_malformed_watch_is_refused_by_name():
    cases = [
        ({"holds": False, "finding": "x"}, "fixture_prober", None, "ticket"),
        ({"ticket": "ffffffffffff", "holds": False, "finding": "x"}, "fixture_prober", None,
         "ticket"),
        ({"ticket": TID, "holds": "yes", "finding": "x"}, "fixture_prober", None, "holds"),
        ({"ticket": TID, "holds": False, "finding": ""}, "fixture_prober", None, "finding"),
        ({"ticket": TID, "holds": False, "finding": "x"}, "fixture_prober", {}, "probe"),
        ({"ticket": TID, "holds": False, "finding": "x"}, None, None, "sender"),
    ]
    for body, sender, watchme, field in cases:
        world = _world(watchme=watchme)
        before = _ticket(world).read_bytes()
        with _standing(world):
            try:
                reply = _watch(body, sender)
            except Exception as exc:  # noqa: BLE001
                raise AssertionError(f"{body!r} raised instead of refusing: {exc!r}") from exc
        assert reply.get("accepted") is False, f"{body!r} was not refused: {reply}"
        assert field in reply.get("reason", ""), \
            f"{body!r}'s refusal does not name {field!r}: {reply.get('reason')!r}"
        assert _ticket(world).read_bytes() == before, f"{body!r} changed the ticket"


def test_a_ticket_not_at_rest_is_not_moved():
    world = _world(NOT_AT_REST)
    before = _ticket(world).read_bytes()
    with _standing(world):
        reply = _watch({"ticket": TID, "holds": False, "finding": "fixture finding"})
    assert reply.get("accepted") is True and reply.get("acted") == "none", reply
    assert "BUILDME" in reply.get("said", ""), f"the reply does not name the cursor: {reply}"
    assert _ticket(world).read_bytes() == before, "a ticket not at rest was moved"


def test_the_watch_verb_receives_a_finding():
    """The composite tooth (the falsifier carries no numbered clauses): every narrow tooth,
    end to end, plus the verb declared on the bus menu."""
    assert "watch" in HarborMasterDevice().declared_verbs(), "harbor_master declares no watch verb"
    test_a_red_finding_sends_the_ticket_to_fixme()
    test_a_green_finding_writes_nothing()
    test_a_malformed_watch_is_refused_by_name()
    test_a_ticket_not_at_rest_is_not_moved()


if __name__ == "__main__":
    checks = [
        test_a_red_finding_sends_the_ticket_to_fixme,
        test_a_green_finding_writes_nothing,
        test_a_malformed_watch_is_refused_by_name,
        test_a_ticket_not_at_rest_is_not_moved,
        test_the_watch_verb_receives_a_finding,
    ]
    failures = 0
    for check in checks:
        try:
            check()
            print(f"  PASS  {check.__name__}")
        except Exception as exc:  # noqa: BLE001
            failures += 1
            print(f"  FAIL  {check.__name__}: {type(exc).__name__}: {exc}")
    if failures:
        print(f"RED — {failures} tooth/teeth bit")
        raise SystemExit(1)
    print("green — a red WATCHME finding sends its ticket to FIXME, a green one writes nothing")
