"""PROBE — does any CLIENT in class-space still pay the heartbeat to ask one question?

Berth for the WATCHME that ticket ``fc93d8cd5961`` (a-client-reaches-and-a-runner-beats)
carries. Berthed beside ``cairn/tools/bus_client`` because that is WHAT IT WATCHES: the two faces
of ``bus_client.py`` (it moved there from ``cairn/tools/base`` on 2026-09-09, ticket
dd8ad9702b49, and this probe moved with it — a probe berths with what it watches) — ``connect_bus``/``connect_system`` (RUN the system: a full
``GroundLoopDevice.beat``) and ``reach`` (USE it: wire, pulse only the shims addressed).

THE MEASUREMENT THAT BORE IT (2026-09-09, the efficiency eval Akien asked for): one
``connect_bus()`` on this machine costs **23.5s** and one ``reach("inference_domain")``
costs **0.23s**, and five clients — the chart's ``live.py``, the librarian's ``live.py``,
the intention extractor's ``live.py``, codemother's ``watch.py`` and ``seed_trees.py`` —
were paying the beat to ask for one embedding. A voyage's chart chain calls ``counsel`` and
``learn`` roughly fifteen times, so the five cost about six minutes of every voyage and
answered nothing the beat was for. ``reach`` had been sitting in the same file since
2026-09-07 with a docstring explaining exactly this; the clients were not switched because
nothing REDDED a client that beats. This is that red.

WHAT IS AND IS NOT A CLIENT, declared here rather than left to the reader. A RUNNER means to
run the system and wants the roster a real beat produces — and the roster of runners is
short, named, and on disk:

  * ``cairn/devices/web_server/listener.py`` — the web server, whose nav IS the beat's roster;
  * ``cairn/devices/cairn/machines/ground_loop/__main__.py`` — the heartbeat's own process;
  * ``cairn/tools/bus_client/bus_client.py`` — the definitions themselves;
  * any ``proofs/`` tree — a proof may beat on purpose to measure what a beat costs.

Everything else that CALLS ``connect_bus`` or ``connect_system`` is a client, and a client
that beats is the finding, with the file that grew it. The walk is an AST walk over CALL
nodes, not a grep: the word ``connect_bus`` in a docstring or a comment is not a caller
(``reach``'s own docstring names it twice, correctly), and a name-only match would red the
explanation of the rule.

MEMOIZED, NON-NEGOTIABLY. Live trouble ``beat-tail-re-walks-corpora-no-sieve-counts``:
roughly 78 probes re-walk corpora that did not move, once per beat, forever, and nothing
would red the 79th. This walk goes through ``settled()`` on class-space, so a beat where no
source moved costs a stat sweep (5.9ms measured) and no parse. This probe is not the 79th.

WHY THE CLEAR NEEDS THE PROOF'S SEAL AND NOT ONLY THE COUNT. A count of zero over the live
tree is one half; it is also what a walk that matches NOTHING returns. The ticket's
``enough`` asks for the fixture tooth to have BITTEN — the proof beside this file plants a
client caller in a temp tree and asserts the walk names it — and a tooth that never bit is
unmeasured. So the clear reads the proof's standing seal (``validation.standing``): green
with a matching fingerprint means the tooth ran and bit; anything else means the zero is
unproven and the watch stays open.

FILES ONLY: it parses ``*.py`` under class-space — no device, no bus, no network.

AUTHORITY: none. It deposits and pokes; re-opening the design is the owner's act (Law 6).
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

from cairn.tools.base.probe import Probe, owning_ticket, once
from cairn.tools.base.settled import settled

_REPO_ROOT = Path(__file__).resolve().parents[4]

_OWNING_TICKET = "a-client-reaches-and-a-runner-beats"

# THE FACES THAT BEAT. A Call to either of these outside the roster is a client paying for a
# heartbeat it did not want.
BEATING_FACES = frozenset({"connect_bus", "connect_system"})

# THE RUNNER ROSTER — repo-relative paths that MEAN to run the system. Short by design: a
# roster that grows is the finding leaking back in under a different name.
RUNNER_ROSTER = frozenset({
    "cairn/devices/web_server/listener.py",
    "cairn/devices/cairn/machines/ground_loop/__main__.py",
    "cairn/tools/bus_client/bus_client.py",
})

# A proof may beat on purpose (to measure the beat), so any proofs/ tree is off the walk.
_EXEMPT_SEGMENTS = frozenset({"proofs", "__pycache__", ".git", "node_modules"})

# THE PROOF WHOSE SEAL THE CLEAR READS — the fixture tooth lives there.
PROOF = _REPO_ROOT / "cairn" / "tools" / "bus_client" / "proofs" / "test_a_client_reaches_and_never_beats.py"

# THE HORIZON. Same tracked debt as the siblings at this address: 1000 pulses stands for
# "clearly a long standing" until the beat rate is a real number.
_HORIZON = 1000


def _callee_name(node: ast.Call) -> str | None:
    fn = node.func
    if isinstance(fn, ast.Name):
        return fn.id
    if isinstance(fn, ast.Attribute):
        return fn.attr
    return None


def _is_exempt(rel: str) -> bool:
    if rel in RUNNER_ROSTER:
        return True
    return any(seg in _EXEMPT_SEGMENTS for seg in Path(rel).parts[:-1])


def walk_client_callers(root: Path | str) -> list[dict]:
    """Every CALL of a beating face outside the runner roster, under ``root``.

    Pure over the tree: the same tree always gives the same list, sorted by file then line,
    so a proof can plant one caller and know exactly what comes back. A file that does not
    parse is skipped, not guessed at — a syntax error is somebody else's red."""
    root = Path(root)
    found: list[dict] = []
    for path in sorted(root.rglob("*.py")):
        try:
            rel = path.relative_to(root).as_posix()
        except ValueError:
            continue
        if _is_exempt(rel):
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (SyntaxError, UnicodeDecodeError, OSError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = _callee_name(node)
                if name in BEATING_FACES:
                    found.append({"file": rel, "line": node.lineno, "callee": name})
    return found


def survey_the_clients() -> dict:
    """The walk over live class-space, MEMOIZED on the tree's fingerprint."""
    callers = settled("client_callers_that_beat", _REPO_ROOT,
                      lambda: walk_client_callers(_REPO_ROOT))
    return {"client_callers": callers, "count": len(callers)}


def _tooth_has_bitten() -> dict:
    """Has the fixture tooth run and bitten? Read from the proof's STANDING seal — green with
    a matching fingerprint — never from memory of having run it."""
    from cairn.tools.base.validation import standing
    try:
        s = standing(str(PROOF))
    except Exception as e:  # noqa: BLE001 — an unreadable seal is "not proven", said loudly
        return {"proven": False, "why": f"standing() raised: {e!r}"}
    return {"proven": bool(s.get("proven")), "why": s.get("why")}


def _trigger(now, context: dict) -> bool:
    """TRUE the beat a client caller stands anywhere off the roster."""
    return once(context, "clients", survey_the_clients)["count"] > 0


def _enough(context: dict) -> bool:
    """CLEARED when the live count is zero AND the proof's fixture tooth stands sealed green
    — both can go back down: a sixth client re-opens the first, an edit to the walk or the
    proof expires the second."""
    s = once(context, "clients", survey_the_clients)
    return s["count"] == 0 and once(context, "tooth", _tooth_has_bitten)["proven"]


def _carry(context: dict) -> dict:
    s = once(context, "clients", survey_the_clients)
    return {
        "finding": "a client in class-space beats — it calls connect_bus/connect_system off "
                   "the runner roster to ask a question reach() answers in 0.23s",
        "client_callers": s["client_callers"],
        "count": s["count"],
        "ticket": owning_ticket(_OWNING_TICKET),
        "against_falsifier": ("WRONG INTENT if the five were switched and a sixth grew back: "
                              "the rule lived in a docstring and nothing enforced it, which "
                              "is the Law 4 IOU this probe exists to close."),
        "suggests": ("switch the caller to reach(<device>) unless it is a runner — and if it "
                     "IS a runner, the roster in this probe is where that fact is recorded, "
                     "with the file, not in a paragraph"),
    }


PROBE = Probe(
    why="does any client still pay the 23.5s heartbeat to ask one question? — five did on "
        "2026-09-09 while reach() sat two functions below with the explanation already written",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "hypothesize", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=_HORIZON,
)


if __name__ == "__main__":
    s = survey_the_clients()
    ctx = {"clients": s}
    print(json.dumps({"clients": s,
                      "tooth": _tooth_has_bitten(),
                      "would_trigger": _trigger(None, ctx),
                      "enough": _enough(ctx)}, indent=2))
