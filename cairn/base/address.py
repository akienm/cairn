"""ADDRESS — the one owner of where a thing lives, class-space and instance-space both.

THE MEASUREMENT THAT PRODUCED THIS FILE (2026-08-12, ticket ``one-owner-for-the-instance-address``).
The instance-space path shape is SETTLED — CLAUDE.md carries the instance-0 rule, and Akien's
four-rung ruling of 2026-08-12 generalised it to every device with ``tools/<name>/`` and
``machines/<name>/`` beneath. It was re-derived by hand at TEN sites in class-space, nine of
which also baked in ``Path.home()``:

    sudo_relay/relay.py:103          devices/sudo_relay/0
    ground_loop/liveness.py:46       devices/ground_loop/<instance>   (the only one taking the instance)
    build_inspector/inspector.py:216 devices/chart                    (another device's space)
    learning_block/learning_block.py:83      devices/learning_block/0/traces
    learning_block/probes/engine_trace_corpus.py:42   THE SAME ADDRESS, SPELLED TWICE
    inference_domain/route.py:44     .cairn/inference/hosts.json      (off the devices/ ladder)
    skill_block/counters.py:39       the .cairn root itself, as the root table
    librarian/library.py:43          devices/librarian/0/library
    skill_block/skill_block.py:46    devices/skill_block/0/berths
    chart/orient.py:51               devices/chart/0/packets

**THE TOP LEVEL OF ~/.cairn/ IS FOR WHAT IS NOT ANY DEVICE'S STATE** — Akien, 2026-08-12, two
rulings with one shape. On the one entry above that sits off the devices/ ladder: *"devices/
inference_domain/0/ is exactly right. ruled with a smile"* — ``hosts.json`` is
``inference_domain``'s own state, so it belongs in ``inference_domain``'s own space, and the
move creates that space (no ``devices/inference_domain/`` exists yet). And on what legitimately
stays at the top: *"i think what i see is ~/.cairn/venv and not ~/.cairn/anything else/venv —
~/.cairn/venv is correct"* — ONE venv per box, never one per device, and the same for ``logs``
and ``backups``. So the test is not depth, it is OWNERSHIP: a file that answers "what is true of
this machine" lives at the top; a file that answers "what is true of this device" lives under
``devices/<name>/<instance>/``, singleton or not. Recorded here because the site is in the table
above; the move itself is owed and rides the sail batch. CC had proposed instead that the ladder
was MISSING A MACHINE-SCOPED RUNG and asked which it was — overruled, and it was an invented
blocker: ``venv`` proves the top level already has a coherent job, and the file was simply in
the wrong place.

The drift is not hypothetical and it did not wait: ``~/.cairn/devices/learning_block/0/traces``
was spelled out character-for-character in a device AND in that device's own probe — one
component, one settled address, two independent derivations. That is Law 1's defect at the
smallest possible scale, and it is what a resolver stops.

THE LIVED SYMPTOM, which is not tidiness: provisioning instance 1 of anything meant finding and
editing nine files, and a shipped app whose root is not under this developer's home directory
could not run at all. Akien's stated reason (II) for the four-rung ruling — "it leaves open the
possibility to expand in the future without rearchitecting that part" — was bought in the
DIRECTORY LAYOUT and not in the CODE. This module buys the code half.

**THIS RESOLVES AND NEVER TOUCHES DISK.** No mkdir, no create-on-read, no exists-check that
creates. The bound is what keeps Law 6 a distinction rather than a collision: instance space
belongs to the device that owns it, computing an address opens nothing and crosses nobody's
gate, and a shared helper that reached into every device's space to CREATE would be that
failure written once and called convenient. Provisioning is a different act with a different
owner.

**IT TAKES NO POSITION ON WHETHER A NAME IS A DEVICE.** It computes an address for whatever
name it is handed. Which names are devices is answered elsewhere and by someone else —
``cairn/ground_loop/discovery.device_folders`` for class-space, ``cairn/base/deviceness`` for
the predicate — and a path resolver that quietly became the roster would be a second answer to
a question that already has one.

TWO FACES, ONE TABLE. A charter author writes a ROOTED TOKEN (``instance/devices/chart/0/packets``
— measured in use: of the five ``address`` values authored across every charter in the system,
two are instance-space device paths written that way). Code passes DEVICE AND INSTANCE as
arguments. Those are not rival vocabularies to choose between; they are two faces of one table,
and ``cairn/base/proofs/test_instance_address.py`` pins them to each other by equality so they
cannot drift apart. ``cairn/skill_block/counters.resolve`` is this module's ``resolve``,
re-exported at its own address — the token face did not move, only the table beneath it.

THE ROOT VALUES ARE DERIVED, NEVER CONFIGURED — repo from this module's own address, commons as
its sibling, instance from the home directory. That is house style with a proof behind it
(``ground_loop.discovery.repo_root``: "derived from this file's own address, never
configured"). The ``roots`` parameter is the ONE seam at which they can be pointed elsewhere,
which is what makes the packaged-app claim testable at all — and what lets a proof run against
a temp directory instead of polluting the live tree it will be read against.
"""

