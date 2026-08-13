"""Proof for determinism — where the LLM is, and the floor under a green.

THE FAILURE MODE THIS COMPONENT HAS. A reach report is satisfied by a hollow implementation
in two opposite directions, and each one reads as success:

  - a walk that stops short returns an empty closure, finds no LLM, and reports the whole
    corpus PURE. That is the loudest possible green and it means nothing.
  - a walk that over-matches reports everything as reaching an oracle, and a scan that reds
    everything gets ignored, which is the same as not existing.

So every verdict tooth is PAIRED: the same rule is measured over a planted tree that must
produce it and over a tree that must not. Either half alone is passed by sheet metal.

TOOTH (b) IS AKIEN'S CORRECTION, ARMED AS A PERMANENT TRAP. The first cut graded on "does
it leave the process", which made a `git` call disqualifying and reported 17 components as
reaching an oracle when not one could reach the inference host. His words, 2026-08-13:
"DETERMINISTIC code can call other scripts. But Pure DETERMINISTIC means no LLM calls."
A shell-out that downgrades a verdict is now a RED, not a nuance.

Tooth (e) pins the other half of the same axis: a seam reaching the LLM must not red the
fire path (or every component that learns reds itself), and must still be REPORTED (or a
genuine oracle hides behind a filename).

    python3 cairn/tools/determinism/proofs/test_determinism.py     # exit 0 = green
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.devices.tester.scratch import scratch_dir
from cairn.tools.determinism import determinism as D
from cairn.tools.import_sieve import sieve

LLM_IMPORT = "from cairn.devices.inference_domain import domain\n"


def _tree(**components) -> Path:
    """A synthetic corpus: {component_path: {filename: source}}, each with a charter.

    Padded past import_sieve's hollow floor so a clean result here is a real one — the same
    reason the sieve's own proof plants filler.
    """
    root = scratch_dir("determinism-proof-")
    for i in range(25):
        f = root / "filler" / f"mod_{i}.py"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text("import json\n")
    (root / "filler" / "intention+why.json").write_text(json.dumps({"component": "filler"}))
    for rel, files in components.items():
        d = root / rel
        d.mkdir(parents=True, exist_ok=True)
        (d / "intention+why.json").write_text(json.dumps({"component": Path(rel).name}))
        for name, src in files.items():
            (d / name).write_text(src)
    return root


def _row(report, path):
    for r in report["rows"]:
        if r["path"] == path:
            return r
    raise AssertionError(f"{path} missing from roster: {[r['path'] for r in report['rows']]}")


# ── the axis is the LLM, and a shell is ordinary ──────────────────────────────


def test_a_pure_imports_are_pure():
    root = _tree(**{"tools/pure": {"pure.py": "import json\nimport os\n"}})
    row = _row(D.measure(root), "tools/pure")
    assert row["verdict"] == D.PURE, row
    assert not row["llm"], row


def test_b_shelling_out_does_not_cost_purity():
    """AKIEN, 2026-08-13: "DETERMINISTIC code can call other scripts." A component that
    runs `git` and calls no LLM is PURE. The first cut got this wrong; this is the trap."""
    root = _tree(**{"tools/shells": {
        "shells.py": "import subprocess\nsubprocess.run(['git', 'status'])\n"}})
    row = _row(D.measure(root), "tools/shells")
    assert row["verdict"] == D.PURE, f"a shell-out downgraded a verdict: {row}"
    assert "git" in row["shells"], "the shell target must still be reported, just not graded"


def test_c_an_opaque_argv_is_flagged_not_assumed_innocent():
    """Shelling is allowed inside PURE, which makes an unresolved target the one way this
    verdict can be wrong. It must be surfaced rather than quietly passed."""
    root = _tree(**{"tools/opaque": {
        "opaque.py": "import subprocess\ndef go(argv):\n    subprocess.run(argv)\n"}})
    row = _row(D.measure(root), "tools/opaque")
    assert row["opaque_argv"], f"a computed argv was silently treated as clean: {row}"


def test_d_off_box_state_is_reported_but_does_not_set_the_verdict():
    """psycopg2 is not an LLM. Grading 5432 as an oracle is the error the first cut shipped."""
    root = _tree(**{"tools/dbish": {"dbish.py": "import psycopg2\n"}})
    row = _row(D.measure(root), "tools/dbish")
    assert row["verdict"] == D.PURE, f"off-box state was graded as an oracle: {row}"
    assert row["offbox"], "off-box reach must still be reported"


# ── the LLM: in the loop, at SLEEP, or off the path ───────────────────────────


def test_e_the_llm_in_the_fire_path_reaches_an_oracle():
    """TWO hops out. A one-hop check passes this while the loop really does call an LLM."""
    root = _tree(**{
        "devices/front": {"front.py": "import mid.mid\n"},
        "mid": {"mid.py": LLM_IMPORT},
    })
    row = _row(D.measure(root), "devices/front")
    assert row["verdict"] == D.ORACLE, row
    assert "->" in next(iter(row["llm"].values())), "the chain must say HOW, not just that"


def test_f_a_sleep_seam_does_not_red_the_fire_path():
    """BOTH halves are the tooth: the verdict must ignore the seam (or every learning
    component reds itself), and the seam's reach must still be REPORTED."""
    root = _tree(**{"machines/gate": {"gate.py": "import json\n", "live.py": LLM_IMPORT}})
    row = _row(D.measure(root), "machines/gate")
    assert row["verdict"] == D.MOSTLY, f"the seam red the fire path: {row}"
    assert row["seam_llm"], f"the seam's LLM reach went unreported: {row}"


