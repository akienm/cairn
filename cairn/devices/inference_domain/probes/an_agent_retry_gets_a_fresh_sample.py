"""PROBE — does a tool-using conversation actually get FRESH samples over live traffic?

Berth for the WATCHME that ticket ``548dd13fb4db`` carries. Berthed beside
``cairn/devices/inference_domain`` because that is WHAT IT WATCHES.

THE INTENTION BEING WATCHED, and it is not "does the code work". The proofs settle, in a
fixture world, that a resolver built with ``host.EXPIRED`` re-resolves a byte-identical repeat.
What a fixture cannot settle is whether the agent lane is USED — whether the caller that ends
up driving a tool-using conversation was actually built with that horizon. That is a fact about
live traffic and about a shim nobody has written yet, and it is precisely the shape this system
has been caught by before: a sealed door with green proofs, routed around by six voyages in two
days.

WHY A CACHE HIT ON A TOOL-CARRYING CALL IS THE FINDING. An agent re-asks a byte-identical
question ON PURPOSE — turn N+1 is turn N plus the tool result, and a stalled loop re-sends a
prefix it has already sent. Serving that from the store is not a saved call, it is a HANG: the
agent gets back the identical ``tool_calls``, runs the identical tool, appends the identical
result, and asks again forever. So the defect does not look like an error anywhere. It looks
like a cheap, fast, well-cached agent that never finishes — which is exactly the kind of green
Law 8 says is worse than a red, because a peer leans on it.

THE FINDING (trigger): a post-era row with ``verdict='hit'`` whose canonical carries a toolset.
One is enough. There is no rate to be patient about — a tool-carrying call is either in the
agent lane or it is not, and a single hit means some caller built its resolver without the
horizon and is at risk of the loop above.

WHAT WOULD MAKE THIS PROBE LIE, named rather than left as an absence. It reads the toolset off
the CANONICAL TEXT (the request as canonicalize() froze it), so it sees exactly what the cache
keyed on and cannot be fooled by a request that carried tools somewhere the key never saw. It
cannot, however, see a caller that sends an agent conversation with NO ``tools`` key at all —
a model that has been told about its tools in the system prompt instead. That caller would hang
the same way and this probe would read green over it. It is a real gap, it is not closable from
the store alone (nothing in the row says "this was an agent"), and it is written here so the
next reader does not have to re-derive it.

THE ERA FLOOR is the moment the toolset could first cross this door: before this build the chat
branch sent no ``tools`` key at all, so no pre-era row can carry one and counting them would be
counting an impossibility.
"""

from __future__ import annotations

from datetime import datetime

from cairn.tools.base.probe import Probe, owning_ticket, once

_OWNING_TICKET = "548dd13fb4db"

# The moment the chat branch learned to carry a toolset (this ticket's build).
_ERA = datetime.fromisoformat("2026-09-11T00:00:00-06:00")

# The sample size below which the question cannot be answered. A store with no agent traffic
# disagrees with nothing and would otherwise CLEAR AT ZERO — a watch that can clear before it
# can fire is not a watch. Hand-set, and therefore a learns-its-gates IOU named at birth.
#
# IT IS THE TICKET'S NUMBER, NOT THE PROBE'S. The watchme spec on 548dd13fb4db says "when 50
# agent-door calls have landed"; this file first carried 20, which would have let the watch
# clear at less than half the evidence its own ticket demanded — a probe quietly grading
# itself easier than the spec it was compiled from. Raised to match. If 50 turns out to be
# the wrong floor, the number moves in the TICKET first and follows here, never the reverse.
_ENOUGH = 50


def _post_era_row(row: dict) -> bool:
    created = row.get("created")
    if created is None:
        return False
    if isinstance(created, str):
        try:
            created = datetime.fromisoformat(created)
        except ValueError:
            return False
    if created.tzinfo is None:
        created = created.replace(tzinfo=_ERA.tzinfo)
    return created >= _ERA


def _carries_a_toolset(row: dict) -> bool:
    """Read off the CANONICAL TEXT — the request exactly as the cache keyed it.

    ``canonicalize`` emits compact JSON with sorted keys and no spaces, so a top-level toolset
    is always the literal ``"tools":[``. Matching that rather than the bare word keeps a user
    who merely mentions tools in their prompt out of the count.
    """
    return '"tools":[' in str(row.get("canonical") or "")


def judge(rows: list[dict]) -> dict:
    """The deterministic read. Separated from the live fetch so a proof can hand it fixtures."""
    post = [r for r in rows if _post_era_row(r)]
    tool_rows = [r for r in post if _carries_a_toolset(r)]
    hits = [r for r in tool_rows if r.get("verdict") == "hit"]
    misses = [r for r in tool_rows if r.get("verdict") == "miss"]
    return {
        "era": _ERA.isoformat(),
        "post_era_rows": len(post),
        "tool_carrying_calls": len(tool_rows),
        "tool_carrying_misses": len(misses),
        "tool_carrying_hits": len(hits),
        # The finding itself: which questions were REPLAYED to an agent.
        "replayed_to_an_agent": sorted(
            {str(r.get("canonical"))[:200] for r in hits}
        ),
    }


def survey_the_corpus() -> dict:
    """The live read: the store through its one door.

    A DB this probe cannot reach RAISES rather than reporting a clean zero — a silent 0/0 reads
    as both "no finding" and "not yet enough", and those are different states (Law 7).
    """
    from cairn.devices.db_domain import store            # late: imports clean without a DB

    return judge(store.read("inference_calls"))


def _corpus(context: dict) -> dict:
    return once(context, "corpus", survey_the_corpus)


def _trigger(now, context: dict) -> bool:
    """TRUE on the FIRST tool-carrying cache hit. One is the finding — see the module note: a
    replayed tool_call is how the loop hangs, and it never surfaces as an error."""
    return bool(_corpus(context)["tool_carrying_hits"])


def _enough(context: dict) -> bool:
    """CLEARED once enough real agent traffic has crossed to judge AND none of it was replayed.

    The floor is the non-vacuity tooth and it is doing real work here: with no agent traffic at
    all this would clear immediately, certifying a lane nobody has used yet."""
    s = _corpus(context)
    return s["tool_carrying_misses"] >= _ENOUGH and not s["tool_carrying_hits"]


def _carry(context: dict) -> dict:
    s = _corpus(context)
    if s["tool_carrying_hits"]:
        finding = (
            f"{s['tool_carrying_hits']} tool-carrying call(s) were SERVED FROM THE STORE. An "
            f"agent that re-asks a question and gets the identical tool_calls back runs the "
            f"identical tool and asks again — this is the hang, and it reports no error. Some "
            f"caller built its resolver without horizon=host.EXPIRED."
        )
    elif s["tool_carrying_misses"] < _ENOUGH:
        finding = (
            f"not yet judgeable: {s['tool_carrying_misses']} tool-carrying call(s) against a "
            f"floor of {_ENOUGH}. The agent lane has not been used enough to certify."
        )
    else:
        finding = (
            f"{s['tool_carrying_misses']} tool-carrying calls, none replayed — the agent lane "
            f"is re-resolving as intended."
        )
    return {"finding": finding, **s, "owning_ticket": owning_ticket(_OWNING_TICKET)}


_HORIZON = 1000

PROBE = Probe(
    why="the proofs settle in a fixture world that an EXPIRED horizon re-resolves; what they "
        "cannot settle is whether the caller driving a real tool-using conversation was built "
        "with it, and a cache hit there is a silent infinite loop rather than an error",
    trigger=_trigger,
    to="inference_domain",
    body={"nexus": "hypothesize", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=_HORIZON,
)
