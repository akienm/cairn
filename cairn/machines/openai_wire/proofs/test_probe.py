"""Proofs for the WATCHME probe openai_wire_is_included_by_a_second_holder: the count of
DISTINCT holders read off a fixture import graph. A hollow probe that counted files, or
counted the machine's own tree, or counted instruments, fails here.

Provenance: ticket 76639374d9f9.
"""
import sys

from cairn.machines.openai_wire.probes import openai_wire_is_included_by_a_second_holder as probe
from cairn.tools.base.probe import Probe

PASS = 0
FAIL = 0


def _tooth(name, fn):
    global PASS, FAIL
    try:
        fn()
    except Exception as exc:
        FAIL += 1
        print(f"  RED   {name}: {type(exc).__name__}: {exc}")
        return
    PASS += 1
    print(f"  green {name}")


M = {"cairn.machines.openai_wire.serve.make_handler"}
M2 = {"cairn.machines.openai_wire"}


def two_files_in_one_device_are_one_holder():
    graph = {"devices/hermes_shim/shim.py": M, "devices/hermes_shim/machines/door/door.py": M2,
             "devices/other/x.py": {"json"}}
    s = probe.judge_graph(graph)
    assert s["distinct"] == 1 and list(s["holders"]) == ["devices/hermes_shim"], s
    assert len(s["holders"]["devices/hermes_shim"]) == 2, s


def the_machines_own_tree_and_its_instruments_do_not_count():
    graph = {"machines/openai_wire/__init__.py": M, "machines/openai_wire/serve.py": M2,
             "machines/openai_wire/proofs/test_serve.py": M,
             "devices/x/proofs/test_x.py": M, "devices/x/probes/p.py": M2,
             "top.py": M}
    s = probe.judge_graph(graph)
    assert s["distinct"] == 0, s


def two_distinct_holders_is_enough_and_one_is_not():
    one = {"corpus": probe.judge_graph({"devices/a/x.py": M})}
    two = {"corpus": probe.judge_graph({"devices/a/x.py": M, "machines/b/y.py": M2})}
    assert probe.PROBE.fires(None, one) and not probe.PROBE.gathered_enough(one), one
    assert probe.PROBE.fires(None, two) and probe.PROBE.gathered_enough(two), two
    none = {"corpus": probe.judge_graph({"devices/a/x.py": {"json"}})}
    assert not probe.PROBE.fires(None, none), none


def a_look_alike_module_does_not_count():
    s = probe.judge_graph({"devices/a/x.py": {"cairn.machines.openai_wire_v2.serve"}})
    assert s["distinct"] == 0, s


def the_carry_names_the_holders_and_the_bar():
    ctx = {"corpus": probe.judge_graph({"devices/a/x.py": M})}
    c = probe.PROBE.payload(ctx)
    assert c["distinct"] == 1 and c["enough_at"] == 2 and c["holders"] == {"devices/a": ["devices/a/x.py"]}, c
    assert "ticket" in c and "against_falsifier" in c, c


def the_probe_is_frozen_and_declared():
    assert isinstance(probe.PROBE, Probe)
    assert probe.PROBE.to == "harbor_master" and probe.PROBE.horizon == 1000


def the_live_walk_reads_the_tree():
    s = probe.survey_the_corpus()
    assert isinstance(s["distinct"], int) and "machines/openai_wire" not in s["holders"], s


TEETH = [
    two_files_in_one_device_are_one_holder,
    the_machines_own_tree_and_its_instruments_do_not_count,
    two_distinct_holders_is_enough_and_one_is_not,
    a_look_alike_module_does_not_count,
    the_carry_names_the_holders_and_the_bar,
    the_probe_is_frozen_and_declared,
    the_live_walk_reads_the_tree,
]

if __name__ == "__main__":
    for tooth in TEETH:
        _tooth(tooth.__name__, tooth)
    print(f"\n{PASS} passed, {FAIL} failed out of {PASS + FAIL}")
    sys.exit(1 if FAIL else 0)
