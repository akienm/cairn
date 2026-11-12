"""Proof: route reads its walk order from the nest (ticket ae6bdf48b76d, outline 11.4.6).

Akien 2026-09-15: "capabilities checked first then the post process picked the cheapest ... if
it's not like that now, that's a bug"; 2026-09-29 (open-8ecde12362d6), option c: the shake
RANKS instead of cutting, and route reads the walk order from the stamps. Measured 2026-11-10:
route shook the nest for cuts only and then sorted the survivors itself (cost, then a domain's
prefers). This proof holds the move: one postprocess sieve, walk_rank, stamps every survivor;
route builds its survivors in the shake's order; nothing sorts after the nest; and the walk a
caller sees is, element for element, what the old sort-and-reorder gave.

The hollow build these teeth catch: a route that still sorts after the shake (tooth 1), a
walk_rank the phase reader puts in the measure band where it would score instead of rank
(tooth 1), an order that drifted from the old one (tooth 2), a rank that cuts (tooth 3), and a
refusal that moved or went quiet (tooth 4).

Hermetic: fixture stacks and a fixture overlay; the authored stacks are read as class-space
files beside the code; the instance overlay is never opened.

    python3 cairn/devices/inference_domain/machines/route/proofs/test_route_reads_its_walk_order_from_the_nest.py
"""

from __future__ import annotations

import ast
import copy
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[6]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.devices.inference_domain.machines.route import route  # noqa: E402
from cairn.machines.nest import nest as base_nest  # noqa: E402

PROVES = {"ae6bdf48b76d": {
    "1": "test_route_sorts_nothing",
    "2": "test_the_walk_order_is_byte_identical",
    "3": "test_the_rank_cuts_nothing",
    "4": "test_the_standing_teeth_hold",
    "5": "test_refusals_unchanged",
}}

_ROUTE_PY = Path(route.__file__)
_STANDING = Path(__file__).resolve().parent / "test_route.py"
_MEASURE = ("enabled", "never_routed", "serves_kind", "keyed", "addressed")

# A fixture world with every case the ticket names: cost ties (two rungs at 0.5, two at 0.0),
# a preferred model that survives, a preferred model whose only rung is cut, a never-route
# rung, an unkeyed rung, an unaddressed rung.
_FIXTURE_STACKS = {
    "providers": {"providers": [
        {"name": "dear", "enabled": True, "cash_per_mtoken": 0.5},
        {"name": "free", "enabled": True, "cash_per_mtoken": 0.0},
        {"name": "dear2", "enabled": True, "cash_per_mtoken": 0.5},
        {"name": "local", "enabled": True, "cash_per_mtoken": 0.0, "never_route": True},
        {"name": "mid", "enabled": True, "cash_per_mtoken": 0.2},
        {"name": "free2", "enabled": True, "cash_per_mtoken": 0.0},
        {"name": "locked", "enabled": True, "cash_per_mtoken": 0.1, "needs_key": True},
        {"name": "off", "enabled": False, "cash_per_mtoken": 0.0},
    ]},
    "models": {"models": [
        {"name": "m-a", "serves": ["generate"]},
        {"name": "m-b", "serves": ["generate"]},
        {"name": "m-pref", "serves": ["generate"]},
        {"name": "m-cut", "serves": ["generate"]},
        {"name": "m-embed", "serves": ["embed"]},
    ]},
    "combos": {"combos": [
        {"provider": "dear", "model": "m-a"},
        {"provider": "dear2", "model": "m-pref"},
        {"provider": "free", "model": "m-b"},
        {"provider": "local", "model": "m-cut"},
        {"provider": "mid", "model": "m-a"},
        {"provider": "free2", "model": "m-a"},
        {"provider": "locked", "model": "m-pref"},
        {"provider": "off", "model": "m-cut"},
        {"provider": "free", "model": "m-embed"},
        {"provider": "dear", "model": "m-pref"},
        {"provider": "free2", "model": "m-pref"},
    ]},
    "domains": {"domains": [
        {"name": "general", "default": True, "why": "w", "prompts": {}, "escalation": {}, "prefers": []},
        {"name": "keen", "why": "w", "prompts": {}, "escalation": {}, "prefers": ["m-pref"]},
        {"name": "lost", "why": "w", "prompts": {}, "escalation": {}, "prefers": ["m-cut"]},
    ]},
}
_FIXTURE_OVERLAY = {name: {"endpoint": f"http://{name}:1"} for name in
                    ("dear", "free", "dear2", "local", "mid", "free2", "locked", "off")}

