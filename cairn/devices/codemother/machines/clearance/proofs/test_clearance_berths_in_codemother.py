#!/usr/bin/env python3
"""Proof that the clearance gate berths in CodeMother, and the harbor answers no `clear`.

Akien 2026-11-10 (outline 9.4.1.5, Q#80): the harbor's verbs are status queries (show, get)
and crossing; it answers no gate and moves no ticket, and `clear` leaves. Outline 9.6 and
3.3.4.3 (Q#81): the gates are CodeMother's machines. Ticket 0be964512fb0 moves the module,
its proofs and its probes, and the gate answers queueme <fileref>.

The retired spellings are built from parts below, so this file never names them whole and
tooth (2) can read it like any other file.

Teeth, each importing the code under test at call time:
  (1) the module imports at its new address with clear, _decide and riders_of, and the old
      file is gone; every moved probe and proof stands at its new berth and not its old,
      the package files and the charter exist, and codemother's charter holds clearance;
  (2) no class-space file outside history, state, validations and journals names the old
      module, its probes or its moved proofs, dotted, slashed or path-joined;
  (3) lives at the harbor's own address (RULE 1: this proof may not import the harbor):
      cairn/devices/cairn/machines/harbor_master/proofs/test_the_harbor_answers_no_clear.py;
  (4) CodeMother declares no cross verb and holds the clearance gate; the gate, asked queueme
      <fileref> over a scratch world, derives the crossing and answers a clearance refusal;
  (5) no RULE 1 breach between codemother and harbor_master names clearance, and the total
      is not above 71 (measured 2026-11-11);
  (6) the four clearance probes' tickets name a probe under clearance/probes/ that exists;
  (7) the deprecation report runs from the new address;
  (8) lives at the Ticket's own address: cairn/machines/ticket/proofs/
      test_a_passed_ticket_crosses_through_the_gates_door.py;
  (9) `cairn codemother cross <ticket>` has the ticket queue itself at clearance.

    bin/cairn test cairn/devices/codemother/machines/clearance/proofs/test_clearance_berths_in_codemother.py
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

_REPO = Path(__file__).resolve().parents[6]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {"0be964512fb0": {"1": "test_the_module_berths_in_codemother",
                           "2": "test_no_class_space_file_names_the_old_berth",
                           "4": "test_the_gate_answers_queueme_with_a_clearance_refusal",
                           "5": "test_no_breach_joins_codemother_and_the_harbor_over_clearance",
                           "6": "test_the_probe_tickets_name_the_new_berth",
                           "7": "test_the_deprecation_report_runs_from_the_new_address",
                           "9": "test_the_cross_command_has_the_ticket_queue_itself"}}

NEW = "cairn/devices/codemother/machines/clearance"
NEW_DOTTED = "cairn.devices.codemother.machines.clearance"
_H = "harbor" + "_master"
OLD_DIR = "cairn/devices/cairn/machines/" + _H
PROBE_TICKETS = ("0354c0269ff7", "0cde908b8fbe", "2b16d2d8b056", "faa51bcfbdfc")
BREACH_CEILING = 71
_MOVED_PROOFS = ("test_clearance", "test_a_notified_file_is_covered", "test_" + "harbor_asks_the_real_host",
                 "test_the_proven_space_rule_follows_the_ticket_kind",
                 "test_" + _H + "_probes_report_to_the_watch")

# (old path under OLD_DIR, new path under NEW) for every moved source file — the ticket's
# forwarding order, written here because a hollow worktree has no commons beside it.
_MOVED_FILES = (
    ("clearance.py", "clearance.py"),
    ("probes/__init__.py", "probes/__init__.py"),
    ("probes/a_second_hand_meets_the_gate.py", "probes/a_second_hand_meets_the_gate.py"),
    ("probes/a_superseded_intention_is_never_silent.py", "probes/a_superseded_intention_is_never_silent.py"),
    ("probes/boat_owner_comes_from_the_boat.py", "probes/boat_owner_comes_from_the_boat.py"),
    ("probes/clearance_actually_gates.py", "probes/clearance_actually_gates.py"),
    ("proofs/test_a_notified_file_is_covered.py", "proofs/test_a_notified_file_is_covered.py"),
    ("proofs/test_clearance.py", "proofs/test_clearance.py"),
    ("proofs/test_clearance_accepts_a_recorded_approval.py", "proofs/test_clearance_accepts_a_recorded_approval.py"),
    ("proofs/test_clearance_reaches_trouble_through_its_tool.py",
     "proofs/test_clearance_reaches_trouble_through_its_tool.py"),
    ("proofs/test_clearance_reads_a_plan_approval.py", "proofs/test_clearance_reads_a_plan_approval.py"),
    ("proofs/test_" + "harbor_asks_the_real_host.py", "proofs/test_clearance_asks_the_real_host.py"),
    ("proofs/test_" + _H + "_probes_report_to_the_watch.py", "proofs/test_clearance_probes_report_to_the_watch.py"),
    ("proofs/test_the_proven_space_rule_follows_the_ticket_kind.py",
     "proofs/test_the_proven_space_rule_follows_the_ticket_kind.py"),
)

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def test_the_module_berths_in_codemother() -> None:
    import importlib
    bad = []
    try:
        mod = importlib.import_module(NEW_DOTTED + ".clearance")
        for name in ("clear", "_decide", "riders_of"):
            if not callable(getattr(mod, name, None)):
                bad.append(f"{name} missing at the new address")
    except Exception as exc:  # noqa: BLE001
        bad.append(f"new address does not import: {type(exc).__name__}: {exc}")
    if (_REPO / OLD_DIR / "clearance.py").exists():
        bad.append("the old module still stands")
    # The move is WHOLE (clause 1): every source file the forwarding order names stands at
    # its new berth and not at its old one, the package files beside them exist, and the
    # holder's charter says it holds the machine. Hollow measured each of these HOLLOW when
    # the tooth read only clearance.py (2026-11-11).
    for old, new in _MOVED_FILES:
        if not (_REPO / NEW / new).is_file():
            bad.append(f"{new} is not at {NEW}/")
        if (_REPO / OLD_DIR / old).exists():
            bad.append(f"{OLD_DIR}/{old} still stands")
    for new in ("__init__.py", "probes/__init__.py", "intention+why.json"):
        if not (_REPO / NEW / new).is_file():
            bad.append(f"{NEW}/{new} is absent")
    try:
        charter = json.loads((_REPO / NEW / "intention+why.json").read_text("utf-8"))
        if not (charter.get("why") or charter.get("what")):
            bad.append("the clearance charter carries no why")
    except Exception as exc:  # noqa: BLE001
        bad.append(f"the clearance charter does not parse: {type(exc).__name__}")
    try:
        cm = json.loads((_REPO / "cairn/devices/codemother/intention+why.json").read_text("utf-8"))
        if "clearance" not in (cm.get("held_machines") or []):
            bad.append("codemother's charter does not hold clearance")
    except Exception as exc:  # noqa: BLE001
        bad.append(f"codemother's charter does not parse: {type(exc).__name__}")
    check("test_the_module_berths_in_codemother", not bad, "; ".join(bad))


def test_no_class_space_file_names_the_old_berth() -> None:
    h = re.escape(_H)
    spellings = [h + r"\.clearance\b", h + r"/clearance", h + r" import clearance\b",
                 h + r"\"\s*/\s*\"clearance", h + r"[./]probes\b", h + r"\"\s*/\s*\"probes"]
    spellings += [h + r"/proofs/" + p + r"\b" for p in _MOVED_PROOFS]
    spellings.append(r"\btest_" + "harbor_asks_the_real_host\\b")
    r = subprocess.run(["git", "grep", "--untracked", "-nE", "|".join(spellings), "--", ".",
                        ":!*.jsonl", ":!*history.json", ":!*state.json", ":!*/validations/*"],
                       cwd=_REPO, capture_output=True, text=True)
    hits = [l for l in r.stdout.splitlines() if l.strip()]
    check("test_no_class_space_file_names_the_old_berth", r.returncode in (0, 1) and not hits,
          f"{len(hits)} hit(s): " + "; ".join(hits[:8]) if hits else r.stderr.strip())


class _Heard:
    """A participant that only listens: a refused queueme must post nothing and ask nothing."""

    def __init__(self) -> None:
        self.said: list[tuple[str, dict]] = []

    def request(self, **kw):
        self.said.append(("request", kw))
        return {"body": {"accepted": True}}

    def post(self, **kw):
        self.said.append(("post", kw))


_CHARTER = "intention" + "+why.json"


def test_the_gate_answers_queueme_with_a_clearance_refusal() -> None:
    import importlib
    from cairn.devices.codemother.shim import CodeMotherDevice
    clearance = importlib.import_module(NEW_DOTTED + ".clearance")
    gate_mod = importlib.import_module(NEW_DOTTED + ".gate")
    dev = CodeMotherDevice(bus=None)
    bad = []
    if "cross" in dev.declared_verbs():
        bad.append("codemother still declares a cross verb")
    if "clearance" not in dev.declared_machines():
        bad.append("codemother's declared_machines holds no clearance gate")
    wf = "code-seam@v2: THINKME -> [TICKETME:waiting] -> BUILDME -> PROVEME -> PROVED"
    with tempfile.TemporaryDirectory(prefix="clearance-berth-") as tmp:
        t = Path(tmp)
        repo, commons = t / "repo", t / "commons"
        (repo / "comp" / "proofs").mkdir(parents=True)
        (commons / "tickets").mkdir(parents=True)
        (repo / "comp" / _CHARTER).write_text(json.dumps({"gated_by": ["nobody"]}))
        proof = repo / "comp" / "proofs" / "test_the_fixture.py"
        proof.write_text('PROVES = {"000000000000": {"1": "test_one"}}\n')
        plan = commons / "tickets" / "000000000000-the-fixture.json"
        plan.write_text(json.dumps({"id": "000000000000", "owning_intention": "comp/" + _CHARTER,
                                    "workflow_and_state": wf}))
        old = os.environ.get("CAIRN_LB_TRACE_ROOT")
        os.environ["CAIRN_LB_TRACE_ROOT"] = str(t / "traces")
        heard = _Heard()
        try:
            gate = gate_mod.ClearanceGate(participant=heard, roots={"repo": repo, "commons": commons,
                                                                    "instance": t / "instance"})
            answer = gate.declared_verbs()["queueme"]({"sender": "cc", "body": {"fileref": str(plan)}})
        finally:
            if old is None:
                os.environ.pop("CAIRN_LB_TRACE_ROOT", None)
            else:
                os.environ["CAIRN_LB_TRACE_ROOT"] = old
        cursor = json.loads(plan.read_text()).get("workflow_and_state")
    refusal = answer.get("refusal") or ""
    cls = getattr(clearance, refusal, None)
    if not (answer.get("accepted") is False and isinstance(cls, type) and issubclass(cls, Exception)
            and cls.__module__ == clearance.__name__):
        bad.append("not a clearance refusal: " + json.dumps(answer, default=str)[:300])
    if answer.get("door") != "clearance":
        bad.append(f"door {answer.get('door')!r}")
    if answer.get("target") != "BUILDME":
        bad.append(f"derived target {answer.get('target')!r}, not BUILDME")
    if [Path(p).name for p in answer.get("proven_by") or []] != [proof.name]:
        bad.append(f"derived proven_by {answer.get('proven_by')!r}")
    if cursor != wf:
        bad.append(f"the refused ticket's cursor moved: {cursor!r}")
    if heard.said:
        bad.append(f"a refusal spoke: {heard.said}")
    check("test_the_gate_answers_queueme_with_a_clearance_refusal", not bad, "; ".join(bad))


def test_no_breach_joins_codemother_and_the_harbor_over_clearance() -> None:
    from cairn.machines.build_inspector import inspector
    here = os.getcwd()
    os.chdir(_REPO)
    try:
        breaches = inspector.encapsulation_breaches(".")
    finally:
        os.chdir(here)
    pair = {"cairn/devices/codemother", OLD_DIR}
    joined = [b for b in breaches if {b.get("source"), b.get("target")} == pair
              and "clearance" in str(b.get("module"))]
    check("test_no_breach_joins_codemother_and_the_harbor_over_clearance",
          not joined and len(breaches) <= BREACH_CEILING,
          f"{len(breaches)} breach(es); joined: " + "; ".join(f"{b['file']}:{b['line']}" for b in joined))


def test_the_probe_tickets_name_the_new_berth() -> None:
    from cairn.tools.base import ticket_file
    bad = []
    for tid in PROBE_TICKETS:
        plan = ticket_file.find_ticket(tid)
        if plan is None:
            bad.append(f"{tid}: no ticket")
            continue
        w = json.loads(ticket_file.state_path(plan).read_text("utf-8")).get("watchme")
        specs = w if isinstance(w, list) else [w]
        probes = [s.get("probe") for s in specs if isinstance(s, dict) and s.get("probe")]
        if not probes:
            bad.append(f"{tid}: no probe named")
        for p in probes:
            if not (str(p).startswith(NEW + "/probes/") and (_REPO / p).is_file()):
                bad.append(f"{tid}: {p}")
    check("test_the_probe_tickets_name_the_new_berth", not bad, "; ".join(bad))


def test_the_deprecation_report_runs_from_the_new_address() -> None:
    r = subprocess.run([sys.executable, "-m", NEW_DOTTED, OLD_DIR + "/intention+why.json"],
                       cwd=_REPO, capture_output=True, text=True, timeout=120)
    check("test_the_deprecation_report_runs_from_the_new_address",
          r.returncode == 0 and "DEPRECATION REPORT" in r.stdout,
          f"exit {r.returncode}: " + (r.stderr.strip().splitlines() or r.stdout.strip().splitlines() or [""])[-1])


def test_the_cross_command_has_the_ticket_queue_itself() -> None:
    mouth = _REPO / "cairn/devices/codemother/0/bin/cross"
    text = mouth.read_text(encoding="utf-8")
    bad = []
    if re.search(r"verb\s*=\s*['\"]cross['\"]", text):
        bad.append("the mouth still sends verb 'cross'")
    if not re.search(r"\.queueme\(\s*['\"]clearance['\"]", text):
        bad.append("the mouth does not have the ticket queue itself at clearance")
    r = subprocess.run([str(mouth)], cwd=_REPO, capture_output=True, text=True, timeout=60)
    usage = r.stdout + r.stderr
    if r.returncode == 0 or "cross <ticket>" not in usage or "<target>" in usage:
        bad.append(f"bare mouth: exit {r.returncode}, said {usage.strip()[:200]!r}")
    check("test_the_cross_command_has_the_ticket_queue_itself", not bad, "; ".join(bad))


TEETH = (test_the_module_berths_in_codemother,
         test_no_class_space_file_names_the_old_berth,
         test_the_gate_answers_queueme_with_a_clearance_refusal,
         test_no_breach_joins_codemother_and_the_harbor_over_clearance,
         test_the_probe_tickets_name_the_new_berth,
         test_the_deprecation_report_runs_from_the_new_address,
         test_the_cross_command_has_the_ticket_queue_itself)


def main() -> int:
    for tooth in TEETH:
        try:
            tooth()
        except Exception as exc:  # noqa: BLE001 — a tooth that cannot run is a red, loudly
            check(tooth.__name__, False, f"raised {type(exc).__name__}: {exc}")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
