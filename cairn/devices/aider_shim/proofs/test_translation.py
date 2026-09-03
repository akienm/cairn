#!/usr/bin/env python3
"""Teeth for the translation. The claim under test is falsifier clause (7).

THE CLAUSE: "a prompt handed to aider contains anything not traceable to a berthed packet
field — the chain stopped being the input and the conversation started being it." Every
tooth here is aimed at one of the ways that could be true and go unnoticed.

WHY THESE RUN OVER FIXTURES AND NOT THE LIVE CHAIN. The standing chain lives in
instance-space, and a sealed proof may never read there. The second reason is that it
would be asserting over a snapshot: the aider-shim chain has seven pieces TODAY, and a
tooth reading `order[4]` would go red the day somebody re-charts, with nothing broken. So
the chain is built here, in a temp dir, shaped exactly like the real berths (measured off
~/.cairn/devices/chart/0/packets/ on 2026-08-16: orient.intent, constrain.bounds.{in,out},
constrain.constraints[].{text,source,kind}, survey.holdings[].{what,address},
decompose.sub_problems[].{what,why,kind,fills,uses,writes_to}, triage.order[].{what,why_now}). The
live chain is exercised by the live fire instead — the proof pins the contract, the live
fire meets the world.

THE FIXTURE'S ONE DELIBERATE ASYMMETRY: the split is [alpha, beta, gamma] and the ranked
order is [gamma, alpha, beta]. With the two agreeing, a brief that indexed the split
directly would pass every tooth here and be wrong in production.
"""

import ast
import json
import sys
import tempfile
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from cairn.devices.aider_shim import translate  # noqa: E402

REPO = Path(__file__).resolve().parents[4]
TICKET = "fixture-ticket"
FAILURES = []


def check(name, fn):
    try:
        fn()
        print(f"  ok   {name}")
    except Exception:
        FAILURES.append(name)
        print(f"  FAIL {name}")
        traceback.print_exc()


def berth(root: Path, stage: str, packet: dict, stamp="20260816T000000") -> Path:
    d = root / "chart" / "packets"
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"{stage}-{stamp}-abcdef123456.json"
    p.write_text(json.dumps(packet), encoding="utf-8")
    return p


def make_chain(root: Path) -> Path:
    """A complete, well-formed chain, in the real berths' shape."""
    berth(root, "orient", {"ticket": TICKET, "intent": "Do the fixture thing, grounded."})
    berth(root, "constrain", {
        "ticket": TICKET,
        "bounds": {"in": ["touch alpha.py", "touch beta.py"],
                   "out": ["never touch vendor/", "never widen the fence"]},
        "constraints": [{"text": "Law 4: physics not policy", "source": "CLAUDE.md",
                         "kind": "law"},
                        {"text": "proofs run twice", "source": "skills/sail/SKILL.md",
                         "kind": "skill"}],
    })
    berth(root, "survey", {
        "ticket": TICKET, "sought": ["everywhere"],
        "holdings": [
            {"what": "the verdict resolver",
             "address": "cairn/devices/codemonkey/machines/verdict/verdict.py"},
            {"what": "aider's model layer",
             "address": str(Path.home() / "dev/src/aider/aider/models.py")},
            {"what": "a directory holding", "address": "cairn/tools/base"},
            {"what": "something that moved", "address": "cairn/does/not/exist.py"},
        ],
        "absences": [{"what": "any translation", "measure": "grep found none"}],
    })
    berth(root, "decompose", {
        "ticket": TICKET,
        # EVERY PIECE CARRIES `uses`, BECAUSE THE REAL ONES DO. Until 2026-08-17 the two
        # build pieces here carried only `fills`, and that fixture disagreed with the
        # producer: measured across 51 decompose berths, 320 of 321 pieces declare `uses`
        # — 235 of 236 BUILD pieces among them. The file list is selected from `uses`, so
        # a fixture without it could not have caught the survey-wide selection that made
        # every piece's brief identical and over the model's window.
        # gamma carries all four holdings so the classification teeth (outside-the-repo,
        # directory, dead path) still have something to classify; alpha carries one, and
        # the DIFFERENCE between them is what a piece-scoped file list means.
        # AND EVERY PIECE CARRIES `writes_to` (2026-08-17, ticket
        # a-piece-names-where-its-output-lands), because the decompose door now requires
        # it: `uses` names survey HOLDINGS — things that EXIST — so it cannot name where
        # a build piece's output lands. Each piece's writes_to deliberately includes an
        # address that DOES NOT EXIST, which is the ordinary case for a build piece and
        # the one a fixture built from `uses` could never contain.
        "sub_problems": [
            {"what": "alpha", "why": "because alpha", "kind": "build",
             "fills": ["any translation"],
             "uses": ["cairn/devices/codemonkey/machines/verdict/verdict.py"],
             "writes_to": ["cairn/devices/aider_shim/alpha_not_yet.py"]},
            {"what": "beta", "why": "because beta", "kind": "compose",
             "uses": ["cairn/devices/codemonkey/machines/verdict/verdict.py"],
             "writes_to": ["cairn/devices/aider_shim/translate.py"]},
            {"what": "gamma", "why": "because gamma", "kind": "build",
             "fills": ["any translation"],
             "uses": ["cairn/devices/codemonkey/machines/verdict/verdict.py",
                      str(Path.home() / "dev/src/aider/aider/models.py"),
                      "cairn/tools/base",
                      "cairn/does/not/exist.py"],
             "writes_to": ["cairn/devices/aider_shim/translate.py",
                           "cairn/devices/aider_shim/gamma_not_yet.py"]},
        ],
    })
    berth(root, "triage", {
        "ticket": TICKET,
        "order": [{"what": "gamma", "why_now": "first because gamma"},
                  {"what": "alpha", "why_now": "second because alpha"},
                  {"what": "beta", "why_now": "last because beta"}],
    })
    return root


