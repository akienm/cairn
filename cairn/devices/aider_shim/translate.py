"""The chart chain -> aider's inputs. Every span of the prompt carries where it came from.

WHAT THIS SOLVES IS FALSIFIER CLAUSE (7): "a prompt handed to aider contains anything not
traceable to a berthed packet field — the chain stopped being the input and the
conversation started being it." That clause is easy to write and almost impossible to
check after the fact: a finished prompt string is a flat wall of text, and 'does this
sentence come from a berth?' has to be re-litigated for every sentence, by a reader who
was not there. So the prompt is not built as a string. It is built as a list of
:class:`Span`, each carrying its ORIGIN, and the string is a derived view of them. A span
is one of exactly two kinds:

  * ``berth`` — the text came from a field in a berthed chart packet, and the span names
    the berth path and the field path. The check re-opens the berth and looks.
  * ``scaffold`` — connective tissue ("Build exactly this:"), drawn from :data:`SCAFFOLD`,
    a frozen table in this module. A scaffold span whose text is not in that table fails
    the check.

Between them there is no third door, which is the point: for a conversational sentence to
reach aider, someone would have to add it to a frozen module-level table in a committed
file. That is not impossible — nothing is — but it is no longer something that can happen
by accident at 2am, and it leaves a diff.

ONE DECOMPOSE PIECE PER INVOCATION, settled at decompose after being carried openly from
orient. The shim is a single-shot function from (chain, piece index) to a brief; the
caller drives the loop in the order triage already ranked. The three grounds are in the
charter's filed edge (c); the operative one is that triage ALREADY produces the order, so
a whole-ticket shim would re-derive a sequencing the chain has settled — Law 1's defect,
committed by the very device built to serve Law 1.

WHAT IS DELIBERATELY NOT HERE: this module builds a brief and touches nothing. It does not
construct a Coder, does not import aider, and does not run anything. That is what lets its
proof be a sealed proof — it reads berths and returns data — and it is also the honest
seam, because the thing that RUNS aider needs a venv, a repo and a live host, and the thing
that decides WHAT TO SAY needs none of the three.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from cairn.devices.builder.machines.verdict.verdict import chain_for_ticket

#: Class-space root. Holdings addressed relative to it resolve here; holdings OUTSIDE it
#: are read-only to aider, because constrain's `out` says so.
REPO = Path(__file__).resolve().parents[3]

#: EVERY non-berth string that may appear in a prompt. Frozen, and the check enforces it.
#: Keep these instructional and content-free: the moment one of them starts carrying a fact
#: about the work, the fact has entered the prompt without a berth behind it.
SCAFFOLD = {
    "header": "You are implementing ONE piece of a task that has already been analysed. "
              "The analysis below is settled — do not redesign it, and do not widen it.",
    "piece": "THE PIECE TO BUILD — this and nothing else:",
    "why": "WHY THIS PIECE EXISTS:",
    "kind_build": "This piece BUILDS something measured absent. It fills:",
    "kind_compose": "This piece COMPOSES things that already exist. It uses:",
    "bounds_in": "IN BOUNDS:",
    "bounds_out": "OUT OF BOUNDS — do not touch these, do not work around them, and if the "
                  "piece seems to require one, stop and say so instead:",
    "constraints": "CONSTRAINTS THAT BIND THIS WORK:",
    "holdings": "THESE ALREADY EXIST. Use them; do not rebuild them:",
    "intent": "WHAT THE WHOLE TASK IS FOR (context only — build the piece, not the task):",
    # Content-free ON PURPOSE — it does not name the command. The command itself rides
    # Brief.test_cmd and reaches aider as its test_cmd argument, which is where a command
    # belongs; naming it here would put a caller-supplied string into the one place this
    # design refuses to have one, and would break the two-kinds invariant to do it.
    "proof": "Your work is judged by a test command that runs automatically after each "
             "edit. It must pass, and it was not written to be easy to pass.",
    "critique": "Before you begin: if anything in this brief is unclear, contradictory, "
                "or missing information you need, say what SPECIFICALLY is wrong. Your "
                "assessment is recorded and inspectable after the fact.",
    "close": "Make the smallest change that does the piece. If something needed is "
             "missing, say what and stop — do not invent it.",
}


@dataclass(frozen=True)
class Span:
    """One piece of the prompt, and where it came from. ``kind`` is 'berth' or 'scaffold'."""

    text: str
    kind: str
    berth: str = ""        # path to the berthed packet, for kind='berth'
    field: str = ""        # dotted/indexed path within it, e.g. "order.2.what"
    key: str = ""          # the SCAFFOLD key, for kind='scaffold'


@dataclass
class Brief:
    """What aider is handed for one piece. A brief is data; running it is someone else's."""

    ticket: str
    piece_index: int
    spans: list[Span] = field(default_factory=list)
    files: list[str] = field(default_factory=list)       # aider's fnames — editable
    read_only: list[str] = field(default_factory=list)   # aider's read_only_fnames
    skipped: list[dict] = field(default_factory=list)    # holdings that reached neither
    test_cmd: str = ""
    chain: dict = field(default_factory=dict)

    #: aider's ``map_tokens``, and ZERO IS THE DESIGN, not a performance setting. aider's
    #: repo map walks the whole repository and splices a ranked digest of it into the
    #: prompt — content that traces to no berthed packet field, assembled by the held
    #: program after this module has finished counting spans. ``unsourced()`` would still
    #: return empty and clause (7) would still be violated, because the violation happens
    #: downstream of the only thing that can see it. It is also Law 1 twice over: the
    #: chart chain already settled which files this piece touches (survey's holdings,
    #: constrain's bounds), so a repo map is aider re-deriving the settled by heuristic.
    #: MEASURED, not reasoned: the first live fire died in ``repomap.get_ranked_tags`` on
    #: ``import networkx`` — a module the venv's closure correctly measured as lazy-only
    #: and therefore never installed. The traceback is what surfaced the prompt hole.
    map_tokens: int = 0

    @property
    def prompt(self) -> str:
        return "\n\n".join(s.text for s in self.spans if s.text)

    def unsourced(self) -> list[Span]:
        """Spans that cannot be traced. THE INSTRUMENT FOR FALSIFIER CLAUSE (7).

        Re-opens each berth and looks the value up rather than trusting the span's own
        claim about itself — a span that says where it came from and is not checked is a
        self-report, which is the thing this whole design is built against.
        """
        bad = []
        for s in self.spans:
            if s.kind == "scaffold":
                if SCAFFOLD.get(s.key) != s.text:
                    bad.append(s)
            elif s.kind == "berth":
                if not _contains(s.text, _lookup(s.berth, s.field)):
                    bad.append(s)
            else:
                bad.append(s)
        return bad


