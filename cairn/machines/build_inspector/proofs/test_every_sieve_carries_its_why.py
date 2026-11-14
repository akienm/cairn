"""Proof for ticket 39eccfbc09aa — every sieve carries its own why.

Akien, 2026-11-13 (outline 17.11.6.1): "we are supposed to add a why to each sieve so we can
help adjudicate it." Every registered sieve's record in ``sieves/`` carries a ``why`` and a
``why_source`` that checks; the sieve ``every_sieve_carries_its_why`` reds a record that does
not, and the refusing sieve's why rides each finding into the PROVEME refusal text. One tooth
per falsifier clause:

  1. the live records are valid and the sieve reads clean over them;
  2. each mutation of a scratch copy of sieves/ reds the sieve with exactly one finding,
     naming the mutated sieve (a record removed, a why blanked, an unknown source kind, a
     quote that does not stand at its address, a quote addressed at a sieve's own source, a
     Law that is not one, a cc_reading of nothing, an orphan record);
  3. inspect() stamps the refusing sieve's why on its findings as ``values.sieve_why``;
  4. the PROVEME refusal text carries that why;
  5. sieves/ holds exactly one record per registered sieve, and the runners file has moved
     beside the charter.

Mutations run over scratch copies (marked testing). Teeth 3 and 4 swap in one always-red
testing sieve and a scratch record directory; nothing writes to the live tree.

    bin/cairn test cairn/machines/build_inspector/proofs/test_every_sieve_carries_its_why.py
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"39eccfbc09aa": {
    "1": "test_the_live_records_carry_whys_that_check",
    "2": "test_each_mutation_reds_once_naming_its_sieve",
    "3": "test_inspect_stamps_the_sieve_why_on_its_findings",
    "4": "test_the_proveme_refusal_carries_the_why",
    "5": "test_one_record_per_sieve_and_the_runners_file_moved",
}}

BI = _REPO_ROOT / "cairn" / "machines" / "build_inspector"
ROW = {"component": "build_inspector", "dir": "machines/build_inspector"}


def _I():
    from cairn.machines.build_inspector import inspector
    return inspector


def _scratch_copy() -> Path:
    """A scratch build_inspector dir holding a copy of the live sieves/ (marked testing)."""
    from cairn.tools.scratch.scratch import scratch_dir
    comp = scratch_dir("testing-sieve-why-") / "build_inspector"
    shutil.copytree(BI / "sieves", comp / "sieves")
    return comp


def _edit(comp: Path, name: str, fn) -> None:
    f = comp / "sieves" / f"{name}.json"
    rec = json.loads(f.read_text(encoding="utf-8"))
    fn(rec)
    f.write_text(json.dumps(rec), encoding="utf-8")


def test_the_live_records_carry_whys_that_check():
    I = _I()
    found = I.every_sieve_carries_its_why(ROW, BI)
    assert found == [], found
    for name in I.SIEVES:
        rec = json.loads((BI / "sieves" / f"{name}.json").read_text(encoding="utf-8"))
        assert rec["why"].strip() and rec["why_source"]["kind"] in I._WHY_KINDS, name
    # Another component's row is not this sieve's subject.
    assert I.every_sieve_carries_its_why({"component": "testing_tool"}, BI) == []


def _set(key, value):
    return lambda rec: rec.__setitem__(key, value)


def _src(**kv):
    return lambda rec: rec.__setitem__("why_source", kv)


MUTATIONS = {
    "proofs_exist": ("remove", None),
    "charter_on_disk": ("edit", _set("why", "   ")),
    "silent_device": ("edit", _src(kind="hunch", of="5dbc03e007c5")),
    "sole_path_holds": ("edit", _src(
        kind="akien", quote="testing: words Akien never said here",
        at="CairnCommons/decisions/2026-08-08-inference-proxy-is-a-rules-stack.json")),
    "component_color": ("edit", _src(
        kind="akien", quote="Law 9 ruled as default-red by Akien",
        at="cairn/machines/build_inspector/inspector.py")),
    "history_integrity": ("edit", _src(kind="law", law="Law 11")),
    "learning_declared": ("edit", _src(kind="cc_reading", of="000000000000")),
    "gated_by_declared": ("edit", _src(kind="cc_reading", of="99.99.99")),
    "testing_orphan_record": ("orphan", None),
}


def test_each_mutation_reds_once_naming_its_sieve():
    I = _I()
    for name, (how, fn) in MUTATIONS.items():
        comp = _scratch_copy()
        if how == "remove":
            (comp / "sieves" / f"{name}.json").unlink()
        elif how == "edit":
            _edit(comp, name, fn)
        else:
            (comp / "sieves" / f"{name}.json").write_text(
                json.dumps({"name": name, "why": "testing", "why_source":
                            {"kind": "law", "law": "Law 3"}}), encoding="utf-8")
        found = I.every_sieve_carries_its_why(ROW, comp)
        assert [f["values"]["sieve"] for f in found] == [name], (name, found)
        assert all(f["method"] == "every_sieve_carries_its_why" for f in found)
        # The quote's at must be a record of Akien's words, never a sieve's source.
        if name == "component_color":
            assert "not where Akien's words are recorded" in found[0]["actual"], found
    # The same quote at its real address checks, whitespace folded.
    comp = _scratch_copy()
    _edit(comp, "sole_path_holds", _src(
        kind="akien", quote="NO OTHER  REACHING FOR\nINFERENCE VIA ANY OTHER MECHANISM IS ALLOWED",
        at="CairnCommons/decisions/2026-08-08-inference-proxy-is-a-rules-stack.json"))
    assert I.every_sieve_carries_its_why(ROW, comp) == []


WHY = "testing: this sieve exists so its refusal can be adjudicated against this sentence"


def _with_testing_sieve(body):
    """Run body() with the registry swapped for one always-red testing sieve whose record
    (in a scratch sieves/ dir) carries WHY. The gate's feedback write is stubbed: it would
    land in instance-space for a sieve that does not exist."""
    I = _I()
    from cairn.tools.base import transitions as T
    from cairn.tools.scratch.scratch import scratch_dir
    records = scratch_dir("testing-sieve-why-records-")
    (records / "testing_always_reds.json").write_text(json.dumps(
        {"name": "testing_always_reds", "why": WHY,
         "why_source": {"kind": "law", "law": "Law 3"}}), encoding="utf-8")

    def testing_always_reds(row, comp_dir):
        return [I._finding("testing_always_reds", row["component"], "testing red",
                           expected=0, actual=1)]

    saved = (I.SIEVES, I._NEST_CACHE, I._SIEVE_RECORDS, T.BUILD_GATE._collect_feedback)
    I.SIEVES = {"testing_always_reds": testing_always_reds}
    I._NEST_CACHE, I._SIEVE_RECORDS = None, records
    T.BUILD_GATE._collect_feedback = lambda *a, **k: None
    try:
        return body(I, T)
    finally:
        I.SIEVES, I._NEST_CACHE, I._SIEVE_RECORDS, T.BUILD_GATE._collect_feedback = saved


def test_inspect_stamps_the_sieve_why_on_its_findings():
    def body(I, T):
        report = I.inspect(root=BI.parent, component="build_inspector")
        assert report["findings"], report
        assert all(f["values"]["sieve_why"] == WHY for f in report["findings"]), report["findings"]
    _with_testing_sieve(body)


def test_the_proveme_refusal_carries_the_why():
    def body(I, T):
        try:
            T._build_gate(str(BI / "history.json"))
        except T.BuildGateRed as e:
            assert WHY in str(e), str(e)
            return
        raise AssertionError("the build gate did not refuse an always-red sieve")
    _with_testing_sieve(body)


def test_one_record_per_sieve_and_the_runners_file_moved():
    I = _I()
    assert sorted(p.stem for p in (BI / "sieves").glob("*.json")) == sorted(I.SIEVES)
    assert not (BI / "sieves" / "runners_leave_trails.json").exists()
    assert I._RUNNERS_FILE == BI / "runners_leave_trails.json"
    assert isinstance(I.declared_runners(), list) and I.declared_runners()


if __name__ == "__main__":
    tests = [test_the_live_records_carry_whys_that_check,
             test_each_mutation_reds_once_naming_its_sieve,
             test_inspect_stamps_the_sieve_why_on_its_findings,
             test_the_proveme_refusal_carries_the_why,
             test_one_record_per_sieve_and_the_runners_file_moved]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"PASS {t.__name__}")
        except Exception as e:  # noqa: BLE001 — a proof reports every tooth
            failed += 1
            print(f"FAIL {t.__name__}: {type(e).__name__}: {e}")
    print(f"{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
