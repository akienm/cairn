"""COUNTERS — read a skill's firings where they ALREADY live, per its charter's declaration.

THE MEASUREMENT THAT PRODUCED THIS FILE (2026-08-04). ``skilldial`` printed six of eleven
skills as *not countable*. That reading was wrong about five of them. Their firings were
recorded all along, just not in the seam's trace:

    commit     192   git log's Co-Authored-By trailer      (a PROXY — overcounts, said so)
    chart      170   ~/.cairn/devices/chart/0/packets/     (exact, and per-door)
    note         3   CairnCommons/notes/, template-conforming records (25 files, 3 conform)
    moreabout    2   moreabout_signal nodes in the tenant trees
    challenge  3/10  the `challenge` field on /intent's berths
    sail         —   nothing, anywhere. The only genuinely dark one.

Against ~408 real firings, the roster could see 19. The obvious repair — give the six an
``input_contract`` so they ride the seam — is the Law 1 defect wearing a helpful face: six
new doors built to re-derive counts that exist, and for ``chart`` and ``commit`` a SECOND
berth per firing, so "how many times did it fire" would acquire two answers that can
disagree. A skill is counted where it already leaves a mark.

So the charter declares where its own count lives (``counted_by``) and this module reads
it. That keeps the roster a re-derivation and not a registry: nothing enrols, nothing is
stored, and the declaration sits beside the skill it describes (Law 5).

**A reader may return None. It may never return 0 to mean "could not look."** An
unreachable database, a missing directory and a git that will not run are all *no
measurement*, and every one of them travels back as ``unreadable`` with its reason
attached (Law 7 at a diagnostic surface). Zero is a fact and it has to be earned.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

# THE ROOT TABLE AND ITS RESOLVER MOVED DOWN TO cairn/base/address.py ON 2026-08-12 (ticket
# one-owner-for-the-instance-address). They were BORN here, for the counted_by address, and
# then the rest of the system turned out to need the same table: ten sites in class-space were
# spelling ~/.cairn/devices/<device>/<instance> by hand, and base could not stand on a table
# living at skill_block's address. What is imported below is the same code, at a floor that
# base's rungs can reach — so the two faces of the table (a charter author's rooted token, a
# caller's device+instance) are one table and are pinned to each other by a proof tooth
# (cairn/base/proofs/test_instance_address.py).
#
# THE NAMES STAY EXPORTED FROM THIS MODULE ON PURPOSE. counters.resolve is what a charter's
# counted_by address is read by, and counters.Unreadable is the exception its callers catch —
# re-export keeps both at the address they already have, and keeps the CLASS IDENTITY of
# Unreadable single, so `except counters.Unreadable` still catches what base raises.
from cairn.base.address import ROOTS as _ROOTS  # noqa: F401  (re-exported vocabulary)
from cairn.base.address import Unreadable, resolve  # noqa: F401  (re-exported: see above)

_REPO = _ROOTS["repo"]

_STAMP = re.compile(r"(\d{8})T(\d{6})")


def _iso(stamp: str) -> str | None:
    """``20260803T163639`` -> ``2026-08-03T16:36:39``. The filename IS the clock here."""
    m = _STAMP.search(stamp)
    if not m:
        return None
    d, t = m.groups()
    return f"{d[:4]}-{d[4:6]}-{d[6:]}T{t[:2]}:{t[2:4]}:{t[4:]}"


# ── the readers ──────────────────────────────────────────────────────────────
#
# Four, because there are four physically different stores, not because four felt like
# a good number. Collapsing them would mean building the unified event bus none of these
# skills asked for.


def _read_files(spec: dict, *, roots=None, **_) -> dict:
    """JSON records in a directory. Optionally grouped by filename prefix (chart's eight
    doors), optionally filtered to those conforming to a store template (note's).

    The template filter is the tooth: 25 files sit in ``CairnCommons/notes/`` and 3 are
    notes. Counting the directory would have reported /note as the second-busiest skill
    in Cairn on the strength of 22 hand-written design documents that share its folder.
    """
    d = resolve(spec["address"], roots)
    if not d.is_dir():
        raise Unreadable(f"{d} does not exist — nothing to count, and nothing counted")

    files = [p for p in sorted(d.glob("*.json")) if not p.name.startswith("_")]

    if spec.get("conform_to_template"):
        charter = d / "_charter+why.json"
        if not charter.is_file():
            raise Unreadable(
                f"{d} declares conform_to_template but has no _charter+why.json to "
                "conform TO — the filter cannot be applied, so no count is honest here"
            )
        tmpl = json.loads(charter.read_text()).get("template") or {}
        required = [k for k, v in tmpl.items() if "optional" not in str(v).lower()]
        kept = [p for p in files if _conforms(p, required)]
        detail = {"in_directory": len(files), "conforming": len(kept),
                  "required_fields": required}
        dates = [_record_date(p) for p in kept]
        return {"firings": len(kept),
                "last_fired": max([x for x in dates if x], default=None),
                "detail": detail}

    if spec.get("group_by_prefix"):
        by_door: dict[str, int] = {}
        for p in files:
            by_door[p.name.split("-")[0]] = by_door.get(p.name.split("-")[0], 0) + 1
        stamps = [_iso(p.name) for p in files]
        return {"firings": len(files),
                "last_fired": max([s for s in stamps if s], default=None),
                "detail": dict(sorted(by_door.items(), key=lambda kv: -kv[1]))}

    stamps = [_iso(p.name) for p in files]
    return {"firings": len(files),
            "last_fired": max([s for s in stamps if s], default=None),
            "detail": None}


def _conforms(path: Path, required: list[str]) -> bool:
    try:
        rec = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return False
    return isinstance(rec, dict) and all(k in rec for k in required)


def _record_date(path: Path) -> str | None:
    try:
        return json.loads(path.read_text()).get("date")
    except (OSError, json.JSONDecodeError):
        return None


def _read_git_trailer(spec: dict, *, repo: Path | None = None, **_) -> dict:
    """Commits carrying a trailer. A PROXY, and the charter says so in its own words —
    every /commit firing makes such a commit, but so does every commit made without the
    skill, so this is an upper bound. An upper bound with its bias named is a
    measurement; a dash would have been less true, not more careful."""
    pattern = spec["address"].split(":", 1)[1]
    root = repo or _REPO
    try:
        out = subprocess.run(
            ["git", "log", "--format=%aI%x00%b%x01"],
            cwd=str(root), capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError) as exc:
        raise Unreadable(f"git would not run in {root}: {exc}")
    if out.returncode != 0:
        raise Unreadable(f"git log exited {out.returncode}: {out.stderr.strip()[:200]}")

    dates = []
    for entry in out.stdout.split("\x01"):
        when, _, body = entry.partition("\x00")
        if pattern in body:
            dates.append(when.strip())
    return {"firings": len(dates), "last_fired": max(dates, default=None),
            "detail": {"proxy": True, "pattern": pattern,
                       "bias": "upper bound — counts commits CC authored, not /commit firings"}}


def _read_tree_nodes(spec: dict, *, connect=None, **_) -> dict:
    """Nodes deposited into the tenant trees with a given provenance kind.

    The one reader that can find the store *absent* rather than empty, which is why it is
    the one that most needs to refuse to say 0. A stopped database and a door nobody
    fired look identical to a count and completely different to a decision.
    """
    kind = spec["provenance_kind"]
    try:
        from cairn.db_domain import store as _store
        opener = connect or _store.connect
        with opener() as conn:
            cur = conn.cursor()
            cur.execute("select table_name from information_schema.tables "
                        "where table_schema='public' and table_name like '%_nodes' order by 1")
            tables = [r[0] for r in cur.fetchall()]
            total, per, dates = 0, {}, []
            for t in tables:
                try:
                    cur.execute(
                        f"select count(*), max(provenance->>'date') from {t} "
                        "where provenance->>'kind' = %s", (kind,))
                    n, last = cur.fetchone()
                except Exception:                      # a tenant table without provenance
                    conn.rollback()
                    continue
                if n:
                    total += n
                    per[t] = n
                    if last:
                        dates.append(last)
            return {"firings": total, "last_fired": max(dates, default=None),
                    "detail": {"provenance_kind": kind, "per_tree": per,
                               "trees_searched": len(tables)}}
    except Unreadable:
        raise
    except Exception as exc:
        raise Unreadable(
            f"the tree store could not be read ({type(exc).__name__}: {exc}). "
            "This is NOT zero signals — it is no measurement, and a disuse call made "
            "on an unreachable store is a call made on nothing."
        )


def _read_rides_host(spec: dict, *, berths: Path | None = None, roots=None, **_) -> dict:
    """A skill that fires INSIDE another skill's step, counted by the field it leaves on
    the host's packet. /challenge is the case: it has no door of its own because it has
    no moment of its own — it runs on the host's packet, at the host's gate."""
    d = Path(berths) if berths is not None else resolve(spec["address"], roots)
    if not d.is_dir():
        raise Unreadable(f"{d} does not exist — the host has never berthed a firing")
    field = spec["host_field"]
    hits, total, whens = 0, 0, []
    for p in sorted(d.glob("*.json")):
        try:
            rec = json.loads(p.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        total += 1
        if (rec.get("answers") or {}).get(field):
            hits += 1
            if rec.get("when"):
                whens.append(rec["when"])
    return {"firings": hits, "last_fired": max(whens, default=None),
            "detail": {"host": spec.get("host_skill"), "host_field": field,
                       "host_firings": total,
                       "note": "hits < host_firings means the host gate predates the "
                               "requirement; those records are permanent (Law 7)"}}


READERS = {
    "files": _read_files,
    "git-trailer": _read_git_trailer,
    "tree-nodes": _read_tree_nodes,
    "rides-host": _read_rides_host,
}


def count(spec: dict, **kw) -> dict:
    """Dispatch on the charter's declared reader.

    Returns ``{firings, last_fired, detail}`` or ``{unreadable: <why>}``. Never both, and
    never a zero standing in for either.
    """
    reader = spec.get("reader")
    if reader == "none":
        # THE CLAIM THIS BRANCH MAY NOT MAKE (2026-08-11, Akien: the charter said /sail
        # left no record anywhere, and 32 MANDATORY verdict berths said otherwise). A
        # charter declaring no reader is a fact about THIS ROSTER — nothing here can
        # count the firings. It is not a fact about the world, and the two were being
        # collapsed into one sentence that read as the second. The charter's own
        # what_it_counts is the standing claim; this surface quotes it and never
        # replaces it, because the charter is where a correction can land.
        said = str(spec.get("what_it_counts") or "").strip()
        return {"unreadable": (
            "the charter declares NO READER, so this roster cannot count it. That says "
            "nothing about whether a record exists — only that none is declared here. "
            + (f"The charter's own claim: {said}" if said else
               "And the charter is silent on what it counts, which is the defect to fix "
               "first: an undeclared reader plus an unstated claim is a skill nobody can "
               "say anything about."))}
    fn = READERS.get(reader)
    if fn is None:
        return {"unreadable": (
            f"counted_by.reader {reader!r} is not one of {sorted(READERS)} plus 'none'. "
            "A charter naming a reader nobody implements is a charter defect, and it "
            "reads as no measurement rather than as zero.")}
    try:
        return fn(spec, **kw)
    except Unreadable as exc:
        return {"unreadable": str(exc)}


__all__ = ["READERS", "Unreadable", "count", "resolve"]
