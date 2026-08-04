"""PROOF — the usage roster counts what it can and refuses to invent the rest.

Teeth a hollow build could not pass (Law 8), every root injected.

THE TOOTH THIS FILE EXISTS FOR is the one that would make the whole surface a liability
if it failed: a skill with no door must never render as **0**. Akien's disuse clause
says a skill "could wind up being excised through disuse" — so a surface that prints 0
for a skill nobody ever wired hands him evidence for excising a door that was never
tried. Unmeasured and zero are different facts and the renderer may not collapse them
(Law 7 at a diagnostic surface).

Two more that keep it honest: the roster IS the directory (no registry to fall out of
sync), and reading never writes (the dial's own law — a metric that disturbs what it
counts is not a metric).

Run bare:  PYTHONPATH=$HOME/dev/src/cairn python3 cairn/skill_block/proofs/test_skilldial.py
Run twice; never trust the first green.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO))

from cairn.skill_block import skill_block as sb          # noqa: E402
from cairn.skill_block import skilldial                   # noqa: E402

PASSES = 0


def ok(name: str, cond: bool, detail: str = ""):
    global PASSES
    if not cond:
        print(f"RED  {name}  {detail}")
        raise SystemExit(1)
    PASSES += 1
    print(f"  ok {name}")


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="skilldial-proof-"))
    skills, traces, berths = tmp / "skills", tmp / "traces", tmp / "berths"

    # A tenant, a non-tenant, and a skill with no charter at all.
    (skills / "wired").mkdir(parents=True)
    (skills / "wired" / "intention+why.json").write_text(json.dumps(
        {"input_contract": {"thing": "why the thing is required"}}))
    (skills / "unwired").mkdir(parents=True)
    (skills / "unwired" / "intention+why.json").write_text(json.dumps(
        {"what": "a skill that fires no door"}))
    (skills / "charterless").mkdir(parents=True)

    kw = dict(skills_root=skills, berths=berths, trace_root=traces)

    # ── the roster is the directory ───────────────────────────────────────────
    ok("roster IS the directory listing — no registry",
       skilldial.skill_names(skills) == ["charterless", "unwired", "wired"])

    rows = {r["skill"]: r for r in skilldial.roster(skills_root=skills, traces=traces)}
    ok("every skill on disk gets a row", set(rows) == {"charterless", "unwired", "wired"})

    # ── THE TOOTH: unmeasured is not zero ─────────────────────────────────────
    ok("a non-tenant is marked NOT countable", rows["unwired"]["countable"] is False)
    ok("a non-tenant carries NO count fields at all",
       "firings" not in rows["unwired"], str(rows["unwired"]))
    ok("its why says so in words", "NOT zero uses" in rows["unwired"]["why_not_countable"])
    ok("a charterless skill is refused differently from an unwired one",
       rows["charterless"]["why_not_countable"] != rows["unwired"]["why_not_countable"])

    rendered = skilldial.render(list(rows.values()))
    unwired_line = next(l for l in rendered.splitlines() if l.startswith("unwired"))
    ok("THE RENDER TOOTH: the uncountable row prints no zero",
       "0" not in unwired_line, unwired_line)
    ok("the uncountable row says 'not countable' out loud",
       "not countable" in unwired_line)
    ok("the summary refuses to add the two kinds together",
       "not zero uses" in rendered)

    # ── a tenant, never fired, IS a zero — and that is a different fact ───────
    ok("a wired skill with no firings counts 0", rows["wired"]["firings"] == 0)
    ok("never-fired is rendered as 'never', not blank",
       "never" in next(l for l in rendered.splitlines() if l.startswith("wired")))
    ok("zero and uncountable render differently",
       next(l for l in rendered.splitlines() if l.startswith("wired")) !=
       next(l for l in rendered.splitlines() if l.startswith("unwired")))

    # ── the numbers are the trace's, re-derived ───────────────────────────────
    packet = {"thing": "x", "bullets": [{"text": "t", "stratum": "code"}],
              "exit": "routed_forward"}
    sb.fire("wired", packet, **kw)
    sb.fire("wired", packet, **kw)
    try:
        sb.fire("wired", {"bullets": [{"text": "t", "stratum": "code"}]}, **kw)
    except Exception:
        pass

    after = {r["skill"]: r for r in skilldial.roster(skills_root=skills, traces=traces)}
    ok("firings counted", after["wired"]["firings"] == 3, str(after["wired"]))
    ok("refusals counted separately", after["wired"]["send_backs"] == 1)
    ok("findings counted", after["wired"]["findings"] == 2)
    ok("last_fired appears once it has fired", after["wired"]["last_fired"] is not None)
    ok("last_fired is an ISO timestamp", after["wired"]["last_fired"].startswith("20"))
    ok("the non-tenant is STILL not countable after real traffic elsewhere",
       after["unwired"]["countable"] is False)
    ok("match_rate is None until a verdict exists — not 0%",
       after["wired"]["match_rate"] is None)

    # ── reading never writes ──────────────────────────────────────────────────
    trace_file = traces / "skill:wired.jsonl"
    before = trace_file.read_bytes()
    for _ in range(3):
        skilldial.roster(skills_root=skills, traces=traces)
    ok("THE PURE-READ TOOTH: the trace is byte-identical after three reads",
       trace_file.read_bytes() == before)

    # ── the live surface still renders ────────────────────────────────────────
    live = skilldial.roster()
    ok("the live roster covers every real skill",
       {"intent", "sorted", "idea", "design", "note"} <= {r["skill"] for r in live})
    ok("the live render does not crash", isinstance(skilldial.render(live), str))

    print(f"GREEN — {PASSES} teeth")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
