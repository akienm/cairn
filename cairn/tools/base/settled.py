"""SETTLED — an answer about a tree, kept until the tree moves.

Law 1 names the defect and gives this module its word: *"the resolver is spent on the novel,
not on re-deriving the settled. Every answered question becomes structure; re-deriving a
settled answer is a defect."* The ground loop was re-deriving settled answers on a
60-second clock.

AKIEN'S RED, 2026-09-07 (ticket 9579a6f9cec6): *"i can't imagine why we should need to parse
all class space every 60 seconds. that's not efficient."* Measured, the beat cost 104.8s;
``once`` (in ``probe.py``) took the intra-pulse triple-derivation out and left 42.8s of
trigger cost, which is corpus scans re-run against a world that had not moved. A census of
one beat found ``orient.device_census`` called 14 times for 9.3s and ``address_rule.scan``
twice for 2.3s — each of them a full AST walk of class-space, each answering a question whose
inputs are files on disk.

WHAT ``once`` IS AND THIS IS NOT. ``once`` memoizes for the span of ONE PULSE and dies with
it, so it needs no notion of staleness at all — a beat is short and the world is held still
inside it by assumption. This memo lives ACROSS pulses, so it owes an answer to "is it still
true", and the answer must be measured rather than assumed (Law 3). Two helpers, two
lifetimes, and deliberately not one: a single "cache" with a mode flag would put the
staleness question where a caller could forget it.

THE TOKEN IS A STAT SWEEP, and the numbers are why. Over ``cairn/`` — 806 files —
``os.walk`` reading mtime and size costs **5.9ms**, against 664ms for one ``device_census``
and 1,108ms for one ``address_rule.scan``. A ``git rev-parse`` + ``git status --porcelain``
fingerprint measured 6.9ms, so it was not chosen for speed: the stat sweep sees files git
is told to ignore, needs no subprocess, and works in a temp root a proof built — and the
first two matter, because a scan blinded to a file the world can still read is a watch
reporting on a world it cannot see. Size rides along with mtime so a same-nanosecond
rewrite of different content is still caught.

WHAT IT DOES NOT SEE, declared here rather than discovered later:
  - A CHANGE OUTSIDE THE FINGERPRINTED TREE. A scan whose answer depends on two roots must
    fingerprint both, or it must not use this. That is the caller's declaration to make, and
    it is why ``root`` is an explicit argument and never inferred.
  - A CHANGE THE FILESYSTEM DID NOT TIMESTAMP. On a filesystem with coarse mtime, a write
    landing in the same tick as the last sweep and leaving the size identical is invisible.
    ext4 here reports nanoseconds; a coarser host is a real limit, and the disposition when
    one appears is to escalate, not to widen this quietly (Law 10).

A RAISE IS NOT REMEMBERED. A scan that blew up is not an answer, and remembering one would
turn a transient read failure into a permanent lie — the same rule ``once`` holds, for the
same reason, and here it matters more because there is no beat boundary to clear it.
"""
from __future__ import annotations

import os
from collections.abc import Callable

#: ``(key, root) -> (token, answer)``. Bounded by the number of distinct scans and roots a
#: process touches, which is small and does not grow with the corpus.
_SETTLED: dict[tuple[str, str], tuple] = {}

#: How many times a guarded scan has actually RUN (not been served). A proof asserts this
#: does not move over an unchanged tree — the only way to tell a memo that works from one
#: that quietly re-derives, since both return the same answer.
DERIVATIONS = 0

#: Never fingerprinted: generated, and it moves whenever python merely IMPORTS the tree, so
#: including it would expire the memo on activity that changed no source.
_SKIP_DIRS = {"__pycache__", ".git", ".pytest_cache", ".mypy_cache", "node_modules"}


def tree_fingerprint(root) -> tuple:
    """What the tree at ``root`` looks like right now: one entry per file, name + mtime_ns +
    size, in a stable order. Measured at 5.9ms over 806 files.

    A tree that cannot be walked fingerprints as empty rather than raising — the SCAN is the
    surface that should be loud about an unreadable corpus (``device_census`` refuses on one
    already), and a fingerprint that raised would take down every caller including the ones
    whose answer does not depend on the unreadable part."""
    entries = []
    for dirpath, dirnames, filenames in os.walk(str(root)):
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS]
        dirnames.sort()
        for name in sorted(filenames):
            path = os.path.join(dirpath, name)
            try:
                st = os.stat(path)
            except OSError:
                continue
            entries.append((path, st.st_mtime_ns, st.st_size))
    return tuple(entries)


def settled(key: str, root, compute: Callable[[], object]):
    """``compute()``, remembered under ``key`` until the tree at ``root`` moves.

    ``key`` names the question and ``root`` names the world it is asked about; together they
    are the memo's address, so two scans over one tree do not collide and one scan over two
    trees keeps two answers. Both are explicit because a memo that guessed its own world is
    exactly the thing that goes stale without saying so."""
    global DERIVATIONS
    slot = (key, str(root))
    token = tree_fingerprint(root)
    remembered = _SETTLED.get(slot)
    if remembered is not None and remembered[0] == token:
        return remembered[1]
    answer = compute()          # a raise propagates and is NOT remembered
    _SETTLED[slot] = (token, answer)
    DERIVATIONS += 1
    return answer


def forget(key: str | None = None) -> int:
    """Drop remembered answers — all of them, or every root of one ``key``. For a caller that
    has just changed the world through a door the fingerprint cannot see, and for proofs that
    want a cold start. Returns how many were dropped, so a caller that expected to clear
    something can tell that it did."""
    if key is None:
        n = len(_SETTLED)
        _SETTLED.clear()
        return n
    doomed = [s for s in _SETTLED if s[0] == key]
    for s in doomed:
        del _SETTLED[s]
    return len(doomed)
