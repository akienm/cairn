"""Proof for three-classes-cannot-be-cast.

Teeth a hollow build could not pass:

  - HOST-SEAM HAS WORKFLOW_VERSIONS V1. load_class_def("host-seam") returns a
    definition with workflow_versions containing v1, and the v1 entry has the
    ruled path (THINKME -> TICKETME -> RESEARCHME -> POCME -> PROVEME -> PROVED),
    TICKETME and RESEARCHME skippable, WATCHME free.
  - A HOST-SEAM@V1 WORKFLOW STRING PARSES AND CONFORMS. parse_workflow followed
    by _conform does not raise — the string is a valid instance of the registered
    path.
  - OPERATIONAL-DRIVER CARRIES SUPERSEDED. The file has a "superseded" field with
    "by" naming the probe primitive.
  - ZERO TICKETS REFERENCE OPERATIONAL-DRIVER. No ticket in CairnCommons/tickets/
    carries node_class "operational-driver".

    python3 cairn/tools/base/proofs/test_three_classes.py
"""

from __future__ import annotations

import glob
import json
import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.base.transitions import load_class_def, parse_workflow, _conform

_COMMONS = _REPO_ROOT.parent / "CairnCommons"

PASSES = 0


def ok(name: str, cond: bool, detail: str = ""):
    global PASSES
    if not cond:
        print(f"RED  {name}  {detail}")
        raise SystemExit(1)
    PASSES += 1
    print(f"  ok {name}")


def main() -> int:
    # ── host-seam has workflow_versions ──────────────────────────────────
    cd = load_class_def("host-seam")
    ok("host-seam loads", cd is not None)
    wv = cd.get("workflow_versions", {})
    ok("host-seam has workflow_versions", bool(wv))
    ok("host-seam has v1", "v1" in wv)

    v1 = wv["v1"]
    expected_path = ["THINKME", "TICKETME", "RESEARCHME", "POCME", "PROVEME", "PROVED"]
    ok("v1 path matches the ruled shape",
       v1["path"] == expected_path,
       f"got {v1['path']}")

    ok("TICKETME is skippable",
       "TICKETME" in v1.get("skippable_summons", []))
    ok("RESEARCHME is skippable (optional per Akien)",
       "RESEARCHME" in v1.get("skippable_summons", []))
    ok("WATCHME is a free summons",
       "WATCHME" in v1.get("free_summons", []))
    ok("v1 has a why", bool(v1.get("why")))

    # ── a host-seam@v1 string parses and conforms ───────────────────────
    wf = parse_workflow(
        "host-seam@v1: THINKME -> [TICKETME] -> RESEARCHME -> POCME -> PROVEME -> PROVED")
    ok("parse_workflow succeeds", wf is not None)
    ok("parsed class is host-seam", wf.node_class == "host-seam")
    ok("parsed version is v1", wf.version == "v1")

    _conform(wf, cd)
    ok("_conform does not raise", True)

    # ── skipping RESEARCHME works (it is skippable) ─────────────────────
    from cairn.tools.base.transitions import legal_targets
    wf_at_ticketme = parse_workflow(
        "host-seam@v1: THINKME -> [TICKETME] -> RESEARCHME -> POCME -> PROVEME -> PROVED")
    targets = legal_targets(wf_at_ticketme, class_def=cd)
    ok("RESEARCHME can be skipped (POCME is a legal target from TICKETME)",
       "POCME" in targets, f"legal targets: {targets}")

    # ── WATCHME as free summons works ───────────────────────────────────
    wf_watch = parse_workflow(
        "host-seam@v1: THINKME -> [TICKETME] -> RESEARCHME -> POCME -> PROVEME -> WATCHME(some-probe) -> PROVED")
    _conform(wf_watch, cd)
    ok("WATCHME(object) accepted as free summons", True)

    # ── operational-driver carries SUPERSEDED ───────────────────────────
    od = json.load(open(_COMMONS / "node_classes" / "operational-driver.json"))
    ok("operational-driver has superseded field",
       "superseded" in od)
    sup = od["superseded"]
    ok("superseded.by names probe",
       "probe" in sup.get("by", "").lower(),
       f"got by={sup.get('by')}")
    ok("superseded.date is set",
       bool(sup.get("date")))
    ok("superseded.ruling is set",
       bool(sup.get("ruling")))
    ok("superseded.evidence is set",
       bool(sup.get("evidence")))

    # ── zero tickets reference operational-driver ───────────────────────
    count = 0
    for f in glob.glob(str(_COMMONS / "tickets" / "*.json")):
        try:
            t = json.load(open(f))
            if t.get("node_class") == "operational-driver":
                count += 1
                print(f"  FOUND: {f}")
        except (json.JSONDecodeError, OSError):
            pass
    ok("zero tickets reference operational-driver as node_class",
       count == 0, f"found {count}")

    print(f"GREEN — {PASSES} teeth")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
