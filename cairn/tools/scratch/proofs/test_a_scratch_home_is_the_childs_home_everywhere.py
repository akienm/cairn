"""Proof for ticket d95796cdfb9b — a scratch HOME is the child's home on Windows too.

Measured 2026-11-13 on akiendell: a child given HOME=<scratch> still found Path.home() at
C:\\Users\\akien, because on Windows Path.home() and expanduser('~') read USERPROFILE and ignore
HOME. cairn/tools/base/address.py builds the instance root as Path.home()/'.cairn', so the child
resolved the LIVE ~/.cairn, and a proof's fixture traces landed in the live librarian berth.

One tooth per falsifier clause:

  1. a child run with sys.executable under home_env(scratch) prints Path.home(),
     os.path.expanduser('~') and cairn.tools.base.address.ROOTS['instance'], and they equal
     scratch, scratch and scratch/.cairn (on Windows and POSIX alike);
  2. home_env(scratch, USERPROFILE=other) gives USERPROFILE=other: extra still applies last;
  3. scratch_home_bypass over a testing tree with one proof that does dict(os.environ, HOME=x)
     and one that calls home_env(x) names exactly the first;
  4. home_env names the box the child was moved off: CAIRN_SCRATCH_BOX_INSTANCE is the caller's
     ~/.cairn, and a value the caller already carries (it is itself a scratch child) is kept.
     Measured 2026-11-13: without it, test_clearance.py's scratch-HOME ask red on Windows with
     "5432 fe_sendauth: no password supplied" (the box's pgpass is under the box, not the scratch).

    python cairn/tools/scratch/proofs/test_a_scratch_home_is_the_childs_home_everywhere.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from cairn.tools.scratch import scratch  # noqa: E402

PROVES = {"d95796cdfb9b": {
    "1": "test_a_child_under_home_env_finds_its_home_in_the_scratch",
    "2": "test_an_explicit_userprofile_in_extra_still_wins",
    "3": "test_the_bypass_scan_names_the_hand_built_env_and_not_the_door",
    "4": "test_home_env_names_the_box_the_child_was_moved_off"}}

_PROBE = ("import json, os; from pathlib import Path; "
          "from cairn.tools.base.address import ROOTS; "
          "print(json.dumps([str(Path.home()), os.path.expanduser('~'), str(ROOTS['instance'])]))")


def _same(a: str, b: Path) -> bool:
    return os.path.normcase(os.path.realpath(a)) == os.path.normcase(os.path.realpath(str(b)))


def test_a_child_under_home_env_finds_its_home_in_the_scratch():
    home = scratch.scratch_dir("home-env-userprofile-testing-")
    env = scratch.home_env(home, PYTHONPATH=str(REPO))
    r = subprocess.run([sys.executable, "-c", _PROBE], cwd=str(home), env=env,
                       capture_output=True, text=True, encoding="utf-8", errors="replace",
                       timeout=120)
    assert r.returncode == 0, r.stdout[-1500:] + r.stderr[-1500:]
    got_home, got_user, got_instance = json.loads(r.stdout.strip().splitlines()[-1])
    assert _same(got_home, home), f"Path.home() in the child is {got_home}, not the scratch {home}"
    assert _same(got_user, home), f"expanduser('~') in the child is {got_user}, not {home}"
    assert _same(got_instance, home / ".cairn"), \
        f"the child's instance root is {got_instance}, not {home / '.cairn'}: it reaches live space"


def test_an_explicit_userprofile_in_extra_still_wins():
    home = Path("/nonexistent/scratch-home-d95796cdfb9b")
    other = Path("/nonexistent/other-profile-d95796cdfb9b")
    plain = scratch.home_env(home)
    assert plain["HOME"] == str(home) and plain["USERPROFILE"] == str(home), \
        (plain.get("HOME"), plain.get("USERPROFILE"))
    named = scratch.home_env(home, USERPROFILE=other)
    assert named["USERPROFILE"] == str(other), named.get("USERPROFILE")
    assert named["HOME"] == str(home), named.get("HOME")


_BYPASS = '''import os
import subprocess


def _env(home):
    return dict(os.environ, HO''' + '''ME=str(home))


def test_runs():
    subprocess.run(["true"], env=_env("/x"))
'''

_DOOR = '''from cairn.tools.scratch.scratch import home_env


def _env(home):
    return home_env(home)


def test_runs():
    assert _env("/x")
'''


def test_the_bypass_scan_names_the_hand_built_env_and_not_the_door():
    tree = scratch.scratch_dir("home-bypass-scan-testing-")
    (tree / "comp_a" / "proofs").mkdir(parents=True)
    (tree / "comp_b" / "proofs").mkdir(parents=True)
    (tree / "comp_a" / "proofs" / "test_bypass.py").write_text(_BYPASS, encoding="utf-8")
    (tree / "comp_b" / "proofs" / "test_door.py").write_text(_DOOR, encoding="utf-8")
    # a non-proof file with the same body is out of the scan's reach, as bare_temp_reach's is
    (tree / "comp_a" / "helper.py").write_text(_BYPASS, encoding="utf-8")
    got = scratch.scratch_home_bypass(tree)
    assert got == ["comp_a/proofs/test_bypass.py:5 _env"], got


def test_home_env_names_the_box_the_child_was_moved_off():
    home = Path("/nonexistent/scratch-home-d95796cdfb9b")
    saved = os.environ.pop(scratch.BOX_INSTANCE_VAR, None)
    try:
        env = scratch.home_env(home)
        assert env[scratch.BOX_INSTANCE_VAR] == str(Path.home() / ".cairn"),             env.get(scratch.BOX_INSTANCE_VAR)
        assert not env[scratch.BOX_INSTANCE_VAR].startswith(str(home)), "it must name the box"
        os.environ[scratch.BOX_INSTANCE_VAR] = "/nonexistent/the-real-box/.cairn"
        nested = scratch.home_env(Path("/nonexistent/a-second-scratch"))
        assert nested[scratch.BOX_INSTANCE_VAR] == "/nonexistent/the-real-box/.cairn",             "a scratch child's own scratch child must still name the real box"
    finally:
        if saved is None:
            os.environ.pop(scratch.BOX_INSTANCE_VAR, None)
        else:
            os.environ[scratch.BOX_INSTANCE_VAR] = saved


TEETH = [test_a_child_under_home_env_finds_its_home_in_the_scratch,
         test_an_explicit_userprofile_in_extra_still_wins,
         test_the_bypass_scan_names_the_hand_built_env_and_not_the_door,
         test_home_env_names_the_box_the_child_was_moved_off]

if __name__ == "__main__":
    failed = 0
    for tooth in TEETH:
        try:
            tooth()
            print(f"  green  {tooth.__name__}")
        except Exception as exc:  # noqa: BLE001 — a tooth's failure is its verdict
            failed += 1
            print(f"  RED    {tooth.__name__}: {type(exc).__name__}: {exc}")
    print(f"\n{len(TEETH) - failed}/{len(TEETH)} teeth green")
    sys.exit(1 if failed else 0)
