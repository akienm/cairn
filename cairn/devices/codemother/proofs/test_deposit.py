"""Proof: the deposit face — landing a verdict in its tree, codemother's act.

Moved here with the code (ticket e8fe361a5b2f, RULE 1): deposit_verdict and drain_pending
left skills/chart/live.py for cairn/devices/codemother/deposit.py, and a proof measures
its own component, so their teeth left the verdict machine's proof
(cairn/devices/codemother/machines/verdict/proofs/test_chart_verdict.py) for this one,
bodies unchanged. The fixtures are copied from that proof, not imported: a proof does not
reach into another component's proof.

  - THE DEPOSIT FACE IS GATED (refusals leave the tree standing) and lands with the berth
    as provenance.
  - THE DRAIN LANDS THROUGH THE ONE DOOR, ONCE; a FAILED deposit stands pending, names
    itself, and does not stop the drain from returning.
  - EACH PART LANDS BYTE-IDENTICAL to what was embedded; a REFUSED PART is loud and the
    berth stands pending until a retry lands the rest.
  - NO CHARACTER CEILING is consulted anywhere in the deposit path.
  - THE NEXUS IS THE ARTIFACT'S TO NAME; an explicit argument still wins.

DB teeth need the one-time provisioning (as the tree proof). Self-cleaning.

    python3 cairn/devices/codemother/proofs/test_deposit.py     # exit 0 = green
"""
from __future__ import annotations

import contextlib
import json
import os
import pytest
import shutil
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.devices.codemother import deposit as deposit_mod
from cairn.devices.codemother.deposit import deposit_verdict, drain_pending
from cairn.devices.codemother.machines.verdict import verdict as verdict_mod
from cairn.devices.codemother.machines.verdict.verdict import (
    VerdictRefused, enqueue_verdict, mark_deposited, pending, read_ledger,
    verdict_node_content, verdict_node_parts, write_verdict,
)
from cairn.tools.tree.tree import nexus_table, scratch_nexus
from cairn.devices.db_domain.tools.client import store
from cairn.devices.librarian.tools.trees import trees
from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

_SCRATCH = contextlib.ExitStack()   # the nexus tables this run mints ride store.scratch(): dropped at close, swept by pid if not
_HELD: list[str] = []


def _nexus() -> str:
    """This run's own nexus, minted on first use through tree.scratch_nexus()."""
    if not _HELD:
        _HELD.append(_SCRATCH.enter_context(scratch_nexus("verdict")))
    return _HELD[0]


def make_root():
    """A synthetic world: a filed ticket, a claiming chain (hypothesize <-
    validate), berthed where the exit gate globs."""
    tmp = str(scratch_dir("chart_verdict_proof_"))
    root = os.path.join(tmp, "repo")
    os.makedirs(os.path.join(root, "cairn"))
    # TWO REAL INSTRUMENTS (ticket 8e5db5f3edb2). The door RUNS what it is handed,
    # so a fixture whose instruments are prose exercises the refusal path and
    # nothing else. These are the smallest honest commands: one exits 0, one exits
    # 7, and the second is here so `expect_exit` is a DECLARATION the door reads
    # rather than a zero it assumes.
    os.makedirs(os.path.join(root, "proofs"))
    for name, body in (("splitter.sh", "echo 'splitter: 2 runs, 0 red'\nexit 0\n"),
                       ("phantom.sh", "echo 'phantom ref refused'\nexit 7\n")):
        with open(os.path.join(root, "proofs", name), "w") as fh:
            fh.write(body)
    tickets = os.path.join(tmp, "CairnCommons", "tickets")
    os.makedirs(tickets)
    with open(os.path.join(tickets, "sworn.json"), "w") as fh:
        fh.write("{}")
    berths = os.path.join(tmp, "berths")
    packets = os.path.join(berths, "0", "packets")
    os.makedirs(packets)
    hyp = os.path.join(packets, "hypothesize-20260729T000000-feedfeedfeed.json")
    with open(hyp, "w") as fh:
        json.dump({"hypotheses": [
            {"piece": "build the alpha splitter",
             "expect": "the splitter's teeth pass twice",
             "falsifier": "any tooth red on either run",
             "instrument": "python3 proofs/test_splitter.py, twice"},
            {"piece": "compose the settled machinery",
             "expect": "the composed door refuses a phantom ref",
             "falsifier": "a phantom ref berths",
             "instrument": "the door's own gate, fixture ref"}]}, fh)
    val = os.path.join(packets, "validate-20260729T000001-cafecafecafe.json")
    with open(val, "w") as fh:
        json.dump({"ticket": "sworn", "hypothesize_ref": hyp,
                   "criteria": [
                       {"claim": "the splitter is green twice",
                        "instrument": "the splitter's teeth, twice: `bash proofs/splitter.sh`",
                        "expect_exit": 0,
                        "covers": ["build the alpha splitter"]},
                       {"claim": "the door refuses the phantom",
                        "instrument": "bash proofs/phantom.sh",
                        "expect_exit": 7,
                        "covers": ["compose the settled machinery"]}]}, fh)
    return root, berths, val


