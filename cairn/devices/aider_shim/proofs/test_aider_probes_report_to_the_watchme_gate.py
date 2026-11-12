"""Proof for ticket 0e0f208bb893 — aider_shim's four standing probes report to CodeMother's
WATCHME gate (a child of 835b5736bf2b, every probe has a receiver).

Each probe posts its verdict against ITS OWN ticket's falsifier to codemother's
`machines/watchme/watch` verb through `watch_carry`, and each ticket's WATCHME spec names that
gate as its receiver. One tooth per falsifier clause:

  1. each PROBE posts to codemother, verb machines/watchme/watch, and its carry returns its own
     ticket's 12-hex id with a bool `holds`;
  2. each predicate reads False on its own falsifying rows and True on rows that do not
     falsify;
  3. each ticket's WATCHME spec carries the receiver.

    bin/cairn test cairn/devices/aider_shim/proofs/test_aider_probes_report_to_the_watchme_gate.py
"""

from __future__ import annotations

import importlib
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"0e0f208bb893": {
    "1": "test_each_probe_posts_to_the_watchme_gate_with_its_own_ticket",
    "2": "test_each_predicate_reads_its_own_falsifier",
    "3": "test_each_spec_names_the_watchme_gate_as_receiver",
}}

PROBES = {
    "edit_survival_probe": "6d3e689b0bf8",
    "offload_yield_probe": "d7b4019d2407",
    "reflection_earns_its_ask": "e9b0a8d4fb99",
    "writes_to_is_where_it_landed_probe": "68f1fc073512",
}
RECEIVER = {"what": "codemother watchme gate", "in": "cairn/devices/codemother/machines/watchme"}


def _probe(name):
    return importlib.import_module(f"cairn.devices.aider_shim.probes.{name}")


def _empty_context(tmp: Path) -> dict:
    """Every reader pointed at a place holding nothing, so no live record decides a tooth."""
    return {"drives_path": tmp / "drives.jsonl", "ask_log": tmp / "asks.jsonl",
            "berths_root": tmp / "berths", "root": tmp}


class _Substituted:
    """Swap a module's own reader for a row source, and put it back."""

    def __init__(self, module, **names):
        self.module, self.names, self.saved = module, names, {}

    def __enter__(self):
        for k, v in self.names.items():
            self.saved[k] = getattr(self.module, k)
            setattr(self.module, k, v)
        return self.module

    def __exit__(self, *exc):
        for k, v in self.saved.items():
            setattr(self.module, k, v)


def test_each_probe_posts_to_the_watchme_gate_with_its_own_ticket():
    with tempfile.TemporaryDirectory() as tmp:
        ctx = _empty_context(Path(tmp))
        for name, tid in PROBES.items():
            p = _probe(name).PROBE
            assert p.to == "codemother", (name, p.to)
            assert p.verb == "machines/watchme/watch", (name, p.verb)
            c = p.carry(ctx)
            assert c["ticket"] == tid, (name, c["ticket"])
            assert isinstance(c["holds"], bool), (name, c["holds"])
            assert c["holds"] is True, (name, c.get("finding"))   # nothing recorded falsifies nothing


def test_each_predicate_reads_its_own_falsifier():
    ctx = {}
    m = _probe("reflection_earns_its_ask")
    with _Substituted(m, readings=lambda **k: [{"x": 1}], falsifications=lambda rows: [{"which": "w"}]):
        assert m._holds(ctx) is False, "a stop-early observation must falsify"
    with _Substituted(m, readings=lambda **k: [{"x": 1}], falsifications=lambda rows: []):
        assert m._holds(ctx) is True, "no stop-early observation is still counting"

    m = _probe("writes_to_is_where_it_landed_probe")
    with _Substituted(m, readings=lambda **k: [{"disposition": m.INSIDE}, {"disposition": m.OUTSIDE}]):
        assert m._holds(ctx) is False, "a landed-outside drive is the finding"
    with _Substituted(m, readings=lambda **k: [{"disposition": m.INSIDE}, {"disposition": m.MIXED},
                                              {"disposition": m.NO_EDIT}]):
        assert m._holds(ctx) is True, "inside/mixed/no-edit do not falsify"

    m = _probe("edit_survival_probe")
    rows = lambda *ds: (lambda **k: [{"disposition": d} for d in ds])  # noqa: E731
    with _Substituted(m, dispositions=rows(*["rewritten"] * 5)):
        assert m._holds(ctx) is False, "five rewritten, none survived, is the wrong-intent tell"
        c = m.PROBE.carry(ctx)
        assert c["holds"] is False and "wrong-intent" in c["finding"], c["finding"]
    with _Substituted(m, dispositions=rows("rewritten", "discarded", "rewritten", "survived", "survived")):
        assert m._holds(ctx) is False, "the hand's three over two survived falsifies"
    with _Substituted(m, dispositions=rows("rewritten", "survived", "survived", "survived", "discarded")):
        assert m._holds(ctx) is True, "survival in the majority holds"
    with _Substituted(m, dispositions=rows(*["rewritten"] * 4, "not-applied")):
        assert m._holds(ctx) is True, "below enough the watch is still counting"

    m = _probe("offload_yield_probe")
    assert m._holds(ctx) is True, "cc_calls is a declared hole: no row can falsify it yet"


def test_each_spec_names_the_watchme_gate_as_receiver():
    from cairn.tools.chain.grammar import ticket_path
    from cairn.tools.base.ticket_file import read_ticket
    for name, tid in PROBES.items():
        spec = read_ticket(Path(ticket_path(tid)))["watchme"]
        assert spec.get("receiver") == RECEIVER, (tid, spec.get("receiver"))
        assert spec["probe"].endswith(f"probes/{name}.py"), (tid, spec["probe"])


def main() -> int:
    teeth = [v for k, v in globals().items() if k.startswith("test_") and callable(v)]
    failed = 0
    for t in teeth:
        try:
            t()
            print(f"  ok   {t.__name__}")
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"  FAIL {t.__name__}: {type(exc).__name__}: {exc}")
    print(f"{len(teeth) - failed}/{len(teeth)} green")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