def _contains(text: str, value) -> bool:
    """Is every atom of the berthed value still present, verbatim, in the span's text?

    SHAPE-AWARE ON PURPOSE. A render may add bullets and wrap; it may not DROP or REWORD,
    and a list rendered as bullets has no single string to look for — checking
    ``str(list) in text`` would fail every list and pass nothing meaningful. So a list is
    checked element by element, which is the check that actually bites: drop one bound
    from ``bounds.out`` and this goes red, which is precisely the summarisation that
    clause (7) is about.
    """
    if value is None:
        return False
    if isinstance(value, (list, tuple)):
        return bool(value) and all(_contains(text, v) for v in value)
    return str(value) in text


def _lookup(berth: str, dotted: str):
    """Read a field out of a berthed packet by dotted path, integers indexing lists."""
    try:
        cur = json.loads(Path(berth).read_text(encoding="utf-8"))
    except Exception:
        return None
    for part in dotted.split("."):
        try:
            cur = cur[int(part)] if part.isdigit() else cur[part]
        except Exception:
            return None
    return cur


def _scaffold(key: str) -> Span:
    return Span(text=SCAFFOLD[key], kind="scaffold", key=key)


def _berth(berth: str, dotted: str, render=None) -> Span | None:
    """A span whose text is derived from a berth field. Returns None if the field is absent.

    ``render`` may reshape the value for reading (bullets, joins) but the raw value must
    remain a substring of the result — that containment is what :meth:`Brief.unsourced`
    checks, and it is why a render that SUMMARISES would be caught rather than trusted.
    """
    value = _lookup(berth, dotted)
    if value is None:
        return None
    text = render(value) if render else str(value)
    return Span(text=text, kind="berth", berth=berth, field=dotted)


