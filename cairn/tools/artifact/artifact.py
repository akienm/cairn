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

import fcntl
import fnmatch
import hashlib
import json
import os
import re
import subprocess
import sys
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path

from cairn.tools.cgroup.cgroup import cgroup_of

_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parents[2]
_JURISDICTION = _HERE / "jurisdiction.json"

VERBS = ("genesis", "cast", "append", "compile", "seal", "raise", "clear", "ruling", "slate", "question", "answer",
         "idea", "charter", "phase", "hand-edit", "rename", "remove", "bulk", "write",
         # ``rehearse`` joined 2026-09-15 (ticket cf80bdb57205): a rehearsal record — the cheapest
         # reader's converged build tree over a ticket, under CairnCommons/rehearsals/.
         "rehearse")

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
    """The caller class from a cgroup path. Pure, so a proof can pin it over text."""
    leaf = (cgroup or "").rstrip("/").rsplit("/", 1)[-1]
    if _GATE.match(leaf):
        cls, unit = "gate", leaf
    elif _CC.match(leaf):
        cls, unit = "cc", leaf
    elif _AKIEN.match(leaf):
        cls, unit = "akien", leaf
    else:
        cls, unit = "unknown", None
    return {"class": cls, "cgroup": cgroup, "unit": unit}


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


def caller() -> dict:
    """This process's caller record — kernel truth, read now, never cached.

    The class is decided over the ANCESTRY, not the leaf alone: a ``cc`` anywhere up the
    tree makes the caller cc, because a process CC started is CC's hand whatever scope it
    sits in; otherwise the leaf decides. The chain rides the entry so a reader can see
    how the class was reached."""
    chain = ancestry()
    me = classify(chain[0]["cgroup"] if chain else cgroup_of("self"))
    if me["class"] != "cc" and any(a["class"] == "cc" for a in chain[1:]):
        cc = next(a for a in chain[1:] if a["class"] == "cc")
        me = {"class": "cc", "cgroup": me["cgroup"], "unit": classify(cc["cgroup"])["unit"],
              "via_ancestor": cc["pid"]}
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


def _append(root: Path, entry: dict) -> dict:
    """Append under a lock: read the tail, chain, write. Two writers cannot fork the chain."""
    jp = journal_path(root)
    jp.parent.mkdir(parents=True, exist_ok=True)
    with open(jp, "a+", encoding="utf-8") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
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
    return entry


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
    try:
        tmp.write_bytes(blob)
        os.chmod(tmp, mode)
        os.replace(tmp, path)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise


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


def remove(path: str | os.PathLike, *, why: str) -> dict:
    """Delete a record through the door: journaled with ``sha_after: absent``."""
    p = Path(path).resolve()
    hit = locate(p)
    if hit is None:
        p.unlink(missing_ok=True)
        return {"path": str(p), "journaled": False}
    name, root, rel = hit
    before = p.read_bytes() if p.exists() else None
    if before is None:
        raise Refused(f"{p} does not exist — nothing to remove")
    entry = _entry(rel, "remove", why, before, None)
    p.unlink()
    return {"path": str(p), "journaled": True, "root": name, "entry": _append(root, entry)}


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
