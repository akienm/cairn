"""Each test run tickets every new red and orphaned file it finds (ticket 207c4074b3d5).

Outline 9.4.2.3.7.5, Akien 2026-11-13: "every test failure, every orphaned file, HAS TO BE FIXED
... reds don't get lost", "so each run writes any new bugs". The one entry point is
``ticket_what_is_new(results, scan_orphans=...)``: the tester's run_proof calls it on every red
(D5), and a whole-tree run (the tier verbs, 810fb2fc4a15 / cd40ac53f08a / 346c75c2f8b7) calls it
once with ``scan_orphans=True``. The adjudication ticket (aa2d42b15886) adds its call here.

KEYS (D1). A red is ``red:<proof repo-rel path>::<tooth>`` (``*`` when the run names no tooth);
an orphan is ``orphan:<repo-rel path>``. The key a ticket CARRIES is its ``fixes`` entry, and
the store's charter shapes ``fixes`` as paths that resolve to files (ticket 5defc13bfebe, read
by reseal's rung 4 and codemother's fixit rule), so each key also names the one file a ticket
fixes: the proof for a red, the orphaned file for (b), the orphaned seal for (a). One ticket
per proof, not per tooth: a second tooth reding on a proof an open ticket already fixes is
the same repair, and the keys ride the ticket's ``measured`` so none is lost.

ORPHANS (D2), CC's reading of 9.4.2.3.7.5, measured from ``git ls-files`` so the tester reaches
into no other component (RULE 1):
  (a) ``<x>/validations/test_<stem>.json`` whose ``<x>/proofs/test_<stem>.py`` is gone;
  (b) a tracked file under cairn/ or skills/ with no intention+why.json in its directory or any
      parent below the repo root. A package ``__init__.py`` is import plumbing, not a file
      anything owns (measured 2026-11-13 at 06a1e8755: 2236 tracked files, 5 such, all
      ``__init__.py`` at the namespace roots; 1 orphaned seal).

DEDUP (D3). A key is carried by a ticket not at a terminal state that lists its file in
``fixes``, or, for a red, names the proof in ``bounds.in``.

CAST (D4). Fire /sorted through skills/sorted/door.py, then cast_ticket. Either door's refusal
raises ``RedTicketRefused`` naming it (Law 7): never swallowed, and a ticket the cast door
refused never lands (cast_ticket writes nothing on a refusal).
"""
from __future__ import annotations

import json
import subprocess
import uuid
from datetime import date
from pathlib import Path

from cairn.tools.base.diagnostic import DiagnosticBase

_REPO = Path(__file__).resolve().parents[3]
CHARTER = "intention+why.json"
WORKFLOW = "code-seam@v2: THINKME -> [TICKETME:waiting] -> BUILDME -> PROVEME -> PROVED"
FALLBACK_OWNER = "cairn/devices/tester/intention+why.json"
_TREES = ("cairn", "skills")

# Where a cast lands. None is each door's own live default; a proof points them at scratch.
ROOTS: dict = {"repo": None, "tickets": None, "berths": None, "trace": None, "commons": None,
               "raiser": None}   # "raiser": the trouble raiser's three-root world (None: live)


class RedTicketRefused(DiagnosticBase, RuntimeError):
    """A door refused the ticket for ``key``; ``lacks`` is what it named."""

    def __init__(self, key: str, door: str, lacks):
        self.key, self.door, self.lacks = key, door, list(lacks or [])
        super().__init__(f"red_tickets: the {door} door refused the ticket for {key}: {self.lacks}")


class StoreUnreachable(RedTicketRefused):
    """The ticket store is in no git tree, so no cast can commit in the same act (D7). A run
    whose checkout has no commons beside it (a hollow or build worktree) meets this; the run
    that measured the red goes on, and the red stays in its own record (FIXME 1)."""


def _repo(repo_root=None) -> Path:
    return Path(repo_root or ROOTS["repo"] or _REPO).resolve()


def _rel(path, repo: Path) -> str | None:
    """``path`` repo-relative in posix spelling, or None when it lies outside the repo (a
    scratch or hollow-worktree proof is never ticketed)."""
    try:
        return Path(path).resolve().relative_to(repo).as_posix()
    except (ValueError, OSError):
        return None


def _is_red(r: dict) -> bool:
    return str(r.get("verdict") or r.get("outcome") or "").lower() == "red"


