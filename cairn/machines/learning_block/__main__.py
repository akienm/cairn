"""The primitive's shell door — how a BASH component, and AKIEN'S OWN HAND, ride it.

    python3 -m cairn.machines.learning_block trace <block> <door_pass|send_back> <op> [lack ...]
    python3 -m cairn.machines.learning_block dial  <block>
    python3 -m cairn.machines.learning_block recordverdict [<target>] [<signal>] ["<words>"]

trace/dial were built for the deploy pass's approved move (one wire per existing
door): superclaude and logger_for_bash are bash, and a wire only python can fire is
a wire two of the four ordered components cannot wear.

recordverdict (ticket recordverdict-cli-door, Akien 2026-08-01: "i still want
/recordverdict but more importantly, we'll need to automate this gating process")
revises this door's original stance that verdicts stay python-side: the VERDICT is
the one organ whose caller is a human shell — his gate act must not route through
anyone's keystroke. The verb:

  - bare            → LIST what stands at the gate (pure read, touches nothing)
  - "<words>"       → signal parsed from the words' leading token ("Approved …"),
                      target = the single pending finding; anything ambiguous or
                      unparseable is REFUSED with every lack named in one pass
  - <target> …      → a finding-id prefix or a block name, when more than one
                      finding is in flight (his multi-flight requirement)
  - <signal>        → approve|disprove|question, explicit, when the words don't
                      lead with one

The gate name on the record is DERIVED from the finding's block, never typed —
the 2026-08-01 mislabel (gate-record lb-20260801-f4f21cbb wrote gate='akien'
where block-name was the convention) is the measured defect that rule kills.
The write rides learning_block.record_verdict alone; this door adds NO second
path into CairnCommons/learning/ (the ticket's falsifier 3).

Exit codes are honest: 0 recorded (or listed), 2 refused (the lack named on
stderr). Callers whose prime directive forbids dying on this (superclaude's
launch, a sourced logger) guard the CALL SITE with `|| true`; this door itself
never lies with a green exit.
"""

from __future__ import annotations

import getpass
import json
import platform
import sys

from cairn.machines.learning_block import learning_block as lb

_USAGE = (
    "usage: cairn recordverdict                                — list what stands at the gate\n"
    "       cairn recordverdict \"<your words>\"                 — judge the single pending finding\n"
    "       cairn recordverdict <block-or-id> \"<your words>\"   — name the finding you judge\n"
    "       cairn recordverdict [<block-or-id>] <approve|disprove|question> \"<your words>\""
)


def _infer_signal(words: str) -> str | None:
    """The leading token of his words, when it already says the signal.
    'Approved - more to come…' → approve. Anything less obvious is not guessed."""
    for token in words.replace("-", " ").replace(":", " ").split():
        token = token.strip(".,!?—").lower()
        if not token:
            continue
        if token.startswith("approv"):
            return "approve"
        if token.startswith("disprov"):
            return "disprove"
        if token.startswith("question"):
            return "question"
        return None
    return None


def _show(f: dict, out) -> None:
    print(f"  [{f.get('block', '?')}] {f.get('id', '?')}  {str(f.get('when', ''))[:19]}",
          file=out)
    for b in (f.get("data") or {}).get("bullets", []):
        print(f"      · ({b.get('stratum', '?')}) {b.get('text', '')}", file=out)


