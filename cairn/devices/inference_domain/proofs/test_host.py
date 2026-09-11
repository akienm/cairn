"""Proof: the HOST SEAM (cairn/devices/inference_domain/host.py) meters real tokens or refuses.

The gate a hollow build could not pass. The failure this module exists to prevent is not "the
host is down" — that one is loud and obvious. It is A RESOLVER THAT WORKS AND METERS NOTHING:
right shape, real answers, cost silently 0, and ``yield_report`` reporting a beautifully
consistent 0-spent/0-avoided that testifies to a saving nobody measured. Telos 1 is the claim
that inference compilation PAYS; a meter reading zeroes cannot support or refute it (Law 3), and
would never look broken (Law 8). So the teeth below are mostly about the cost, not the answer:

  - the older ``/api/embeddings`` path — which measurably reports NO counters — is not used;
  - a response with no counters is REFUSED, never defaulted to 0;
  - the cost is the SUM of the host's own counters, checked against a real measured response.

Hermetic: every host touch (POST and the digest GET) goes through an injected transport, so this
runs green with no ollama present and cannot pass by accident on a machine where one happens to
be up. The LIVE measurement against the real host is a separate, deliberate act recorded in the
node's VALIDATION — not smuggled in here, where an absent host would read as a flake.

    python3 cairn/devices/inference_domain/proofs/test_host.py     # exit 0 = green, no host needed
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.import_sieve import sieve
from cairn.devices.inference_domain import host

# The mesh. OUTBOUND ONLY, matched on the full dotted name: a module that can DIAL is a
# potential door; one that can only LISTEN is not, and urllib.parse is pure string work.
_SOLE_PATH = {
    "kind": "sole_path",
    "capability": "the inference host",
    "modules": ("urllib.request", "urllib.error", "http.client", "requests", "httpx",
                "aiohttp", "socket", "ftplib", "telnetlib"),
    "only": "cairn/devices/inference_domain/",
}

# A REAL response, captured from the live host 2026-07-26 (llama3.2:1b, "Reply with the single
# word: ok"). Copied rather than invented: a proof whose fixture is imaginary proves the fixture.
_REAL_GENERATE = {
    "model": "llama3.2:1b", "created_at": "2026-07-27T01:48:26.45489729Z",
    "response": "No.", "done": True, "done_reason": "stop",
    "total_duration": 2168603913, "load_duration": 1666588633,
    "prompt_eval_count": 32, "prompt_eval_duration": 383415849,
    "eval_count": 3, "eval_duration": 111089356,
}
# Also real: /api/embed reports prompt_eval_count and NO eval_count (an embed evaluates no output).
_REAL_EMBED = {"model": "nomic-embed-text", "embeddings": [[0.01] * 768],
               "total_duration": 394565317, "load_duration": 328372368, "prompt_eval_count": 9}
# And the one that started this: /api/embeddings, the older path, returns ONLY the vector.
_REAL_EMBEDDINGS_UNMETERED = {"embedding": [0.01] * 768}
# Also real, and captured BEFORE the chat branch was written rather than after it: qwen3-coder:30b
# on hex.local, 2026-08-16, stream false, "Reply with the single word: ok". The whole chat verb
# rested on one question — does /api/chat report counters the way /api/generate does — and this
# response is the answer. Note load_duration ~18s against eval_duration ~0.02s: that is a cold
# model load, a property of the host's cache and not of any code here.
_REAL_CHAT = {
    "model": "qwen3-coder:30b", "created_at": "2026-08-16T02:39:54.806337Z",
    "message": {"role": "assistant", "content": "ok"},
    "done": True, "done_reason": "stop",
    "total_duration": 18208569500, "load_duration": 18013486208,
    "prompt_eval_count": 15, "prompt_eval_duration": 171578000,
    "eval_count": 2, "eval_duration": 21563000,
}
_A_TURN = [{"role": "user", "content": "Reply with the single word: ok"}]

# The tag names EXACTLY as the host reports them — note the implicit ':latest' on the embed model,
# which is what broke the falsifier on the first live run. A fixture that tidied it away would have
# kept this proof green through the bug.
_TAGS = {"models": [{"name": "qwen2.5:7b", "digest": "845dbda0ea48ed749ca"},
                    {"name": "llama3.2:1b", "digest": "baf6a787fdffd633537"},
                    {"name": "nomic-embed-text:latest", "digest": "0a109f422b47e3a30ba"}]}
_TAGS_MAP = {m["name"]: m["digest"] for m in _TAGS["models"]}


class Transport:
    """Records every host touch. The recording IS most of the proof — which URL was opened."""

    def __init__(self, response, status=200):
        self.response, self.status = response, status
        self.urls: list[str] = []
        self.bodies: list[dict] = []

    def post(self, url, body, timeout):
        self.urls.append(url)
        self.bodies.append(json.loads(body))
        payload = self.response(url) if callable(self.response) else self.response
        return self.status, json.dumps(payload).encode()

    def get(self, url, timeout):
        self.urls.append(url)
        return 200, json.dumps(_TAGS).encode()


# EXPLICIT endpoint everywhere in this file: since the routed default landed (2026-08-08), an
# endpoint-less build takes the ROUTED path — real stacks, the real ~/.cairn overlay — which a
# sealed proof must never read. The routed walk has its own teeth below, on injected fixtures.
_FIXTURE_ENDPOINT = "http://fixture-host:11434"

# WHICH CLAUSE OF 548dd13fb4db'S FALSIFIER EACH TOOTH PROVES — read by proof_coverage and by
# the hollow check, which fires each named tooth at a REVERTED build and demands a red.
# The ticket states five DONE-when clauses plus a WRONG INTENT; this proof owns the three that
# are about what crosses to the host. The cache-side clauses (b) and (e) are declared by
# cairn/devices/inference_domain/proofs/test_inference_domain.py, which is where the canonical
# digest and the agent lane actually live.
#
# (c) IS THE ONE THAT EARNS ITS KEEP. The inbound tool-call argument shape fails ONLY on the
# second turn — OpenAI carries arguments as a JSON string, ollama wants an object — so a
# one-shot test reads green over a door that cannot hold a conversation. Measured 2026-09-11 on
# hex.local against qwen3-coder:30b before any of this was built.
PROVES = {
    "548dd13fb4db": {
        "carries_a_toolset": "test_a_toolset_crosses_to_the_host_and_a_toolless_chat_is_byte_identical",
        "second_turn": "test_the_second_turn_of_a_tool_using_conversation_reaches_the_host",
        "checked_not_exempted": "test_the_agent_shapes_are_CHECKED_not_exempted",
    }
}



def _resolver(t, **kw):
    return host.ollama_resolver(model="llama3.2:1b", endpoint=_FIXTURE_ENDPOINT,
                                transport=t.post, get=t.get, **kw)


def _refuses(fn, exc, because):
    """A refusal that names the gate. A generic exception means the gate was removed, and the
    downstream crash is the symptom, not the cause — so say that instead of letting it surface raw."""
    try:
        fn()
    except exc:
        return
    except Exception as e:                       # noqa: BLE001 — the diagnostic IS the point
        raise AssertionError(
            f"THE GATE DID NOT REFUSE — {because}. Instead the bad case got far enough in to break "
            f"something else: {type(e).__name__}: {e}. The refusal was removed or weakened."
        ) from None
    raise AssertionError(f"NO REFUSAL AT ALL — {because}. A silent pass here is the hollow direction.")


# ---------------------------------------------------------------- the meter, which is the point

def test_an_unmetered_response_is_refused_not_metered_as_zero():
    """THE HEADLINE TOOTH: an answer that is PERFECTLY GOOD and carries no counters is refused.

    If this tooth is deleted, everything else still passes and the whole Telos 1 instrument
    silently reports zeroes. That is why it is first.

    The fixture is a valid 768-float vector with the counter stripped — which is the actual
    hazard shape. Written first with the real /api/embeddings response as the fixture, and the
    tooth failed for the RIGHT reason: that body has no 'embeddings' key at all, so the shape gate
    fires before the meter gate ever runs. Two different gates, and the sloppy version of this
    tooth would have credited the meter for the shape check's work.
    """
    t = Transport({"model": "nomic-embed-text", "embeddings": [[0.01] * 768]})   # counter stripped
    _refuses(lambda: _resolver(t)({"kind": "embed", "prompt": "the embedding is the path"}),
             host.HostUnmetered,
             "a good answer carrying no token counters must not be metered at cost 0")
    # And separately, on the real captured body: the older endpoint's response cannot be metered
    # AT ALL. This is the measurement that decided which door this module opens.
    _refuses(lambda: host.metered_cost(_REAL_EMBEDDINGS_UNMETERED), host.HostUnmetered,
             "the real /api/embeddings response carries no counters — it is unmeterable, which is "
             "the whole reason /api/embed is the door")


def test_the_cost_is_the_sum_of_the_hosts_own_counters():
    t = Transport(_REAL_GENERATE)
    out = _resolver(t)({"kind": "generate", "prompt": "Reply with the single word: ok"})
    assert out["cost"] == 35, (
        f"cost must be prompt_eval_count + eval_count = 32 + 3 = 35, got {out['cost']!r} — a proxy "
        "for tokens is not tokens")
    assert out["provenance"]["counters"] == {"prompt_eval_count": 32, "eval_count": 3}, \
        "the raw counters must survive into provenance, so the cost can be audited, not trusted"


def test_an_embed_meters_its_input_tokens_alone():
    """An embed evaluates no output, so eval_count is absent — and that is still metered."""
    t = Transport(_REAL_EMBED)
    out = _resolver(t)({"kind": "embed", "prompt": "the embedding is the path"})
    assert out["cost"] == 9, f"embed cost must be prompt_eval_count alone, got {out['cost']!r}"
    assert out["answer"]["dim"] == 768 == len(out["answer"]["vector"]), \
        "the vector and its declared dim must agree — a dim nobody derived is a claim, not a fact"


def test_metered_cost_refuses_a_renamed_counter():
    """A host that renames its counters must break LOUDLY, not meter zero. This is the drift case:
    nothing in our code changes, the host changes under us, and the meter goes quietly dead."""
    _refuses(lambda: host.metered_cost({"tokens_used": 40}), host.HostUnmetered,
             "an unrecognised counter name is not a reason to meter 0")


# ---------------------------------------------------------------- which door it actually opens

def test_embed_uses_api_embed_and_never_the_unmetered_api_embeddings():
    t = Transport(_REAL_EMBED)
    _resolver(t)({"kind": "embed", "prompt": "x"})
    assert t.urls[0].endswith("/api/embed"), f"opened the wrong door: {t.urls[0]}"
    assert not any(u.endswith("/api/embeddings") for u in t.urls), (
        "/api/embeddings reports no counters (measured 2026-07-26) — resolving through it is how "
        "the meter dies without a red")


def test_temperature_is_pinned_to_zero_and_the_caller_may_override():
    t = Transport(_REAL_GENERATE)
    _resolver(t)({"kind": "generate", "prompt": "x"})
    assert t.bodies[0]["options"]["temperature"] == 0.0, (
        "a cached nondeterministic answer changes what the cache MEANS — the default must be 0")
    t2 = Transport(_REAL_GENERATE)
    _resolver(t2)({"kind": "generate", "prompt": "x", "options": {"temperature": 0.8}})
    assert t2.bodies[0]["options"]["temperature"] == 0.8, "the caller's option must win"


# ---------------------------------------------------------------- refusals before the host

def test_an_unknown_kind_is_refused_before_any_host_call():
    t = Transport(_REAL_GENERATE)
    _refuses(lambda: _resolver(t)({"kind": "summarise", "prompt": "x"}), host.BadRequest,
             "an unknown kind must be refused, not guessed")
    assert t.urls == [], "the host was touched despite an invalid request — spend before validation"


def test_an_empty_or_missing_prompt_is_refused_before_any_host_call():
    t = Transport(_REAL_GENERATE)
    for bad in ({"kind": "generate"}, {"kind": "generate", "prompt": "   "},
                {"kind": "generate", "prompt": 7}):
        _refuses(lambda b=bad: _resolver(t)(b), host.BadRequest,
                 f"a request with no usable prompt must be refused ({bad!r})")
    assert t.urls == [], "an empty prompt reached the host"


# ---------------------------------------------------------------- loud failures (Law 7)

def test_the_hosts_own_error_message_is_carried_through_verbatim():
    """Measured for real earlier today: asking for a model that is not installed. The diagnostic
    surface must carry the host's words — 'inference failed' would cost a second run to learn why
    (I-complete-diagnostic-on-first-pass)."""
    t = Transport({"error": "model 'llama3.2:3b' not found"})
    try:
        _resolver(t)({"kind": "generate", "prompt": "x", "model": "llama3.2:3b"})
    except host.HostRefused as e:
        assert "llama3.2:3b" in str(e) and "not found" in str(e), \
            f"the host's own diagnosis was swallowed: {e}"
    else:
        raise AssertionError("an error body was treated as an answer")


def test_an_unreachable_host_raises_and_never_returns_an_empty_answer():
    def dead(url, body, timeout):
        raise host.HostUnreachable(f"nobody home at {url}")
    r = host.ollama_resolver(model="m", endpoint=_FIXTURE_ENDPOINT,
                             transport=dead, get=lambda u, t: (200, b"{}"))
    _refuses(lambda: r({"kind": "generate", "prompt": "x"}), host.HostUnreachable,
             "an unreachable host must raise, never return a hollow answer that gets cached")


def test_an_unexpected_embed_shape_is_refused_not_blindly_indexed():
    for weird in ({"embeddings": [], "prompt_eval_count": 9},
                  {"embeddings": [[0.1], [0.2]], "prompt_eval_count": 9},
                  {"embeddings": {"v": [0.1]}, "prompt_eval_count": 9},
                  {"prompt_eval_count": 9}):
        t = Transport(weird)
        _refuses(lambda: _resolver(t)({"kind": "embed", "prompt": "x"}), host.HostRefused,
                 f"an unexpected embeddings shape must be refused, not indexed into ({weird!r})")


def test_a_generate_with_no_response_field_is_refused():
    t = Transport({"model": "m", "prompt_eval_count": 5, "eval_count": 1})
    _refuses(lambda: _resolver(t)({"kind": "generate", "prompt": "x"}), host.HostRefused,
             "a generate with no 'response' must not yield an answer of None")


# ---------------------------------------------------------------- the falsifier is checkable

def test_the_falsifier_names_a_digest_a_machine_can_check():
    """Charter edge (c): VERIFY checks the horizon, the FALSIFIER is carried for T1.4. A prose
    falsifier makes that edge expensive; this one is answered by a single /api/tags read."""
    t = Transport(_REAL_GENERATE)
    out = _resolver(t)({"kind": "generate", "prompt": "x"})
    fals = out["falsifier"]
    assert fals == host.digest_falsifier("llama3.2:1b", "baf6a787fdffd633537"), \
        f"the falsifier is not the checkable digest form: {fals!r}"
    # And it is answerable: the same read the falsifier implies, through the same seam.
    assert host.installed_models(endpoint=_FIXTURE_ENDPOINT, get=t.get)["llama3.2:1b"] in fals, \
        "the falsifier cannot be evaluated against what the host reports — then it is prose"
    assert out["horizon"] == "", \
        "a temperature-0 answer does not rot with the clock; a time horizon here would be theatre"


def test_the_digest_read_goes_through_the_seam_not_around_it():
    """The bug this caught while being written: installed_models reached urllib DIRECTLY, so this
    proof would have depended on a live host on the author's box and degraded silently elsewhere.
    A seam that is bypassed anywhere is not a sole path (charter edge (b))."""
    t = Transport(_REAL_GENERATE)
    _resolver(t)({"kind": "generate", "prompt": "x"})
    assert any(u.endswith("/api/tags") for u in t.urls), \
        "the digest read did not go through the injected transport — it went around the seam"


def test_a_model_named_without_its_implicit_latest_tag_still_gets_a_real_digest():
    """Regression from the FIRST LIVE RUN. The proof was green and the stored row still carried
    'model_digest(nomic-embed-text) == <unread at resolve time>': the host tags it
    'nomic-embed-text:latest', the caller names it 'nomic-embed-text', and a dict lookup missed.
    Silent degradation on the most common way to name a model — caught by reading the record the
    run actually wrote, which is the only place it was visible."""
    t = Transport(_REAL_EMBED)
    out = host.ollama_resolver(model="nomic-embed-text", endpoint=_FIXTURE_ENDPOINT,
                               transport=t.post, get=t.get)(
        {"kind": "embed", "prompt": "x"})
    assert out["falsifier"] == host.digest_falsifier("nomic-embed-text", "0a109f422b47e3a30ba"), \
        f"the implicit :latest tag lost the digest: {out['falsifier']!r}"
    # both directions, and a genuinely-absent model is still honestly empty
    assert host.lookup_digest(_TAGS_MAP, "nomic-embed-text:latest") == "0a109f422b47e3a30ba"
    assert host.lookup_digest(_TAGS_MAP, "llama3.2:1b") == "baf6a787fdffd633537"
    assert host.lookup_digest(_TAGS_MAP, "not-installed") == "", \
        "a model the host does not have must not be handed some other model's digest"


def test_a_falsifier_survives_an_unreadable_digest_and_says_so():
    """Degrading is allowed; degrading SILENTLY is not (Law 7)."""
    def no_tags(url, timeout):
        raise host.HostUnreachable("tags unavailable")
    r = host.ollama_resolver(model="llama3.2:1b", endpoint=_FIXTURE_ENDPOINT,
                             transport=Transport(_REAL_GENERATE).post, get=no_tags)
    fals = r({"kind": "generate", "prompt": "x"})["falsifier"]
    assert "unread" in fals, f"an unread digest must be admitted in the falsifier, got {fals!r}"


# ---------------------------------------------------------------- sole path

def test_no_other_module_in_the_tree_opens_the_inference_host():
    """Charter edge (b): the host client lives HERE and nowhere else. The IOU is now CLOSED —
    this delegates to cairn/tools/import_sieve, the shared tooth, instead of carrying its own copy.

    WHAT CHANGED ON 2026-08-06, and why it was not just a refactor. The hand-rolled version
    globbed `_REPO_ROOT / "cairn"` — the package directory. It therefore never looked at
    bin/, skills/, launchers/ or learning/: 26 real Python files, including every skill door
    and probe, in which a second dialer would have been invisible. Measured with the mutant:
    a file planted at skills/ was missed by the old glob and is caught by the sieve.

    The two hard-won properties are unchanged, because they moved INTO the sieve rather than
    being re-derived here (Law 1): outbound-only matched on the full dotted name, so a module
    that can only LISTEN (web_server's http.server) is not a door and urllib.parse is not a
    door; and the non-hollow floor, which is now a raise inside catches() rather than a
    separate assert at the bottom of this function that a second copy could forget.
    """
    caught = sieve.catches(sieve.import_graph(str(_REPO_ROOT)), _SOLE_PATH)
    assert not caught, (
        "a SECOND module can open a network connection — the sole path to the inference host "
        "is no longer sole (Law 6, charter falsifier (6)). If the new door is legitimate and "
        "NOT an inference-host client, it belongs in this rule's mesh WITH a reason, which is "
        "the conversation this red exists to force:\n  " + "\n  ".join(caught))


def test_the_sole_path_tooth_reds_on_a_planted_dialer():
    """Non-vacuity, and it is the tooth that was missing before. The check above passes over a
    clean tree and would pass identically if the mesh were solid sheet metal."""
    planted = {f"filler/m{i}.py": {"json"} for i in range(25)}
    planted["skills/sorted/probes/door.py"] = sieve.imports_in("import http.client")
    planted["cairn/devices/inference_domain/host.py"] = sieve.imports_in("import urllib.request")
    caught = sieve.catches(planted, _SOLE_PATH)
    assert len(caught) == 1, f"exactly the rogue, inference_domain itself spared: {caught}"
    assert "skills/sorted/probes/door.py" in caught[0], (
        "and it is caught OUTSIDE cairn/ — the blind spot the hand-rolled glob had")


# ------------------------------------------------- the domains: dressing and the walk-rule

def _domain_stacks(*, allow=None):
    """Walk fixtures WITH a domains stack: general (default, adds nothing) and 'narrow', a
    fixture vertical carrying a dressing and, when given, an escalation walk-rule. Two fake
    providers, never the real unkeyed cloud rungs."""
    return {
        "providers": {"providers": [
            {"name": "p-cheap", "protocol": "ollama", "cash_per_mtoken": 0.1, "enabled": True},
            {"name": "p-dear", "protocol": "ollama", "cash_per_mtoken": 0.2, "enabled": True},
        ]},
        "models": {"models": [{"name": "m", "serves": ["generate", "chat"]}]},
        "combos": {"combos": [{"provider": "p-cheap", "model": "m"},
                              {"provider": "p-dear", "model": "m"}]},
        "domains": {"domains": [
            {"name": "general", "default": True, "why": "fixture default",
             "prompts": {"generate": ""}, "escalation": {}, "prefers": []},
            {"name": "narrow", "default": False, "why": "fixture vertical",
             "prompts": {"generate": "Fixture dressing: answer narrowly."},
             "escalation": ({"allow": allow} if allow else {}), "prefers": []},
        ]},
    }


_DOMAIN_OVERLAY = {"p-cheap": {"endpoint": "http://cheap:11434"},
                   "p-dear": {"endpoint": "http://dear:11434"}}


def test_the_outbound_body_wears_the_named_domains_prompt_content():
    """Ticket tell 1, answered by CAPTURE, not narration: the request dressed by the domain
    seam reaches the host with the row's prompt content in the /api/generate body's own
    'system' field — domains applied, not decorative."""
    from cairn.devices.inference_domain import domain
    stacks = _domain_stacks()
    dressed, name = domain._domain_dressed(
        {"kind": "generate", "prompt": "the question", "domain": "narrow"}, stacks=stacks)
    assert name == "narrow"
    t = Transport(_REAL_GENERATE)
    _resolver(t)(dressed)
    body = t.bodies[-1]
    assert body["system"] == "Fixture dressing: answer narrowly.", \
        f"the captured outbound body must wear the domain's prompt content: {body}"
    assert body["prompt"] == "the question", "the caller's own prompt crosses verbatim beside it"


def test_a_bare_requests_outbound_body_is_byte_for_byte_undressed():
    """The default adds nothing: a bare request's dressed form posts exactly the pre-domains
    body — no system field, no domain key, nothing new for the host to see."""
    from cairn.devices.inference_domain import domain
    dressed, name = domain._domain_dressed(
        {"kind": "generate", "prompt": "plain"}, stacks=_domain_stacks())
    assert name == "general"
    t = Transport(_REAL_GENERATE)
    _resolver(t)(dressed)
    assert sorted(t.bodies[-1]) == ["model", "options", "prompt", "stream"], \
        f"a general call's host body must carry no domain artifacts: {sorted(t.bodies[-1])}"


def _domain_walk(request, *, allow=None, cheap_answers=True, dear_answers=True):
    dialed: list[str] = []

    def transport(url, body, timeout):
        dialed.append(url)
        up = cheap_answers if url.startswith("http://cheap") else dear_answers
        if not up:
            raise host.HostUnreachable(f"nobody home at {url}")
        answer = _REAL_CHAT if url.endswith("/api/chat") else _REAL_GENERATE
        return 200, json.dumps(answer).encode()

    r = host.ollama_resolver(model="m", stacks=_domain_stacks(allow=allow),
                             overlay=_DOMAIN_OVERLAY, transport=transport,
                             get=lambda u, t: (200, b'{"models": []}'))
    return r(request), dialed


def test_generals_walk_is_todays_walk_exactly():
    """The default vertical reproduces the pre-domains dial sequence under identical
    fixtures — cheapest first, walk on unreachability only (hypothesize falsifier)."""
    bare, bare_dialed = _domain_walk({"kind": "generate", "prompt": "x"},
                                     cheap_answers=False, dear_answers=True)
    named, named_dialed = _domain_walk({"kind": "generate", "prompt": "x",
                                        "domain": "general"},
                                       cheap_answers=False, dear_answers=True)
    assert bare_dialed == named_dialed, \
        f"general must dial exactly the bare sequence: {bare_dialed} vs {named_dialed}"
    assert named["provenance"]["provider"] == "p-dear"


def test_the_walk_obeys_the_domains_escalation_rule():
    """The GETTING rule: a domain allowing only the dear rung never dials the cheap one,
    and the skipped rung is loud in the trace — never a silent narrowing."""
    out, dialed = _domain_walk({"kind": "generate", "prompt": "x", "domain": "narrow"},
                               allow=["p-dear"])
    assert out["provenance"]["provider"] == "p-dear"
    assert not any(u.startswith("http://cheap") for u in dialed), \
        f"a rung outside the walk-rule must never be dialed: {dialed}"
    assert any("walk-rule" in w for w in out["provenance"]["route_walked"]), \
        "the skipped rung must ride the provenance naming the rule that skipped it"


# ------------------------------------------------------------------- the third verb: chat

def test_a_chat_call_meters_the_hosts_own_counters():
    """THE FIRST FALSIFIER TELL, against the REAL captured response: a chat answer's cost is the
    host's own two counters summed, and the answer carries the assistant's content as text.

    The ticket entered carrying this as its one risky assumption — /api/chat might have been
    /api/embeddings all over again (a perfectly good answer with no counters, metered as a
    silent zero). It is not, and the fixture above is the measurement that settled it."""
    t = Transport(_REAL_CHAT)
    out = _resolver(t)({"kind": "chat", "messages": _A_TURN})
    assert out["cost"] == 15 + 2, f"cost must be the host's own counters summed: {out['cost']}"
    assert out["answer"]["text"] == "ok", f"the assistant's content is the answer: {out['answer']}"
    assert out["answer"]["role"] == "assistant"
    assert out["provenance"]["counters"] == {"prompt_eval_count": 15, "eval_count": 2}, \
        f"the counters ride the provenance verbatim: {out['provenance']['counters']}"


def test_an_unmetered_chat_answer_is_refused_not_metered_as_zero():
    """The headline tooth, extended to the new verb: a PERFECTLY GOOD chat answer whose counters
    have been stripped is refused, never metered 0.

    The fixture is the real response with the two counters removed — not a hand-built stub —
    so what is being tested is the meter, not somebody's idea of what a bad response looks like."""
    counterless = {k: v for k, v in _REAL_CHAT.items() if k not in host._COUNTERS}
    assert counterless["message"]["content"] == "ok", "the answer itself is still perfectly good"
    t = Transport(counterless)
    _refuses(lambda: _resolver(t)({"kind": "chat", "messages": _A_TURN}), host.HostUnmetered,
             because="a chat answer with no counters must refuse, not meter zero — the same "
                     "lesson /api/embeddings taught on 2026-07-26, one verb later")


def test_chat_opens_api_chat_and_nothing_else():
    """The door tooth: one URL, and it is /api/chat. The recording IS the proof."""
    t = Transport(_REAL_CHAT)
    _resolver(t)({"kind": "chat", "messages": _A_TURN})
    # /api/tags is the falsifier's digest read, a different act on the same recorder. Every
    # url that ISN'T that must be the one inference door, and there must be exactly one.
    dialed = [u for u in t.urls if not u.endswith("/api/tags")]
    assert dialed == [f"{_FIXTURE_ENDPOINT}/api/chat"], \
        f"a chat call opens /api/chat exactly once and no other inference door: {t.urls}"
    body = t.bodies[-1]
    assert body["messages"] == _A_TURN, f"the turn list crosses verbatim: {body}"
    assert body["stream"] is False, "chat is non-streaming, deliberately — its consumer runs --no-stream"
    assert sorted(body) == ["messages", "model", "options", "stream"], \
        f"a chat body carries no prompt and no domain artifacts: {sorted(body)}"


def test_an_unexpected_chat_message_shape_is_refused_not_blindly_indexed():
    """The shape tooth, the embed branch's standard applied to chat: a body with no usable
    'message' is REFUSED, never turned into an answer whose text is None travelling as prose."""
    for broken in ({"prompt_eval_count": 1, "eval_count": 1},
                   {"message": "a string, not a turn", "prompt_eval_count": 1, "eval_count": 1},
                   {"message": {"role": "assistant"}, "prompt_eval_count": 1, "eval_count": 1}):
        t = Transport(broken)
        _refuses(lambda: _resolver(t)({"kind": "chat", "messages": _A_TURN}), host.HostRefused,
                 because=f"a chat response shaped {sorted(broken)} cannot yield an answer, and "
                         "indexing into it blindly would make the defect surface as bad prose")


def test_a_malformed_messages_list_never_reaches_the_host():
    """The validation tooth, and the assertion that makes it one: the transport records NOTHING.

    A bare refusal check would not distinguish refused-before-dialing from refused-after. On Hex
    a cold qwen3-coder:30b load is ~18 seconds, so the difference is the whole point of the gate."""
    for bad in ({"kind": "chat"},
                {"kind": "chat", "messages": []},
                {"kind": "chat", "messages": "not a list"},
                {"kind": "chat", "messages": ["not a dict"]},
                {"kind": "chat", "messages": [{"role": "user"}]},
                {"kind": "chat", "messages": [{"content": "no role"}]},
                {"kind": "chat", "messages": [{"role": "user", "content": "   "}]}):
        t = Transport(_REAL_CHAT)
        _refuses(lambda: _resolver(t)(bad), host.BadRequest,
                 because=f"the chat door must refuse {bad!r} before spending anything")
        assert t.urls == [], \
            f"a refused chat request must never have touched the host: {t.urls} for {bad!r}"


def test_the_chat_walk_obeys_the_domains_escalation_rule():
    """THE SECOND FALSIFIER TELL: a fenced domain's chat traffic can never dial a rung outside
    its walk-rule, and the rung it skipped is LOUD in the trace.

    Built on the two-provider fixture and not on the real stacks, because today no non-hex
    provider carries qwen3-coder:30b — a fence with nothing to refuse would look identical to
    a fence that works. The fixture is what lets the tooth actually bite."""
    out, dialed = _domain_walk({"kind": "chat", "messages": _A_TURN, "domain": "narrow"},
                               allow=["p-dear"])
    assert out["provenance"]["provider"] == "p-dear"
    assert out["cost"] == 15 + 2, "the fenced chat answer is still metered from real counters"
    assert not any(u.startswith("http://cheap") for u in dialed), \
        f"a rung outside the walk-rule must never be dialed, chat included: {dialed}"
    assert any("walk-rule" in w for w in out["provenance"]["route_walked"]), \
        "the skipped rung must ride the provenance naming the rule that skipped it"


def test_the_shipped_models_stack_declares_the_chat_verb():
    """The AUTHORED piece, read from the rows that actually ship rather than from a fixture.

    A fixture would prove the sieve; only the real rows prove the DECLARATION. The overlay is
    injected so this stays a read of git-tracked files and never of instance-space.

    WHAT THIS TOOTH IS NO LONGER ALLOWED TO ASSERT, and why it is worth saying here rather
    than leaving as an absence: it used to also assert a ``builder-aider`` row in the domains
    stack — an allow-list fencing that consumer's traffic to hex. The row was removed
    2026-08-16 on Akien's ruling, verbatim: "The inference proxy knows about providers and
    models. it does not understand about consumers. the consumer asks for what it wants.
    period, end of story." A row named for a caller is the caller belonging to a class, which
    is the very shape the domains stack's own authoring ticket forbids (falsifier tell 6:
    rows are FIELD SETS an instance composes, never classes it belongs to).

    So the pin and the fence are not the proxy's to hold. The consumer ASKS — the shim names
    ``qwen3-coder:30b`` and the hex rung when it calls, and asking for exactly that is the
    whole of the safety. What survives here is the half that IS provider-and-model knowledge:
    the model declares which verbs it serves."""
    from cairn.devices.inference_domain.machines.route import route as route_mod
    stacks = route_mod.load_stacks()

    serving_chat = [m["name"] for m in stacks["models"]["models"] if "chat" in (m.get("serves") or [])]
    assert serving_chat == ["qwen3-coder:30b"], \
        f"exactly the pinned model declares it serves chat: {serving_chat}"
    assert "generate" in next(m for m in stacks["models"]["models"]
                              if m["name"] == "qwen3-coder:30b")["serves"], \
        "declaring the new verb must not have cost the model the one it already served"

    # A chat call names its model and rides the ordinary walk — no consumer-shaped domain
    # anywhere in it. The default vertical is what a bare call lands on, unchanged.
    rows = route_mod.domain_rows(stacks)
    assert rows["default"] == "general", "a chat call rides the ordinary default like any other"

    survivors = route_mod.route("chat", "qwen3-coder:30b", stacks=stacks,
                                overlay={"hex": {"endpoint": "http://fixture-hex:11434"}})["survivors"]
    assert [s["provider"] for s in survivors] == ["hex"], \
        f"the named model resolves to the rung that serves it: {survivors}"
    assert survivors[0]["model"] == "qwen3-coder:30b", "and a named model is never substituted"


# ------------------------------------------------- the answer that was never finished

# THE REAL NON-FINAL FRAME, byte-for-byte off the wire. Captured 2026-08-18T06:35Z from hex's
# ollama, n=6: unload qwen3-coder:30b (POST /api/chat with messages [] and keep_alive 0), confirm
# /api/ps empty, then fire four IDENTICAL non-streaming chat asks — every one came back HTTP 200
# carrying exactly this, at 14.2s / 0.1s / 0.1s / 0.1s, with the model resident in /api/ps
# afterwards. 96 bytes. Note what it is NOT: not a timeout (three orders of magnitude inside the
# 120s bound), not a num_ctx effect (six successes at 8192/32768/81920 minutes later), not an
# error (no status >= 400, no "error" key). It is ollama answering a NON-STREAMING request with a
# frame from the STREAMING grammar while the model loads — and the empty-string content is a str,
# so the chat branch's shape check waves it through too.
_REAL_NON_FINAL_CHAT = {"model": "", "created_at": "0001-01-01T00:00:00Z",
                        "message": {"role": "", "content": ""}, "done": False}


def test_a_non_final_answer_is_refused_by_its_own_name():
    """THE TOOTH THIS TICKET EXISTS FOR — and it is written to be UNPASSABLE BY A HOLLOW BUILD.

    HEAD already raises on this body. Measured against unmodified HEAD before a line of the fix
    was written: ``HostUnmetered: the host reported no token counters (looked for
    ['prompt_eval_count', 'eval_count']; response carried ['created_at', 'done', 'message',
    'model'])``. So a tooth asserting merely "some error is raised" goes GREEN on a codebase
    containing no fix at all. That is why this one asserts the TYPE, and why _refuses is the
    right helper: its middle branch says THE GATE DID NOT REFUSE and names what fired instead.

    What the wrong error costs, and it is not tidiness: the message sends the reader to the
    meter. The meter is innocent. The host never answered — and a diagnostic surface that is
    loud about the wrong organ costs more than silence, because silence is investigated and a
    confident wrong answer is followed (Law 7).
    """
    t = Transport(_REAL_NON_FINAL_CHAT)
    _refuses(lambda: _resolver(t)({"kind": "chat", "messages": _A_TURN}), host.HostNonFinal,
             because="a non-streaming ask answered with a NON-FINAL frame got no answer at all, "
                     "and must say so by its own name rather than arriving as a complaint about "
                     "token counters")

    # And the counterpart, on the same verb and the same fixture endpoint: a REAL finished answer
    # is untouched. Without this half the tooth above is satisfied by refusing everything.
    t = Transport(_REAL_CHAT)
    out = _resolver(t)({"kind": "chat", "messages": _A_TURN})
    assert out["answer"]["text"] == "ok", \
        f"a finished answer (done true) passes through unchanged: {out['answer']}"
    assert out["cost"] == 15 + 2, f"and it still meters its own counters: {out['cost']}"


def test_a_response_carrying_no_done_key_at_all_is_left_alone():
    """THE BOUND THE FIX HAD TO BE WRITTEN INSIDE — green before the predicate and green after.

    The obvious predicate is ``body.get("done") is not True``. It is wrong, and wrong in the
    expensive direction: /api/embed's real responses carry NO ``done`` key at all, so that
    predicate refuses every embedding this system has ever taken. Measured while charting:
    ``done`` appears in this 600-line file at exactly two lines, and both are the generate and
    chat fixtures — every embed fixture and every hand-built shape fixture is done-less.

    So the predicate must key on ``done`` PRESENT and not true. This tooth is what stops that
    from being softened back later by someone who sees the embed teeth go red and reaches for
    the smaller diff. It asserts on the REAL captured bodies, because a fixture that invented a
    done-less shape would only prove the inventor knew the rule.
    """
    assert "done" not in _REAL_EMBED, \
        "the real /api/embed response carries no done key — that is the whole hazard"
    assert "done" not in _REAL_EMBEDDINGS_UNMETERED, "nor does the older endpoint's"

    t = Transport(_REAL_EMBED)
    out = _resolver(t)({"kind": "embed", "prompt": "the embedding is the path"})
    assert len(out["answer"]["vector"]) == 768, \
        f"a done-less embed answer is an ORDINARY answer and passes: {sorted(out['answer'])}"
    assert out["cost"] == 9, f"and meters its own prompt_eval_count: {out['cost']}"


# ---------------------------------------------------------------------------------------------
# A TOOL-USING CONVERSATION (ticket 548dd13fb4db). The teeth below are the ones a ONE-SHOT test
# cannot have: the defect they were written against appears only on the SECOND turn, which is
# exactly why the live spike read green and the agent loop did not.
# ---------------------------------------------------------------------------------------------

# The toolset as hermes actually sends it (measured 2026-09-11: 25 of these ride every request;
# one is enough to prove the crossing, and the shape is the OpenAI function schema verbatim).
_A_TOOLSET = [{
    "type": "function",
    "function": {
        "name": "terminal",
        "description": "Run a shell command",
        "parameters": {"type": "object",
                       "properties": {"command": {"type": "string"}},
                       "required": ["command"]},
    },
}]

# A REAL tool-calling response shape: the content is EMPTY because the calls are the content.
_REAL_TOOL_CALL = {
    "model": "qwen3-coder:30b", "created_at": "2026-09-11T00:00:00.000000Z",
    "message": {"role": "assistant", "content": "",
                "tool_calls": [{"function": {"name": "terminal",
                                             "arguments": {"command": "hostname"}}}]},
    "done": True, "done_reason": "stop",
    "prompt_eval_count": 1200, "eval_count": 30,
}

# The SECOND turn's request: what an agent sends back after running the tool. These three turns
# are the shape validated_messages used to refuse outright.
_A_TOOL_USING_CONVERSATION = [
    {"role": "user", "content": "what host am I on?"},
    {"role": "assistant", "content": "",
     "tool_calls": [{"id": "call_1",
                     "function": {"name": "terminal", "arguments": {"command": "hostname"}}}]},
    {"role": "tool", "tool_call_id": "call_1", "content": "akiendelllinux"},
]


def test_a_toolset_crosses_to_the_host_and_a_toolless_chat_is_byte_identical():
    """Both halves in one tooth, because the risk is a pair: carrying the toolset is the
    feature, and NOT perturbing the toolless payload is what keeps every existing chat caller
    asking the same question. An unconditional `tools` key would pass the first half and
    silently fork the cache for everyone else (canonicalize digests every request key)."""
    t = Transport(_REAL_CHAT)
    _resolver(t)({"kind": "chat", "messages": _A_TURN, "tools": _A_TOOLSET})
    body = t.bodies[-1]
    assert body["tools"] == _A_TOOLSET, f"the toolset must cross to the host verbatim: {body}"
    assert sorted(body) == ["messages", "model", "options", "stream", "tools"], \
        f"a tool-carrying chat body carries the toolset and nothing invented: {sorted(body)}"

    t2 = Transport(_REAL_CHAT)
    _resolver(t2)({"kind": "chat", "messages": _A_TURN})
    assert "tools" not in t2.bodies[-1], \
        f"a chat WITHOUT a toolset must send no 'tools' key at all — an empty one is a " \
        f"different question to canonicalize(): {t2.bodies[-1]}"


def test_the_answer_lifts_tool_calls_out_of_the_hosts_message():
    """The calls must reach the caller ON THE ANSWER, because the answer is what resolve()
    STORES and what a cache hit replays. Anything left only in the raw body is dropped forever
    on every hit — and absent (not empty) on a plain chat, so stored answers keep their shape."""
    t = Transport(_REAL_TOOL_CALL)
    out = _resolver(t)({"kind": "chat", "messages": _A_TURN, "tools": _A_TOOLSET})
    assert out["answer"]["tool_calls"] == _REAL_TOOL_CALL["message"]["tool_calls"], \
        f"the host's tool_calls must be lifted onto the answer: {out['answer']}"
    assert out["answer"]["text"] == "", "a tool-calling turn has empty text, and that is not an error"
    assert out["cost"] == 1200 + 30, "a tool-calling answer is metered like any other"

    plain = _resolver(Transport(_REAL_CHAT))({"kind": "chat", "messages": _A_TURN})
    assert "tool_calls" not in plain["answer"], \
        f"a plain chat answer must not grow an empty tool_calls key: {plain['answer']}"


def test_the_second_turn_of_a_tool_using_conversation_reaches_the_host():
    """THE TOOTH THE ONE-SHOT GREEN COULD NOT HAVE. Measured 2026-09-11: the first turn of a
    hermes conversation succeeded against hex.local and the second failed, because the door
    refused the two turns an agent appends — the assistant turn whose content is empty (its
    tool_calls ARE its content) and the tool-result turn. A proof that sends one user turn
    reads green through exactly that defect, which is why this sends THREE."""
    t = Transport(_REAL_CHAT)
    _resolver(t)({"kind": "chat", "messages": _A_TOOL_USING_CONVERSATION, "tools": _A_TOOLSET})
    sent = t.bodies[-1]["messages"]
    assert sent == _A_TOOL_USING_CONVERSATION, \
        f"all three turns of a tool-using conversation must cross verbatim: {sent}"
    assert len(sent) == 3 and sent[1]["content"] == "" and sent[2]["role"] == "tool", \
        "the empty-content assistant turn and the tool-result turn are the two that used to be refused"


def test_the_agent_shapes_are_CHECKED_not_exempted():
    """The gate-health ruling made physics (Akien, 2026-09-11: when a gate reads a component's
    health and that health is the work, "the answer is a second checkable shape, never an
    exemption"). THIS is the tooth that tells the two apart: an exemption can only let things
    THROUGH, so if the new shapes were a hole, every case below would sail past. Each must be
    refused, and refused BEFORE the host is dialed."""
    malformed = [
        ({"role": "tool", "content": "out"},
         "a tool result with no tool_call_id — the model cannot tell which call it answers"),
        ({"role": "user", "tool_call_id": "c1", "content": "out"},
         "a tool result whose role is not 'tool' pairs a result with the wrong speaker"),
        ({"role": "tool", "tool_call_id": "c1", "content": {"not": "a string"}},
         "a tool result whose content is a dict would reach the model through somebody's repr()"),
        ({"role": "user", "content": "",
          "tool_calls": [{"function": {"name": "t", "arguments": {}}}]},
         "only an assistant turn calls tools"),
        ({"role": "assistant", "content": "", "tool_calls": []},
         "an assistant turn with empty content and no calls says nothing at all"),
        ({"role": "assistant", "content": "", "tool_calls": [{"function": {"arguments": {}}}]},
         "a tool call with no function name"),
        ({"role": "assistant", "content": "", "tool_calls": [{"function": {"name": "t"}}]},
         "a tool call whose arguments are missing entirely"),
    ]
    for turn, because in malformed:
        t = Transport(_REAL_CHAT)
        _refuses(lambda t=t, turn=turn: _resolver(t)({"kind": "chat", "messages": [turn]}),
                 host.BadRequest, because=because)
        assert t.urls == [], \
            f"a malformed agent turn must never reach the host ({because}): {t.urls}"


def test_tool_call_arguments_as_a_json_string_are_refused_at_our_own_door():
    """The measured cross-format defect, turned into a LOUD refusal instead of a confusing one.

    OpenAI carries tool-call arguments as a JSON STRING; ollama wants an object and answers a
    string with a complaint about a missing closing brace — after ~18s of cold model load, from
    somebody else's process, on the second turn only. Refusing here costs nothing and names the
    owner of the fix: the shim that speaks the wire format owes the json.loads(), not this door.

    THE REFUSAL IS CHECKED BY ITS REASON, NOT MERELY BY ITS OCCURRENCE — and that is not
    fastidiousness, it is a measured correction. Written the obvious way (assert it raises
    BadRequest) this tooth read GREEN against the pre-build code, because the OLD door happened
    to refuse the same turn for an unrelated reason: the assistant's content was empty. A tooth
    that cannot tell "caught the string arguments" from "tripped over empty content" is a
    coin-toss green, and it would have gone on reading green if this branch were deleted."""
    t = Transport(_REAL_CHAT)
    string_args = [{"role": "assistant", "content": "",
                    "tool_calls": [{"function": {"name": "terminal",
                                                 "arguments": '{"command": "hostname"}'}}]}]
    try:
        _resolver(t)({"kind": "chat", "messages": string_args})
        raise AssertionError(
            "NO REFUSAL AT ALL — tool-call arguments arriving as a JSON string are the OpenAI "
            "wire shape, and forwarding them buys a confusing host error 18 seconds later")
    except host.BadRequest as e:
        said = str(e).lower()
        assert "arguments" in said and "string" in said, (
            "THE REFUSAL FIRED FOR THE WRONG REASON. It must name the ARGUMENTS as the defect; "
            "refusing this turn over its empty content would read identical here while the "
            f"string-argument branch was missing entirely. Got: {e}")
    assert t.urls == [], "the string-argument refusal must happen before the host is dialed"


def test_the_horizon_is_a_construction_policy_and_never_touches_the_request():
    """The agent lane, and the reason it is a FACTORY keyword. A request key would enter
    canonicalize() and fork the cache so the chat and agent callers stopped sharing answers they
    should share; out-of-band, both lanes ask the same question and only the KEEPING differs."""
    default = _resolver(Transport(_REAL_CHAT))({"kind": "chat", "messages": _A_TURN})
    assert default["horizon"] == "", "the default stays no-expiry: a temperature-0 answer does not rot"

    agent = _resolver(Transport(_REAL_CHAT), horizon=host.EXPIRED)(
        {"kind": "chat", "messages": _A_TURN})
    assert agent["horizon"] == host.EXPIRED, \
        f"an agent-lane resolver returns the expired horizon it was built with: {agent['horizon']}"

    # And the request dict is left alone — the canonical key cannot have been perturbed.
    request = {"kind": "chat", "messages": _A_TURN}
    before = json.dumps(request, sort_keys=True)
    _resolver(Transport(_REAL_CHAT), horizon=host.EXPIRED)(request)
    assert json.dumps(request, sort_keys=True) == before, \
        "the horizon policy must not write itself into the request — that would fork the cache"


def test_the_expired_horizon_is_parseable_or_it_means_its_own_opposite():
    """A constant worth a tooth, because getting it wrong FAILS OPEN AND SILENTLY. domain._valid
    treats an unparseable horizon as no-expiry (deliberately — a bad shape should not discard a
    stored answer), so a word like "expired" would cache FOREVER for the one caller who needs no
    caching at all. This asserts the constant against the real reader, not against its name."""
    from datetime import datetime, timezone
    from cairn.devices.inference_domain import domain
    now = datetime.now(timezone.utc)
    assert domain._valid({"horizon": host.EXPIRED}, now) is False, \
        f"EXPIRED must read as EXPIRED to the real validator, not merely look expired: {host.EXPIRED}"
    assert domain._valid({"horizon": ""}, now) is True, "the default horizon still means no expiry"


def _main() -> int:
    checks = [
        test_an_unmetered_response_is_refused_not_metered_as_zero,
        test_the_cost_is_the_sum_of_the_hosts_own_counters,
        test_an_embed_meters_its_input_tokens_alone,
        test_metered_cost_refuses_a_renamed_counter,
        test_embed_uses_api_embed_and_never_the_unmetered_api_embeddings,
        test_temperature_is_pinned_to_zero_and_the_caller_may_override,
        test_an_unknown_kind_is_refused_before_any_host_call,
        test_an_empty_or_missing_prompt_is_refused_before_any_host_call,
        test_the_hosts_own_error_message_is_carried_through_verbatim,
        test_an_unreachable_host_raises_and_never_returns_an_empty_answer,
        test_an_unexpected_embed_shape_is_refused_not_blindly_indexed,
        test_a_generate_with_no_response_field_is_refused,
        test_the_falsifier_names_a_digest_a_machine_can_check,
        test_the_digest_read_goes_through_the_seam_not_around_it,
        test_a_model_named_without_its_implicit_latest_tag_still_gets_a_real_digest,
        test_a_falsifier_survives_an_unreadable_digest_and_says_so,
        test_no_other_module_in_the_tree_opens_the_inference_host,
        test_the_sole_path_tooth_reds_on_a_planted_dialer,
        test_the_outbound_body_wears_the_named_domains_prompt_content,
        test_a_bare_requests_outbound_body_is_byte_for_byte_undressed,
        test_generals_walk_is_todays_walk_exactly,
        test_the_walk_obeys_the_domains_escalation_rule,
        test_a_chat_call_meters_the_hosts_own_counters,
        test_an_unmetered_chat_answer_is_refused_not_metered_as_zero,
        test_chat_opens_api_chat_and_nothing_else,
        test_an_unexpected_chat_message_shape_is_refused_not_blindly_indexed,
        test_a_malformed_messages_list_never_reaches_the_host,
        test_the_chat_walk_obeys_the_domains_escalation_rule,
        test_the_shipped_models_stack_declares_the_chat_verb,
        test_a_toolset_crosses_to_the_host_and_a_toolless_chat_is_byte_identical,
        test_the_answer_lifts_tool_calls_out_of_the_hosts_message,
        test_the_second_turn_of_a_tool_using_conversation_reaches_the_host,
        test_the_agent_shapes_are_CHECKED_not_exempted,
        test_tool_call_arguments_as_a_json_string_are_refused_at_our_own_door,
        test_the_horizon_is_a_construction_policy_and_never_touches_the_request,
        test_the_expired_horizon_is_parseable_or_it_means_its_own_opposite,
        test_a_non_final_answer_is_refused_by_its_own_name,
        test_a_response_carrying_no_done_key_at_all_is_left_alone,
    ]
    for check in checks:
        check()
        print(f"  PASS  {check.__name__}")
    print("green — the host seam meters REAL tokens from the host's own counters or refuses "
          "(never 0), opens /api/embed and never the unmetered /api/embeddings, refuses bad "
          "requests before spending, carries the host's own diagnosis verbatim, hands T1.4 a "
          "digest falsifier a machine can check, and is still the ONLY door to the host")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