def red_keys(results, repo: Path) -> list[dict]:
    """One entry per red proof inside ``repo``. Each result names its ``proof``: reseal's
    results do ({"proof", "outcome"}), and run_proof hands its record in with the path added."""
    out: dict[str, dict] = {}
    for r in results or []:
        if not isinstance(r, dict) or not _is_red(r):
            continue
        ev = r.get("evidence") if isinstance(r.get("evidence"), dict) else {}
        proof = r.get("proof")
        rel = _rel(repo / proof if proof and not Path(proof).is_absolute() else proof, repo) \
            if proof else None
        if rel is None or not _is_proof(rel):
            continue
        teeth = [t for t in (ev.get("teeth_red") or r.get("teeth_red") or []) if t] or ["*"]
        e = out.setdefault(rel, {"kind": "red", "path": rel, "keys": [],
                                 "record": r.get("record") or _record_of(repo / rel)})
        e["keys"] += [f"red:{rel}::{t}" for t in teeth if f"red:{rel}::{t}" not in e["keys"]]
    return list(out.values())


def _is_proof(rel: str) -> bool:
    """A proof is ``<component>/proofs/test_<name>.py``: every tracked test_*.py stands there
    (measured 2026-11-13, 0 elsewhere). A fixture another proof runs to see a red
    (proofs/fixtures/red_proof.py) is not a red to fix; the first bounded run cast one."""
    p = Path(rel)
    return p.parent.name == "proofs" and p.name.startswith("test_") and p.suffix == ".py"


def _record_of(proof: Path) -> str:
    """The run record a red cites: the proof's seal when one stands, else the proof itself."""
    seal = proof.parent.parent / "validations" / f"{proof.stem}.json"
    return (seal if seal.is_file() else proof).as_posix()


def orphan_keys(repo: Path) -> list[dict]:
    """The two kinds of orphan (D2) among the files git tracks under cairn/ and skills/."""
    done = subprocess.run(["git", "-C", str(repo), "ls-files", "--", *_TREES],
                          capture_output=True, text=True, check=True)
    files = [f for f in done.stdout.splitlines() if f.strip()]
    owned: dict[str, bool] = {}

    def has_charter(d: str) -> bool:
        if d not in owned:
            owned[d] = (repo / d / CHARTER).is_file() or (
                d not in ("", ".") and has_charter(Path(d).parent.as_posix()))
        return owned[d]

    out = []
    for f in files:
        p = Path(f)
        if p.parent.name == "validations" and p.suffix == ".json" and p.name.startswith("test_"):
            if not (repo / p.parent.parent / "proofs" / f"{p.stem}.py").is_file():
                out.append({"kind": "orphan", "path": f, "keys": [f"orphan:{f}"],
                            "why": f"a seal whose proof {p.parent.parent.as_posix()}/proofs/"
                                   f"{p.stem}.py is gone"})
                continue
        if p.name != "__init__.py" and not has_charter(p.parent.as_posix()):
            out.append({"kind": "orphan", "path": f, "keys": [f"orphan:{f}"],
                        "why": f"no {CHARTER} in its directory or any parent below the repo root"})
    return out


def carried(repo: Path, tickets_dir=None) -> tuple[set[str], set[str]]:
    """(files open tickets fix, files open tickets bound in) — tickets at a terminal state
    carry nothing."""
    from cairn.tools.base import ticket_file as tf
    from cairn.tools.base.workflow_grammar import is_terminal, parse_workflow
    fixes, bounds = set(), set()
    for plan in tf.plans(tickets_dir if tickets_dir is not None else ROOTS["tickets"]):
        try:
            doc = tf.read_ticket(plan)
            if is_terminal(parse_workflow(str(doc.get("workflow_and_state") or "")).here):
                continue
        except Exception:  # noqa: BLE001 — an unreadable ticket carries nothing; others still count
            continue
        fixes |= {_carried_rel(x, repo) for x in (doc.get("fixes") or []) if isinstance(x, str)}
        b = doc.get("bounds") if isinstance(doc.get("bounds"), dict) else {}
        bounds |= {_carried_rel(x, repo) for x in (b.get("in") or []) if isinstance(x, str)}
    return fixes, bounds


def _carried_rel(x: str, repo: Path) -> str:
    """A ticket's path as this repo spells it: an absolute one inside the repo folds to its
    repo-relative form (see ``_fixes_path``)."""
    x = x.replace("\\", "/")
    return (_rel(x, repo) or x) if Path(x).is_absolute() else x


def _fixes_path(rel: str, repo: Path) -> str:
    """The ``fixes`` entry for ``rel``: repo-relative in the live repo, which is the root the
    cast door and every fixit reader resolve against; absolute for any other repo (a proof's
    scratch repo), since a relative path there would resolve against the live one."""
    return rel if repo == _REPO else (repo / rel).as_posix()


