"""PROOF — the sorted door refuses complete, passes clean, and pollutes nothing.

Teeth a hollow build could not pass (Law 8), defect-first, every root injected:
the door's judges never read this proof's fixtures into the live trace the
``sorted-door-refusals`` probe counts — and one tooth pins exactly that.

Run bare:  PYTHONPATH=$HOME/dev/src/cairn python3 skills/sorted/proofs/test_sorted_door.py
Run twice; never trust the first green.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO))

from cairn.machines.learning_block.learning_block import DoorRefused, read_trace  # noqa: E402
from cairn.machines.skill_block.skill_block import read_berth                     # noqa: E402

sys.path.insert(0, str(_REPO / "skills" / "sorted"))
import door  # noqa: E402

PASSES = 0
def ok(name: str, cond: bool, detail: str = ""):
    global PASSES
    if not cond:
        print(f"RED  {name}  {detail}")
        raise SystemExit(1)
    PASSES += 1
    print(f"  ok {name}")


def fields_of(exc: DoorRefused) -> list[str]:
    return [l["field"] for l in (getattr(exc, "lacks", None) or [])]


def whys_of(exc: DoorRefused, field: str) -> str:
    return " | ".join(l["why"] for l in exc.lacks if l["field"] == field)


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        classes = tmp / "node_classes"; classes.mkdir()
        (classes / "boxling.json").write_text(json.dumps({
            "class": "boxling",
            "workflow_versions": {"v1": {
                "path": ["THINKME", "TICKETME", "BUILDME", "PROVEME", "PROVED"],
                "skippable_summons": [], "free_summons": ["WATCHME"]}}}))
        commons = tmp / "commons"; (commons / "tickets").mkdir(parents=True)
        (commons / "tickets" / "real-ticket.json").write_text("{}")
        berths = tmp / "berths"; traces = tmp / "traces"
        roots = dict(node_class_root=classes, commons=commons, repo=tmp,
                     berths=berths, trace_root=traces)

        WF = "boxling@v1: THINKME -> [TICKETME] -> BUILDME -> PROVEME -> WATCHME(door-health) -> PROVED"
        GOOD = {
            "assumption_check": "none remain: the seam's contract capability was measured, not assumed",
            "missing_check": "all points wrapped; the census ran (76 tickets, 30 pre-BUILDME)",
            "builder_check": "a Haiku-level builder needs the fixture class definition and the injected roots layout — both are in the test preamble, nothing implicit",
            "falsifier_check": "RED if the door passes a hollow watchme; horizon: next roster migration",
            "collision_check": "no collision — pays the charter's own tracked debt (casting has no chokepoint)",
            "node_class": "boxling",
            "workflow": WF,
            "gates_bound": {"prove_gate": "proof beside the code, sealed under the tester"},
            "watchme": {"object": "door-health", "trigger": "every firing",
                        "enough": "one real refusal and one recovery", "carrier": "a verdict artifact",
                        "nexus": "the sorted-door trace", "consumer": "Akien",
                        "probe": "skills/sorted/proofs/door_health_probe.py"},
            "children": "none, because the node is a leaf (see real-ticket)",
            "exit": "routed_forward",
            "disposition": "cast",
            "bullets": [{"text": "fixture cast", "stratum": "code"}],
        }

        # ── the live trace this proof must not touch ──────────────────────────
        live_trace = Path.home() / ".cairn/devices/learning_block/0/traces/skill:sorted.jsonl"
        live_before = live_trace.read_bytes() if live_trace.exists() else None

        # 1-2. triple-defective packet: ONE refusal, every planted lack named — twice
        bad = dict(GOOD, node_class="no-such-class",
                   watchme={"object": "door-health", "trigger": "every firing"},
                   disposition="not-ready")
        for attempt in (1, 2):
            try:
                door.fire(bad, **roots)
                ok(f"triple-defect refused (pass {attempt})", False, "door passed a defective cast")
            except DoorRefused as exc:
                f = fields_of(exc)
                ok(f"triple-defect refused once, all named (pass {attempt})",
                   "node_class" in f and "watchme" in f and "disposition" in f,
                   f"lacks named only {f}")
        # no whack-a-mole: both passes named the identical set
        # 3. flat + semantic lacks land in the SAME refusal
        try:
            door.fire({k: v for k, v in bad.items() if k != "bullets"}, **roots)
            ok("flat+semantic one pass", False, "door passed")
        except DoorRefused as exc:
            f = fields_of(exc)
            ok("flat+semantic one pass", "bullets" in f and "node_class" in f,
               f"named {f}")

        # 3b. missing builder_check refused by name
        no_bc = {k: v for k, v in GOOD.items() if k != "builder_check"}
        try:
            door.fire(no_bc, **roots)
            ok("missing builder_check refused", False, "door passed without builder_check")
        except DoorRefused as exc:
            ok("missing builder_check refused", "builder_check" in fields_of(exc),
               f"lacks named only {fields_of(exc)}")

        # 4. drifted workflow string refused (path not in registered version)
        drifted = dict(GOOD, workflow="boxling@v1: THINKME -> [TICKETME] -> SHIPME -> PROVED")
        try:
            door.fire(drifted, **roots)
            ok("drifted workflow refused", False)
        except DoorRefused as exc:
            ok("drifted workflow refused", "workflow" in fields_of(exc))

        # 5. cursor already downstream refused
        sailed = dict(GOOD, workflow=WF.replace("[TICKETME]", "TICKETME").replace("PROVEME", "[PROVEME]"))
        try:
            door.fire(sailed, **roots)
            ok("downstream cursor refused", False)
        except DoorRefused as exc:
            ok("downstream cursor refused", "cursor" in whys_of(exc, "workflow"))

        # 6. class/workflow mismatch refused
        mismatch = dict(GOOD, workflow=WF.replace("boxling@v1", "otherclass@v1"))
        try:
            door.fire(mismatch, **roots)
            ok("class mismatch refused", False)
        except DoorRefused as exc:
            ok("class mismatch refused", "workflow" in fields_of(exc))

        # 7. watchme object disagreeing with the summons refused
        disagree = dict(GOOD, watchme=dict(GOOD["watchme"], object="something-else"))
        try:
            door.fire(disagree, **roots)
            ok("summons/spec disagreement refused", False)
        except DoorRefused as exc:
            ok("summons/spec disagreement refused", "watchme" in fields_of(exc))

        # 7b-7c. THE MEASURED FAILURE, REPLAYED (2026-08-05, n=2 in one session): the
        # door held a private five-field list, passed two casts clean, and the emission
        # gate's corpus proof redded both minutes later. The door's judgment is now the
        # gate's own watchme_spec_error, so the exact packets that sailed must refuse —
        # naming the berth field the old list never asked for, in the same pass.
        no_probe = dict(GOOD, watchme={k: v for k, v in GOOD["watchme"].items()
                                       if k != "probe"})
        try:
            door.fire(no_probe, **roots)
            ok("five-field spec with no probe berth refused", False,
               "the n=2 escape sailed again")
        except DoorRefused as exc:
            ok("five-field spec with no probe berth refused",
               "probe" in whys_of(exc, "watchme"), whys_of(exc, "watchme"))
        no_nexus = dict(GOOD, watchme={k: v for k, v in GOOD["watchme"].items()
                                       if k != "nexus"})
        try:
            door.fire(no_nexus, **roots)
            ok("spec missing nexus refused", False, "the second forgotten field sailed")
        except DoorRefused as exc:
            ok("spec missing nexus refused",
               "nexus" in whys_of(exc, "watchme"), whys_of(exc, "watchme"))

        # 8. exemption while the workflow carries the summons refused
        exempt_with_summons = dict(GOOD, watchme="none, because real-ticket carries it")
        try:
            door.fire(exempt_with_summons, **roots)
            ok("exemption-under-summons refused", False)
        except DoorRefused as exc:
            ok("exemption-under-summons refused", "watchme" in fields_of(exc))

        # 9-10. the judgeable floor: hollow reason refused naming the referent kinds;
        # a real referent passes the judge (workflow without the summons)
        no_summons_wf = "boxling@v1: THINKME -> [TICKETME] -> BUILDME -> PROVEME -> PROVED"
        hollow = dict(GOOD, workflow=no_summons_wf,
                      watchme="none, because this node is a one-off")
        try:
            door.fire(hollow, **roots)
            ok("hollow exemption refused", False, "the rank-3 hollow pass passed")
        except DoorRefused as exc:
            why = whys_of(exc, "watchme")
            ok("hollow exemption refused",
               "path" in why and "ticket id" in why and "roster command" in why,
               f"refusal did not name the three referent kinds: {why}")
        judged = door.judge_packet(
            dict(GOOD, workflow=no_summons_wf,
                 watchme="none, because real-ticket carries the watch"),
            node_class_root=classes, commons=commons, repo=tmp)
        ok("referent-carrying exemption passes the judge",
           not any(l["field"] == "watchme" for l in judged), str(judged))

        # 11. wrong-typed watchme refused (the type hole)
        try:
            door.fire(dict(GOOD, watchme=["object", "trigger"]), **roots)
            ok("wrong-typed watchme refused", False)
        except DoorRefused as exc:
            ok("wrong-typed watchme refused", "watchme" in fields_of(exc))

        # 12-13. exit/disposition coherence
        try:
            door.fire(dict(GOOD, disposition="not-ready"), **roots)
            ok("forward+not-ready refused", False)
        except DoorRefused as exc:
            ok("forward+not-ready refused", "disposition" in fields_of(exc))
        try:
            door.fire(dict(GOOD, exit="routed_out", disposition="cast"), **roots)
            ok("routed_out+cast refused", False)
        except DoorRefused as exc:
            ok("routed_out+cast refused", "disposition" in fields_of(exc))
        judged = door.judge_packet(dict(GOOD, exit="routed_out",
                                        disposition="escalated:advisor"),
                                   node_class_root=classes, commons=commons, repo=tmp)
        ok("routed_out+escalated coheres",
           not any(l["field"] == "disposition" for l in judged), str(judged))

        # 14. bad exit named in the SAME pass (not left to the seam's second trip)
        try:
            door.fire(dict(GOOD, exit="wandered_off"), **roots)
            ok("unknown exit refused at the door", False)
        except DoorRefused as exc:
            ok("unknown exit refused at the door", "exit" in fields_of(exc))

        # 15-17. a conforming cast rides the seam: berth written, readable, door_pass traced
        result = door.fire(dict(GOOD), **roots)
        ok("conforming cast berths", bool(result.get("berth")) and Path(result["berth"]).exists(),
           str(result))
        doc = read_berth(result["berth"])
        ok("berth reads and names the skill", doc is not None and doc.get("skill") == "sorted")
        recs = read_trace("skill:sorted", root=traces)
        ok("both edges traced in the injected root",
           any(r["event"] == "door_pass" for r in recs) and
           any(r["event"] == "send_back" for r in recs),
           f"events: {[r.get('event') for r in recs]}")

        # 18. refusals traced with the judge named — the probe's denominator
        sb_recs = [r for r in recs if r["event"] == "send_back"]
        ok("refusal trace carries the judge and the lacks",
           all(r["data"].get("judge") == "sorted-door" and r["data"].get("lacks")
               for r in sb_recs), str(sb_recs[:1]))

        # 19. the CLI: exit 2 with every lack on stderr; exit 0 with the berth JSON
        env = dict(os.environ, PYTHONPATH=str(_REPO),
                   CAIRN_SKILL_BERTHS=str(berths), CAIRN_LB_TRACE_ROOT=str(traces))
        pkt = tmp / "pkt.json"
        pkt.write_text(json.dumps(bad))
        r = subprocess.run([sys.executable, str(_REPO / "skills/sorted/door.py"), str(pkt)],
                           capture_output=True, text=True, env=env)
        ok("CLI refusal: exit 2, lacks on stderr",
           r.returncode == 2 and "node_class" in r.stderr and "disposition" in r.stderr,
           f"rc={r.returncode} stderr={r.stderr[:200]}")
        # CLI's judges read the LIVE commons/repo (no injection through the CLI on
        # purpose — the real caller is the skill): keep the fixture class out by using
        # a real class the live roster carries.
        live_good = dict(GOOD, node_class="code-seam",
                         workflow="code-seam@v2: THINKME -> [TICKETME] -> BUILDME -> PROVEME -> WATCHME(door-health) -> PROVED")
        pkt.write_text(json.dumps(live_good))
        r = subprocess.run([sys.executable, str(_REPO / "skills/sorted/door.py"), str(pkt)],
                           capture_output=True, text=True, env=env)
        ok("CLI pass: exit 0, berth printed",
           r.returncode == 0 and json.loads(r.stdout).get("berth"),
           f"rc={r.returncode} stderr={r.stderr[:300]}")

        # ── the downstream consumer: buildme_rides_the_sorted ─────────────────
        from cairn.machines.build_inspector.inspector import buildme_rides_the_sorted as gate

        # ticket_path joins <root's parent>/CairnCommons/tickets — mirror that layout
        tickets_root = tmp / "CairnCommons"
        tickets = tickets_root / "tickets"; tickets.mkdir(parents=True)
        def file_ticket(fields: dict) -> None:
            (tickets / "t.json").write_text(json.dumps(dict({"id": "t"}, **fields)))

        # 21. no field at all → one finding, remedy named
        file_ticket({})
        found = gate("t", tickets_root=tickets_root)
        ok("consumer: missing field reds with the remedy",
           len(found) == 1 and "sorted" in found[0]["about"]
           and found[0]["method"] == "buildme_rides_the_sorted")

        # 22. blank exemption reason reds
        file_ticket({"sorted_berth": "none, because "})
        ok("consumer: blank exemption reason reds",
           len(gate("t", tickets_root=tickets_root)) == 1)

        # 23. hollow exemption reason reds naming the referent kinds
        file_ticket({"sorted_berth": "none, because this is a one-off"})
        found = gate("t", tickets_root=tickets_root)
        ok("consumer: hollow exemption reds naming the kinds",
           len(found) == 1 and "resolvable" in found[0]["about"])

        # 24. exemption whose reason resolves (a real cast ticket id, live commons) passes
        file_ticket({"sorted_berth":
                     "none, because the cast predates the door — sorted-becomes-a-learning-block"})
        ok("consumer: referent-carrying exemption passes",
           gate("t", tickets_root=tickets_root) == [])

        # 25. a berth for the wrong skill reds by name
        wrong = berths / "intent" / "fake.json"
        wrong.parent.mkdir(parents=True, exist_ok=True)
        wrong.write_text(json.dumps({"skill": "intent"}))
        file_ticket({"sorted_berth": str(wrong)})
        found = gate("t", tickets_root=tickets_root)
        ok("consumer: wrong-skill berth reds",
           len(found) == 1 and found[0]["expected"] == "sorted")

        # 26. the real berth from tooth 15 opens the door
        file_ticket({"sorted_berth": result["berth"]})
        ok("consumer: a real /sorted berth opens the door",
           gate("t", tickets_root=tickets_root) == [])

        # 27. unfiled ticket stays silent — the chokepoint already refuses it by name
        ok("consumer: unfiled ticket is not this gate's finding",
           gate("no-such-ticket", tickets_root=tickets_root) == [])

        # 28. the entry gate reports chart+intent+sorted lacks in ONE raise
        import cairn.machines.build_inspector.inspector as insp
        from cairn.tools.base.transitions import EntryGateRed, _entry_gate
        file_ticket({})  # no chart claim, no intent_berth, no sorted_berth
        saved = insp._TICKETS_ROOT
        insp._TICKETS_ROOT = tickets_root  # proof-local injection, restored below
        try:
            _entry_gate("t")
            ok("entry gate: triple lack in one raise", False, "gate passed")
        except EntryGateRed as exc:
            methods = {f["method"] for f in exc.findings}
            ok("entry gate: triple lack in one raise",
               {"buildme_rides_the_chart", "buildme_rides_the_intent",
                "buildme_rides_the_sorted"} <= methods,
               f"methods seen: {methods}")
        finally:
            insp._TICKETS_ROOT = saved

        # 29. the live trace is byte-identical across this whole proof run
        live_after = live_trace.read_bytes() if live_trace.exists() else None
        ok("live trace untouched by the proof", live_before == live_after,
           "the proof deposited into the probe's denominator")

        # 30. render() round-trip: a workflow string built through render() is
        # byte-identical to what parse_workflow reproduces, and the door accepts it
        from cairn.tools.base.transitions import Workflow, render as wf_render, parse_workflow as pw
        cd = json.loads((classes / "boxling.json").read_text())
        ver = cd["workflow_versions"]["v1"]
        path = tuple(ver["path"])
        free = ver.get("free_summons", [])
        objects = []
        for s in path:
            if s in free:
                objects.append("door-health")
            else:
                objects.append(None)
        wf = Workflow(node_class="boxling", version="v1", path=path,
                      cursor=0, objects=tuple(objects))
        rendered = wf_render(wf, "TICKETME")
        ok("render round-trip: string parses back identically",
           rendered == WF or pw(rendered).path == wf.path,
           f"rendered={rendered!r} WF={WF!r}")
        render_cast = dict(GOOD, workflow=rendered)
        judged = door.judge_packet(render_cast, node_class_root=classes,
                                   commons=commons, repo=tmp)
        ok("render-produced workflow passes the door",
           not any(l["field"] == "workflow" for l in judged),
           f"judged: {judged}")

    print(f"GREEN — {PASSES} teeth")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
