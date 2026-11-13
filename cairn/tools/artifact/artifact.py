"""artifact — the one door a record of truth changes through, and the journal of who came.

Ticket 30531f6e1c5d; ruling 2026-09-13-records-of-truth-change-only-through-the-artifact-door.

THE LIVED SYMPTOM. Ticket 481221f45884 stood at ``[PROVED]`` with no crossing in the harbor
journal: its cursor had been moved by hand (commit 42e3db0, 2026-09-10), and nothing in the
system could say so until a reader compared two records by eye. "Records go through their
door" was a memory and a paragraph; 145 code sites in 69 files wrote record paths with
``write_text`` (census 2026-09-13). Akien: *"we have to build a machine that you must use to
update .artifacts and the job of the machine will be in part to assure that a hand edits
only happen with an explicit from me to allow that."*

WHO IS KERNEL TRUTH; WHY IS TESTIMONY. Every write journals its caller's CLASS read from the
process's cgroup ancestry (``cairn.tools.cgroup``) — a gate under a ``cairn-*.service``
unit, CC under the ``superclaude-<pid>.scope`` the launcher puts every session in, Akien at a
desktop-app or login-session scope. A caller cannot forge that from inside its own process.
The call stack Akien asked for is journaled BESIDE it as provenance — which gate, which
line — and is never used to decide trust, because a stack is a claim the caller makes and
three lines of Python could make any claim.

THE JOURNAL IS HASH-CHAINED AND LIVES IN THE REPO beside the records it describes: one
``.artifact-journal.jsonl`` per root, each entry carrying the sha256 of the record before and
after and the sha256 of the previous entry. The pre-commit check (``check_staged``) refuses
to commit any record whose STAGED bytes are not the journal's last ``sha_after`` for that
path — catching a hand edit, a git surgery, CC and Akien alike at the one point everything
passes. A record edited by hand is not forbidden; it is PARKED (``park_hand_edit``) and
waits for Akien's words, and his approval is itself measured: ``approve`` refuses a caller
whose class is not ``akien``.

A TOOL, NOT AN OWNER (Law 6). The door gates nothing at its own address: the journal is the
record repo's state, owned by whoever owns that repo's records, and every per-class door
(the validation store, the history append, the trouble device, the ruling intake, the skill
doors) keeps its own verb and calls this to do the write. A proof hands the door a scratch
world through ``set_diagnostic_roots`` — the same seam every device offers — so its fixture
records never touch the live journals.

WHAT IS NOT CLAIMED. The pre-commit check and the PreToolUse gate are policy a process can
bypass (``git commit --no-verify``; a session with hooks off). The physics — the record roots
owned by a second unix user with this door the only path through the sudo relay — is the
ticket's owed_physics, named and not paid here.
"""

from __future__ import annotations

import contextlib
import fnmatch
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import threading
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path

if os.name == "nt":       # no fcntl on Windows: a 1-byte msvcrt lock plays flock (dies with the process too)
    import msvcrt
else:
    import fcntl

from cairn.tools.cgroup.cgroup import cgroup_of

_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parents[2]
_JURISDICTION = _HERE / "jurisdiction.json"

VERBS = ("genesis", "cast", "append", "compile", "seal", "raise", "clear", "ruling", "slate", "question", "answer",
         "idea", "charter", "phase", "hand-edit", "rename", "remove", "bulk", "write",
         # ``rehearse`` joined 2026-09-15 (ticket cf80bdb57205): a rehearsal record — the cheapest
         # reader's converged build tree over a ticket, under CairnCommons/rehearsals/.
         "rehearse",
         # ``outline_check`` joined 2026-10-26 (ticket 6541ccd1594c): one read of a ticket beside
         # the component outline, under CairnCommons/outline_checks/.
         "outline_check",
         # ``certify`` joined 2026-10-28 (ticket 5dc4d8a0b4d2): a certificate, under
         # CairnCommons/certificates/, which only TransitionGate.certify writes.
         "certify")

# Caller classes, and the cgroup leaf that MEASURES each. ``akien`` is a desktop-app scope
# (Konsole, Kate, ...) or a logind session scope (a tty or ssh login): a hand at a terminal.
# Measured 2026-09-13 on this host: cairn-web-server.service, superclaude-2132130.scope,
# app-org.kde.konsole-….scope on /dev/pts/N.
_GATE = re.compile(r"^cairn-[^/]+\.service$")
_CC = re.compile(r"^superclaude-\d+\.scope$")
_AKIEN = re.compile(r"^(?:app-[^/]+|session-[^/]+)\.scope$")

CALLER_CLASSES = ("gate", "cc", "akien", "unknown")

_diagnostic_roots: dict[str, Path] | None = None


class Refused(Exception):
    """The door said no, and the message carries the way through (Law 7)."""


class JournalLineOrphaned(OSError):
    """The record landed but git replaced the journal under the append: the line went to a file
    no longer at the path. The entry is parked, never dropped (ticket 0f8aefbba1d0)."""


# ---------------------------------------------------------------------------
# WORLD: which roots, which records


def set_diagnostic_roots(roots: dict[str, Path] | None) -> None:
    """Point the door at a different WORLD — the temp-tree seam every device offers.

    ``roots`` maps a root NAME to a directory; ``None`` restores the live pair. A scratch
    root is judged by the jurisdiction rules of the live root with the same name, so a
    proof exercises the real predicate over a fixture tree instead of a substitute one."""
    global _diagnostic_roots
    _diagnostic_roots = None if roots is None else {k: Path(v).resolve() for k, v in roots.items()}


def jurisdiction() -> dict:
    return json.loads(_JURISDICTION.read_text(encoding="utf-8"))


def roots() -> dict[str, Path]:
    """Root name → directory, live or diagnostic. Only names the jurisdiction declares.

    ``CAIRN_ARTIFACT_ROOTS`` (a JSON object name → dir) is the same seam for a SUBPROCESS —
    the pre-commit hook a proof fires inside a scratch clone cannot be handed a Python
    call, so it is handed the environment."""
    if _diagnostic_roots is not None:
        return {k: v for k, v in _diagnostic_roots.items() if k != "parked"}
    env = os.environ.get("CAIRN_ARTIFACT_ROOTS")
    if env:
        return {k: Path(v).resolve() for k, v in json.loads(env).items() if k != "parked"}
    return {"cairn": _REPO, "CairnCommons": _REPO.parent / "CairnCommons"}


def root_name_of(path: str | os.PathLike) -> str:
    """Which declared root a directory IS (the hook asks this of its own toplevel)."""
    p = Path(path).resolve()
    for name, root in roots().items():
        if root == p:
            return name
    raise Refused(f"{p} is not a declared record root ({', '.join(roots())}) — nothing to check")


