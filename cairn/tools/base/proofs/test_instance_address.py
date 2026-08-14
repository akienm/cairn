"""Proof for the instance-space address — one owner for where a thing lives.

Teeth a hollow build could not pass:
  - THE REAL HOME DIRECTORY IS NOT READ AT ALL. Every assertion below runs under a roots
    table pointed at an EMPTY temp directory, and the resolved paths are asserted not to
    contain the real home. This is the tooth that makes the rest non-hollow: a resolver
    that ignored its roots argument entirely and read the module-level table would pass
    every shape assertion on this developer's box, because ~/.cairn happens to exist here.
    On a box where it does not — a packaged app, another user, CI — it would resolve
    nowhere. The proof must be able to tell those two apart, so it runs as if it were on
    that other box.
  - RESOLVING NEVER TOUCHES DISK. The temp tree is empty before and empty after all three
    rungs are called. base knows every device's address; if it also CREATED, one module
    would be reaching into every owner's space (Law 6), and that failure would be written
    once and called convenient. The bound is checked, not promised.
  - THE INSTANCE SEGMENT IS PRESENT EVEN AT 0. Akien's ruling of 2026-08-12: a singleton is
    instance 0, not an exemption — "(A) same rules for everything, no special cases, and
    (II) it leaves open the possibility to expand in the future without rearchitecting that
    part." The falsifier is a resolved path that omits the segment when instance is 0.
  - THE HELD PART IS ADDRESSED BY NAME, NEVER BY NUMBER. tools/<name>/ and machines/<name>/,
    with no ordinal parameter in the signature to encode the killed shape back in.
  - THE TWO FACES OF THE TABLE AGREE. A charter author writes a rooted token
    ("instance/devices/chart/0/packets" — two of the five address values authored across the
    whole charter corpus are exactly this shape); code passes device and instance as
    arguments. They are one table, and they are pinned to each other here by Path equality
    under the same injected roots — including for a device that does not exist, because the
    agreement is about the ADDRESS and not about what happens to be on disk.
  - THE CLASS-SPACE WALK DESCENDS A HOLDER'S OWN RUNGS. A device's held tools and machines
    nest under it at the same shape (CLAUDE.md), so the census that finds components has to
    go down with them — and it must not read a component's proofs/, probes/ or validations/
    as smaller components. The falsifier is a held machine that is simply ABSENT from the
    roster: not an error, just gone, which is how a gate stops covering something without
    ever saying so. Born the day the builder device took the seven pre-build stages in.
  - A HAND-SPELLED ABSOLUTE PATH IS STILL REFUSED as an address. The behaviour was born in
    cairn/machines/skill_block/counters.py and moved down here on 2026-08-12; the tooth moved with
    it, and skill_block's own proof still holds its copy — the relocation is checked from
    both ends.

Runnable bare (no DB, no framework):
    python3 cairn/tools/base/proofs/test_instance_address.py     # exit 0 = green
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.base import address as A


def _elsewhere(tmp: Path) -> dict[str, Path]:
    """A roots table for a box that is NOT this one. Only 'instance' is exercised below;
    the other two ride along so the table has the same shape the real one does."""
    return {"repo": tmp / "code", "commons": tmp / "knowledge", "instance": tmp / "state"}


def test_the_three_rungs_resolve_off_this_box():
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        roots = _elsewhere(tmp)
        home = str(Path.home())

        got = {
            "instance": A.instance_path("chart", 0, roots),
            "instance_1": A.instance_path("chart", 1, roots),
            "tool": A.tool_path("gate", 0, "buildme_entry", roots),
            "machine": A.machine_path("librarian", 2, "shelver", roots),
        }

        # THE NON-HOLLOW TOOTH, AND IT RUNS FIRST ON PURPOSE. Not one resolved path may
        # mention the real home directory. It is checked ahead of the shapes because it is
        # the assertion that NAMES the failure: a rung that ignores its roots fails the
        # shapes too, but "AssertionError" on a path equality tells a reader the answer was
        # wrong, while this tells them WHY it was wrong and on which box it would have gone
        # green. It is also the backstop for a shape assertion written loosely — one
        # comparing against the module's own table instead of the temp root would pass a
        # roots-ignoring resolver, and only this tooth would still bite.
        for name, path in got.items():
            assert home not in str(path), \
                (f"{name} resolved to {path}, which contains the real home directory — the "
                 "roots argument was ignored, so this proof would go green on a box where "
                 "~/.cairn exists and red nowhere else")

        assert got["instance"] == tmp / "state" / "devices" / "chart" / "0", got["instance"]
        assert got["instance_1"] == tmp / "state" / "devices" / "chart" / "1", got["instance_1"]
        assert got["tool"] == (tmp / "state" / "devices" / "gate" / "0"
                               / "tools" / "buildme_entry"), got["tool"]
        assert got["machine"] == (tmp / "state" / "devices" / "librarian" / "2"
                                  / "machines" / "shelver"), got["machine"]


def test_the_instance_segment_is_present_even_at_zero():
    with tempfile.TemporaryDirectory() as td:
        roots = _elsewhere(Path(td))
        # A singleton is instance 0, not an exemption. The DEFAULT is an argument default;
        # the SEGMENT is never optional, and that is what is asserted.
        defaulted = A.instance_path("sudo_relay", roots=roots)
        explicit = A.instance_path("sudo_relay", 0, roots)
        assert defaulted == explicit, "omitting the argument must not omit the segment"
        assert defaulted.name == "0", f"the instance segment vanished at 0: {defaulted}"
        assert defaulted.parent.name == "sudo_relay"
        assert defaulted.parent.parent.name == "devices"


def test_the_held_part_is_named_never_numbered():
    with tempfile.TemporaryDirectory() as td:
        roots = _elsewhere(Path(td))
        named = A.tool_path("gate", 0, "buildme_entry", roots)
        assert named.name == "buildme_entry", \
            "the tool segment must be the NAME — 'tools/gate/2/probes' is the shape the " \
            "2026-08-12 ruling killed, because a number makes a reader memorise a mapping"
        # And the signature offers no ordinal to put it back with: the only positional
        # parameters are device, instance, tool.
        import inspect
        params = list(inspect.signature(A.tool_path).parameters)
        assert params == ["device", "instance", "tool", "roots"], params
        assert list(inspect.signature(A.machine_path).parameters) == \
            ["device", "instance", "machine", "roots"]


def test_resolving_creates_nothing():
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        roots = _elsewhere(tmp)
        assert list(tmp.rglob("*")) == [], "the temp tree did not start empty"

        A.instance_path("chart", 0, roots)
        A.instance_path("a_device_that_does_not_exist", 7, roots)
        A.tool_path("gate", 0, "buildme_entry", roots)
        A.machine_path("librarian", 2, "shelver", roots)
        A.resolve("instance/devices/chart/0/packets", roots)

        left = list(tmp.rglob("*"))
        assert left == [], \
            (f"resolving created {[str(p) for p in left]} — base computes addresses and does "
             "not provision. A shared helper that reached into every device's space to CREATE "
             "would be a Law 6 crossing written once and called convenient.")


def test_the_two_faces_are_one_table():
    with tempfile.TemporaryDirectory() as td:
        roots = _elsewhere(Path(td))
        from cairn.machines.skill_block import counters

        # The charter-author face and the code face, for a device that exists...
        assert counters.resolve("instance/devices/chart/0", roots) == \
            A.instance_path("chart", 0, roots)
        # ...for the deeper address a charter actually carries...
        assert counters.resolve("instance/devices/skill_block/0/berths/intent", roots) == \
            A.instance_path("skill_block", 0, roots) / "berths" / "intent"
        # ...and for one that does not exist anywhere, because the agreement is about the
        # ADDRESS, not about what is on disk.
        assert counters.resolve("instance/devices/no_such_device/3", roots) == \
            A.instance_path("no_such_device", 3, roots)

        # ONE table, not two that agree: counters reads base's, and the exception it raises
        # IS base's class, so `except counters.Unreadable` catches what base throws.
        assert counters._ROOTS is A.ROOTS
        assert counters.Unreadable is A.Unreadable
        assert counters.resolve is A.resolve


def test_a_bare_absolute_path_is_refused_as_an_address():
    with tempfile.TemporaryDirectory() as td:
        roots = _elsewhere(Path(td))
        try:
            A.resolve("/home/somebody/.cairn/devices/x", roots)
            raise AssertionError("a bare absolute path was accepted as an address")
        except A.Unreadable as exc:
            assert "not one of" in str(exc), str(exc)
            # The message carries the WHY, which is the whole reason the token form exists.
            assert "another box" in str(exc), str(exc)


def test_the_class_space_walk_descends_a_holders_own_rungs():
    """CLAUDE.md grants a device the same shape one level down — "a device's held tools and
    machines nest under it at the same shape" — and until 2026-08-13 nothing on disk had
    used the grant, so the walk stopped one level in. The failure mode is not a crash: a
    held component simply would not EXIST as far as the roster, the derivation gate or any
    judge is concerned. Green by absence is the worst colour a census can be, so the
    descent is pinned here rather than remembered.

    Fabricated tree, no live snapshot values. Shape:

        cairn/devices/holder/{__init__.py, machines/held/held.py, tools/gadget/gadget.py}
        cairn/devices/quiet/machines/hidden/hidden.py     <- holder has no code of its own
        cairn/tools/plain/plain.py
        cairn/devices/holder/machines/held/proofs/test_x.py   <- a RECORD, not a component
    """
    with tempfile.TemporaryDirectory() as td:
        pkg = Path(td) / "cairn"

        def mk(rel: str, code: bool = True) -> Path:
            d = pkg / rel
            d.mkdir(parents=True, exist_ok=True)
            if code:
                (d / (d.name + ".py")).write_text("x = 1\n")
            return d

        mk("tools/plain")
        holder = mk("devices/holder", code=False)
        (holder / "__init__.py").write_text("")
        mk("devices/holder/machines/held")
        mk("devices/holder/tools/gadget")
        # A holder with NO code and NO charter of its own still holds what it holds.
        mk("devices/quiet", code=False)
        mk("devices/quiet/machines/hidden")
        # A component's own record dirs are not smaller components inside it.
        for record in ("proofs", "probes", "validations"):
            r = pkg / "devices/holder/machines/held" / record
            r.mkdir()
            (r / "test_x.py").write_text("x = 1\n")

        found, unreadable = A.component_dirs(pkg)
        rel = sorted(str(p.relative_to(pkg)) for p in found)
        assert unreadable == [], unreadable
        assert rel == ["devices/holder",
                       "devices/holder/machines/held",
                       "devices/holder/tools/gadget",
                       "devices/quiet/machines/hidden",
                       "tools/plain"], rel

        # THE NAME IS NOT THE ADDRESS, and the walk is what makes that true rather than a
        # slogan: the same name at two rungs comes back as TWO dirs, and the bare-name
        # lookup refuses to pick one.
        mk("tools/held")
        homes = sorted(str(p.relative_to(pkg)) for p in A.component_dirs(pkg)[0]
                       if p.name == "held")
        assert homes == ["devices/holder/machines/held", "tools/held"], homes
        try:
            A.component_dir("held", pkg)
            raise AssertionError("a name two rungs answer to resolved to one home")
        except A.AmbiguousComponent as exc:
            assert exc.name == "held" and len(exc.homes) == 2, exc.homes


def test_a_path_resolves_to_its_deepest_component_never_its_holder():
    """``component_of`` — the other half of ``component_dir``, asking the same question
    from the other end: given a PATH, which component owns it?

    THE DEEPEST ANCESTOR IS THE ANSWER, NOT A TIE-BREAK. Components nest, so a file inside
    ``devices/holder/machines/held/`` sits under two of them. Both are true statements
    about the file; only one is its address, and answering with the holder attributes a
    machine's code to the device that assembles it. A first-match or shallowest-match
    implementation passes every other tooth here and fails this one.

    IT RETURNS WHERE ``component_dir`` RAISES, and the asymmetry is the point:
    ``AmbiguousComponent`` tells its caller "a path resolves unambiguously", and this is
    the function that makes that sentence true instead of merely advisory.
    """
    with tempfile.TemporaryDirectory() as td:
        pkg = Path(td) / "cairn"

        def mk(rel: str) -> Path:
            d = pkg / rel
            d.mkdir(parents=True, exist_ok=True)
            (d / (d.name + ".py")).write_text("x = 1\n")
            return d

        mk("tools/plain")
        holder = mk("devices/holder")
        held = mk("devices/holder/machines/held")
        (held / "proofs").mkdir()
        (held / "proofs" / "test_x.py").write_text("x = 1\n")

        assert A.component_of(pkg / "tools/plain/plain.py", pkg) == (pkg / "tools/plain")
        assert A.component_of(pkg / "devices/holder/holder.py", pkg) == holder
        # THE TOOTH: two owners, and the deeper one wins.
        assert A.component_of(held / "held.py", pkg) == held, \
            "a machine's code belongs to the machine, not to the device holding it"
        # A component's own record dirs are its record, so a proof file still answers to
        # the component whose proof it is.
        assert A.component_of(held / "proofs" / "test_x.py", pkg) == held
        # The component directory itself is its own owner — ancestor-OR-SELF.
        assert A.component_of(held, pkg) == held

        assert A.component_of(pkg / "devices" / "nothing_here.py", pkg) is None, \
            "a path under no component answers None — a rung container is not a component"
        assert A.component_of(Path(td) / "outside.txt", pkg) is None


def _main() -> int:
    for check in (test_the_three_rungs_resolve_off_this_box,
                  test_the_class_space_walk_descends_a_holders_own_rungs,
                  test_a_path_resolves_to_its_deepest_component_never_its_holder,
                  test_the_instance_segment_is_present_even_at_zero,
                  test_the_held_part_is_named_never_numbered,
                  test_resolving_creates_nothing,
                  test_the_two_faces_are_one_table,
                  test_a_bare_absolute_path_is_refused_as_an_address):
        check()
        print(f"  PASS  {check.__name__}")
    print("green — the instance address has one owner: the three rungs resolve under an "
          "injected root with the real home never read, the instance segment survives at 0, "
          "the held part is named and cannot be numbered through the signature, resolving "
          "creates nothing on disk, and the charter-author token and the code arguments are "
          "two faces of ONE table")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