@pytest.fixture
def _world():
    return make_root()


@pytest.fixture
def root(_world):
    return _world[0]


@pytest.fixture
def berths(_world):
    return _world[1]


@pytest.fixture
def val(_world):
    return _world[2]


def good_artifact(val):
    return {
        "ticket": "sworn",
        "validate_ref": val,
        "verdicts": [
            {"claim": "the splitter is green twice",
             "instrument": "the splitter's teeth, twice: `bash proofs/splitter.sh`",
             "outcome": "pass", "evidence": "exit 0 on both runs",
             "discriminating_observation": "reverted the fix; the same instrument exits 1"},
            {"claim": "the door refuses the phantom",
             "instrument": "bash proofs/phantom.sh",
             "outcome": "pass", "evidence": "VerdictRefused raised, tree untouched",
             "discriminating_observation": "removed the ref check; the phantom berths"},
        ],
        "dispositions": [
            {"piece": "build the alpha splitter",
             "expect": "the splitter's teeth pass twice",
             "disposition": "confirmed", "by": "exit 0 on both runs"},
            {"piece": "compose the settled machinery",
             "expect": "the composed door refuses a phantom ref",
             "disposition": "killed", "by": "the phantom berthed on run one"},
        ],
    }


def expect_refusal(fn, needle):
    try:
        fn()
    except VerdictRefused as err:
        assert needle in str(err), "refusal lacks %r: %s" % (needle, err)
        return
    raise AssertionError("expected VerdictRefused mentioning %r, got none" % needle)


def _berth_a_verdict(berths, artifact, stamp):
    """Land a verdict artifact where the latest-claimer rule globs, with a stamp we
    choose (the filename carries the order — sorted IS chronological)."""
    path = os.path.join(berths, "0", "packets", "verdict-%s-feedfeedfeed.json" % stamp)
    with open(path, "w") as fh:
        json.dump(artifact, fh)
    return path


def test_the_deposit_face_is_gated(root, berths, val):
    berth_dir = os.path.join(root, "instance", "deposit_berth")
    a = good_artifact(val)
    berth = write_verdict(a, instance_dir=berth_dir, root=root)
    table = nexus_table(_nexus())
    before = trees.tree_state(_nexus(), table=table, owner="chart")
    fixed = lambda text: [1.0, 0.0, 0.0]  # noqa: E731 — the seam, not a vector, since 2026-07-29
    expect_refusal(lambda: deposit_verdict(a, fixed,
                                           berth_path=berth + ".gone", root=root),
                   "does not exist")
    expect_refusal(lambda: deposit_verdict(dict(a, dispositions=[]), fixed,
                                           berth_path=berth, root=root),
                   "undispositioned")
    assert trees.tree_state(_nexus(), table=table, owner="chart") == before, \
        "a refused deposit leaves the tree standing"
    # The real landing, with the berth as provenance (scratch corpus, as the
    # sibling proofs: the LIVE hypothesize tree is never a fixture).
    content = verdict_node_content(a)
    unique = content + f" [{_nexus()}]"
    r = trees.deposit(unique, [1.0, 0.0, 0.0],
                      {"source": berth, "validate_ref": a["validate_ref"],
                       "ticket": a["ticket"]},
                      tree=_nexus(), table=table, owner="chart")
    rows = store.read(trees.NODES_TABLE, where="node_id = %s", params=(r["node_id"],))
    assert rows and rows[0]["content"] == unique
    assert rows[0]["provenance"]["source"] == berth
    assert rows[0]["provenance"]["ticket"] == "sworn"


