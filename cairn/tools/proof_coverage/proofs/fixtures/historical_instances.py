"""The three measured instances of a proof binding its subject at import — rebuilt as worlds.

Each builder makes a scratch repository with TWO commits (the world before the build, dated
2020-01-01, and the build, dated 2020-01-03), a journal whose forward BUILDME crossing sits
between them (2020-01-02), a decompose berth naming what the build wrote, and the ticket the
sieve is asked about. That is exactly the set of inputs the sieve reads and hollow reverts,
so a tooth over one of these worlds exercises the same doors the live corpus goes through.

THE NAMES SAY WHAT THEY ARE (memory: self-describing fixture names). A file called
``subject_added_by_the_build.py`` leaking into a listing explains itself; ``a.py`` does not.

The three shapes, dated:

- 2026-09-10 — ``proof_coverage.py`` imported ``has_crossings`` from ``crossings.py`` at module
  level; the proofs reached proof_coverage for ``print_teeth_main``, so reverting the ADDED
  FILE crossings.py crashed the runner two hops from the proof. TRANSITIVE, ADDED FILE.
- 2026-09-13 (a38204e) — ``test_artifact_door.py`` line 25 did
  ``from cairn.tools.artifact import artifact as A`` and artifact.py was the build. DIRECT,
  ADDED FILE.
- 2026-09-14 (e1dcc6e) — ``test_exemption_set.py`` imported ``justification_lack`` from a module
  that itself imported ``answered_question`` from ``citation.py`` at module level, and that NAME
  was the build's addition to a file that already existed. TRANSITIVE, ADDED NAME. The hand fix
  wrapped the inner import in try/except with a stub, which is the green shape here.
"""
from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

TICKET = "f1x7u2ebind1"

_GIT_LOCATION_VARS = ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_PREFIX",
                      "GIT_COMMON_DIR", "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES")


def _env() -> dict:
    """The git identity, over an environment with the seven location variables removed — a
    proof run under a git hook inherits ``GIT_INDEX_FILE`` and every ``git -C <fixture>``
    would otherwise resolve against the caller's tree."""
    env = {k: v for k, v in os.environ.items() if k not in _GIT_LOCATION_VARS}
    env.update({"GIT_AUTHOR_NAME": "fixture", "GIT_AUTHOR_EMAIL": "f@x",
                "GIT_COMMITTER_NAME": "fixture", "GIT_COMMITTER_EMAIL": "f@x"})
    return env


def _git(repo: Path, *args: str, date: str | None = None) -> None:
    env = _env()
    if date:
        env["GIT_AUTHOR_DATE"] = env["GIT_COMMITTER_DATE"] = date
    got = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, env=env)
    if got.returncode != 0:
        raise RuntimeError(f"fixture git {' '.join(args)}: {got.stderr.strip()}")


@dataclass
class World:
    """One built fixture world: what the sieve and hollow are handed."""
    repo: Path
    roots: dict
    ticket: dict
    proof: str                       # repo-relative path of the proof the journal names
    writes_to: list[str]
    berth: Path
    commons: Path
    notes: dict = field(default_factory=dict)


def build_world(tmp: Path, *, before: dict[str, str], build: dict[str, str], proof: str,
                writes_to: list[str], clauses: int = 2, ticket: str = TICKET) -> World:
    """A two-commit repo: ``before`` is the pre-build tree, ``build`` is what the build wrote
    (new files and rewrites both), ``proof`` names the proof the BUILDME crossing carries,
    ``writes_to`` is what the decompose berth declares."""
    repo, commons, berths = tmp / "repo", tmp / "CairnCommons", tmp / "berths"
    repo.mkdir(parents=True)
    _git(repo, "init", "-q", "-b", "main")
    _write_all(repo, before)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "before the build", date="2020-01-01T00:00:00")
    _write_all(repo, build)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "the build", date="2020-01-03T00:00:00")

    # The journal is UNTRACKED on purpose — it describes the build and is not part of it.
    journal = repo / "cairn" / "fixture" / "history.json"
    journal.parent.mkdir(parents=True, exist_ok=True)
    journal.write_text(json.dumps({"entries": [
        {"ticket": ticket, "direction": "forward", "actor": "fixture",
         "at": "2020-01-02T00:00:00", "from": "TICKETME", "to": "BUILDME", "proven_by": proof},
        {"ticket": ticket, "direction": "forward", "actor": "fixture",
         "at": "2020-01-02T00:01:00", "from": "BUILDME", "to": "PROVEME", "proven_by": proof},
    ]}, indent=2), encoding="utf-8")

    berth = berths / "0" / "packets" / f"decompose-20200103T000000-{ticket}.json"
    berth.parent.mkdir(parents=True, exist_ok=True)
    berth.write_text(json.dumps({
        "ticket": ticket, "stage": "decompose",
        "sub_problems": [{"what": "the build", "kind": "build", "writes_to": writes_to}]}),
        encoding="utf-8")

    falsifier = "DONE when: " + "; ".join(f"({i}) clause {i} holds" for i in range(1, clauses + 1))
    ticket_doc = {"id": ticket, "node_class": "code-seam", "falsifier": falsifier,
                  "workflow_and_state": "code-seam@v2: THINKME -> TICKETME -> BUILDME -> "
                                        "[PROVEME:waiting] -> PROVED"}
    (commons / "tickets").mkdir(parents=True, exist_ok=True)
    (commons / "tickets" / f"{ticket}-fixture-binding-world.json").write_text(
        json.dumps(ticket_doc, indent=2), encoding="utf-8")

    roots = {"repo": repo, "commons": commons, "instance": tmp / ".cairn", "berths": berths}
    return World(repo=repo, roots=roots, ticket=ticket_doc, proof=proof, writes_to=writes_to,
                 berth=berth, commons=commons)


