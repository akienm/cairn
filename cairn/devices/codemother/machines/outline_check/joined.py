"""The joined outline: the requirements pieces as one file, followed by every open question
(ticket b3472c7ee794). Akien 2026-11-17: the joined outline is "the ideal surface for me to
field questions from". The pieces stay the source of truth; this file is derived, and an edit
to it is carried back into its piece by hand until that is scripted.

    cairn codemother outline [<out>]     default ~/.akien/temp/outline.md

A record's Q# is read from its latest note ``outline: Q#n ...`` first, else from ``Q#n (``
or ``Q#n:`` at the opening of its question, or ``where Q#n stands open``. Never from text it quotes.
"""
from __future__ import annotations

import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from cairn.devices.codemother.machines.outline_check import outline_check as OC
from cairn.tools.question import question as Q

DEFAULT_OUT = Path.home() / ".akien" / "temp" / "outline.md"
SECTION_HEAD = "# OPEN QUESTIONS"
NO_MARKER = "NO MARKER IN THE OUTLINE (answered there? close it, or place it)"

_NOTE = re.compile(r"^outline:\s*Q#(\d+)\b")
_OPENING = re.compile(r"^\s*Q#(\d+)\s*[(:]")
_STANDS = re.compile(r"where Q#(\d+) stands open")
_MARK = re.compile(r"\[Q#(\d+)\b")


def qnum(record: dict) -> int | None:
    """The record's Q#, or None when it has none."""
    for n in reversed(record.get("notes") or []):
        m = _NOTE.match(str(n.get("text", "")))
        if m:
            return int(m.group(1))
    text = str(record.get("question", ""))
    m = _OPENING.match(text) or _STANDS.search(text)
    return int(m.group(1)) if m else None


def markers(text: str) -> dict[int, str]:
    """Q# -> the section number of the entry its marker stands in."""
    out: dict[int, str] = {}
    for e in OC.parse(text):
        for m in _MARK.finditer(e["text"]):
            out.setdefault(int(m.group(1)), e["number"])
    return out


def section(pieces_text: str, records: list[dict]) -> str:
    marks = markers(pieces_text)
    by_q: dict[int, list[dict]] = {}
    loose: list[dict] = []
    for r in records:
        n = qnum(r)
        (by_q.setdefault(n, []) if n is not None else loose).append(r)
    stamp = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    lines = [SECTION_HEAD, "",
             f"Generated {stamp} by cairn codemother outline: {len(records)} open, "
             f"{len(by_q)} by number, {len(loose)} unnumbered. A numbered question's words "
             f"stand at its marker above.", ""]
    for n in sorted(by_q):
        where = marks.get(n)
        lines.append(f"## Q#{n} " + (f"at {where}" if where else f"— {NO_MARKER}"))
        for r in by_q[n]:
            lines.append(f"- {r.get('id')} (ticket {r.get('ticket') or '-'})")
            if not where:
                lines.append(f"  {r.get('question', '')}")
        lines.append("")
    if loose:
        lines += ["## Unnumbered", ""]
        for r in loose:
            lines += [f"- {r.get('id')} (ticket {r.get('ticket') or '-'})",
                      f"  {r.get('question', '')}", ""]
    return "\n".join(lines).rstrip() + "\n"


def join(folder: Path | None = None, qroot: Path | str | None = None) -> str:
    """The pieces joined as outline_bytes joins them, then the open-questions section."""
    head = OC.outline_bytes(folder or OC.outline_dir()).decode("utf-8")
    return head + "\n" + section(head, Q.list_open(qroot))


def write(out: Path | None = None) -> Path:
    out = Path(out) if out else DEFAULT_OUT
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(join(), encoding="utf-8")
    return out


def main(argv: list[str]) -> int:
    if len(argv) > 1 or (argv and argv[0].startswith("-")):
        print("usage: cairn codemother outline [<out>]", file=sys.stderr)
        return 2
    print(write(Path(argv[0]) if argv else None))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