def test_the_drain_lands_through_the_one_door_and_never_twice(root, berths, val):
    """The read is the event: a pending verdict deposits through deposit_verdict
    (the ONE door — no parallel writer), lands with its berth as provenance, is
    marked deposited, and a SECOND drain finds nothing pending, so the tree stands
    exactly still. Scratch nexus, fixed vector: the LIVE hypothesize tree is never
    a fixture and no embed host is on this tooth's path."""
    ledger = os.path.join(root, "instance", "ledger4", "verdict-deposits.jsonl")
    # Its OWN artifact text: the deposit door dedups by (tree, content), so reusing
    # the gated-face tooth's artifact would land a DUPLICATE carrying that tooth's
    # provenance — a green that proved nothing about this drain (measured on the
    # first run of this tooth, 2026-07-29).
    # PART BY PART since 2026-07-29 this must distinguish EVERY part, not just the
    # criteria: two verdicts that differ only in their criteria now SHARE their
    # disposition nodes (measured on this tooth's first run under the new renderer).
    # That sharing is the stone's win and has its own tooth below; here it would just
    # blur what this one is asking.
    drained_artifact = dict(good_artifact(val))
    drained_artifact["verdicts"] = [dict(v, evidence=v["evidence"] + f" — drained [{_nexus()}]")
                                    for v in drained_artifact["verdicts"]]
    drained_artifact["dispositions"] = [dict(d, by=d["by"] + f" — drained [{_nexus()}]")
                                        for d in drained_artifact["dispositions"]]
    art = _berth_a_verdict(berths, drained_artifact, "20260729T040000")
    assert enqueue_verdict("sworn", berths_root=berths, ledger_path=ledger) == art
    table = nexus_table(_nexus())
    drained = drain_pending(root=root, nexus=_nexus(), embed=lambda text: [0.0, 1.0, 0.0],
                            ledger_path=ledger)
    assert len(drained) == 1 and drained[0]["berth"] == art, drained
    assert "failed" not in drained[0] and drained[0]["duplicates"] == 0, drained
    # ONE NODE PER CLAIM since 2026-07-29: the berth lands as its parts, and the
    # WHOLE rendering is never persisted — the monolith is gone, not merely joined by.
    node_ids = drained[0]["deposited"]
    parts = verdict_node_parts(drained_artifact)
    assert len(node_ids) == len(parts) == 4, (node_ids, parts)
    rows = [store.read(trees.NODES_TABLE, where="node_id = %s", params=(n,))[0] for n in node_ids]
    assert [r["content"] for r in rows] == [c for _, c in parts], rows
    assert all(r["provenance"]["source"] == art for r in rows), rows
    assert all(r["provenance"]["ticket"] == "sworn" for r in rows), rows
    whole = verdict_node_content(drained_artifact)
    assert not store.read(trees.NODES_TABLE, where="content = %s", params=(whole,)), \
        "the WHOLE verdict must never be persisted as a node — one node holds one claim"
    assert pending(ledger_path=ledger) == [], "the landed berth is marked, not pending"
    standing = trees.tree_state(_nexus(), table=table, owner="chart")
    assert drain_pending(root=root, nexus=_nexus(), embed=lambda text: [0.0, 1.0, 0.0],
                         ledger_path=ledger) == [], "a second drain has nothing to do"
    assert trees.tree_state(_nexus(), table=table, owner="chart") == standing, \
        "a re-drain must never double-deposit — the tree stands exactly still"
    os.unlink(art)


