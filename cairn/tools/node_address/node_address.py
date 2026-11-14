"""The librarian's address: one 64-bit integer, a 16-bit table tag over a 48-bit row (ticket a90747de35d2).

Akien, Q#108 answer, 2026-11-14 (outline 4.3.1.5.1): every reference is one 64-bit integer, top 16
bits the table tag and low 48 the row, so every pointer is a direct row fetch and a new kind of
thing is a new tag. A reference carries (address, gen); a gen that no longer matches the row is a
reused row, read as gone, never as the new tenant's data.

POSTGRES BIGINT IS SIGNED. A tag at or past 0x8000 sets the int64 sign bit, so ``pack`` returns the
two's-complement int64 (negative for those tags) and ``unpack`` reads either form back. All 16 tag
bits stay usable, and the value always fits a bigint column (tooth 3 measures it).

Pure: no state, no I/O except reading ``tags.json`` beside this file.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

TAG_BITS = 16
ROW_BITS = 48
MAX_TAG = (1 << TAG_BITS) - 1
MAX_ROW = (1 << ROW_BITS) - 1
_ROW_MASK = MAX_ROW
_U64 = 1 << 64
_I64_MIN, _I64_MAX = -(1 << 63), (1 << 63) - 1

_TAGS_FILE = Path(__file__).with_name("tags.json")


class AddressRefused(ValueError):
    """An address, tag, row or gen off its bits: refused loudly, never wrapped (Law 7)."""


def _int(value, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise AddressRefused(f"{field} {value!r} is not an int")
    return value


def pack(tag: int, row: int) -> int:
    """The address of ``row`` in the table ``tag``, as a signed int64 (bigint-ready)."""
    tag, row = _int(tag, "tag"), _int(row, "row")
    if not 1 <= tag <= MAX_TAG:
        raise AddressRefused(f"tag {tag} is outside 1..{MAX_TAG} (16 bits; tag 0 is no table)")
    if not 1 <= row <= MAX_ROW:
        raise AddressRefused(f"row {row} is outside 1..{MAX_ROW} (48 bits; rows count from 1)")
    u = (tag << ROW_BITS) | row
    return u - _U64 if u > _I64_MAX else u


def unpack(address: int) -> tuple[int, int]:
    """(tag, row) of an address, from its signed int64 form."""
    a = _int(address, "address")
    if not _I64_MIN <= a <= _I64_MAX:
        raise AddressRefused(f"address {a} is not an int64")
    u = a % _U64
    tag, row = u >> ROW_BITS, u & _ROW_MASK
    if tag == 0 or row == 0:
        raise AddressRefused(f"address {a} names tag {tag} row {row}; neither may be 0")
    return tag, row


def tag_of(address: int) -> int:
    return unpack(address)[0]


def row_of(address: int) -> int:
    return unpack(address)[1]


@lru_cache(maxsize=1)
def registry() -> dict[str, int]:
    """Table name -> tag, as tags.json declares it. Refuses a file that reuses a tag."""
    tags = json.loads(_TAGS_FILE.read_text(encoding="utf-8"))["tags"]
    for name, tag in tags.items():
        if isinstance(tag, bool) or not isinstance(tag, int) or not 1 <= tag <= MAX_TAG:
            raise AddressRefused(f"tags.json: tag {tag!r} for {name!r} is outside 1..{MAX_TAG}")
    if len(set(tags.values())) != len(tags):
        raise AddressRefused(f"tags.json: two names share a tag: {tags}")
    return dict(tags)


def tag_for(name: str) -> int:
    try:
        return registry()[name]
    except KeyError:
        raise AddressRefused(f"no tag is registered for {name!r} (tags.json)") from None


def name_for(tag: int) -> str:
    for name, t in registry().items():
        if t == tag:
            return name
    raise AddressRefused(f"tag {tag} names no table (tags.json)")


class Ref:
    """A reference: an address and the gen of the row it was taken at. A reused row has a new
    gen, so a Ref held from before the reuse no longer equals the row's current Ref."""

    __slots__ = ("address", "gen")

    def __init__(self, address: int, gen: int):
        unpack(address)
        gen = _int(gen, "gen")
        if gen < 0:
            raise AddressRefused(f"gen {gen} is negative")
        object.__setattr__(self, "address", address)
        object.__setattr__(self, "gen", gen)

    def __setattr__(self, *_):
        raise AttributeError("a Ref is immutable")

    def __eq__(self, other):
        return isinstance(other, Ref) and (self.address, self.gen) == (other.address, other.gen)

    def __hash__(self):
        return hash((self.address, self.gen))

    def __repr__(self):
        tag, row = unpack(self.address)
        return f"Ref(tag={tag}, row={row}, gen={self.gen})"
