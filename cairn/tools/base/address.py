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
``cairn/devices/cairn/machines/ground_loop/discovery.device_folders`` for class-space, ``cairn/tools/base/deviceness.py`` for
the predicate — and a path resolver that quietly became the roster would be a second answer to
a question that already has one.

TWO FACES, ONE TABLE. A charter author writes a ROOTED TOKEN (``instance/devices/chart/0/packets``
— measured in use: of the five ``address`` values authored across every charter in the system,
two are instance-space device paths written that way). Code passes DEVICE AND INSTANCE as
arguments. Those are not rival vocabularies to choose between; they are two faces of one table,
and ``cairn/tools/base/proofs/test_instance_address.py`` pins them to each other by equality so they
cannot drift apart. ``cairn/machines/skill_block/counters.resolve`` is this module's ``resolve``,
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

# THE THREE ROOTS. Lowered here from cairn/machines/skill_block/counters.py on 2026-08-12 — the table
# was already injectable and already carried the why; what it lacked was an address the rest of
# the system could stand on.
#
# THIS MODULE IMPORTS pathlib AND NOTHING ELSE — measured, not asserted: import_map over it
# says ['__future__', 'pathlib']. That is what makes it a legal floor for every caller,
# including the ones whose proofs pin an import allowlist (cairn/devices/librarian/library.py and
# cairn/tools/chain/grammar.py both admit it by name, each with the measurement in the comment;
# the grammar's seat was orient's until 2026-08-13, when the chain grammar was carved out and
# took the address with it — the admitters change, the reason does not). Note what is NOT claimed: cairn/tools/base as a PACKAGE is not import-clean —
# deviceness.py reaches cairn.devices.cairn.machines.ground_loop.discovery and transitions.py reaches four
# components. The floor is this FILE, and the package __init__ is empty by the boot-order law
# written into it, so importing this leaf pulls none of that in.
_REPO = Path(__file__).resolve().parents[3]
_COMMONS = _REPO.parent / "CairnCommons"
_INSTANCE = Path.home() / ".cairn"

ROOTS = {"repo": _REPO, "commons": _COMMONS, "instance": _INSTANCE}

# The segment names, once. A reader looking for "where does tools/ come from" finds one answer.
DEVICES = "devices"
FOLDERS = "folders"
TOOLS = "tools"
MACHINES = "machines"
LOGS = "logs"


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


def folder_path(name: str, roots: dict[str, Path] | None = None) -> Path:
    """``<instance root>/folders/<name>`` — instance-space for a non-device component.

    A folder is a component that has runtime state (a DataRecorder, an instanceizer)
    but is not a device — no process, no bus presence, no instance number. The address
    is ``~/.cairn/folders/<name>/``, parallel to ``devices/<name>/<instance>/`` but one
    rung lighter: no instance segment because a folder has no instances to distinguish.
    """
    return resolve(f"instance/{FOLDERS}", roots) / str(name)


def log_path(device: str, instance: int = 0, roots: dict[str, Path] | None = None) -> Path:
    """``<instance root>/logs/<device>/<instance>`` — where a thing's LOGS live.

    NOT A SECOND ``instance_path``, and the difference is the one Akien's two rulings draw
    between them. ``instance_path`` answers "where does this device keep what is TRUE of it" —
    its state, and its own to gate (Law 6). This answers "where does this device write what
    HAPPENED to it", and the segments below ``logs`` are an INDEX, not a second ownership
    claim: *"in ~/.cairn/logs/<device>/<instance>/<whatever else> so the path mirrors the code
    tree"* (Akien, 2026-08-18).

    THE WHY IS RETENTION, AND HE STATED IT IN THE SAME BREATH AS THE SHAPE: *"easy to delete
    everything in the logs tree over 30 days old in one go."* That is what makes the two
    addresses different rather than redundant. A trail filed under each device's own state
    directory is fourteen sweeps, each reaching into a space its owner gates; one root is one
    deletion crossing nobody's gate. So the shape does not strain Law 6, it PROTECTS it — the
    prohibition this module carries above (a shared helper must not reach into every device's
    space to CREATE) reads identically in the DELETE direction, and this is how the sweep
    avoids it. Akien read that reasoning and ruled "agree" (2026-08-18).

    IT COMPOSES WITH THE 2026-08-12 RULING RATHER THAN OVERTURNING IT. That ruling — recorded
    at the top of this file — named ``logs`` top-level in the same breath as ``venv`` and
    ``backups``, so it had already settled that ``logs`` IS a machine-scoped root. What it did
    not say was what the inside of it looks like, and that is what 2026-08-18 settles. The
    ownership test is untouched: a file answering "what is true of this device" still lives
    under ``devices/<name>/<instance>/``.
    """
    return resolve(f"instance/{LOGS}", roots) / str(device) / str(instance)


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