def test_a_failed_deposit_stands_pending_and_is_named(root, berths, val):
    """Law 7 at this seam: the deposit refuses (the artifact stopped validating),
    so the ENQUEUED line stands — the obligation is permanent in the record — while
    the failure is named in what the door serves. The drain RETURNS instead of
    raising: a counsel read must still serve, and the tree is untouched."""
    ledger = os.path.join(root, "instance", "ledger5", "verdict-deposits.jsonl")
    bad = _berth_a_verdict(berths, dict(good_artifact(val), dispositions=[]),
                           "20260729T050000")
    assert enqueue_verdict("sworn", berths_root=berths, ledger_path=ledger) == bad
    table = nexus_table(_nexus())
    before = trees.tree_state(_nexus(), table=table, owner="chart")
    drained = drain_pending(root=root, nexus=_nexus(), embed=lambda text: [0.0, 0.0, 1.0],
                            ledger_path=ledger)
    assert len(drained) == 1 and "failed" in drained[0], drained
    assert "undispositioned" in drained[0]["failed"], drained
    assert drained[0]["still_pending"] is True
    assert [e["berth"] for e in pending(ledger_path=ledger)] == [bad], \
        "a failed deposit leaves its entry STANDING — nothing vanishes"
    assert not [r for r in read_ledger(ledger_path=ledger) if r["kind"] == "deposited"], \
        "nothing may claim a landing that did not happen"
    assert trees.tree_state(_nexus(), table=table, owner="chart") == before, \
        "a refused deposit leaves the tree standing"
    os.unlink(bad)
    os.unlink(ledger)


def test_each_part_lands_byte_identical_to_what_was_embedded(root, berths, val):
    """The vector and the bytes are the SAME act: whatever string was handed to the
    embed seam is the string that landed, character for character. A rendering that
    happened twice — once to embed, once to store — is a vector describing bytes its
    node does not hold, and nothing downstream could ever detect it.

    Also here: the provenance carries which part of which berth this node is, because
    the parts are bare by construction and the attribution has to ride SOMEWHERE."""
    ledger = os.path.join(root, "instance", "ledger7", "verdict-deposits.jsonl")
    a = dict(good_artifact(val))
    a["verdicts"] = [dict(v, evidence=v["evidence"] + f" — byte-identity tooth [{_nexus()}]")
                     for v in a["verdicts"]]
    a["dispositions"] = [dict(d, by=d["by"] + f" — byte-identity [{_nexus()}]")
                         for d in a["dispositions"]]
    art = _berth_a_verdict(berths, a, "20260729T080000")
    assert enqueue_verdict("sworn", berths_root=berths, ledger_path=ledger) == art
    seen = []

    def recording_embed(text):
        seen.append(text)
        # the metered shape: a dict carrying the host's own count beside the vector
        return {"vector": [float(len(seen)), 1.0, 0.0], "tokens": 10 + len(seen)}

    table = nexus_table(_nexus())
    drained = drain_pending(root=root, nexus=_nexus(), embed=recording_embed,
                            ledger_path=ledger)
    assert "failed" not in drained[0], drained
    assert seen == [c for _, c in verdict_node_parts(a)], \
        "the seam was handed something other than the parts: %r" % (seen,)
    rows = [store.read(trees.NODES_TABLE, where="node_id = %s", params=(n,))[0]
            for n in drained[0]["deposited"]]
    assert [r["content"] for r in rows] == seen, \
        "a node holds bytes its vector never saw — the two renderings drifted"
    for i, r in enumerate(rows):
        assert r["provenance"]["part_index"] == i, r["provenance"]
        assert r["provenance"]["part_count"] == len(seen)
        assert r["provenance"]["part"] in ("criterion", "disposition")
        assert r["provenance"]["source"] == art
    # the meter came back with the parts (None would mean 'not reported', not zero)
    assert drained[0]["tokens"] == [11, 12, 13, 14], drained[0]["tokens"]
    assert pending(ledger_path=ledger) == []

    # THE PROPERTY A MONOLITH CANNOT HAVE, measured right here: a second verdict that
    # answers ONE criterion with different evidence and everything else identically
    # shares the unchanged claims as the SAME nodes. Under the whole-verdict rendering
    # the two documents differed by one clause and were therefore two entirely distinct
    # nodes — every claim they agreed on stored twice, and neither retrievable on its
    # own. This is the deduplication half of why one node holds one claim.
    second = dict(a)
    second["verdicts"] = [a["verdicts"][0],
                          dict(a["verdicts"][1],
                               evidence=f"VerdictRefused raised on the second run too [{_nexus()}]")]
    art2 = _berth_a_verdict(berths, second, "20260729T081500")
    assert enqueue_verdict("sworn", berths_root=berths, ledger_path=ledger) == art2
    grew_from = trees.tree_state(_nexus(), table=table, owner="chart")
    d2 = drain_pending(root=root, nexus=_nexus(),
                       embed=lambda text: {"vector": [2.0, 1.0, 0.0], "tokens": 5},
                       ledger_path=ledger)
    assert "failed" not in d2[0], d2
    shared = [p for p in d2[0]["parts"] if p["duplicate"]]
    assert [p["part_index"] for p in shared] == [0, 2, 3], d2[0]["parts"]
    assert d2[0]["deposited"][0] == drained[0]["deposited"][0], \
        "an unchanged claim must be the SAME node, not a second copy of itself"
    grew_to = trees.tree_state(_nexus(), table=table, owner="chart")
    assert grew_to["nodes"] - grew_from["nodes"] == 1, \
        "only the claim that actually changed is a new node"
    os.unlink(art)
    os.unlink(art2)
    os.unlink(ledger)


