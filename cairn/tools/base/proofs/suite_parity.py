#!/usr/bin/env python3
"""Suite parity for ticket 284798998ab0 — the ticket split adds no red to the suite (D10).

    python3 cairn/tools/base/proofs/suite_parity.py --baseline <out.json>
    python3 cairn/tools/base/proofs/suite_parity.py <baseline.json>

The first runs ``bin/cairn test -q`` and writes the proof paths it prints as not green —
RED, TIMEOUT, REFUSED, UNRUNNABLE, since none of them is a pass — to ``<out.json>`` through
the artifact door, before any of D2-D8 lands. The second runs the same command after the
build and exits 0 only when every red it sees stands in that baseline's ``red`` list,
printing each new one. A red the build cured is printed too, and does not fail the run.
"""

from __future__ import annotations

import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

COMMAND = ["bin/cairn", "test", "-q"]
NOT_GREEN = re.compile(r"^\s+(RED|TIMEOUT|REFUSED|UNRUNNABLE)\s+(\S+\.py)\b")


def reds(text: str) -> list[str]:
    """The proof paths ``text`` prints as not green, once each, in printed order."""
    out: list[str] = []
    for line in text.splitlines():
        m = NOT_GREEN.match(line)
        if m and m.group(2) not in out:
            out.append(m.group(2))
    return out


def run() -> list[str]:
    proc = subprocess.run(COMMAND, cwd=REPO, capture_output=True, text=True)
    return reds(proc.stdout + proc.stderr)


def main(argv: list[str]) -> int:
    import json
    from cairn.tools.artifact import artifact as A
    if argv[:1] == ["--baseline"] and len(argv) == 2:
        got = run()
        doc = {"measured_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
               "command": " ".join(COMMAND), "red": got}
        A.write_json(Path(argv[1]), doc, verb="measure",
                     why="ticket 284798998ab0 D10: the suite's reds before the ticket split")
        print(f"baseline: {len(got)} red(s) -> {argv[1]}")
        return 0
    if len(argv) != 1:
        print(__doc__, file=sys.stderr)
        return 2
    base = set(json.loads(Path(argv[0]).read_text(encoding="utf-8"))["red"])
    got = run()
    new = [r for r in got if r not in base]
    for r in new:
        print(f"  NEW RED  {r}")
    for r in sorted(base - set(got)):
        print(f"  cured    {r}")
    print(f"{'GREEN' if not new else 'RED'} — {len(got)} red(s) now, {len(new)} not in the baseline "
          f"of {len(base)}")
    return 1 if new else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
