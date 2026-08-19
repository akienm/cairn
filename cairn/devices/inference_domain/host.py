"""inference_domain/host.py — THE ONE PLACE THAT OPENS THE INFERENCE HOST.

The domain's ``resolve(request, resolver=...)`` takes the host client as an injected seam. This
module is that seam filled in: an ollama-backed ``resolver`` callable, living HERE and nowhere
else (charter filed edge (b); CLAUDE.md's "the inference host is reached only through
inference_domain"). Sole path is PHYSICS at two moments now, one rule both times: proof-time,
the repo-wide import-sieve mesh in ``proofs/test_host.py``; build-time, the ``sole_path_holds``
sieve in build_inspector's roster (ruling 2026-08-08, item 1: "THAT NEEDS TO BE IN THE BUILD
INSPECTION"). The subprocess/dynamic-import residue stays a named IOU in CLAUDE.md.

Why it exists: ``yield_report()`` is the measuring instrument for Telos 1 — tokens SPENT on
misses against tokens AVOIDED by hits. Until now it metered a stub resolver, so the compile-once
claim was arithmetic over invented numbers. With a real host behind it the yield is a MEASURED
fact (Law 3), which is the whole difference between demonstrating inference compilation and
asserting it.

TWO THINGS MEASURED AGAINST THE LIVE HOST, 2026-07-26 (both changed the design):

  1. ``/api/embeddings`` (the older endpoint) RETURNS ONLY THE VECTOR — no token counters at
     all. Resolving through it would have handed the meter a cost of 0 on every call, and
     ``yield_report`` would have reported a perfectly consistent, perfectly meaningless
     0-spent/0-avoided. That is the stub problem again wearing the clothes of a real host, and
     it would have been INVISIBLE — the shape is right, only the numbers are hollow (Law 8).
     So this module uses ``/api/embed``, which reports ``prompt_eval_count``, and REFUSES LOUDLY
     (``HostUnmetered``) if a response carries no counter. An unmetered answer is not cheaper
     than no answer; it is a lie about the thesis. Law 7 — loud at the diagnostic surface.
  2. The counters ollama actually reports are ``prompt_eval_count`` (input) and ``eval_count``
     (output); embed reports the first only. ``cost`` is their sum — real tokens, not a proxy.

HORIZON AND FALSIFIER. A time horizon on a temperature-0 completion is superstition: nothing
about the answer rots as the clock moves. What DOES invalidate it is the model changing under
us. So the horizon is left empty (no expiry, the domain's documented '' case) and the falsifier
carries the model's DIGEST in a mechanically-checkable form — ``model_digest == sha256:...``,
answerable by one ``/api/tags`` read. Charter edge (c) says VERIFY checks the horizon only and
the falsifier is carried for T1.4; this makes that edge cheap to close later instead of leaving
prose in the column. Sampling is pinned to temperature 0 by default for the same reason: caching
a nondeterministic call quietly changes what the cache MEANS (a stand-in for a fresh call
becomes a stand-in for one particular roll), and the request's options are canonicalized with
it, so a caller who wants sampling gets a different question, not a corrupted answer.

Dependency-light on purpose: stdlib ``urllib`` only, no client library, and the HTTP call is
itself an injected ``transport`` so the code-seam proofs run with no host present.

    python3 cairn/devices/inference_domain/proofs/test_host.py     # exit 0 = green (no host needed)
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

# The second host appeared (Hex, 2026-08-08) and the filed edge closed as filed: endpoints
# read from ~/.cairn/devices/inference_domain/0/hosts.json through route.py's overlay (moved
# there 2026-08-17 — the device's state in the device's own space), and the default-built
# resolver ROUTES through the rules stacks instead of dialing a literal (ruling
# 2026-08-08-inference-proxy-is-a-rules-stack). There is no default endpoint constant to
# fall back to on purpose — a literal that survives "just in case" is the defect returning.
DEFAULT_TIMEOUT = 300.0

# The counters a metered response must carry at least one of. Named here so the refusal below
# has one place to point at, and so a host that renames them fails loudly instead of quietly
# metering zero.
_COUNTERS = ("prompt_eval_count", "eval_count")

# The verbs this module sends, each against the one ollama path that serves it. ONE TABLE, read
# by the single-endpoint resolver's provenance AND by the routed walk's kind guard, because the
# set of verbs the resolver can send and the set the walk may admit are the same fact — and a
# fourth verb added to a branch but not to a guard is a request that dies at a door for a reason
# nobody wrote down. The routing stacks still decide WHO serves which verb (route.py's
# serves_kind sieve over the models stack); this only says what this seam knows how to speak.
_PATH_FOR_KIND = {
    "generate": "/api/generate",
    "embed": "/api/embed",
    "chat": "/api/chat",
}


class HostUnreachable(RuntimeError):
    """The host could not be reached at all. Loud — never a silently-empty answer (Law 7)."""


class HostRefused(RuntimeError):
    """The host answered, and its answer was an error (unknown model, bad request)."""


class HostUnmetered(RuntimeError):
    """The host answered WITHOUT token counters, so the call cannot be metered.

    Raised rather than defaulted to 0. A zero-cost row is worse than no row: it keeps the meter's
    shape intact while draining its meaning, and ``yield_report`` would then testify to a saving
    it never measured (Telos 1 / Law 3). The one failure this module most needs to be loud about.
    """


class HostNonFinal(RuntimeError):
    """The host answered a NON-STREAMING request with a frame that is not the final one.

    Named for the field that says so: ollama marks the last frame of a response ``done: true``,
    and a frame carrying ``done: false`` is one of the intermediate ones the STREAMING grammar
    is made of. Arriving in answer to a request that set ``stream: false``, it means the host
    accepted the ask and has not finished it — measured on hex 2026-08-18, six times, while a
    model was loading: HTTP 200, 96 bytes, empty role and empty content, no counters.

    IT EXISTS BECAUSE THE ALTERNATIVE WAS A CONFIDENT WRONG ANSWER. That frame passes three
    checks on its way in — 200 is not >= 400, there is no "error" key, and the chat branch's
    shape check accepts ``message`` because an empty string IS a str — and then dies at
    ``metered_cost``, which reports that the host sent no token counters. True, and useless: it
    sends the reader to the meter, and the meter is innocent. A diagnostic surface that is loud
    about the wrong organ costs MORE than silence, because silence gets investigated and a
    confident wrong answer gets followed (Law 7).

    Deliberately not a retry and not a wait. This says WHAT HAPPENED; what to do about a host
    that is still warming up is a policy decision with its own falsifier, and it is not here.
    """


class BadRequest(ValueError):
    """The request does not name something this resolver can send. Refused before the host."""


def _urllib_transport(url: str, body: bytes, timeout: float) -> tuple[int, bytes]:
    """The default transport. Injectable so the proofs never need a live host."""
    req = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as e:            # the host spoke, and said no
        return e.code, e.read()
    except (urllib.error.URLError, OSError) as e:  # nobody there
        raise HostUnreachable(f"inference host unreachable at {url}: {e}") from e


def _post(path: str, payload: dict, *, endpoint: str, timeout: float, transport) -> dict:
    url = f"{endpoint.rstrip('/')}{path}"
    status, raw = transport(url, json.dumps(payload).encode("utf-8"), timeout)
    try:
        body = json.loads(raw)
    except (ValueError, TypeError) as e:
        raise HostRefused(f"{url} returned non-JSON (status {status}): {raw[:200]!r}") from e
    if status >= 400 or (isinstance(body, dict) and body.get("error")):
        # The host's own message is carried through verbatim — a diagnostic surface must not
        # collapse it into "inference failed" (Law 7, and complete-diagnostic-on-first-pass).
        raise HostRefused(
            f"{url} refused (status {status}): {body.get('error', body) if isinstance(body, dict) else body}")
    if not isinstance(body, dict):
        raise HostRefused(f"{url} returned {type(body).__name__}, expected a JSON object")
    # THE ANSWER MUST BE FINISHED. Every verb this module sends sets stream=False, so the host's
    # reply is one frame and that frame is the last one — ollama says so with done: true. A
    # frame carrying done: false is an intermediate one from the streaming grammar, and it means
    # the ask was accepted and not completed (measured on hex while a model loads, n=6).
    #
    # PRESENT AND NOT TRUE, never merely "not true": /api/embed's real responses carry no `done`
    # key at all, and `body.get("done") is not True` would refuse every embedding this system
    # has ever taken. The narrower predicate is the whole difference between a fix and an
    # outage, and proofs/test_host.py holds a tooth on each side of it.
    #
    # HERE rather than in the three branches below, because this is a property of the RESPONSE
    # and holds whatever verb produced it. The frame was reproduced on /api/chat only; putting
    # the check per-branch would have meant three copies of a claim measured once, and the two
    # unmeasured verbs left open exactly as they were.
    if "done" in body and body["done"] is not True:
        raise HostNonFinal(
            f"{url} answered a non-streaming request with a NON-FINAL frame "
            f"(done={body['done']!r}) — the host accepted the ask and has not finished it, so "
            f"there is no answer here to meter or to read. Model {payload.get('model')!r}. "
            f"The frame verbatim: {json.dumps(body)[:400]}")
    return body


def metered_cost(payload: dict) -> int:
    """Real tokens from the host's own counters, or refuse. The gate that keeps the meter honest."""
    present = [k for k in _COUNTERS if isinstance(payload.get(k), (int, float))]
    if not present:
        raise HostUnmetered(
            f"the host reported no token counters (looked for {list(_COUNTERS)}; "
            f"response carried {sorted(payload)}) — this call cannot be metered, and a cost of 0 "
            "would make yield_report testify to a saving nobody measured")
    return int(sum(payload[k] for k in present))


