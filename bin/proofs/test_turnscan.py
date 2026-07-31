#!/usr/bin/env python3
"""Proof for ``bin/cmd/turnscan`` — the Stop-hook scan for the turn-shape rule.

TEETH A HOLLOW BUILD COULD NOT PASS (Law 8):

  1. IT MUST NOT BLOCK, AND THAT IS THE LOAD-BEARING ONE. A Stop hook may return
     ``{"decision": "block"}``. The obvious build does, because "enforcement"
     sounds like stopping. But the rule being measured says whether a concern
     blocks is THE OWNER'S CALL — so a detector that halted the turn would take
     Akien's call ambiently, committing the exact defect it exists to catch, one
     level up. Case 4 fails any build that emits a decision key. This is the
     tooth most likely to be "fixed" by someone who thinks it is a bug.
  2. USE vs MENTION. Measured, not imagined: the first red the crude detector
     produced was a message QUOTING the rule to explain it. A build without a
     quote-stripper reds every discussion of the rule — which taxes exactly the
     conversation the rule wants to have. Case 2 quotes the canonical phrase and
     requires silence.
  3. ORDER IS THE WHOLE SIGNAL. Unordered co-occurrence measured 4.7% of real
     turns and was mostly noise; requiring the proposal AFTER the concern gave
     1.5% and hand-reviewed hits that were mostly right. A build that just checks
     "both present" passes a naive test and lands on case 3.
  4. THE RECEIPT CARRIES ITS EVIDENCE. A finding that will not show what tripped
     it cannot be falsified by the person receiving it. Case 5 requires BOTH
     matched phrases in the receipt — a bare "turn-shape violation" fails.
  5. NEVER WEDGES A TURN. Malformed JSON, empty stdin, absent field, and the
     re-entry guard — each exits 0 and stays off the receipt. A scan that can
     stop a session ending is worse than the prose it replaces.

INVARIANTS, NOT SNAPSHOTS. Case 7 runs the real transcript corpus, which GROWS
every session. It therefore asserts a CEILING and a shape — never today's count.
Pinning "6 reds" would go red the next time anyone talks about a caveat.

    python3 bin/proofs/test_turnscan.py     # exit 0 = green
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
TURNSCAN = REPO / "bin" / "cmd" / "turnscan"

FAILURES: list[str] = []
CHECKS = 0


def check(label: str, condition: bool, detail: str = "") -> None:
    global CHECKS
    CHECKS += 1
    if condition:
        print(f"  ok   {label}")
    else:
        print(f"  RED  {label}" + (f"  — {detail}" if detail else ""))
        FAILURES.append(label)


def run(payload, raw: str | None = None) -> subprocess.CompletedProcess:
    text = raw if raw is not None else json.dumps(payload)
    return subprocess.run([sys.executable, str(TURNSCAN)], input=text,
                          capture_output=True, text=True)


def scan(message: str, **extra) -> tuple[dict | None, subprocess.CompletedProcess]:
    r = run({"last_assistant_message": message, **extra})
    if not r.stdout.strip():
        return None, r
    return json.loads(r.stdout), r


# The canonical defect, in CLAUDE.md's own words.
RED_TURN = (
    "The projector looks right. One thing I want to name before it lands: the "
    "append door is not the only path to that file, so a hand-write would look "
    "exactly like a fresh seal. Anyway, here's the plan — I'll write the shape "
    "gate first, then wire the emit chokepoint."
)


def main() -> int:
    print(__doc__.strip().splitlines()[0])
    print()

    # ── 1. the canonical shape is caught ──────────────────────────────────────
    print("1. a concern raised and then dispositioned in the same message is a red")
    out, r = scan(RED_TURN)
    check("exit 0", r.returncode == 0, f"rc={r.returncode} err={r.stderr[:200]}")
    check("a receipt is emitted", out is not None and "systemMessage" in (out or {}),
          f"stdout={r.stdout[:200]}")

    # ── 2. USE vs MENTION ─────────────────────────────────────────────────────
    print("\n2. QUOTING the rule is not committing it")
    quoted = (
        'The rule in CLAUDE.md is about turn shape. When I write '
        '"one thing to point out... anyway, here\'s the plan", I have raised a '
        'concern and decided it does not block in one breath. That second act is '
        'the owner\'s. This message only describes the defect.'
    )
    out_q, r_q = scan(quoted)
    check("a quoted concern-marker does not red", out_q is None,
          f"a build with no quote-stripper lands here: {r_q.stdout[:200]}")
    fenced = "Here is the detector:\n```\nmy own damage ... anyway\n```\nIt is not wired yet."
    out_f, _ = scan(fenced)
    check("a fenced code block does not red", out_f is None)
    blockquoted = "> one thing I want to flag: anyway, here's the plan\n\nThat is the shape."
    out_b, _ = scan(blockquoted)
    check("a blockquote does not red", out_b is None)

    # ── 3. ORDER IS THE SIGNAL ────────────────────────────────────────────────
    print("\n3. order is the signal, not co-occurrence")
    reversed_order = (
        "Anyway, here's the plan — I'll write the gate first. That is settled and "
        "measured. Separately, one thing I want to name for later: the corpus is "
        "still small."
    )
    out_r, r_r = scan(reversed_order)
    check("forward BEFORE concern is not a red", out_r is None,
          f"a co-occurrence build lands here: {r_r.stdout[:200]}")
    check("a concern with no proposal is silent",
          scan("One thing I want to name: the door is not the only path.")[0] is None)
    check("a proposal with no concern is silent",
          scan("Here's the plan — I'll write the shape gate, then wire it.")[0] is None)

    # ── 4. IT MUST NOT BLOCK ──────────────────────────────────────────────────
    print("\n4. the scan raises; it never decides (Law 6 — the owner's call)")
    check("no decision key on a red", out is not None and "decision" not in out,
          f"a blocking build lands here: {out}")
    check("no continue:false on a red", (out or {}).get("continue") is not False)
    check("the receipt says the call is the owner's",
          "your call" in (out or {}).get("systemMessage", "").lower(),
          f"got {(out or {}).get('systemMessage')!r}")

    # ── 5. THE RECEIPT CARRIES ITS EVIDENCE ───────────────────────────────────
    print("\n5. the receipt shows what tripped it, not just that something did")
    msg = (out or {}).get("systemMessage", "")
    check("names the concern marker it matched", "One thing I want" in msg or
          "one thing i want" in msg.lower(), f"got {msg!r}")
    check("names the forward marker it matched", "Anyway" in msg or "anyway" in msg.lower(),
          f"got {msg!r}")
    check("cites the rule's home", "CLAUDE.md" in msg, f"got {msg!r}")

    # ── 6. NEVER WEDGES A TURN ────────────────────────────────────────────────
    print("\n6. every failure path exits 0 and stays off the receipt")
    r1 = run(None, raw="{ not json at all")
    check("malformed input: exit 0", r1.returncode == 0, f"rc={r1.returncode}")
    check("malformed input: nothing on stdout", not r1.stdout.strip(),
          f"stdout={r1.stdout[:120]}")
    r2 = run(None, raw="")
    check("empty stdin: exit 0", r2.returncode == 0, f"rc={r2.returncode}")
    r3 = run({"hook_event_name": "Stop"})
    check("absent message field: exit 0 and silent",
          r3.returncode == 0 and not r3.stdout.strip(), f"stdout={r3.stdout[:120]}")
    out_g, r_g = scan(RED_TURN, stop_hook_active=True)
    check("stop_hook_active suppresses a re-fire", out_g is None,
          "without this a blocking successor could loop")

    # ── 7. the real corpus: CEILING and shape, never today's count ────────────
    print("\n7. against the real transcript corpus: invariants only")
    rc = subprocess.run([sys.executable, str(TURNSCAN), "--corpus"],
                        capture_output=True, text=True)
    check("corpus mode exits 0", rc.returncode == 0,
          f"rc={rc.returncode} err={rc.stderr[:200]}")
    head = rc.stdout.splitlines()[:2] if rc.stdout else []
    check("reports transcripts and turns scanned", len(head) >= 2 and "end_turn" in head[0],
          f"got {head}")
    rate = None
    for line in rc.stdout.splitlines():
        if line.strip().endswith(")") and "red (" in line:
            rate = float(line.split("(")[1].rstrip("%)"))
            break
    check("reports a red RATE", rate is not None, f"stdout={rc.stdout[:200]}")
    # A detector that reds a fifth of all turns is not measuring this rule; it is
    # measuring my vocabulary. The ceiling is the falsifier, not the count.
    check("the red rate is under the 10% ceiling", rate is not None and rate < 10.0,
          f"rate={rate}% — a detector this loud would be noise, not physics")

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
