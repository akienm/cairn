"""Proof of the counting block — ticket 5a4ec289bf15.

The world is SCRATCH: two journal roots the artifact door is pointed at through
``set_diagnostic_roots``, a scratch instance root for the block's emissions and the
trouble shim's watermark, and a scratch trouble store the drain folds into. Nothing here
writes the live journals, the live table, or the live store. The one live read is clause
5's — the compression invariant over the corpus on this box — and it asserts a ratio,
never a number (memory proof-over-live-data-assert-invariants).

Journal entries are HAND-BUILT with the caller class the tooth needs (an akien-class
clearance cannot be produced from inside a cc session; the class is the kernel's word and
the fold's whole input), appended through the door's own chain so the scratch journals
are real journals.

Teeth are declared per falsifier clause (1)…(5). The subject's names are resolved AT CALL
TIME (``_Late``) so a hollow revert of block.py reds every tooth instead of killing the
proof at import (UNRAN is not evidence).
"""
from __future__ import annotations

import datetime
import importlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from cairn.tools.artifact import artifact as door


class _Late:
    def __init__(self, module):
        self._module = module

    def __getattr__(self, name):
        return getattr(importlib.import_module(self._module), name)


block = _Late("cairn.machines.counting_block.block")
pulse_mod = _Late("cairn.machines.counting_block.groundloop.pulse")
probe_mod = _Late("cairn.machines.counting_block.probes.raise_rate_falls")

PROVES = {
    "5a4ec289bf15": {
        "1": "the_table_compiles_from_both_journals_and_is_byte_identical_when_recompiled",
        "2": "an_unseen_triple_raises_exactly_one_trouble_and_a_seen_one_raises_nothing",
        "3": "an_akien_clearance_teaches_the_row_and_a_cc_clearance_does_not",
        "4": "the_block_runs_on_the_beat_with_no_process_of_its_own_and_the_probe_fires_once_per_raise",
        "5": "over_the_live_corpus_rows_are_well_under_entries",
    },
}

PASS = 0
FAIL = 0
_TMP: list[str] = []


def _scratch(prefix):
    d = tempfile.mkdtemp(prefix=prefix)
    _TMP.append(d)
    return Path(d)


def _tooth(name, fn):
    global PASS, FAIL
    try:
        fn()
    except Exception as exc:  # noqa: BLE001 — a proof reports, never hides
        FAIL += 1
        print(f"  RED   {name}: {type(exc).__name__}: {exc}")
    else:
        PASS += 1
        print(f"  green {name}")


# ---------------------------------------------------------------------------
# THE SCRATCH WORLD


class World:
    """Two journal roots, an instance root, a table dir, a clock. ``append`` hand-builds an
    entry with the caller class asked for and chains it through the door."""

    def __init__(self):
        base = _scratch("counting-block-proof-")
        self.roots = {"cairn": base / "cairn", "CairnCommons": base / "CairnCommons"}
        for r in self.roots.values():
            r.mkdir(parents=True)
        self.instance = base / "instance"
        self.iroots = {"instance": self.instance}
        self.table = base / "table"
        self.store = self.roots["CairnCommons"] / "troubles"
        self.t = datetime.datetime(2026, 9, 17, 12, 0, 0, tzinfo=datetime.timezone.utc)
        door.set_diagnostic_roots(dict(self.roots))

    def close(self):
        door.set_diagnostic_roots(None)

    def append(self, root: str, rel: str, verb: str, cls: str, why: str = "seeded by the proof"):
        self.t += datetime.timedelta(seconds=1)
        entry = door._entry(Path(rel), verb, why, None, b"{}")
        entry["at"] = self.t.isoformat(timespec="seconds")
        entry["caller"] = {"class": cls, "cgroup": f"/proof/{cls}.scope", "unit": f"{cls}.scope",
                           "ancestry": []}
        return door._append(self.roots[root], entry)

    def raiser(self):
        from cairn.tools.base.diagnostic import ModuleRaiser
        return ModuleRaiser(block.COMPONENT, roots=self.iroots)

    def pulse(self):
        return block.pulse(roots=self.roots, raiser=self.raiser(), where=self.table, now=self.t)

    def table_doc(self):
        return json.loads((self.table / block.TABLE_FILE).read_text())

    def drain(self):
        from cairn.devices.trouble.shim import TroubleShim
        shim = TroubleShim(roots=self.iroots, root=self.store)
        out = shim.drain()
        assert out["outcome"] == "ok" and not out.get("refused"), out
        return out

    def live_troubles(self):
        from cairn.devices.trouble.trouble import TroubleDevice
        return {t["id"]: t for t in TroubleDevice(root=self.store).live()}


