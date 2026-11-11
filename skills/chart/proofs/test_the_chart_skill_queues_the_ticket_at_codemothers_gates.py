"""Proof for ticket 1800df654068 — the /chart skill drafts each stage on the ticket and queues it
at CodeMother's gate.

RULE 1 (skills included): nothing outside a device reaches into its code. Measured 2026-11-10:
skills/chart/SKILL.md told the builder to import cairn.devices.codemother.machines fourteen
times. Outline 9.6 (Q#81): each chart stage is a gate machine answering ``queueme <fileref>``
and the ticket queues itself to each; there is no chart verb. So the skill charts through the
ticket: ``live.py draft`` puts the stage's draft on the plan, ``live.py queue`` has the ticket
queue itself at that stage's gate.

Every tooth runs in a scratch world: a tempdir tickets store (the live store charter copied in,
one fixture plan and state), ``ticket_file._TICKETS`` pointed at it, the ticket's diagnostic
roots under the same tempdir, and ``live._gates`` swapped for a recording participant, so no
bus is dialled and no trouble reaches ~/.cairn. ``skills.chart.live`` is imported inside each
tooth.

    python3 skills/chart/proofs/test_the_chart_skill_queues_the_ticket_at_codemothers_gates.py
"""

from __future__ import annotations

import contextlib
import importlib
import io
import json
import re
import shutil
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {
    "1800df654068": {
        "1": "test_the_skill_names_no_codemother_module",
        "2": "test_draft_writes_the_stage_onto_the_plan_and_refuses_a_stranger",
        "3": "test_queue_asks_the_stage_gate_once_and_prints_the_berth",
        "4": "test_a_refusing_or_absent_gate_makes_queue_exit_nonzero_with_the_reason",
    },
}

_TID = "fixture1800a"
_STORE_CHARTER = _REPO.parent / "CairnCommons" / "tickets" / "_charter+why.json"
if not _STORE_CHARTER.is_file():
    _STORE_CHARTER = Path.home() / "dev" / "src" / "CairnCommons" / "tickets" / "_charter+why.json"


class _Spy:
    """A bus participant answering request() from a script and recording every ask."""

    def __init__(self, replies):
        self._replies = list(replies)
        self.asked: list[dict] = []

    def request(self, **kw):
        self.asked.append(kw)
        return self._replies.pop(0)

    def post(self, **kw):
        return {"id": "post"}


@contextmanager
def _world(spy=None):
    """Yield (live module, plan path, tmp root) inside a scratch tickets store."""
    import cairn.tools.base.ticket_file as tf
    from cairn.machines.ticket.ticket import Ticket
    live = importlib.import_module("skills.chart.live")
    tmp = Path(tempfile.mkdtemp(prefix="t1800-chart-"))
    store = tmp / "tickets"
    store.mkdir()
    shutil.copy(_STORE_CHARTER, store / "_charter+why.json")
    plan = store / f"{_TID}-a-fixture-ticket.json"
    plan.write_text(json.dumps({"id": _TID, "title": "a fixture ticket",
                                "owning_intention": "skills/chart/intention+why.json"},
                               indent=2) + "\n")
    tf.state_path(plan).write_text(json.dumps(
        {"workflow_and_state": "code-seam@v2: THINKME -> [TICKETME:waiting] -> BUILDME -> "
                               "PROVEME -> PROVED", "node_class": "code-seam"}, indent=2) + "\n")
    roots = {k: tmp / k for k in ("repo", "commons", "instance")}
    for p in roots.values():
        p.mkdir()
    was_tickets = tf._TICKETS
    had_roots = "_diagnostic_roots" in Ticket.__dict__
    was_roots = Ticket.__dict__.get("_diagnostic_roots")
    had_gates = hasattr(live, "_gates")
    was_gates = getattr(live, "_gates", None)
    tf._TICKETS = store
    Ticket._diagnostic_roots = roots
    if spy is not None:
        live._gates = lambda: spy
    try:
        yield live, plan, tmp
    finally:
        tf._TICKETS = was_tickets
        if had_roots:
            Ticket._diagnostic_roots = was_roots
        else:
            del Ticket._diagnostic_roots
        if had_gates:
            live._gates = was_gates
        elif hasattr(live, "_gates"):
            del live._gates
        shutil.rmtree(tmp, ignore_errors=True)


def _run(live, argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = live._main(argv)
        except SystemExit as exc:
            code = exc.code if isinstance(exc.code, int) else 1
    return code, out.getvalue(), err.getvalue()


def test_the_skill_names_no_codemother_module():
    pat = re.compile(r"cairn\.devices\.codemother")
    for rel in ("skills/chart/SKILL.md", "skills/chart/live.py"):
        hits = [n for n, line in enumerate((_REPO / rel).read_text(encoding="utf-8").splitlines(), 1)
                if pat.search(line)]
        assert not hits, f"{rel} names a cairn.devices.codemother module at lines {hits}"


def test_draft_writes_the_stage_onto_the_plan_and_refuses_a_stranger():
    with _world() as (live, plan, tmp):
        packet = {"request": "a fixture request", "intent": "the fixture's intent"}
        pfile = tmp / "orient.json"
        pfile.write_text(json.dumps(packet))
        code, out, err = _run(live, ["draft", _TID, "orient", str(pfile)])
        assert code == 0, f"draft exited {code}: {out} {err}"
        chart = json.loads(plan.read_text(encoding="utf-8")).get("chart") or {}
        assert chart.get("orient") == packet, f"the plan's chart.orient is {chart.get('orient')!r}"
        code, out, err = _run(live, ["draft", _TID, "launch", str(pfile)])
        assert code != 0, f"draft of a stage outside the chart exited 0: {out}"
        assert "launch" not in (json.loads(plan.read_text(encoding="utf-8")).get("chart") or {})


def test_queue_asks_the_stage_gate_once_and_prints_the_berth():
    spy = _Spy([{"body": {"accepted": True, "passed": True, "berth": "/scratch/survey-1.json"}}])
    with _world(spy) as (live, plan, tmp):
        code, out, err = _run(live, ["queue", _TID, "survey"])
        assert code == 0, f"queue exited {code}: {out} {err}"
        assert len(spy.asked) == 1, f"queue asked {len(spy.asked)} times: {spy.asked}"
        ask = spy.asked[0]
        assert ask.get("to") == "codemother" and ask.get("verb") == "machines/survey/queueme", ask
        assert ask.get("body") == {"fileref": str(plan)}, ask
        assert "/scratch/survey-1.json" in out, f"the berth is not printed: {out!r}"


def test_a_refusing_or_absent_gate_makes_queue_exit_nonzero_with_the_reason():
    refusal = {"body": {"accepted": True, "passed": False,
                        "lacks": [{"kind": "survey", "why": "holdings name no address"}]}}
    with _world(_Spy([refusal])) as (live, plan, tmp):
        code, out, err = _run(live, ["queue", _TID, "survey"])
        assert code != 0, f"a refused stage exited 0: {out}"
        assert "holdings name no address" in out + err, f"the reason is not said: {out!r} {err!r}"
    with _world(_Spy([{"body": {"is_bounce": True, "reason": "no handler"}}])) as (live, plan, tmp):
        code, out, err = _run(live, ["queue", _TID, "survey"])
        assert code != 0, f"a bounced ask exited 0: {out}"
        assert (out + err).strip(), "a bounced ask said nothing"


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
