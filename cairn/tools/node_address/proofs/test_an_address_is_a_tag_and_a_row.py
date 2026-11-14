"""Every librarian reference is one 64-bit address: a 16-bit table tag over a 48-bit row (ticket a90747de35d2).

Akien, Q#108 answer, 2026-11-14 (outline 4.3.1.5.1): "every reference is one 64-bit integer: top
16 bits = table tag, low 48 = row ... a new kind of thing is a new tag, not a schema change", and
"a reference carries (row, gen); a mismatch after a VOID row is reused reads loud 'gone'".

  1. pack and unpack round-trip at the edge tags (1, 0x7FFF, 0x8000, 0xFFFF) and edge rows
     (1, 2**48 - 1), and tag_of / row_of agree with unpack;
  2. tag 0, a tag past 16 bits, row 0, a row past 48 bits, and a non-int (bool, str, float) are
     refused with AddressRefused naming the field; unpack of 0 is refused;
  3. every address fits a postgres bigint: written to a scratch bigint column and read back, it
     unpacks to the same tag and row, the sign-bit tags (>= 0x8000) included;
  4. the tag registry names nodes 1, lists 2, links 3, blobs 4; its names and tags are unique;
     tag_for / name_for round-trip; an unknown name or tag is refused;
  5. a Ref carries (address, gen): gen is a non-negative int, and the same address under another
     gen is a different ref.

THE WORLD: tooth 3 writes one scratch table through store.scratch, dropped at exit. Nothing else
touches the database.

    bin/cairn test cairn/tools/node_address/proofs/test_an_address_is_a_tag_and_a_row.py
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"a90747de35d2": {
    "1": "test_an_address_round_trips_at_the_edges",
    "2": "test_an_address_off_its_bits_is_refused_naming_the_field",
    "3": "test_every_address_fits_a_postgres_bigint",
    "4": "test_the_registry_names_the_four_tables_once_each",
    "5": "test_a_ref_carries_its_gen",
}}

PROOF_TIMEOUT_S = 120

_TAGS = (1, 0x7FFF, 0x8000, 0xFFFF)
_ROWS = (1, 2, 2**47, 2**48 - 1)


def _refused(fn, *args, field: str) -> None:
    from cairn.tools.node_address import AddressRefused
    try:
        got = fn(*args)
    except AddressRefused as e:
        assert field in str(e), f"{fn.__name__}{args} refused without naming {field!r}: {e}"
    else:
        raise AssertionError(f"{fn.__name__}{args} was not refused: {got!r}")


def test_an_address_round_trips_at_the_edges():
    from cairn.tools.node_address import pack, unpack, tag_of, row_of
    seen = set()
    for tag in _TAGS:
        for row in _ROWS:
            a = pack(tag, row)
            assert isinstance(a, int) and not isinstance(a, bool), a
            assert -(2**63) <= a < 2**63, f"pack({tag}, {row}) = {a} is not an int64"
            assert unpack(a) == (tag, row), (tag, row, a, unpack(a))
            assert tag_of(a) == tag and row_of(a) == row, (tag, row, a)
            seen.add(a)
    assert len(seen) == len(_TAGS) * len(_ROWS), "two (tag, row) pairs packed to one address"


def test_an_address_off_its_bits_is_refused_naming_the_field():
    from cairn.tools.node_address import pack, unpack
    _refused(pack, 0, 1, field="tag")
    _refused(pack, 0x10000, 1, field="tag")
    _refused(pack, -1, 1, field="tag")
    _refused(pack, 1, 0, field="row")
    _refused(pack, 1, 2**48, field="row")
    _refused(pack, 1, -5, field="row")
    _refused(pack, True, 1, field="tag")
    _refused(pack, 1, "7", field="row")
    _refused(pack, 1, 7.0, field="row")
    _refused(unpack, 0, field="address")
    _refused(unpack, 2**63, field="address")
    _refused(unpack, "12", field="address")


def test_every_address_fits_a_postgres_bigint():
    from cairn.devices.db_domain.tools.client import store
    from cairn.tools.node_address import pack, unpack
    wanted = [(tag, row) for tag in _TAGS for row in _ROWS]
    with store.scratch("node_address", "node_address_bigint", {
            "n": "integer PRIMARY KEY", "address": "bigint NOT NULL"}) as table:
        for n, (tag, row) in enumerate(wanted):
            store.write(table, "node_address", {"n": n, "address": pack(tag, row)})
        back = {r["n"]: r["address"] for r in store.read(table)}
    got = [unpack(back[n]) for n in range(len(wanted))]
    assert got == wanted, [(w, g) for w, g in zip(wanted, got) if w != g]


def test_the_registry_names_the_four_tables_once_each():
    from cairn.tools.node_address import registry, tag_for, name_for, AddressRefused
    reg = registry()
    for name, tag in (("nodes", 1), ("lists", 2), ("links", 3), ("blobs", 4)):
        assert reg.get(name) == tag, f"{name} is not tag {tag}: {reg}"
        assert tag_for(name) == tag and name_for(tag) == name
    assert len(set(reg.values())) == len(reg), f"two names share a tag: {reg}"
    assert all(1 <= t <= 0xFFFF for t in reg.values()), reg
    for bad, fn in (("no_such_table", tag_for), (0xFFFE, name_for)):
        try:
            fn(bad)
        except AddressRefused as e:
            assert str(bad) in str(e), str(e)
        else:
            raise AssertionError(f"{fn.__name__}({bad!r}) was not refused")


def test_a_ref_carries_its_gen():
    from cairn.tools.node_address import Ref, pack, AddressRefused
    a = pack(1, 42)
    r0, r1 = Ref(a, 0), Ref(a, 1)
    assert r0.address == a and r0.gen == 0 and r1.gen == 1
    assert r0 != r1, "the same row under a new gen is the same ref"
    assert Ref(a, 3) == Ref(a, 3) and hash(Ref(a, 3)) == hash(Ref(a, 3))
    for bad in (-1, True, "1", 1.0):
        try:
            Ref(a, bad)
        except AddressRefused as e:
            assert "gen" in str(e), str(e)
        else:
            raise AssertionError(f"Ref took gen {bad!r}")
    try:
        Ref(0, 0)
    except AddressRefused as e:
        assert "address" in str(e), str(e)
    else:
        raise AssertionError("Ref took address 0")


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