class chain:
    """Context manager yielding a temp berths root holding the fixture chain."""

    def __enter__(self):
        self._d = tempfile.TemporaryDirectory()
        return make_chain(Path(self._d.name) / "berths")

    def __exit__(self, *exc):
        self._d.cleanup()
        return False


def raises(fn, needle):
    try:
        fn()
    except ValueError as e:
        assert needle in str(e), f"refused, but not for {needle!r}: {e}"
        return
    raise AssertionError(f"expected a refusal naming {needle!r}; none came")


# ----------------------------------------------------------------- the clause

def test_every_span_of_a_real_brief_traces():
    """THE CLAUSE, ASSERTED DIRECTLY. Nothing in the prompt lacks an origin."""
    with chain() as root:
        b = translate.brief(TICKET, 0, berths_root=root)
        assert b.unsourced() == [], b.unsourced()
        assert b.prompt
        assert any(s.kind == "berth" for s in b.spans), \
            "a prompt of pure scaffold traces perfectly and says nothing — hollow green"


def test_the_prompt_is_NOTHING_BUT_its_spans():
    """The derived view adds no text of its own.

    Without this, ``unsourced`` could pass while :meth:`Brief.prompt` glued an untraceable
    sentence between the spans — the check would be measuring a structure the caller never
    actually sends, which is the proxy-instead-of-behaviour failure in its purest form.
    """
    with chain() as root:
        b = translate.brief(TICKET, 0, berths_root=root)
        assert b.prompt == "\n\n".join(s.text for s in b.spans if s.text)


def test_a_SUMMARISED_berth_span_is_caught():
    """A render that reworded its value must not read as traceable.

    This is the realistic shape of the failure: nobody adds a conversational paragraph on
    purpose. Somebody shortens a bound to make the prompt fit, and the span still names
    the berth it came from — a self-report that would pass any check built on the span's
    own claim about itself.
    """
    with chain() as root:
        b = translate.brief(TICKET, 0, berths_root=root)
        i, s = next((i, s) for i, s in enumerate(b.spans) if s.kind == "berth")
        b.spans[i] = translate.Span(text="roughly what the berth said", kind="berth",
                                    berth=s.berth, field=s.field)
        assert b.unsourced() == [b.spans[i]], b.unsourced()


