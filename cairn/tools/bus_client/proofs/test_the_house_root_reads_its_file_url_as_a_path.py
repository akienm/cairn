r"""Proof for ticket 7579b542b4d4 "the house root reads its editable install's file URL as a path".

MEASURED 2026-11-14 on akiendell (Windows): the editable install's direct_url.json holds
``file:///C:/automation/local/cairn``, and ``_house_root()`` answered
``C:\C:\automation\local\cairn``. Stripping "file://" left "/C:/...", which Windows resolves
onto the current drive. So the house checkout's own client never matched the house root: every
client there, the house's included, was refused a replace of a stale live bus (ticket
3deafc9e36de), and BusStale named a path that does not exist (Law 7: the diagnostic hid the
real one). The same strip leaves a space as "%20" on every box.

  1. test_the_box_s_own_checkout_reads_back_as_itself: the install URL is built from this
     checkout's real path with Path.as_uri(), the platform's own encoding; _house_root() answers
     that path. Reds on Windows under the strip.
  2. test_a_percent_encoded_path_is_decoded: a scratch directory whose name holds a space reads
     back with the space, not "%20". Reds on every box under the strip.

``importlib.metadata.distribution`` is replaced inside each tooth; no install is touched.

    bin/cairn test cairn/tools/bus_client/proofs/test_the_house_root_reads_its_file_url_as_a_path.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {"7579b542b4d4": {
    "1": "test_the_box_s_own_checkout_reads_back_as_itself",
    "2": "test_a_percent_encoded_path_is_decoded",
}}

_ENV = "CAIRN_BUS_CLIENT_HOUSE_ROOT"


def _installed_at(monkeypatch, where: Path):
    """The editable install's direct_url.json says ``where``, as pip writes it."""
    from cairn.tools.bus_client import remote
    monkeypatch.delenv(_ENV, raising=False)
    doc = json.dumps({"dir_info": {"editable": True}, "url": where.as_uri()})

    class _Dist:
        def read_text(self, name):
            return doc if name == "direct_url.json" else None
    monkeypatch.setattr(remote.importlib.metadata, "distribution", lambda name: _Dist())
    return remote


def test_the_box_s_own_checkout_reads_back_as_itself(monkeypatch):
    here = _REPO.resolve()
    remote = _installed_at(monkeypatch, here)
    got = remote._house_root()
    assert got == here, f"the install URL {here.as_uri()} read back as {got}, not {here}"


def test_a_percent_encoded_path_is_decoded(monkeypatch):
    from cairn.tools.scratch.scratch import scratch_dir
    spaced = (Path(scratch_dir("testing-7579-house-")) / "a house root").resolve()
    spaced.mkdir()
    remote = _installed_at(monkeypatch, spaced)
    assert "%20" in spaced.as_uri(), spaced.as_uri()
    got = remote._house_root()
    assert got == spaced, f"the install URL {spaced.as_uri()} read back as {got}, not {spaced}"


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