def _owner(rel: str, repo: Path) -> str:
    d = Path(rel).parent
    while d.as_posix() not in ("", "."):
        if (repo / d / CHARTER).is_file():
            return f"{d.as_posix()}/{CHARTER}"
        d = d.parent
    return FALLBACK_OWNER


def _cast(item: dict, repo: Path, run_record: str | None, tickets_dir) -> Path:
    from cairn.tools.base.transitions import CastRefused, cast_ticket
    from cairn.machines.learning_block.learning_block import DoorRefused
    sys_door = _sorted_door()
    rel, keys = item["path"], item["keys"]
    record = Path(run_record or item.get("record") or repo / rel)
    record = (record if record.is_absolute() else repo / record).as_posix()
    red = item["kind"] == "red"
    title = (f"the red proof {rel} reseals green" if red
             else f"the orphaned file {rel} belongs to a component or is gone")
    saw = (f"{rel} ran red; teeth red: {', '.join(k.split('::', 1)[1] for k in keys)}" if red
           else f"{rel} is orphaned: {item.get('why')}")
    falsifier = "the proof reseals green" if red else "the path belongs to a component or is gone"
    because = f"none, because {record} is the run that found it"
    packet = {
        "skill": "sorted", "title": title,
        "assumption_check": f"Measured by the tester: {saw}. Run record: {record}.",
        "builder_check": f"Find why {rel} {'reds' if red else 'is orphaned'} and fix it so that "
                         f"{falsifier}. Keys: {', '.join(keys)}.",
        "children": because, "collision_check": f"none: the tester dedups on fixes and bounds.in "
                                                f"before casting ({', '.join(keys)})",
        "disposition": "cast", "exit": "routed_forward",
        "falsifier_check": f"1 clause: {falsifier}",
        "gates_bound": "code-seam: BUILDME entry gate, PROVEME build gate, PROVED exit gate",
        "missing_check": f"cast by the tester (ticket 207c4074b3d5) from {record}",
        "node_class": "code-seam", "questions": because, "task_or_ticket": "ticket",
        "watchme": because, "workflow": WORKFLOW,
        "bullets": [{"text": f"Measured by the tester: {saw}.", "stratum": "code"}],
    }
    try:
        fired = sys_door.fire(packet, berths=ROOTS["berths"], trace_root=ROOTS["trace"],
                              repo=repo, commons=ROOTS["commons"])
    except DoorRefused as exc:
        raise RedTicketRefused(keys[0], "sorted", getattr(exc, "lacks", None) or [str(exc)]) from exc
    if not fired.get("berth"):
        raise RedTicketRefused(keys[0], "sorted", [f"no berth recorded: {fired}"])
    doc = {
        "id": uuid.uuid4().hex[:12], "title": title, "date": date.today().isoformat(),
        "owner": "CC", "owning_intention": _owner(rel, repo),
        "intention": f"{rel} {'reseals green' if red else 'belongs to a component or is gone'}, "
                     "so the red the tester found is not lost.",
        "why": f"Outline 9.4.2.3.7.5 (reds don't get lost): the tester measured it. {saw}.",
        "traces_to": "Law 7 (errors are permanent in records of truth); outline 9.4.2.3.7.5",
        "how": packet["builder_check"],
        "falsifier": {"clauses": [{"n": 1, "claim": falsifier}]},
        "bounds": {"in": [rel], "out": ["every other component"]},
        "measured": [{"when": date.today().isoformat(), "saw": saw,
                      "how": f"the tester's run, record {record}; keys {', '.join(keys)}"}],
        "fixes": [_fixes_path(rel, repo)], "node_class": "code-seam", "workflow_and_state": WORKFLOW,
        "watchme": because, "intent_berth": because, "sorted_berth": fired["berth"],
    }
    try:
        return cast_ticket(doc, actor="tester", tickets_dir=tickets_dir), Path(fired["berth"])
    except CastRefused as exc:
        raise RedTicketRefused(keys[0], "cast", exc.lacks) from exc


def _git(top: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(top), *args], capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


def _commons_top(tickets_dir) -> Path:
    """The git tree the store lives in. A store outside git cannot commit in the same act, and
    a cast that cannot commit is dirt that refuses every crossing after it: loud (Law 7)."""
    from cairn.tools.base import ticket_file as _tf
    d = Path(_tf._TICKETS if tickets_dir is None else tickets_dir)
    got = _git(d, "rev-parse", "--show-toplevel")
    if got.returncode != 0:
        raise StoreUnreachable("*", "commit", [f"the ticket store {d} is in no git tree: "
                                               f"{got.stderr.strip()}"])
    return Path(got.stdout.strip())


