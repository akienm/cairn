#!/usr/bin/env python3
"""Proof that the clearance gate berths in CodeMother, and the harbor answers no `clear`.

Akien 2026-11-10 (outline 9.4.1.5, Q#80): the harbor's verbs are status queries (show, get)
and crossing; it answers no gate and moves no ticket, and `clear` leaves. Outline 9.6 and
3.3.4.3 (Q#81): the gates are CodeMother's machines. Ticket 0be964512fb0 moves the module,
its proofs and its probes, and CodeMother's `cross` fires the gate in her own process.

The retired spellings are built from parts below, so this file never names them whole and
tooth (2) can read it like any other file.

Teeth, each importing the code under test at call time:
  (1) the module imports at its new address with clear, _decide and riders_of, and the old
      file is gone;
  (2) no class-space file outside history, state, validations and journals names the old
      module, its probes or its moved proofs, dotted, slashed or path-joined;
  (3) lives at the harbor's own address (RULE 1: this proof may not import the harbor):
      cairn/devices/cairn/machines/harbor_master/proofs/test_the_harbor_answers_no_clear.py;
  (4) CodeMother's cross with no bus answers a clearance refusal over a fixture, never a
      no-bus or harbor-unwired one;
  (5) no RULE 1 breach between codemother and harbor_master names clearance, and the total
      is not above 71 (measured 2026-11-11);
  (6) the four clearance probes' tickets name a probe under clearance/probes/ that exists;
  (7) the deprecation report runs from the new address.

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
                           "4": "test_codemother_reaches_the_gate_without_a_bus",
                           "5": "test_no_breach_joins_codemother_and_the_harbor_over_clearance",
                           "6": "test_the_probe_tickets_name_the_new_berth",
                           "7": "test_the_deprecation_report_runs_from_the_new_address"}}

NEW = "cairn/devices/codemother/machines/clearance"
NEW_DOTTED = "cairn.devices.codemother.machines.clearance"
_H = "harbor" + "_master"
OLD_DIR = "cairn/devices/cairn/machines/" + _H
PROBE_TICKETS = ("0354c0269ff7", "0cde908b8fbe", "2b16d2d8b056", "faa51bcfbdfc")
BREACH_CEILING = 71
_MOVED_PROOFS = ("test_clearance", "test_a_notified_file_is_covered", "test_harbor_asks_the_real_host",
                 "test_the_proven_space_rule_follows_the_ticket_kind",
                 "test_" + _H + "_probes_report_to_the_watch")

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
    check("test_the_module_berths_in_codemother", not bad, "; ".join(bad))


def test_no_class_space_file_names_the_old_berth() -> None:
    h = re.escape(_H)
    spellings = [h + r"\.clearance\b", h + r"/clearance", h + r" import clearance\b",
                 h + r"\"\s*/\s*\"clearance", h + r"[./]probes\b", h + r"\"\s*/\s*\"probes"]
    spellings += [h + r"/proofs/" + p + r"\b" for p in _MOVED_PROOFS]
    spellings.append(r"\btest_harbor_asks_the_real_host\b")
    r = subprocess.run(["git", "grep", "--untracked", "-nE", "|".join(spellings), "--", ".",
                        ":!*.jsonl", ":!*history.json", ":!*state.json", ":!*/validations/*"],
                       cwd=_REPO, capture_output=True, text=True)
    hits = [l for l in r.stdout.splitlines() if l.strip()]
    check("test_no_class_space_file_names_the_old_berth", r.returncode in (0, 1) and not hits,
          f"{len(hits)} hit(s): " + "; ".join(hits[:8]) if hits else r.stderr.strip())


def test_codemother_reaches_the_gate_without_a_bus() -> None:
    import importlib
    from cairn.devices.codemother.shim import CodeMotherDevice
    clearance = importlib.import_module(NEW_DOTTED + ".clearance")
    with tempfile.TemporaryDirectory(prefix="clearance-berth-") as tmp:
        old = os.environ.get("CAIRN_LB_TRACE_ROOT")
        os.environ["CAIRN_LB_TRACE_ROOT"] = str(Path(tmp) / "traces")
        try:
            comp = Path(tmp) / "comp"
            comp.mkdir()
            answer = CodeMotherDevice(bus=None)._handle_cross({"sender": "codemother", "body": {
                "ticket": "000000000000", "target": "BUILDME",
                "workflow": "code-seam@v2: THINKME -> [TICKETME:waiting] -> BUILDME -> PROVEME -> PROVED",
                "history_path": str(comp / "history.json"), "state_path": str(comp / "state.json"),
                "proven_by": str(comp / "proofs" / "test_nothing.py")}})
        finally:
            if old is None:
                os.environ.pop("CAIRN_LB_TRACE_ROOT", None)
            else:
                os.environ["CAIRN_LB_TRACE_ROOT"] = old
    refusal = answer.get("refusal") or ""
    cls = getattr(clearance, refusal, None)
    ok = (answer.get("accepted") is False and isinstance(cls, type)
          and issubclass(cls, Exception) and cls.__module__ == clearance.__name__
          and answer.get("door") == "clearance")
    check("test_codemother_reaches_the_gate_without_a_bus", ok, json.dumps(answer, default=str)[:400])


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


TEETH = (test_the_module_berths_in_codemother,
         test_no_class_space_file_names_the_old_berth,
         test_codemother_reaches_the_gate_without_a_bus,
         test_no_breach_joins_codemother_and_the_harbor_over_clearance,
         test_the_probe_tickets_name_the_new_berth,
         test_the_deprecation_report_runs_from_the_new_address)


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