def test_dropping_ONE_item_from_a_list_bound_is_caught():
    """The tooth that pays for :func:`translate._contains` being shape-aware.

    ``constrain.bounds.out`` is a list, rendered as bullets. A naive containment check
    (``str(value) in text``) fails every list and therefore never distinguishes a complete
    render from one missing a line — which is the single most likely way an OUT bound goes
    quietly missing on its way to the model.
    """
    with chain() as root:
        b = translate.brief(TICKET, 0, berths_root=root)
        i, s = next((i, s) for i, s in enumerate(b.spans) if s.field == "bounds.out")
        b.spans[i] = translate.Span(text="\n".join(s.text.split("\n")[:-1]), kind="berth",
                                    berth=s.berth, field=s.field)
        assert b.spans[i] in b.unsourced()


def test_a_span_naming_a_field_THAT_IS_NOT_THERE_is_caught():
    """A berth origin that does not resolve is not an origin.

    ADDED AFTER A MUTANT SURVIVED: reducing ``_contains`` to pass on a ``None`` value —
    the shape a lookup returns when the field is absent — left the whole proof green.
    That is the clause's failure wearing its most convincing disguise: the span names a
    real berth and a plausible field, so it reads as sourced under any check that stops
    at 'does it claim an origin'. It matters more than it looks, because it is also what
    a RENAMED berth field produces — the chain drifts, the lookup goes empty, and the
    prompt keeps carrying whatever was written the day the field still existed.
    """
    with chain() as root:
        b = translate.brief(TICKET, 0, berths_root=root)
        s = next(s for s in b.spans if s.kind == "berth")
        b.spans.append(translate.Span(text="a plausible sentence", kind="berth",
                                      berth=s.berth, field="bounds.sideways"))
        b.spans.append(translate.Span(text="another one", kind="berth",
                                      berth="/no/such/berth.json", field="intent"))
        assert len(b.unsourced()) == 2, b.unsourced()


def test_an_INVENTED_scaffold_string_is_caught():
    """Text that is not in the frozen table cannot pass as scaffold — under either key."""
    with chain() as root:
        b = translate.brief(TICKET, 0, berths_root=root)
        b.spans.append(translate.Span(text="Also, be creative here.", kind="scaffold",
                                      key="header"))
        b.spans.append(translate.Span(text="And here.", kind="scaffold", key="not_a_key"))
        assert len(b.unsourced()) == 2, b.unsourced()


def test_a_THIRD_KIND_of_span_is_caught():
    """There are two doors, and anything arriving through neither is unsourced.

    The failure this stops is a future edit adding ``kind='note'`` for something that
    seemed obviously fine. A checker whose else-branch PASSED unknown kinds would let the
    new kind through silently, and the two-door invariant would be gone with no diff that
    looks like removing it.
    """
    with chain() as root:
        b = translate.brief(TICKET, 0, berths_root=root)
        b.spans.append(translate.Span(text="just a note", kind="note"))
        assert [s.kind for s in b.unsourced()] == ["note"]


def test_the_test_command_never_enters_the_prompt():
    """A caller-supplied string stays out of the one place that has only two doors."""
    cmd = "python3 -m pytest cairn/devices/aider_shim/proofs -q"
    with chain() as root:
        b = translate.brief(TICKET, 0, berths_root=root, test_cmd=cmd)
        assert b.test_cmd == cmd
        assert cmd not in b.prompt
        assert translate.SCAFFOLD["proof"] in b.prompt, \
            "the model is not told it is judged by a command at all"
        assert b.unsourced() == []


def test_every_scaffold_entry_is_content_free():
    """No scaffold string names a file, a path, or a component.

    The frozen table is a guarantee only while its entries stay instructional. The day one
    carries a FACT about the work — a filename, a module, a rule specific to this build —
    a fact has entered the prompt with no berth behind it: the two-door invariant intact
    while the clause it exists to serve is broken.
    """
    for key, text in translate.SCAFFOLD.items():
        assert isinstance(text, str) and text, key
        assert "/" not in text, f"{key} names a path: {text!r}"
        assert ".py" not in text, f"{key} names a file: {text!r}"


# --------------------------------------- the chain is read as the chain says

