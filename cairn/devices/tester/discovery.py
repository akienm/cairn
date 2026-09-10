"""cairn.devices.tester.discovery — resolving CLI targets to proof files, and nothing else.

WHY THIS IS ITS OWN MODULE, and it is an import-graph reason rather than a tidiness one.
``discover`` used to live in ``cli.py`` beside the command's other faces. ``cli.py`` also
posts the seal announcement, which reaches the bus, and the bus client imports
``inference_domain`` — so anything importing ``cli.py`` inherits a static path to an oracle.
``cairn/tools/base/validation.py`` imports ``cli.py`` for exactly one name (this one), and
seven components import that tool: the build inspector and the six codemother chart doors.
All seven are GATES, and Akien's ruling of 2026-08-13 is that NO GATES MAY CONSULT ORACLES
EVER PERIOD. Measured 2026-09-09 by ``bin/cmd/determinism``: seven of eight standing
violations were that one edge, none of them touching the component the ticket named.

The same shape was measured and cleared once already — ticket 9579a6f9cec6 (2026-09-08) took
a bus dial out of ``validation_store.py`` for the same reason, and its comment is still in the
tree at line 742 saying so. Nine hours before this module was written, commit f8d09aa put a
dial back one file over. That is why the fix here is a SEAM and not a promise: a function with
no imports beyond ``Path`` and ``sys`` cannot re-acquire an oracle by anyone's later edit,
where a rule saying "don't dial the bus from cli.py" could only be re-broken.

``cli.py`` imports both names straight back, so the command's public surface is unchanged.
"""

from __future__ import annotations

import sys
from pathlib import Path

# The repo root: cairn/devices/tester/discovery.py -> cairn/devices/tester -> cairn -> root
REPO_ROOT = Path(__file__).resolve().parents[3]


def discover(targets: list[str]) -> list[Path]:
    """Resolve CLI targets to proof files.

    A directory (or no argument at all, meaning the repo) expands to every
    ``*/proofs/test_*.py`` beneath it. Sorted, because an unstable run order makes an
    intermittent red impossible to attribute — the one failure mode a proof suite must
    never add on its own.
    """
    if not targets:
        targets = [str(REPO_ROOT)]
    found: list[Path] = []
    for t in targets:
        p = Path(t)
        if not p.is_absolute():
            p = (Path.cwd() / p).resolve()
        if p.is_file():
            found.append(p)
        elif p.is_dir():
            # BOTH SHAPES, because the obvious thing to type is a ``proofs/`` directory and
            # the pattern below cannot match it: ``**/proofs/test_*.py`` requires a
            # ``proofs`` segment BENEATH the directory given, so pointing this command at
            # ``cairn/tools/base/proofs/`` found ZERO files and the run reported success on
            # whatever else was named alongside it. Measured 2026-09-07 while sealing a
            # six-target run: 3 proofs found where 14 were asked for. That is exactly the
            # hollow green the docstring above forbids, wearing the one disguise it did not
            # check for — a correct-looking count.
            found.extend(p.glob("**/proofs/test_*.py"))
            if p.name == "proofs":
                found.extend(p.glob("test_*.py"))
        else:
            # Loud, and it exits non-zero below. A typo'd path that silently ran zero
            # proofs and reported success is a hollow green (Law 8) — the worst outcome
            # this command could produce, because it looks exactly like a good one.
            print(f"cairn test: no such path: {t}", file=sys.stderr)
            found.append(Path(t))  # kept so the run reports it as unrunnable, not skipped
    # dedupe, keep determinism
    return sorted(set(found))