def _recordverdict(args: list[str]) -> int:
    pend = lb.pending_findings()

    if not args:                                     # the bare command: the gate, listed
        if not pend:
            print("nothing stands at the gate — every finding has its verdict.")
            return 0
        print(f"AT THE GATE — {len(pend)} finding(s) awaiting a verdict:")
        for f in pend:
            _show(f, sys.stdout)
        print('answer with: cairn recordverdict [<block-or-id>] "<your words>"')
        return 0

    target: str | None = None
    signal: str | None = None
    if len(args) == 1:
        words = args[0]
    elif len(args) == 2 and args[0] in lb.SIGNALS:
        signal, words = args
    elif len(args) == 2:
        target, words = args
    elif len(args) == 3 and args[1] in lb.SIGNALS:
        target, signal, words = args
    else:
        print(_USAGE, file=sys.stderr)
        return 2

    # Every lack in one pass (Law 7): words and signal are checked together.
    lacks: list[str] = []
    if not str(words).strip():
        lacks.append("the words are empty — the signal carries Akien's words verbatim "
                     "or it is a keystroke wearing his act")
    if signal is None:
        signal = _infer_signal(words)
        if signal is None and str(words).strip():
            lacks.append(f"no signal: the words {words[:40]!r} do not lead with "
                         "approve/disprove/question — say it explicitly: "
                         'cairn recordverdict [<target>] <signal> "<words>"')
    if lacks:
        print("recordverdict refused —", file=sys.stderr)
        for lack in lacks:
            print(f"  · {lack}", file=sys.stderr)
        return 2

    if target is not None:
        matches = [f for f in pend
                   if str(f.get("id", "")).startswith(target) or f.get("block") == target]
        if not matches:
            print(f"recordverdict refused — {target!r} matches nothing pending "
                  "(an invented finding is refused against the berth's actual contents). "
                  + ("At the gate:" if pend else "Nothing stands at the gate."),
                  file=sys.stderr)
            for f in pend:
                _show(f, sys.stderr)
            return 2
    else:
        matches = pend
        if not matches:
            print("recordverdict refused — nothing stands at the gate; a verdict "
                  "needs a finding to judge.", file=sys.stderr)
            return 2

    if len(matches) > 1:
        print(f"recordverdict refused — {len(matches)} findings stand at the gate; "
              "an ambiguous act is never guessed. Name the one you judge "
              "(block name or id prefix):", file=sys.stderr)
        for f in matches:
            _show(f, sys.stderr)
        return 2

    finding = matches[0]
    # platform.node(), not socket.gethostname(): both read the same local name, but importing
    # `socket` makes this module a module that CAN DIAL, and inference_domain's sole-path tooth
    # scans for exactly that (Law 6 — the inference host has one door, by construction). The
    # honest fix is not an allowlist entry for a module that never connects; it is to not hold
    # the capability at all.
    session = f"shell:{getpass.getuser()}@{platform.node()}"
    try:
        path = lb.record_verdict(finding["block"], finding, signal, words,
                                 session=session,
                                 note="recorded via cairn recordverdict — "
                                      "the gate owner's own shell")
    except lb.VerdictRefused as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(f"recorded: {signal} on {finding['id']} ({finding['block']}) -> {path}")
    print(json.dumps(lb.dial(finding["block"])))
    return 0


def main(argv: list[str]) -> int:
    if argv and argv[0] == "recordverdict":
        return _recordverdict(argv[1:])
    if len(argv) == 2 and argv[0] == "dial":
        print(json.dumps(lb.dial(argv[1])))
        return 0
    if len(argv) < 3 or argv[0] != "trace":
        print("usage: python3 -m cairn.machines.learning_block trace <block> "
              "<door_pass|send_back> <op> [lack ...]   |   dial <block>   |\n"
              + _USAGE, file=sys.stderr)
        return 2
    _, block, event, *rest = argv
    if event not in ("door_pass", "send_back"):
        print(f"trace refused — event {event!r} is not a firing "
              "(door_pass|send_back); findings go through python",
              file=sys.stderr)
        return 2
    if not rest:
        print("trace refused — the op is missing (what fired?)", file=sys.stderr)
        return 2
    op, *lacks = rest
    if event == "send_back" and not lacks:
        print("trace refused — a send_back names its lack(s); an unnamed refusal "
              "teaches nothing", file=sys.stderr)
        return 2
    data: dict = {"op": op}
    if lacks:
        data["lacks"] = lacks
    lb.write_trace(block, event, "training", data)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