# The class-space half of the same shape. instance_path/tool_path/machine_path address a
# device's LIFE under ~/.cairn; this addresses its CLASS under the repo — "one address written
# in two roots" (CLAUDE.md, ruled 2026-08-13).
CLASS_RUNGS = (TOOLS, MACHINES, DEVICES)


def component_of_module(module: str) -> str | None:
    """WHICH COMPONENT OWNS THIS DOTTED MODULE NAME — ``cairn.devices.cairn.machines.bus.bus`` -> ``bus``.
    ``None`` when the name sits under no rung at all.

    The third face of a question this module already answers twice: ``component_dir`` goes from
    a name to a directory, ``component_of`` goes from a path to a directory, and this goes from
    an IMPORT NAME to a component name. It exists because a class can be handed its own address
    for free — ``type(self).__module__`` is always there — which is what lets a device know what
    device it is without anybody telling it (``cairn/tools/base/diagnostic.py``, the caller this
    was written for). Before it, the only place in the running system that knew the string
    ``"ground_loop"`` was the runner that hand-spelled it, and a device that cannot name itself
    cannot write to an address keyed on its name.

    STRINGS ONLY, NO DISK, NO TREE WALK. ``component_of`` reads the real tree and is honest but
    expensive; this is asked at construction time by every device, so it is a split on a dotted
    name. The cost of that choice is real and named: this will happily answer for a module that
    does not exist, because it never checks. That is the right trade for the caller (a class
    that imported is a module that exists) and the wrong one for a caller holding an unvalidated
    string — such a caller wants ``component_dir``, which walks.

    THE DEEPEST RUNG WINS, which is the same rule ``component_of`` states and for the same
    reason: components nest, so ``cairn.devices.codemother.machines.orient.orient`` sits under both
    the ``builder`` device and the ``orient`` machine. Both are true and only one is its address;
    answering with the holder would attribute a machine's records to the device that assembles it.

    A NAME UNDER NO RUNG GETS ``None`` RATHER THAN A GUESS. ``__main__``, a doctest, a class
    defined in a proof — all real, none of them components, and inventing a component name for
    them would file records under a device that does not exist. The caller decides what to do
    with the honest absence; this does not decide for it.
    """
    parts = module.split(".")
    rungs = [i for i, p in enumerate(parts) if p in CLASS_RUNGS]
    if not rungs or rungs[-1] + 1 >= len(parts):
        return None
    return parts[rungs[-1] + 1]


def package_root(roots: dict[str, Path] | None = None) -> Path:
    """``<repo>/cairn`` — the package every component now sits two levels under."""
    return resolve("repo/cairn", roots)