from __future__ import annotations

from pathlib import Path

# THE THREE ROOTS. Lowered here from cairn/skill_block/counters.py on 2026-08-12 — the table
# was already injectable and already carried the why; what it lacked was an address the rest of
# the system could stand on.
#
# THIS MODULE IMPORTS pathlib AND NOTHING ELSE — measured, not asserted: import_map over it
# says ['__future__', 'pathlib']. That is what makes it a legal floor for every caller,
# including the ones whose proofs pin an import allowlist (cairn/librarian/library.py and
# cairn/chart/orient.py both admitted it by name on 2026-08-12, each with the measurement in
# the comment). Note what is NOT claimed: cairn/base as a PACKAGE is not import-clean —
# deviceness.py reaches cairn.ground_loop.discovery and transitions.py reaches four
# components. The floor is this FILE, and the package __init__ is empty by the boot-order law
# written into it, so importing this leaf pulls none of that in.
_REPO = Path(__file__).resolve().parents[2]
_COMMONS = _REPO.parent / "CairnCommons"
_INSTANCE = Path.home() / ".cairn"

ROOTS = {"repo": _REPO, "commons": _COMMONS, "instance": _INSTANCE}

# The segment names, once. A reader looking for "where does tools/ come from" finds one answer.
DEVICES = "devices"
TOOLS = "tools"
MACHINES = "machines"


class Unreadable(Exception):
    """The store could not be reached or read. Distinct from 'the store holds nothing'."""


def resolve(address: str, roots: dict[str, Path] | None = None) -> Path:
    """``<root>/<rest>`` -> a real path. An unknown root is a charter defect, said so."""
    table = roots or ROOTS
    head, _, rest = address.partition("/")
    if head not in table:
        raise Unreadable(
            f"address {address!r} starts with {head!r}, which is not one of "
            f"{sorted(table)}. A rooted address is a token, not a "
            "filesystem path — a bare path would resolve differently on another box."
        )
    return table[head] / rest


def instance_path(device: str, instance: int = 0, roots: dict[str, Path] | None = None) -> Path:
    """``<instance root>/devices/<device>/<instance>`` — an instance's own space.

    THE INSTANCE SEGMENT IS NEVER OPTIONAL. A singleton is instance ``0``, not an exemption,
    for Akien's two stated reasons: "(A) same rules for everything, no special cases, and
    (II) it leaves open the possibility to expand in the future without rearchitecting that
    part." The default here is a defaulted ARGUMENT, not an omittable SEGMENT — ``0`` still
    appears in every path this returns. It exists because this generalises
    ``ground_loop.liveness.instance_home(instance=0)``, which already carried it and already
    said why in its own docstring: "instance 0 is the singleton, not a special case."
    """
    return resolve(f"instance/{DEVICES}", roots) / str(device) / str(instance)


def tool_path(device: str, instance: int, tool: str,
              roots: dict[str, Path] | None = None) -> Path:
    """``.../<device>/<instance>/tools/<tool>`` — a tool held by that instance.

    THE HELD PART IS ADDRESSED BY NAME, NEVER BY NUMBER: "so it is
    ``tools/gate/buildme_entry/probes``, never ``tools/gate/2/probes``, because a number makes
    a reader memorise a mapping" (Akien, 2026-08-12). ``tool`` is therefore a name and there is
    no ordinal parameter to encode the killed shape back into the signature.

    The instance is named plainly here rather than defaulted: these two rungs have no incumbent
    whose callers would all have to grow a ``0``, so they take the strictest reading of the rule.
    """
    return instance_path(device, instance, roots) / TOOLS / str(tool)


def machine_path(device: str, instance: int, machine: str,
                 roots: dict[str, Path] | None = None) -> Path:
    """``.../<device>/<instance>/machines/<machine>`` — a machine held by that instance.

    The fourth rung of the 2026-08-12 ladder (TOOLS -> MACHINES -> DEVICES -> DEVICE INSTANCES,
    a complexity axis). Same name-not-number rule as ``tool_path``, same silence about whether
    the holder is a device.
    """
    return instance_path(device, instance, roots) / MACHINES / str(machine)