def validated_messages(request: dict) -> list:
    """The chat request's ``messages``, or refuse — BEFORE the host is dialed.

    The two verbs beside chat are addressed by a single ``prompt`` string; chat is addressed
    by a turn list, so the resolver's promptless refusal cannot judge it and a well-formed
    chat request would be turned away as promptless. This is that check's chat half, and it
    keeps the same discipline: an invalid request is refused where it costs nothing. On Hex a
    cold qwen3-coder:30b load is ~18s (measured 2026-08-16), so a malformed request that
    reaches the host is not a wasted round trip, it is a wasted eighteen seconds.

    Every entry needs BOTH a role and a content string. A turn missing one is the shape ollama
    accepts and answers strangely rather than rejecting, which would make the defect surface as
    a bad answer instead of as an error (Law 7 — loud at the diagnostic surface).
    """
    messages = request.get("messages")
    if not isinstance(messages, list) or not messages:
        raise BadRequest(
            f"a chat request needs a non-empty 'messages' list (got {messages!r})")
    for i, turn in enumerate(messages):
        if not isinstance(turn, dict):
            raise BadRequest(
                f"messages[{i}] must be a dict with 'role' and 'content', "
                f"got {type(turn).__name__}")
        lacking = [k for k in ("role", "content")
                   if not isinstance(turn.get(k), str) or not turn[k].strip()]
        if lacking:
            raise BadRequest(
                f"messages[{i}] lacks a non-empty {' and '.join(repr(k) for k in lacking)} "
                f"(carried {sorted(turn)})")
    return messages


