"""chart/dial.py — THE DIAL: the compilation claim, read off the berthed packets.

The nexi-everywhere ruling (held-nexi-everywhere, 2026-07-28) traded the ban-by-prose on
inference for detection-by-instrument: a nexus whose floor+tree fraction is not growing
is not compiling — the ceiling is doing the floor's job forever, which is the puppet.
That claim can only red a nexus if someone can READ the fraction. This module is the
reader (Law 3: until it existed, the ruling's anti-puppet claim was a hypothesis).

A read-only compile over the packet berth (instance-space, ``~/.cairn/devices/chart/``):
per nexus, in time order (the timestamp rides the filename), the fraction of authored
fields filled by floor vs tree vs claude. It REPORTS; the judgment stays with its
readers — the dial is never fed back to a nexus as its own score (the home-field fence,
charter falsifier 6), and "not growing over N crossings" becomes a checkable gate shape
only through the inspector's own admission door (chart-tree filed edge (c)).

Honesty at the edges: an empty or absent berth is a nameable state (no /chart has ever
berthed here), not an error. A packet-shaped file the dial cannot read — or one whose
provenance fails the shape a berthed packet must have — is reported by name in
``unreadable``, never silently skipped (Law 7: a berthed packet that fails its own gate
is a finding, not noise).

    python3 -m cairn.chart.dial            # the live berth
    python3 -m cairn.chart.dial <dir>      # any berth
"""
from __future__ import annotations

import json
import os
import re

import cairn.chart.constrain as _constrain
import cairn.chart.survey as _survey
from cairn.chart.orient import AUTHORED_FIELDS, INSTANCE_DIR, STRATA

# orient-20260728T110828-63dcfc770585.json → (nexus, stamp)
_PACKET_RE = re.compile(r"^([a-z][a-z0-9_]*)-(\d{8}T\d{6})-([0-9a-f]+)\.json$")

# Each stage authors its own fields; the dial reads a packet against ITS stage's
# shape (a constrain packet judged by orient's fields would be a false finding).
# A berthed stage with no registered shape is reported loudly — stage 3 registers
# here when it lands, and silence would hide a whole nexus from the reading.
STAGE_FIELDS = {
    "orient": AUTHORED_FIELDS,
    "constrain": _constrain.AUTHORED_FIELDS,
    "survey": _survey.AUTHORED_FIELDS,
}


def _fractions(provenance: dict, fields) -> dict:
    counts = {s: 0 for s in STRATA}
    for field in fields:
        counts[provenance[field]] += 1
    return {s: round(counts[s] / len(fields), 4) for s in STRATA}


def dial(instance_dir: str = INSTANCE_DIR) -> dict:
    """The reading: ``{"berth", "packets", "nexi": {nexus: {"packets", "series",
    "aggregate"}}, "unreadable"}`` — series in time order, fractions per packet, the
    aggregate a plain mean. Everything a reader needs to see whether the boundary is
    moving down; no verdict is minted here."""
    berth = os.path.expanduser(instance_dir)
    out = {"berth": berth, "packets": 0, "nexi": {}, "unreadable": []}
    if not os.path.isdir(berth):
        return out  # no berth yet: /chart has never landed a packet here — a nameable state

    for name in sorted(os.listdir(berth)):  # the stamp rides the name, so sorted IS time order
        m = _PACKET_RE.match(name)
        if not m:
            continue  # not packet-shaped: not this instrument's jurisdiction
        nexus, stamp = m.group(1), m.group(2)
        try:
            fields = STAGE_FIELDS.get(nexus)
            if fields is None:
                raise ValueError(
                    f"no registered field-shape for stage {nexus!r} — the stage "
                    "registers in STAGE_FIELDS when it lands")
            with open(os.path.join(berth, name), encoding="utf-8") as fh:
                packet = json.load(fh)
            provenance = packet["provenance"]
            bad = [f for f in fields
                   if provenance.get(f) not in STRATA]
            if bad:
                raise ValueError(
                    f"provenance fails the berthed shape on: {', '.join(bad)}")
        except Exception as e:  # a berthed packet that fails its own gate is a finding
            out["unreadable"].append({"packet": name, "why": str(e)})
            continue
        entry = {"packet": name, "at": stamp, **_fractions(provenance, fields)}
        out["nexi"].setdefault(nexus, []).append(entry)
        out["packets"] += 1

    for nexus, series in out["nexi"].items():
        # Full precision on purpose: rounding a mean of exact fifths breaks the
        # sum-to-1 invariant the whole reading is trusted by.
        aggregate = {s: sum(e[s] for e in series) / len(series) for s in STRATA}
        out["nexi"][nexus] = {"packets": len(series), "series": series,
                              "aggregate": aggregate}
    return out


if __name__ == "__main__":
    import sys
    print(json.dumps(dial(sys.argv[1]) if len(sys.argv) > 1 else dial(), indent=2))
