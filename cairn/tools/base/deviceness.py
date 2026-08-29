"""DEVICENESS — the one callable answer to "is X a device?", and the divergence it exposes.

RULED BY AKIEN 2026-08-11, twice in one day, and the two rulings are the same ruling seen
from two ends:

  "a shim fits TO the device; you + your shim = your device."
  "THE UNIT IS THE FOLDER, NOT THE REGISTRATION. A device is a directory with a ``probes/``
   subdirectory in it; its id is the directory's own name."

WHY THIS FILE EXISTS AT ALL. Device-ness was decided by INHERITANCE — a thing was a device
if it subclassed ``BaseDevice`` — and that axis cannot see an external device. Calibre was a
UU device with no device code at all, just its shim, because Calibre itself managed the
books. A class read can never admit that member, so the rule was restated in prose. It did
not hold: with the rule stated plainly in conversation, the same session measured
device-ness by reading ``BaseDevice`` inheritance TWICE. A rule that loses to a habit inside
one session is not a rule yet (Law 4) — so it is a function now, and the function is the
rule.

THIS COMPOSES, IT DOES NOT RE-DERIVE. Membership is ``cairn.devices.cairn.machines.ground_loop.discovery``'s to
know: it is the mechanism Akien ruled, it shipped, and it is what the running loop actually
fits shims to (``loop.py::_reconcile``). Asking it here is Law 1 — the answered question
became structure, and a second parallel roster would be exactly the failure the folder rule
was ruled to end. The import is DEFERRED into the call rather than taken at module level
because ``ground_loop`` imports ``base``: the dependency genuinely points that way, and the
lazy import is the honest way to say "base asks ground_loop" without inverting a layering
that three live charters are red on.

CLAUSE 1 ONLY, AND THE OTHER CLAUSE IS DECLARED, NOT OMITTED. The ticket's falsifier names
TWO clauses: a shim is fitted (this), AND the thing answers a health query over the bus.
The second names something that does not exist — MEASURED at the build, ``grep -rni health``
over ``cairn/`` outside proofs returns 21 hits and every one is the English word in prose or
one line of UU ancestry in ``device.py``. There is no health protocol, no health method, no
health message on the bus. Building one inside this ticket was ruled OUT of the chart's
bounds ("Building a health-query protocol from scratch if none exists"). So the clause is
carried as ``HEALTH_QUERY_CLAUSE`` below, unbuilt and saying so, because a predicate that
silently implements half of its own definition is the shape a reader mistakes for whole.

WHAT THIS FILE IS NOT. It is not an authority and it grants nothing. Discovery decides
membership; this reads it and puts the two axes side by side so their disagreement can be
seen. Acting on that disagreement is each component's owner's act (Law 6).
"""

from __future__ import annotations

import ast
from pathlib import Path

# THE UNBUILT HALF OF THE PREDICATE, NAMED SO IT CANNOT PASS AS BUILT.
# The ticket's falsifier reads: device-ness is answered by ASKING X — a health query over
# the bus. Nothing in the corpus can be asked that today. This constant is the tracked debt
# (Law 4: until a rule is physics it is an IOU, not a resting state), and the probe beside
# this file reports it on every firing so the gap is loud rather than remembered.
HEALTH_QUERY_CLAUSE = (
    "UNBUILT — no health-query protocol exists on the bus. Measured 2026-08-11: "
    "grep -rni health over cairn/ excluding proofs returns 21 hits, all prose plus one "
    "line of UU ancestry in cairn/tools/base/device.py. is_device() therefore answers the "
    "FITTED clause only; a member that is discovered but dead cannot be told from a "
    "member that is discovered and answering. Ticket: device-ness-is-decided-at-the-shim."
)


def fitted_device_ids(root: Path | str | None = None) -> set[str]:
    """The device roster, as the running loop knows it — the ruled predicate, RUN.

    Composed from ``cairn.devices.cairn.machines.ground_loop.discovery.device_folders``, never reimplemented: the
    folder walk, its pruning, and its ``probes/`` convention are ground_loop's to own, and a
    second copy here would drift from the one the beat actually uses.
    """
    from cairn.devices.cairn.machines.ground_loop.discovery import device_folders  # deferred: ground_loop imports base

    return {device_id for device_id, _folder in device_folders(root)}


