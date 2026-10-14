"""A verdict answers the build it was written after (ticket 6ebec06794ac).

PROVES: falsifier clauses (1) a verdict written before the ticket's latest forward BUILDME
crossing T is refused at the PROVED gate, naming the verdict's time and T; (2) one written at
or after T crosses; (3) with a stale and a fresh verdict, the fresh one is read; (4) with no
BUILDME crossing, freshness is bounded by the latest build commit's time, and with neither the
refusal names both; (5) the freshness read runs no instrument and reaches no tree; (6) live:
6890cf7e4053's 2026-09-02 verdict, against its 2026-10-13 BUILDME, is refused.

Teeth 1-5 stand a fixture world: chart berths in a tempdir (``berths_root``) and a crossing
journal behind ``inspector._crossing_roots``. Tooth 6 reads the live journals and the live
verdict berth, and asserts invariants (refused; the BUILDME it names postdates the verdict),
never a snapshot of which BUILDME stands.

A hollow build could not pass: without the predicate the stale verdict in tooth 1 answers its
chart completely and the gate reads green, and tooth 6 reads green for the verdict that let
6890cf7e4053 cross on a different build.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

PROVES = {
    "6ebec06794ac": {
        "1": "test_a_stale_verdict_is_refused_naming_both_times",
        "2": "test_a_fresh_verdict_crosses",
        "3": "test_of_two_verdicts_the_fresh_one_is_read",
        "4": "test_build_commits_bound_freshness_when_no_buildme",
        "5": "test_the_read_runs_no_instrument_and_reaches_no_tree",
        "6": "test_live_6890_old_verdict_is_refused",
    }
}

T = "2026-10-01T12:00:00"
LIVE_6890 = "/home/akien/.cairn/devices/chart/0/packets/verdict-20260902T053326-61dcf9791245.json"

_ANSWER = {
    "verdicts": [{"claim": "c1", "instrument": "cmd", "outcome": "pass",
                  "evidence": "seen: exit 0 twice",
                  "discriminating_observation": "reverted the fix; the instrument exits 1"}],
    "dispositions": [{"piece": "p1", "expect": "e1", "disposition": "confirmed",
                      "by": "the run observed"}],
}


def _world(d: Path, verdict_stamps: list[str], buildme_at: str | None = T):
    """Chart berths claiming 'widget' with one verdict per stamp, and a crossing journal
    holding (or not) a forward BUILDME at ``buildme_at``."""
    packets = d / "berths" / "0" / "packets"
    packets.mkdir(parents=True)
    hyp = packets / "hypothesize-20260901T000000-feed.json"
    hyp.write_text(json.dumps({"hypotheses": [
        {"piece": "p1", "expect": "e1", "falsifier": "f", "instrument": "i"}]}))
    val = packets / "validate-20260901T000001-feed.json"
    val.write_text(json.dumps({"ticket": "widget", "hypothesize_ref": str(hyp),
                               "criteria": [{"claim": "c1", "instrument": "cmd", "covers": ["p1"]}]}))
    paths = []
    for i, stamp in enumerate(verdict_stamps):
        p = packets / f"verdict-{stamp}-{i:04x}feed.json"
        p.write_text(json.dumps({"ticket": "widget", "validate_ref": str(val), **_ANSWER}))
        paths.append(p)
    journal = d / "crossings"
    journal.mkdir()
    entries = [] if buildme_at is None else [
        {"ticket": "widget", "at": buildme_at, "from": "TICKETME", "to": "BUILDME",
         "direction": "forward", "by": "fixture"}]
    (journal / "history.json").write_text(json.dumps(entries))
    return d / "berths", {"repo": journal, "commons": journal}, paths


def _gate(berths: Path, roots: dict) -> list[dict]:
    import cairn.machines.build_inspector.inspector as insp
    saved = insp._crossing_roots
    insp._crossing_roots = lambda: roots
    try:
        return insp.proved_answers_the_chart("widget", berths_root=berths)
    finally:
        insp._crossing_roots = saved


def test_a_stale_verdict_is_refused_naming_both_times():
    with tempfile.TemporaryDirectory() as d:
        berths, roots, _ = _world(Path(d), ["20261001T115959"])
        f = _gate(berths, roots)
        assert len(f) == 1, f"a stale verdict is refused, once: {f}"
        about = f[0]["about"]
        assert "predates the build" in about, about
        assert "2026-10-01T11:59:59" in about and "2026-10-01T12:00:00" in about, \
            f"the refusal names the verdict's time and T: {about}"
    print("ok test_a_stale_verdict_is_refused_naming_both_times")


def test_a_fresh_verdict_crosses():
    # at T exactly and after T (the wrong-intent signal: a verdict written between hollow
    # seal and PROVED is after BUILDME and must cross)
    for stamp in ("20261001T120000", "20261014T093000"):
        with tempfile.TemporaryDirectory() as d:
            berths, roots, _ = _world(Path(d), [stamp])
            assert _gate(berths, roots) == [], f"a verdict at {stamp} answers the build at {T}"
    print("ok test_a_fresh_verdict_crosses")


def test_of_two_verdicts_the_fresh_one_is_read():
    with tempfile.TemporaryDirectory() as d:
        berths, roots, (stale, fresh) = _world(Path(d), ["20260902T053326", "20261002T080000"])
        assert _gate(berths, roots) == [], "the fresh verdict stands"
        fresh.unlink()
        f = _gate(berths, roots)
        assert f and stale.name in f[0]["about"], f"with the fresh one gone the stale one reds: {f}"
    print("ok test_of_two_verdicts_the_fresh_one_is_read")


def _git(repo: Path, *args, env=None):
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True,
                   env={**os.environ, **(env or {})})


def _fresh(ticket, verdict, **kw):
    """The gate's own composition: the inspector gathers when the build began, and the
    pure predicate in verdict_contract judges the verdict against it."""
    from cairn.machines.build_inspector.inspector import build_started
    from cairn.tools.chain.verdict_contract import predates_the_build
    buildme_at, commit_times = build_started(ticket, **kw)
    return predates_the_build(ticket, verdict, buildme_at=buildme_at, commit_times=commit_times)


def test_build_commits_bound_freshness_when_no_buildme():
    with tempfile.TemporaryDirectory() as d:
        base = Path(d)
        commons = base / "commons"
        tickets = commons / "tickets"
        tickets.mkdir(parents=True)
        _git(commons, "init", "-q")
        _git(commons, "config", "user.email", "fixture@cairn")
        _git(commons, "config", "user.name", "fixture")
        (commons / "stone").write_text("built\n")
        _git(commons, "add", "-A")
        _git(commons, "commit", "-q", "-m", "the build",
             env={"GIT_COMMITTER_DATE": T, "GIT_AUTHOR_DATE": T})
        sha = subprocess.run(["git", "-C", str(commons), "rev-parse", "HEAD"],
                             capture_output=True, text=True, check=True).stdout.strip()
        _, roots, _ = _world(base / "w", [], buildme_at=None)
        (tickets / "widget.json").write_text(json.dumps({"build_commits": [sha]}))
        kw = dict(roots=roots, root=str(commons), tickets_dir=str(tickets))
        stale = _fresh("widget", "/x/verdict-20261001T115959-aa.json", **kw)
        assert len(stale) == 1 and "latest build commit" in stale[0] \
            and "2026-10-01T12:00:00" in stale[0] and "2026-10-01T11:59:59" in stale[0], stale
        assert _fresh("widget", "/x/verdict-20261001T120001-aa.json", **kw) == []
        # neither a BUILDME nor a readable build commit: refused, naming both
        (tickets / "widget.json").write_text(json.dumps({}))
        none = _fresh("widget", "/x/verdict-20261001T120001-aa.json", **kw)
        assert len(none) == 1 and "no forward BUILDME crossing" in none[0] \
            and "no build_commits" in none[0], none
        # and a BUILDME, where one stands, outranks the build commits
        (tickets / "widget.json").write_text(json.dumps({"build_commits": [sha]}))
        _, roots2, _ = _world(base / "w2", [], buildme_at="2026-10-05T00:00:00")
        kw2 = dict(kw, roots=roots2)
        late = _fresh("widget", "/x/verdict-20261003T000000-aa.json", **kw2)
        assert late and "BUILDME" in late[0], late
    print("ok test_build_commits_bound_freshness_when_no_buildme")


_PROBE = r"""
import json, subprocess, sys
from pathlib import Path
calls = []
_real = subprocess.run
def spy(argv, *a, **k):
    calls.append(list(argv))
    return _real(argv, *a, **k)
