"""Proof: the RULES STACK routes (cairn/devices/inference_domain/route.py + stacks/), or refuses loudly.

The ruling (2026-08-08-inference-proxy-is-a-rules-stack): providers, models, combos, and a nest
of sieves letting out the lowest-cost route — "And the lowest cost answer is NEVER 127.0.0.1."
The hollow build these teeth exist to catch is a router that LOOKS like the ruled shape while
routing on something else: stacks present but content-drifted, loopback let out when it is the
only rung standing, an unkeyed cloud rung silently dialed, a walk that retries a host's own
refusal elsewhere and hands back a different model's answer under the same cache key.

Hermetic: the AUTHORED stacks are class-space files beside the code, so reading them here reads
the code — but the machine overlay is instance-space and is NEVER read in a proof; every route()
call below gets a fixture overlay injected, and every dialed rung an injected transport. The
live measurement against real Hex is the validation's separate, deliberate act.

    python3 cairn/devices/inference_domain/proofs/test_route.py     # exit 0 = green, no host, no ~/.cairn
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.devices.inference_domain import host, route

# The machine half, as a FIXTURE mirroring ~/.cairn/devices/inference_domain/0/hosts.json's shape — endpoints are
# this-LAN facts and a sealed proof owns none, so it fabricates them and never opens the real one.
_FIXTURE_OVERLAY = {
    "hex": {"endpoint": "http://fixture-hex:11434"},
    "loopback": {"endpoint": "http://127.0.0.1:11434"},
    "ollama-cloud": {"endpoint": "https://ollama.com", "api_key": None},
    "gemini": {"endpoint": "https://generativelanguage.googleapis.com", "api_key": None},
}

# A real metered generate body (captured 2026-07-26) for the walk teeth — the walk hands the
# request to the single-host resolver, whose meter gate needs real-shaped counters to pass.
_REAL_GENERATE = {"model": "m", "response": "ok", "done": True,
                  "prompt_eval_count": 32, "eval_count": 3}


def _refuses(fn, exc, because):
    try:
        fn()
    except exc as e:
        return e
    except Exception as e:  # noqa: BLE001 — the diagnostic IS the point
        raise AssertionError(
            f"THE GATE DID NOT REFUSE — {because}. Instead: {type(e).__name__}: {e}") from None
    raise AssertionError(f"NO REFUSAL AT ALL — {because}.")


# ---------------------------------------------------------------- the stacks carry the ruling

def test_the_three_stacks_carry_the_ruled_rows_by_content():
    """The ruled rows asserted by CONTENT, not by the files existing. A stack whose rows drift
    from the ruling routes on something other than what Akien ruled — and file-exists teeth
    would stay green the whole way down."""
    stacks = route.load_stacks()
    providers = {p["name"]: p for p in stacks["providers"]["providers"]}

    hex_row = providers["hex"]
    assert hex_row["enabled"] and not hex_row.get("needs_key") and hex_row["cash_per_mtoken"] == 0.0, \
        "hex is the ruled usual route: enabled, keyless, marginal cash zero"
    assert providers["ollama-cloud"]["needs_key"] and providers["ollama-cloud"]["enabled"], \
        "ollama-cloud is the first failover: enabled, and dead only for want of a key"
    gm = providers["gemini"]
    assert gm["needs_key"] and gm["enabled"] and gm["protocol"] == "gemini", \
        "gemini is the second failover, and its protocol row is what stops an ollama-shaped dial"
    orr = providers["openrouter"]
    assert orr["enabled"] is False and "cash" in orr["why"], \
        "openrouter is OFF and its row remembers why (Akien: bugs kept sucking up all the cash)"
    lb = providers["loopback"]
    assert lb.get("never_route") is True and "NEVER 127.0.0.1" in lb["why"], \
        "loopback carries the ruled NEVER as a row a sieve reads, not as a comment"

    models = {m["name"]: m for m in stacks["models"]["models"]}
    assert models["qwen2.5:7b"]["serves"] == ["generate"], "the librarian's standing default serves generate"
    nomic = models["nomic-embed-text"]
    assert nomic["serves"] == ["embed"] and "only to train graph trees" in nomic["duty_bound"], \
        "nomic serves embed alone and carries Akien's duty bound verbatim"

    combos = stacks["combos"]["combos"]
    hex_models = {c["model"] for c in combos if c["provider"] == "hex"}
    assert {"qwen2.5:7b", "nomic-embed-text", "llama3.2:3b"} <= hex_models, \
        "the live callers' models all have a hex road"
    assert all(c["provider"] in providers for c in combos), \
        "every combo names a provider the providers stack carries — the stacks have not drifted apart"


def test_missing_rules_or_overlay_refuse_loudly_naming_the_path():
    """A router without its rules must never quietly fall back to a literal — the defect the
    ruling exists to end. Both refusals must NAME the missing path (complete diagnostic)."""
    gone = Path("/nonexistent-cairn-fixture")
    e = _refuses(lambda: route.load_stacks(gone), route.RouteRefused,
                 "missing stacks must refuse, not default")
    assert str(gone) in str(e), f"the refusal must name where the rules were expected: {e}"
    e = _refuses(lambda: route.load_overlay(gone / "hosts.json"), route.RouteRefused,
                 "a missing overlay must refuse, not invent an endpoint")
    assert "hosts.json" in str(e), f"the refusal must name the overlay path: {e}"


# ---------------------------------------------------------------- the shake

def test_hex_survives_the_shake_for_both_verbs_and_is_cheapest_first():
    for kind, model in (("generate", "qwen2.5:7b"), ("embed", "nomic-embed-text")):
        plan = route.route(kind, model, stacks=route.load_stacks(), overlay=_FIXTURE_OVERLAY)
        assert [s["provider"] for s in plan["survivors"]] == ["hex"], \
            f"{kind}/{model}: with clouds unkeyed, hex must be the sole survivor, got {plan['survivors']}"
        assert plan["survivors"][0]["endpoint"] == "http://fixture-hex:11434", \
            "the survivor's endpoint comes from the overlay, never a literal"


def test_loopback_and_unkeyed_rungs_are_cut_and_the_trace_says_by_what():
    plan = route.route("generate", "qwen2.5:7b",
                       stacks=route.load_stacks(), overlay=_FIXTURE_OVERLAY)
    cuts = {(f["sieve"], f["combo"]) for f in plan["findings"]}
    assert ("never_routed", "loopback/qwen2.5:7b") in cuts, \
        "loopback must be cut BY the never_routed sieve — the categorical rule, named in the trace"
    assert ("keyed", "ollama-cloud/qwen2.5:7b") in cuts, \
        "the unkeyed cloud rung must be cut by keyed, listed and loudly refusing"
    assert all(s["provider"] not in ("loopback", "openrouter") for s in plan["survivors"])


def test_loopback_never_survives_even_as_the_last_rung_standing():
    """The ruled NEVER is categorical: an overlay where loopback is the ONLY addressed provider
    still routes NOTHING. A 'last resort' loopback would be the lived symptom (the 100s CPU
    generate) sneaking back in exactly when the system is most tempted."""
    only_loopback = {"loopback": {"endpoint": "http://127.0.0.1:11434"}}
    e = _refuses(lambda: route.route("generate", "qwen2.5:7b",
                                     stacks=route.load_stacks(), overlay=only_loopback),
                 route.RouteRefused, "loopback as sole addressed rung must still refuse")
    assert "never" in str(e).lower(), f"the trace must show the categorical cut: {e}"


def test_a_request_for_an_unserved_kind_or_foreign_model_routes_nothing():
    _refuses(lambda: route.route("generate", "nomic-embed-text",
                                 stacks=route.load_stacks(), overlay=_FIXTURE_OVERLAY),
             route.RouteRefused, "nomic serves embed only — a generate through it must refuse")
    _refuses(lambda: route.route("embed", "some-model-nobody-authored",
                                 stacks=route.load_stacks(), overlay=_FIXTURE_OVERLAY),
             route.RouteRefused, "a model with no combo row has no road — refuse, never guess one")


def test_the_nest_is_the_general_nest_not_a_private_copy():
    """The route is the SECOND CARRIER of cairn.tools.base.nest (build_inspector is the first) — read
    from the AST, the same way the does_the_gradation_find_a_reader probe counts carriers, so
    this tooth going green is that watch's cleared condition made physics here."""
    tree = ast.parse((Path(route.__file__)).read_text(encoding="utf-8"))
    carried = any(
        (isinstance(n, ast.ImportFrom) and n.module == "cairn.tools.base"
         and any(a.name == "nest" for a in n.names))
        or (isinstance(n, ast.ImportFrom) and n.module == "cairn.tools.base.nest")
        or (isinstance(n, ast.Import) and any(a.name == "cairn.tools.base.nest" for a in n.names))
        for n in ast.walk(tree))
    assert carried, "route.py must IMPORT cairn.tools.base.nest — a private shake would be the reified copy"
    bands = route.the_nest()
    assert sorted(n for _, names in bands for n in names) == sorted(route.SIEVES), \
        "every sieve is in the assembled nest — a sieve authored but not nested never fires"