def is_device(candidate: str, root: Path | str | None = None) -> bool:
    """Is ``candidate`` a device? The FITTED clause, answered once, for everyone.

    ``candidate`` is a device id — the directory's own name, which is what the ruling makes
    the identity. Answering by id rather than by object is what lets an EXTERNAL member be
    admitted: a Calibre-shaped device has no Python object to hand this function, and any
    signature that demanded one would re-create the inheritance axis in a new spelling.

    Returns FALSE for a thing that merely subclasses ``BaseDevice``. That is not a bug and
    it is the whole point — see ``divergence()``.
    """
    return candidate in fitted_device_ids(root)


def _class_census(root: Path, base_name: str) -> dict[str, list[str]]:
    """Which components declare a subclass of ``base_name`` — an AST CLASS census.

    Deliberately not a filename search. This ticket's own cast recorded three shims because
    its author looked for files named ``shim.py``; ``system_rackmount``'s shim is a class in
    ``rackmount.py``, so the convention hid it. The lesson is in the instrument now, where
    the next reader inherits it instead of rediscovering it.
    """
    hits: dict[str, list[str]] = {}
    for path in sorted(root.rglob("*.py")):
        parts = set(path.parts)
        if parts & {"proofs", "probes", "__pycache__"}:
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError, OSError):
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            for base in node.bases:
                name = base.attr if isinstance(base, ast.Attribute) else getattr(base, "id", None)
                if name == base_name:
                    rel = path.relative_to(root)
                    component = rel.parts[1] if len(rel.parts) > 1 else path.stem
                    hits.setdefault(component, []).append(f"{rel}::{node.name}")
    return hits


def claims_device_by_inheritance(root: Path | str | None = None) -> set[str]:
    """The OLD axis, still measurable: components declaring a ``BaseDevice`` subclass.

    Kept because the divergence is the finding. Deleting the old measure would make the two
    axes agree by making one of them unaskable.
    """
    from cairn.devices.cairn.machines.ground_loop.discovery import repo_root  # deferred, same reason as above

    root = Path(root) if root is not None else repo_root()
    return set(_class_census(root, "BaseDevice"))


def has_fitted_shim_class(root: Path | str | None = None) -> set[str]:
    """Components declaring a ``BaseShim`` subclass — the in-Python half of "a shim fits to it".

    A THIRD number, and not a synonym for ``fitted_device_ids``: a discovered device may have
    no Python shim at all (``DiscoveredShim`` is fitted TO it by the loop, at ``ground_loop``'s
    address, not at the device's). That gap is precisely what makes a Calibre-shaped member
    representable, so the two are reported separately rather than reconciled into one count.
    """
    from cairn.devices.cairn.machines.ground_loop.discovery import repo_root  # deferred, same reason as above

    root = Path(root) if root is not None else repo_root()
    return set(_class_census(root, "BaseShim"))


def divergence(root: Path | str | None = None) -> dict:
    """The three axes side by side, with names — never a count alone.

    A count is what lets a divergence sit still: "6" reads the same in a report whether it is
    the same six every week or a different six. The per-component lists are what a reader can
    act on, and they are what the probe carries back.
    """
    fitted = fitted_device_ids(root)
    inherited = claims_device_by_inheritance(root)
    shim_classes = has_fitted_shim_class(root)
    return {
        "ruled_devices": sorted(fitted),
        "claims_device_by_inheritance": sorted(inherited),
        "declares_a_shim_class": sorted(shim_classes),
        # Inherits device-hood but is not on the roster the beat reads. These are the
        # components whose charters and code read as devices while nothing fires for them.
        "inherits_but_not_ruled": sorted(inherited - fitted),
        # Ruled a device with no device class at all — the CALIBRE SHAPE, which the old axis
        # could not represent. A non-empty list here is the ruling working, not a fault.
        "ruled_but_inherits_nothing": sorted(fitted - inherited),
        "on_all_three": sorted(fitted & inherited & shim_classes),
        "symmetric_difference_ruled_vs_inherited": len(fitted ^ inherited),
        "health_query_clause": HEALTH_QUERY_CLAUSE,
    }