def _bullets(values) -> str:
    if isinstance(values, str):
        return f"  - {values}"
    return "\n".join(f"  - {v}" for v in values)


def brief(ticket: str, piece_index: int, *, test_cmd: str = "",
          berths_root=None) -> Brief:
    """Build the brief for ONE piece of a cast ticket's berthed chain.

    Raises ValueError with a specific reason rather than producing a thin brief: a brief
    assembled from a broken chain is worse than no brief, because it looks like one.

    ``berths_root`` is threaded straight through to :func:`chain_for_ticket`, and it is
    what lets this module's proof be a SEALED one. The standing chain lives in
    instance-space (``~/.cairn/devices/chart/0/packets/``); a sealed proof may never read
    there, and a proof that read the live chain would also be asserting over a snapshot
    that changes every time anything charts. So the teeth run over fixture berths under
    the test's own tmp_path, and the real chain is exercised by the live fire instead —
    which is the correct division: the proof pins the contract, the live fire meets the
    world.
    """
    chain = chain_for_ticket(ticket, berths_root=berths_root)
    standing = {k: v for k, v in chain.items() if v}
    for needed in ("orient", "constrain", "survey", "decompose", "triage"):
        if not standing.get(needed):
            raise ValueError(
                f"no standing {needed} berth for ticket {ticket!r} — the chain is the "
                f"input, and this link is missing. Standing: {sorted(standing)}"
            )

    o, c, s, d, t = (standing["orient"], standing["constrain"], standing["survey"],
                     standing["decompose"], standing["triage"])

    # THE ORDER IS TRIAGE'S, NOT OURS. piece_index indexes the RANKED order, and the piece
    # it names is then found in the decompose split by its `what`. Indexing decompose
    # directly would silently ignore the ranking the chain spent a whole stage producing.
    order = _lookup(t, "order") or []
    if not 0 <= piece_index < len(order):
        raise ValueError(f"piece {piece_index} is outside the triage order (0..{len(order)-1})")
    ranked_what = order[piece_index]["what"]
    pieces = _lookup(d, "sub_problems") or []
    matches = [i for i, p in enumerate(pieces) if p.get("what") == ranked_what]
    if len(matches) != 1:
        raise ValueError(
            f"the ranked piece matches {len(matches)} entries in the decompose split — "
            "the triage order and the split have drifted, and no brief can be honest "
            "about which piece it means"
        )
    di = matches[0]
    piece = pieces[di]

    spans = [_scaffold("header")]

    intent = _berth(o, "intent")
    if intent:
        spans += [_scaffold("intent"), intent]

    spans += [_scaffold("piece"), _berth(d, f"sub_problems.{di}.what"),
              _scaffold("why"), _berth(d, f"sub_problems.{di}.why")]

    if piece.get("kind") == "build" and piece.get("fills"):
        spans += [_scaffold("kind_build"), _berth(d, f"sub_problems.{di}.fills", _bullets)]
    elif piece.get("kind") == "compose" and piece.get("uses"):
        spans += [_scaffold("kind_compose"), _berth(d, f"sub_problems.{di}.uses", _bullets)]

    bounds_in = _berth(c, "bounds.in", _bullets)
    if bounds_in:
        spans += [_scaffold("bounds_in"), bounds_in]
    bounds_out = _berth(c, "bounds.out", _bullets)
    if bounds_out:
        spans += [_scaffold("bounds_out"), bounds_out]

    constraints = _lookup(c, "constraints") or []
    if constraints:
        spans.append(_scaffold("constraints"))
        for i, _ in enumerate(constraints):
            span = _berth(c, f"constraints.{i}.text", lambda v: f"  - {v}")
            if span:
                spans.append(span)

    holdings = _lookup(s, "holdings") or []
    if holdings:
        spans.append(_scaffold("holdings"))
        for i, _ in enumerate(holdings):
            span = _berth(s, f"holdings.{i}.what",
                          lambda v, i=i: f"  - {v}  [{(holdings[i] or {}).get('address','')}]")
            if span:
                spans.append(span)

    if test_cmd:
        spans.append(_scaffold("proof"))

    spans.append(_scaffold("critique"))
    spans.append(_scaffold("close"))

    uses = piece.get("uses") or []
    if not uses:
        raise ValueError(
            f"piece {piece_index} of {ticket!r} declares no `uses`, so nothing berthed says "
            "which files it READS. Handing it the whole survey instead is what this "
            "function used to do, and it is what made every piece's brief identical and "
            "over the model's window. Measured 2026-08-17 across 51 decompose berths: 1 "
            "piece in 321 lacks `uses`, so this is a real state and a rare one — the fix "
            "is upstream, in the split, not a fallback here."
        )
    writes_to = piece.get("writes_to") or []
    if not writes_to:
        raise ValueError(
            f"piece {piece_index} of {ticket!r} declares no `writes_to`, so nothing berthed "
            "says where its output LANDS, and the editable file list would have to be "
            "guessed from the piece's prose — which is exactly what handed the apprentice "
            "the file it READS at the first live drive (2026-08-17). `uses` cannot stand in: "
            "it names survey HOLDINGS, things that exist, and a build piece's whole job is "
            "to create what a measured absence says is missing. THE BERTH IS STALE — it "
            f"predates the field: {d}. Re-chart the ticket (`/chart {ticket}`) so its "
            "decompose berth carries the field the door now requires."
        )
    editable, read_only, skipped = _files(uses, writes_to, holdings)
    return Brief(ticket=ticket, piece_index=piece_index,
                 spans=[s for s in spans if s is not None],
                 files=editable, read_only=read_only, skipped=skipped,
                 test_cmd=test_cmd, chain=standing)