def test_g_a_seam_reachable_from_the_fire_path_still_counts():
    """A filename cannot launder an oracle. If the loop imports the seam, the LLM is in the
    loop — which is exactly why the librarian's shim makes it REACHES AN ORACLE."""
    root = _tree(**{"devices/loud": {"loud.py": "import devices.loud.live\n",
                                     "live.py": LLM_IMPORT}})
    row = _row(D.measure(root), "devices/loud")
    assert row["verdict"] == D.ORACLE, f"a seam import from the fire path was excused: {row}"


def test_h_an_llm_off_the_path_is_not_caught():
    """The other half of (e): a component that calls an LLM but is NOT reachable from this
    one must stay pure. Without this, `catch everything` passes tooth (e)."""
    root = _tree(**{"tools/clean": {"clean.py": "import json\n"},
                    "elsewhere": {"elsewhere.py": LLM_IMPORT}})
    assert _row(D.measure(root), "tools/clean")["verdict"] == D.PURE


# ── the roster is disk, and the floor under a clean report ────────────────────


def test_i_a_charter_with_no_code_is_not_on_the_roster():
    """Prose-as-implementation ships no fire path. Reporting it PURE would be a green
    earned by having nothing to measure."""
    root = _tree(**{"skills/prose": {}})
    assert not any(r["path"] == "skills/prose" for r in D.measure(root)["rows"])


def test_j_the_hollow_floor_refuses_an_unread_tree():
    """A report over zero files finds zero oracles and looks perfect (Law 8)."""
    try:
        D.measure(scratch_dir("determinism-empty-"))
    except sieve.HollowScan:
        return
    raise AssertionError("a report over an unread tree came back clean instead of refusing")


def test_k_the_real_corpus_is_read_by_invariant():
    """Against the live tree — INVARIANTS, never today's counts, so this cannot go red
    merely because the corpus grew (I-proof-over-live-data)."""
    report = D.measure(_REPO_ROOT)
    assert report["rows"], "the real corpus reported no components at all"
    for r in report["rows"]:
        assert (_REPO_ROOT / r["path"] / D.CHARTER).is_file(), \
            f"invented a component with no charter on disk: {r['path']}"
        assert r["verdict"] in (D.PURE, D.MOSTLY, D.ORACLE), r
        if r["verdict"] == D.ORACLE:
            assert r["llm"], f"{r['path']} reds with no LLM chain named — incomplete finding"
        if r["verdict"] == D.MOSTLY:
            assert r["seam_llm"], f"{r['path']} is MOSTLY with no SLEEP seam named"
    # inference_domain is the sole path to the host, so it must be IN the loop; and this
    # tool must be pure, because an instrument that measures replayability and is not
    # itself replayable cannot be trusted about anything.
    assert _row(report, "cairn/devices/inference_domain")["verdict"] == D.ORACLE
    assert _row(report, "cairn/tools/determinism")["verdict"] == D.PURE


def _run() -> int:
    fails = []
    for name, fn in sorted(globals().items()):
        if not name.startswith("test_") or not callable(fn):
            continue
        try:
            fn()
            print(f"  ok   {name}")
        except Exception as exc:  # noqa: BLE001 — the proof reports, it does not propagate
            fails.append((name, exc))
            print(f"  RED  {name}: {type(exc).__name__}: {exc}")
    print(f"\n{'RED' if fails else 'green'}: {len(fails)} failing")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(_run())