def _rule_matches(rule: dict, rel: Path) -> bool:
    if not fnmatch.fnmatchcase(rel.name, rule.get("name", "*")):
        return False
    if "under" in rule:
        return rel.parent.as_posix() == rule["under"]
    if "parent" in rule:
        return rel.parent.name == rule["parent"]
    return True


def locate(path: str | os.PathLike) -> tuple[str, Path, Path] | None:
    """``(root name, root dir, repo-relative path)`` when ``path`` is a record of truth in a
    known root; ``None`` when it is outside the door's jurisdiction. A None is a real answer:
    the door still writes such a file, it just does not journal it."""
    p = Path(path)
    p = (p if p.is_absolute() else Path.cwd() / p).resolve()
    rules = jurisdiction()["roots"]
    for name, root in roots().items():
        try:
            rel = p.relative_to(root)
        except ValueError:
            continue
        for rule in rules.get(name, {}).get("records", []):
            if _rule_matches(rule, rel):
                return name, root, rel
        return None
    return None


def journal_path(root: Path) -> Path:
    return root / jurisdiction()["journal"]


# ---------------------------------------------------------------------------
# WHO: the caller, measured


def classify(cgroup: str | None) -> dict:
    """The caller class from a cgroup path. Pure, so a proof can pin it over text.

    The segments are walked from the leaf outward and the innermost class-naming one
    decides, so a scope a terminal nests per tab (Konsole's ``tab(N).scope``) reads as
    the terminal that holds it (ticket b63f5bbbef89)."""
    for seg in reversed((cgroup or "").rstrip("/").split("/")):
        for cls, pat in (("gate", _GATE), ("cc", _CC), ("akien", _AKIEN)):
            if pat.match(seg):
                return {"class": cls, "cgroup": cgroup, "unit": seg}
    return {"class": "unknown", "cgroup": cgroup, "unit": None}


def _ppid(pid: int) -> int | None:
    """The parent pid from /proc/<pid>/stat — the field after the ')' that ends the comm."""
    try:
        raw = Path(f"/proc/{pid}/stat").read_text()
    except OSError:
        return None
    try:
        return int(raw.rsplit(")", 1)[1].split()[1])
    except (IndexError, ValueError):
        return None


def ancestry(pid: int | None = None, limit: int = 64) -> list[dict]:
    """``[{pid, cgroup, class}]`` from this process up to pid 1 — the process tree the
    kernel keeps. Measured 2026-09-13: ``systemd-run --user --scope`` moves a child into a
    fresh scope but does NOT reparent it, so a CC session that spawns an ``app-*.scope`` to
    look like a hand at a terminal still has the claude process — in its superclaude
    scope — as an ancestor. The one escape (a scope AND a daemonising double-fork, which
    reparents to systemd) is two deliberate steps, and is the ticket's owed physics."""
    pid = os.getpid() if pid is None else int(pid)
    out, seen = [], set()
    while pid and pid > 1 and pid not in seen and len(out) < limit:
        seen.add(pid)
        cg = cgroup_of(pid)
        out.append({"pid": pid, "cgroup": cg, "class": classify(cg)["class"]})
        pid = _ppid(pid)
    return out


def _env(name: str) -> str:
    """One environment variable, empty when unset: the one place caller() reads the environment (8a53046951bb)."""
    return os.environ.get(name) or ""


def caller() -> dict:
    """This process's caller record — kernel truth, read now, never cached.

    The class is decided over the ANCESTRY, not the leaf alone: a ``cc`` anywhere up the
    tree makes the caller cc, because a process CC started is CC's hand whatever scope it
    sits in; otherwise the leaf decides. The chain rides the entry so a reader can see
    how the class was reached. The environment then names whose hand it is, and can never
    turn a measured cc into akien (ticket 8a53046951bb)."""
    chain = ancestry()
    me = classify(chain[0]["cgroup"] if chain else cgroup_of("self"))
    if me["class"] != "cc" and any(a["class"] == "cc" for a in chain[1:]):
        cc = next(a for a in chain[1:] if a["class"] == "cc")
        me = {"class": "cc", "cgroup": me["cgroup"], "unit": classify(cc["cgroup"])["unit"],
              "via_ancestor": cc["pid"]}
    # WHOSE TERMINAL IT IS (8a53046951bb). Akien 2026-10-13: "if CAIRN_USER is set, then it's
    # you... if it's not, then it's me." CC evidence (a cc up the tree, CAIRN_USER, CLAUDECODE)
    # always wins: CC's shells snapshot ~/.bashrc and so carry CAIRN_OPERATOR=Akien too.
    if me["class"] == "cc":
        me["who"] = _env("CAIRN_USER") or "cc"
    elif _env("CAIRN_USER") or _env("CLAUDECODE"):
        me.update({"class": "cc", "who": _env("CAIRN_USER") or "cc", "via": "env"})
    elif me["class"] == "akien":
        me["who"] = _env("CAIRN_OPERATOR") or "akien"
    elif me["class"] == "unknown" and _env("CAIRN_OPERATOR"):
        me.update({"class": "akien", "who": _env("CAIRN_OPERATOR"), "via": "env"})
    elif me["class"] == "gate":
        me["who"] = "gate"
    else:
        me["who"] = None
    me["ancestry"] = [f"{a['pid']}:{(a['cgroup'] or '').rsplit('/', 1)[-1]}" for a in chain]
    return me


def _stack(limit: int = 6) -> list[str]:
    """The frames above the door, innermost first — the WHY, as testimony."""
    out = []
    for fr in reversed(traceback.extract_stack()):
        if Path(fr.filename).resolve().parent == _HERE:
            continue
        out.append(f"{fr.filename}:{fr.lineno}:{fr.name}")
        if len(out) >= limit:
            break
    return out


# ---------------------------------------------------------------------------
# THE JOURNAL


def _sha(data: bytes | None) -> str:
    return "absent" if data is None else hashlib.sha256(data).hexdigest()


def _entry_sha(entry: dict) -> str:
    body = {k: v for k, v in entry.items() if k != "entry"}
    return hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":")).encode("utf-8")).hexdigest()