def test_a_refused_part_is_loud_and_the_berth_stands_pending(root, berths, val):
    """THE HOST'S REFUSAL IS THE BOUND — the thing this stone was cast to build a
    pre-flight for, and measured impossible: the host reports prompt_eval_count only
    in a SUCCESSFUL body, so nothing can ask 'how many tokens is this' without doing
    the work. The refusal already fires, already loud, at exactly the right moment.

    What that leaves is a PARTIAL LANDING, and it is safe by construction rather than
    by luck: no 'deposited' record is written unless every part landed, so the berth
    stays pending and the retry re-deposits the whole verdict — where the parts that
    already landed dedupe on their content hash and the table does not grow. This
    tooth forces the refusal mid-verdict and then proves the retry closes it.

    A refused part is NEVER split further, summarised, or truncated to fit: no such
    path exists, and the next tooth proves no length is even consulted."""
    ledger = os.path.join(root, "instance", "ledger8", "verdict-deposits.jsonl")
    a = dict(good_artifact(val))
    a["dispositions"] = [dict(d, by=d["by"] + f" — refusal tooth [{_nexus()}]") for d in a["dispositions"]]
    a["verdicts"] = [dict(v, evidence=v["evidence"] + f" — refusal tooth [{_nexus()}]")
                     for v in a["verdicts"]]
    art = _berth_a_verdict(berths, a, "20260729T090000")
    assert enqueue_verdict("sworn", berths_root=berths, ledger_path=ledger) == art
    table = nexus_table(_nexus())
    calls = {"n": 0}

    def refusing_embed(text):
        calls["n"] += 1
        if calls["n"] == 3:  # the host's own refusal shape: over-length input
            raise RuntimeError("HostRefused: input exceeds the model's context length")
        return {"vector": [0.0, 0.0, float(calls["n"])], "tokens": 7}

    drained = drain_pending(root=root, nexus=_nexus(), embed=refusing_embed,
                            ledger_path=ledger)
    assert len(drained) == 1 and "failed" in drained[0], drained
    assert "context length" in drained[0]["failed"], drained
    assert drained[0]["still_pending"] is True
    assert [e["berth"] for e in pending(ledger_path=ledger)] == [art], \
        "a berth whose parts did not all land STANDS pending"
    assert not [r for r in read_ledger(ledger_path=ledger) if r["kind"] == "deposited"], \
        "nothing may claim a landing that did not happen"
    parts = verdict_node_parts(a)
    landed = [store.read(trees.NODES_TABLE, where="content = %s", params=(c,)) for _, c in parts]
    assert [bool(x) for x in landed] == [True, True, False, False], \
        "the parts before the refusal landed; the refused one and its successors did not"
    # THE RETRY: the same berth, a seam that no longer refuses. The already-landed
    # parts come back as DUPLICATES and the tree grows by exactly the missing two.
    before = trees.tree_state(_nexus(), table=table, owner="chart")
    again = drain_pending(root=root, nexus=_nexus(),
                          embed=lambda text: {"vector": [0.0, 0.0, 9.0], "tokens": 7},
                          ledger_path=ledger)
    assert "failed" not in again[0], again
    assert again[0]["duplicates"] == 2, again[0]
    assert len(again[0]["deposited"]) == 4
    assert pending(ledger_path=ledger) == [], "the completed berth is finally marked"
    after = trees.tree_state(_nexus(), table=table, owner="chart")
    assert after["nodes"] - before["nodes"] == 2, (before, after)
    os.unlink(art)
    os.unlink(ledger)