def test_the_piece_is_TRIAGES_rank_not_DECOMPOSES_position():
    """piece 0 is `gamma` — the ranked first — not `alpha`, the split's first.

    Triage spends a whole stage producing the order. A shim that indexed the split would
    silently discard it and build in authoring order, and the two agree often enough that
    the bug would survive a long time.
    """
    with chain() as root:
        assert "because gamma" in translate.brief(TICKET, 0, berths_root=root).prompt
        assert "because alpha" in translate.brief(TICKET, 1, berths_root=root).prompt
        assert "because beta" in translate.brief(TICKET, 2, berths_root=root).prompt


def test_a_piece_carries_ITS_OWN_why_and_kind():
    """Each piece's own `why` and its kind-specific field reach the prompt — and only its own."""
    with chain() as root:
        p0 = translate.brief(TICKET, 0, berths_root=root).prompt
        assert "because gamma" in p0 and "because alpha" not in p0
        assert translate.SCAFFOLD["kind_build"] in p0
        p2 = translate.brief(TICKET, 2, berths_root=root).prompt
        assert translate.SCAFFOLD["kind_compose"] in p2
        assert translate.SCAFFOLD["kind_build"] not in p2


def test_drift_between_the_order_and_the_split_REFUSES():
    """When triage names a piece the split does not hold, no brief is honest — so none is made.

    The tempting failure is a fallback: match loosely, or fall back to the split's own
    order. Either produces a brief that looks exactly like a correct one and builds the
    wrong piece.
    """
    with chain() as root:
        berth(root, "triage", {"ticket": TICKET, "order": [
            {"what": "gamma-renamed", "why_now": "x"}, {"what": "alpha", "why_now": "y"},
            {"what": "beta", "why_now": "z"}]}, stamp="20260816T235959")
        raises(lambda: translate.brief(TICKET, 0, berths_root=root), "drifted")


def test_a_missing_LINK_refuses_and_names_WHICH():
    """A chain with a hole is a red to dispose, not a thin brief to build from."""
    with chain() as root:
        for stage in ("orient", "constrain", "survey", "decompose", "triage"):
            p = next((root / "chart" / "packets").glob(f"{stage}-*.json"))
            hidden = p.with_suffix(".json.hidden")
            p.rename(hidden)
            raises(lambda: translate.brief(TICKET, 0, berths_root=root),
                   f"no standing {stage} berth")
            hidden.rename(p)


def test_a_piece_index_off_the_end_refuses():
    with chain() as root:
        raises(lambda: translate.brief(TICKET, 3, berths_root=root),
               "outside the triage order")
        raises(lambda: translate.brief(TICKET, -1, berths_root=root),
               "outside the triage order")


# --------------------- the file list carries constrain's bound, in aider's words

def test_a_holding_OUTSIDE_the_repo_is_never_editable():
    """constrain's `out` names modifying ~/dev/src/aider. The file list obeys it structurally.

    THE FALSIFIER IS THE POINT: this reds the moment a foreign-program holding lands in
    ``fnames``, which is exactly the state in which aider would be free to edit the held
    program — a breach no prompt sentence reliably prevents.

    STRUCTURAL SINCE 2026-08-17 (ticket a-piece-names-where-its-output-lands): a `uses`
    entry can no longer reach ``fnames`` by ANY path, in the repo or out of it, because
    the editable list is sourced from `writes_to` alone. The bound used to rest on a
    path comparison; now the out-of-repo check is the second lock, not the only one.
    """
    with chain() as root:
        b = translate.brief(TICKET, 0, berths_root=root)
        assert any("dev/src/aider" in f for f in b.read_only), b.read_only
        assert not any("dev/src/aider" in f for f in b.files), b.files
        assert all(f.startswith(str(REPO)) for f in b.files), b.files