# ---------------------------------------------------------------- the walk (failover, injected)

def _walk_fixture(cheap_answers: bool, dear_answers: bool):
    """Two FAKE providers (never the real unkeyed cloud rungs — keying those in a fixture would
    proof-pass a configuration the world doesn't have): p-cheap at 0.1, p-dear at 0.2, both
    ollama-protocol and addressed, so cost order is the walk order and the transport decides
    who answers."""
    stacks = {
        "providers": {"providers": [
            {"name": "p-cheap", "protocol": "ollama", "cash_per_mtoken": 0.1, "enabled": True},
            {"name": "p-dear", "protocol": "ollama", "cash_per_mtoken": 0.2, "enabled": True},
        ]},
        "models": {"models": [{"name": "m", "serves": ["generate"]}]},
        "combos": {"combos": [{"provider": "p-cheap", "model": "m"},
                              {"provider": "p-dear", "model": "m"}]},
    }
    overlay = {"p-cheap": {"endpoint": "http://cheap:11434"},
               "p-dear": {"endpoint": "http://dear:11434"}}
    dialed: list[str] = []

    def transport(url, body, timeout):
        dialed.append(url)
        up = cheap_answers if url.startswith("http://cheap") else dear_answers
        if not up:
            raise host.HostUnreachable(f"nobody home at {url}")
        import json as _json
        return 200, _json.dumps(_REAL_GENERATE).encode()

    r = host.ollama_resolver(model="m", stacks=stacks, overlay=overlay,
                             transport=transport, get=lambda u, t: (200, b'{"models": []}'))
    return r, dialed