def test_no_character_ceiling_is_consulted_anywhere_in_the_deposit_path(root, berths, val):
    """The ticket's sharpest falsifier, read straight: if any length heuristic
    survives in the deposit path, the bound is a guess wearing a measurement's
    clothes — and a guess that is WRONG in the safe direction still silently drops
    claims the host would have accepted. The source itself is the instrument; a
    length COMPARISON is what is forbidden (reporting len(content) as evidence is
    measurement, not a gate)."""
    import inspect as _inspect
    import re
    src = "".join(_inspect.getsource(f) for f in (deposit_mod.deposit_verdict,
                                                  deposit_mod.drain_pending))
    offenders = [ln.strip() for ln in src.splitlines()
                 if re.search(r"len\s*\([^)]*\)\s*(<|>|<=|>=|==|!=)", ln)
                 or re.search(r"(<|>|<=|>=)\s*\d{3,}", ln)]
    assert not offenders, (
        "a character ceiling crept back into the deposit path: %r — the host's own "
        "refusal IS the bound" % offenders)


def test_the_deposit_lands_in_the_nexus_the_artifact_names(root, berths, val):
    """THE NEXUS IS A SPECIFIED PARAMETER (ticket watchme-emits-a-probe piece (d)).
    It was the string ``"hypothesize"`` written into this face and into the learn
    verb — correct for every verdict answering a chart chain, wrong for a probe's
    verdict, and impossible for a consumer outside this toolchain.

    Three-part precedence, measured against the TREE and not the return value: an
    explicit argument wins, then the artifact's field, then the default. The
    return value is checked too, because the drain now reports the RESOLVED nexus
    (one drain can land two berths in two different trees)."""
    berth_dir = os.path.join(root, "instance", "nexus_berth")
    fixed = lambda text: [0.0, 0.5, 0.5]  # noqa: E731
    named = _SCRATCH.enter_context(scratch_nexus("verdict_named"))   # a second tree of its own, also scratch
    a = dict(good_artifact(val), nexus=named)
    berth = write_verdict(a, instance_dir=berth_dir, root=root)

    before_named = trees.tree_state(named, table=nexus_table(named), owner="chart")
    got = deposit_verdict(a, fixed, berth_path=berth, root=root)
    assert got["nexus"] == named, got["nexus"]
    after_named = trees.tree_state(named, table=nexus_table(named), owner="chart")
    assert after_named != before_named, \
        "the artifact named its tree and the deposit landed somewhere else"

    # An explicit argument still wins — the caller is closer to the truth than a
    # file, and every existing drain call in this proof depends on that holding.
    before_scratch = trees.tree_state(_nexus(), table=nexus_table(_nexus()), owner="chart")
    got = deposit_verdict(a, fixed, berth_path=berth, root=root, nexus=_nexus())
    assert got["nexus"] == _nexus(), got["nexus"]
    assert trees.tree_state(_nexus(), table=nexus_table(_nexus()), owner="chart") \
        != before_scratch, "the explicit argument was ignored"

    # And an artifact that says nothing resolves to where it always landed — the
    # non-regression that makes this field additive rather than a migration.
    assert verdict_mod.verdict_nexus(good_artifact(val)) == "hypothesize"


def _main() -> int:
    root, berths, val = make_root()
    checks = [
        test_the_deposit_face_is_gated,
        test_the_drain_lands_through_the_one_door_and_never_twice,
        test_a_failed_deposit_stands_pending_and_is_named,
        test_each_part_lands_byte_identical_to_what_was_embedded,
        test_a_refused_part_is_loud_and_the_berth_stands_pending,
        test_no_character_ceiling_is_consulted_anywhere_in_the_deposit_path,
        test_the_deposit_lands_in_the_nexus_the_artifact_names,
    ]
    try:
        for check in checks:
            check(root, berths, val)
            print(f"  PASS  {check.__name__}")
    finally:
        _SCRATCH.close()
        shutil.rmtree(os.path.dirname(root), ignore_errors=True)
    print("green — codemother/deposit: the deposit face is gated, the drain lands "
          "through the one door exactly once and a failed deposit stands pending, each "
          "part lands byte-identical to what was embedded, a refused part is loud, no "
          "character ceiling is consulted, and the artifact names its own nexus")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
