"""inference_domain/route.py — the FOURTH STACK: the nest of sieves that lets out the route.

The ruling, verbatim (CairnCommons/decisions/2026-08-08-inference-proxy-is-a-rules-stack.json):
"The fourth 'stack' is the nest. a mesh built of seives that allow out the lowest cost answer.
And the lowest cost answer is NEVER 127.0.0.1."

Three authored stacks live beside this module in ``stacks/`` — providers (costs, connection
handling, enabled+why), models (names, parameters, pros/cons, scores, serves), combos (the
provider/model pairings and their specifics). The machine half — THIS LAN's endpoints, API
keys — lives in ``~/.cairn/inference/hosts.json`` (instance-space, never git; the edge
host.py filed 2026-07-26 closes here). This module composes ``cairn.base.nest`` over the
combos: every sieve is a rule a combo must pass, the shake is one pass coarse-first, and
what survives is ordered cheapest-first for the resolver to dial — the second carrier of
the block-general nest (build_inspector is the first).

A sieve CUTS with a finding that names itself, so "why didn't this route?" is always
answered by the trace, never by silence: an unkeyed cloud rung is listed and loudly
refusing (cut by ``keyed``, the finding says so and names the overlay path where the key
would land), and loopback is cut by ``never_routed`` categorically — the rule is a row a
sieve reads, not a comment (Law 4).

Bands are DERIVED from what each sieve's body reaches (import_sieve.reach_of, the
inspector's precedent) — a hand-set band would be a learned value stranded in a head.
Every sieve here reads data already in hand, so today the nest is one band; that is a
measurement, not a design constraint.
"""

from __future__ import annotations

import json
from pathlib import Path

from cairn.base import nest as base_nest
from cairn.import_sieve import sieve as import_sieve

STACKS_DIR = Path(__file__).resolve().parent / "stacks"
OVERLAY_PATH = Path.home() / ".cairn" / "inference" / "hosts.json"


class RouteRefused(RuntimeError):
    """No combo survived the shake (or the rules themselves are unreadable). Loud, with the
    full sieve trace carried in ``.findings`` — a diagnostic surface delivers ALL the data
    in its first report, never 'no route' alone."""

    def __init__(self, message: str, findings: list | None = None):
        super().__init__(message)
        self.findings = findings or []


def load_stacks(stacks_dir: str | Path | None = None) -> dict:
    """The three authored stacks, loaded and cross-indexed. Refuses loudly on absence —
    a router without its rules must never quietly fall back to a literal (the defect
    this module exists to end)."""
    d = Path(stacks_dir) if stacks_dir else STACKS_DIR
    out = {}
    for name in ("providers", "models", "combos"):
        path = d / f"{name}.json"
        if not path.exists():
            raise RouteRefused(
                f"the {name} stack is missing at {path} — the rules stack routes or nothing "
                "does; there is no literal to fall back to (ruling 2026-08-08)")
        out[name] = json.loads(path.read_text())
    return out


def load_overlay(path: str | Path | None = None) -> dict:
    """The machine half: ``{provider name: {endpoint, api_key?}}`` from instance-space."""
    p = Path(path) if path else OVERLAY_PATH
    if not p.exists():
        raise RouteRefused(
            f"the machine-facts overlay is missing at {p} — endpoints are facts about this "
            "machine, not about the code (three-roots law); write hosts.json there with at "
            "least {'hosts': {'hex': {'endpoint': ...}}} before anything can route")
    return json.loads(p.read_text()).get("hosts", {})


# ---- the sieves. Each fires on one combo VIEW (combo row + its provider/model/host rows)
# and returns findings — empty means the combo passes this mesh. The finding shape names
# the sieve, the combo, and the fix, so the trace answers the operator without a re-run.

def _finding(sieve: str, view: dict, why: str) -> dict:
    return {"sieve": sieve,
            "combo": f"{view['combo']['provider']}/{view['combo']['model']}",
            "why": why}


def enabled(view: dict) -> list:
    """The provider is switched on. OpenRouter sits here: listed, disabled, with Akien's
    why on the row — the stack remembering what a comment would forget."""
    p = view["provider"]
    if not p.get("enabled"):
        return [_finding("enabled", view,
                         f"provider {p['name']!r} is disabled — its row says why: {p.get('why', '(no why recorded)')}")]
    return []


def never_routed(view: dict) -> list:
    """The ruled NEVER: 'the lowest cost answer is NEVER 127.0.0.1.' Categorical — this
    sieve reads the row's standing, not its price, so no cost table can ever let it out."""
    p = view["provider"]
    if p.get("never_route"):
        return [_finding("never_routed", view,
                         f"provider {p['name']!r} is listed never-route: {p.get('why', '(no why recorded)')}")]
    return []