def _urllib_get(url: str, timeout: float) -> tuple[int, bytes]:
    try:
        with urllib.request.urlopen(urllib.request.Request(url, method="GET"), timeout=timeout) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except (urllib.error.URLError, OSError) as e:
        raise HostUnreachable(f"inference host unreachable at {url}: {e}") from e


def installed_models(*, endpoint: str, timeout: float = 10.0,
                     get=None) -> dict[str, str]:
    """``{model_name: digest}`` as the host reports it — the evidence a falsifier is checked against.

    ``get`` is the same injectable-transport courtesy the POST path has, and for the same reason:
    without it the digest read reached the network DIRECTLY, so a proof of this module would have
    quietly depended on a live host on the developer's box and degraded elsewhere. Caught while
    writing the proof — the seam only counts if EVERY host touch goes through it.
    """
    url = f"{endpoint.rstrip('/')}/api/tags"
    status, raw = (get or _urllib_get)(url, timeout)
    try:
        body = json.loads(raw)
    except (ValueError, TypeError) as e:
        raise HostRefused(f"{url} returned non-JSON (status {status})") from e
    if status >= 400 or not isinstance(body, dict):
        raise HostRefused(f"{url} refused (status {status})")
    return {m["name"]: m.get("digest", "") for m in body.get("models", [])}