PRIOR = [
    # the shape of the live corpus on 2026-09-17, a few of each: the prior every judged entry
    # is read against. The trouble store's own rows are here so the store's writes inside
    # this proof (raise, clear by the device) are seen triples, not raises of their own.
    ("CairnCommons", "tickets/aaaa.json", "genesis", "cc"),
    ("CairnCommons", "tickets/aaaa.json", "cast", "cc"),
    ("CairnCommons", "tickets/bbbb.json", "cast", "cc"),
    ("CairnCommons", "slates/s1.json", "slate", "cc"),
    ("CairnCommons", "troubles/old-one.json", "genesis", "cc"),
    ("CairnCommons", "troubles/old-one.json", "raise", "cc"),
    ("CairnCommons", "troubles/old-one.json", "clear", "cc"),
    # one akien-class clearance in the prior: on the live corpus (0 akien entries on
    # 2026-09-17) the FIRST akien clearance is itself news and raises its own row — which
    # Akien clears, settling it — and that first-day flap is not what clause 3 measures
    ("CairnCommons", "troubles/old-two.json", "clear", "akien"),
    ("cairn", "cairn/devices/x/history.json", "append", "cc"),
    ("cairn", "cairn/devices/x/state.json", "append", "cc"),
    ("cairn", "cairn/devices/x/intention+why.json", "genesis", "cc"),
    ("cairn", "cairn/devices/x/validations/test_x.json", "seal", "cc"),
]


def _seed(w: World, arm: bool = True):
    for root, rel, verb, cls in PRIOR:
        w.append(root, rel, verb, cls)
    if arm:
        w.append("cairn", block.CHARTER_REL, block.ARMING_VERB, "cc", "the charter is born — arming")


UNSEEN_1 = ("cairn", "cairn/devices/y/state.json", "hand-edit", "gate")
UNSEEN_2 = ("CairnCommons", "slates/s2.json", "remove", "cc")
SEEN = ("CairnCommons", "tickets/cccc.json", "cast", "cc")


def _key(root, rel, verb, cls):
    return block.triple(block.path_class(root, rel), verb, cls)


# ---------------------------------------------------------------------------
# THE TEETH


def the_table_compiles_from_both_journals_and_is_byte_identical_when_recompiled():
    w = World()
    try:
        _seed(w)
        j = block.read_journals(w.roots)
        assert set(j) == {"cairn", "CairnCommons"} and all(j.values()), "both journals read"
        a = block.render(block.compile(j))
        b = block.render(block.compile(block.read_journals(w.roots)))
        assert a == b, "two folds of the same journals differ"
        # the fold interleaves the roots by `at`: the arming (last cairn line) is judged as
        # the last entry overall, and every prior triple carries its count
        t = json.loads(a)
        assert t["armed"] and t["armed"]["root"] == "cairn", t["armed"]
        assert t["post_appends"] == 0 and t["raises"] == [], "nothing after arming was judged"
        assert t["rows"][_key(*PRIOR[0])] == 1
        assert t["rows"][_key("CairnCommons", "tickets/a.json", "cast", "cc")] == 2
        assert t["unclassed"] == [], t["unclassed"]
        # the roots are read in either order and the bytes do not move
        rev = {k: j[k] for k in reversed(list(j))}
        assert block.render(block.compile(rev)) == a, "root read order changed the bytes"
        # the beat writes it; delete it; the next beat writes the same bytes
        w.pulse()
        on_disk = (w.table / block.TABLE_FILE).read_bytes()
        assert on_disk == a.encode("utf-8")
        (w.table / block.TABLE_FILE).unlink()
        w.pulse()
        assert (w.table / block.TABLE_FILE).read_bytes() == on_disk, "recompile after delete differs"
        # unarmed: the whole corpus is prior and nothing is ever judged
        w2 = World()
        try:
            _seed(w2, arm=False)
            w2.append(*UNSEEN_1)
            t2 = block.compile(block.read_journals(w2.roots))
            assert t2["armed"] is None and t2["raises"] == [] and t2["rows"][_key(*UNSEEN_1)] == 1
        finally:
            w2.close()
    finally:
        w.close()


