"""Proof that the librarian's command line folds its system words (ticket c29a2d0dcebb).

Ruled 2026-09-07 (ticket e3cf75c6dc8f): a status or command word Akien may type is case
insensitive. ``live._main`` folds its first token and passes the rest verbatim. Until this
ticket that was measured from system_word's proof, which imported the librarian (RULE 1: a
ticket's proofs measure only that component), so the tooth berths here with its owner.

Each branch is stubbed and driven twice, lowercase and uppercase; the stub records what it was
handed, so a fold that touched the rest of the line, or a branch the uppercase word missed,
reds. Nothing runs the loop or reaches the bus.

    python3 cairn/devices/librarian/proofs/test_librarian_cli_folds_its_verbs.py   # exit 0 = green
"""

from __future__ import annotations

import io
import sys
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"c29a2d0dcebb": {
    "1": "test_an_uppercase_verb_reaches_its_branch",
    "2": "test_the_rest_of_the_line_rides_verbatim",
}}

_BRANCHES = {"loop": "_loop", "shelve": "_shelve_collection", "learn": "_learn",
             "summarize": "_summarize"}


def _drive(argv: list[str]) -> dict:
    """Run live._main with every branch stubbed; return {branch: [rest, ...]} it reached."""
    from cairn.devices.librarian import live
    hits: dict[str, list] = {}
    saved = {name: getattr(live, name) for name in _BRANCHES.values()}
    for verb, name in _BRANCHES.items():
        setattr(live, name, lambda rest, verb=verb: hits.setdefault(verb, []).append(rest) or 0)
    try:
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            rc = live._main(argv)
    finally:
        for name, fn in saved.items():
            setattr(live, name, fn)
    assert rc == 0, f"{argv!r} exited {rc}"
    return hits


def test_an_uppercase_verb_reaches_its_branch():
    for verb in _BRANCHES:
        for spelled in (verb, verb.upper(), verb.capitalize()):
            got = _drive([spelled, "x"])
            assert list(got) == [verb], (
                f"{spelled!r} reached {list(got)!r}, not the {verb!r} branch — the librarian's "
                f"command word did not fold")


def test_the_rest_of_the_line_rides_verbatim():
    got = _drive(["LOOP", "Once", "MiXeD Text"])
    assert got == {"loop": [["Once", "MiXeD Text"]]}, (
        f"the fold reached past the verb: {got!r}")


def _main() -> int:
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_")]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"  PASS  {name}")
        except Exception as exc:  # noqa: BLE001 — a proof reports every red (Law 7)
            failed += 1
            print(f"  FAIL  {name}: {type(exc).__name__}: {exc}")
    print(f"\n{len(tests) - failed}/{len(tests)} green")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(_main())
