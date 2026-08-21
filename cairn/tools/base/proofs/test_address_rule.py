"""Proof for the address rule — the refusal half of the instance-space address.

Teeth a hollow build could not pass:

  - A MENTION IS NOT A CATCH, and this is the tooth the whole shape was chosen for. The text
    scan this rule replaces had to exclude two files BY NAME because they say in prose what
    they look for, and import_sieve's charter names that failure in one line: "a mention
    becomes a catch". The falsifier is a fixture whose docstring, comment and string literals
    all spell both shapes and which draws nothing — and its live twin, ``address_rule.py``
    itself, which spells both shapes repeatedly in its own docstring, is NOT exempt, and must
    never appear in a scan of the real corpus. A rule that passed the fixture and caught its
    own author would be a rule with a name-list in its future.

  - A REAL SPELLING IS A CATCH — both shapes, at the right line. The pair is what makes the
    tooth above non-vacuous: a rule that caught nothing would pass the mention tooth
    perfectly, and that is precisely how a scan goes quietly hollow.

  - THE EXEMPTION SET IS A RULE, NOT A LIST, AND IT IS CLOSED AT TWO. The ticket's declared
    load-bearing unknown, in its own words: "if the exemption set cannot be stated as a rule
    rather than a list of names, this shape is wrong." So the teeth are about the RULE — the
    module that owns the address is exempt wherever it lives (resolved from the module object,
    never from a string), any file under proofs/ is exempt at any depth, and an ordinary file
    is not exempt however suggestive its name. A third reason appearing in ``exemption_of``
    breaks the count tooth, which is the point: the sieve becoming a hand-widened allowlist is
    the failure this same address retired once already.

  - A SCAN THAT READ NO FILES RAISES. Law 8's floor: a count of 0 hand-spellings over 0 files
    is what a working corpus and a broken scanner both look like, and only one of them is
    true. HollowScan is composed from import_sieve rather than re-invented, so the tooth also
    pins that composition.

  - A NON-INSTANCE HOME PATH IS LEFT ALONE. ``Path.home() / "dev" / "src" / "aider"`` is a
    live legitimate expression (``aider_shim/venv.py:54``, a held foreign program) and the
    reason the IMPORT-level rule — who may call ``Path.home()`` at all — was bounded OUT. A
    rule that redded it would be forbidding a use the address module has no opinion about.

  - AN UNPARSEABLE FILE RIDES THE RETURN. Law 7: a scan that silently skipped what it could
    not read would report a cleaner corpus the worse its own condition got.

  - THE LIVE CORPUS IS ASSERTED BY INVARIANT, NEVER BY COUNT. Today's number is 7 and this
    voyage is about to make it 0; a tooth pinned to either would go red at the moment its
    condition was satisfied. What is pinned instead is what must be true at every count: no
    site is ever an exempt file, and every exemption recorded is one of the two.

Runnable bare (no DB, no framework):
    python3 cairn/tools/base/proofs/test_address_rule.py     # exit 0 = green
"""

from __future__ import annotations

import sys
import tempfile
from cairn.devices.tester.scratch import scratch_dir
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from cairn.tools.base import address_rule as AR          # noqa: E402
from cairn.tools.import_sieve import HollowScan          # noqa: E402

# A fixture that MENTIONS both shapes in every way a source file can mention something without
# building one: a docstring, a comment, and a plain string constant. Assembled from pieces so
# this proof's own source does not contain a spelling either — the file would then be making
# the claim it is trying to test, and a reader could not tell which.
_MENTION_ONLY = '''"""A module that talks about %s and about %s without building either."""

# Somebody might write %s here, and that would be a defect.

DOC = 'the rule catches %s'
NOTE = 'and it catches %s too'
'''
_SHAPE_A_TEXT = 'Path.home() / ' + '".cairn"'
_SHAPE_B_TEXT = 'expanduser(' + '"~/.cairn"' + ')'

_REAL_SPELLINGS = '''from pathlib import Path
import os

A = Path.home() / ".cairn" / "devices" / "thing" / "0"
B = Path("~/.cairn/devices/thing/0").expanduser()
C = os.path.expanduser("~/.cairn/logs")
LEGITIMATE = Path.home() / "dev" / "src" / "aider"
'''


def _plant(source: str, name: str = "planted.py") -> str:
    """Write one source file into a fresh temp tree and return the tree's path."""
    td = scratch_dir("cairn-address-rule-proof-")
    (td / name).write_text(source, encoding="utf-8")
    return str(td)


def test_a_mention_is_not_a_catch():
    """A docstring, a comment and two string literals naming both shapes — and no hits.

    This is the tooth the AST shape exists for. A text scan fails it by construction.
    """
    src = _MENTION_ONLY % (_SHAPE_A_TEXT, _SHAPE_B_TEXT, _SHAPE_A_TEXT,
                           _SHAPE_A_TEXT, _SHAPE_B_TEXT)
    assert _SHAPE_A_TEXT in src and _SHAPE_B_TEXT in src, \
        "the fixture must actually contain the text, or the tooth is vacuous"
    hits = AR.spellings_in(src)
    assert hits == [], f"a mention became a catch: {hits}"

    result = AR.scan(_plant(src))
    assert result["count"] == 0, f"a mention became a catch through scan(): {result['sites']}"
    assert result["files_read"] == 1, "the scan must have actually read the planted file"


