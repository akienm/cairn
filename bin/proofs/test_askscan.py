#!/usr/bin/env python3
"""Proof for ``bin/cmd/askscan`` — the Stop-hook scan for the prebuild-feedback signal.

TEETH A HOLLOW BUILD COULD NOT PASS (Law 8):

  1. IT MUST NOT BLOCK, AND IT IS RULED, NOT INFERRED. Akien, 2026-08-14: *"each
     ruling packet issued at build time needs to feed back, but it does not need
     to stop the work"* and, of this signal specifically, *"it still should not
     stop the work, but yes, we wanna capture that."* A Stop hook MAY return
     ``{"decision": "block"}``, and "enforcement" is exactly the word that makes
     someone add it later. Case 1 fails any build that emits a decision key on
     any input, including the reddest one.

  2. IT MUST CAPTURE, AND THAT IS THE OTHER HALF OF THE SAME SENTENCE. A build
     that only prints a receipt passes tooth 1 and still loses the feedback the
     moment the turn scrolls. Case 6 requires exactly one appended row, in the
     instance that owns the packet, carrying the gap and the packet it keyed on.

  3. BOTH CONDITIONS, OR IT IS NOT THE SIGNAL. The naive build detects a
     question. 33% of my end_turns carry one — a detector that fires on all of
     them measures my punctuation, not the rule. What makes a question EVIDENCE
     is a prebuild chain having already run. Case 3 asks the same question with
     no run behind it and requires silence; case 4 puts the run three hours back
     and requires silence again.

  4. SEQUENCING IS SUBTRACTED, AND THE SUBTRACTION IS THE CALIBRATION. "Want me
     to do that now, or sail X first?" is Akien's call to make — ordering is his
     — and 29 of 73 question-turns in the real corpus are that shape. A build
     that counts them reds the one kind of question the system WANTS asked, and a
     detector that punishes correct behaviour gets turned off. Case 5 fires it
     seconds after a run and requires silence.

  5. USE vs MENTION. The scan's own docstring quotes two clarifying questions
     verbatim to explain itself. A build without a quote-stripper reds every
     discussion of the rule — the tax turnscan already paid once. Case 7 feeds a
     quoted question and requires silence.

  6. NEVER WEDGES A TURN. Malformed JSON, empty stdin, absent field, and the
     re-entry guard each exit 0 and stay off the receipt. A scan that can stop a
     session ending is worse than the prose it replaces.

INVARIANTS, NOT SNAPSHOTS. Case 9 runs the real transcript corpus, which GROWS
every session, and the packet folder grows with it. It asserts a CEILING and a
SHAPE — never today's count. Pinning "6 reds" would go red the next time anyone
asks a question after a build.

    python3 bin/proofs/test_askscan.py     # exit 0 = green
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
ASKSCAN = REPO / "bin" / "cmd" / "askscan"

_spec = importlib.util.spec_from_loader(
    "askscan", importlib.machinery.SourceFileLoader("askscan", str(ASKSCAN)))
askscan = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(askscan)

FAILURES: list[str] = []
CHECKS = 0

CLARIFYING = ("So — when you say the gate learns its own threshold, do you mean the "
              "number moves with the evidence, or that the shape of the rule does?")
SEQUENCING = ("Want me to build the ledger now, or sail the carve-out first and pick "
              "the ledger up after?")


def check(label: str, condition: bool, detail: str = "") -> None:
    global CHECKS
    CHECKS += 1
    if condition:
        print(f"  ok   {label}")
    else:
        print(f"  RED  {label}" + (f"  — {detail}" if detail else ""))
        FAILURES.append(label)


def _world(tmp: str, *, age_seconds: float = 60.0):
    """A berths root with one prebuild packet, aged as asked. Returns (root, runs)."""
    packets = Path(tmp) / "0" / "packets"
    packets.mkdir(parents=True)
    p = packets / "verdict-20260814T090000-abc123abc123.json"
    p.write_text(json.dumps({"ticket": "a-fixture"}), encoding="utf-8")
    when = time.time() - age_seconds
    os.utime(p, (when, when))
    return str(Path(tmp)), askscan.prebuild_runs(str(Path(tmp)))


def _hook(payload: dict) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(ASKSCAN)], input=json.dumps(payload),
                          capture_output=True, text=True, timeout=60)


def main() -> int:
    print("askscan — the prebuild-feedback signal\n")

    # ── 1. RULED: it does not stop the work ──────────────────────────────────
    src = ASKSCAN.read_text(encoding="utf-8")
    check("no build-time path can emit a block decision",
          '"decision"' not in src and "'decision'" not in src,
          "the ruled clause is 'it does not need to stop the work'")
    for label, payload in (
            ("clarifying", {"last_assistant_message": CLARIFYING}),
            ("sequencing", {"last_assistant_message": SEQUENCING}),
            ("empty", {}),
            ("re-entry guard", {"last_assistant_message": CLARIFYING,
                                "stop_hook_active": True})):
        rc = _hook(payload)
        ok = rc.returncode == 0 and "decision" not in rc.stdout
        check(f"hook exits 0 and never blocks: {label}", ok,
              f"rc={rc.returncode} stdout={rc.stdout[:160]}")

    # ── 2. both conditions, or it is not the signal ──────────────────────────
    with tempfile.TemporaryDirectory() as tmp:
        _, runs = _world(tmp, age_seconds=60)
        g = askscan.gap(CLARIFYING, time.time(), runs=runs)
        check("a clarifying question minutes after a run is the signal",
              g is not None and g["after_stage"] == "verdict" and g["gap_seconds"] <= 120,
              f"got {g}")
        check("the evidence names the packet it keyed on, so the window is auditable",
              bool(g) and g["after_packet"].startswith("verdict-")
              and g["window_seconds"] == askscan.WINDOW_SECONDS, f"got {g}")

        check("the SAME question with no prebuild run behind it is silent",
              askscan.gap(CLARIFYING, time.time(), runs=[]) is None,
              "a question alone is an ordinary question, not evidence")

    with tempfile.TemporaryDirectory() as tmp:
        _, old = _world(tmp, age_seconds=3 * 60 * 60)
        check("a run three hours back is outside the window and is silent",
              askscan.gap(CLARIFYING, time.time(), runs=old) is None,
              "the window is the proxy for 'this work', and it has an edge")

    # ── 3. sequencing is his call, and is subtracted ─────────────────────────
    with tempfile.TemporaryDirectory() as tmp:
        _, runs = _world(tmp, age_seconds=30)
        check("a sequencing question seconds after a run is NOT the defect",
              askscan.gap(SEQUENCING, time.time(), runs=runs) is None,
              "ordering is Akien's to call; reding it would punish correct behaviour")
        ask = askscan.asked(SEQUENCING)
        check("and the subtraction names the pattern that made it, never silently drops",
              bool(ask) and ask["clarifying"] is False and bool(ask["sequencing"]),
              f"got {ask}")

    # ── 4. it CAPTURES — the other half of the ruling ────────────────────────
    with tempfile.TemporaryDirectory() as tmp:
        root, runs = _world(tmp, age_seconds=60)
        g = askscan.gap(CLARIFYING, time.time(), runs=runs)
        where = askscan.record(g)
        ledger = Path(root) / "0" / askscan.LEDGER
        check("the gap lands in the instance that OWNS the run, not a central pile",
              where == str(ledger) and ledger.exists(), f"where={where}")
        rows = [json.loads(l) for l in ledger.read_text(encoding="utf-8").splitlines() if l]
        check("exactly one row per gap, and it carries its evidence whole",
              len(rows) == 1 and rows[0]["gap_seconds"] == g["gap_seconds"]
              and rows[0]["question"] == g["question"]
              and rows[0]["after_packet"] == g["after_packet"], f"rows={rows}")
        askscan.record(g)
        rows2 = [l for l in ledger.read_text(encoding="utf-8").splitlines() if l]
        check("the ledger is APPEND-only — a second gap adds, never rewrites",
              len(rows2) == 2 and rows2[0] == json.dumps(rows[0], ensure_ascii=False),
              f"{len(rows2)} row(s)")

    # ── 5. use vs mention ────────────────────────────────────────────────────
    with tempfile.TemporaryDirectory() as tmp:
        _, runs = _world(tmp, age_seconds=60)
        quoted = f'The rule was measured on this one: "{CLARIFYING}" — and it held.'
        check("a QUOTED clarifying question is mention, not utterance, and is silent",
              askscan.gap(quoted, time.time(), runs=runs) is None,
              "this scan's own docstring quotes two; a build without a stripper reds "
              "every discussion of the rule")
        fenced = f"Here is the shape:\n```\n{CLARIFYING}\n```\nNothing else."
        check("a fenced one likewise", askscan.gap(fenced, time.time(), runs=runs) is None)

    # ── 6. the receipt carries its evidence ──────────────────────────────────
    with tempfile.TemporaryDirectory() as tmp:
        _, runs = _world(tmp, age_seconds=45)
        r = askscan.receipt(askscan.gap(CLARIFYING, time.time(), runs=runs))
        check("the receipt names the gap, the stage, and the question",
              "verdict" in r and "s after" in r and "do you mean" in r, f"got {r!r}")
        check("and says out loud that it is not stopping anything",
              "not blocking" in r or "continues" in r, f"got {r!r}")

    # ── 7. it never wedges a turn ────────────────────────────────────────────
    for label, raw in (("malformed json", "{not json"), ("empty stdin", ""),
                       ("absent field", '{"session_id":"x"}')):
        rc = subprocess.run([sys.executable, str(ASKSCAN)], input=raw,
                            capture_output=True, text=True, timeout=60)
        check(f"survives {label} with exit 0 and an empty receipt",
              rc.returncode == 0 and not rc.stdout.strip(),
              f"rc={rc.returncode} stdout={rc.stdout[:120]}")

    # ── 8. a fragment is not a design question ───────────────────────────────
    with tempfile.TemporaryDirectory() as tmp:
        _, runs = _world(tmp, age_seconds=60)
        for frag in ("?", "by line?", "Which?"):
            check(f"the fragment {frag!r} is below the floor and is silent",
                  askscan.gap(f"Some report text.\n\n{frag}", time.time(),
                              runs=runs) is None)

    # ── 9. the corpus falsifier — invariants, never today's count ────────────
    rc = subprocess.run([sys.executable, str(ASKSCAN), "--corpus"],
                        capture_output=True, text=True, timeout=300)
    check("--corpus runs green over the real transcripts", rc.returncode == 0,
          rc.stderr[:200])
    out = rc.stdout
    check("it reports attendance, not only objections — turns, era, packets on disk",
          "end_turn message(s)" in out and "packet(s) on disk" in out
          and "in the prebuild era" in out, f"head={out[:220]!r}")
    check("it reports the SUBTRACTION by name, so the calibration is arguable",
          "sequencing" in out and "clarifying" in out, f"head={out[:220]!r}")
    reds = None
    for line in out.splitlines():
        if "red: clarifying" in line:
            reds = int(line.split()[0])
            break
    in_era = None
    for line in out.splitlines():
        if "in the prebuild era" in line:
            in_era = int(line.split()[0])
            break
    check("it reports a red COUNT", reds is not None, f"stdout={out[:300]}")
    # A detector that reds a tenth of every turn in the era is measuring my
    # punctuation, not this rule. The ceiling is the falsifier, not the count.
    rate = (100.0 * reds / in_era) if (reds is not None and in_era) else None
    check("the red rate is under the 5% ceiling", rate is not None and rate < 5.0,
          f"rate={rate}% over {in_era} turns — this loud would be noise, not physics")
    check("and it is not vacuously silent — the rule fired on real history",
          bool(reds), "zero reds over the whole prebuild era would mean the scan "
                      "cannot see the thing Akien measured by hand")

    print()
    print(f"{CHECKS - len(FAILURES)}/{CHECKS} green")
    if FAILURES:
        print("RED:")
        for f in FAILURES:
            print(f"  - {f}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
