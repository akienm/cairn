"""THE BUILD'S TOOL CALLS ARE EVIDENCE ABOUT THE CHART — the count leg of /sail step 9.
Ticket 61416fbb8013.

The chart's job is to guess every tool call a build needs before the build starts, so every
call the build still makes is a measured anticipation miss (Akien, open-0aa1abce1583). This
module counts them from the session transcript and reads the ones that touch a path against
the claims the ticket was cast with (Akien, open-a5798f263e66: option 2, claims plus surprises):

- a WRITE to a path outside ``bounds.in`` is a **surprise**: a write outside every charted path;
- a WRITE to a path ``bounds.out`` names is a **contradiction** of constrain's hard edge;
- a READ of a path no decision reads or writes is a **miss**; a read the decisions foresaw is
  counted and makes no finding (no claim, no finding: the firehose is refused by construction).

The claims are the ticket's own ``bounds`` and ``decisions``, read from the commons, because the
chart berths sit in instance-space on whichever box charted, and the transcript on the box that
built. Writes made inside a Bash command are not seen; completeness is not the aim (his answer).

The transcript is PARSED, record by record, never grepped: the file stores ``/`` and non-ASCII
escaped, so a substring match reports a real path absent.

    PYTHONPATH=$HOME/dev/src/cairn python3 -m skills.sail.toolcalls <ticket> [--transcript F]
        [--since ISO] [--until ISO] [--into reflection.json]

Without ``--into`` the observation prints as JSON. With it, the observation merges into the
reflection packet at that path (cost_estimate and findings), which the builder finishes by hand
(``at_par``) and fires with ``python3 -m skills.sail.reflection``; that door's bus verb
``feedback`` lands in codemother, whose ``ingest_reflections`` is the consumer.
exit 0 observed, 2 refused (an unreadable transcript, an unfiled ticket, an unwindowed ticket).
"""

from __future__ import annotations

import glob
import json
import os
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

WRITES = ("Write", "Edit", "NotebookEdit")
READS = ("Read",)
OPENERS = ("show artifact", "outlinecheck")


def _path_of(name: str, inp: dict) -> str | None:
    p = inp.get("file_path") or inp.get("notebook_path")
    return p if isinstance(p, str) and p.strip() else None


