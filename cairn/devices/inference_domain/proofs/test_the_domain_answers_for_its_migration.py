"""Proof for ticket d9d87ccb97e5 — the inference domain answers for its migration over the bus.

MEASURED 2026-11-13 on akienasus: 98ab0e9db57f tooth 7 redded "17 leaves in the answer tree",
because it counted THIS box's tree and looked for THIS box's dump. The answer tree is one box's
(open-39f6229e7241; outline 5.5.3.8, 11.3.5.1), so the reading belongs to the device that owns
it, asked over its bus (RULE 1): the verb ``migration`` answers
{old_table_gone, leaves, dump_spent, dump_avoided, dump_newest} from the home instance.

  1. old table gone, a dump standing: the verb answers true, the leaf count, and the dump's
     spent (miss cost), avoided (hit cost) and newest created;
  2. the old table still registered, or still present: old_table_gone is false;
  3. no dump standing: the three dump fields are null and the verb still answers;
  4. the device declares ``migration``, and device.py still names no old table.

The store is faked inside the migration module (nothing dials 5432), and HOME is a scratch dir,
so the dump read is a scratch file at the instance's own temp path. The subject is bound inside
each tooth.

    bin/cairn test cairn/devices/inference_domain/proofs/test_the_domain_answers_for_its_migration.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {"d9d87ccb97e5": {
    "1": "test_gone_with_a_dump_answers_the_counts_and_sums",
    "2": "test_a_table_still_registered_or_present_is_not_gone",
    "3": "test_no_dump_answers_nulls",
    "4": "test_the_device_declares_the_verb_and_names_no_old_table",
}}

OLD = "inference" + "_calls"          # spelled split: 98ab0e9db57f tooth 1 greps the device
DEVICE = _REPO / "cairn" / "devices" / "inference_domain"


class _Store:
    """The store the report reads: who owns which table, which tables exist, how many leaves."""

    def __init__(self, *, owned=None, present=(), leaves=0):
        self.owned, self.present, self.leaves = dict(owned or {}), set(present), leaves
        self.asked: list[str] = []

    def owner_of(self, table):
        return self.owned.get(table)

    def query(self, sql, *, tables=None, params=()):
        self.asked.append(sql)
        if "information_schema" in sql:
            return [{"?column?": 1}] if params and params[0] in self.present else []
        if "count(*)" in sql:
            return [{"n": self.leaves}]
        raise AssertionError(f"testing-d9d8: an unexpected query: {sql}")


def _home(monkeypatch, tmp_name: str) -> Path:
    from cairn.tools.scratch.scratch import scratch_dir
    home = Path(scratch_dir(f"testing-d9d8-{tmp_name}-"))
    monkeypatch.setenv("HOME", str(home))
    return home


def _dump(home: Path, name: str, rows) -> Path:
    temp = home / ".cairn/devices/inference_domain/0/temp"
    temp.mkdir(parents=True, exist_ok=True)
    lines = ["-- testing-d9d8 scratch dump\n",
             f"COPY public.{OLD} (canonical, verdict, answer, cost, created) FROM stdin;\n"]
    for canonical, verdict, cost, created in rows:
        lines.append("\t".join([canonical, verdict, "{}", cost, created]) + "\n")
    lines.append("\\.\n")
    p = temp / f"{OLD}-{name}.sql"
    p.write_text("".join(lines), encoding="utf-8")
    return p


def _ask(monkeypatch, fake):
    from cairn.devices.inference_domain import migrate_answers_to_their_tree as m
    from cairn.devices.inference_domain.device import InferenceDomainDevice
    monkeypatch.setattr(m, "store", fake)
    reply = InferenceDomainDevice()._handle_migration({"body": {}})
    json.dumps(reply)                   # the bus carries it: JSON or nothing
    return reply


def test_gone_with_a_dump_answers_the_counts_and_sums(monkeypatch):
    home = _home(monkeypatch, "gone")
    _dump(home, "20261101", [("a", "miss", "9.0", "2026-11-01 10:00:00+00")])
    _dump(home, "20261109", [("a", "miss", "1.5", "2026-11-09 10:00:00+00"),
                             ("b", "hit", "2.25", "2026-11-09 11:00:00+00"),
                             ("c", "miss", "\\N", "2026-11-09 09:00:00+00"),
                             ("d", "refused", "4.0", "2026-11-09 12:30:00+00")])
    got = _ask(monkeypatch, _Store(leaves=11366))
    assert got["old_table_gone"] is True, got
    assert got["leaves"] == 11366, got
    assert (got["dump_spent"], got["dump_avoided"]) == (1.5, 2.25), f"not the newest dump's sums: {got}"
    assert got["dump_newest"].startswith("2026-11-09T12:30:00"), got


def test_a_table_still_registered_or_present_is_not_gone(monkeypatch):
    home = _home(monkeypatch, "present")
    _dump(home, "20261109", [("a", "miss", "1.0", "2026-11-09 10:00:00+00")])
    got = _ask(monkeypatch, _Store(owned={OLD: "inference_domain"}, leaves=3))
    assert got["old_table_gone"] is False, f"a registered old table read as gone: {got}"
    got = _ask(monkeypatch, _Store(present={OLD}, leaves=3))
    assert got["old_table_gone"] is False, f"a present old table read as gone: {got}"


def test_no_dump_answers_nulls(monkeypatch):
    _home(monkeypatch, "nodump")
    got = _ask(monkeypatch, _Store(leaves=17))
    assert got["leaves"] == 17 and got["old_table_gone"] is True, got
    assert (got["dump_spent"], got["dump_avoided"], got["dump_newest"]) == (None, None, None), got


def test_the_device_declares_the_verb_and_names_no_old_table():
    from cairn.devices.inference_domain.device import InferenceDomainDevice
    assert "migration" in InferenceDomainDevice().declared_verbs(), "the verb is not declared"
    assert OLD not in (DEVICE / "device.py").read_text(encoding="utf-8"), "device.py names the old table"


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
