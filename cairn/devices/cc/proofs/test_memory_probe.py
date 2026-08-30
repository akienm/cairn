"""Proofs for the memory curve probe — teeth a hollow build could not pass.

Four things the ticket's falsifier demands:
  (1) the probe loads via ProbeCache with zero failures
  (2) a sample produces a non-empty series with positive cgroup_bytes
  (3) cgroup_bytes matches an independent read within one page (4096 bytes)
  (4) rss_bytes is present and distinct from cgroup_bytes
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _isolate_series(tmp_path, monkeypatch):
    series = tmp_path / "memory_series.jsonl"
    import cairn.devices.cc.probes.memory_curve as mod
    monkeypatch.setattr(mod, "_SERIES_PATH", series)
    yield series


def test_probe_loads_via_probecache_with_zero_failures():
    from cairn.devices.cairn.machines.ground_loop.discovery import ProbeCache

    probes, failures = ProbeCache().probes_for(Path("cairn/devices/cc/probes"))
    assert len(failures) == 0, f"probe loading failures: {failures}"
    names = [p.why for p in probes]
    assert any("memory" in w for w in names), (
        f"memory probe not found among {names}"
    )


def test_sample_produces_nonempty_series_with_positive_cgroup(_isolate_series):
    from cairn.devices.cc.probes.memory_curve import sample

    rec = sample()
    assert isinstance(rec["cgroup_bytes"], int) and rec["cgroup_bytes"] > 0, (
        f"cgroup_bytes must be a positive int, got {rec['cgroup_bytes']}"
    )
    lines = _isolate_series.read_text().strip().splitlines()
    assert len(lines) == 1, f"expected 1 line after 1 sample, got {len(lines)}"
    parsed = json.loads(lines[0])
    assert parsed["cgroup_bytes"] == rec["cgroup_bytes"]


def test_cgroup_matches_independent_read_within_one_page(_isolate_series):
    from cairn.devices.cc.probes.memory_curve import sample, _cgroup_path

    rec = sample()
    cgroup = _cgroup_path()
    assert cgroup is not None, "no cgroup v2 path found"
    direct = int(Path(f"/sys/fs/cgroup{cgroup}/memory.current").read_text().strip())
    delta = abs(rec["cgroup_bytes"] - direct)
    assert delta <= 4096, (
        f"cgroup_bytes {rec['cgroup_bytes']} vs independent {direct}, "
        f"delta {delta} exceeds one page (4096)"
    )


def test_rss_present_and_distinct_from_cgroup(_isolate_series):
    from cairn.devices.cc.probes.memory_curve import sample

    rec = sample()
    assert isinstance(rec["rss_bytes"], int) and rec["rss_bytes"] > 0, (
        f"rss_bytes must be a positive int, got {rec['rss_bytes']}"
    )
    assert rec["rss_bytes"] != rec["cgroup_bytes"], (
        f"rss_bytes and cgroup_bytes are both {rec['rss_bytes']} — "
        f"the distinction this ticket exists to make is absent"
    )


def test_series_grows_monotonically(_isolate_series):
    from cairn.devices.cc.probes.memory_curve import sample

    for _ in range(3):
        sample()
    lines = _isolate_series.read_text().strip().splitlines()
    assert len(lines) == 3, f"expected 3 lines after 3 samples, got {len(lines)}"
    sizes = []
    for line in lines:
        rec = json.loads(line)
        assert "cgroup_bytes" in rec and "rss_bytes" in rec
        sizes.append(rec["ts"])
    assert sizes == sorted(sizes), f"timestamps not monotonically increasing: {sizes}"