subprocess.run = spy
import cairn.machines.build_inspector.inspector as insp
berths, journal = Path(sys.argv[1]), Path(sys.argv[2])
insp._crossing_roots = lambda: {"repo": journal, "commons": journal}
f = insp.proved_answers_the_chart("widget", berths_root=berths)
reached = sorted(m for m in sys.modules if m.startswith((
    "cairn.tools.tree", "cairn.devices.db_domain", "cairn.devices.librarian",
    "cairn.devices.inference_domain", "psycopg", "requests", "httpx")))
print(json.dumps({"findings": f, "calls": calls, "reached": reached}))
"""


def test_the_read_runs_no_instrument_and_reaches_no_tree():
    with tempfile.TemporaryDirectory() as d:
        berths, roots, _ = _world(Path(d), ["20261001T115959"])
        out = subprocess.run([sys.executable, "-c", _PROBE, str(berths), str(roots["repo"])],
                             capture_output=True, text=True, cwd=str(ROOT),
                             env={**os.environ, "PYTHONPATH": str(ROOT)}, timeout=120)
        assert out.returncode == 0, out.stderr
        got = json.loads(out.stdout.strip().splitlines()[-1])
        assert got["findings"] and "predates the build" in got["findings"][0]["about"], got
        assert got["calls"] == [], f"the freshness read runs nothing when a BUILDME stands: {got['calls']}"
        assert got["reached"] == [], f"the gate reached tree/db/inference machinery: {got['reached']}"
    print("ok test_the_read_runs_no_instrument_and_reaches_no_tree")


def test_live_6890_old_verdict_is_refused():
    import time
    from cairn.tools.base import crossings
    assert Path(LIVE_6890).is_file(), f"the live 6890 verdict is gone: {LIVE_6890}"
    entry = crossings.buildme_crossing("6890cf7e4053")
    assert entry is not None, "6890cf7e4053 has no forward BUILDME crossing journaled"
    assert entry["at"] > "2026-09-02T05:33:26", entry
    f = _fresh("6890cf7e4053", LIVE_6890)
    assert len(f) == 1 and "predates the build" in f[0], f
    assert "2026-09-02T05:33:26" in f[0], f"names the verdict's time: {f[0]}"
    assert time.strftime("%Y-%m-%dT%H:%M:%S",
                         time.strptime(entry["at"][:19], "%Y-%m-%dT%H:%M:%S")) in f[0], \
        f"names the BUILDME time {entry['at']}: {f[0]}"
    print("ok test_live_6890_old_verdict_is_refused")


if __name__ == "__main__":
    # The house runner: every tooth runs and prints PASS or FAIL by name, so a hollow reading
    # that takes the predicate away reads each tooth failing rather than one crash.
    rc = 0
    for t in (test_a_stale_verdict_is_refused_naming_both_times, test_a_fresh_verdict_crosses,
              test_of_two_verdicts_the_fresh_one_is_read,
              test_build_commits_bound_freshness_when_no_buildme,
              test_the_read_runs_no_instrument_and_reaches_no_tree,
              test_live_6890_old_verdict_is_refused):
        try:
            t()
            print(f"  PASS  {t.__name__}")
        except Exception as exc:  # noqa: BLE001
            rc = 1
            print(f"  FAIL  {t.__name__}: {type(exc).__name__}: {exc}")
    print("test_a_verdict_answers_the_build_it_was_written_after: green" if rc == 0
          else "test_a_verdict_answers_the_build_it_was_written_after: RED")
    sys.exit(rc)
