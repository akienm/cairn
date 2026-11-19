"""Proof for ticket f64b87bf0f67 — migrate keeps a trace's order, and a flat root left standing says so.

Measured 2026-11-16 on akiendelllinux: ticket 17d4d1899545 moved every learning_block trace under
its holder and shipped `migrate` for the old flat root, but the verb never ran on this box. The flat
root still held 16 files (~18,200 lines, all 351 historical `finding` events), trace_roots() does
not read it, and every reader counted from 2026-11-13 only. Two defects made that silent and risky:
migrate APPENDED the old lines after a holder's newer ones (readers return a file in order), and
nothing announced a flat root still standing.

Every write runs in a subprocess under a scratch HOME, so the live instance space is never touched
and a tooth reds on the code, not on the box.

    python3 cairn/machines/learning_block/proofs/test_migrate_keeps_order_and_a_flat_root_announces_itself.py
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]

PROVES = {"f64b87bf0f67": {
    "1": "test_migrate_writes_old_lines_first_then_the_holders_own",
    "2": "test_a_standing_flat_root_raises_one_trouble_naming_it",
    "3": "test_no_flat_root_raises_nothing",
}}

_FLAT = Path(".cairn/devices/learning_block/0/traces")
_CC = Path(".cairn/devices/cc/0/machines/learning_block/traces")
_RAISES = Path(".cairn/logs/learning_block/0")
_TROUBLE = "learning-block-flat-root-stands"


def _env(home: Path) -> dict:
    from cairn.tools.scratch.scratch import home_env  # CAIRN_BUS_* scrubbed, USERPROFILE moved (ticket a9c900180061)
    return {k: v for k, v in home_env(home, PYTHONPATH=str(_REPO_ROOT)).items() if k != "CAIRN_LB_TRACE_ROOT"}


def _run(home: Path, *argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *argv], capture_output=True, text=True,
                          env=_env(home), cwd=str(_REPO_ROOT), timeout=120)


def _line(i: int, block: str = "skill:intent") -> str:
    return json.dumps({"block": block, "consumer": "training", "data": {"n": i}, "event": "door_pass",
                       "id": f"{i:012x}", "when": f"2026-11-{i:02d}T00:00:00+00:00"}, sort_keys=True)


def _raises(home: Path) -> list[dict]:
    d = home / _RAISES
    out = [json.loads(p.read_text()) for p in sorted(d.glob("*.raise_trouble.json"))] if d.is_dir() else []
    return [r for r in out if r.get("pointer") == _TROUBLE]


_SURVEY_TWICE = ("from cairn.machines.learning_block import learning_block as lb\n"
                 "a = lb.trace_roots(); b = lb.trace_roots(); print(len(a), len(b))\n")


def test_migrate_writes_old_lines_first_then_the_holders_own():
    with tempfile.TemporaryDirectory() as d:
        home = Path(d)
        (home / _FLAT).mkdir(parents=True)
        (home / _CC).mkdir(parents=True)
        old = [_line(1), _line(2), _line(3)]
        new = [_line(3), _line(14), _line(15)]  # line 3 already copied once: never written twice
        (home / _FLAT / "skill__intent.jsonl").write_text("\n".join(old) + "\n")
        (home / _CC / "skill__intent.jsonl").write_text("\n".join(new) + "\n")
        r = _run(home, "-m", "cairn.machines.learning_block", "migrate")
        assert r.returncode == 0, f"migrate exited {r.returncode}: {(r.stdout + r.stderr)[-600:]}"
        got = (home / _CC / "skill__intent.jsonl").read_text().splitlines()
        want = [_line(1), _line(2), _line(3), _line(14), _line(15)]
        assert got == want, f"the holder's file is not old-then-new, each line once:\n{got}"
        assert "(2 new line(s))" in r.stdout, f"migrate miscounted what it moved: {r.stdout!r}"
        assert not (home / _FLAT / "skill__intent.jsonl").exists(), "the flat file was not removed"
        assert not list((home / _CC).glob("*.migrating")), "a partial rewrite was left behind"


def test_a_standing_flat_root_raises_one_trouble_naming_it():
    with tempfile.TemporaryDirectory() as d:
        home = Path(d)
        (home / _FLAT).mkdir(parents=True)
        (home / _FLAT / "skill__intent.jsonl").write_text("\n".join([_line(1), _line(2)]) + "\n\n")
        (home / _FLAT / "web_server.jsonl").write_text(_line(3, "web_server") + "\n")
        r = _run(home, "-c", _SURVEY_TWICE)
        assert r.returncode == 0, f"the survey failed: {(r.stdout + r.stderr)[-600:]}"
        got = _raises(home)
        assert len(got) == 1, f"two surveys in one process should raise once, raised {len(got)}"
        det = got[0]["values"]["detail"]
        assert det["root"] == str(home / _FLAT), f"the trouble names the wrong root: {det['root']}"
        assert det["lines"] == 3, f"the trouble counts {det['lines']} lines, not the 3 standing"
        assert sorted(det["files"]) == ["skill__intent.jsonl", "web_server.jsonl"], det["files"]
        assert "migrate" in got[0]["values"]["why"], "the why does not name the verb that clears it"


def test_no_flat_root_raises_nothing():
    with tempfile.TemporaryDirectory() as d:
        home = Path(d)
        (home / _CC).mkdir(parents=True)
        r = _run(home, "-c", _SURVEY_TWICE)
        assert r.returncode == 0, (r.stdout + r.stderr)[-600:]
        assert _raises(home) == [], "a box with no flat root raised the trouble"
        (home / _FLAT).mkdir(parents=True)  # an emptied flat root, as migrate leaves it
        r = _run(home, "-c", _SURVEY_TWICE)
        assert _raises(home) == [], "an empty flat root raised the trouble"
        (home / _FLAT / "skill__intent.jsonl").write_text(_line(1) + "\n")
        env_root = home / "override"
        env_root.mkdir()
        r = subprocess.run([sys.executable, "-c", _SURVEY_TWICE], capture_output=True, text=True,
                           env=dict(_env(home), CAIRN_LB_TRACE_ROOT=str(env_root)),
                           cwd=str(_REPO_ROOT), timeout=120)
        assert r.returncode == 0, (r.stdout + r.stderr)[-600:]
        assert _raises(home) == [], "a survey over the proofs' override root raised the box's trouble"


TEETH = [test_migrate_writes_old_lines_first_then_the_holders_own,
         test_a_standing_flat_root_raises_one_trouble_naming_it, test_no_flat_root_raises_nothing]


def main() -> int:
    failed = 0
    for t in TEETH:
        try:
            t()
            print(f"  green  {t.__name__}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"  RED    {t.__name__}: {type(e).__name__}: {e}")
    print(f"\n{len(TEETH) - failed}/{len(TEETH)} teeth green")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