def _write_all(repo: Path, files: dict[str, str]) -> None:
    for rel, text in files.items():
        path = repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def _proof(body_imports: str, teeth: dict[str, str], *, main_imports: str = "") -> str:
    """A proof in the corpus's own printing style: ``PROVES`` at the top, one function per
    tooth, a runner that prints ``ok <tooth>`` / ``FAIL <tooth>`` and catches Exception so a
    tooth over a reverted subject reds instead of crashing the runner."""
    proves = {TICKET: {str(i + 1): name for i, name in enumerate(teeth)}}
    out = ["import sys", "from pathlib import Path",
           "sys.path.insert(0, str(Path(__file__).resolve().parents[1]))",
           f"PROVES = {json.dumps(proves)}", "", body_imports, ""]
    for name, body in teeth.items():
        out += [f"def {name}():", *("    " + line for line in body.splitlines()), ""]
    out += ["if __name__ == '__main__':"]
    if main_imports:
        out += ["    " + line for line in main_imports.splitlines()]
    out += ["    bad = 0",
            f"    for name in {json.dumps(list(teeth))}:",
            "        try:", "            ok = bool(globals()[name]())",
            "        except Exception:", "            ok = False",
            "        print(('ok' if ok else 'FAIL') + ' ' + name)",
            "        bad += 0 if ok else 1",
            "    raise SystemExit(1 if bad else 0)", ""]
    return "\n".join(out)


# ── the direct shape (a38204e): the proof itself imports the added file at module level ──

def direct_added_file(tmp: Path, *, moved_into_main: bool = False) -> World:
    """``from subject_added_by_the_build import ...`` on the proof's own line 6. With
    ``moved_into_main`` the same import sits inside the runner — the hand fix's shape."""
    teeth = {"test_the_added_subject_answers": "import subject_added_by_the_build as s\n"
                                               "return s.answer() == 42",
             "test_the_old_subject_still_stands": "import subject_that_existed as o\n"
                                                  "return o.VALUE == 2"}
    imports = "" if moved_into_main else "from subject_added_by_the_build import answer  # noqa"
    proof = _proof(imports, teeth,
                   main_imports="from subject_added_by_the_build import answer  # noqa" if moved_into_main else "")
    world = build_world(
        tmp,
        before={"subject_that_existed.py": "VALUE = 1\n",
                "proofs/test_fixture_direct.py": _proof("", {"test_the_old_subject_still_stands":
                                                             "import subject_that_existed as o\nreturn o.VALUE == 1"})},
        build={"subject_that_existed.py": "VALUE = 2\n",
               "subject_added_by_the_build.py": "def answer():\n    return 42\n",
               "proofs/test_fixture_direct.py": proof},
        proof="proofs/test_fixture_direct.py",
        writes_to=["subject_that_existed.py", "subject_added_by_the_build.py",
                   "proofs/test_fixture_direct.py"])
    world.notes = {"binding_line": 6 if not moved_into_main else None,
                   "added_file": "subject_added_by_the_build.py"}
    return world


# ── the first shape (2026-09-10): the proof reaches the added file through a helper ──

def transitive_added_file(tmp: Path) -> World:
    """The proof imports ``runner_that_existed`` (for its printer, nothing to do with the
    build) and THAT module imports ``crossings_added_by_the_build`` at module level."""
    teeth = {"test_the_runner_prints": "return runner_that_existed.PRINTER == 'teeth'",
             "test_the_added_crossings_read": "import crossings_added_by_the_build as c\n"
                                              "return c.has_crossings('x') is False"}
    proof = _proof("import runner_that_existed  # noqa", teeth)
    world = build_world(
        tmp,
        before={"runner_that_existed.py": "PRINTER = 'teeth'\n",
                "proofs/test_fixture_transitive.py": _proof("import runner_that_existed  # noqa",
                                                           {"test_the_runner_prints":
                                                            "return runner_that_existed.PRINTER == 'teeth'"})},
        build={"runner_that_existed.py": "from crossings_added_by_the_build import has_crossings  # noqa\n"
                                         "PRINTER = 'teeth'\n",
               "crossings_added_by_the_build.py": "def has_crossings(tid):\n    return False\n",
               "proofs/test_fixture_transitive.py": proof},
        proof="proofs/test_fixture_transitive.py",
        writes_to=["runner_that_existed.py", "crossings_added_by_the_build.py",
                   "proofs/test_fixture_transitive.py"])
    world.notes = {"proof_line": 6, "helper_line": 1, "added_file": "crossings_added_by_the_build.py"}
    return world


