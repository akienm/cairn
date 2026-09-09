"""trouble/shim.py — the trouble lane's always-on front, and the ONE writer of its store.

WHY THIS FILE EXISTS AT ALL. Until 2026-09-07 anyone who wanted to report a fault
imported ``TroubleDevice`` and called it, in their own process. That worked, and the
build inspector's ``device_isolation_holds`` sieve was red about it every run: two
devices (``cairn``, ``web_server``) held a cross-device import, and no device may import
another (``db_domain`` is the sole exception). The panel Akien opens was built on the
red. Ticket ``9579a6f9cec6``.

THE SPLIT, in Akien's words (2026-09-07): *"anybody can send a trouble ticket. but a
trouble ticket should not be an import. in fact, i'd say a trouble ticket is in a similar
class with logging."* — then, on the split below: *"a good choice. i'd forgotten it was
it's own device!"*

  SENDING IS A TOOL.  ``DiagnosticBase.raise_trouble`` — inherited by everything, no
                      import, one emission file in the raiser's own log home.
  HOLDING IS OWNED.   This shim. It drains those emissions into ``CairnCommons/troubles/``
                      in the ONE process that owns the store, and answers ``live`` and
                      ``clear`` on the bus.

WHY THE FOLD CANNOT LIVE WITH THE RAISER, which is the whole reason this is a device and
not a second tool. Incrementing a count is a read-modify-write on a shared JSON file. Two
processes raising the same identity at the same moment both read count 3 and both write
4, and the lane's entire value is that the count is trustworthy (see ``trouble.py``: *"a
count is only trustworthy if there is one way to increment it"*). Raising is append-only
into a directory nobody else writes, so it needs no owner; folding is not, so it has one.
That is Law 6's own test applied rather than quoted.

THE DRAIN SKIPS TROUBLE'S OWN LOG HOME, and this is not an optimisation — it is a
correctness bound with a cycle behind it. ``TroubleDevice.raise_trouble`` (the fold)
emits its own ``raise_trouble`` breadcrumb when a ticket lands, into ``trouble``'s log
home, because that landing IS a gate contact worth recording. Drain that directory and
every fold manufactures the raise that causes the next fold, forever. So the owner's own
trail is read by nobody here. The trouble device raising a fault ABOUT ITSELF still works
and needs no drain at all: it owns the store, so it writes directly, which is the same
Law 6 clause seen from the inside.

POKE, THEN READ YOUR OWN STORE. A raiser wired with ``set_trouble_notifier`` pokes
``receive_raise``, which ignores the record it is handed and runs the ordinary drain —
exactly the way ``BaseShim._receive_poke`` ignores its envelope and runs
``_check_mail``. One code path reaches the store, so a poked raise and a beat-drained
raise cannot land differently, and a poke can never double-count a record the beat
already folded. The beat is the backstop, not a poller: it drains what it finds and
nothing else (memory ``reaching-for-daemons-is-drift`` — a backstop that grew logic would
be a poller wearing a coat).

THE WATERMARK is per source directory, and it is the emission FILENAME. Breadcrumb files
are named by a UTC stamp to the microsecond, so filename order IS write order within a
directory, and "everything after this name" is a complete, gap-free description of what
has not been folded. It lives in trouble's own instance home — ``state`` about what this
device has done, which is instance-space, never git (the roots table).

    python3 cairn/devices/trouble/proofs/test_trouble.py     # exit 0 = green
"""

from __future__ import annotations

import json
from pathlib import Path

from cairn.tools.base.address import LOGS, instance_path, resolve
from cairn.tools.base.shim import BaseShim

WATERMARK_NAME = "drained.json"

# The gate every raise is emitted under, and therefore the suffix every raise's filename
# carries (``BreadcrumbLog._emission_filename`` puts the gate in the name). Globbing on it
# means the drain reads only raises — never every breadcrumb every device ever wrote.
RAISE_GATE = "raise_trouble"

# The other two lanes, added 2026-09-08 when the SEND half of a clear stopped being a bus
# request (ticket 9579a6f9cec6). Same physics as the raise: one file per emission under the
# sender's own log home, folded here, in the one process that owns the store. The ORDER
# below is the drain order and it is deliberate — raises fold before reconciles, so a run
# that reports a new finding and its complete current picture in the same breath lands the
# raise first and then measures the picture against a store that already holds it.
CLEAR_GATE = "clear_trouble"
RECONCILE_GATE = "reconcile_troubles"
GATES = (RAISE_GATE, CLEAR_GATE, RECONCILE_GATE)