def test_the_walk_dials_the_second_rung_when_the_first_is_unreachable():
    r, dialed = _walk_fixture(cheap_answers=False, dear_answers=True)
    out = r({"kind": "generate", "prompt": "x"})
    assert out["provenance"]["provider"] == "p-dear", "the walk must reach the second survivor"
    assert out["provenance"]["host"] == "http://dear:11434"
    assert any("p-cheap" in w for w in out["provenance"]["route_walked"]), \
        "a walked-past rung must ride the provenance — silence about the fall-over hides the outage"
    assert any(u.startswith("http://cheap") for u in dialed), \
        "cheapest is dialed FIRST — a walk that skips straight to the dear rung pays for nothing"


def test_a_hosts_own_refusal_is_carried_not_retried_elsewhere():
    """HostRefused is the host ANSWERING. Retrying it on the next rung would hand back a
    different model's answer under the same cache key — the walk walks on unreachability only."""
    dialed2: list[str] = []

    def refusing_transport(url, body, timeout):
        dialed2.append(url)
        import json as _json
        return 200, _json.dumps({"error": "model 'm' not found"}).encode()

    rr = host.ollama_resolver(
        model="m",
        stacks={"providers": {"providers": [
                    {"name": "p-cheap", "protocol": "ollama", "cash_per_mtoken": 0.1, "enabled": True},
                    {"name": "p-dear", "protocol": "ollama", "cash_per_mtoken": 0.2, "enabled": True}]},
                "models": {"models": [{"name": "m", "serves": ["generate"]}]},
                "combos": {"combos": [{"provider": "p-cheap", "model": "m"},
                                      {"provider": "p-dear", "model": "m"}]}},
        overlay={"p-cheap": {"endpoint": "http://cheap:11434"},
                 "p-dear": {"endpoint": "http://dear:11434"}},
        transport=refusing_transport, get=lambda u, t: (200, b'{"models": []}'))
    try:
        rr({"kind": "generate", "prompt": "x"})
    except host.HostRefused as e:
        assert "not found" in str(e), f"the host's own diagnosis must survive the walk: {e}"
    else:
        raise AssertionError("a host error body was treated as an answer by the routed walk")
    posts = [u for u in dialed2 if "/api/generate" in u]
    assert len(posts) == 1 and posts[0].startswith("http://cheap"), \
        f"the refusal must NOT be retried on the dear rung — dialed {posts}"