def read_journal(root: Path) -> list[dict]:
    jp = journal_path(root)
    if not jp.exists():
        return []
    entries = []
    for n, line in enumerate(jp.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise Refused(f"{jp}:{n} is not a journal entry ({exc}) — the journal is a record "
                          f"of truth and a broken line is a broken chain, not a line to skip")
    return entries


def last_sha(entries: list[dict], rel: str) -> str | None:
    """The journal's last ``sha_after`` for ``rel``, or None when it was never journaled."""
    for e in reversed(entries):
        if e.get("path") == rel:
            return e.get("sha_after")
    return None


def verify_chain(root: Path) -> list[str]:
    """Replay the chain from genesis. Every fault, none swallowed."""
    faults = []
    prev = "genesis"
    for n, e in enumerate(read_journal(root), 1):
        if e.get("prev") != prev:
            faults.append(f"entry {n}: prev {e.get('prev')!r} is not the previous entry's sha {prev!r}")
        want = _entry_sha(e)
        if e.get("entry") != want:
            faults.append(f"entry {n}: entry sha {e.get('entry')!r} does not match its body ({want})")
        prev = e.get("entry")
    return faults


def _identity(entry: dict) -> str:
    """What an entry SAYS, without where it hangs: the body less ``prev`` and ``entry``. A copy
    re-linked by an earlier merge carries a new sha and the same identity."""
    return json.dumps({k: v for k, v in entry.items() if k not in ("prev", "entry")},
                      sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _parse_journal(blob: bytes, side: str) -> list[dict]:
    out = []
    for n, line in enumerate(blob.decode("utf-8").splitlines(), 1):
        if line.strip():
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise Refused(f"{side} journal line {n} is not an entry ({exc})")
    return out


def merge_journals(ours: bytes, theirs: bytes) -> bytes:
    """Two journals that grew apart, met without forking the chain (ticket b7d2e05a1c93).

    Git's text merge of ``.artifact-journal.jsonl`` either conflicts or leaves two entries
    chained to one ``prev``. Measured 2026-11-11 (6d324d26343d's PROVED push): upstream was
    already forked at entry 16162, a peer having chained off entry 16018, and the repair was a
    hand re-link. Here OURS is kept byte for byte, in order. Each entry of THEIRS whose identity
    OURS lacks is appended in THEIRS' order with ``prev`` and ``entry`` re-linked onto the tail.
    Its body is never touched. So the result replays clean from genesis (``verify_chain``) and
    holds every entry either side wrote, once. In a rebase OURS is upstream, so only the
    replayed commits' entries are re-linked; in a merge it is the branch merged into.
    """
    mine = _parse_journal(ours, "ours")
    have = {_identity(e) for e in mine}
    tail = mine[-1]["entry"] if mine else "genesis"
    added = []
    for e in _parse_journal(theirs, "theirs"):
        key = _identity(e)
        if key in have:
            continue
        have.add(key)
        e = {k: v for k, v in e.items() if k not in ("prev", "entry")}
        e["prev"] = tail
        e["entry"] = _entry_sha(e)
        tail = e["entry"]
        added.append(json.dumps(e, ensure_ascii=False, sort_keys=True) + "\n")
    head = ours if not ours or ours.endswith(b"\n") else ours + b"\n"
    return head + "".join(added).encode("utf-8")


def _lock(fh, tries: int = 1) -> None:
    if os.name == "nt":
        for n in range(tries):
            fh.seek(0)
            try:
                msvcrt.locking(fh.fileno(), msvcrt.LK_LOCK, 1)   # retries ~10 s, then raises OSError
                return
            except OSError:
                if n == tries - 1:
                    raise
    else:
        fcntl.flock(fh, fcntl.LOCK_EX)


def _unlock(fh) -> None:
    if os.name == "nt":
        fh.seek(0)
        msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
    else:
        fcntl.flock(fh, fcntl.LOCK_UN)


def _same_file(fh, path: Path) -> bool:
    """Does the open handle still name the file at ``path``? (st_dev, st_ino); on nt a zero
    st_ino carries no identity, so the check passes there (ticket 0f8aefbba1d0)."""
    try:
        a, b = os.fstat(fh.fileno()), os.stat(path)
    except FileNotFoundError:
        return False
    if os.name == "nt" and (not a.st_ino or not b.st_ino):
        return True
    return (a.st_dev, a.st_ino) == (b.st_dev, b.st_ino)


_GIT_DIRS: dict[Path, Path | None] = {}
_held = threading.local()


def git_dir(where: Path) -> Path | None:
    """The absolute git dir of the work tree at ``where`` (a worktree has its own), or None."""
    where = Path(where).resolve()
    if where not in _GIT_DIRS:
        try:
            out = subprocess.run(["git", "-C", str(where), "rev-parse", "--absolute-git-dir"],
                                 capture_output=True, text=True, timeout=30)
            _GIT_DIRS[where] = Path(out.stdout.strip()) if out.returncode == 0 and out.stdout.strip() else None
        except (OSError, subprocess.SubprocessError):
            _GIT_DIRS[where] = None
    return _GIT_DIRS[where]


@contextlib.contextmanager
def door_lock(where: Path):
    """Hold the repo-level door lock, ``<git dir>/cairn-door.lock``, for the work tree at ``where``.

    The door holds it across a record write and its journal append; ``cairn artifact quiet --
    <git cmd>`` holds it around a git rewrite (stash, checkout, pull --rebase --autostash), so
    the two cannot interleave. Measured 2026-11-13 (ticket 0f8aefbba1d0): a batch's autostash
    replaced the journal under an open append and the line was lost; re-landing it mid-stash
    instead jams the pop. Re-entrant within a thread; no git dir, no lock."""
    gd = git_dir(where)
    if gd is None:
        yield None
        return
    lp = gd / "cairn-door.lock"
    depth = getattr(_held, "depth", {})
    _held.depth = depth
    if depth.get(lp):
        depth[lp] += 1
        try:
            yield lp
        finally:
            depth[lp] -= 1
        return
    with open(lp, "a+", encoding="utf-8") as fh:
        _lock(fh, tries=30)
        depth[lp] = 1
        try:
            yield lp
        finally:
            depth[lp] = 0
            _unlock(fh)


def orphan_park(root: Path) -> Path:
    gd = git_dir(root)
    return (gd / "cairn-orphaned-lines.jsonl") if gd else journal_path(root).with_name(".artifact-orphaned-lines.jsonl")


def _append(root: Path, entry: dict) -> dict:
    """Append under a lock: read the tail, chain, write. Two writers cannot fork the chain.

    A writer that ignores the lock (git replacing the journal file) is met twice (ticket
    0f8aefbba1d0): at lock time, a handle that no longer names the file at the path is
    re-opened (at most 5 tries, then loud); after the write, a path that now names another
    file means the line went to an orphan, so the entry is parked in ``orphan_park(root)``
    and JournalLineOrphaned raises. Re-landing it there and then would jam git's stash pop
    (measured), so the re-land is a later act on a settled tree. A lock-time re-open that
    lands mid-stash leaves the pop to refuse, loudly, with the stash kept: loud, not dropped.
    Only ``quiet`` keeps a rewrite out of the window altogether."""
    jp = journal_path(root)
    jp.parent.mkdir(parents=True, exist_ok=True)
    for _ in range(5):
        fh = open(jp, "a+", encoding="utf-8")
        _lock(fh)
        if _same_file(fh, jp):
            break
        _unlock(fh)
        fh.close()
    else:
        raise OSError(f"{jp}: the journal was replaced under the lock five times running; "
                      "nothing appended (ticket 0f8aefbba1d0)")
    try:
        fh.seek(0)
        tail = None
        for line in fh:
            if line.strip():
                tail = line
        entry["prev"] = json.loads(tail)["entry"] if tail else "genesis"
        entry["entry"] = _entry_sha(entry)
        fh.seek(0, os.SEEK_END)
        fh.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")
        fh.flush()
        os.fsync(fh.fileno())
        landed = _same_file(fh, jp)
    finally:
        _unlock(fh)
        fh.close()
    if not landed:
        park = orphan_park(root)
        with open(park, "a", encoding="utf-8") as ph:
            ph.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")
            ph.flush()
            os.fsync(ph.fileno())
        raise JournalLineOrphaned(
            f"{jp}: git replaced the journal under the append, so entry {entry['entry']} for "
            f"{entry.get('path')} went to a file no longer at the path. The record's bytes landed; "
            f"the entry is parked in {park} — re-land it once the tree is settled (ticket 0f8aefbba1d0)")
    return entry


def reland(name: str, *, why: str) -> dict:
    """Re-land the entries ``_append`` parked in ``orphan_park`` (ticket b80c6d5637fe).

    Each parked entry, in park order: one that already stands in the journal (as an ``entry``
    or a ``relanded_from``) is dropped; one whose ``sha_before`` is the journal's last
    ``sha_after`` for its path and whose record stands at its ``sha_after`` is appended once,
    chained on the tail, keeping its writer's why and caller and adding ``relanded_from``,
    ``relanded_why`` and ``relanded_by``; anything else stays parked with its reason, because
    the bytes it describes are not the bytes that stand. The park keeps what stayed, plus
    every line parked while this ran. Run it on a settled tree (the door lock is held)."""
    if not (why or "").strip():
        raise Refused("a re-land with no why is the silent change this door exists to end — say why")
    root = roots()[name]
    park = orphan_park(root)
    out = {"relanded": [], "dropped": [], "kept": []}
    with door_lock(root):
        if not park.exists():
            return out
        lines = [x for x in park.read_text(encoding="utf-8").splitlines() if x.strip()]
        journal = read_journal(root)
        stands = {e.get("entry") for e in journal} | {e.get("relanded_from") for e in journal}
        keep: list[str] = []
        stuck = False
        for raw in lines:
            e = json.loads(raw)
            if stuck:
                keep.append(raw)
                out["kept"].append({"entry": e["entry"], "path": e.get("path"),
                                    "reason": "an earlier re-land in this run was parked again"})
                continue
            if e["entry"] in stands:
                out["dropped"].append(e["entry"])
                continue
            rel = e["path"]
            p = root / rel
            have = _sha(p.read_bytes() if p.exists() else None)
            last = last_sha(journal, rel)
            if last != e.get("sha_before") or have != e.get("sha_after"):
                keep.append(raw)
                out["kept"].append({"entry": e["entry"], "path": rel, "reason": (
                    f"the journal's last sha_after for {rel} is {(last or 'never journaled')[:12]} "
                    f"(the entry's sha_before is {str(e.get('sha_before'))[:12]}) and the record stands "
                    f"at {have[:12]} (the entry's sha_after is {str(e.get('sha_after'))[:12]})")})
                continue
            copy = {k: v for k, v in e.items() if k not in ("prev", "entry")}
            copy.update(relanded_from=e["entry"], relanded_why=why, relanded_by=caller())
            try:
                landed = _append(root, copy)
            except JournalLineOrphaned:
                stuck = True
                keep.append(raw)
                out["kept"].append({"entry": e["entry"], "path": rel,
                                    "reason": "git replaced the journal under the re-land; parked again"})
                continue
            journal.append(landed)
            stands |= {landed["entry"], e["entry"]}
            out["relanded"].append(landed["entry"])
        now = [x for x in park.read_text(encoding="utf-8").splitlines() if x.strip()]
        rest = keep + now[len(lines):]
        if rest:
            tmp = park.with_name(f".{park.name}.{uuid.uuid4().hex[:8]}.tmp")
            tmp.write_text("".join(x + "\n" for x in rest), encoding="utf-8")
            os.replace(tmp, park)
        else:
            park.unlink()
    return out


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _entry(rel: Path, verb: str, why: str, before: bytes | None, after: bytes | None,
           *, count: int = 1, extra: dict | None = None) -> dict:
    if verb not in VERBS:
        raise Refused(f"verb {verb!r} is not one of {VERBS}")
    if not (why or "").strip():
        raise Refused("a write with no why is the silent change this door exists to end — say why")
    e = {
        "at": _now(),
        "path": rel.as_posix(),
        "verb": verb,
        "why": why,
        "count": int(count),
        "sha_before": _sha(before),
        "sha_after": _sha(after),
        "caller": caller(),
        "stack": _stack(),
    }
    if extra:
        e.update(extra)
    return e


# ---------------------------------------------------------------------------
# THE DOOR


def _atomic_write(path: Path, blob: bytes, mode: int | None) -> None:
    """Temp-then-replace in the same directory: a partial write never sits in ``git status``
    as a corrupted record. ``mode`` None keeps the existing file's mode (the validation store
    parks its seals at 0444) and gives a new file 0644."""
    if mode is None:
        mode = (path.stat().st_mode & 0o777) if path.exists() else 0o644
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{uuid.uuid4().hex[:8]}.tmp")
    held = path.stat().st_mode if os.name == "nt" and path.exists() else None
    try:
        tmp.write_bytes(blob)
        os.chmod(tmp, mode)
        if held is not None:      # Windows: a read-only (0444) target cannot be replaced, Linux's can
            os.chmod(path, 0o666)
        os.replace(tmp, path)
    except BaseException:
        if os.name == "nt":       # ...nor can a read-only temp be unlinked; put the target's mode back
            if tmp.exists():
                os.chmod(tmp, 0o666)
            if held is not None and path.exists():
                os.chmod(path, held & 0o777)
        tmp.unlink(missing_ok=True)
        raise


def _refuse_non_canonical(p: Path, blob: bytes) -> None:
    """A JSON record lands in one canonical form (f9ba6c89844d): indent=2, with ensure_ascii
    and the trailing newline either way — the four bodies json.dumps writes. Anything else is
    refused before a byte lands or an entry journals, so the next reader never meets a shape
    it has to guess at."""
    try:
        text = blob.decode("utf-8")
        doc = json.loads(text)
    except ValueError as exc:
        raise Refused(f"{p} is a JSON record and the body does not parse ({exc}) — "
                      "nothing written (f9ba6c89844d)") from None
    forms = {json.dumps(doc, indent=2, ensure_ascii=ea) + ("\n" if nl else "")
             for ea in (False, True) for nl in (False, True)}
    if text not in forms:
        raise Refused(f"{p} is a JSON record and the body is not canonical (found {text[:60]!r}) — "
                      "write json.dumps(doc, indent=2) or use write_json; nothing written (f9ba6c89844d)")


def _refuse_history_without_floor(p: Path, blob: bytes) -> None:
    """A history row carries the projector's floor at this door too (62a57b781efc). Two rows
    without ``standing`` landed here on 2026-10-02 through verb append, past
    projector.append_entry's gate one door up. A row the body introduces — one not equal to a
    row of the standing file — must carry every key of projector.UNIVERSAL_REQUIRED; rows
    already standing are not re-judged, so keeping an old row never refuses the next append."""
    from cairn.tools.charter import projector  # at call time: projector imports this door
    body = json.loads(blob.decode("utf-8"))
    if not isinstance(body, list):
        return
    try:
        standing = json.loads(p.read_text(encoding="utf-8")) if p.exists() else []
    except ValueError:
        standing = []
    if not isinstance(standing, list):
        standing = []
    for rec in body:
        if rec in standing:
            continue
        missing = [k for k in projector.UNIVERSAL_REQUIRED
                   if not (isinstance(rec, dict) and rec.get(k))]
        if missing:
            seq = rec.get("seq") if isinstance(rec, dict) else None
            raise Refused(f"{p} is a history record and the row it introduces (seq {seq!r}) lacks "
                          f"{missing}, the floor projector.UNIVERSAL_REQUIRED names — append "
                          "through projector.append_entry; nothing written (62a57b781efc)")


def _refuse_non_append(p: Path, blob: bytes) -> None:
    """A ``.jsonl`` record only grows (9df0f230a087; Akien 2026-10-10, "Flat plan + .log.jsonl").

    Judged by byte prefix, never by parsing and comparing objects (D1): the new bytes must
    start with the record's current bytes (``b''`` when absent), and what they add must be
    whole lines, ending in a newline, each a JSON object. Anything else is refused, naming the
    path, and nothing is written."""
    old = p.read_bytes() if p.exists() else b""
    if not blob.startswith(old):
        at = next((i for i, (a, b) in enumerate(zip(old, blob)) if a != b), min(len(old), len(blob)))
        raise Refused(f"{p} is an append-only record (.jsonl) and this write does not start with "
                      f"its current {len(old)} bytes (first difference at byte {at}); append "
                      "whole lines, never rewrite; nothing written (9df0f230a087)")
    tail = blob[len(old):]
    if tail and not tail.endswith(b"\n"):
        raise Refused(f"{p} is an append-only record (.jsonl) and the appended bytes do not end "
                      "in a newline; append whole lines; nothing written (9df0f230a087)")
    for n, line in enumerate(tail.splitlines(), 1):
        try:
            obj = json.loads(line)
        except ValueError as exc:
            raise Refused(f"{p}: appended line {n} is not JSON ({exc}); nothing written "
                          "(9df0f230a087)") from None
        if not isinstance(obj, dict):
            raise Refused(f"{p}: appended line {n} is a JSON {type(obj).__name__}, not an "
                          "object; nothing written (9df0f230a087)")


def _refuse_undeclared_keys(name: str, root: Path, rel: Path, p: Path, blob: bytes) -> None:
    """A record set's keys are declared once, in its store's own charter (1fc53d5d96cc).

    The matched record entry's ``keys_from`` (``<path under the root>#<field>``) names the
    list; a body key outside it is refused by name. A charter or field that cannot be read
    refuses every write to the set (gates are hard). A name starting ``_`` is the store's own
    charter, not a member, and writes freely — it is what a member's keys are read FROM."""
    rule = next((r for r in jurisdiction()["roots"].get(name, {}).get("records", [])
                 if _rule_matches(r, rel)), None)
    if not rule or "keys_from" not in rule or rel.name.startswith("_"):
        return
    where, _, field = rule["keys_from"].partition("#")
    try:
        declared = json.loads((root / where).read_text(encoding="utf-8"))[field]
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise Refused(f"{p}: its record set reads its keys from {rule['keys_from']} and that "
                      f"cannot be read ({type(exc).__name__}: {exc}); every write to the set is "
                      "refused until it can; nothing written (1fc53d5d96cc)") from None
    doc = json.loads(blob.decode("utf-8"))
    if not isinstance(doc, dict):
        raise Refused(f"{p}: a member of a keyed record set is a JSON object, not a "
                      f"{type(doc).__name__}; nothing written (1fc53d5d96cc)")
    extras = sorted(set(doc) - set(declared))
    if extras:
        raise Refused(f"{p}: key(s) {extras} are not declared in {rule['keys_from']} — the plan "
                      "holds the plan; a trail goes to the .log.jsonl beside it; nothing written "
                      "(1fc53d5d96cc)")


def _refuse_dropped_entries(p: Path, blob: bytes) -> None:
    """An append keeps what was there (a742af217819; 9528475c replaced a 29-entry history with
    one entry under verb ``append`` and nothing fired).

    Judged only when the record's current value is a JSON list: the new value must be a list
    beginning with every current element, unchanged and in order. A record that is absent,
    unparseable, or not a list (a state.json re-projected under append) is not judged here."""
    try:
        old = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return
    if not isinstance(old, list):
        return
    new = json.loads(blob.decode("utf-8"))
    if not isinstance(new, list):
        raise Refused(f"{p} holds a list and an append must keep it one; this write is a JSON "
                      f"{type(new).__name__}; nothing written (a742af217819)")
    at = next((i for i, e in enumerate(old) if i >= len(new) or new[i] != e), None)
    if at is not None:
        raise Refused(f"{p}: this append drops or changes the entry at index {at} of the "
                      f"{len(old)} it holds; an append keeps what was there; nothing written "
                      "(a742af217819)")


def _refuse_by_rule(name: str, rel: Path, p: Path, verb: str, exists: bool) -> None:
    """A record set may name the verbs it takes, the one writer it takes them from, and that
    each member is written once (5dc4d8a0b4d2). The writer is the frame two above this one —
    the caller of ``write``/``remove`` — read as ``<repo path>:<qualname>``, so a write from
    anywhere else bumps its nose here. A ``certify`` onto a set that does not take it is
    refused too: the verb is a claim about who wrote the record."""
    rule = next((r for r in jurisdiction()["roots"].get(name, {}).get("records", [])
                 if _rule_matches(r, rel)), None) or {}
    verbs = rule.get("verbs")
    if verbs is not None and verb not in verbs:
        raise Refused(f"{p}: this record set takes only verb(s) {verbs}, not {verb!r}; "
                      "nothing written (5dc4d8a0b4d2)")
    if verb == "certify" and not (verbs and "certify" in verbs):
        raise Refused(f"{p}: verb 'certify' writes only a record set that names it; this one "
                      "does not; nothing written (5dc4d8a0b4d2)")
    if "writer" in rule:
        frame = sys._getframe(2)
        try:
            where = Path(frame.f_code.co_filename).resolve().relative_to(_REPO).as_posix()
        except ValueError:
            where = frame.f_code.co_filename
        who = f"{where}:{frame.f_code.co_qualname}"
        if who != rule["writer"]:
            raise Refused(f"{p}: only {rule['writer']} writes this record set; the caller is "
                          f"{who}; nothing written (5dc4d8a0b4d2)")
    if rule.get("write_once") and exists:
        raise Refused(f"{p}: a member of this record set is written once and it already "
                      "stands; nothing written (5dc4d8a0b4d2)")


def write(path: str | os.PathLike, content: str | bytes, *, verb: str, why: str,
          count: int = 1, mode: int | None = None) -> dict:
    """Write ``content`` to ``path``; journal it when ``path`` is a record of truth.

    Returns ``{"path", "journaled", "root", "entry"}``. A write outside the jurisdiction is
    an ordinary atomic write and says so (``journaled: False``) — the door does not refuse
    to write a scratch file, it refuses to PRETEND one is a record."""
    p = Path(path)
    p = (p if p.is_absolute() else Path.cwd() / p).resolve()
    blob = content.encode("utf-8") if isinstance(content, str) else bytes(content)
    hit = locate(p)
    if hit is None:
        _atomic_write(p, blob, mode)
        return {"path": str(p), "journaled": False, "root": None, "entry": None}
    name, root, rel = hit
    _refuse_by_rule(name, rel, p, verb, p.exists())
    if p.suffix == ".json":
        _refuse_non_canonical(p, blob)
        if p.name == "history.json":
            _refuse_history_without_floor(p, blob)
        _refuse_undeclared_keys(name, root, rel, p, blob)
        if verb == "append":
            _refuse_dropped_entries(p, blob)
    if p.suffix == ".jsonl":
        _refuse_non_append(p, blob)
    with door_lock(root):        # the record and its line, never split by a git rewrite (0f8aefbba1d0)
        before = p.read_bytes() if p.exists() else None
        if before == blob:
            # Nothing changed on disk; nothing to journal. A no-op that wrote an entry would let
            # the chain say "changed" about bytes that did not.
            return {"path": str(p), "journaled": False, "root": name, "entry": None,
                    "unchanged": True}
        entry = _entry(rel, verb, why, before, blob, count=count)
        _atomic_write(p, blob, mode)
        entry = _append(root, entry)
    return {"path": str(p), "journaled": True, "root": name, "entry": entry}


def write_json(path, doc, *, verb: str, why: str, indent: int = 2, ensure_ascii: bool = False,
               sort_keys: bool = False, newline: bool = True, mode: int | None = None) -> dict:
    body = json.dumps(doc, indent=indent, ensure_ascii=ensure_ascii, sort_keys=sort_keys)
    return write(path, body + ("\n" if newline else ""), verb=verb, why=why, mode=mode)


def _clear_read_only(p: Path) -> None:
    """The validation store writes seals read-only on purpose; Windows will not unlink a read-only
    file (WinError 5), so the door clears the bit before it removes one. Every OS, same act."""
    try:
        mode = p.stat().st_mode
    except FileNotFoundError:
        return
    if not mode & stat.S_IWRITE:
        os.chmod(p, mode | stat.S_IWRITE)


def remove(path: str | os.PathLike, *, why: str) -> dict:
    """Delete a record through the door: journaled with ``sha_after: absent``."""
    p = Path(path).resolve()
    hit = locate(p)
    if hit is None:
        _clear_read_only(p)
        p.unlink(missing_ok=True)
        return {"path": str(p), "journaled": False}
    name, root, rel = hit
    _refuse_by_rule(name, rel, p, "remove", p.exists())
    with door_lock(root):
        before = p.read_bytes() if p.exists() else None
        if before is None:
            raise Refused(f"{p} does not exist — nothing to remove")
        entry = _entry(rel, "remove", why, before, None)
        _clear_read_only(p)
        p.unlink()
        entry = _append(root, entry)
    return {"path": str(p), "journaled": True, "root": name, "entry": entry}


def rename(src: str | os.PathLike, dst: str | os.PathLike, *, why: str) -> dict:
    """Move a record: one ``remove`` of the source and one ``rename`` write of the target, so
    the target's chain starts with the bytes it arrived with."""
    s = Path(src).resolve()
    blob = s.read_bytes()
    out_rm = remove(s, why=why)
    out_wr = write(dst, blob, verb="rename", why=why)
    return {"removed": out_rm, "written": out_wr}


# ---------------------------------------------------------------------------
# GENESIS: every record that predates the door gets its first entry


def iter_records(name: str, root: Path):
    rules = jurisdiction()["roots"].get(name, {}).get("records", [])
    for p in sorted(root.rglob("*")):
        if not p.is_file() or ".git" in p.parts:
            continue
        rel = p.relative_to(root)
        if any(_rule_matches(r, rel) for r in rules):
            yield rel, p


def genesis(name: str, *, why: str) -> dict:
    """Journal the standing bytes of every record not yet journaled in ``name``'s root.
    Re-runnable: a record already journaled is skipped, so the second run is a no-op and
    the first run after a new class enters the jurisdiction covers only the newcomers."""
    root = roots()[name]
    known = {e["path"] for e in read_journal(root)}
    n = 0
    for rel, p in iter_records(name, root):
        if rel.as_posix() in known:
            continue
        blob = p.read_bytes()
        _append(root, _entry(rel, "genesis", why, None, blob))
        n += 1
    return {"root": name, "journaled": n}


# ---------------------------------------------------------------------------
# THE COMMIT CHECK: what the pre-commit hook asks


def _git(root: Path, *args: str) -> bytes:
    return subprocess.run(["git", "-C", str(root), *args], check=True,
                          capture_output=True).stdout


def _staged(root: Path) -> list[tuple[str, str, str | None]]:
    """``(status, path, old_path)`` for every staged change."""
    raw = _git(root, "diff", "--cached", "--name-status", "-z", "-M")
    parts = raw.split(b"\0")
    out, i = [], 0
    while i < len(parts) and parts[i]:
        status = parts[i].decode()
        if status[0] in "RC":
            out.append((status[0], parts[i + 2].decode(), parts[i + 1].decode()))
            i += 3
        else:
            out.append((status[0], parts[i + 1].decode(), None))
            i += 2
    return out


def check_staged(name: str) -> list[str]:
    """Every refusal for the staged tree of root ``name``, in one pass. Empty means commit.

    For each staged record: an added or modified record's STAGED blob must hash to the
    journal's last ``sha_after`` for its path; a deleted record's last entry must say
    ``absent``; a rename is a delete of the old path and an add of the new. The chain
    itself is replayed. Then the journal is staged alongside, because a commit that carried
    the records and not the journal that explains them is half a record."""
    root = roots()[name]
    rules = jurisdiction()["roots"].get(name, {}).get("records", [])
    faults = [f"journal chain: {f}" for f in verify_chain(root)]
    entries = read_journal(root)
    fix = "cairn artifact hand-edit <path> --why '<what changed and why>'"
    for status, path, old in _staged(root):
        rel = Path(path)
        targets = [(status, rel)]
        if old is not None:
            targets = [("D", Path(old)), ("A", rel)]
        for st, r in targets:
            if not any(_rule_matches(rule, r) for rule in rules):
                continue
            last = last_sha(entries, r.as_posix())
            if st == "D":
                if last != "absent":
                    faults.append(f"{r}: staged for deletion but the journal's last entry says "
                                  f"it stands ({(last or 'never journaled')[:12]}) — remove it "
                                  f"through the door: cairn artifact remove {r} --why '...'")
                continue
            staged_blob = _git(root, "show", f":{r.as_posix()}")
            have = _sha(staged_blob)
            if last is None:
                faults.append(f"{r}: staged but NEVER journaled — it was written around the door. "
                              f"Fix: {fix}")
            elif last != have:
                faults.append(f"{r}: staged bytes {have[:12]} are not the journal's last "
                              f"sha_after {last[:12]} — changed around the door. Fix: {fix}")
    if not faults:
        jp = journal_path(root)
        if jp.exists():
            _git(root, "add", "--", jp.name)
    return faults


# A COMMIT TAKES ONLY THE PATHS ITS AUTHOR NAMES (ticket 23c822fe8095). Sessions share one
# working tree and one index, so a commit of the shared index carries whatever another session
# staged. Inside a pre-commit hook git names the index it hands over in GIT_INDEX_FILE, measured
# on Linux and git for Windows: plain commit and --amend = ``index``, -a/-i = ``index.lock``,
# ``git commit -- <paths>`` = a temp ``next-index-<pid>.lock`` built from HEAD plus the paths.
ONLY_INDEX_PREFIX = "next-index-"
_SEQUENCER_HEADS = ("MERGE_HEAD", "CHERRY_PICK_HEAD", "REVERT_HEAD")
PATH_COMMIT = "git commit -m ... -- <paths>"


def _git_dir(root: Path) -> Path:
    return Path(_git(root, "rev-parse", "--absolute-git-dir").decode().strip())


def check_shared_index(root: Path, index_file: str | None) -> list[str]:
    """A fault when a hook was handed a shared index (anything but git's --only temp index),
    unless a merge, cherry-pick or revert is in progress: those commit what git itself staged.
    ``index_file`` None (a hand `cairn artifact check`, not a hook) is never a fault."""
    if not index_file or Path(index_file).name.startswith(ONLY_INDEX_PREFIX):
        return []
    gd = _git_dir(root)
    if any((gd / h).exists() for h in _SEQUENCER_HEADS):
        return []
    return [f"commit names its paths: {PATH_COMMIT}; another session's staged work is in "
            f"this index ({Path(index_file).name}), and a commit of it would carry that work"]


def _index_entries(root: Path, index_file: str | os.PathLike) -> dict[str, tuple[str, str]]:
    out = subprocess.run(["git", "-C", str(root), "ls-files", "-s", "-z"], check=True,
                         capture_output=True, env={**os.environ, "GIT_INDEX_FILE": str(index_file)}).stdout
    entries = {}
    for rec in out.decode("utf-8", "surrogateescape").split("\0"):
        if not rec:
            continue
        meta, path = rec.split("\t", 1)
        mode, sha, stage = meta.split()
        if stage == "0":
            entries[path] = (mode, sha)
    return entries


def _head_entries(root: Path) -> dict[str, tuple[str, str]]:
    r = subprocess.run(["git", "-C", str(root), "ls-tree", "-r", "-z", "HEAD"], capture_output=True)
    if r.returncode:
        return {}  # the first commit: HEAD has no tree yet
    entries = {}
    for rec in r.stdout.decode("utf-8", "surrogateescape").split("\0"):
        if rec:
            meta, path = rec.split("\t", 1)
            mode, _kind, sha = meta.split()
            entries[path] = (mode, sha)
    return entries


def refresh_shared_index(root: Path, index_file: str | None) -> list[str]:
    """After a path commit's hook staged into the temp index, bring the shared index along.

    Under ``git commit -- <paths>`` git holds the shared index as ``index.lock`` (it becomes
    ``index`` when the commit lands) and has already written the named paths into it. A path
    the HOOK staged (the journal, a reseal's seals) went only into the temp index, so the shared
    index would keep its pre-commit blob and `git status` would show a staged change nobody made.
    Each path the commit writes (temp index differs from HEAD) whose shared entry still equals
    HEAD's is set to the temp blob. A shared entry that differs from HEAD is another session's
    staging and is left alone. It runs inside pre-commit, so nothing hangs off post-commit
    (Q#60). Returns the refreshed paths."""
    if not index_file or not Path(index_file).name.startswith(ONLY_INDEX_PREFIX):
        return []
    shared = _git_dir(root) / "index.lock"
    if not shared.exists():
        return []
    temp, head, now = _index_entries(root, index_file), _head_entries(root), _index_entries(root, shared)
    lines, done = [], []
    for path in sorted(set(temp) | set(head)):
        want = temp.get(path)
        if want == head.get(path) or now.get(path) != head.get(path) or now.get(path) == want:
            continue
        lines.append(f"{want[0]} {want[1]}\t{path}" if want else f"0 {'0' * len(head[path][1])}\t{path}")
        done.append(path)
    if lines:
        subprocess.run(["git", "-C", str(root), "update-index", "-z", "--index-info"], check=True,
                       input=("\0".join(lines) + "\0").encode("utf-8", "surrogateescape"),
                       capture_output=True, env={**os.environ, "GIT_INDEX_FILE": str(shared)})
    return done


# A records commit's title is a record too: git log is read as the history of crossings, so a
# title naming a state the ticket never reached is a false record (ticket cdac80129536).
_RECORDS_TITLE = re.compile(r"^records:\s+([0-9a-f]{12})\s+([A-Z]+)\b")


def check_title(subject: str) -> list[str]:
    """Faults for a commit subject of the shape ``records: <ticket> <STATE>``. When STATE is a
    state of that ticket's workflow, the ticket's cursor (the bracketed state in its
    workflow_and_state, read from the CairnCommons root) must be STATE. A word that is no state
    of the workflow (cast, seal, hollow) and every other subject shape pass untouched."""
    m = _RECORDS_TITLE.match(subject.strip())
    if not m:
        return []
    tid, word = m.groups()
    tickets = roots()["CairnCommons"] / "tickets"
    from cairn.tools.base.ticket_file import plans_of, read_ticket
    hits = plans_of(tid, tickets)
    if len(hits) != 1:
        return [f"title names ticket {tid}, but {tickets} holds {len(hits)} plan(s) for it"]
    try:
        wf = str(read_ticket(hits[0]).get("workflow_and_state") or "")
    except (OSError, ValueError) as exc:
        return [f"title names ticket {tid}, whose plan {hits[0].name} is unreadable ({exc})"]
    if word not in re.findall(r"[A-Z]{2,}", wf.split(":", 1)[-1]):
        return []
    cur = re.search(r"\[([A-Z]+)", wf)
    cursor = cur.group(1) if cur else None
    if cursor != word:
        return [f"title says {tid} {word}, but its cursor stands at {cursor} ({wf}) — "
                f"title the commit by the state it landed, not the one it attempted"]
    return []


# ---------------------------------------------------------------------------
# HAND EDITS: parked, then approved by a measured hand


def parked_dir() -> Path:
    if _diagnostic_roots is not None and "parked" in _diagnostic_roots:
        return _diagnostic_roots["parked"]
    env = os.environ.get("CAIRN_ARTIFACT_ROOTS")
    if env and "parked" in json.loads(env):
        return Path(json.loads(env)["parked"])
    # The address is RESOLVED, never spelled (address_is_resolved_never_spelled): the parks
    # berth under the operator instance's held copy of this tool, Law 6's shape for tool state.
    from cairn.tools.base.address import tool_path
    return tool_path("operator", 0, "artifact") / "parked"


def _head_bytes(root: Path, rel: Path) -> bytes | None:
    try:
        return _git(root, "show", f"HEAD:{rel.as_posix()}")
    except subprocess.CalledProcessError:
        return None


def park_hand_edit(path: str | os.PathLike, *, why: str) -> dict:
    """A record was changed around the door. Park the changed bytes for Akien, and put the
    record back to its last journaled bytes so nothing unapproved stands as truth.

    The last journaled bytes are recovered from HEAD when the journal's last sha matches
    HEAD (the ordinary case) — the door never had the bytes, git did."""
    p = Path(path).resolve()
    hit = locate(p)
    if hit is None:
        raise Refused(f"{p} is not a record of truth — edit it as you like")
    name, root, rel = hit
    if not (why or "").strip():
        raise Refused("a parked edit with no why is the change this door exists to explain — say why")
    entries = read_journal(root)
    last = last_sha(entries, rel.as_posix())
    proposed = p.read_bytes() if p.exists() else None
    if last is not None and last == _sha(proposed):
        raise Refused(f"{rel} already matches the journal — nothing to park")
    head = _head_bytes(root, rel)
    if last is None:
        standing = None                       # a new record: nothing stands
    elif last == "absent":
        standing = None
    elif head is not None and _sha(head) == last:
        standing = head
    else:
        raise Refused(f"{rel}: the journal's last sha {last[:12]} matches neither HEAD nor the "
                      f"working copy — the standing bytes cannot be recovered; this is a finding "
                      f"for Akien, not a park")
    park_id = uuid.uuid4().hex[:12]
    pd = parked_dir()
    pd.mkdir(parents=True, exist_ok=True)
    record = {
        "id": park_id, "root": name, "path": rel.as_posix(), "why": why, "at": _now(),
        "parked_by": caller(), "stack": _stack(),
        "sha_standing": _sha(standing), "sha_proposed": _sha(proposed),
        "proposed": proposed.decode("utf-8", "surrogateescape") if proposed is not None else None,
        "standing": standing.decode("utf-8", "surrogateescape") if standing is not None else None,
    }
    (pd / f"{park_id}.json").write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n",
                                        encoding="utf-8")
    if standing is None:
        if p.exists():
            p.unlink()
    else:
        _atomic_write(p, standing, None)
    return {"parked": park_id, "path": str(pd / f"{park_id}.json"), "record": rel.as_posix(),
            "restored_to": record["sha_standing"]}


def parked() -> list[dict]:
    pd = parked_dir()
    if not pd.is_dir():
        return []
    return [json.loads(f.read_text(encoding="utf-8")) for f in sorted(pd.glob("*.json"))]


def _park(park_id: str) -> tuple[Path, dict]:
    for f in sorted(parked_dir().glob("*.json")):
        if f.stem.startswith(park_id):
            return f, json.loads(f.read_text(encoding="utf-8"))
    raise Refused(f"no parked edit with id {park_id!r} — `cairn artifact parked` lists them")


def approve(park_id: str, words: str) -> dict:
    """Akien's sign-off, MEASURED: the approving process must sit in an ``akien`` scope. His
    words ride the journal entry as the ruling; a CC session cannot type them on his behalf
    because it does not sit where he sits."""
    who = caller()
    if who["class"] != "akien":
        raise Refused(f"approve refused: the caller is {who['class']} ({who['cgroup']}), and only "
                      f"a hand at a terminal — Akien's — may approve a hand edit")
    if not (words or "").strip():
        raise Refused("approve needs his words — they are the ruling the journal records")
    f, rec = _park(park_id)
    root = roots()[rec["root"]]
    p = root / rec["path"]
    proposed = None if rec["proposed"] is None else rec["proposed"].encode("utf-8", "surrogateescape")
    before = p.read_bytes() if p.exists() else None
    if _sha(before) != rec["sha_standing"]:
        raise Refused(f"{rec['path']} moved since it was parked ({_sha(before)[:12]} vs "
                      f"{rec['sha_standing'][:12]}) — park it again")
    extra = {"approved_by_words": words, "park": rec["id"], "parked_by": rec["parked_by"],
             "parked_why": rec["why"]}
    if proposed is None:
        entry = _entry(Path(rec["path"]), "hand-edit", rec["why"], before, None, extra=extra)
        p.unlink(missing_ok=True)
    else:
        entry = _entry(Path(rec["path"]), "hand-edit", rec["why"], before, proposed, extra=extra)
        _atomic_write(p, proposed, None)
    entry = _append(root, entry)
    f.unlink()
    return {"approved": rec["id"], "path": str(p), "entry": entry}


def refuse(park_id: str, words: str) -> dict:
    """The parked edit dies; the record already stands at its journaled bytes."""
    if not (words or "").strip():
        raise Refused("refuse needs words — a refusal with no reason teaches nobody")
    f, rec = _park(park_id)
    rec["refused"] = {"at": _now(), "by": caller(), "words": words}
    f.unlink()
    return {"refused": rec["id"], "path": rec["path"], "words": words}