_AUTHORED_OVERLAY = {
    "hex": {"endpoint": "http://fixture-hex:11434"},
    "loopback": {"endpoint": "http://127.0.0.1:11434"},
    "ollama-cloud": {"endpoint": "https://ollama.com", "api_key": "fixture-key"},
    "gemini": {"endpoint": "https://generativelanguage.googleapis.com", "api_key": "fixture-key"},
}


def _subjects(stacks: dict, overlay: dict, kind: str, model: str | None) -> dict:
    providers = {p["name"]: p for p in stacks["providers"]["providers"]}
    models = {m["name"]: m for m in stacks["models"]["models"]}
    return {f"{i:03d} {c['provider']}/{c['model']}": {
        "combo": c, "provider": providers[c["provider"]], "model": models.get(c["model"]),
        "host": overlay.get(c["provider"]), "kind": kind, "requested_model": model, "prefers": []}
        for i, c in enumerate(stacks["combos"]["combos"])}


def _measure_shake(stacks, overlay, kind, model) -> dict:
    """The measure band alone, shaken over the same subjects: what the old route cut."""
    assembled = base_nest.nest({name: 1 for name in _MEASURE})
    return base_nest.shake(assembled, _subjects(stacks, overlay, kind, model),
                           lambda name, view: route.SIEVES[name](view))


def _frozen_old_walk(stacks, overlay, kind, model, domain) -> list:
    """A FROZEN COPY of the route walk as it stood before this ticket (route.py :293, :301):
    survivors in combos-stack order, a stable sort by cash_per_mtoken, then a stable reorder
    putting the domain's preferred models first. Kept here verbatim in effect, so the new
    order is measured against the old one and not against itself."""
    shaken = _measure_shake(stacks, overlay, kind, model)
    subjects = _subjects(stacks, overlay, kind, model)
    survivors = []
    for key in sorted(subjects):
        if shaken["roll_up"][key] == 1.0:
            v = subjects[key]
            survivors.append({"provider": v["provider"]["name"], "model": v["combo"]["model"],
                              "cash_per_mtoken": v["provider"].get("cash_per_mtoken")})
    survivors.sort(key=lambda s: s["cash_per_mtoken"])
    if domain is not None:
        prefers = route.domain_rows(stacks)["rows"][domain].get("prefers") or []
        survivors.sort(key=lambda s: 0 if s["model"] in prefers else 1)
    return [(s["provider"], s["model"]) for s in survivors]


def _walk(stacks, overlay, kind, model, domain) -> list:
    got = route.route(kind, model, domain=domain, stacks=copy.deepcopy(stacks), overlay=overlay)
    return [(s["provider"], s["model"]) for s in got["survivors"]]


def _cases():
    """(label, stacks, overlay, kind, model, domain) across the fixture world and the authored
    stacks, each with no domain, the general domain, and a preferring one."""
    authored = route.load_stacks()
    coding = [r["name"] for r in authored["domains"]["domains"] if r.get("prefers")]
    out = []
    for domain in (None, "general", "keen", "lost"):
        out.append(("fixture generate", _FIXTURE_STACKS, _FIXTURE_OVERLAY, "generate", None, domain))
        out.append(("fixture one survivor", _FIXTURE_STACKS, _FIXTURE_OVERLAY, "generate", "m-b", domain))
        out.append(("fixture preferred model asked", _FIXTURE_STACKS, _FIXTURE_OVERLAY, "generate", "m-pref", domain))
    for domain in [None, "general", *coding]:
        for kind in ("generate", "embed"):
            out.append((f"authored {kind}", authored, _AUTHORED_OVERLAY, kind, None, domain))
    return out


# ---------------------------------------------------------------------------------- teeth

def test_route_sorts_nothing():
    """Falsifier (1): no .sort( and no sorted( anywhere in route.py, and the phase reader puts
    walk_rank in band 2 (postprocess), derived from what it reads, never hand-set."""
    tree = ast.parse(_ROUTE_PY.read_text())
    sorts = [n.lineno for n in ast.walk(tree) if isinstance(n, ast.Call) and (
        (isinstance(n.func, ast.Attribute) and n.func.attr == "sort")
        or (isinstance(n.func, ast.Name) and n.func.id == "sorted"))]
    assert sorts == [], f"route.py still sorts, at lines {sorts} — the walk order belongs to the nest"
    from cairn.tools.import_sieve import sieve as import_sieve
    phases = import_sieve.phase_of(_ROUTE_PY.read_text())
    assert "walk_rank" in route.SIEVES, f"no walk_rank sieve in the nest: {sorted(route.SIEVES)}"
    assert phases.get("walk_rank") == base_nest.POSTPROCESS, \
        f"walk_rank must derive as postprocess (band {base_nest.POSTPROCESS}); phase_of says {phases.get('walk_rank')}"
    assert dict(route.the_nest()).get(base_nest.POSTPROCESS) == ["walk_rank"], \
        f"the assembled nest must carry walk_rank as its one postprocess sieve: {route.the_nest()}"