def lookup_digest(models: dict[str, str], name: str) -> str:
    """The digest for ``name``, tolerating the implicit ``:latest`` tag. '' if genuinely absent.

    FOUND IN THE FIRST LIVE RECORD, 2026-07-26, not by a proof: the run resolved fine and the row
    it wrote carried ``model_digest(nomic-embed-text) == <unread at resolve time>``. The host reports
    its tags as ``nomic-embed-text:latest`` while a caller addresses the model as
    ``nomic-embed-text`` — ollama treats those as the same model, and a bare dict lookup does not.
    So the falsifier degraded to 'unread' for the MOST COMMON way to name a model, quietly, on a
    green run. It surfaced only because the stored record was read back and looked at (Law 3 — the
    proof said the shape was right; only the live row said the content was empty).
    """
    if name in models:
        return models[name]
    if ":" not in name:
        return models.get(f"{name}:latest", "")
    base, _, tag = name.rpartition(":")
    return models.get(base, "") if tag == "latest" else ""


def digest_falsifier(model: str, digest: str) -> str:
    """The falsifier, machine-checkable: one ``/api/tags`` read answers it (T1.4's cheap door)."""
    return f"model_digest({model}) == {digest}"


def ollama_resolver(
    *,
    model: str,
    endpoint: str | None = None,
    timeout: float = DEFAULT_TIMEOUT,
    transport=None,
    get=None,
    temperature: float = 0.0,
    stacks: dict | None = None,
    overlay: dict | None = None,
):
    """Build the ``resolver`` callable ``domain.resolve`` injects — the host, behind one seam.

    WITH NO ``endpoint``, THE RESOLVER ROUTES (the default every live caller uses): each call
    shakes route.py's nest over the authored stacks and dials the surviving combos cheapest
    first — usually Hex — walking to the next survivor on ``HostUnreachable`` and refusing
    loudly when the walk exhausts. The four bare call sites (librarian x3,
    intention_extractor x1) got the ruled routing through this default with zero edits.
    An EXPLICIT ``endpoint`` pins one host and skips the stacks — the proofs' seam, and the
    routed walk's own inner rungs.

    The request it accepts::

        {"kind": "generate", "prompt": "..."}          -> answer {"text": ...}
        {"kind": "embed",    "prompt": "..."}          -> answer {"vector": [...], "dim": n}
        {"kind": "chat", "messages": [{"role", "content"}, ...]}
                                                      -> answer {"text": ..., "role": ...}

    plus an optional ``"model"`` override and an optional ``"options"`` dict passed to the host.
    Chat is NON-STREAMING and deliberately so — its first consumer runs ``--no-stream``, and a
    streaming face is growth against no measured need. It is also UNDRESSED by construction:
    the domain seam dresses ``generate`` only, and a turn list already carries a system role,
    so a second path to the same thing would be invented before a caller wanted it.
    ``kind`` is required and an unknown one is REFUSED before any host call: guessing the caller's
    intent is how a request for a vector comes back as prose (a silent wrong answer).

    Returns ``{"answer", "cost", "falsifier", "horizon", "provenance"}`` — the contract
    ``resolve`` documents, with ``cost`` in real tokens; a routed answer's provenance also
    names the ``provider`` the nest chose and, if the walk fell over, the rungs it walked.
    """
    if endpoint is None:
        return _routed_resolver(model=model, timeout=timeout, transport=transport, get=get,
                                temperature=temperature, stacks=stacks, overlay=overlay)
    send = transport or _urllib_transport
    digests: dict[str, str] = {}

    def _falsifier_for(name: str) -> str:
        # Read once per model per resolver, not once per call: the falsifier is worth one extra
        # host read, not one per miss. A host that cannot report it does not sink the answer —
        # the falsifier degrades to naming the model, and says so.
        if name not in digests:
            try:
                digests[name] = lookup_digest(
                    installed_models(endpoint=endpoint, timeout=10.0, get=get), name)
            except (HostUnreachable, HostRefused):
                digests[name] = ""
        d = digests[name]
        return digest_falsifier(name, d) if d else f"model_digest({name}) == <unread at resolve time>"

    def resolver(request: dict) -> dict:
        if not isinstance(request, dict):
            raise BadRequest(f"request must be a dict, got {type(request).__name__}")
        kind = request.get("kind")
        # The shape check dispatches on kind because the verbs are addressed differently: two
        # take a prompt string, chat takes a turn list. Both refusals fire before any host call.
        if kind == "chat":
            messages = validated_messages(request)
        else:
            prompt = request.get("prompt")
            if not isinstance(prompt, str) or not prompt.strip():
                raise BadRequest(f"request needs a non-empty 'prompt' (got {prompt!r})")
        name = request.get("model") or model
        options = {"temperature": temperature, **(request.get("options") or {})}

        if kind == "generate":
            payload = {"model": name, "prompt": prompt, "stream": False, "options": options}
            if request.get("system"):
                # The domain seam's dressing (or a caller's own system text) rides ollama's
                # native 'system' field — it is part of the question and canonicalizes
                # upstream, so it must reach the host, never be dropped here.
                payload["system"] = request["system"]
            body = _post("/api/generate", payload,
                         endpoint=endpoint, timeout=timeout, transport=send)
            if "response" not in body:
                raise HostRefused(f"/api/generate returned no 'response' field: {sorted(body)}")
            answer = {"text": body["response"]}
        elif kind == "embed":
            # /api/embed, NOT /api/embeddings — the older path reports no counters (measured
            # 2026-07-26, see the module note). It returns a LIST of vectors for a list input;
            # one prompt in, so one vector out, and a shape that surprises us is refused rather
            # than indexed into blindly.
            body = _post("/api/embed", {"model": name, "input": prompt},
                         endpoint=endpoint, timeout=timeout, transport=send)
            vectors = body.get("embeddings")
            if not (isinstance(vectors, list) and len(vectors) == 1 and isinstance(vectors[0], list)):
                raise HostRefused(
                    f"/api/embed returned an unexpected 'embeddings' shape for a single input: "
                    f"{type(vectors).__name__}"
                    + (f" of {len(vectors)}" if isinstance(vectors, list) else ""))
            answer = {"vector": vectors[0], "dim": len(vectors[0])}
        elif kind == "chat":
            # /api/chat is generate's turn-taking sibling: same counters, same stream flag,
            # a messages list where generate has a prompt. MEASURED against the live host
            # 2026-08-16 before this branch was written, because the whole verb rests on it —
            # the response carried prompt_eval_count 15 and eval_count 2, so the meter below
            # is metering the host's own numbers here exactly as it does for generate. Had it
            # come back counterless (as /api/embeddings did in 2026-07-26), HostUnmetered would
            # have refused every chat call and the design would have gone back for a ruling
            # rather than quietly metering zero.
            payload = {"model": name, "messages": messages, "stream": False, "options": options}
            body = _post("/api/chat", payload,
                         endpoint=endpoint, timeout=timeout, transport=send)
            message = body.get("message")
            if not isinstance(message, dict) or not isinstance(message.get("content"), str):
                # Refused, not indexed into — the embed branch's standard, for the same reason:
                # a missing field indexed blindly becomes an answer of None travelling as prose.
                raise HostRefused(
                    f"/api/chat returned an unexpected 'message' shape: "
                    f"{type(message).__name__}"
                    + (f" carrying {sorted(message)}" if isinstance(message, dict) else ""))
            answer = {"text": message["content"], "role": message.get("role", "assistant")}
        else:
            raise BadRequest(
                f"unknown request kind {kind!r} — this resolver sends 'generate', 'embed' or "
                "'chat'. Guessing would answer a different question than the one asked.")

        return {
            "answer": answer,
            "cost": metered_cost(body),          # refuses rather than metering zero
            "falsifier": _falsifier_for(name),
            "horizon": "",                       # no time expiry: a temperature-0 answer does not
                                                 # rot with the clock; the digest is what falsifies
            "provenance": {
                "host": endpoint,
                "path": _PATH_FOR_KIND[kind],
                "model": name,
                "options": options,
                "counters": {k: body[k] for k in _COUNTERS if k in body},
            },
        }

    return resolver


