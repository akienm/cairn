"""Proof for ticket 271146bf067d — a runner's drive runs the caller's own interpreter.

Measured 2026-11-13 on akiendell: the rehearsal runner's drive began with a bare ``python3``,
which on Windows is the Microsoft Store stub. It exited 9009 and wrote no trail, so
``a_run_that_fails_to_run_leaves_a_trail`` redded a runner that does leave one. The drive now
names ``{python}``, which the sieve expands to ``sys.executable``. One tooth per falsifier
clause:

  1. no declared runner drive begins with a bare interpreter name, and the rehearsal runner's
     drive begins with ``{python}``;
  2. a testing runner whose drive is ``{python} -c <write a json file into argv[1]> {scratch}``
     reads green: the placeholder expanded to a working interpreter and the scratch arrived;
  3. the same runner with ``testing-no-such-interpreter`` as its first word reds once, and the
     finding's exit starts ``un-runnable``;
  4. (decision D4) no declared drive begins with a bare ``bin/cairn``, the tester runner's drive
     begins with ``{cairn}``, and ``{cairn}`` expands to an absolute launcher that exists:
     ``bin/cairn.cmd`` on Windows (which cannot exec the bash script), ``bin/cairn`` elsewhere.

Every tooth measures only build_inspector (RULE 1). The drives run under scratch dirs that the
sieve mints itself.

    python cairn/machines/build_inspector/proofs/test_a_runner_drive_runs_the_callers_interpreter.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.machines.build_inspector import inspector as I  # noqa: E402

_SIEVE = "a_run_that_fails_to_run_leaves_a_trail"
_BARE = {"python", "python3", "py"}
_WRITER = ("import json, pathlib, sys; "
           "pathlib.Path(sys.argv[1], 'testing-trail.json').write_text(json.dumps({'ok': 1}))")


def _testing_runner(first_word: str) -> dict:
    return {"runner": "testing-interpreter", "component": "testing-interpreter",
            "failure": "testing: a drive that writes one json file", "trail": "*.json",
            "drive": [first_word, "-c", _WRITER, "{scratch}"]}


def _run(runner: dict) -> list[dict]:
    return I.SIEVES[_SIEVE]({"component": runner["component"]}, _REPO_ROOT / "cairn",
                            runners=[runner])


def test_no_declared_drive_names_a_bare_interpreter():
    declared = I.declared_runners()
    for r in declared:
        first = r["drive"][0]
        stem = first.lower().removesuffix(".exe")
        assert stem not in _BARE, f"runner {r['runner']} drives a bare interpreter: {first!r}"
    rehearsal = [r for r in declared if r["runner"] == "rehearsal"]
    assert len(rehearsal) == 1, rehearsal
    assert rehearsal[0]["drive"][0] == "{python}", rehearsal[0]["drive"]


def test_the_python_placeholder_runs_the_callers_interpreter():
    got = _run(_testing_runner("{python}"))
    assert got == [], got


def test_an_interpreter_that_does_not_exist_reds_as_unrunnable():
    got = _run(_testing_runner("testing-no-such-interpreter"))
    assert len(got) == 1 and got[0]["method"] == _SIEVE, got
    exit_value = str(got[0]["values"]["exit"])
    assert exit_value.startswith("un-runnable"), exit_value


def test_the_cairn_placeholder_names_this_hosts_launcher():
    declared = I.declared_runners()
    for r in declared:
        assert r["drive"][0] not in ("bin/cairn", "bin/cairn.cmd"), (r["runner"], r["drive"])
    tester = [r for r in declared if r["runner"] == "tester"]
    assert len(tester) == 1 and tester[0]["drive"][0] == "{cairn}", tester
    seen = {}
    import subprocess

    def _capture(argv, **kw):
        seen["argv"] = argv
        raise OSError("testing: captured, not run")

    subprocess_run, subprocess.run = subprocess.run, _capture
    try:
        _run({"runner": "testing-launcher", "component": "testing-launcher",
              "failure": "testing: the launcher is only named", "trail": "*.json",
              "drive": ["{cairn}", "test", "{scratch}"]})
    finally:
        subprocess.run = subprocess_run
    launcher = Path(seen["argv"][0])
    want = "cairn.cmd" if sys.platform == "win32" else "cairn"
    assert launcher.is_absolute() and launcher.name == want and launcher.is_file(), launcher


def main() -> int:
    teeth = [v for k, v in globals().items() if k.startswith("test_") and callable(v)]
    failed = 0
    for t in teeth:
        try:
            t()
            print(f"  ok   {t.__name__}")
        except Exception as exc:  # noqa: BLE001 — a tooth's failure is its verdict
            failed += 1
            print(f"  FAIL {t.__name__}: {type(exc).__name__}: {exc}")
    print(f"{len(teeth) - failed}/{len(teeth)} green")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
