"""A green measured under other conditions than its red completes and tells the operator (ticket f0aad0cd0f56).

Akien's answer to open-ed0a56ce6357: "something where the system works... but it doesn't match
the model in my head. so it passes the before test before, and the after test after, but only
because the conditions of measurment have changed ... that's probably an item to check with
operator" — and "we let it complete AND notify me". So every sealed run records the conditions
it was measured under (proof bytes, fixture bytes, interpreter, isolation, timeout, the CAIRN_*
environment as digests), and a green seal that replaces a red recorded under other conditions
seals green AND posts one notice naming each changed condition. A red never posts, an unsealed
run never posts, and a red that predates the instrument compares nothing and says so.

The teeth drive the real run_proof (and tooth 7 the real reseal door, decision D9) over a one-tooth fixture proof in scratch. The store's read
and write are replaced by recorders (the store REPLACES, so the standing record a green reads is
the red it replaces); notices berth in scratch. Every tooth imports the tester INSIDE its body,
so a reverted device.py or conditions.py reds teeth instead of breaking this file's import.
"""
from __future__ import annotations

import contextlib
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROVES = {"f0aad0cd0f56": {
    "1": "test_a_sealed_run_records_its_conditions_with_env_as_digests",
    "2": "test_a_green_over_a_red_under_another_timeout_posts_one_notice",
    "3": "test_a_green_over_a_red_under_the_same_conditions_posts_nothing",
    "4": "test_a_red_that_predates_the_instrument_compares_nothing",
    "5": "test_a_red_never_posts",
    "6": "test_an_unsealed_run_never_posts",
    "7": "test_a_reseal_green_over_a_red_under_other_conditions_notifies",
}}

_FIXTURE = '''import sys
from pathlib import Path
PROVES = {"aaaaaaaaaaaa": {"1": "test_fixture_tooth"}}
if (Path(__file__).parent / "RED").exists():
    print("FAIL test_fixture_tooth")
    sys.exit(1)
print("ok   test_fixture_tooth")
'''
_SWEEP = {"skipped": "proof fixture: a scratch component, nothing to sweep"}


def _component(prefix: str, *, red: bool = False) -> Path:
    root = scratch_dir(prefix) / "fixture_component"
    (root / "proofs" / "fixtures").mkdir(parents=True)
    (root / "proofs" / "fixtures" / "data.txt").write_text("fixture bytes\n")
    proof = root / "proofs" / "test_fixture.py"
    proof.write_text(_FIXTURE)
    if red:
        (root / "proofs" / "RED").write_text("")
    return proof


@contextlib.contextmanager
def _store(standing: list, home: Path):
    """read_validations answers `standing`; persist_validation records instead of writing."""
    import cairn.tools.validation_store.validation_store as vs
    from cairn.devices.tester import notices
    persisted: list = []
    saved = (vs.read_validations, vs.persist_validation, notices.HOME)
    vs.read_validations = lambda proof_path=None, **kw: list(standing)
    vs.persist_validation = lambda record, **kw: persisted.append(record) or "recorded"
    notices.HOME = home
    try:
        yield persisted
    finally:
        vs.read_validations, vs.persist_validation, notices.HOME = saved


def _run(proof: Path, *, sink: str, timeout: int) -> dict:
    from cairn.devices.tester.device import TesterDevice
    kw = {"scratch_sweep": dict(_SWEEP)} if sink == "validations" else {}
    return TesterDevice().run_proof(proof, sink=sink, caller="proof-fixture", timeout=timeout,
                                    isolation="none", **kw)


def _red_like(rec: dict, **changes) -> dict:
    red = {k: v for k, v in rec.items()}
    ev = dict(rec["evidence"])
    if "conditions" in ev:
        ev["conditions"] = dict(ev["conditions"], **changes)
    red["evidence"], red["verdict"] = ev, "red"
    return red


def _notices(home: Path) -> list:
    return sorted(home.glob("n-*.json")) if home.is_dir() else []


def test_a_sealed_run_records_its_conditions_with_env_as_digests():
    import hashlib
    import json
    import os
    proof = _component("cairn-condproof-1-")
    home = proof.parents[2] / "notices"
    mark, value = "CAIRN_CONDPROOF_MARK", "condproof-raw-value-never-recorded"
    prior = os.environ.get(mark)
    os.environ[mark] = value
    try:
        with _store([], home) as persisted:
            rec = _run(proof, sink="validations", timeout=61)
    finally:
        if prior is None:
            os.environ.pop(mark, None)
        else:
            os.environ[mark] = prior
    assert rec["verdict"] == "green", rec["evidence"].get("stderr_tail")
    assert persisted and persisted[0] is rec, persisted
    cond = rec["evidence"]["conditions"]
    assert set(cond) == {"proof", "fixtures", "interpreter", "isolation", "timeout", "env"}, cond
    assert cond["timeout"] == 61 and cond["fixtures"], cond
    assert cond["proof"] == hashlib.sha256(proof.read_bytes()).hexdigest(), cond
    assert sys.executable in cond["interpreter"] and cond["isolation"].startswith("none"), cond
    assert cond["env"].get(mark) == hashlib.sha256(value.encode()).hexdigest()[:12], cond["env"]
    assert all(k.startswith("CAIRN_") and len(v) == 12 for k, v in cond["env"].items()), cond
    assert value not in json.dumps(rec), "a raw CAIRN_* value entered the record"