def an_unseen_triple_raises_exactly_one_trouble_and_a_seen_one_raises_nothing():
    w = World()
    try:
        _seed(w)
        first = w.pulse()
        assert first["raised"] == [] and first["post_appends"] == 0, first
        # a seen triple: counted, silent
        w.append(*SEEN)
        out = w.pulse()
        assert out["raised"] == [], out
        assert w.table_doc()["rows"][_key(*SEEN)] == 3, "the seen row did not count the append"
        # an unseen triple: exactly one raise naming the triple and the row
        w.append(*UNSEEN_1)
        out = w.pulse()
        key = _key(*UNSEEN_1)
        assert len(out["raised"]) == 1, out
        r = out["raised"][0]
        assert r["identity"] == block.identity(block.path_class(UNSEEN_1[0], UNSEEN_1[1]), "hand-edit", "gate")
        assert r["poke"] is not None, "the emission carries how the lane was reached"
        doc = w.table_doc()
        assert doc["rows"][key] == 0, "the raised row must stay at zero"
        assert doc["raises"][0]["triple"] == key and doc["raises"][0]["row"] == 0
        assert doc["raises"][0]["disposition"] == "raised"
        # the same beat again reports nothing new
        assert w.pulse()["raised"] == [], "a raise was reported twice"
        # the emission is on disk in the block's own log home, and the drain folds it to
        # ONE ticket whose id is the slug of the identity, whose tail names triple and row
        logs = list((w.instance / "logs" / block.COMPONENT / "0").glob("*.raise_trouble.json"))
        assert len(logs) == 1, logs
        rec = json.loads(logs[0].read_text())
        assert rec["pointer"] == r["identity"] and rec["values"]["detail"]["row"]["triple"] == key
        w.drain()
        live = w.live_troubles()
        assert list(live) == [block.slug(r["identity"])], live
        ticket = live[block.slug(r["identity"])]
        assert ticket["count"] == 1, ticket
        # the store's own write rode the door into the scratch journal as a seen triple, so
        # the next beat raises nothing for it
        assert w.pulse()["raised"] == []
    finally:
        w.close()


def an_akien_clearance_teaches_the_row_and_a_cc_clearance_does_not():
    w = World()
    try:
        _seed(w)
        w.pulse()
        # the block's slug is the store's addressing rule — pinned, so a clear on disk
        # always finds the row it names
        from cairn.devices.trouble.trouble import TroubleDevice
        ident = block.identity(block.path_class(*UNSEEN_1[:2]), UNSEEN_1[2], UNSEEN_1[3])
        assert block.slug(ident) == TroubleDevice(root=w.store).identity_of(ident)
        # akien clears: the row becomes 1 and the same triple is silent from then on
        w.append(*UNSEEN_1)
        assert len(w.pulse()["raised"]) == 1
        k1 = _key(*UNSEEN_1)
        w.append("CairnCommons", f"troubles/{block.slug(ident)}.json", "clear", "akien",
                 "Akien cleared it: a gate hand-editing state is how the reseal ladder lands")
        out = w.pulse()
        assert out["raised"] == [], out
        doc = w.table_doc()
        assert doc["rows"][k1] == 1, doc["rows"]
        assert len(doc["increments"]) == 1 and doc["increments"][0]["triple"] == k1
        assert doc["raises"][0]["disposition"] == "cleared:akien"
        w.append(*UNSEEN_1)
        out = w.pulse()
        assert out["raised"] == [], "the triple raised again after an akien clearance"
        assert w.table_doc()["rows"][k1] == 2
        # cc clears: the row stays at zero, the trouble reads cleared:cc, and the same
        # triple raises AGAIN as a recurrence
        w.append(*UNSEEN_2)
        out = w.pulse()
        assert len(out["raised"]) == 1
        ident2 = out["raised"][0]["identity"]
        k2 = _key(*UNSEEN_2)
        w.append("CairnCommons", f"troubles/{block.slug(ident2)}.json", "clear", "cc",
                 "cc cleared its own novelty")
        out = w.pulse()
        assert out["raised"] == [], out
        doc = w.table_doc()
        assert doc["rows"][k2] == 0, "a cc clearance taught the table"
        assert len(doc["increments"]) == 1, "a cc clearance was counted as an increment"
        assert [r["disposition"] for r in doc["raises"]] == ["cleared:akien", "cleared:cc"]
        w.append(*UNSEEN_2)
        out = w.pulse()
        assert len(out["raised"]) == 1 and out["raised"][0]["identity"] == ident2, out
        assert w.table_doc()["rows"][k2] == 0
        # and the drain folds the recurrence onto the one identity: two tickets in the
        # store, the cc-cleared one counted twice
        w.drain()
        live = w.live_troubles()
        assert set(live) == {block.slug(ident), block.slug(ident2)}, live
        assert live[block.slug(ident2)]["count"] == 2 and live[block.slug(ident)]["count"] == 1
    finally:
        w.close()


