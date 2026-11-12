"""DEVICENESS — the one callable answer to "is X a device?", and the divergence it exposes.

RULED BY AKIEN 2026-08-11: "a shim fits TO the device; you + your shim = your device."
Restated 2026-09-30 (the bus charter, ``cairn/devices/cairn/machines/bus/intention+why.json``):
"a device is a shim + it's component(s)" — the device = shim + the component or external
thing it talks to.

CORRECTED 2026-09-30: this header used to set a second line beside that one as his words —
"a device is a directory with a ``probes/`` subdirectory". Those were CC's gloss, not his;
the 2026-08-13 decision (``CairnCommons/decisions/2026-08-13-a-device-is-its-own-process-and-
the-roster-is-sorted.json``) retired the probes/ folder as the registration path. Since
ticket a808e21d646f membership is the rack: a folder directly under ``cairn/devices/``.

WHY THIS FILE EXISTS AT ALL. Device-ness was decided by INHERITANCE — a thing was a device
if it subclassed ``BaseDevice`` — and that axis cannot see an external device. Calibre was a
UU device with no device code at all, just its shim, because Calibre itself managed the
books. A class read can never admit that member, so the rule was restated in prose. It did
not hold: with the rule stated plainly in conversation, the same session measured
device-ness by reading ``BaseDevice`` inheritance TWICE. A rule that loses to a habit inside
one session is not a rule yet (Law 4) — so it is a function now, and the function is the
rule.

THIS COMPOSES, IT DOES NOT RE-DERIVE. Membership is ``cairn.tools.rack``'s to know: the
roster is the rack, read from folder names alone by one tool every caller uses (ticket
a808e21d646f). Asking it here is Law 1 — the answered question became structure, and a
second parallel roster would be exactly the failure the folder rule was ruled to end. Until
a808 this asked ground_loop's probes/ walk, which named 42 "devices" (tools such as base,
question and artifact among them) against 13 rack folders, measured 2026-09-30.

BOTH CLAUSES, AND THE SECOND ASKS. The falsifier of ticket 74d4124bc0e7 names two clauses: a
shim is fitted (``is_device``), AND the thing answers a health query over the bus
(``answers_health``). When 74d4 was built the second named nothing that existed (measured
2026-08-11) and was carried here as a constant declaring itself unbuilt. Every shim has since
answered the root view ``status`` (``cairn/tools/base/shim.py`` ``ROOT_VIEWS``), and ticket
7cb1989e7825 proved the tooth "the bus answers get status", so ticket f78a1a09e8ff built the
clause: ``is_live_device`` is fitted AND its shim answers ``get status``. Outline 5.8.3.2.3: a
shim answers what it can, so a cached reply from a sleeping device's shim is an answer.

WHAT THIS FILE IS NOT. It is not an authority and it grants nothing. Discovery decides
membership; this reads it and puts the two axes side by side so their disagreement can be
seen. Acting on that disagreement is each component's owner's act (Law 6).
"""

from __future__ import annotations

import ast
from pathlib import Path

# THE SECOND CLAUSE, BUILT (ticket f78a1a09e8ff). Kept as a named constant because the probe
# beside this file carries it on every firing.
HEALTH_QUERY_CLAUSE = (
    "a device answers a health query: its shim replies to `get status` (the root view in "
    "cairn/tools/base/shim.py ROOT_VIEWS) with exit 0 and data; is_live_device() asks it, "
    "is_device() answers the fitted clause alone."
)

# ask(device_id, verb, view) -> the shim's reply dict ({"exit", "data", ...}). Injected, so
# nothing here opens a bus (D1): the live path hands in the bus client's ask.
Ask = "Callable[[str, str, str], dict]"


def answers_health(device_id: str, ask) -> bool:
    """Does ``device_id``'s shim answer ``get status``? True only for exit 0 with data. A
    refusal, a raise, a non-dict, or data None is no answer."""
    try:
        reply = ask(device_id, "get", "status")
    except Exception:  # noqa: BLE001 — any failure to answer is the answer "no"
        return False
    return isinstance(reply, dict) and reply.get("exit") == 0 and reply.get("data") is not None


def is_live_device(candidate: str, ask, root: Path | str | None = None) -> bool:
    """Device-ness whole: fitted at the rack AND answering a health query."""
    return is_device(candidate, root) and answers_health(candidate, ask)


def fitted_device_ids(root: Path | str | None = None) -> set[str]:
    """The device roster — the rack, the ruled predicate, RUN.

    Composed from ``cairn.tools.rack.rack.rack_ids``, never reimplemented: which folders
    are devices is the rack tool's to know, and a second copy here would drift from it.
    """
    from cairn.tools.rack.rack import rack_ids

    return set(rack_ids(root))


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


_TIERS = {"devices", "tools", "machines"}


def _component_of(rel: Path, path: Path) -> str:
    """The component a file belongs to: the folder after the first tier folder
    (``devices``/``tools``/``machines``) in its path, else the second path part. Measured
    2026-10-03 (a808e21d646f): taking ``parts[1]`` alone named the TIERS — ``devices`` for
    every BaseDevice, ``devices``/``tools`` for every BaseShim — once the repo nested
    components under tier folders, so the inheritance axis named no component at all."""
    parts = rel.parts
    for i, part in enumerate(parts[:-2]):
        if part in _TIERS:
            return parts[i + 1]
    return parts[1] if len(parts) > 1 else path.stem


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
                    component = _component_of(rel, path)
                    hits.setdefault(component, []).append(f"{rel}::{node.name}")
    return hits


def claims_device_by_inheritance(root: Path | str | None = None) -> set[str]:
    """The OLD axis, still measurable: components declaring a ``BaseDevice`` subclass.

    Kept because the divergence is the finding. Deleting the old measure would make the two
    axes agree by making one of them unaskable.
    """
    from cairn.tools.rack.rack import repo_root

    root = Path(root) if root is not None else repo_root()
    return set(_class_census(root, "BaseDevice"))


def has_fitted_shim_class(root: Path | str | None = None) -> set[str]:
    """Components declaring a ``BaseShim`` subclass — the in-Python half of "a shim fits to it".

    A THIRD number, and not a synonym for ``fitted_device_ids``: a rack device may have no
    Python shim at all (``DiscoveredShim`` is fitted TO it by the bus client's roster, from
    ``ground_loop``'s address, not the device's). That gap is precisely what makes a Calibre-shaped member
    representable, so the two are reported separately rather than reconciled into one count.
    """
    from cairn.tools.rack.rack import repo_root

    root = Path(root) if root is not None else repo_root()
    return set(_class_census(root, "BaseShim"))


def divergence(root: Path | str | None = None, ask=None) -> dict:
    """The three axes side by side, with names — never a count alone.

    A count is what lets a divergence sit still: "6" reads the same in a report whether it is
    the same six every week or a different six. The per-component lists are what a reader can
    act on, and they are what the probe carries back. Given an ``ask``, it also splits the
    fitted devices into those whose shim answers ``get status`` and those that stay silent.
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
        **({} if ask is None else {"answers_health": sorted(d for d in fitted if answers_health(d, ask)),
                                   "fitted_but_silent": sorted(d for d in fitted if not answers_health(d, ask))}),
    }