def _routed_resolver(*, model: str, timeout: float, transport, get, temperature: float,
                     stacks: dict | None, overlay: dict | None):
    """The routed walk: the nest decides WHO may be dialed, the walk discovers who ANSWERS.

    Per call: shake the nest for this request's kind and model, then dial survivors cheapest
    first through the single-endpoint resolver above. ``HostUnreachable`` walks to the next
    rung; every other error is the HOST'S answer and is carried through loud (a refusal from
    a host that answered is not a routing problem, and retrying it elsewhere would hand back
    a different model's answer under the same cache key). A survivor whose protocol has no
    transport yet (gemini, until its key lands and the transport is built) is noted and
    walked past — listed, refusing, never silently dialed with the wrong protocol.
    """
    from cairn.devices.inference_domain import route as route_mod  # late: keeps the import edge one-way

    inners: dict[str, object] = {}

    def _inner(rung_endpoint: str):
        if rung_endpoint not in inners:
            inners[rung_endpoint] = ollama_resolver(
                model=model, endpoint=rung_endpoint, timeout=timeout,
                transport=transport, get=get, temperature=temperature)
        return inners[rung_endpoint]

    def resolver(request: dict) -> dict:
        if not isinstance(request, dict):
            raise BadRequest(f"request must be a dict, got {type(request).__name__}")
        kind = request.get("kind")
        if kind not in _PATH_FOR_KIND:
            raise BadRequest(
                f"unknown request kind {kind!r} — this resolver sends "
                f"{', '.join(repr(k) for k in _PATH_FOR_KIND)}. "
                "Guessing would answer a different question than the one asked.")
        domain = request.get("domain")
        allow = None
        if domain is not None:
            row = route_mod.domain_rows(stacks)["rows"].get(domain)
            if row is None:
                raise BadRequest(
                    f"no domain row named {domain!r} in the domains stack — a vertical is an "
                    "authored row, never an ad-hoc string")
            # The domain's escalation walk-rule: WHICH rungs this vertical's walk may dial —
            # a GETTING rule only (Akien's boundary sentence: the reasoning happens in the
            # calling device). It filters the walk, never the nest: the shake and its cuts
            # are untouched, and a skipped rung is in the trace, not silent. Absent = every
            # survivor, which is exactly today's walk.
            allow = (row.get("escalation") or {}).get("allow")
        plan = route_mod.route(kind, request.get("model") or model,
                               domain=domain, stacks=stacks, overlay=overlay)
        walked: list[str] = []
        for rung in plan["survivors"]:
            if allow is not None and rung["provider"] not in allow:
                walked.append(f"{rung['provider']}: outside domain {domain!r}'s escalation "
                              f"walk-rule (allow: {allow})")
                continue
            if rung["protocol"] != "ollama":
                walked.append(f"{rung['provider']}: no transport for protocol "
                              f"{rung['protocol']!r} yet — grows when the rung goes live")
                continue
            try:
                out = _inner(rung["endpoint"])(request)
            except HostUnreachable as e:
                walked.append(f"{rung['provider']} ({rung['endpoint']}): {e}")
                continue
            out["provenance"]["provider"] = rung["provider"]
            if walked:
                out["provenance"]["route_walked"] = walked
            return out
        raise HostUnreachable(
            "every routed rung failed for this call — walked, in cost order: "
            + "; ".join(walked))

    return resolver
