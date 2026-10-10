"""codemother/deposit.py — landing a berthed chart packet in its tree, codemother's own act.

Moved here from skills/chart/live.py by ticket e8fe361a5b2f (RULE 1, 2026-10-01): writing
nodes into the chart trees through codemother's stage machines is codemother acting, so it
lives inside codemother and is reached over the bus — the ``deposit`` and ``drain`` verbs
on CodeMotherDevice (shim.py). The chart skill asks; it no longer holds her hands.

The bodies of deposit_verdict and drain_pending moved unchanged; the stage dispatch that
was inline in live.py's ``learn`` is deposit_berth. The embed seam asks inference_domain's
``resolve`` verb directly (its public interface) rather than borrowing librarian's code.
"""
from __future__ import annotations

import json
import os

from cairn.devices.codemother.machines.constrain.constrain import constrain_node_content, deposit_constrain
from cairn.devices.codemother.machines.decompose.decompose import decompose_node_content, deposit_decompose
from cairn.devices.codemother.machines.hypothesize.hypothesize import deposit_hypothesize, hypothesize_node_content
from cairn.devices.codemother.machines.orient.orient import deposit_orient
from cairn.devices.codemother.machines.survey.survey import deposit_survey, survey_node_content
from cairn.devices.codemother.machines.triage.triage import deposit_triage, triage_node_content
from cairn.devices.codemother.machines.validate.validate import deposit_validate, validate_node_content
from cairn.devices.codemother.machines.verdict.verdict import (VerdictRefused, mark_deposited, pending,
                                 validate_verdict, verdict_nexus,
                                 verdict_node_parts)
from cairn.tools.bus_client import reach
from cairn.tools.chain.grammar import CAIRN_ROOT
from cairn.tools.chain.verdict_contract import mark_failed
from cairn.tools.tree.tree import deposit_learning

EMBED_MODEL = "nomic-embed-text"
_SENDER = "codemother"


def _resolve_embed(bus, text: str) -> dict:
    reply = bus.request(sender=_SENDER, to="inference_domain", verb="resolve",
                        why="codemother deposit embed",
                        body={"kind": "embed", "prompt": text, "model": EMBED_MODEL,
                              "domain": "research"})
    return reply["body"]


def embed(bus):
    """text -> vector over inference_domain's resolve verb."""
    def _embed(text: str) -> list[float]:
        return _resolve_embed(bus, text)["answer"]["vector"]
    return _embed


def embed_metered(bus):
    """text -> {vector, tokens, hit}: the same request, keeping the host's own
    prompt_eval_count (None on a cache hit — not reported, never a guess)."""
    def _embed(text: str) -> dict:
        got = _resolve_embed(bus, text)
        counters = (got.get("provenance") or {}).get("counters") or {}
        return {"vector": got["answer"]["vector"],
                "tokens": counters.get("prompt_eval_count"),
                "hit": got.get("hit")}
    return _embed


