"""Proof for skills/ruled — RETIRED 2026-09-14 under ticket 9adc6fddf185.

Teeth a hollow build could not pass:

  - EVERY MODE REFUSES: bare, a real-looking id, a bogus id — exit 2, nothing written.
    A door.py that still confirms or lists trips this.
  - THE REFUSAL POINTS AT THE REPLACEMENT: `cairn question open` and `cairn question
    answer` are named on stderr, with the ticket. A silent non-zero teaches nobody.
  - NOTHING IN THIS PACKAGE IMPORTS THE RULING MACHINE — the retirement is not a
    wrapper that could be re-armed by one line.

    PYTHONPATH=. python3 -m pytest skills/ruled/proofs/test_ruled.py -v
"""

from __future__ import annotations

import io
import sys
from contextlib import redirect_stderr
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from skills.ruled import door


def _run(argv: list[str]) -> tuple[int, str]:
    buf = io.StringIO()
    with redirect_stderr(buf):
        rc = door.main(argv)
    return rc, buf.getvalue()


def test_bare_ruled_refuses_and_points_at_the_question_door():
    rc, err = _run([])
    assert rc == 2, rc
    assert "cairn question open" in err and "cairn question answer" in err, err
    assert "9adc6fddf185" in err, err


def test_ruled_with_an_id_confirms_nothing():
    rc, err = _run(["2026-08-15-some-ruling"])
    assert rc == 2, rc
    assert "retired" in err, err


def test_ruled_with_a_bogus_id_refuses_the_same_way():
    rc, err = _run(["no-such-thing"])
    assert rc == 2 and "retired" in err, (rc, err)


def test_the_door_does_not_import_the_ruling_machine():
    src = Path(door.__file__).read_text(encoding="utf-8")
    assert "cairn.machines.ruling" not in src, "a retired door that still wraps the machine is one line from re-armed"
    assert "confirm(" not in src


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"  ok {name}")
    print("GREEN")