def the_block_runs_on_the_beat_with_no_process_of_its_own_and_the_probe_fires_once_per_raise():
    # the beat's hook is discovered by the ground loop under the block's own folder …
    from cairn.devices.cairn.machines.ground_loop.discovery import pulse_sites
    sites = [s for s in pulse_sites() if s["device_id"] == block.COMPONENT]
    assert len(sites) == 1 and sites[0]["path"].name == "pulse.py", sites
    # … and nothing else runs it: no process of the block's own between beats
    ps = subprocess.run(["ps", "-eo", "args"], capture_output=True, text=True, check=True).stdout
    mine = [l for l in ps.splitlines() if "counting_block" in l and "proofs/test_counting_block" not in l]
    assert mine == [], f"a counting_block process is running: {mine}"
    # the hook is the whole entry point: calling it IS a beat, over the scratch world
    w = World()
    try:
        _seed(w)
        real_dir, real_roots = block.table_dir, door.roots
        # the hook and the probe read the block's live addresses; point both at the scratch
        # world for this tooth by the same seams the block itself uses
        import cairn.machines.counting_block.block as blk
        blk.table_dir = lambda: w.table
        blk.ModuleRaiser = lambda component: w.raiser()
        try:
            out = pulse_mod.on_pulse(w.t, {})
            assert out["block"] == block.COMPONENT and out["raised"] == 0, out
            # the probe: declared, armed with carry and enough, and silent on the seed
            P = probe_mod.PROBE
            assert P.carry is not None and P.enough is not None and P.horizon
            assert P.trigger(w.t, {}) is False, "the probe fired on the seed"
            # one raise → the probe fires on the NEXT beat, exactly once, carrying the triple
            w.append(*UNSEEN_1)
            pulse_mod.on_pulse(w.t, {})
            assert P.trigger(w.t, {}) is True, "a raise did not fire the probe"
            ctx = {}
            P.trigger(w.t, ctx)
            carried = P.carry(ctx)
            assert carried["raised"][0]["triple"] == _key(*UNSEEN_1), carried
            assert carried["rows"] >= 1 and "finding" in carried
            pulse_mod.on_pulse(w.t, {})  # the ack catches up
            assert P.trigger(w.t, {}) is False, "the probe fired twice for one raise"
            assert P.enough({}) is False
        finally:
            blk.table_dir = real_dir
            blk.ModuleRaiser = importlib.import_module("cairn.tools.base.diagnostic").ModuleRaiser
    finally:
        w.close()


def over_the_live_corpus_rows_are_well_under_entries():
    """Clause 5, and the ticket's HORIZON: compression exists. Read by address on this box so
    a hollow worktree with no commons beside it still measures the corpus that is here."""
    home = Path.home() / "dev" / "src"
    roots = {n: home / n for n in ("cairn", "CairnCommons") if (home / n / ".artifact-journal.jsonl").exists()}
    assert roots, "no live journal found under ~/dev/src"
    t = block.compile(block.read_journals(roots))
    c = block.compression(t)
    assert c["entries"] >= 500, c
    assert c["rows"] * 10 <= c["entries"], f"no compression: {c}"
    assert t["unclassed"] == [], f"the door journaled paths its jurisdiction does not name: {t['unclassed'][:3]}"
    print(f"        live corpus: {c['rows']} rows over {c['entries']} entries ({c['ratio']:.1f}:1)")


TEETH = [
    the_table_compiles_from_both_journals_and_is_byte_identical_when_recompiled,
    an_unseen_triple_raises_exactly_one_trouble_and_a_seen_one_raises_nothing,
    an_akien_clearance_teaches_the_row_and_a_cc_clearance_does_not,
    the_block_runs_on_the_beat_with_no_process_of_its_own_and_the_probe_fires_once_per_raise,
    over_the_live_corpus_rows_are_well_under_entries,
]

if __name__ == "__main__":
    try:
        for fn in TEETH:
            _tooth(fn.__name__, fn)
    finally:
        door.set_diagnostic_roots(None)
        for d in _TMP:
            shutil.rmtree(d, ignore_errors=True)
    print(f"{PASS} passed, {FAIL} failed out of {PASS + FAIL}")
    sys.exit(1 if FAIL else 0)