def serves_kind(view: dict) -> list:
    """The model actually serves the requested verb, and a request that names a model
    routes only through that model's combos — the resolver never substitutes an answer
    from a different model (the cache canonicalizes on the request)."""
    m, want = view["model"], view["kind"]
    if m is None:
        return [_finding("serves_kind", view,
                         f"combo names model {view['combo']['model']!r} but the models stack has no such row")]
    if want not in (m.get("serves") or []):
        return [_finding("serves_kind", view,
                         f"model {m['name']!r} serves {m.get('serves')}, not {want!r}")]
    asked = view["requested_model"]
    if asked and m["name"] != asked:
        return [_finding("serves_kind", view,
                         f"the request names model {asked!r}; this combo carries {m['name']!r}")]
    return []


def keyed(view: dict) -> list:
    """A provider that needs a key has one in the overlay. An unkeyed rung is listed and
    loudly refusing — dead until the key lands in instance-space, visible the whole time."""
    p = view["provider"]
    if p.get("needs_key") and not (view["host"] or {}).get("api_key"):
        return [_finding("keyed", view,
                         f"provider {p['name']!r} needs a key and none is set — the rung goes "
                         f"live the day a key lands in {OVERLAY_PATH} (Akien's act, instance-space)")]
    return []


def addressed(view: dict) -> list:
    """The overlay names an endpoint for the provider on THIS machine — a combo without a
    machine address cannot be dialed, however sound its rules."""
    if not (view["host"] or {}).get("endpoint"):
        return [_finding("addressed", view,
                         f"no endpoint for provider {view['provider']['name']!r} in the overlay "
                         f"({OVERLAY_PATH}) — a rule row routes only where a machine fact lands it")]
    return []


SIEVES = {
    "enabled": enabled,
    "never_routed": never_routed,
    "serves_kind": serves_kind,
    "keyed": keyed,
    "addressed": addressed,
}

_NEST_CACHE: list | None = None


def the_nest() -> list:
    """The sieves assembled coarsest-first — bands derived from each sieve's own reach,
    never hand-set (the inspector's the_nest() precedent, and the same one-shake word)."""
    global _NEST_CACHE
    if _NEST_CACHE is None:
        reaches = import_sieve.reach_of(Path(__file__).read_text())
        _NEST_CACHE = base_nest.nest(
            {name: reaches.get(fn.__name__, 0) for name, fn in SIEVES.items()})
    return _NEST_CACHE


def route(kind: str, model: str | None = None, *,
          stacks: dict | None = None, overlay: dict | None = None) -> dict:
    """One shake of the nest over the combos: what may this request dial, cheapest first?

    Returns ``{"survivors": [...], "gradation": ..., "findings": [...]}`` where survivors
    are ``{"provider", "model", "endpoint", "cash_per_mtoken"}`` ordered by authored cost
    (ties keep the combos stack's own order — the author's preference is the tiebreak).
    The resolver dials survivors in order and walks on HostUnreachable: the nest decides
    WHO may be dialed, the walk discovers who ANSWERS — reachability is a per-call fact,
    never a snapshot. No survivors is a loud RouteRefused carrying the full trace."""
    stacks = stacks or load_stacks()
    overlay = overlay if overlay is not None else load_overlay()
    providers = {p["name"]: p for p in stacks["providers"]["providers"]}
    models = {m["name"]: m for m in stacks["models"]["models"]}

    subjects = {}
    for i, combo in enumerate(stacks["combos"]["combos"]):
        p = providers.get(combo["provider"])
        if p is None:
            raise RouteRefused(
                f"combo {combo['provider']}/{combo['model']} names a provider the providers "
                "stack does not carry — the stacks have drifted apart; fix the rules, not the router")
        subjects[f"{i:03d} {combo['provider']}/{combo['model']}"] = {
            "combo": combo, "provider": p, "model": models.get(combo["model"]),
            "host": overlay.get(combo["provider"]), "kind": kind, "requested_model": model,
        }

    shaken = base_nest.shake(the_nest(), subjects,
                             lambda name, view: SIEVES[name](view))
    survivors = []
    for key in sorted(subjects):                      # combos-stack order
        if shaken["roll_up"][key] == 1.0:
            view = subjects[key]
            survivors.append({
                "provider": view["provider"]["name"],
                "protocol": view["provider"].get("protocol", "ollama"),
                "model": view["combo"]["model"],
                "endpoint": view["host"]["endpoint"],
                "cash_per_mtoken": view["provider"].get("cash_per_mtoken"),
            })
    survivors.sort(key=lambda s: s["cash_per_mtoken"])  # stable: ties keep authored order
    if not survivors:
        raise RouteRefused(
            f"no combo survives the nest for kind={kind!r}"
            + (f", model={model!r}" if model else "")
            + " — the trace names what cut each rung: "
            + "; ".join(f"[{f['sieve']}] {f['combo']}: {f['why']}" for f in shaken["findings"]),
            findings=shaken["findings"])
    return {"survivors": survivors, "gradation": shaken["gradation"],
            "findings": shaken["findings"]}
