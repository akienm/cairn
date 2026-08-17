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
decompose.sub_problems[].{what,why,kind,fills,uses}, triage.order[].{what,why_now}). The
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
             "address": "cairn/devices/builder/machines/verdict/verdict.py"},
            {"what": "aider's model layer",
             "address": str(Path.home() / "dev/src/aider/aider/models.py")},
            {"what": "a directory holding", "address": "cairn/tools/base"},
            {"what": "something that moved", "address": "cairn/does/not/exist.py"},
        ],
        "absences": [{"what": "any translation", "measure": "grep found none"}],
    })
    berth(root, "decompose", {
        "ticket": TICKET,
        "sub_problems": [
            {"what": "alpha", "why": "because alpha", "kind": "build",
             "fills": ["any translation"]},
            {"what": "beta", "why": "because beta", "kind": "compose",
             "uses": ["cairn/devices/builder/machines/verdict/verdict.py"]},
            {"what": "gamma", "why": "because gamma", "kind": "build",
             "fills": ["any translation"]},
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
    """
    with chain() as root:
        b = translate.brief(TICKET, 0, berths_root=root)
        assert any("dev/src/aider" in f for f in b.read_only), b.read_only
        assert not any("dev/src/aider" in f for f in b.files), b.files
        assert all(f.startswith(str(REPO)) for f in b.files), b.files


def test_no_holding_is_SILENTLY_dropped():
    """Every addressed holding lands in exactly one of the three lists (Law 7).

    The survey's inventory reaching the last hop and shrinking without a word is the
    failure; a directory and a dead path are both in the fixture because both are the
    ordinary way it happens.
    """
    with chain() as root:
        b = translate.brief(TICKET, 0, berths_root=root)
        holdings = json.loads(next((root / "chart" / "packets")
                                   .glob("survey-*.json")).read_text())["holdings"]
        assert len(b.files) + len(b.read_only) + len(b.skipped) == len(holdings)
        assert {s["why"] for s in b.skipped} == {"a directory, not a file",
                                                 "does not resolve"}


def test_the_editable_list_is_absolute_and_deduplicated():
    """aider resolves fnames against ITS repo root, which is not necessarily our cwd."""
    with chain() as root:
        berth(root, "survey", {"ticket": TICKET, "sought": ["x"], "absences": [],
                               "holdings": [
                                   {"what": "a", "address": "cairn/tools/base/probe.py"},
                                   {"what": "same file, absolute",
                                    "address": str(REPO / "cairn/tools/base/probe.py")}]},
              stamp="20260816T235959")
        b = translate.brief(TICKET, 0, berths_root=root)
        assert b.files == [str(REPO / "cairn/tools/base/probe.py")], b.files


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
        assert str(REPO / "cairn/devices/builder/machines/verdict/verdict.py") in b.files, \
            f"a repo-relative holding did not survive a foreign cwd: {b.files} {b.skipped}"


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
    for name in ("fnames", "read_only_fnames", "test_cmd", "auto_test"):
        assert name in params, f"aider's Coder no longer takes {name!r}"


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