def deposit_verdict(artifact: dict, embed, *, berth_path: str,
                    root: str = CAIRN_ROOT, nexus: str | None = None,
                    conn=None) -> dict:
    """The verdict face on the deposit door (ticket proved-answers-the-chart): the
    dispositions become the HYPOTHESIZE tree's memory of what killed which — the
    'one day' deposit_hypothesize's docstring has promised since the brick landed.

    Lives in codemother's deposit module (moved from skills/chart/live.py by ticket
    e8fe361a5b2f, body unchanged) and not in verdict.py by construction: verdict.py is the tree-free
    validator both the exit gate and this face compose (the fire path from the
    chokepoint may never reach tree machinery — a verdict is always hardware);
    the tree side of the split is this module's side. Gate before seed, like
    every face: the artifact re-validates at the ONE door, and the berth must
    exist on disk.

    PART BY PART since 2026-07-29 (ticket a-node-holds-one-claim). Takes the EMBED
    CALLABLE rather than a finished vector, because there is no longer one vector:
    each part is embedded and deposited on its own, and the content deposited is
    the very string that was embedded — the same object, never re-rendered between
    the two, so a vector can never describe bytes its node does not hold.

    THE HOST'S REFUSAL IS THE BOUND, and no length is measured anywhere in this
    path. The pre-flight this stone was cast to build turned out to be impossible:
    the host reports prompt_eval_count only in a SUCCESSFUL body, so nothing can
    ask "how many tokens is this" without doing the work. The refusal we already
    observe does the job better than a guess would — it fires exactly when it
    should, it is already loud, and it costs nothing. A part the host refuses
    raises; it is NEVER split further, summarised, or truncated to fit (a truncated
    part is a vector describing bytes the node does not hold — the permanent
    resident the provenance gate exists to refuse).

    A refusal mid-way therefore leaves EARLIER PARTS ALREADY LANDED, and that is
    safe by construction rather than by luck: no ``deposited`` record is written
    unless every part landed, so the berth stays pending and the next door read
    retries the whole verdict — where the already-landed parts dedupe on their
    content hash and the table does not grow. The duplicate path stops being
    incidental and becomes the retry's physics.

    THE NEXUS IS THE ARTIFACT'S TO NAME since 2026-07-30 (ticket
    watchme-emits-a-probe piece (d)). It used to default to the string
    ``"hypothesize"`` right here, which was correct for every verdict that answers
    a chart chain and wrong for the one this ticket built: a probe's verdict
    against its ticket's falsifier may belong in a different tree, and a device
    outside this toolchain has no reason to own a tree called hypothesize at all.
    An explicit ``nexus=`` still wins (the caller is closer to the truth than the
    file), then the artifact's own field, then the default — so an artifact that
    says nothing lands exactly where it always did.

    Returns ``{"node_ids", "parts", "duplicates", "tokens", "nexus"}``."""
    validate_verdict(artifact, root=root)
    nexus = nexus or verdict_nexus(artifact)
    if not isinstance(berth_path, str) or not os.path.isfile(os.path.expanduser(berth_path)):
        raise VerdictRefused(
            "deposit_verdict: berth %r does not exist on disk — a node whose "
            "provenance points at nothing is fabricated attribution one layer up"
            % (berth_path,))
    parts = verdict_node_parts(artifact)
    if not parts:
        raise VerdictRefused(
            "deposit_verdict: %r renders to no parts — a verdict that answers "
            "nothing has nothing to teach the tree" % (berth_path,))
    landed = []
    for i, (kind, content) in enumerate(parts):
        provenance = {
            "source": berth_path,
            "validate_ref": artifact["validate_ref"],
            "ticket": artifact["ticket"],
            "part": kind,
            "part_index": i,
            "part_count": len(parts),
        }
        got = embed(content)
        # The seam may be metered ({"vector", "tokens"}) or bare (a vector). Both
        # are honest; only the metered one can say what the ceiling really is.
        vector = got["vector"] if isinstance(got, dict) else got
        tokens = got.get("tokens") if isinstance(got, dict) else None
        node = deposit_learning(nexus, content, vector, provenance, conn=conn)
        landed.append({"part": kind, "part_index": i, "node_id": node["node_id"],
                       "duplicate": node.get("duplicate"), "tokens": tokens,
                       "chars": len(content)})
    return {
        "node_ids": [p["node_id"] for p in landed],
        "parts": landed,
        "duplicates": sum(1 for p in landed if p["duplicate"]),
        "tokens": [p["tokens"] for p in landed],
        "nexus": nexus,
    }