def tool_calls(transcript: str | Path) -> list[dict]:
    """Every tool_use block in the transcript, in order: {at, name, input}. Parsed records."""
    out: list[dict] = []
    with open(transcript, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            msg = rec.get("message") if isinstance(rec, dict) else None
            content = msg.get("content") if isinstance(msg, dict) else None
            if not isinstance(content, list):
                continue
            for b in content:
                if isinstance(b, dict) and b.get("type") == "tool_use":
                    inp = b.get("input") if isinstance(b.get("input"), dict) else {}
                    out.append({"at": rec.get("timestamp") or "", "name": b.get("name") or "",
                                "input": inp})
    return out


def window(calls: list[dict], ticket: str, since: str | None = None,
           until: str | None = None) -> list[dict] | None:
    """The calls of this ticket's voyage. With since/until, the calls between them (ISO
    strings compare in order). Without, from the voyage's opening call (the last one that loads
    or checks the ticket: ``show artifact <id>``, ``outlinecheck <id>``) to the
    last call naming the id; from the first naming call when no opening call stands. A session
    names a ticket long before it builds it (a list, a reply), and measured on the first live
    fire (2026-11-13) a first-mention start swept a whole earlier voyage in. None when no call
    names it: an unwindowed ticket is said, never counted as the session."""
    if since or until:
        return [c for c in calls if (not since or c["at"] >= since) and (not until or c["at"] <= until)]
    text = [json.dumps(c["input"], ensure_ascii=False) for c in calls]
    named = [i for i, t in enumerate(text) if ticket in t]
    if not named:
        return None
    opens = [i for i in named if any(f"{v} {ticket}" in text[i] for v in OPENERS)]
    return calls[(opens[-1] if opens else named[0]): named[-1] + 1]


def _roots() -> dict[str, str]:
    """Absolute prefix -> the spelling a ticket uses for it: the cairn repo is repo-relative,
    the commons is ``CairnCommons/...``."""
    cairn = {str(_REPO), os.path.realpath(str(_REPO)),
             os.path.expanduser("~/dev/src/cairn"), os.path.expanduser("~/cairn")}
    commons = {os.path.expanduser("~/dev/src/CairnCommons"), os.path.expanduser("~/CairnCommons"),
               os.path.realpath(os.path.expanduser("~/dev/src/CairnCommons"))}
    out = {r.rstrip("/") + "/": "" for r in cairn}
    out.update({r.rstrip("/") + "/": "CairnCommons/" for r in commons})
    return dict(sorted(out.items(), key=lambda kv: len(kv[0]), reverse=True))


def relative(path: str, roots: dict[str, str] | None = None) -> str | None:
    """A path in the repos, in the spelling a ticket uses; None for a path outside both (a
    scratchpad, /tmp). The charted paths are repo paths, so a write outside the repos is
    counted and not judged: measured on the first live fire, scratch scripts were the only
    'surprises', which is the firehose the ticket refuses."""
    for r, to in (roots if roots is not None else _roots()).items():
        if path.startswith(r):
            return to + path[len(r):]
    return None


def _under(path: str, entries) -> bool:
    for e in entries or []:
        if not isinstance(e, str):
            continue
        e = e.rstrip("/")
        if path == e or path.startswith(e + "/"):
            return True
    return False


def observe(ticket_doc: dict, calls: list[dict], roots: dict[str, str] | None = None) -> dict:
    """Count the calls and read the path-bearing ones against the ticket's claims."""
    bounds = ticket_doc.get("bounds") if isinstance(ticket_doc.get("bounds"), dict) else {}
    b_in, b_out = bounds.get("in") or [], bounds.get("out") or []
    foreseen: list[str] = []
    for d in ticket_doc.get("decisions") or []:
        if isinstance(d, dict):
            foreseen += [p for p in (d.get("reads") or []) + (d.get("writes_to") or []) if isinstance(p, str)]
    by_tool: dict[str, int] = {}
    findings: list[dict] = []
    for c in calls:
        by_tool[c["name"]] = by_tool.get(c["name"], 0) + 1
        raw = _path_of(c["name"], c["input"])
        if raw is None:
            continue
        path = relative(raw, roots)
        if path is None:
            continue
        if c["name"] in WRITES:
            if _under(path, b_out):
                findings.append({"kind": "contradiction", "field": "bounds.out", "path": path,
                                 "tool": c["name"], "at": c["at"]})
            elif not _under(path, b_in):
                findings.append({"kind": "surprise", "field": "bounds.in", "path": path,
                                 "tool": c["name"], "at": c["at"]})
        elif c["name"] in READS and not (_under(path, foreseen) or _under(path, b_in)):
            findings.append({"kind": "miss", "field": "decisions.reads", "path": path,
                             "tool": c["name"], "at": c["at"]})
    return {"ticket": ticket_doc.get("id"), "calls": len(calls), "by_tool": by_tool,
            "findings": findings}


def merge(observation: dict, packet: dict) -> dict:
    """Fold the observation into a reflection packet: the count into cost_estimate, each
    surprise and contradiction as a flag on the ticket field it falsifies. Misses are summed
    in cost_estimate rather than listed, one line per read would be the firehose."""
    out = dict(packet)
    out["ticket"] = out.get("ticket") or observation.get("ticket")
    found = observation.get("findings") or []
    misses = [f for f in found if f["kind"] == "miss"]
    tools = ", ".join(f"{k} {v}" for k, v in sorted(observation.get("by_tool", {}).items()))
    count = (f"{observation.get('calls', 0)} tool calls after the chart, each an anticipation miss "
             f"({tools or 'none'}); {len(misses)} read(s) no decision foresaw"
             + (f": {', '.join(sorted({f['path'] for f in misses})[:10])}" if misses else ""))
    prior = out.get("cost_estimate")
    out["cost_estimate"] = f"{prior}; {count}" if isinstance(prior, str) and prior.strip() else count
    flags = list(out.get("findings") or [])
    for f in found:
        if f["kind"] == "miss":
            continue
        flags.append({"artifact": "ticket", "field": f["field"], "kind": "flag",
                      "text": f"{f['kind']}: {f['tool']} {f['path']} at {f['at']}",
                      "would_change": (f"{f['field']} names {f['path']}" if f["kind"] == "surprise"
                                       else f"{f['path']} is in or out of bounds, said once")})
    out["findings"] = flags
    return out


def _latest_transcript() -> str | None:
    cwd = os.getcwd().replace("/", "-")
    found = sorted(glob.glob(os.path.expanduser(f"~/.claude/projects/{cwd}/*.jsonl")),
                   key=os.path.getmtime)
    return found[-1] if found else None


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if not argv or argv[0].startswith("-"):
        print(__doc__.split("\n\n")[-2], file=sys.stderr)
        return 2
    ticket, opts, i = argv[0], {}, 1
    while i < len(argv):
        if argv[i] in ("--transcript", "--since", "--until", "--into", "--tickets-dir") and i + 1 < len(argv):
            opts[argv[i][2:]] = argv[i + 1]
            i += 2
        else:
            print(f"refused: unknown argument {argv[i]}", file=sys.stderr)
            return 2
    from cairn.tools.chain.grammar import ticket_path
    tp = ticket_path(ticket, tickets_dir=opts.get("tickets-dir"))
    if tp is None:
        print(f"refused: no ticket {ticket} on file", file=sys.stderr)
        return 2
    transcript = opts.get("transcript") or _latest_transcript()
    try:
        doc = json.loads(Path(tp).read_text(encoding="utf-8"))
        calls = tool_calls(transcript)
    except (OSError, TypeError, ValueError) as exc:
        print(f"refused: cannot read {transcript or 'a transcript'}: {exc}", file=sys.stderr)
        return 2
    win = window(calls, ticket, opts.get("since"), opts.get("until"))
    if win is None:
        print(f"refused: no tool call in {transcript} names {ticket}; pass --since/--until",
              file=sys.stderr)
        return 2
    obs = observe(doc, win)
    if "into" in opts:
        p = Path(opts["into"])
        packet = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
        p.write_text(json.dumps(merge(obs, packet), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(p)
    else:
        print(json.dumps(obs, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