def _files(uses, writes_to, holdings) -> tuple[list[str], list[str], list[dict]]:
    """THE PIECE'S declared addresses, sorted into what aider may EDIT and what it may READ.

    EDITABLE COMES FROM ``writes_to``, READ-ONLY FROM ``uses``, and the asymmetry is the
    whole ticket (a-piece-names-where-its-output-lands, 2026-08-17). ``uses`` names survey
    HOLDINGS — things the sweep FOUND, i.e. things that EXIST — and a build piece's whole
    job is to create what a measured absence says is missing, so its target is excluded
    from ``uses`` by construction. Handing ``uses`` over as editable was therefore looser
    and wronger at once: looser because a file the piece merely reads was open for
    writing, wronger because the file the piece was actually there to write was in no
    list at all. MEASURED at the first live drive that landed an applied edit: the brief
    handed the apprentice ``venv.py`` — a holding the piece names in ``uses`` — and the
    piece's job was to create a new verb. It built the wrong thing in the wrong place,
    and both halves trace here.

    A ``writes_to`` THAT DOES NOT EXIST PASSES THROUGH AS EDITABLE. That is the subtle
    half and it is not an oversight: a build piece names the file it is about to create,
    so reporting it ``skipped`` — the treatment a non-resolving ``uses`` gets, correctly,
    because a holding that isn't there is a finding about the survey — would reproduce
    this ticket's exact defect at the exact function that fixes it. aider is given the
    path and creates it.

    THE SELECTION IS DECOMPOSE'S, AND IT USED TO BE NOBODY'S. Until 2026-08-17 this
    function took the whole survey and handed every holding to aider, so every piece of a
    ticket got a byte-identical file list and the piece's own ``uses`` — a berthed field
    the decompose gate already refuses to leave unresolvable — was read into the prompt
    as prose and then ignored where it decides something. That is Law 1 at the last hop:
    the chain spent a stage settling which holdings each piece composes, and this module
    re-derived "all of them". MEASURED, and it is why the falsifier's middle arm never
    landed: all 8 pieces of `aider-builds-a-piece` weighed ~74,090 tokens against a
    send budget of 73,728, because 129,155 chars of aider's own source rode along for
    pieces that never named it. Selecting by ``uses``, the same pieces weigh 6.8k–41k.

    THE SHORTER LIST IS NOT A QUIET DROP, and the distinction matters because the old
    docstring here argued the opposite case correctly. Every holding the survey found is
    still IN THE PROMPT, by name and address, under the "THESE ALREADY EXIST" scaffold —
    what narrows is only which of them aider is handed as open files. A survey finding
    going missing would be invisible; this one is written down two spans above the file
    list.

    THE EDIT/READ SPLIT IS CONSTRAIN'S, NOT A CONVENIENCE. Several holdings in a real
    chain sit outside this repo — the held foreign program's own modules are holdings,
    because the survey legitimately found them and downstream legitimately needs to see
    them. Handing those to aider as editable files would invite exactly the edit
    constrain puts out of bounds ("modifying ~/dev/src/aider itself"), and it would
    invite it silently, by putting them in the same list as everything else. aider has a
    real distinction for this — ``fnames`` vs ``read_only_fnames`` — so the bound is
    expressed in the foreign program's own vocabulary rather than in a hope that the
    model reads the prompt.

    A declared use that resolves to nothing, or to a directory, is REPORTED rather than
    dropped: the piece named it, so its absence is a finding about the split, and Law 7
    says a diagnostic surface is loud. The same holds for a ``writes_to`` this function
    cannot honour — a directory, or an address outside this repo — with the difference
    that non-existence is not one of those cases.
    """
    editable, read_only, skipped = [], [], []
    for addr in writes_to:
        if not isinstance(addr, str) or not addr.strip():
            skipped.append({"address": addr, "why": "declared as an output address, "
                                                    "but not a usable path"})
            continue
        p = Path(addr)
        p = p if p.is_absolute() else REPO / addr
        if REPO not in p.resolve().parents and p.resolve() != REPO:
            # The decompose door already refuses this and the promotion judge reds it;
            # a berth that predates both can still carry one, and an out-of-repo output
            # handed over as editable is a write this system does not gate (Law 6).
            skipped.append({"address": addr, "why": "an output address outside this "
                                                    "repo — not opened for editing"})
        elif p.is_dir():
            skipped.append({"address": addr, "why": "a directory, not a file"})
        else:
            # NOT gated on existence. See the docstring: the piece is here to create it.
            editable.append(str(p.resolve()))

    known = {h.get("address") for h in holdings if isinstance(h, dict)}
    for addr in uses:
        if not isinstance(addr, str) or not addr:
            continue
        if addr not in known:
            skipped.append({"address": addr, "why": "declared by the piece, not in the "
                                                    "survey's holdings"})
            continue
        p = Path(addr)
        p = p if p.is_absolute() else REPO / addr
        if not p.exists():
            skipped.append({"address": addr, "why": "does not resolve"})
        elif p.is_dir():
            skipped.append({"address": addr, "why": "a directory, not a file"})
        else:
            read_only.append(str(p.resolve()))
    # A piece may legitimately both read and write one file. It goes in the editable
    # list only — aider's own contract: a path in both `fnames` and `read_only_fnames`
    # is a contradiction, and the piece's DECLARED OUTPUT is the stronger claim.
    editable = sorted(set(editable))
    return editable, sorted(set(read_only) - set(editable)), skipped
