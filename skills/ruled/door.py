"""skills/ruled/door.py — RETIRED 2026-09-14 (ticket 9adc6fddf185).

Akien, 2026-09-14: *"why are we still doing rulings? we replaced that with questions that
would show up in my inbox."* A decision he has to make is a QUESTION bound to the ticket
that needs it (``cairn question open --ticket <id> "<q?>" --why ...``); his answer IS the
decision (``cairn question answer <qid> "<his words>"``), and the ticket does not cross to
BUILDME while a question stands. There is nothing left for a RULED marker to confirm:
``CairnCommons/decisions/`` stays a read-only, citable record (his answer to
open-68aabd7eb2e0 — no migration), so this door refuses every mode and points at the one
that replaced it. The skill directory stays so the retirement is readable at its own
address rather than inferred from an absence (Law 7).
"""

from __future__ import annotations

import sys

RETIRED = (
    "/ruled is retired (ticket 9adc6fddf185, Akien 2026-09-14: 'why are we still doing "
    "rulings? we replaced that with questions that would show up in my inbox').\n"
    "  a decision he must make:  cairn question open --ticket <id> \"<question?>\" --why \"<what it blocks>\"\n"
    "  his answer (verbatim):    cairn question answer <qid> \"<his words>\" --spawned none | --spawned \"<q?>\"\n"
    "  what stands open:         cairn question list\n"
    "The past rulings stay readable: cairn ruling list | show <id>. Nothing opens or confirms one."
)


def main(argv: list[str]) -> int:
    print(RETIRED, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
