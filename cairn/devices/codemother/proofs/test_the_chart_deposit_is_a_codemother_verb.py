"""Proof for ticket e8fe361a5b2f — depositing a berthed chart packet is codemother acting, so
codemother answers it on the bus, and the chart skill asks instead of running her machines.

RULE 1 (Akien, 2026-10-01): every component talks to every other only through its public
interface, and a device's is the bus. Measured before the build: skills/chart/live.py imported
eight of codemother's machines to land berths in the chart trees, and librarian's code to embed.

One tooth per numbered falsifier clause, over the LIVE system (invariants, never snapshots):

  1. THE SKILL HOLDS NO REACH. No encapsulation_breaches row comes from skills/chart/live.py.
  2. CODEMOTHER ANSWERS. CodeMotherDevice's verb menu carries 'deposit' and 'drain', and a
     deposit without a berth, or naming a berth not on disk, is refused (accepted False).
  3. THE CODE MOVED, ONCE. cairn/devices/codemother/deposit.py defines deposit_berth,
     deposit_verdict and drain_pending and imports nothing of librarian's; live.py defines
     neither of the last two and calls no deposit_<stage> function.
  4. A REAL DEPOSIT RIDES THE BUS. Over reach('codemother', 'inference_domain'), a deposit
     request for the newest berthed orient packet into a scratch nexus (a table that cannot
     outlive this process — the testing mark) replies accepted with that nexus and a node.

    python3 cairn/devices/codemother/proofs/test_the_chart_deposit_is_a_codemother_verb.py   # exit 0 = green
"""
import ast
import glob
import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"e8fe361a5b2f": {"1": "the_skill_holds_no_reach",
                           "2": "codemother_answers_deposit_and_drain",
                           "3": "the_code_moved_once",
                           "4": "a_real_deposit_rides_the_bus"}}

LIVE = _REPO_ROOT / "skills" / "chart" / "live.py"
DEPOSIT = _REPO_ROOT / "cairn" / "devices" / "codemother" / "deposit.py"
SENDER = "testing-e8fe361a5b2f-proof"

PASS = 0
FAIL = 0


def _tooth(name, fn):
    global PASS, FAIL
    try:
        fn()
    except Exception as exc:  # noqa: BLE001 — a proof reports, never hides
        FAIL += 1
        print(f"  RED   {name}: {type(exc).__name__}: {exc}")
    else:
        PASS += 1
        print(f"  green {name}")


def _rel(path) -> str:
    p = Path(path)
    return str(p.relative_to(_REPO_ROOT)) if p.is_absolute() else str(p)


def the_skill_holds_no_reach():
    from cairn.machines.build_inspector.inspector import encapsulation_breaches
    rows = [b for b in encapsulation_breaches(str(_REPO_ROOT))
            if _rel(b["file"]) == "skills/chart/live.py"]
    assert not rows, f"{len(rows)} reach(es) from skills/chart/live.py: " + \
        "; ".join(f":{b['line']} -> {b['module']}" for b in rows[:10])


def _device():
    from cairn.devices.codemother.shim import CodeMotherDevice
    return CodeMotherDevice(bus=None)


def codemother_answers_deposit_and_drain():
    verbs = _device().declared_verbs()
    missing = [v for v in ("deposit", "drain") if v not in verbs]
    assert not missing, f"codemother declares no {missing}: {sorted(verbs)}"
    for body in ({}, {"berth": "/nonexistent/testing-e8fe-orient.json"}):
        got = verbs["deposit"]({"sender": SENDER, "verb": "deposit", "body": body})
        assert isinstance(got, dict) and got.get("accepted") is False, \
            f"deposit {body} was not refused: {got}"


def _tree(path: Path):
    return ast.parse(path.read_text(encoding="utf-8"))


def the_code_moved_once():
    assert DEPOSIT.is_file(), f"{_rel(DEPOSIT)} does not exist"
    dep = _tree(DEPOSIT)
    defined = {n.name for n in dep.body if isinstance(n, ast.FunctionDef)}
    lacking = [n for n in ("deposit_berth", "deposit_verdict", "drain_pending") if n not in defined]
    assert not lacking, f"deposit.py does not define {lacking}"
    lib = [m for n in ast.walk(dep)
           for m in ([a.name for a in n.names] if isinstance(n, ast.Import)
                     else [n.module or ""] if isinstance(n, ast.ImportFrom) else [])
           if m.startswith("cairn.devices.librarian")]
    assert not lib, f"deposit.py imports librarian's code: {lib}"
    live = _tree(LIVE)
    still = [n.name for n in live.body if isinstance(n, ast.FunctionDef)
             and n.name in ("deposit_verdict", "drain_pending")]
    calls = sorted({n.func.id for n in ast.walk(live) if isinstance(n, ast.Call)
                    and isinstance(n.func, ast.Name) and n.func.id.startswith("deposit_")})
    assert not still and not calls, \
        f"live.py still holds the deposit: defines {still}, calls {calls}"


def a_real_deposit_rides_the_bus():
    from cairn.tools.bus_client import reach
    from cairn.tools.chain.grammar import INSTANCE_DIR
    from cairn.tools.tree.tree import scratch_nexus
    packets = sorted(glob.glob(os.path.join(INSTANCE_DIR, "orient-*.json")))
    assert packets, f"no berthed orient packet under {INSTANCE_DIR} to deposit"
    berth = packets[-1]
    bus = reach("codemother", "inference_domain")
    with scratch_nexus("testing_e8fe") as nexus:
        reply = bus.request(sender=SENDER, to="codemother", verb="deposit",
                            why="testing: e8fe361a5b2f proof deposits into a scratch nexus",
                            body={"berth": berth, "nexus": nexus})
        body = (reply or {}).get("body") or {}
        assert body.get("accepted") is True, f"codemother did not accept the deposit: {reply}"
        assert body.get("nexus") == nexus, f"landed in {body.get('nexus')!r}, not {nexus!r}"
        learned = body.get("learn") or {}
        assert learned.get("id") or learned.get("node_id") or learned.get("node_ids"), \
            f"the reply names no node: {body}"


TEETH = [the_skill_holds_no_reach, codemother_answers_deposit_and_drain, the_code_moved_once,
         a_real_deposit_rides_the_bus]

if __name__ == "__main__":
    for fn in TEETH:
        _tooth(fn.__name__, fn)
    print(f"{PASS} passed, {FAIL} failed out of {PASS + FAIL}")
    sys.exit(1 if FAIL else 0)