def drain_pending(*, root: str = CAIRN_ROOT, nexus: str | None = None,
                  embed=None, ledger_path: str | None = None, conn=None) -> list[dict]:
    """THE DRAIN (ticket the-deposit-rides-the-read, 2026-07-29): every verdict the
    emit chokepoint enqueued and nobody has deposited, landed through the ONE
    deposit door above — run by both door verbs BEFORE they serve.

    THE READ IS THE EVENT. Nothing polls and nothing schedules: the drain fires
    inside a door entry that was already happening, which is where the tree is
    already open and the db cost is already being paid (Law 1; 'reach for the
    event that already fires, never a clock'). The crossing side stayed tree-free
    so a netns-sealed crossing could enqueue identically — this is the other half,
    on the tree side, where the db is allowed.

    Law 7 at this exact seam: a deposit that raises leaves its ENQUEUED line
    standing (the record of truth keeps the obligation) and rides back named in
    the result (the presentation surface says so loudly) — and the verb still
    serves. A landing appends a ``deposited`` record, which is also the whole
    idempotence story: the second drain finds nothing pending, so no berth is ever
    deposited twice, and no line was ever edited to make that true.

    PART BY PART since 2026-07-29 (ticket a-node-holds-one-claim): the drain hands
    the deposit door the EMBED SEAM rather than one finished vector, because a
    verdict lands as many nodes and each is embedded on its own. The seam defaults
    to the METERED one, so an ordinary drain reports what each part actually cost
    in host tokens — the number that makes the embed ceiling a measured fact
    instead of an operator's rule of thumb.

    The Law 7 story above is unchanged and now covers a PARTIAL landing too: if the
    host refuses part 6 of 8, five nodes are already in the tree, no ``deposited``
    record is written, the berth stays pending and says so loudly — and the next
    door read re-deposits the whole verdict, where the five already-landed parts
    dedupe on content hash. Retry is idempotent by the tree's own physics, not by
    bookkeeping.

    Returns one entry per pending berth: ``{"berth", "deposited"|"failed", ...}``.
    """
    embed = embed or embed_metered(reach("inference_domain"))
    drained = []
    for entry in pending(ledger_path=ledger_path):
        berth = entry["berth"]
        try:
            with open(os.path.expanduser(berth), encoding="utf-8") as fh:
                artifact = json.load(fh)
            got = deposit_verdict(artifact, embed, berth_path=berth, root=root,
                                  nexus=nexus, conn=conn)
            mark_deposited(berth, got["node_ids"], ledger_path=ledger_path)
            # The RESOLVED nexus, not the argument — the drain reports where each
            # berth actually landed, and with the artifact now able to name its own
            # tree, one drain can land two berths in two different ones.
            drained.append({"berth": berth, "deposited": got["node_ids"],
                            "parts": got["parts"], "duplicates": got["duplicates"],
                            "tokens": got["tokens"], "nexus": got["nexus"]})
        except Exception as e:  # noqa: BLE001 — deliberate: the door must still serve
            # THE FAILURE IS A RECORD (ticket 637d206be821): the line is rendered ONCE,
            # here, written to the ledger and carried back for the printer — two
            # renderings drift. A ledger that cannot take the record does not stop the
            # drain; the entry says so instead (the door must still serve).
            failed = "%s: %s" % (type(e).__name__, e)
            line = "DEPOSIT FAILED — %s STANDS PENDING on the ledger: %s" % (berth, failed)
            out = {"berth": berth, "failed": failed, "still_pending": True,
                   "stderr": line, "result_code": type(e).__name__}
            try:
                mark_failed(berth, stderr=line, result_code=type(e).__name__,
                            ticket=entry.get("ticket"), ledger_path=ledger_path)
            except Exception as w:  # noqa: BLE001 — named in the entry, never swallowed
                out["ledger_write_failed"] = "%s: %s" % (type(w).__name__, w)
            drained.append(out)
    return drained


def deposit_berth(berth: str, *, nexus: str | None = None, embed, embed_metered) -> dict:
    """Land one berthed packet in the tree its stage names — the dispatch live.py's
    ``learn`` ran inline until ticket e8fe361a5b2f, unchanged. ``embed`` is text ->
    vector and ``embed_metered`` text -> {vector, tokens}; ``nexus`` is honoured
    where it always was (an orient packet) and the stage's own tree everywhere else.
    Returns ``{"learn", "berth", "nexus"}``."""
    with open(berth, encoding="utf-8") as fh:
        packet = json.load(fh)
    if os.path.basename(berth).startswith("constrain-"):
        # Stage 2's deposit-back: the vector embeds the SAME rendering the node
        # deposits (constrain_node_content — one rendering, no drift).
        nexus = "constrain"
        got = deposit_constrain(packet, embed(constrain_node_content(packet)),
                                berth_path=berth)
    elif os.path.basename(berth).startswith("survey-"):
        nexus = "survey"
        got = deposit_survey(packet, embed(survey_node_content(packet)),
                             berth_path=berth)
    elif os.path.basename(berth).startswith("decompose-"):
        nexus = "decompose"
        got = deposit_decompose(packet, embed(decompose_node_content(packet)),
                                berth_path=berth)
    elif os.path.basename(berth).startswith("triage-"):
        nexus = "triage"
        got = deposit_triage(packet, embed(triage_node_content(packet)),
                             berth_path=berth)
    elif os.path.basename(berth).startswith("hypothesize-"):
        nexus = "hypothesize"
        got = deposit_hypothesize(packet,
                                  embed(hypothesize_node_content(packet)),
                                  berth_path=berth)
    elif os.path.basename(berth).startswith("validate-"):
        nexus = "validate"
        got = deposit_validate(packet,
                               embed(validate_node_content(packet)),
                               berth_path=berth)
    elif os.path.basename(berth).startswith("verdict-"):
        # The exit gate's write-back: what killed which lands in the tree the
        # ARTIFACT names (default hypothesize — the loop the brick promised), as
        # ONE NODE PER CLAIM since 2026-07-29, so the metered seam goes in whole
        # rather than a finished vector, and the berth's landing is the list of
        # ids it became. This branch is the only one that does not hardwire its
        # nexus, because it is the only one whose berth is not a chart stage.
        got = deposit_verdict(packet, embed_metered, berth_path=berth)
        nexus = got["nexus"]
    else:
        nexus = nexus or "orient"
        got = deposit_orient(packet, embed(packet["intent"]),
                             berth_path=berth, nexus=nexus)
    return {"learn": got, "berth": berth, "nexus": nexus}
