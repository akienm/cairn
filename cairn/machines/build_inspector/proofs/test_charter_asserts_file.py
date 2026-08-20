"""Proof: a charter may not assert a file that is not there.

Teeth a hollow build could not pass:

  - A FALSE ASSERTION IS CAUGHT. A charter whose state_and_history names a file beside
    it that does not exist produces a finding. A build that always returns [] fails.
  - AN HONEST QUALIFICATION PASSES. A charter that acknowledges the absence — "born at
    this address's first crossing" — is not a present-tense claim and produces no finding.
  - A PRESENT FILE PASSES. A charter that names a file beside it that DOES exist produces
    no finding — the assertion is true.
  - THE CHECK IS NOT HARDCODED TO TWO FILENAMES. A charter asserting any *.json file
    beside it that is absent produces a finding, not just state.json and history.json
    (falsifier point 4).
  - THE LIVE CORPUS IS CLEAN. Every charter on disk passes the sieve after the corrections.

    python3 cairn/machines/build_inspector/proofs/test_charter_asserts_file.py   # exit 0 = green
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.machines.build_inspector.inspector import charter_asserts_file_present
from cairn.tools.base.address import component_dirs


def _make_charter(d: str, state_and_history: str, create_files: list[str] | None = None) -> Path:
    comp = Path(d) / "test_component"
    comp.mkdir(parents=True, exist_ok=True)
    charter = {"state_and_history": state_and_history}
    (comp / "intention+why.json").write_text(json.dumps(charter))
    for name in (create_files or []):
        (comp / name).write_text("{}")
    return comp


def test_false_assertion_is_caught():
    with tempfile.TemporaryDirectory() as d:
        comp = _make_charter(d, "state.json + history.json beside this charter, born at the carve-out.")
        result = charter_asserts_file_present({"component": "test_component"}, comp)
        assert len(result) >= 1, f"false assertion must be caught, got {result}"
        names = {f["evidence"]["asserted_file"] for f in result}
        assert "state.json" in names, f"state.json must be caught: {names}"
        assert "history.json" in names, f"history.json must be caught: {names}"


def test_honest_qualification_passes():
    with tempfile.TemporaryDirectory() as d:
        comp = _make_charter(
            d,
            "state.json + history.json beside this charter, BORN AT THIS ADDRESS'S "
            "FIRST CROSSING. Until a ticket crosses here there is no journal.")
        result = charter_asserts_file_present({"component": "test_component"}, comp)
        assert result == [], f"honest qualification must pass, got {result}"


def test_present_file_passes():
    with tempfile.TemporaryDirectory() as d:
        comp = _make_charter(
            d,
            "state.json + history.json beside this charter.",
            create_files=["state.json", "history.json"])
        result = charter_asserts_file_present({"component": "test_component"}, comp)
        assert result == [], f"present files must pass, got {result}"


def test_not_hardcoded_to_two_filenames():
    with tempfile.TemporaryDirectory() as d:
        comp = _make_charter(d, "config.json beside this charter, always present.")
        result = charter_asserts_file_present({"component": "test_component"}, comp)
        assert len(result) == 1, f"any asserted file must be caught, got {result}"
        assert result[0]["evidence"]["asserted_file"] == "config.json"


def test_live_corpus_is_clean():
    dirs, _ = component_dirs()
    failures = []
    for d in dirs:
        result = charter_asserts_file_present({"component": d.name}, d)
        if result:
            failures.extend(f"{f['component']}: {f['finding']}" for f in result)
    assert not failures, (
        f"the live corpus must be clean after corrections, {len(failures)} finding(s):\n"
        + "\n".join(failures))


def _main() -> int:
    checks = [
        test_false_assertion_is_caught,
        test_honest_qualification_passes,
        test_present_file_passes,
        test_not_hardcoded_to_two_filenames,
        test_live_corpus_is_clean,
    ]
    for c in checks:
        c()
        print(f"  PASS  {c.__name__}")
    print(f"green — charter_asserts_file_present ({len(checks)} teeth): "
          "a false assertion is caught, an honest qualification passes, present files "
          "pass, the check is not hardcoded to two filenames, and the live corpus is clean")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
