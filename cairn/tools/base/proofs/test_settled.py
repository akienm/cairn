"""SETTLED — an answer about a tree, kept until the tree moves, and never a moment longer.

Ticket ``9579a6f9cec6`` (2026-09-07). Akien's red: *"i can't imagine why we should need to
parse all class space every 60 seconds. that's not efficient."* Measured over one ground-loop
beat: ``orient.device_census`` ran 14 times for 9.3s and ``address_rule.scan`` twice for 2.3s,
both full AST walks of a corpus that had not changed between the first call and the last.

A CROSS-PULSE MEMO IS A SECOND COPY OF A MEASUREMENT, so every tooth here is aimed at a way
one lies, and none at how fast it is. A fast wrong census is worse than a slow right one —
it is a watch reporting confidently on a world it has stopped looking at (Law 3).

WHAT THIS PROVES:
  - IT REMEMBERS. The only claim invisible in the answers, since a memo that silently
    re-derives returns exactly what a working one returns. ``DERIVATIONS`` is the only
    surface that can tell them apart, which is why it exists.
  - EVERY SHAPE OF CHANGE EXPIRES IT — a new file, a deleted file, an EDITED file, and an
    edit that leaves the byte count identical. The last is the sharp one: mtime alone
    catches it here only because this filesystem timestamps in nanoseconds, and size is in
    the fingerprint so a coarser one still cannot hide a resize.
  - TWO TREES KEEP TWO ANSWERS, and a change to one does not expire the other. A memo that
    keyed on the question alone would serve a proof's temp corpus as the live one.
  - TWO QUESTIONS OVER ONE TREE KEEP TWO ANSWERS.
  - A RAISE IS NOT REMEMBERED. There is no beat boundary to clear it, so a remembered
    failure would be permanent.
  - ``forget`` ACTUALLY DROPS, by key and wholesale, and says how many — a caller that
    meant to clear something can tell that it did.
  - GENERATED DIRECTORIES ARE NOT FINGERPRINTED. ``__pycache__`` moves whenever python
    merely IMPORTS the tree, so counting it would expire the memo on activity that changed
    no source — a memo that expires on its own use is not one.
  - AND THE TWO LIVE SCANS ANSWER IDENTICALLY WARM AND COLD, end to end, because "the
    helper is sound" and "the corpus scans still tell the truth" are two different claims.
"""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

from cairn.tools.base import settled as S
from cairn.tools.base.settled import forget, settled, tree_fingerprint
from cairn.devices.tester.scratch import scratch_dir


class _Counted:
    """A scan that reports how many times it has actually been derived."""

    def __init__(self, tag="scan"):
        self.tag, self.calls = tag, 0

    def __call__(self):
        self.calls += 1
        return {"tag": self.tag, "derived": self.calls}


def _tree(*names) -> str:
    # scratch_dir, NOT a bare mkdtemp. The tester's corpus scan
    # (test_scratch.py::test_no_proof_in_this_repo_calls_mkdtemp_bare) reds any proof that
    # reaches the system temp directory directly, because what it makes there outlives the
    # run — that is how 3581 stale directories accumulated. Every call site here already
    # rmtree's in a ``finally``; the swept directory is the belt to that pair of braces, and
    # it is what the scan can actually see.
    root = str(scratch_dir("cairn-settled-proof-"))
    for n in names:
        p = Path(root) / n
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(f"# {n}\n")
    return root


def test_it_remembers_over_an_unchanged_tree():
    root, scan = _tree("a.py", "b.py"), _Counted()
    try:
        first = settled("q", root, scan)
        for _ in range(30):
            assert settled("q", root, scan) == first
        assert scan.calls == 1, (
            f"derived {scan.calls} times over an unchanged tree — that is a scan wearing a "
            "memo's name, and nothing in the answers would have told you")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_every_shape_of_change_expires_it():
    root, scan = _tree("a.py", "pkg/b.py"), _Counted()
    try:
        settled("q", root, scan)
        assert scan.calls == 1

        Path(root, "c.py").write_text("# added\n")
        settled("q", root, scan)
        assert scan.calls == 2, "a NEW file did not expire the memo"

        Path(root, "a.py").write_text("# a.py, edited, and LONGER than before\n")
        settled("q", root, scan)
        assert scan.calls == 3, "an EDITED file did not expire the memo"

        # same byte count, different bytes — mtime is what must catch this
        before = Path(root, "pkg/b.py").read_text()
        Path(root, "pkg/b.py").write_text("#" + "x" * (len(before) - 2) + "\n")
        assert len(Path(root, "pkg/b.py").read_text()) == len(before)
        settled("q", root, scan)
        assert scan.calls == 4, (
            "an edit that kept the byte count identical did not expire the memo — the "
            "fingerprint has stopped reading mtime")

        os.remove(Path(root, "c.py"))
        settled("q", root, scan)
        assert scan.calls == 5, "a DELETED file did not expire the memo"
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_two_trees_keep_two_answers():
    a, b = _tree("x.py"), _tree("x.py")
    sa, sb = _Counted("tree-a"), _Counted("tree-b")
    try:
        assert settled("q", a, sa)["tag"] == "tree-a"
        assert settled("q", b, sb)["tag"] == "tree-b", "one tree's answer was served for another"
        Path(a, "new.py").write_text("# moved\n")
        settled("q", a, sa)
        settled("q", b, sb)
        assert sa.calls == 2, "the changed tree did not re-derive"
        assert sb.calls == 1, "a change in ANOTHER tree expired this one's memo"
    finally:
        shutil.rmtree(a, ignore_errors=True)
        shutil.rmtree(b, ignore_errors=True)


