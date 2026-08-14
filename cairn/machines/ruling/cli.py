"""cairn/machines/ruling/cli.py — the verbs, and the Stop hook that makes the gate fire itself.

WHY THERE IS A HOOK AT ALL. A gate I have to REMEMBER to run is the /loadslate defect
rebuilt: discipline doing a job physics should do (Law 4), and the reason /loadslate is
deleted is that it only ran when Akien remembered to type it. So the same answer applies
one layer down — the host fires a Stop hook unconditionally, every turn, and turnscan
already proves that seat works.

WHAT THE HOOK DOES AND DOES NOT DO. It reports; it never blocks. A red ruling means either
Akien has not confirmed my reading yet or the tree contradicts a confirmed one — and in
both cases the disposition is his, not mine. It is the trouble lane's rule applied to
rulings: an open one stays in the inbox until cleared, printing every turn, because a
ruling that goes quiet is exactly how the last one got lost.

IT CANNOT WEDGE A TURN. Every path exits 0, including a crash. A gate that can kill the
session is a worse defect than the silence it replaces.

    echo '{}' | python3 -m cairn.machines.ruling.cli --hook
"""

from __future__ import annotations

import json
import sys

from cairn.machines.ruling import ruling

_USAGE = """cairn ruling — the ruling intake gate (CairnCommons/decisions/)

  cairn ruling open <packet.json>   intake: refuse with every reason, or write
  cairn ruling list                 every ruling and its verdict
  cairn ruling verify <id>          the mechanical verdict for one
  cairn ruling confirm <id> "<his words>"   his sign-off, with its source recorded
  cairn ruling supersede <old-id> <new-id> "<evidence>"   retire a misfiled packet:
                                    stamps the successor, never touches the retired
"""


def _cmd_open(path: str) -> int:
    with open(path, encoding="utf-8") as fh:
        packet = json.load(fh)
    try:
        written = ruling.open_ruling(packet)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(f"ruling opened: {written}")
    # No second ask, either way. If he typed RULED it is confirmed and there is nobody to
    # ask; if he did not, this is MY reading and the work proceeds regardless — an unmarked
    # packet is never a red and never a nag (Akien, 2026-08-13: "it does not need to stop
    # the work"). Said once, here, and not again every turn.
    if ruling.ruled_marks(json.load(open(written, encoding="utf-8"))):
        print("CONFIRMED by his RULED marker. The verdict now measures the WORK.")
    else:
        print("UNMARKED — no RULED in his words, so this is MY READING on the record. "
              "It does not stop the work and will not be raised again; it stays visible "
              "in `cairn ruling list` until he marks it.")
    return 0


def _cmd_list() -> int:
    records = ruling.load_all()
    if not records:
        print("no rulings in the store")
        return 0
    # Presentation may collapse a retired packet's reds into one line (Law 7 allows a
    # surface to do that); the record itself is untouched and verify still reds on it.
    superseded_by = {e["id"]: r["id"] for r in records if r.get("confirmed")
                     for e in ruling._supersessions(r)}
    red = proved = 0
    for record in records:
        if record.get("id") in superseded_by:
            print(f"  ret'd  {record['id']}")
            print(f"         → superseded by {superseded_by[record['id']]}")
            continue
        verdict = ruling.verify(record)
        mark = "green" if verdict["green"] else "RED"
        # THE MARKER IS SHOWN, NEVER NAGGED. `RULED` is his word on the packet; its absence
        # means this is MY READING awaiting his — a fact about who has spoken, not a defect
        # in the work, so it rides beside the verdict and never inside it (2026-08-13).
        print(f"  {mark:5}  {'RULED ' if verdict['ruled'] else 'mine  '} {record['id']}")
        print(f"         {record['now_the_spec_says']}")
        for failure in verdict["failures"]:
            print(f"         ! {failure}")
        red += 0 if verdict["green"] else 1
        proved += len(verdict["record"])
    mine = sum(1 for r in records if r.get("id") not in superseded_by
               and not r.get("confirmed"))
    # THE COUNT OF CHECKS IS THE BOARD'S HALF OF THE RECORD (Akien, 2026-08-13:
    # "EVERYTHING ALWAYS PROVED AND LISTING WHAT IT PROVED"). The board is a presentation
    # surface and Law 7 lets it collapse — 42 rulings printing every entry is 200 lines
    # nobody reads — but "0 red" alone is the silence the ruling names, since it is the
    # same words whether every lane ran or none did. The number moves when a lane stops
    # running; `cairn ruling verify <id>` prints that ruling's entries whole.
    print(f"\n{len(records)} ruling(s) · {red} red · {len(superseded_by)} retired"
          f" · {proved} checks proved"
          + (f" · {mine} unmarked (my reading, awaiting his RULED)" if mine else ""))
    return 0


def _cmd_verify(ruling_id: str) -> int:
    for record in ruling.load_all():
        if record.get("id") == ruling_id:
            verdict = ruling.verify(record)
            print(json.dumps(verdict, indent=2, ensure_ascii=False))
            return 0 if verdict["green"] else 1
    print(f"no such ruling: {ruling_id}", file=sys.stderr)
    return 1


def _cmd_confirm(ruling_id: str, evidence: list[str]) -> int:
    try:
        path = ruling.confirm(ruling_id, " ".join(evidence))
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(f"confirmed: {path}")
    return 0


def _cmd_supersede(old_id: str, new_id: str, evidence: list[str]) -> int:
    try:
        path = ruling.supersede(old_id, new_id, " ".join(evidence))
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(f"retired: {old_id} — successor stamped at {path}")
    print("the retired packet itself is untouched; `cairn ruling list` still shows it")
    return 0


def _hook() -> int:
    """Stop-hook mode: one line to Akien when a ruling is open or contradicted."""
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        payload = {}
    if payload.get("stop_hook_active"):
        return 0

    reds = ruling.open_rulings()
    if not reds:
        return 0

    # The receipt names the ruling and its first failure — a marker that only ever says
    # "something is open" is a check that goes green for the wrong reason, because it
    # reads identically over a packet nobody can act on.
    parts = [f"{v['id']}: {v['failures'][0]}" for v in reds]
    msg = f"⚖ {len(reds)} ruling(s) not settled — " + " | ".join(parts)
    print(json.dumps({"systemMessage": msg}, ensure_ascii=False))
    return 0


def main(argv: list[str]) -> int:
    if "--hook" in argv:
        return _hook()
    if "--corpus" in argv:
        from cairn.machines.ruling import corpus
        i = argv.index("--corpus")
        return corpus.report(argv[i + 1] if len(argv) > i + 1 else corpus.DEFAULT_CORPUS)
    if not argv:
        print(_USAGE, file=sys.stderr)
        return 2

    verb, rest = argv[0], argv[1:]
    if verb == "open" and rest:
        return _cmd_open(rest[0])
    if verb == "list":
        return _cmd_list()
    if verb == "verify" and rest:
        return _cmd_verify(rest[0])
    if verb == "confirm" and len(rest) >= 2:
        return _cmd_confirm(rest[0], rest[1:])
    if verb == "supersede" and len(rest) >= 3:
        return _cmd_supersede(rest[0], rest[1], rest[2:])

    print(f"cairn ruling: unknown or incomplete: {' '.join(argv)!r}\n", file=sys.stderr)
    print(_USAGE, file=sys.stderr)
    return 2


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception as exc:            # a gate must never be able to wedge a turn
        print(f"cairn ruling failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(0 if "--hook" in sys.argv else 1)