def test_an_exhausted_walk_raises_naming_every_rung_it_tried():
    r, _ = _walk_fixture(cheap_answers=False, dear_answers=False)
    e = _refuses(lambda: r({"kind": "generate", "prompt": "x"}), host.HostUnreachable,
                 "a walk with no rung answering must raise, never hand back a hollow answer")
    assert "p-cheap" in str(e) and "p-dear" in str(e), \
        f"the exhaustion diagnosis must name every rung walked, in one report: {e}"


def test_a_protocol_without_a_transport_is_walked_past_loudly_never_dialed():
    stacks = {
        "providers": {"providers": [
            {"name": "g", "protocol": "gemini", "cash_per_mtoken": 0.0, "enabled": True},
            {"name": "p", "protocol": "ollama", "cash_per_mtoken": 0.1, "enabled": True},
        ]},
        "models": {"models": [{"name": "m", "serves": ["generate"]}]},
        "combos": {"combos": [{"provider": "g", "model": "m"}, {"provider": "p", "model": "m"}]},
    }
    overlay = {"g": {"endpoint": "https://g.example"}, "p": {"endpoint": "http://p:11434"}}
    dialed = []

    def transport(url, body, timeout):
        dialed.append(url)
        import json as _json
        return 200, _json.dumps(_REAL_GENERATE).encode()

    r = host.ollama_resolver(model="m", stacks=stacks, overlay=overlay,
                             transport=transport, get=lambda u, t: (200, b'{"models": []}'))
    out = r({"kind": "generate", "prompt": "x"})
    assert out["provenance"]["provider"] == "p" and not any("g.example" in u for u in dialed), \
        "a gemini-protocol rung must never be dialed with an ollama-shaped request"
    assert any("no transport for protocol" in w for w in out["provenance"]["route_walked"]), \
        "walking past a protocol must be loud in provenance — a silent skip hides the missing transport"


# ---------------------------------------------------------------- the domains: the fourth stack

def test_the_domains_stack_carries_the_ruled_verticals_by_content():
    """The fourth authored stack (ticket the-domain-carries-the-inference-side), by CONTENT:
    rows general/coding/research, general the one default riding bare calls, rows as
    complete FIELD SETS the loader validates.

    THE EQUALITY IS THE POINT AND IT STAYS AN EQUALITY. On 2026-08-16 this tooth went red
    because the chat-verb build had authored a fourth row, ``builder-aider`` — a row named
    for a CONSUMER. The red was correct and the build was wrong, and the first reading of
    it here was that the assertion had become a stale snapshot to loosen. That reading was
    the plaster the deterministic-red rule exists to stop: an equality over an authored set
    is not a snapshot, it is the statement that these three ARE the set.

    Akien's ruling, 2026-08-16, verbatim: "The inference proxy knows about providers and
    models. it does not understand about consumers. the consumer asks for what it wants.
    period, end of story." So no consumer ever earns a row here, and this equality is what
    says so in a form that reds instead of arguing.
    """
    table = route.domain_rows(route.load_stacks())
    assert set(table["rows"]) == {"general", "coding", "research"}
    assert table["default"] == "general", "a bare call rides general — the ruled default"
    assert table["rows"]["general"]["prompts"]["generate"] == "", \
        "general adds NOTHING by design — the default is a row, not a dressing"
    assert table["rows"]["research"]["prompts"]["generate"], \
        "research carries a real dressing — the librarian's vertical is not an empty label"


