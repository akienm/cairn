"""THE REFLECTION — /sail's post-build look back at the packet it was handed, and the door
that carries it to codemother. Ticket 68f563403c8f (post-build-reflection-feeds-codemother).

After the build is proven and before PROVEME is journaled, the builder answers three
questions about the PREBUILD packet — the chart chain, the ticket, the intention — not about
the build: was the packet at par with what the build needed; what specifically deserves
praise or a flag, by artifact and field; what did the packet cost. The answers are a packet
of THIS shape, and the shape is what makes them a record codemother can ingest instead of a
paragraph nobody reads.

THE THREE THINGS THE SHAPE ENFORCES (the ticket's proves_red):

- ``at_par`` is REQUIRED and a bool. "No feedback, the packet was fine" is ``at_par: true``
  with no findings — a complete, POSITIVE answer, at least at par with expectations. Absence
  is refused, because absence is indistinguishable from the step not firing (clause 1), and
  a prompt that frames "nothing to say" as silence suppresses the at-par data point (5).
- a finding names its ``artifact`` and ``field`` and is ``praise`` or ``flag`` — both as easy
  to say as the other (clause 4, the firehose); a flag carries what ``would_change``.
- the shape has NO field for code: a packet carrying ``patch``, ``diff``, ``files`` or any
  other key outside ``SHAPE`` is a second build wearing a reflection's clothes and is refused
  by name (clause 2 — this is post-build, and a finding that changes the build's code is a
  new ticket, never a reflection).

Delivery is a bus request to codemother (verb ``feedback``), never a file write into her
berth from this side (clause 3 — the feedback accumulates in a different observer, which is
the whole point of routing it away from CC).

    PYTHONPATH=$HOME/dev/src/cairn python3 -m skills.sail.reflection <packet.json>

exit 0 delivered (the reply printed), 2 refused (every lack named, nothing sent).
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

# The packet's whole vocabulary. Anything outside it is a lack — see the module docstring.
SHAPE = {
    "ticket": "12-hex id of the ticket the voyage built",
    "at_par": "bool, required and explicit — true means the packet was fine (a positive answer)",
    "findings": "list of {artifact, field, kind, text[, would_change]} — praise and flags alike",
    "cost_estimate": "what the packet cost the build — extra tool calls, minutes, re-reads",
    "stratum": "code | tree",
}
FINDING_KEYS = ("artifact", "field", "kind", "text", "would_change")
ARTIFACTS = ("chart", "ticket", "intention")
KINDS = ("praise", "flag")
STRATA = ("code", "tree")
RECEIVER = "codemother"
VERB = "feedback"

_HEX12 = re.compile(r"^[0-9a-f]{12}$")


def _text(v) -> bool:
    return isinstance(v, str) and bool(v.strip())


def check(packet) -> list[str]:
    """EVERY lack in one pass; ``[]`` is a packet that passes."""
    lacks: list[str] = []
    if not isinstance(packet, dict):
        return [f"the packet is {type(packet).__name__}, not a dict"]
    for k in SHAPE:
        if k not in packet:
            lacks.append(f"{k}: missing — {SHAPE[k]}")
    for k in packet:
        if k not in SHAPE:
            lacks.append(f"{k}: not a field of a reflection (a patch, diff or files key is a "
                         "second build, not a reflection; a reflection carries no code)")
    if "ticket" in packet and not (isinstance(packet["ticket"], str) and _HEX12.match(packet["ticket"])):
        lacks.append("ticket: not a 12-hex ticket id")
    at_par = packet.get("at_par")
    if "at_par" in packet and not isinstance(at_par, bool):
        lacks.append("at_par: must be true or false, explicitly — silence is not an answer")
    findings = packet.get("findings")
    flags = 0
    if "findings" in packet:
        if not isinstance(findings, list):
            lacks.append("findings: must be a list (empty is fine when at_par is true)")
            findings = []
        for i, f in enumerate(findings):
            if not isinstance(f, dict):
                lacks.append(f"findings[{i}]: not a dict")
                continue
            for k in ("artifact", "field", "kind", "text"):
                if not _text(f.get(k)):
                    lacks.append(f"findings[{i}].{k}: missing or empty")
            for k in f:
                if k not in FINDING_KEYS:
                    lacks.append(f"findings[{i}].{k}: not a field of a finding")
            if _text(f.get("artifact")) and f["artifact"] not in ARTIFACTS:
                lacks.append(f"findings[{i}].artifact: {f['artifact']!r} is not one of {ARTIFACTS}")
            kind = f.get("kind")
            if _text(kind) and kind not in KINDS:
                lacks.append(f"findings[{i}].kind: {kind!r} is not one of {KINDS}")
            if kind == "flag":
                flags += 1
                if not _text(f.get("would_change")):
                    lacks.append(f"findings[{i}].would_change: a flag says what would have helped")
            if kind == "praise" and "would_change" in f:
                lacks.append(f"findings[{i}].would_change: praise changes nothing — drop the key")
        if at_par is False and flags == 0:
            lacks.append("at_par: false with no flag finding — below par names what was wrong")
    if "cost_estimate" in packet and not _text(packet.get("cost_estimate")):
        lacks.append("cost_estimate: empty — say what the packet cost, even 'nothing extra'")
    if "stratum" in packet and packet.get("stratum") not in STRATA:
        lacks.append(f"stratum: {packet.get('stratum')!r} is not one of {STRATA}")
    return lacks


def fire(packet: dict, bus=None) -> dict:
    """Check, then post ONE request to codemother. Refuses (ValueError naming every lack)
    before anything is sent; the bus is reached when none is handed in."""
    lacks = check(packet)
    if lacks:
        raise ValueError("reflection refused — " + "; ".join(lacks))
    if bus is None:
        from cairn.tools.bus_client.bus_client import reach
        bus = reach(RECEIVER)
    n = len(packet["findings"])
    return bus.request(
        sender="sail", to=RECEIVER, channel="personal", verb=VERB,
        why=f"post-build reflection on the packet that built {packet['ticket']}: "
            f"{'at par' if packet['at_par'] else 'below par'}, {n} finding(s)",
        body={"reflection": packet})


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        print(__doc__.split("\n\n")[-2], file=sys.stderr)
        return 2
    try:
        packet = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"refused: cannot read a packet at {argv[0]}: {exc}", file=sys.stderr)
        return 2
    lacks = check(packet)
    if lacks:
        print("refused — " + str(len(lacks)) + " lack(s), nothing sent:", file=sys.stderr)
        for l in lacks:
            print("  - " + l, file=sys.stderr)
        return 2
    reply = fire(packet)
    print(json.dumps(reply, indent=2, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