def test_no_DECLARED_use_is_SILENTLY_dropped():
    """Every address the piece declared lands in exactly one of the three lists (Law 7).

    THE DENOMINATOR IS THE PIECE'S OWN FIELDS, NOT THE SURVEY'S HOLDINGS, and that changed
    on 2026-08-17 with what it counts. It used to read the survey berth back and count
    every holding, which was the right check for a function that handed aider the whole
    survey — and it was exactly the check that could not see the defect, because it was
    measuring the survey against itself. What the piece named is what may go missing now,
    so that is what is counted; a directory and a dead path are both in the fixture
    because both are the ordinary way it happens.

    AND THE DENOMINATOR IS BOTH FIELDS, not `uses` alone: `writes_to` joined the piece
    later the same day, and a total counted over one field would go green while the other
    field's addresses vanished — the precise shape of the defect this whole voyage is
    about, reproduced in the tooth that exists to catch it.
    """
    with chain() as root:
        b = translate.brief(TICKET, 0, berths_root=root)
        d = json.loads(next((root / "chart" / "packets")
                            .glob("decompose-*.json")).read_text())
        gamma = next(p for p in d["sub_problems"] if p["what"] == "gamma")
        declared = len(gamma["uses"]) + len(gamma["writes_to"])
        assert len(b.files) + len(b.read_only) + len(b.skipped) == declared, (
            b.files, b.read_only, b.skipped, declared)
        assert {s["why"] for s in b.skipped} == {"a directory, not a file",
                                                 "does not resolve"}


def test_the_file_list_IS_THE_PIECES_not_the_SURVEYS():
    """Two pieces of ONE chain get different files — which is the whole repair.

    THE DEFECT THIS WOULD HAVE CAUGHT, measured 2026-08-17 on the real chain for
    `aider-builds-a-piece`: all 8 pieces got a byte-identical file list, because the
    selection was the survey's 16 holdings and the piece's own `uses` — a berthed field
    the decompose gate refuses to leave unresolvable — was read into the prompt as prose
    and ignored where it decides something. Every piece therefore weighed ~74,090 tokens
    against a send budget of 73,728, and no drive could reach the model at all. Selecting
    by `uses`, the same pieces weigh 6.8k-41k.

    So the tooth is a DIFFERENCE, not a size: any check on one piece's list alone goes
    green under both behaviours.
    """
    with chain() as root:
        gamma = translate.brief(TICKET, 0, berths_root=root)   # 4 uses, 2 writes_to
        alpha = translate.brief(TICKET, 1, berths_root=root)   # 1 use,  1 writes_to
        assert len(alpha.files) == 1, alpha.files
        assert alpha.skipped == [], alpha.skipped
        assert len(alpha.read_only) == 1, alpha.read_only
        wide = set(gamma.files) | set(gamma.read_only) | {s["address"] for s in gamma.skipped}
        narrow = set(alpha.files) | set(alpha.read_only)
        assert len(narrow) < len(wide), \
            "the piece that declared fewer addresses did not get a smaller file list"
        assert narrow != wide, (narrow, wide)
        assert gamma.read_only, "gamma declared a use outside the repo and got no read-only"
        # And the survey's full inventory is still IN THE PROMPT — the narrowing is of
        # what aider is handed as open files, never of what the chain told it exists.
        holdings = json.loads(next((root / "chart" / "packets")
                                   .glob("survey-*.json")).read_text())["holdings"]
        for h in holdings:
            assert h["what"] in alpha.prompt, \
                f"holding {h['what']!r} vanished from the prompt, not just from the files"


def test_a_piece_that_declares_NO_uses_REFUSES_rather_than_taking_everything():
    """The fallback that would quietly restore the defect is refused, and says where to fix.

    A piece with no `uses` has nothing berthed saying which files it touches. The
    tempting fallback — hand it the survey — is precisely the behaviour that was just
    removed, and it would come back for the rarest case and be invisible. Measured: 1
    piece in 321 across 51 berths, so this refusal costs almost nothing and the fix it
    names is upstream, in the split.
    """
    with chain() as root:
        # Every piece carries `writes_to`, so the ONLY lack is the one under test — a
        # fixture short of both fields would pass this tooth on the wrong refusal.
        berth(root, "decompose", {"ticket": TICKET, "sub_problems": [
            {"what": "gamma", "why": "because gamma", "kind": "build",
             "fills": ["any translation"], "writes_to": ["cairn/devices/aider_shim/g.py"]},
            {"what": "alpha", "why": "because alpha", "kind": "build",
             "fills": ["any translation"], "writes_to": ["cairn/devices/aider_shim/a.py"]},
            {"what": "beta", "why": "because beta", "kind": "compose",
             "writes_to": ["cairn/devices/aider_shim/b.py"],
             "uses": ["cairn/devices/codemonkey/machines/verdict/verdict.py"]}]},
              stamp="20260817T235959")
        try:
            b = translate.brief(TICKET, 0, berths_root=root)
        except ValueError as e:
            assert "declares no `uses`" in str(e), e
            assert "the fix is upstream" in str(e), e
        else:
            raise AssertionError(
                f"a piece with no declared uses produced a brief carrying {len(b.files)} "
                f"editable and {len(b.read_only)} read-only file(s) — the survey-wide "
                "selection is back, for the one case nobody looks at")