def test_the_walk_order_is_byte_identical():
    """Falsifier (2): over every case, route's survivors equal the frozen old walk exactly."""
    checked = 0
    for label, stacks, overlay, kind, model, domain in _cases():
        old = _frozen_old_walk(stacks, overlay, kind, model, domain)
        new = _walk(stacks, overlay, kind, model, domain)
        assert new == old, f"{label} domain={domain} model={model}: walk changed\n old {old}\n new {new}"
        checked += 1
    assert checked >= 18, f"the case table collapsed: {checked}"
    keen = _walk(_FIXTURE_STACKS, _FIXTURE_OVERLAY, "generate", None, "keen")
    assert keen[0][1] == "m-pref" and keen[-1][1] != "m-pref", \
        f"the fixture must exercise a reorder, or tooth 2 proves nothing about preference: {keen}"
    plain = _walk(_FIXTURE_STACKS, _FIXTURE_OVERLAY, "generate", None, None)
    assert plain[:3] == [("free", "m-b"), ("free2", "m-a"), ("free2", "m-pref")], \
        f"cost ties must keep the combos stack's order: {plain}"


def test_the_rank_cuts_nothing():
    """Falsifier (3): the survivors are exactly the subjects the measure band rolls up to 1.0."""
    for label, stacks, overlay, kind, model, domain in _cases():
        shaken = _measure_shake(stacks, overlay, kind, model)
        subjects = _subjects(stacks, overlay, kind, model)
        want = {(subjects[k]["provider"]["name"], subjects[k]["combo"]["model"])
                for k, up in shaken["roll_up"].items() if up == 1.0}
        got = set(_walk(stacks, overlay, kind, model, domain))
        assert got == want, f"{label} domain={domain}: the rank changed the set: {got ^ want}"


def test_the_standing_teeth_hold():
    """Falsifier (4): every tooth in test_route.py passes unchanged, the walk teeth included —
    its own main(), in its own process, so nothing this proof patched leaks into it."""
    done = subprocess.run([sys.executable, str(_STANDING)], capture_output=True, text=True,
                          timeout=240, cwd=str(_REPO_ROOT))
    assert done.returncode == 0, f"test_route.py red (exit {done.returncode}):\n{done.stdout[-2000:]}\n{done.stderr[-2000:]}"
    passed = done.stdout.count("PASS")
    assert passed >= 16, f"test_route.py ran {passed} teeth; its own floor is 16:\n{done.stdout[-1500:]}"


def test_refusals_unchanged():
    """Falsifier (5): every rung cut → RouteRefused naming each cut; an unknown domain refuses
    before the shake ever runs."""
    try:
        route.route("generate", "m-cut", stacks=copy.deepcopy(_FIXTURE_STACKS), overlay=_FIXTURE_OVERLAY)
    except route.RouteRefused as e:
        assert "[never_routed] local/m-cut" in str(e) and "[enabled] off/m-cut" in str(e), \
            f"the refusal must name each cut: {e}"
        assert e.findings, "the refusal must carry the findings"
    else:
        raise AssertionError("every rung cut, and route did not refuse")

    shaken = []
    saved = base_nest.shake
    base_nest.shake = lambda *a, **k: shaken.append(1) or saved(*a, **k)
    try:
        try:
            route.route("generate", None, domain="nowhere",
                        stacks=copy.deepcopy(_FIXTURE_STACKS), overlay=_FIXTURE_OVERLAY)
        except route.RouteRefused as e:
            assert "nowhere" in str(e), f"the refusal must name the domain: {e}"
        else:
            raise AssertionError("an unknown domain routed")
    finally:
        base_nest.shake = saved
    assert shaken == [], "an unknown domain must refuse before the shake, not after it"


def _main() -> int:
    checks = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    assert sorted(c.__name__ for c in checks) == sorted(PROVES["ae6bdf48b76d"].values()), f"the derived roster changed: {len(checks)}"
    failed = []
    for check in checks:                    # the house runner: every tooth runs and is said
        try:
            check()
        except Exception as exc:  # noqa: BLE001 — a tooth that cannot run is a red, loudly
            failed.append(check.__name__)
            print(f"  FAIL  {check.__name__}: {type(exc).__name__}: {exc}")
        else:
            print(f"  PASS  {check.__name__}")
    if failed:
        print(f"RED — {len(failed)} of {len(checks)} teeth failed: {', '.join(failed)}")
        return 1
    print("green — route sorts nothing, walk_rank ranks inside the nest as its one postprocess "
          "sieve, the walk is the old sort-and-reorder element for element, the rank cuts "
          "nothing, test_route.py holds, and the refusals stand")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