def component_dirs(pkg_root: Path | str | None = None) -> tuple[list[Path], list[dict]]:
    """Every component directory in class-space, and the entries that could not be read.

    WHY THIS EXISTS AS A FUNCTION. Until 2026-08-13 a component sat at ``cairn/<name>/`` and
    every roster walker spelled that as one ``iterdir()``. The rung reorganisation moved them
    to ``cairn/<rung>/<name>/``, and the flat walk did not fail loudly — it returned THREE
    directories (the rung containers) and every caller carried on as though the tree had
    shrunk to three components. What caught it was HollowScan ("the census barely saw the
    tree"), which is Law 8's floor working exactly as designed and is the reason this is one
    function instead of four copies of a two-level loop.

    THE RUNGS ARE READ, NOT ASSUMED. A directory named in ``CLASS_RUNGS`` is descended into;
    anything else is judged on its own merits, so a component that has not migrated yet is
    still found and a fourth rung costs one constant. The component test is unchanged from
    the flat era: a directory holding ``*.py`` or an ``intention+why.json``. That union is
    load-bearing — it was widened to it on 2026-08-01 because ``skills/intent/`` was invisible
    to the ``*.py``-only test and the build gate refused the crossing.

    A HOLDER'S OWN RUNGS ARE RUNGS. CLAUDE.md grants a device the same shape one level down —
    "a device's held tools and machines nest under it at the same shape, tools/<name>/ and
    machines/<name>/, named and never numbered" — and until 2026-08-13 nothing on disk had
    ever used that grant, so the walk stopped at ``cairn/<rung>/<name>/`` and a nested
    component would simply not have existed as far as the roster, the derivation gate or any
    judge was concerned. It would not have failed; it would have gone QUIET, which is the same
    failure HollowScan caught the first time. The descent is therefore recursive rather than
    one-extra-level: a rung inside a component is descended wherever it appears, so the depth
    of the ladder costs nothing here and no future holder has to remember to widen this walk.

    An unreadable entry RIDES THE RETURN rather than crashing the walk or vanishing from it
    (Law 7, and the same shape ``device_census`` already used for the identical reason: a
    scan that dies on one entry reports nothing about the other twenty-three).
    """
    # A str root is accepted and coerced: the callers that inject one are the older
    # os.path-dialect modules (chart/constrain), and making each of them wrap in Path()
    # would put the coercion at four call sites instead of at the one door.
    root = Path(pkg_root) if pkg_root is not None else package_root()
    components: list[Path] = []
    unreadable: list[dict] = []

    def looks_like_a_component(d: Path) -> bool:
        return bool(list(d.glob("*.py"))) or (d / "intention+why.json").is_file()

    def held_rungs(c: Path) -> None:
        """Descend whatever rungs this component holds. Only a directory NAMED in
        CLASS_RUNGS is entered, which is what keeps ``proofs/``, ``probes/`` and
        ``validations/`` from being read as components — they are a component's
        record, not smaller components inside it."""
        for rung in CLASS_RUNGS:
            sub = c / rung
            if sub.is_dir():
                walk(sub)

    def walk(container: Path) -> None:
        for c in sorted(container.iterdir()):
            try:
                if not c.is_dir() or c.name == "__pycache__":
                    continue
                if looks_like_a_component(c):
                    components.append(c)
                # UNCONDITIONAL, not an else and not folded into the branch above: a
                # holder that has not yet grown code of its own still holds what it
                # holds, and hiding the descent behind the holder's own component-ness
                # would make the parts visible or invisible depending on a fact about
                # the parent. That is exactly the quiet failure this walk exists to end.
                held_rungs(c)
            except OSError as e:
                unreadable.append({"path": str(c), "why": f"UNREADABLE: {e}"})

    for d in sorted(root.iterdir()):
        try:
            if not d.is_dir() or d.name == "__pycache__":
                continue
            if d.name in CLASS_RUNGS:
                walk(d)
            else:
                if looks_like_a_component(d):
                    components.append(d)
                held_rungs(d)
        except OSError as e:
            unreadable.append({"path": str(d), "why": f"UNREADABLE: {e}"})
    return components, unreadable


class AmbiguousComponent(LookupError):
    """A bare name that two rungs both answer to. Carries every home it found.

    THE NAME IS NOT THE ADDRESS ANY MORE, and this is what says so out loud. The
    first live instance was born the day the rungs landed: ``orient`` is a TOOL
    (``cairn/tools/orient`` — the deterministic scanner) and, since the chart
    decomposition of 2026-08-13, also a MACHINE (``cairn/devices/codemother/machines/orient``
    — that scanner plus the chain glue, held by the device whose parts the pre-build
    stages are). Both are correct; the layering is the point, and the nesting makes it
    louder rather than quieter: the two homes are now three rungs apart, not one.
    What is not correct is a lookup answering with whichever one sorts first, which
    is what happened silently until this class existed: ``constrain`` would have read
    the machine's charter while its own roster meant either, and reported the result
    as the charter of "orient".

    A pointer that resolves to two places is not a pointer, and Law 7 puts the loud
    end of that at the diagnostic surface: the caller is told BOTH homes and asked to
    say which, rather than handed one of them and left to find out later."""

    def __init__(self, name: str, homes: list[Path]):
        self.name = name
        self.homes = list(homes)
        super().__init__(
            "%r names %d components, not one: %s — the rung is not part of the name, "
            "so a bare name that two rungs answer to is not an address. Say which "
            "(a path resolves unambiguously)."
            % (name, len(homes), ", ".join(str(h) for h in homes)))


