"""counting_block — a count table over (path class, verb, caller class), compiled from the
two artifact journals, that raises one trouble for the row it has never seen.

Ticket 5a4ec289bf15. A tenant of the learning-block anatomy
(I-the-system-is-a-learning-block): the DOOR is the artifact door's journal (every record
write already lands there with its caller measured from the kernel), the PRIOR is this
table, the ERROR SIGNAL is a zero-count triple after arming, and the LOCAL ADJUSTMENT is
an akien-class clearance adding one to the row. Law 1 as arithmetic: a triple seen 400
times is settled and costs nobody attention; the unseen one is the novel thing the
resolver is for. Law 3: the table is MEASURED from the journals, never authored, and it
is reproducible from them alone — delete it, recompile, byte-identical.

THE FOLD IS PURE AND WHOLE. ``compile`` takes the journals as lists and returns the table;
it reads no disk and keeps no state. Each beat recompiles from line one rather than
folding the new lines onto the last table, because the two journals interleave by ``at``
and an incremental fold would be order-unstable across the root boundary — a raise could
depend on which journal happened to be read first. The journals are small (2,674 entries
on 2026-09-17, well under a second) and correctness over the boundary is worth the read.

ARMING is the genesis entry of this machine's own charter in the cairn journal. Everything
before it counts freely — that is the prior, and nothing before arming is judged. After
it, an entry whose row is nonzero adds one; an entry whose row is zero is a RAISE and the
row stays at zero (the block learned nothing from an unowned novelty). A clearance of a
who-writes-what trouble by an akien-class caller adds one to the raised row, so the same
triple stops raising; a cc-class clearance adds nothing, so the triple raises again as a
recurrence — cc clearing its own novel write must not teach the table that cc's novelty
is normal (the cast's missing_check (a)). Hard zero, no smoothing: on day one a new
component's first state.json IS news (missing_check (b)); the WATCHME measures whether
the raise rate falls.

THE BLOCK RAISES THROUGH THE INHERITED EMISSION, NEVER THE DEVICE. ``machine_imports_no_device``
reds any top-level machine that imports ``cairn.devices.*``, and the ruling behind it is
that a trouble report is logging-shaped (Akien 2026-09-07): ``ModuleRaiser.raise_trouble``
writes one emission into this machine's own log home and the trouble device folds it at
its drain — one ticket per identity, counted, never raced. The identity names the triple,
so the second raise of a triple is the same trouble as the first.

WHO RUNS IT: nobody of its own. ``groundloop/pulse.py`` beside this file is discovered by
the ground loop and ``on_pulse`` calls ``pulse()`` on the beat; the beat's pulse service
is the poke the ticket's how called the door's probe poke (a --decide line on the ticket).
No poller, no process, no registry — ``ps`` shows nothing (falsifier clause 4).
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

from cairn.tools.artifact import artifact as door
from cairn.tools.base.address import instance_path
from cairn.tools.base.diagnostic import ModuleRaiser

COMPONENT = "counting_block"
#: The entry whose appearance in the cairn journal arms the block.
CHARTER_REL = "cairn/machines/counting_block/intention+why.json"
ARMING_ROOT = "cairn"
ARMING_VERB = "genesis"
#: The trouble store's directory under the commons root, and the identity prefix every
#: raise carries — the clear entries the fold reads back are on ``troubles/<slug>.json``.
TROUBLE_DIR = "troubles"
TROUBLE_ROOT = "CairnCommons"
IDENTITY_PREFIX = "who-writes-what-"
#: The WATCHME's two clocks: the raise-rate window and the every-N-appends trigger.
WINDOW = 200
BUCKET = 100
TABLE_FILE = "table.json"
ACK_FILE = "probe_ack.json"
LEDGER_FILE = "raised.json"

# The trouble store's addressing rule, restated — the fold must find the row a clearance
# names, and what is on disk is the slug. The proof pins this against
# ``TroubleDevice.identity_of`` so the two cannot drift apart unseen.
_SLUG = re.compile(r"[^a-z0-9-]+")


def slug(identity: str) -> str:
    return _SLUG.sub("-", (identity or "").strip().lower()).strip("-")


# ---------------------------------------------------------------------------
# THE TRIPLE


def path_class(root: str, rel: str, rules: dict | None = None) -> str | None:
    """The class of a record path — the jurisdiction rule it matched, spelled as a path
    pattern: ``<root>/<under>`` for an ``under`` rule, ``<root>/**/<parent>`` for a
    ``parent`` rule, ``<root>/**/<name>`` for a name-only rule. ``None`` when no rule
    matches — the door journaled something its own jurisdiction does not name, which is a
    finding the table records under ``unclassed`` rather than a triple."""
    rules = door.jurisdiction()["roots"] if rules is None else rules
    p = Path(rel)
    for rule in rules.get(root, {}).get("records", []):
        if door._rule_matches(rule, p):
            if "under" in rule:
                return f"{root}/{rule['under']}"
            if "parent" in rule:
                return f"{root}/**/{rule['parent']}"
            return f"{root}/**/{rule['name']}"
    return None


def triple(pc: str, verb: str, cls: str) -> str:
    return f"{pc}|{verb}|{cls}"


def identity(pc: str, verb: str, cls: str) -> str:
    """The trouble identity for a triple — names the DEFECT (this triple was never seen), so
    its second occurrence folds onto the first."""
    return f"{IDENTITY_PREFIX}{pc}-{verb}-{cls}"


# ---------------------------------------------------------------------------
# THE FOLD


def ordered(journals: dict[str, list[dict]]) -> list[tuple[str, int, dict]]:
    """Every entry of every journal as ``(root, line, entry)`` in one order: by ``at``,
    ties by root name then line. Deterministic whatever order the roots were read in."""
    seq = [(root, i, e) for root, entries in journals.items() for i, e in enumerate(entries, 1)]
    seq.sort(key=lambda t: (str(t[2].get("at", "")), t[0], t[1]))
    return seq


def arming_index(seq: list[tuple[str, int, dict]]) -> int | None:
    """Position of the arming entry in the ordered stream, or None when the block is not
    armed (then nothing is judged and the whole corpus is prior)."""
    for i, (root, _line, e) in enumerate(seq):
        if root == ARMING_ROOT and e.get("path") == CHARTER_REL and e.get("verb") == ARMING_VERB:
            return i
    return None


def compile(journals: dict[str, list[dict]], rules: dict | None = None) -> dict:
    """The table, from the journals alone. Pure: same journals, same bytes.

    Returns ``{rows, raises, increments, post_appends, windows, unclassed, armed, compiled_to}``
    where ``rows`` maps triple → count, ``raises`` lists every post-arming zero-count entry
    with its disposition (``raised`` | ``cleared:akien`` | ``cleared:cc`` | ``cleared:<class>``),
    ``increments`` lists the akien clearances that added to a row, ``windows`` maps each
    WINDOW-sized post-arming append bucket to the raises inside it."""
    rules = door.jurisdiction()["roots"] if rules is None else rules
    seq = ordered(journals)
    armed = arming_index(seq)
    rows: dict[str, int] = {}
    raises: list[dict] = []
    increments: list[dict] = []
    unclassed: list[dict] = []
    slug_to_triple: dict[str, str] = {}
    post = 0
    windows: dict[str, int] = {}
    trouble_class = f"{TROUBLE_ROOT}/{TROUBLE_DIR}"
    for i, (root, line, e) in enumerate(seq):
        rel = str(e.get("path", ""))
        verb = str(e.get("verb", ""))
        cls = str((e.get("caller") or {}).get("class", "unknown"))
        pc = path_class(root, rel, rules)
        if pc is None:
            unclassed.append({"root": root, "line": line, "path": rel, "verb": verb, "caller_class": cls})
            continue
        key = triple(pc, verb, cls)
        slug_to_triple.setdefault(slug(identity(pc, verb, cls)), key)
        judged = armed is not None and i > armed
        # A clearance on a who-writes-what trouble teaches the row it names — by an akien
        # hand only. It is read BEFORE this entry's own triple is counted, so the clear's
        # own row (troubles|clear|akien) is judged like any other write.
        if pc == trouble_class and verb == "clear" and Path(rel).stem.startswith(IDENTITY_PREFIX):
            s = Path(rel).stem
            target = slug_to_triple.get(s)
            for r in raises:
                if r["identity_slug"] == s:
                    r["disposition"] = f"cleared:{cls}"
            if target is not None and cls == "akien":
                rows[target] = rows.get(target, 0) + 1
                increments.append({"root": root, "line": line, "at": e.get("at"), "triple": target,
                                   "count": rows[target]})
        if not judged:
            rows[key] = rows.get(key, 0) + 1
            continue
        post += 1
        if rows.get(key, 0) > 0:
            rows[key] += 1
            continue
        rows[key] = 0
        w = str(post // WINDOW)
        windows[w] = windows.get(w, 0) + 1
        raises.append({"root": root, "line": line, "at": e.get("at"), "path": rel, "verb": verb,
                       "caller_class": cls, "triple": key, "row": 0,
                       "identity": identity(pc, verb, cls),
                       "identity_slug": slug(identity(pc, verb, cls)),
                       "post_append": post, "disposition": "raised"})
    return {
        "rows": dict(sorted(rows.items())),
        "raises": raises,
        "increments": increments,
        "post_appends": post,
        "windows": windows,
        "unclassed": unclassed,
        "armed": None if armed is None else {"root": seq[armed][0], "line": seq[armed][1],
                                              "at": seq[armed][2].get("at")},
        "compiled_to": {root: len(entries) for root, entries in sorted(journals.items())},
    }


def render(table: dict) -> str:
    """The table's one spelling on disk — sorted keys, fixed indent, so byte-identity is a
    property of the fold and not of dict order."""
    return json.dumps(table, indent=1, sort_keys=True, ensure_ascii=False) + "\n"


def compression(table: dict) -> dict:
    """The first measurement: rows against entries. WRONG INTENT if they are equal."""
    entries = sum(table["compiled_to"].values())
    rows = len(table["rows"])
    return {"rows": rows, "entries": entries, "ratio": (entries / rows) if rows else None}


# ---------------------------------------------------------------------------
# THE BEAT


def table_dir() -> Path:
    """Instance-space, under the holder that runs the beat (Law 6: a machine's ongoing state
    berths under its holder, never in class-space)."""
    return instance_path("cairn", 0) / "machines" / COMPONENT


def read_journals(roots: dict[str, Path] | None = None) -> dict[str, list[dict]]:
    roots = door.roots() if roots is None else roots
    return {name: door.read_journal(Path(root)) for name, root in roots.items()}


def _load(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def _atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def pulse(roots: dict[str, Path] | None = None, raiser=None, where: Path | None = None,
          now=None) -> dict:
    """One beat: recompile the table from both journals, raise each NEW zero-count entry
    once through the inherited emission, write the table, the probe's acknowledgement and
    the ledger of what has been reported.

    ``roots`` (root name → dir) and ``where`` (the table directory) are injectable so a proof
    runs the whole beat over a world it owns; ``raiser`` is injectable so a proof can hand
    it a ``ModuleRaiser`` diverted to a scratch log home.

    THREE FILES, BECAUSE THEY ARE THREE THINGS. ``table.json`` is the pure fold and nothing
    else — delete it, recompile, byte-identical (clause 1). ``raised.json`` is the ledger of
    which journal lines have already been reported, keyed ``root:line``; it is not part of
    the table because a ledger of what was SAID is not a measurement of what IS. Delete the
    ledger and the next beat reports every raise again — onto the same identities, where the
    trouble device folds them as recurrences: loud, never silent (Law 7). ``probe_ack.json``
    lags one beat on purpose: the probe runs BEFORE the pulse modules on a beat, so it reads
    the previous beat's table against the previous beat's ack, and a raise fires the probe
    exactly once — on the beat after it was compiled. The first compile acks itself, so the
    prior seeds without firing."""
    where = table_dir() if where is None else Path(where)
    table = compile(read_journals(roots))
    prev = _load(where / TABLE_FILE)
    ledger = _load(where / LEDGER_FILE) or {"reported": []}
    seen = set(ledger.get("reported", []))
    new = [r for r in table["raises"] if f"{r['root']}:{r['line']}" not in seen]
    raiser = ModuleRaiser(COMPONENT) if raiser is None else raiser
    raised = []
    for r in new:
        rec = raiser.raise_trouble(
            r["identity"],
            why=(f"the artifact door journaled a write the table had never seen: "
                 f"{r['caller_class']} {r['verb']} on {r['triple'].split('|')[0]} "
                 f"({r['path']}) — row {r['triple']} was 0 after arming"),
            detail={"entry": {k: r[k] for k in ("root", "line", "at", "path", "verb", "caller_class")},
                    "row": {"triple": r["triple"], "count": 0}},
            now=now)
        raised.append({"identity": r["identity"], "poke": rec.get("poke"), "root": r["root"],
                       "line": r["line"]})
        seen.add(f"{r['root']}:{r['line']}")
    ack = ({"raises": len(prev["raises"]), "bucket": prev["post_appends"] // BUCKET}
           if prev else {"raises": len(table["raises"]), "bucket": table["post_appends"] // BUCKET})
    _atomic(where / TABLE_FILE, render(table))
    _atomic(where / LEDGER_FILE, json.dumps({"reported": sorted(seen)}, sort_keys=True) + "\n")
    _atomic(where / ACK_FILE, json.dumps(ack, sort_keys=True) + "\n")
    return {"table": str(where / TABLE_FILE), "compression": compression(table),
            "post_appends": table["post_appends"], "raised": raised, "ack": ack}