def test_the_editable_list_is_absolute_and_deduplicated():
    """aider resolves fnames against ITS repo root, which is not necessarily our cwd."""
    rel, absolute = "cairn/tools/base/probe.py", str(REPO / "cairn/tools/base/probe.py")
    with chain() as root:
        berth(root, "survey", {"ticket": TICKET, "sought": ["x"], "absences": [],
                               "holdings": [{"what": "a", "address": rel},
                                            {"what": "same file, absolute",
                                             "address": absolute}]},
              stamp="20260816T235959")
        # THE PIECE HAS TO DECLARE BOTH SPELLINGS IN `writes_to`, or there is nothing to
        # deduplicate: the editable list is sourced from `writes_to` alone since
        # 2026-08-17, so neither a survey carrying a duplicate nor a duplicated `uses`
        # reaches ``fnames`` at all.
        berth(root, "decompose", {"ticket": TICKET, "sub_problems": [
            {"what": "gamma", "why": "because gamma", "kind": "build",
             "fills": ["any translation"], "uses": [rel], "writes_to": [rel, absolute]},
            {"what": "alpha", "why": "because alpha", "kind": "build",
             "fills": ["any translation"], "uses": [rel], "writes_to": [rel]},
            {"what": "beta", "why": "because beta", "kind": "compose",
             "uses": [rel], "writes_to": [rel]}]},
              stamp="20260816T235959")
        b = translate.brief(TICKET, 0, berths_root=root)
        assert b.files == [absolute], b.files
        # And the same file declared BOTH ways is editable only — a file in fnames and
        # read_only_fnames at once is a state aider's own Coder does not define.
        assert b.read_only == [], b.read_only


def test_the_file_list_does_not_depend_on_THE_CALLERS_CWD():
    """A relative holding resolves against the repo, not against wherever we happen to be.

    ADDED AFTER A MUTANT SURVIVED: dropping the ``REPO / addr`` anchoring left every tooth
    green, because the proof had only ever run from the repo root — the check went green
    for the wrong reason, and would have gone on doing so until something ran it from
    elsewhere. Which is not hypothetical: the tester seals proofs in a netns with its own
    working directory, and the caller that will eventually drive this is the shim, running
    inside aider's repo. Relative holdings are the common case (the survey berths them
    repo-relative), so the whole editable list would have silently emptied.
    """
    import os
    with chain() as root:
        here = os.getcwd()
        os.chdir("/")
        try:
            b = translate.brief(TICKET, 0, berths_root=root)
        finally:
            os.chdir(here)
        assert str(REPO / "cairn/devices/aider_shim/translate.py") in b.files, \
            f"a repo-relative `writes_to` did not survive a foreign cwd: {b.files} {b.skipped}"
        assert str(REPO / "cairn/devices/codemonkey/machines/verdict/verdict.py") in b.read_only, \
            f"a repo-relative `uses` did not survive a foreign cwd: {b.read_only} {b.skipped}"


# ------------------ the editable list is WHERE IT WRITES, not what it READS (2026-08-17)