def component_dir(name: str, pkg_root: Path | str | None = None) -> Path | None:
    """Where the component called ``name`` lives, or ``None`` if no such component.
    Raises ``AmbiguousComponent`` when more than one rung answers to the name.

    THE RUNG IS NOT PART OF THE NAME, and this is the function that keeps it that way.
    Before 2026-08-13 a caller holding a component NAME could build its path by
    concatenation — ``cairn/<name>/`` — and several did (``chart/constrain`` reading a
    ref's charter, ``cairnmap/cli`` resolving a bare argument). After the move that
    concatenation is a guess about which rung, and a wrong guess reads as "no charter
    there", which is a red about the component rather than about the caller.

    So the lookup is a WALK, not an assumption: nothing here knows or decides that
    ``base`` is a tool. A component that changes rung changes nothing at any call site.
    NOT-FOUND AND AMBIGUOUS ARE DIFFERENT ANSWERS, and they leave by different doors.
    Returns ``None`` for not-found, because every caller today is already asking a
    question that has "there is no such component" as a real answer. RAISES for
    ambiguous, because no caller has a right answer to give: one home would be a guess
    and ``None`` would be a lie about a component that demonstrably exists — twice.

    ``pkg_root`` IS NOT OPTIONAL FOR AN INJECTED CALLER, and forgetting it is a live
    measured defect rather than a hypothetical one: chart/constrain runs its proofs
    against a temp world, and the first version of this call read the LIVE tree instead
    — so the floor answered a question about the real repo while the proof asked about
    its fixture. Every caller that already takes a root passes it through.
    """
    homes = [d for d in component_dirs(pkg_root)[0] if d.name == name]
    if len(homes) > 1:
        raise AmbiguousComponent(name, homes)
    return homes[0] if homes else None


def rung_of(comp_dir: Path | str, pkg_root: Path | str | None = None) -> str | None:
    """Which rung this component sits on: ``'devices'``, ``'tools'``, or ``'machines'``.
    ``None`` for a component outside the rung structure (skills, bin, launchers).

    Reads the path, never a declaration — the rung IS the directory name on the path,
    and a directory under ``cairn/devices/`` is a device by being there (Law 4).
    """
    root = Path(pkg_root) if pkg_root is not None else package_root()
    try:
        rel = Path(comp_dir).resolve().relative_to(root.resolve())
    except ValueError:
        return None
    found = None
    for part in rel.parts:
        if part in CLASS_RUNGS:
            found = part
    return found


def component_of(path: Path | str, pkg_root: Path | str | None = None) -> Path | None:
    """WHICH COMPONENT OWNS THIS PATH — the other half of ``component_dir``, which answers
    the same question from the other end. ``None`` when the path sits under no component.

    WHY IT HAD TO EXIST, MEASURED 2026-08-14. ``constrain``'s floor walked the refs on an
    orient packet and kept only the ones that appeared in the component ROSTER — a set of
    bare names. But since orient's floor started grounding its refs, a ref is a PATH far
    more often than a name: across the 45 berthed orient packets, 266 of 310 refs are
    paths, so the membership test discarded 86% of the floor's own input and constrain
    emitted an empty constraint list. Nothing redded, because an empty list is a legal
    list. A name-keyed lookup asked of path-shaped data is the whole defect, and it is
    fixed by having the lookup that accepts the other shape rather than by teaching each
    caller to guess.

    THE DEEPEST ANCESTOR WINS, and that is not a tie-break — it is the answer. Components
    nest (CLAUDE.md grants a device ``tools/<name>/`` and ``machines/<name>/`` at the same
    shape), so ``cairn/devices/codemother/machines/orient/orient.py`` sits under BOTH the
    ``builder`` device and the ``orient`` machine. Both are true statements about the file
    and only one of them is its address; the shallower one is the holder, and answering
    with the holder would attribute a machine's code to the device that assembles it.

    NOT AMBIGUOUS, WHICH IS WHY THIS RETURNS WHERE ``component_dir`` RAISES. A bare name
    that two rungs answer to has no answer — either home would be a guess. A path has
    exactly one deepest owner by construction, which is the reason ``AmbiguousComponent``
    tells its caller "a path resolves unambiguously": this is the function that makes that
    sentence true rather than merely advisory.
    """
    # ``Path.expanduser`` and not ``os.path`` — this leaf imports pathlib and NOTHING
    # else, a property measured and leaned on at constrain's import site, so a
    # convenience import here would quietly cost another component its stated shape.
    target = Path(str(path)).expanduser().resolve()
    owners = []
    for c in component_dirs(pkg_root)[0]:
        resolved = c.resolve()
        if target == resolved or resolved in target.parents:
            owners.append(resolved)
    if not owners:
        return None
    return max(owners, key=lambda d: len(d.parts))