def _preference_fixture(prefers):
    """Two models on two rungs, cheapest-first order m-cheap then m-dear; a fixture domain
    whose ``prefers`` is under test, and a PREFERRED loopback rung that never_routed must
    still cut (preference must never outrank a sieve)."""
    return {
        "providers": {"providers": [
            {"name": "p-cheap", "protocol": "ollama", "cash_per_mtoken": 0.1, "enabled": True},
            {"name": "p-dear", "protocol": "ollama", "cash_per_mtoken": 0.2, "enabled": True},
            {"name": "loop", "protocol": "ollama", "cash_per_mtoken": 0.0, "enabled": True,
             "never_route": True, "why": "the ruled NEVER 127.0.0.1"},
        ]},
        "models": {"models": [{"name": "m-cheap", "serves": ["generate"]},
                              {"name": "m-dear", "serves": ["generate"]}]},
        "combos": {"combos": [{"provider": "p-cheap", "model": "m-cheap"},
                              {"provider": "p-dear", "model": "m-dear"},
                              {"provider": "loop", "model": "m-dear"}]},
        "domains": {"domains": [
            {"name": "general", "default": True, "why": "fixture default",
             "prompts": {"generate": ""}, "escalation": {}, "prefers": []},
            {"name": "particular", "default": False, "why": "fixture vertical",
             "prompts": {"generate": ""}, "escalation": {}, "prefers": prefers},
        ]},
    }


_PREF_OVERLAY = {"p-cheap": {"endpoint": "http://cheap:11434"},
                 "p-dear": {"endpoint": "http://dear:11434"},
                 "loop": {"endpoint": "http://127.0.0.1:11434"}}


def test_a_preference_reorders_survivors_without_changing_the_set():
    """The nest keeps the shake (hypothesize falsifier): same stacks with and without the
    preference — survivor SET identical, order alone moves, and no cut is outranked (the
    preferred loopback rung stays cut by never_routed)."""
    plain = route.route("generate", None, stacks=_preference_fixture(["m-dear"]),
                        overlay=_PREF_OVERLAY)
    preferred = route.route("generate", None, domain="particular",
                            stacks=_preference_fixture(["m-dear"]), overlay=_PREF_OVERLAY)
    key = lambda s: (s["provider"], s["model"])
    assert sorted(map(key, plain["survivors"])) == sorted(map(key, preferred["survivors"])), \
        "a preference must never change the survivor SET — a soft input became a hard cut"
    assert [s["model"] for s in plain["survivors"]] == ["m-cheap", "m-dear"], \
        "without a preference the order is cheapest-first, byte-identical to today's"
    assert [s["model"] for s in preferred["survivors"]] == ["m-dear", "m-cheap"], \
        "the preferred model sorts ahead — an ordering the walk then dials"
    assert not any(s["provider"] == "loop" for s in preferred["survivors"]), \
        "never_routed still cuts a rung carrying the preferred model — no preference outranks a sieve"


def test_an_empty_preference_leaves_the_order_untouched():
    """The default vertical (prefers []) shakes byte-identical to no domain at all."""
    bare = route.route("generate", None, stacks=_preference_fixture([]), overlay=_PREF_OVERLAY)
    general = route.route("generate", None, domain="general",
                          stacks=_preference_fixture([]), overlay=_PREF_OVERLAY)
    assert bare["survivors"] == general["survivors"], \
        "general must be indistinguishable from a bare shake — the default adds nothing"


def _main() -> int:
    checks = [
        test_the_three_stacks_carry_the_ruled_rows_by_content,
        test_the_domains_stack_carries_the_ruled_verticals_by_content,
        test_a_preference_reorders_survivors_without_changing_the_set,
        test_an_empty_preference_leaves_the_order_untouched,
        test_missing_rules_or_overlay_refuse_loudly_naming_the_path,
        test_hex_survives_the_shake_for_both_verbs_and_is_cheapest_first,
        test_loopback_and_unkeyed_rungs_are_cut_and_the_trace_says_by_what,
        test_loopback_never_survives_even_as_the_last_rung_standing,
        test_a_request_for_an_unserved_kind_or_foreign_model_routes_nothing,
        test_the_nest_is_the_general_nest_not_a_private_copy,
        test_the_walk_dials_the_second_rung_when_the_first_is_unreachable,
        test_a_hosts_own_refusal_is_carried_not_retried_elsewhere,
        test_an_exhausted_walk_raises_naming_every_rung_it_tried,
        test_a_protocol_without_a_transport_is_walked_past_loudly_never_dialed,
    ]
    for check in checks:
        check()
        print(f"  PASS  {check.__name__}")
    print("green — the stacks carry the ruled rows by content, the nest cuts loopback "
          "categorically (even as the last rung standing) and unkeyed rungs loudly, hex "
          "survives both verbs cheapest-first, and the walk fails over on unreachability "
          "only — never retrying a host's own refusal, never dialing a protocol it has no "
          "transport for")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
