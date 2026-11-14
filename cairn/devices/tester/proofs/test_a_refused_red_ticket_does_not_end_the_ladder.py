"""Proof (the ladder ticket): a refused red ticket is loud, leaves nothing staged, raises a trouble, and does not end the ladder.

``bin/cairn test --reseal <targets>`` died at the first red: ``red_tickets.ticket_what_is_new`` casts and commits the red's auto-ticket,
the commit was refused (a commons hook, staged files, an unreadable object), the refusal propagated out of ``run_proof`` through
``reseal_all`` and killed the batch, and the cast's files stayed staged in the house commons for the next writer to trip over.

Teeth, one per falsifier clause, none of which needs a bus or a database:
  (1) a ladder over [red, green] reseals the green and RECORDS the red (the red proof's run raises RedTicketRefused, as run_proof does
      after it has persisted the red);
  (2) a refused cast-commit (a pre-commit hook in a scratch commons that refuses) is loud AND unstages exactly what it staged;
  (3) a refused cast raises a trouble (``red_tickets:refused:<key>``), never only an exception.

    python <this file>
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from cairn.devices.tester import red_tickets, reseal as door  # noqa: E402
from cairn.devices.tester.device import GREEN, RED  # noqa: E402
from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402
from cairn.tools.validation_store.validation_store import source_fingerprint  # noqa: E402

PROVES = {
    "31b76dfeb864": {
        "1": "a_ladder_over_a_red_and_a_green_reseals_the_green_and_records_the_red",
        "2": "a_refused_cast_commit_is_loud_and_unstages_exactly_what_it_staged",
        "3": "a_refused_cast_raises_a_trouble_never_only_an_exception",
    },
}


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True,
                          env={**__import__("os").environ, "GIT_AUTHOR_NAME": "p", "GIT_AUTHOR_EMAIL": "p@p",
                                "GIT_COMMITTER_NAME": "p", "GIT_COMMITTER_EMAIL": "p@p"}).stdout.strip()


def _record(proof: Path, verdict: str) -> dict:
    return {"claim": f"{proof.name} passes", "caller": "ladder fixture", "date": datetime.now().isoformat(timespec="seconds"),
            "method": "fixture", "verdict": verdict,
            "evidence": {"source_fingerprint": source_fingerprint(str(proof)), "returncode": 0 if verdict == GREEN else 1},
            "falsifier": "the proof exits non-zero", "horizon": "until the proof changes"}


class _FakeTester:
    """run_proof answers green, or raises RedTicketRefused for a name carrying 'red', as the real one does after persisting the red."""

    def __init__(self):
        self.ran = []

    def run_proof(self, proof_path, *, sink, caller=None, timeout=120, isolation="none", scratch_sweep=None):
        self.ran.append(Path(proof_path).name)
        if "red" in Path(proof_path).name:
            raise red_tickets.RedTicketRefused("k-red", "commit", ["git commit in the commons: refused by a hook"])
        return _record(Path(proof_path), GREEN)


class _Raiser:
    def __init__(self):
        self.raised, self.cleared = [], []

    def raise_trouble(self, identity, *, why, detail=None):
        self.raised.append((identity, why, detail))

    def clear_trouble(self, identity, *, by, what_changed):
        self.cleared.append(identity)


def a_ladder_over_a_red_and_a_green_reseals_the_green_and_records_the_red() -> None:
    tmp = Path(str(scratch_dir("ladder_red_green_")))
    try:
        proofs = []
        for name in ("test_red_one.py", "test_green_two.py"):
            p = tmp / "widget" / "proofs" / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("assert True\n", encoding="utf-8", newline="\n")
            proofs.append(p)
        fake = _FakeTester()
        out = door.reseal_all(proofs, tester=fake, raiser=_Raiser())          # must not raise
        assert fake.ran == ["test_red_one.py", "test_green_two.py"], f"the ladder stopped at the red: ran {fake.ran}"
        by = {Path(r["proof"]).name: r for r in out["results"]}
        assert by["test_green_two.py"]["outcome"] in ("resealed", "sealed"), f"the green after the red was not resealed: {by}"
        red = by.get("test_red_one.py")
        assert red and red["outcome"] == "red" and red.get("ticketed") is False, f"the red was not recorded as red-and-unticketed: {by}"
        assert out["counts"].get("red") == 1 and len(out["red"]) == 1, out["counts"]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def a_refused_cast_commit_is_loud_and_unstages_exactly_what_it_staged() -> None:
    tmp = Path(str(scratch_dir("ladder_commit_refused_")))
    try:
        commons = tmp / "CairnCommons"
        (commons / "tickets").mkdir(parents=True)
        _git(commons, "init", "-q")
        (commons / "README.md").write_text("commons\n", encoding="utf-8", newline="\n")
        _git(commons, "add", "README.md")
        _git(commons, "-c", "commit.gpgsign=false", "commit", "-q", "-m", "init")
        hook = commons / ".git" / "hooks" / "pre-commit"
        hook.write_text("#!/bin/sh\necho 'commit names its paths' >&2\nexit 1\n", encoding="utf-8", newline="\n")
        hook.chmod(0o755)
        plan = commons / "tickets" / "abc123abc123-a-red.json"
        plan.write_text("{}\n", encoding="utf-8", newline="\n")
        state, log = plan.with_name("abc123abc123-a-red.state.json"), plan.with_name("abc123abc123-a-red.log.jsonl")
        state.write_text("{}\n", encoding="utf-8", newline="\n")
        log.write_text("{}\n", encoding="utf-8", newline="\n")
        berth = commons / "berths" / "sorted" / "sorted-1.json"
        berth.parent.mkdir(parents=True)
        berth.write_text("{}\n", encoding="utf-8", newline="\n")
        try:
            red_tickets._commit([(plan, berth)], commons, ["k-red"])
        except red_tickets.RedTicketRefused as e:
            assert "commit names its paths" in str(e), f"the refusal does not carry the hook's words: {e}"
            assert "unstaged exactly what was staged" in str(e), f"the refusal does not say it unstaged: {e}"
        else:
            raise AssertionError("a refused commit did not raise")
        staged = _git(commons, "diff", "--cached", "--name-only")
        assert staged == "", f"the refused commit left the commons index holding: {staged!r}"
        assert plan.is_file() and state.is_file(), "the cast's own files must stay on disk"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def a_refused_cast_raises_a_trouble_never_only_an_exception() -> None:
    raiser = _Raiser()
    real = {n: getattr(red_tickets, n) for n in ("red_keys", "carried", "_commons_top", "_staged", "_cast", "_repo", "_raise_refused")}
    item = {"keys": ["k-red"], "path": "cairn/widget/proofs/test_red_one.py", "kind": "red", "record": "r"}
    seen = []
    try:
        red_tickets.red_keys = lambda results, repo: [item]
        red_tickets.carried = lambda repo, tickets_dir: (set(), set())
        red_tickets._commons_top = lambda tickets_dir: Path("/nowhere/CairnCommons")
        red_tickets._staged = lambda top: []
        red_tickets._repo = lambda repo_root=None: Path("/nowhere/repo")

        def refused(*a, **k):
            raise red_tickets.RedTicketRefused("k-red", "cast", ["the cast door refused"])
        red_tickets._cast = refused
        red_tickets._raise_refused = lambda err, items, top, run_record: seen.append((err.door, [i["keys"][0] for i in items]))
        try:
            red_tickets.ticket_what_is_new([{}])
        except red_tickets.RedTicketRefused:
            pass
        else:
            raise AssertionError("a refused cast did not raise")
    finally:
        for n, f in real.items():
            setattr(red_tickets, n, f)
    assert seen == [("cast", ["k-red"])], f"a refused cast raised no trouble: {seen}"
    # and the trouble itself carries the door, the lacks and the red's key
    err = red_tickets.RedTicketRefused("k-red", "commit", ["refused"])
    import cairn.tools.base.diagnostic as diag
    saved = diag.ModuleRaiser
    diag.ModuleRaiser = lambda *a, **k: raiser
    try:
        red_tickets._raise_refused(err, [item], Path("/nowhere/CairnCommons"), "rec")
    finally:
        diag.ModuleRaiser = saved
    assert [i for i, _, _ in raiser.raised] == ["red_tickets:refused:k-red"], raiser.raised
    detail = raiser.raised[0][2]
    assert detail["door"] == "commit" and detail["lacks"] == ["refused"], detail


TEETH = [a_ladder_over_a_red_and_a_green_reseals_the_green_and_records_the_red,
         a_refused_cast_commit_is_loud_and_unstages_exactly_what_it_staged,
         a_refused_cast_raises_a_trouble_never_only_an_exception]


def main() -> int:
    failed = 0
    for t in TEETH:
        try:
            t()
            print(f"  PASS  {t.__name__}")
        except BaseException as e:  # noqa: BLE001
            failed += 1
            print(f"  FAIL  {t.__name__}: {type(e).__name__}: {str(e)[:400]}")
    print(f"\n{len(TEETH) - failed}/{len(TEETH)} teeth green")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
