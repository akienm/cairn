"""Proof for ticket 546c97b24d58 — a crossing reaches a ticket whose intention lives in the commons.

Teeth a hollow build could not pass (Law 8), teeth 1-3 over a SCRATCH world the proof owns: a
commons at root/CairnCommons with tickets/, intentions-not-beside-code/_charter+why.json and a
copy of the live code-seam node class; a repo at root/cairn holding only comp/intention+why.json;
both handed to the artifact door (``artifact.set_diagnostic_roots``) and restored in ``finally``.

1. a ticket owned by intentions-not-beside-code/_charter+why.json crosses through cross() and
   the crossing lands in the commons dir's history.json and state.json, nowhere in the repo;
2. a ticket owned by comp/intention+why.json still journals beside it, and nothing lands in
   the commons charter's dir;
3. an owning_intention naming a file absent from both roots is refused, the refusal naming
   both paths it tried, and the ticket and both histories are byte-identical;
4. live, read-only: charter_dir over 6bc43453ca64's owning_intention resolves to
   CairnCommons/intentions-not-beside-code, and no live file under either root changes;
5. test_a_crossing_runs_through_one_command.py, run as a subprocess, exits 0.

THE SUBJECT IS BOUND AT CALL TIME. ``_cross()`` imports the build when a tooth asks, so a
worktree with cairn/tools/base/cross.py reverted reds every declared tooth by name instead of
failing at import.

Run bare:  PYTHONPATH=. python3 cairn/tools/base/proofs/test_a_crossing_reaches_a_commons_owned_ticket.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {
    "546c97b24d58": {
        "1": "test_a_commons_owned_ticket_journals_beside_its_commons_charter",
        "2": "test_a_cairn_owned_ticket_still_journals_beside_its_intention",
        "3": "test_an_owner_absent_from_both_roots_is_refused_naming_both",
        "4": "test_the_live_commons_owner_resolves_without_writing",
        "5": "test_the_one_command_crossing_proof_stays_green",
    },
}

FAILURES: list[str] = []
_LIVE_COMMONS = next((c for c in (REPO.parent / "CairnCommons", Path.home() / "dev" / "src" / "CairnCommons")
                      if (c / "node_classes" / "code-seam.json").is_file()), None)
TID = "abc123def456"
AT_PROVEME = "code-seam@v2: THINKME -> TICKETME -> BUILDME -> [PROVEME] -> PROVED"
COMMONS_OWNER = "intentions-not-beside-code/_charter+why.json"
CAIRN_OWNER = "comp/intention+why.json"


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def _cross():
    from cairn.tools.base import cross
    return cross


class World:
    """Both roots in scratch: a commons with a commons charter, a repo with one component charter."""

    def __init__(self, owning_intention: str) -> None:
        from cairn.tools.scratch.scratch import scratch_dir
        root = Path(scratch_dir("cross-commons-owner-fixture-"))
        self.commons = root / "CairnCommons"
        self.tickets = self.commons / "tickets"
        self.tickets.mkdir(parents=True)
        (self.tickets / "_charter+why.json").write_text(json.dumps(
            {"plan_fields": ["id", "owning_intention", "workflow_and_state"]}) + "\n")
        self.cdir = self.commons / "intentions-not-beside-code"
        self.cdir.mkdir()
        (self.cdir / "_charter+why.json").write_text("{}", encoding="utf-8")
        self.repo = root / "cairn"
        self.comp = self.repo / "comp"
        self.comp.mkdir(parents=True)
        (self.comp / "intention+why.json").write_text("{}", encoding="utf-8")
        assert _LIVE_COMMONS is not None, "no CairnCommons/node_classes/code-seam.json beside the repo or under $HOME"
        self.node_classes = self.commons / "node_classes"
        self.node_classes.mkdir()
        (self.node_classes / "code-seam.json").write_bytes(
            (_LIVE_COMMONS / "node_classes" / "code-seam.json").read_bytes())
        self.ticket = self.tickets / f"{TID}-a-fixture-ticket.json"
        self.ticket.write_text(json.dumps({
            "id": TID, "owning_intention": owning_intention,
            "workflow_and_state": AT_PROVEME}, indent=2) + "\n", encoding="utf-8")

    def journals(self, d: Path) -> list:
        h = d / "history.json"
        return json.loads(h.read_text(encoding="utf-8")) if h.exists() else []

    def snapshot(self) -> tuple:
        return tuple(p.read_bytes() if p.exists() else None
                     for p in (self.ticket, self.comp / "history.json", self.comp / "state.json",
                               self.cdir / "history.json", self.cdir / "state.json"))

    def cross(self, A, target: str):
        """cross() over this world; emit's own gates read transitions' store, so it points here too."""
        from cairn.tools.base import transitions as T
        saved = (T._TICKETS, T._REPO_ROOT, T._NODE_CLASSES)
        A.set_diagnostic_roots({"CairnCommons": self.commons, "cairn": self.repo})
        T._TICKETS, T._REPO_ROOT, T._NODE_CLASSES = self.tickets, self.repo, self.node_classes
        try:
            return _cross().cross(TID, target, actor="proof", why=f"proof: {target}",
                                  tickets_dir=self.tickets, repo_root=self.repo,
                                  node_class_root=self.node_classes, commons_root=self.commons), None
        except ImportError:
            raise
        except Exception as exc:  # noqa: BLE001 — a refusal is the measured outcome
            return None, exc
        finally:
            T._TICKETS, T._REPO_ROOT, T._NODE_CLASSES = saved
            A.set_diagnostic_roots(None)


# --------------------------------------------------------------------------- the teeth


def test_a_commons_owned_ticket_journals_beside_its_commons_charter(A) -> None:
    w = World(COMMONS_OWNER)
    new, exc = w.cross(A, "BUILDME")
    cursor = json.loads(w.ticket.read_text(encoding="utf-8")).get("workflow_and_state")
    ch, rh = w.journals(w.cdir), w.journals(w.comp)
    ok = (exc is None and isinstance(new, str) and "[BUILDME" in new and cursor == new
          and len(ch) == 1 and ch[0].get("ticket") == TID and (w.cdir / "state.json").exists()
          and rh == [] and not (w.comp / "state.json").exists())
    check(PROVES["546c97b24d58"]["1"], ok,
          f"exc={exc!r} new={new!r} commons history={len(ch)} repo history={len(rh)}")


def test_a_cairn_owned_ticket_still_journals_beside_its_intention(A) -> None:
    w = World(CAIRN_OWNER)
    new, exc = w.cross(A, "BUILDME")
    rh, ch = w.journals(w.comp), w.journals(w.cdir)
    ok = (exc is None and isinstance(new, str) and "[BUILDME" in new
          and len(rh) == 1 and rh[0].get("ticket") == TID and ch == []
          and not (w.cdir / "state.json").exists())
    check(PROVES["546c97b24d58"]["2"], ok,
          f"exc={exc!r} repo history={len(rh)} commons history={len(ch)}")


def test_an_owner_absent_from_both_roots_is_refused_naming_both(A) -> None:
    owning = "nowhere/_charter+why.json"
    w = World(owning)
    snap = w.snapshot()
    new, exc = w.cross(A, "BUILDME")
    msg = str(exc)
    ok = (exc is not None and new is None and w.snapshot() == snap and "names no charter" in msg
          and str(w.repo / owning) in msg and str(w.commons / owning) in msg)
    check(PROVES["546c97b24d58"]["3"], ok, f"exc={exc!r} unchanged={w.snapshot() == snap}")


def _tree_bytes(d: Path) -> dict:
    return {str(p): p.stat().st_mtime_ns for p in d.rglob("*") if p.is_file()}


def test_the_live_commons_owner_resolves_without_writing(A) -> None:
    from cairn.tools.base import transitions as T
    live = Path(T._TICKETS).parent
    hits = [p for p in Path(T._TICKETS).glob("6bc43453ca64-*.json") if not p.name.endswith(".log.jsonl")]
    owning = json.loads(hits[0].read_text(encoding="utf-8"))["owning_intention"] if hits else ""
    watched = live / "intentions-not-beside-code"
    before = _tree_bytes(watched)
    try:
        got, exc = _cross().charter_dir(owning, Path(T._REPO_ROOT), live), None
    except ImportError:
        raise
    except Exception as e:  # noqa: BLE001
        got, exc = None, e
    ok = (exc is None and got == watched and _tree_bytes(watched) == before)
    check(PROVES["546c97b24d58"]["4"], ok, f"owning={owning!r} got={got} exc={exc!r}")


def test_the_one_command_crossing_proof_stays_green(A) -> None:
    proof = REPO / "cairn/tools/base/proofs/test_a_crossing_runs_through_one_command.py"
    r = subprocess.run([sys.executable, str(proof)], cwd=str(REPO), capture_output=True, text=True,
                       timeout=600, env={**__import__("os").environ, "PYTHONPATH": str(REPO)})
    check(PROVES["546c97b24d58"]["5"], r.returncode == 0,
          f"rc={r.returncode} {(r.stdout + r.stderr).strip().splitlines()[-1:] }")


def main() -> int:
    from cairn.tools.artifact import artifact as A
    live = A.journal_path(A.roots()["CairnCommons"])
    live_before = live.read_bytes() if live.exists() else b""
    for tooth, n in ((test_a_commons_owned_ticket_journals_beside_its_commons_charter, "1"),
                     (test_a_cairn_owned_ticket_still_journals_beside_its_intention, "2"),
                     (test_an_owner_absent_from_both_roots_is_refused_naming_both, "3"),
                     (test_the_live_commons_owner_resolves_without_writing, "4"),
                     (test_the_one_command_crossing_proof_stays_green, "5")):
        try:
            tooth(A)
        except Exception as exc:  # noqa: BLE001 — a subject whose build was taken away
            check(PROVES["546c97b24d58"][n], False, f"aborted: {type(exc).__name__}: {exc}")
    live_after = live.read_bytes() if live.exists() else b""
    check("the live journal never moved", live_before == live_after)
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    for f in FAILURES:
        print(f"  - {f}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