class TroubleShim(BaseShim):
    """The trouble device's always-on front: drains raises, answers the bus."""

    def __init__(self, bus=None, *, roots: dict[str, Path] | None = None,
                 root: str | Path | None = None) -> None:
        super().__init__(bus=bus)
        # Both injectable for the same reason ``BreadcrumbLog`` takes ``roots``: a proof
        # must be able to run the whole drain against a tree it owns. An acceptance
        # read-back means nothing if running the proof could have written the live store.
        self._roots = roots
        self._root = Path(root) if root else None
        self._watermarks: dict | None = None

    @property
    def device_id(self) -> str:
        return "trouble"

    def _start_device(self):
        from cairn.devices.trouble.trouble import TroubleDevice
        return TroubleDevice(root=self._root)

    # --- the watermark: what has already been folded ------------------------

    def _watermark_path(self) -> Path:
        return instance_path("trouble", 0, self._roots) / WATERMARK_NAME

    def _load_watermarks(self) -> dict:
        if self._watermarks is not None:
            return self._watermarks
        p = self._watermark_path()
        if not p.exists():
            self._watermarks = {}
            return self._watermarks
        try:
            loaded = json.loads(p.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            # An unreadable watermark must not silently re-fold the whole history into
            # inflated counts. Starting from empty would do exactly that, so the honest
            # move is to refuse the drain (below) rather than guess how far it got.
            self._watermarks = {"__unreadable__": str(p)}
            return self._watermarks
        self._watermarks = loaded if isinstance(loaded, dict) else {}
        return self._watermarks

    def _save_watermarks(self) -> None:
        p = self._watermark_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(self._watermarks or {}, indent=2, sort_keys=True) + "\n",
                     encoding="utf-8")

    # --- the drain ----------------------------------------------------------

    def _source_dirs(self) -> list[Path]:
        """Every ``<logs>/<device>/<instance>/`` directory EXCEPT this device's own.

        The exclusion is the cycle bound documented at the top of this file, and it is
        expressed as a path comparison rather than a name test so a temp-roots proof gets
        the same protection the live tree does.

        The root is ``instance/logs``, the same token ``log_path`` resolves — NOT
        ``folder_path(LOGS)``, which is ``instance/folders/logs`` and is where the first
        draft of this method looked. It found an empty directory and reported a clean
        drain, which is the shape this whole lane exists to refuse: a green that means
        'I looked in the wrong place'. Caught by running it, not by reading it."""
        logs = resolve(f"instance/{LOGS}", self._roots)
        if not logs.exists():
            return []
        mine = logs / self.device_id
        out = []
        for device_dir in sorted(logs.iterdir()):
            if not device_dir.is_dir() or device_dir == mine:
                continue
            for instance_dir in sorted(device_dir.iterdir()):
                if instance_dir.is_dir():
                    out.append(instance_dir)
        return out

    def drain(self) -> dict:
        """Fold every raise emitted since the last drain into the held store.

        Returns a record of what happened — folded ids, per-directory counts, and any
        refusals — never a bare count: a drain that folded three and refused one has to
        be able to say so (Law 7).

        A refusal on ONE emission does not stop the batch, and does not advance the
        watermark past itself either. The alternative — skip it and move on — would make
        an unreadable raise a silently dropped fault, in the lane whose entire purpose is
        that nothing fails silently."""
        marks = self._load_watermarks()
        if "__unreadable__" in marks:
            return {"outcome": "refused", "folded": [], "refused": [
                {"error": "the drain watermark is unreadable, so how much has already "
                          "been folded is unknown — draining now would re-fold history "
                          "into inflated counts. Read or remove: "
                          + marks["__unreadable__"]}]}
        self._ensure_device()
        if self._device is None:
            self._device = self._start_device()
        folded: list[dict] = []
        refused: list[dict] = []
        for source in self._source_dirs():
            key = f"{source.parent.name}/{source.name}"
            for gate in GATES:
                # ONE WATERMARK PER GATE. The raise lane keeps the bare key it has always
                # used, so watermarks written before the other two lanes existed still mean
                # what they meant. A shared watermark would be wrong rather than merely
                # untidy: the names are timestamps, and three gates interleaving under one
                # high-water mark would let a late raise skip an early clear for good.
                mark_key = key if gate == RAISE_GATE else f"{key}::{gate}"
                high = marks.get(mark_key, "")
                names = sorted(p.name for p in source.glob(f"*.{gate}.json"))
                for name in names:
                    if name <= high:
                        continue
                    try:
                        record = json.loads((source / name).read_text(encoding="utf-8"))
                        outcome = self._fold(gate, record, name)
                    except Exception as exc:  # noqa: BLE001 — one bad emission cannot stop the batch
                        refused.append({"emission": f"{key}/{name}",
                                        "error": f"{type(exc).__name__}: {exc}"})
                        break  # the watermark stops HERE; this fault is not skipped past
                    folded.append({"emission": f"{key}/{name}", **outcome})
                    marks[mark_key] = name
        self._watermarks = marks
        if folded:
            self._save_watermarks()
        result = {"outcome": "ok", "folded": folded}
        if refused:
            result["refused"] = refused
        return result

    def _fold(self, gate: str, record: dict, name: str) -> dict:
        """Apply one drained emission to the held store. The OWNER'S half of every lane.

        THE HOLDER DECIDES, AND DECLINING IS AN OUTCOME, NOT AN ERROR. A clear naming a
        trouble that is not live, or a reconcile whose scope matches nothing, folds to
        ``declined``/``nothing to clear`` and lets the watermark advance. Raising instead
        would be the wrong shape twice over: the sender only reported what it observed
        (Law 6 — the judgment is the owner's), and a permanent refusal in this lane wedges
        the watermark forever, so one already-cleared trouble would stop every later
        emission from every device behind it.
        """
        pointer = record.get("pointer") or ""
        values = record.get("values") or {}
        if gate == RAISE_GATE:
            return self._device.raise_trouble(
                pointer,
                why=values.get("why") or "",
                detail={**(values.get("detail") or {}),
                        "raised_by": record.get("source"),
                        "raised_at": record.get("ts"),
                        "emission": name})
        # EVERY COMPARISON AGAINST THE LIVE SET GOES THROUGH THE STORE'S OWN ADDRESSING RULE.
        # The doors slug what they are handed, so what is on disk is always the slug — and
        # both lanes below compare a SENDER'S identity against those stored ids before
        # deciding anything. Comparing the raw pointer was wrong in both, with opposite and
        # both-bad failures, measured live on 2026-09-08 (the day the two lanes shipped):
        #
        #   clear     — 5 of 5 tester clears folded to "declined — not live". The tester
        #               names a trouble after its proof file (test_inspector_nexus); the
        #               store holds test-inspector-nexus. Nothing it ever fixed could clear,
        #               and validation-verdict-changed-test-inspector-nexus sat in the
        #               operator inbox with its proof standing green.
        #   reconcile — the DANGEROUS direction. `still` is the sender's complete current
        #               picture, so an unslugged entry does not match the trouble it names
        #               and that trouble reads as stale — CLEARED while it is still standing.
        #               A loud wrong trouble is safe; a quiet cleared one is not (Law 7).
        #
        # The scope prefix is slugged for the same reason, and slugging is idempotent, so a
        # sender that already speaks in slugs (the build inspector does) is unaffected.
        ident_of = self._device.identity_of
        if gate == CLEAR_GATE:
            wanted = ident_of(pointer)
            if wanted not in {t.get("id") for t in self._device.live()}:
                return {"outcome": "declined", "id": wanted,
                        "why": "not live — nothing standing under that identity to clear"}
            return self._device.clear(wanted, by=values.get("by") or "cc",
                                      what_changed=values.get("what_changed") or "")
        if gate == RECONCILE_GATE:
            still = {ident_of(s) for s in (values.get("still") or [])}
            # THE TRAILING SEPARATOR IS PART OF THE SCOPE AND `identity_of` STRIPS IT.
            # Slugging is right for an identity and half-right for a PREFIX: the store's
            # rule folds "_" to "-" and lowercases (both wanted here), and it also trims
            # the ends (not wanted here). Dropping the trailing "-" would silently widen
            # "inspector-new-finding-" to match "inspector-new-findings-…" as well — a
            # reconcile reaching outside its scope, which is the one thing this lane's own
            # proof calls its real tooth. So slug the body, put the separator back.
            scope = ident_of(pointer) + ("-" if pointer.rstrip().endswith(("-", "_")) else "")
            stale = sorted(t.get("id") for t in self._device.live()
                           if str(t.get("id", "")).startswith(scope)
                           and t.get("id") not in still)
            cleared = []
            for ident in stale:
                cleared.append(self._device.clear(
                    ident, by=values.get("by") or "cc",
                    what_changed=values.get("what_changed") or ""))
            return {"outcome": "reconciled", "scope": scope,
                    "still": len(still), "cleared": cleared}
        raise ValueError(f"no fold for gate {gate!r} — the drain scanned a lane it "
                         f"cannot apply, which would silently drop the emission")

    def receive_raise(self, _record: dict | None = None) -> dict:
        """The injected notifier's contract — poked by a raiser at raise time.

        The record it is handed is IGNORED, exactly as ``BaseShim._receive_poke`` ignores
        its envelope: the emission is already on disk, and reading it from there is the
        one path that cannot double-count against the watermark. What this buys over the
        beat alone is latency — the ticket exists now, not on the next pulse."""
        return self.drain()

    # --- (1) the beat is the backstop --------------------------------------

    def on_pulse(self, now, context: dict | None = None) -> dict:
        """The ordinary pulse, plus a drain of anything no poke delivered.

        Additive on purpose: everything ``BaseShim`` records about a pulse is untouched,
        and the drain rides beside it under its own key. A raiser in another process that
        never wired a notifier is reached here and only here."""
        record = super().on_pulse(now, context)
        record["drained"] = self.drain()
        return record
