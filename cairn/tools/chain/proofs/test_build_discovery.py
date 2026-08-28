"""Proof: the build-discovery detector finds uncharted modifications.

Teeth that GRIP both directions (ticket a-build-discovery-re-enters-the-chain):
  - a seeded chain naming every touched file -> empty finding
  - a seeded voyage with a known inline edit not in any berth -> names the file
  - stubbing the detector to always return empty makes the inline-edit test RED
"""
from __future__ import annotations

import json
import os
import tempfile

import pytest

from cairn.tools.chain.chain import charted_paths, uncharted_modifications


@pytest.fixture
def chain_dir():
    with tempfile.TemporaryDirectory() as d:
        yield d


def _write_berth(d, stage, content):
    path = os.path.join(d, f"{stage}.json")
    with open(path, "w") as f:
        json.dump(content, f)
    return path


def test_charted_paths_reads_holdings_and_uses(chain_dir):
    chain = {
        "survey": _write_berth(chain_dir, "survey", {
            "holdings": [
                {"address": "cairn/tools/chain/chain.py", "what": "the chain tool"},
                {"address": "cairn/tools/base/transitions.py", "what": "the chokepoint"},
            ],
        }),
        "decompose": _write_berth(chain_dir, "decompose", {
            "sub_problems": [
                {"uses": ["cairn/tools/chain/chain.py"],
                 "writes_to": ["cairn/tools/chain/proofs/test_build_discovery.py"]},
            ],
        }),
        "orient": _write_berth(chain_dir, "orient", {
            "refs": ["cairn/tools/chain", "cairn/tools/base/transitions.py"],
        }),
    }
    paths = charted_paths(chain)
    assert "cairn/tools/chain/chain.py" in paths
    assert "cairn/tools/base/transitions.py" in paths
    assert "cairn/tools/chain/proofs/test_build_discovery.py" in paths
    assert "cairn/tools/chain" in paths


def test_clean_chain_returns_empty(chain_dir):
    """A chain naming every modified file -> empty finding."""
    chain = {
        "survey": _write_berth(chain_dir, "survey", {
            "holdings": [
                {"address": "cairn/tools/chain/chain.py", "what": "the chain tool"},
                {"address": "cairn/tools/base/transitions.py", "what": "the chokepoint"},
            ],
        }),
    }
    charted = charted_paths(chain)
    modified = ["cairn/tools/chain/chain.py", "cairn/tools/base/transitions.py"]
    added = []
    findings = uncharted_modifications(charted, modified, added)
    assert findings == [], f"expected empty findings, got {findings}"


def test_inline_edit_is_named(chain_dir):
    """A modified file not in any berth -> the detector names it."""
    chain = {
        "survey": _write_berth(chain_dir, "survey", {
            "holdings": [
                {"address": "cairn/tools/chain/chain.py", "what": "the chain tool"},
            ],
        }),
    }
    charted = charted_paths(chain)
    modified = ["cairn/tools/chain/chain.py", "cairn/machines/build_inspector/inspector.py"]
    added = []
    findings = uncharted_modifications(charted, modified, added)
    assert "cairn/machines/build_inspector/inspector.py" in findings


def test_added_files_are_excluded(chain_dir):
    """Added files are excluded — new files cannot appear in a chart that predates them."""
    chain = {
        "survey": _write_berth(chain_dir, "survey", {
            "holdings": [
                {"address": "cairn/tools/chain/chain.py", "what": "the chain tool"},
            ],
        }),
    }
    charted = charted_paths(chain)
    modified = ["cairn/tools/chain/chain.py", "cairn/tools/chain/new_module.py"]
    added = ["cairn/tools/chain/new_module.py"]
    findings = uncharted_modifications(charted, modified, added)
    assert findings == [], f"added file should be excluded, got {findings}"


def test_substring_match_is_generous(chain_dir):
    """A ref 'cairn/tools/chain' covers 'cairn/tools/chain/chain.py'."""
    chain = {
        "orient": _write_berth(chain_dir, "orient", {
            "refs": ["cairn/tools/chain"],
        }),
    }
    charted = charted_paths(chain)
    modified = ["cairn/tools/chain/chain.py"]
    added = []
    findings = uncharted_modifications(charted, modified, added)
    assert findings == [], f"substring match should cover, got {findings}"


def test_empty_chain_returns_all_modified():
    """An empty chain -> every modified file is uncharted."""
    charted = charted_paths({})
    modified = ["cairn/tools/chain/chain.py", "cairn/tools/base/transitions.py"]
    findings = uncharted_modifications(charted, modified, [])
    assert len(findings) == 2


def test_missing_berth_is_graceful(chain_dir):
    """A berth path that does not exist is skipped, not an error."""
    chain = {
        "survey": os.path.join(chain_dir, "nonexistent.json"),
    }
    paths = charted_paths(chain)
    assert paths == set()