def test_the_rules_own_module_mentions_both_shapes_and_is_not_exempt():
    """The live twin of the tooth above, and the one that cannot be gamed by a fixture.

    ``address_rule.py`` spells both shapes in its own prose, is NOT in the exemption set, and
    must never appear in a scan of the real corpus. The text scan's equivalent file had to be
    excluded by name; this one needs no exclusion at all.
    """
    own = Path(AR.__file__).resolve()
    source = own.read_text(encoding="utf-8")
    assert _SHAPE_A_TEXT in source and _SHAPE_B_TEXT in source, \
        "the rule module no longer says what it looks for — this tooth has lost its subject"
    assert AR.exemption_of(own) is None, \
        "the rule module exempted itself — that is the name-list this shape was chosen to avoid"
    assert AR.spellings_in(source) == [], \
        "the rule module caught itself on its own prose"

    live = AR.scan()
    assert not any(s["site"].startswith(str(own.relative_to(AR.address.ROOTS["repo"])))
                   for s in live["sites"]), "the live scan drew the rule's own module"


def test_a_real_spelling_is_a_catch_in_both_shapes():
    """Both dialects, at their own lines — and the non-instance home path left alone."""
    hits = AR.spellings_in(_REAL_SPELLINGS)
    lines = [h["line"] for h in hits]
    assert lines == [4, 5, 6], f"expected the three built addresses at 4,5,6; got {hits}"
    shapes = {h["line"]: h["shape"] for h in hits}
    assert ".cairn" in shapes[4], "the division-chain shape lost its name"
    assert "expanduser" in shapes[5] and "expanduser" in shapes[6], \
        "the expanduser shape must cover both the pathlib and the os.path dialect"


def test_a_non_instance_home_path_is_left_alone():
    """``Path.home() / "dev" / "src" / "aider"`` — the live case that bounded the import-level
    rule OUT. Asserted separately from the catch tooth because it is a different claim: not
    "the rule catches the right things" but "the rule has no opinion about this one"."""
    hits = AR.spellings_in('from pathlib import Path\nX = Path.home() / "dev" / "src" / "aider"\n')
    assert hits == [], f"a legitimate non-instance home path was caught: {hits}"


def test_the_exemption_set_is_a_rule_and_it_is_closed_at_two():
    """Stated as rules, checked as rules — and counted, so a third cannot arrive quietly."""
    owner = Path(AR.address.__file__).resolve()
    assert AR.exemption_of(owner) == "the module that owns the address"
    assert AR.OWNS_THE_ADDRESS == owner, \
        "the exemption must be resolved from the module object, never spelled as a string"

    with tempfile.TemporaryDirectory() as td:
        deep = Path(td) / "some" / "component" / "proofs" / "sub" / "test_x.py"
        deep.parent.mkdir(parents=True)
        deep.write_text("x = 1\n", encoding="utf-8")
        assert AR.exemption_of(deep) is not None, "proofs/ must be exempt at any depth"

        ordinary = Path(td) / "some" / "component" / "test_looks_like_a_proof.py"
        ordinary.write_text("x = 1\n", encoding="utf-8")
        assert AR.exemption_of(ordinary) is None, \
            "a suggestive FILENAME is not the rule — the rule is the directory's job"

        reasons = {AR.exemption_of(owner), AR.exemption_of(deep)}
        assert len(reasons) == 2, "the two members must give two distinct reasons"


def test_a_scan_that_read_no_files_raises():
    """Law 8's floor. A green over zero files is not a green."""
    with tempfile.TemporaryDirectory() as td:
        try:
            result = AR.scan(td)
        except HollowScan:
            pass
        else:
            raise AssertionError(
                f"an empty tree reported clean instead of raising: {result}")


def test_an_unparseable_file_rides_the_return():
    """Law 7 — loud at the diagnostic surface, never silently absent from the count."""
    td = _plant("def broken(:\n", name="broken.py")
    (Path(td) / "fine.py").write_text('from pathlib import Path\nZ = Path.home() / ".cairn"\n',
                                      encoding="utf-8")
    result = AR.scan(td)
    assert len(result["unreadable"]) == 1, \
        f"the unparseable file vanished from the return: {result}"
    assert "UNPARSEABLE" in result["unreadable"][0]["why"]
    assert result["count"] == 1, "the readable file's spelling must still be counted"


def test_the_live_corpus_holds_the_invariants_whatever_the_count():
    """Asserted by invariant, never by number — today's 7 becomes 0 in this same voyage, and a
    tooth pinned to either would go red at the moment its condition was satisfied."""
    live = AR.scan()
    assert live["files_read"] > 0, "the live scan read nothing — the count is not a measurement"

    legal = {"the module that owns the address",
             "a proof asserting the rule must construct what the rule forbids"}
    for e in live["exempted"]:
        assert e["why"] in legal, f"an exemption outside the closed set: {e}"

    exempt_paths = {e["path"] for e in live["exempted"]}
    for s in live["sites"]:
        path = s["site"].rsplit(":", 1)[0]
        assert path not in exempt_paths, f"an exempt file was also reported as a site: {s}"
        assert "/proofs/" not in path, f"a proof was reported as a site: {s}"


def _main() -> int:
    for check in (test_a_mention_is_not_a_catch,
                  test_the_rules_own_module_mentions_both_shapes_and_is_not_exempt,
                  test_a_real_spelling_is_a_catch_in_both_shapes,
                  test_a_non_instance_home_path_is_left_alone,
                  test_the_exemption_set_is_a_rule_and_it_is_closed_at_two,
                  test_a_scan_that_read_no_files_raises,
                  test_an_unparseable_file_rides_the_return,
                  test_the_live_corpus_holds_the_invariants_whatever_the_count):
        check()
        print(f"  PASS  {check.__name__}")
    print("green — the address rule is an AST predicate over an expression: a mention is not "
          "a catch (proved on a fixture AND on the rule's own module, which is not exempt), "
          "both real dialects are caught, a legitimate non-instance home path is left alone, "
          "the exemption set is two rules rather than a list of names, an empty tree raises "
          "HollowScan, an unparseable file rides the return, and the live corpus is pinned by "
          "invariant rather than by today's count")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