# ── the third shape (e1dcc6e): an added NAME in a file that existed, two hops away ──

_CITATION_BEFORE = "def cite(x):\n    return 'cited ' + x\n"
_CITATION_AFTER = _CITATION_BEFORE + "\n\ndef answered_question(tid):\n    return None\n"
_JUSTIFICATION_BOUND = ("from pkg_that_existed.citation_that_existed import answered_question\n\n"
                        "def justification_lack(tid):\n    return answered_question(tid) is None\n")
_JUSTIFICATION_FIXED = ("try:\n    from pkg_that_existed.citation_that_existed import answered_question\n"
                        "except ImportError:  # the subject may be reverted under a hollow reading\n"
                        "    def answered_question(tid):\n        return None\n\n"
                        "def justification_lack(tid):\n    return answered_question(tid) is None\n")


def transitive_added_name(tmp: Path, *, hand_fixed: bool = False) -> World:
    """The proof imports ``justification_lack`` from a module that existed; that module binds
    ``answered_question`` — the build's addition to ``citation_that_existed.py`` — at module
    level. With ``hand_fixed`` the inner import is wrapped in try/except with a stub, which is
    what e1dcc6e did and what the sieve must read as green."""
    teeth = {"test_a_lack_reads": "return justification_lack('t') is True",
             "test_the_citation_still_cites": "from pkg_that_existed import citation_that_existed as c\n"
                                              "return c.cite('x') == 'cited x'"}
    proof = _proof("from pkg_that_existed.justification_that_existed import justification_lack  # noqa", teeth)
    before_just = "def justification_lack(tid):\n    return True\n"
    world = build_world(
        tmp,
        before={"pkg_that_existed/__init__.py": "",
                "pkg_that_existed/citation_that_existed.py": _CITATION_BEFORE,
                "pkg_that_existed/justification_that_existed.py": before_just,
                "proofs/test_fixture_name.py": _proof(
                    "from pkg_that_existed.justification_that_existed import justification_lack  # noqa",
                    {"test_a_lack_reads": "return justification_lack('t') is True"})},
        build={"pkg_that_existed/citation_that_existed.py": _CITATION_AFTER,
               "pkg_that_existed/justification_that_existed.py":
                   _JUSTIFICATION_FIXED if hand_fixed else _JUSTIFICATION_BOUND,
               "proofs/test_fixture_name.py": proof},
        proof="proofs/test_fixture_name.py",
        writes_to=["pkg_that_existed/citation_that_existed.py",
                   "pkg_that_existed/justification_that_existed.py",
                   "proofs/test_fixture_name.py"])
    world.notes = {"proof_line": 6, "justification_line": 1 if not hand_fixed else None,
                   "added_name": "answered_question",
                   "in": "pkg_that_existed/citation_that_existed.py"}
    return world


# ── the fourth shape (a38204e, test_artifact_gate.py): a loader call the walk cannot see ──

def loader_call_blind_spot(tmp: Path) -> World:
    """``gate = _load(PATH, 'gate')`` at module level binds the added file through importlib.
    The sieve reads this GREEN by construction — it is the charter's first filed edge and what
    the WATCHME measures against hollow, which does catch it."""
    teeth = {"test_the_gate_refuses": "return gate.refuse('x') == 'refused x'"}
    imports = ("import importlib.util\n"
               "def _load(path, name):\n"
               "    spec = importlib.util.spec_from_file_location(name, path)\n"
               "    mod = importlib.util.module_from_spec(spec)\n"
               "    spec.loader.exec_module(mod)\n"
               "    return mod\n"
               "gate = _load(Path(__file__).resolve().parents[1] / 'gate_added_by_the_build.py', 'gate')")
    proof = _proof(imports, teeth)
    return build_world(
        tmp,
        before={"proofs/test_fixture_loader.py": _proof("", {"test_nothing": "return True"})},
        build={"gate_added_by_the_build.py": "def refuse(x):\n    return 'refused ' + x\n",
               "proofs/test_fixture_loader.py": proof},
        proof="proofs/test_fixture_loader.py",
        writes_to=["gate_added_by_the_build.py", "proofs/test_fixture_loader.py"])