def test_two_questions_over_one_tree_keep_two_answers():
    root = _tree("x.py")
    census, rule = _Counted("census"), _Counted("rule")
    try:
        assert settled("census", root, census)["tag"] == "census"
        assert settled("rule", root, rule)["tag"] == "rule", "two questions collapsed into one"
        assert (census.calls, rule.calls) == (1, 1)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_a_raise_is_not_remembered():
    root, calls = _tree("x.py"), []

    def boom():
        calls.append(1)
        raise RuntimeError("the corpus went away")

    try:
        for _ in range(3):
            try:
                settled("q", root, boom)
            except RuntimeError:
                pass
            else:
                raise AssertionError("the raise was swallowed — a broken scan must be loud")
        assert len(calls) == 3, (
            "a failed scan was remembered as though it were an answer, and with no beat "
            "boundary to clear it that lie is permanent")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_forget_drops_by_key_and_wholesale():
    a, b = _tree("x.py"), _tree("x.py")
    sa, sb = _Counted(), _Counted()
    try:
        settled("keep", a, sa)
        settled("drop", a, sb)
        settled("drop", b, sb)
        assert forget("drop") == 2, "forget(key) did not report what it dropped"
        settled("keep", a, sa)
        assert sa.calls == 1, "forget(key) dropped a key it was not asked to"
        settled("drop", a, sb)
        assert sb.calls == 3, "forget(key) did not actually drop"
        assert forget() >= 2
        settled("keep", a, sa)
        assert sa.calls == 2, "forget() left something behind"
    finally:
        shutil.rmtree(a, ignore_errors=True)
        shutil.rmtree(b, ignore_errors=True)


def test_generated_directories_are_not_fingerprinted():
    """``__pycache__`` moves whenever python imports the tree. A memo that expires on its
    own use is not a memo."""
    root, scan = _tree("x.py"), _Counted()
    try:
        settled("q", root, scan)
        cache = Path(root, "__pycache__")
        cache.mkdir()
        (cache / "x.cpython-999.pyc").write_bytes(b"\x00generated\x00")
        settled("q", root, scan)
        assert scan.calls == 1, "a generated bytecode file expired the memo"
        assert not any("__pycache__" in e[0] for e in tree_fingerprint(root))
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_an_unwalkable_tree_fingerprints_empty_rather_than_raising():
    assert tree_fingerprint("/nowhere/that/exists/at/all") == ()


def test_the_live_scans_answer_identically_warm_and_cold():
    """The helper being sound and the corpus scans still telling the truth are two claims."""
    from cairn.tools.base.address_rule import scan
    from cairn.tools.orient.orient import device_census

    forget()
    cold_census = device_census()
    cold_rule = scan()
    before = S.DERIVATIONS
    for _ in range(5):
        assert device_census() == cold_census, "the census changed while the corpus did not"
        assert scan() == cold_rule, "the address rule changed while the corpus did not"
    assert S.DERIVATIONS == before, (
        f"the two live scans re-derived {S.DERIVATIONS - before} times over an unmoved "
        "corpus — the guard is not on")
    assert cold_census["measured"]["count"] > 0 and cold_rule["files_read"] > 0, (
        "a memo over a vacuous scan proves nothing; this ran on the real corpus")


TESTS = [v for k, v in sorted(globals().items()) if k.startswith("test_")]

if __name__ == "__main__":
    failures = 0
    for t in TESTS:
        try:
            t()
            print(f"  ok   {t.__name__}")
        except AssertionError as e:
            failures += 1
            print(f"  FAIL {t.__name__}: {e}")
    print(f"\n{len(TESTS) - failures}/{len(TESTS)} green")
    sys.exit(1 if failures else 0)