def test_the_editable_list_is_WHERE_IT_WRITES_not_WHAT_IT_READS():
    """``fnames`` comes from `writes_to` alone; `uses` can only ever be read-only.

    THE DEFECT THIS CATCHES, measured at the first live drive (2026-08-17): the apprentice
    was handed the file the piece READS as the file to EDIT, and dutifully edited it — a
    correct drive of a wrong brief, which is the failure mode no amount of prompt wording
    fixes. The reason is structural and it is why `uses` could never have carried this:
    `uses` names survey HOLDINGS, and a holding is something the sweep FOUND, so it exists
    by construction. A build piece's whole job is to create what a measured absence says
    is missing. The address it writes is therefore excluded from `uses` BY DEFINITION, and
    no reading of the field could have recovered it.

    THE TOOTH IS A PARTITION, not a membership test: every declared `uses` entry that
    resolves is in read_only and in NEITHER of the other two, and every `writes_to` entry
    is editable. A membership-only check goes green under a function that puts everything
    everywhere.
    """
    with chain() as root:
        b = translate.brief(TICKET, 0, berths_root=root)          # gamma
        d = json.loads(next((root / "chart" / "packets")
                            .glob("decompose-*.json")).read_text())
        gamma = next(p for p in d["sub_problems"] if p["what"] == "gamma")
        for addr in gamma["writes_to"]:
            resolved = str((REPO / addr).resolve())
            assert resolved in b.files, (addr, b.files)
            assert resolved not in b.read_only, (addr, b.read_only)
        for addr in gamma["uses"]:
            p = Path(addr)
            resolved = str((p if p.is_absolute() else REPO / addr).resolve())
            assert resolved not in b.files, \
                f"{addr!r} is something the piece READS and it landed in the editable list"
        assert b.read_only, b.read_only


def test_a_writes_to_THAT_DOES_NOT_EXIST_YET_is_editable_not_skipped():
    """The ordinary case for a build piece, and the one a skip would silently break.

    A `writes_to` naming a file that is not there yet is not a defect — it is the WHOLE
    POINT: the piece exists to create it. Skipping it as unresolvable would hand aider an
    empty editable list for exactly the pieces that have the most to do, and would do it
    quietly, in the `skipped` list nobody re-reads. The fixture's alpha writes to
    `alpha_not_yet.py`, which this proof asserts is absent from disk first — a tooth that
    stopped exercising the case because somebody created the file would otherwise go green
    for the wrong reason.
    """
    target = REPO / "cairn/devices/aider_shim/alpha_not_yet.py"
    assert not target.exists(), \
        f"the fixture's deliberately-absent output address exists on disk: {target}"
    with chain() as root:
        alpha = translate.brief(TICKET, 1, berths_root=root)
        assert str(target) in alpha.files, (alpha.files, alpha.skipped)
        assert not any(s["address"] == str(target) or s["address"].endswith("alpha_not_yet.py")
                       for s in alpha.skipped), alpha.skipped


def test_a_piece_that_declares_NO_writes_to_REFUSES_and_names_THE_RE_CHART():
    """A berth predating the field is STALE, and the refusal says so with both referents.

    NOT A FALLBACK, and not a guess from the piece's prose — guessing from prose is what
    handed the apprentice the wrong file in the first place. The refusal has to be
    actionable at the moment it fires, so it carries BOTH resolvable things a reader
    needs: the berth that is stale (evidence) and the command that re-makes it (the fix).
    Naming only the command leaves the reader hunting for which berth; naming only the
    berth leaves them inventing a repair.
    """
    with chain() as root:
        berth(root, "decompose", {"ticket": TICKET, "sub_problems": [
            {"what": "gamma", "why": "because gamma", "kind": "build",
             "fills": ["any translation"],
             "uses": ["cairn/devices/codemonkey/machines/verdict/verdict.py"]},
            {"what": "alpha", "why": "because alpha", "kind": "build",
             "fills": ["any translation"],
             "uses": ["cairn/devices/codemonkey/machines/verdict/verdict.py"]},
            {"what": "beta", "why": "because beta", "kind": "compose",
             "uses": ["cairn/devices/codemonkey/machines/verdict/verdict.py"]}]},
              stamp="20260817T235959")
        try:
            b = translate.brief(TICKET, 0, berths_root=root)
        except ValueError as e:
            assert "declares no `writes_to`" in str(e), e
            assert "/chart " + TICKET in str(e), e
            assert "decompose-20260817T235959" in str(e), \
                f"the refusal did not name the stale berth it read: {e}"
        else:
            raise AssertionError(
                f"a piece with no declared `writes_to` produced a brief carrying "
                f"{len(b.files)} editable file(s) — the editable list was guessed from "
                "somewhere other than the berth, which is the defect itself")