def test_a_green_over_a_red_under_another_timeout_posts_one_notice():
    import json
    proof = _component("cairn-condproof-2-")
    home = proof.parents[2] / "notices"
    with _store([], home):
        first = _run(proof, sink="validations", timeout=60)
    red = _red_like(first, timeout=30)
    with _store([red], home) as persisted:
        rec = _run(proof, sink="validations", timeout=60)
    assert rec["verdict"] == "green", rec["evidence"].get("stderr_tail")
    moved = rec["evidence"].get("conditions_moved")
    assert moved and moved["changed"] == ["timeout"] and moved["notified"].startswith("n-"), moved
    files = _notices(home)
    assert [p.stem for p in files] == [moved["notified"]], files
    n = json.loads(files[0].read_text())
    assert n["ticket"] == "aaaaaaaaaaaa" and n["file"] == str(proof), n
    assert "timeout: 30 -> 60" in n["diff"] and "timeout" in n["line"], n
    assert persisted and persisted[0] is rec, persisted
    with _store([red], home):
        again = _run(proof, sink="validations", timeout=60)
    assert again["evidence"]["conditions_moved"]["notified"] == moved["notified"], again["evidence"]
    assert len(_notices(home)) == 1, _notices(home)


def test_a_green_over_a_red_under_the_same_conditions_posts_nothing():
    proof = _component("cairn-condproof-3-")
    home = proof.parents[2] / "notices"
    with _store([], home):
        first = _run(proof, sink="validations", timeout=60)
    assert "conditions" in first["evidence"], first["evidence"]
    with _store([_red_like(first)], home):
        rec = _run(proof, sink="validations", timeout=60)
    assert rec["verdict"] == "green", rec["evidence"].get("stderr_tail")
    assert "conditions_moved" not in rec["evidence"], rec["evidence"]
    assert "conditions_compared" not in rec["evidence"], rec["evidence"]
    assert _notices(home) == [], _notices(home)


def test_a_red_that_predates_the_instrument_compares_nothing():
    proof = _component("cairn-condproof-4-")
    home = proof.parents[2] / "notices"
    with _store([], home):
        first = _run(proof, sink="validations", timeout=60)
    legacy = _red_like(first)
    legacy["evidence"] = {k: v for k, v in legacy["evidence"].items() if k != "conditions"}
    with _store([legacy], home):
        rec = _run(proof, sink="validations", timeout=90)
    assert rec["verdict"] == "green", rec["evidence"].get("stderr_tail")
    assert "conditions_moved" not in rec["evidence"], rec["evidence"]
    said = rec["evidence"].get("conditions_compared", "")
    assert "predates" in said, rec["evidence"]
    assert _notices(home) == [], _notices(home)


def test_a_red_never_posts():
    proof = _component("cairn-condproof-5-", red=True)
    home = proof.parents[2] / "notices"
    with _store([], home):
        first = _run(proof, sink="validations", timeout=60)
    assert first["verdict"] == "red", first["evidence"]
    assert "conditions" in first["evidence"], first["evidence"]
    with _store([_red_like(first, timeout=30)], home):
        rec = _run(proof, sink="validations", timeout=60)
    assert rec["verdict"] == "red", rec["evidence"]
    assert "conditions_moved" not in rec["evidence"], rec["evidence"]
    assert _notices(home) == [], _notices(home)


def test_an_unsealed_run_never_posts():
    proof = _component("cairn-condproof-6-")
    home = proof.parents[2] / "notices"
    with _store([], home):
        first = _run(proof, sink="none", timeout=60)
    assert "conditions" in first["evidence"], first["evidence"]
    with _store([_red_like(first, timeout=30)], home) as persisted:
        rec = _run(proof, sink="none", timeout=60)
    assert rec["verdict"] == "green", rec["evidence"].get("stderr_tail")
    assert "conditions_moved" not in rec["evidence"] and persisted == [], rec["evidence"]
    assert _notices(home) == [], _notices(home)


class _QuietRaiser:
    """Stands in for the reseal door's trouble raiser: a fixture files no troubles."""

    def raise_trouble(self, *a, **kw):
        return None

    def clear_trouble(self, *a, **kw):
        return None


def test_a_reseal_green_over_a_red_under_other_conditions_notifies():
    import json
    proof = _component("cairn-condproof-7-")
    home = proof.parents[2] / "notices"
    with _store([], home):
        first = _run(proof, sink="none", timeout=60)
    red = _red_like(first, timeout=30)
    from cairn.devices.tester import reseal as rs
    from cairn.devices.tester.device import TesterDevice
    persisted: list = []
    saved = (rs.standing, rs.read_ladder, rs.persist_validation, rs.sweep_scratch)
    rs.standing = lambda p: {"proven": False, "seal": red, "why": "proof fixture: a standing red"}
    rs.read_ladder = lambda p: None
    rs.persist_validation = lambda record, **kw: persisted.append(record) or "recorded"
    rs.sweep_scratch = lambda: dict(_SWEEP)
    try:
        with _store([red], home):
            out = rs.reseal(proof, tester=TesterDevice(), raiser=_QuietRaiser(),
                            timeout=60, isolation="none")
    finally:
        rs.standing, rs.read_ladder, rs.persist_validation, rs.sweep_scratch = saved
    assert out["outcome"] in ("sealed", "resealed") and len(persisted) == 1, (out, persisted)
    moved = persisted[0]["evidence"].get("conditions_moved")
    assert moved and moved["changed"] == ["timeout"] and moved["notified"].startswith("n-"), moved
    files = _notices(home)
    assert [p.stem for p in files] == [moved["notified"]], files
    assert "timeout: 30 -> 60" in json.loads(files[0].read_text())["diff"], files


def main() -> int:
    fails = 0
    for name in PROVES["f0aad0cd0f56"].values():
        try:
            globals()[name]()
            print(f"  ok   {name}")
        except Exception as exc:  # noqa: BLE001 — every tooth reports, none hides
            fails += 1
            print(f"  FAIL {name}: {type(exc).__name__}: {exc}")
    print("RED" if fails else "GREEN")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
