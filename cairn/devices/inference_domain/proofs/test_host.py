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
        "models": {"models": [{"name": "m", "serves": ["generate"]}]},
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
        return 200, json.dumps(_REAL_GENERATE).encode()

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