def test_a_writes_to_OUTSIDE_THE_REPO_or_A_DIRECTORY_is_skipped_never_editable():
    """The two ways a well-formed output address is still not a file to open.

    Out-of-repo is constrain's `out` bound read from the OTHER side: `uses` was already
    barred from ``fnames``, and this closes the door the new field opened. A directory is
    the shape aider cannot act on at all. Both are `skipped` WITH A REASON rather than
    dropped — Law 7 at a diagnostic surface: the address was declared, so its absence from
    the editable list is a fact the record has to carry.
    """
    with chain() as root:
        berth(root, "decompose", {"ticket": TICKET, "sub_problems": [
            {"what": "gamma", "why": "because gamma", "kind": "build",
             "fills": ["any translation"],
             "uses": ["cairn/devices/codemonkey/machines/verdict/verdict.py"],
             "writes_to": [str(Path.home() / "dev/src/aider/aider/models.py"),
                           "cairn/tools/base",
                           "cairn/devices/aider_shim/translate.py"]},
            {"what": "alpha", "why": "because alpha", "kind": "build",
             "fills": ["any translation"], "uses": ["cairn/tools/base/probe.py"],
             "writes_to": ["cairn/devices/aider_shim/translate.py"]},
            {"what": "beta", "why": "because beta", "kind": "compose",
             "uses": ["cairn/tools/base/probe.py"],
             "writes_to": ["cairn/devices/aider_shim/translate.py"]}]},
              stamp="20260817T235959")
        b = translate.brief(TICKET, 0, berths_root=root)
        assert b.files == [str(REPO / "cairn/devices/aider_shim/translate.py")], b.files
        assert not any("dev/src/aider" in f for f in b.files), b.files
        whys = {s["address"]: s["why"] for s in b.skipped}
        assert whys[str(Path.home() / "dev/src/aider/aider/models.py")] == \
            "an output address outside this repo — not opened for editing", whys
        assert whys["cairn/tools/base"] == "a directory, not a file", whys


# --------------------------------------- the aider-side contract, measured

def test_the_briefs_fields_are_the_names_aiders_Coder_ACTUALLY_takes():
    """Measured against the held program by AST, not transcribed from memory.

    If aider renames one of these in an upgrade, it reds here rather than at the first
    live build. Reading its bytes is inside constrain's bounds; writing them is not — and
    reading by AST rather than by import is what keeps this proof runnable without the
    device's venv.
    """
    src = Path.home() / "dev/src/aider/aider/coders/base_coder.py"
    cls = next(n for n in ast.parse(src.read_text(encoding="utf-8")).body
               if isinstance(n, ast.ClassDef) and n.name == "Coder")
    init = next(n for n in cls.body
                if isinstance(n, ast.FunctionDef) and n.name == "__init__")
    params = {a.arg for a in init.args.args + init.args.kwonlyargs}
    for name in ("fnames", "read_only_fnames", "test_cmd", "auto_test", "map_tokens"):
        assert name in params, f"aider's Coder no longer takes {name!r}"


def test_the_repo_map_is_OFF_because_it_would_write_into_the_prompt_unseen():
    """The hole a span count cannot see, closed by the one number that closes it.

    aider's repo map splices a ranked digest of the whole repository into the prompt
    AFTER this module has finished counting spans, so ``unsourced()`` reports zero while
    clause (7) is being violated. Zero is therefore the design; a non-zero default here
    would be a silent widening of what reaches the model. Surfaced by the first live
    fire, which died on ``import networkx`` inside ``repomap.get_ranked_tags``.
    """
    with chain() as root:
        b = translate.brief(TICKET, 0, berths_root=root)
    assert b.map_tokens == 0, (
        "the repo map is ON — aider will assemble prompt content this module never saw, "
        "and the untraceable-span count will stay at zero while it happens")


def main():
    print("aider_shim :: translation")
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            check(name, fn)
    if FAILURES:
        print(f"\nRED — {len(FAILURES)} failure(s): {FAILURES}")
        return 1
    print("\nGREEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