def _staged(top: Path) -> list[str]:
    got = _git(top, "diff", "--cached", "--name-only")
    if got.returncode != 0:
        raise RedTicketRefused("*", "commit", [f"git diff --cached in {top}: {got.stderr.strip()}"])
    return [x for x in got.stdout.splitlines() if x.strip()]


def _named_paths(plan: Path, berth: Path, top: Path) -> list[str]:
    """Every file one cast wrote, named: the plan, its state and log beside it, the berth
    carried into the commons, and the commons journal."""
    from cairn.tools.base.ticket_file import state_path
    from cairn.tools.base.ticket_log import log_path
    out = [plan, state_path(plan), log_path(plan),
           top / "berths" / berth.parent.name / berth.name, top / ".artifact-journal.jsonl"]
    return [Path(x).resolve().relative_to(top.resolve()).as_posix() for x in out if Path(x).is_file()]


def _commit(plans: list, top: Path, keys: list[str]) -> str:
    """Stage each cast's files by name and plain-commit them. No push: the next pull or push
    carries it (decision D7, orchestrator 2026-11-13)."""
    named: list[str] = []
    for plan, berth in plans:
        named += [x for x in _named_paths(plan, berth, top) if x not in named]
    message = (f"tester: ticketed {len(plans)} new red(s)/orphan(s) (ticket 207c4074b3d5)\n\n"
               + "\n".join(keys))
    for step in (["add", "--", *named], ["commit", "-q", "-m", message]):
        got = _git(top, *step)
        if got.returncode != 0:
            raise RedTicketRefused(keys[0] if keys else "*", "commit",
                                   [f"git {step[0]} in {top}: {(got.stderr or got.stdout).strip()}"])
    return _git(top, "rev-parse", "HEAD").stdout.strip()


def _hold(items: list[dict], staged: list[str], top: Path, run_record) -> None:
    """Another writer's changes are staged: cast nothing, commit nothing, and raise every
    would-be cast as a trouble so nothing is lost (decision D7)."""
    from cairn.tools.base.diagnostic import ModuleRaiser
    raiser = ModuleRaiser("tester", roots=ROOTS["raiser"])
    for item in items:
        raiser.raise_trouble(
            f"red_tickets:held:{item['keys'][0]}",
            why=f"the tester found {item['path']} {item['kind']} and could not ticket it: the "
                f"commons tree {top} holds someone else's staged changes, and a cast commits "
                "in the same act (ticket 207c4074b3d5 D7)",
            detail={"kind": item["kind"], "path": item["path"], "keys": item["keys"],
                    "record": str(run_record or item.get("record") or item["path"]),
                    "staged_by_another": staged, "commons": str(top)})


def _sorted_door():
    import importlib.util
    spec = importlib.util.spec_from_file_location("_sorted_door", _REPO / "skills" / "sorted" / "door.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def ticket_what_is_new(results, *, scan_orphans: bool = False, repo_root=None,
                       tickets_dir=None, run_record: str | None = None) -> list[Path]:
    """Cast one ticket per red proof and per orphan no open ticket carries; return the plans
    cast. ``results`` are run_proof records or reseal results; ``scan_orphans`` is a whole-tree
    run's. A door's refusal raises RedTicketRefused (Law 7).

    D7: what the run casts it commits in the same act, staged by name, plain commit, no push.
    When the commons holds someone else's staged changes it casts nothing, raises one trouble
    per would-be cast, and returns []."""
    repo = _repo(repo_root)
    tickets_dir = tickets_dir if tickets_dir is not None else ROOTS["tickets"]
    items = red_keys(results, repo) + (orphan_keys(repo) if scan_orphans else [])
    if not items:
        return []
    fixes, bounds = carried(repo, tickets_dir)
    new = []
    for item in items:
        if item["path"] in fixes or (item["kind"] == "red" and item["path"] in bounds):
            continue
        new.append(item)
        fixes.add(item["path"])
    if not new:
        return []
    top = _commons_top(tickets_dir)
    staged = _staged(top)
    if staged:
        _hold(new, staged, top, run_record)
        return []
    cast = []
    try:
        for item in new:
            cast.append(_cast(item, repo, run_record, tickets_dir))
    finally:   # a refusal mid-run still commits what landed before it: no dirt left behind
        if cast:
            _commit(cast, top, [k for item in new[:len(cast)] for k in item["keys"]])
    return [plan for plan, _ in cast]
