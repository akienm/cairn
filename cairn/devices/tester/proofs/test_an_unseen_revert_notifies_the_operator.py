"""An unseen revert completes the hollow run and tells the operator, once (ticket b5871526384a).

Akien's answer to open-ed0a56ce6357: a green the measurement cannot vouch for — here, a file
whose revert redded no declared tooth — "we let it complete AND notify me". So the hollow run
stops redding that file, the --seal run posts ONE notice (the file plus its diff) under the
tester's own instance address and seals the file as {"notified": <id>}, and the tester answers
`notices` and `notice-seen` on the bus. The hard reds stand: a file whose proof never ran is
still unreadable and red, and a run that measured nothing still reds.

Every tooth imports the tester's modules INSIDE its body, so a reverted or absent notices.py
reds teeth instead of breaking this file's import — which is what lets the hollow run read it.
"""
from __future__ import annotations

import functools
import importlib.util
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROVES = {"b5871526384a": {
    "1": "test_measure_carries_the_unseen_file_and_its_diff_and_stays_green",
    "2": "test_the_seal_posts_one_notice_and_seals_it_notified",
    "3": "test_a_run_without_seal_posts_nothing",
    "4": "test_the_notices_verbs_list_mark_and_rate",
    "5": "test_the_hard_reds_stand",
}}

_spec = importlib.util.spec_from_file_location(
    "tester_test_hollow", Path(__file__).resolve().parent / "test_hollow.py")
th = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(th)


def _notices_home(tmp: Path):
    from cairn.devices.tester import notices
    was = notices.HOME
    notices.HOME = tmp / "notices"
    return notices, was


def _diff(repo: Path, commit: str, f: str) -> str:
    return subprocess.run(["git", "-C", str(repo), "diff", commit, "HEAD", "--", f],
                          capture_output=True, text=True).stdout


def _run_cli(tmp: Path, argv: list[str], *, stub=None) -> tuple[int, dict, str]:
    """cli.main in-process against the fixture; the seal is captured, never written."""
    import contextlib
    import io
    from cairn.devices.tester import cli, hollow
    repo, commons = th._fixture(tmp)
    sealed: dict = {}

    def recorder(proof, ticket, reading, **kw):
        sealed.update(reading)
        return False

    saved = (hollow.measure, cli.REPO_ROOT, cli.record_hollow)
    hollow.measure = stub or functools.partial(hollow.measure, commons=commons,
                                               berths_root=th._berths_root(tmp))
    cli.REPO_ROOT, cli.record_hollow = repo, recorder
    out = io.StringIO()
    try:
        with contextlib.redirect_stdout(out):
            rc = cli.main(argv)
    finally:
        hollow.measure, cli.REPO_ROOT, cli.record_hollow = saved
    return rc, sealed, out.getvalue()


def test_measure_carries_the_unseen_file_and_its_diff_and_stays_green():
    from cairn.devices.tester.hollow import measure
    tmp = scratch_dir("cairn-unseenproof-")
    repo, commons = th._fixture(tmp)
    f = measure(th.FIXTURE, repo_root=repo, commons=commons,
                berths_root=th._berths_root(tmp), timeout=60)
    assert f["verdict"] == "green", f["reasons"]
    assert f["hollow"] == ["unchecked.py"], f["hollow"]
    assert not any("unchecked.py" in r for r in f["reasons"]), f["reasons"]
    want = _diff(repo, f["commit"], "unchecked.py")
    assert want and f["unseen"]["unchecked.py"] == want, f.get("unseen")


def test_the_seal_posts_one_notice_and_seals_it_notified():
    tmp = scratch_dir("cairn-unseenproof-")
    notices, was = _notices_home(tmp)
    try:
        rc, sealed, out = _run_cli(tmp, ["--hollow", th.FIXTURE, "--seal", "-q"])
        posted = notices.unseen()
        assert rc == 0, out
        assert len(posted) == 1, posted
        n = posted[0]
        assert n["file"] == "unchecked.py" and n["ticket"] == th.FIXTURE, n
        assert "after the build" in n["diff"], n["diff"]
        assert sealed == {"subject.py": ["test_value_is_two"],
                          "unchecked.py": {"notified": n["id"]}}, sealed
        rc2, _, _ = _run_cli(scratch_dir("cairn-unseenproof-"),
                             ["--hollow", th.FIXTURE, "--seal", "-q"])
        assert rc2 == 0 and len(notices.unseen()) == 1, notices.unseen()
    finally:
        notices.HOME = was


def test_a_run_without_seal_posts_nothing():
    tmp = scratch_dir("cairn-unseenproof-")
    notices, was = _notices_home(tmp)
    try:
        rc, sealed, out = _run_cli(tmp, ["--hollow", th.FIXTURE, "-q"])
        assert rc == 0, out
        assert notices.unseen() == [] and sealed == {}, (notices.unseen(), sealed)
        assert "unseen" in out and "unchecked.py" in out, out
    finally:
        notices.HOME = was


def test_the_notices_verbs_list_mark_and_rate():
    from cairn.devices.tester.device import TesterDevice
    tmp = scratch_dir("cairn-unseenproof-")
    notices, was = _notices_home(tmp)
    try:
        verbs = TesterDevice().declared_verbs()
        empty = verbs["notices"]({"body": {}})
        assert empty["unseen"] == [] and empty["rate"]["total"] == 0, empty
        nid = notices.post("abcdefabcdef", "x.py", "-a\n+b\n")
        got = verbs["notices"]({"body": {}})
        assert [n["id"] for n in got["unseen"]] == [nid], got
        assert set(got["rate"]) >= {"total", "first", "days", "per_day"}, got["rate"]
        assert got["rate"]["total"] == 1 and got["rate"]["days"] >= 1, got["rate"]
        assert verbs["notice-seen"]({"body": {"id": nid}}) == {"seen": nid}
        assert verbs["notices"]({"body": {}})["unseen"] == []
        assert verbs["notices"]({"body": {}})["rate"]["total"] == 1
        refused = verbs["notice-seen"]({"body": {"id": "n-000000000000"}})
        assert "n-000000000000" in refused.get("refused", ""), refused
    finally:
        notices.HOME = was


def test_the_hard_reds_stand():
    tmp = scratch_dir("cairn-unseenproof-")
    notices, was = _notices_home(tmp)
    try:
        def stub(ticket, **kw):
            return {"ticket": ticket, "commit": "0" * 40, "proofs": ["p.py"],
                    "measured": {"x.py": []}, "hollow": ["x.py"], "unran": {"x.py": ["p.py"]},
                    "unseen": {}, "skipped": {}, "verdict": "red",
                    "reasons": ["unreadable: x.py — its proof printed no teeth"],
                    "anchor_rule": "stub", "anchor_journal": None,
                    "anchor_first_build": None}
        rc, sealed, out = _run_cli(tmp, ["--hollow", th.FIXTURE, "--seal", "-q"], stub=stub)
        assert rc == 1, out
        assert sealed == {"x.py": {"unreadable": ["p.py"]}}, sealed
        assert notices.unseen() == [], notices.unseen()
    finally:
        notices.HOME = was
    th.test_a_run_that_could_not_be_measured_says_so_instead_of_passing()


def main() -> int:
    fails = 0
    for name in PROVES["b5871526384a"].values():
        try:
            globals()[name]()
            print(f"  ok   {name}")
        except Exception as exc:  # noqa: BLE001 — every tooth reports, none hides
            fails += 1
            print(f"  FAIL {name}: {type(exc).__name__}: {exc}")
    print("RED" if fails else "GREEN")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
