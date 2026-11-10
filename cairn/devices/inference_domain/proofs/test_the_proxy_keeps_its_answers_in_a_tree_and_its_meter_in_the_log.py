"""Proof for ticket 98ab0e9db57f — the inference proxy keeps its answers in a tree and its meter
in metrics.

Outline 11.4.4 (Akien 2026-11-05/09): the proxy's one append-only table was both the compiled
answers and the meter. The answers move to a keyed tree the proxy owns (no embedding, found by
the request's digest — the trees tool's keyed leaf, ticket e62f40f35f59); the meter is the
metrics rows each call records (ticket 0615d8cdc998), read back through the cairn device's
``metrics`` bus verb; the calls are the task tickets in the logs tree; a one-shot migration
carries the stored answers and the historical meter across, then the table drops.

One tooth per numbered falsifier clause:

  1. No non-proof module under the device, other than the migration, names the old table.
  2. A repeat is served from the scratch answer tree: verdict hit, same answer, resolver once.
  3. An answer past its horizon is not served; the resolver is called again.
  4. yield_report over a known metrics reply returns its spent/avoided sums and its
     hit/miss/refused counts, asking the cairn device's metrics verb (never importing it).
  5. The calls verb over a scratch logs tree returns tickets newest first, bounded by limit,
     carrying canonical, created, verdict and answer; ``since`` drops the older.
  6. The migration over a scratch table carries one answer per still-valid canonical, meters
     each pre-meter row once; a second run writes nothing; a forced mismatch drops nothing and
     exits non-zero; no dump, no drop.
  7. LIVE, read-only, after the migration: the old table is gone, the answer tree is owned by
     inference_domain with at least 11,366 leaves, the dump exists, and the metrics rows up to
     the dump's newest row sum to the dump's spent and avoided.
  8. The median of 100 tree lookups is no more than 3x the median of 100 old-shape table reads.
  9. Every other proof under cairn/devices/inference_domain stays green.

Requires the db_domain provisioning; every table here is scratch, and every scratch tree's
nodes are forgotten before it drops. Tooth 7 reads the live store and the live bus.

    bin/cairn test cairn/devices/inference_domain/proofs/test_the_proxy_keeps_its_answers_in_a_tree_and_its_meter_in_the_log.py
"""

from __future__ import annotations

import ast
import contextlib
import json
import statistics
import subprocess
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROOF_TIMEOUT_S = 3600

PROVES = {"98ab0e9db57f": {
    "1": "no_module_names_the_old_table",
    "2": "a_repeat_is_served_from_the_tree",
    "3": "an_expired_answer_is_not_served",
    "4": "the_yield_report_sums_the_metrics_reply",
    "5": "the_calls_verb_reads_the_logs_tree",
    "6": "the_migration_carries_and_meters_once",
    "7": "live_the_table_is_gone_and_the_meter_carried",
    "8": "a_tree_lookup_is_no_slower_than_three_table_reads",
    "9": "every_other_proof_under_the_device_stays_green",
}}

DEVICE = _REPO_ROOT / "cairn" / "devices" / "inference_domain"
OLD = "inference" + "_calls"          # spelled split: tooth 1 greps this file's siblings
MIGRATION = "migrate_answers_to_their_tree.py"
_RUN = uuid.uuid4().hex[:8]
_SCRATCH = contextlib.ExitStack()
_TREES: list[str] = []

PASS = 0
FAIL = 0


def _domain():
    from cairn.devices.inference_domain import domain
    return domain


def _migration():
    from cairn.devices.inference_domain import migrate_answers_to_their_tree as m
    return m


def _store():
    from cairn.devices.db_domain.tools.client import store
    return store


def _trees():
    from cairn.devices.librarian.tools.trees import trees
    return trees


def _tree() -> str:
    """A fresh scratch answer tree, forgotten and dropped at exit."""
    name = _SCRATCH.enter_context(_domain().scratch_answers("answerproof"))
    _TREES.append(name)
    return name


@contextlib.contextmanager
def _isolated():
    from cairn.tools.base import address
    from cairn.tools.base.scratch import scratch_dir
    tmp = scratch_dir("testing-98ab0e9db57f-")
    domain = _domain()
    domain.set_diagnostic_roots({**address.ROOTS, "instance": tmp})
    try:
        yield tmp
    finally:
        domain.set_diagnostic_roots(None)


class _Counting:
    def __init__(self, *, horizon: str = "", cost: float = 11.0):
        self.calls = 0
        self.horizon = horizon
        self.cost = cost

    def __call__(self, request: dict) -> dict:
        self.calls += 1
        return {"answer": {"text": f"answer {self.calls} to {request.get('q')!r}"},
                "cost": self.cost, "horizon": self.horizon,
                "provenance": {"host": "http://testing.invalid", "model": "testing-model"}}


class _Refusing:
    def __call__(self, request: dict) -> dict:
        raise RuntimeError("testing: the host refused")


# ── 1 ────────────────────────────────────────────────────────────────────────

def no_module_names_the_old_table():
    named = []
    for p in sorted(DEVICE.rglob("*.py")):
        rel = p.relative_to(DEVICE)
        if "proofs" in rel.parts or "__pycache__" in rel.parts or rel.as_posix() == MIGRATION:
            continue
        if OLD in p.read_text(encoding="utf-8"):
            named.append(rel.as_posix())
    assert not named, f"non-proof modules still naming the old table: {named}"
    assert (DEVICE / MIGRATION).is_file(), f"the migration {MIGRATION} is absent"


# ── 2, 3 ─────────────────────────────────────────────────────────────────────

def a_repeat_is_served_from_the_tree():
    domain, tree = _domain(), _tree()
    with _isolated():
        ask = {"q": f"repeat_{_RUN}"}
        resolver = _Counting()
        first = domain.resolve(dict(ask), resolver=resolver, table=tree)
        second = domain.resolve(dict(ask), resolver=resolver, table=tree)
    assert first["hit"] is False and second["hit"] is True, (first["hit"], second["hit"])
    assert second["answer"] == first["answer"], (first["answer"], second["answer"])
    assert resolver.calls == 1, f"the resolver was called {resolver.calls} times"
    leaves = _trees().find(domain.canonical_digest(first["canonical"]), table=tree)
    assert len(leaves) == 1, f"{len(leaves)} leaves under the request's digest"
    assert json.loads(leaves[0]["content"])["answer"] == first["answer"], leaves[0]["content"]
    assert leaves[0]["meta"].get("cost") == 11.0, leaves[0]["meta"]


def an_expired_answer_is_not_served():
    domain, tree = _domain(), _tree()
    past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    with _isolated():
        ask = {"q": f"expired_{_RUN}"}
        resolver = _Counting(horizon=past)
        domain.resolve(dict(ask), resolver=resolver, table=tree)
        again = domain.resolve(dict(ask), resolver=resolver, table=tree)
    assert again["hit"] is False, "an expired answer was served"
    assert resolver.calls == 2, f"the resolver was called {resolver.calls} times, not 2"


# ── 4 ────────────────────────────────────────────────────────────────────────

def the_yield_report_sums_the_metrics_reply():
    domain = _domain()

    def row(name, value, verdict, **info):
        return {"name": name, "source": "inference_domain", "value": value,
                "info": {"verdict": verdict, **info}, "at": "2026-11-09T00:00:00+00:00"}
    rows = [row("inference.spent", 10.0, "miss"), row("inference.saved", 0.0, "miss"),
            row("inference.latency", 4.0, "miss"),
            row("inference.spent", 20.0, "miss"), row("inference.latency", 5.0, "miss"),
            row("inference.spent", 5.0, "miss", migrated=True),
            row("inference.latency", None, "miss", migrated=True),
            row("inference.saved", 7.0, "hit"), row("inference.spent", 0.0, "hit"),
            row("inference.latency", 1.0, "hit"),
            row("inference.latency", 2.0, "refused"), row("inference.spent", 0.0, "refused")]
    asked = []

    def ask(body):
        asked.append(dict(body))
        return {"rows": rows, "collected": 0}
    got = domain.yield_report(ask=ask)
    want = {"calls": 5, "hits": 1, "misses": 3, "refused": 1, "spent": 35.0, "avoided": 7.0}
    assert {k: got.get(k) for k in want} == want, got
    assert asked and asked[0].get("source") == "inference_domain", asked
    src = (DEVICE / "domain.py").read_text(encoding="utf-8")
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.ImportFrom):
            assert not (node.module or "").startswith("cairn.devices.cairn"), node.module
        if isinstance(node, ast.Import):
            assert not any(a.name.startswith("cairn.devices.cairn") for a in node.names)
    assert 'verb="metrics"' in src and 'to="cairn"' in src, "yield_report's default ask is not the metrics verb"


# ── 5 ────────────────────────────────────────────────────────────────────────

def the_calls_verb_reads_the_logs_tree():
    domain, tree = _domain(), _tree()
    from cairn.devices.inference_domain.device import InferenceDomainDevice
    dev = InferenceDomainDevice()
    with _isolated():
        domain.resolve({"q": f"calls_a_{_RUN}"}, resolver=_Counting(), table=tree)
        time.sleep(0.01)
        domain.resolve({"q": f"calls_a_{_RUN}"}, resolver=_Counting(), table=tree)
        time.sleep(0.01)
        try:
            domain.resolve({"q": f"calls_r_{_RUN}"}, resolver=_Refusing(), table=tree)
        except RuntimeError:
            pass
        every = dev._handle_calls({"body": {}})["calls"]
        two = dev._handle_calls({"body": {"limit": 2}})["calls"]
        since = dev._handle_calls({"body": {"since": every[-1]["created"]}})["calls"]
    assert [c["verdict"] for c in every] == ["refused", "hit", "miss"], [c.get("verdict") for c in every]
    assert [c["verdict"] for c in two] == ["refused", "hit"], [c.get("verdict") for c in two]
    assert [c["verdict"] for c in since] == ["refused", "hit"], [c.get("verdict") for c in since]
    created = [datetime.fromisoformat(c["created"]) for c in every]
    assert created == sorted(created, reverse=True), created
    for c in every:
        assert {"canonical", "created", "verdict", "answer", "cost"} <= set(c), sorted(c)
    assert every[2]["answer"] == {"text": f"answer 1 to 'calls_a_{_RUN}'"}, every[2]["answer"]
    json.dumps(every)


# ── 6 ────────────────────────────────────────────────────────────────────────

def _old_shape(prefix: str):
    m = _migration()
    return _store().scratch("inference_domain", prefix, m.SOURCE_COLUMNS)


def _fill(table: str, base: datetime) -> None:
    store = _store()
    past = (base - timedelta(days=30)).isoformat()
    rows = [
        ("A", "miss", {"text": "the older answer to A"}, "", 3, 0),
        ("A", "miss", {"text": "the newer answer to A"}, "", 4, 1),
        ("A", "hit", {"text": "the newer answer to A"}, "", 4, 2),
        ("B", "miss", {"text": "an answer to B, expired"}, past, 6, 3),
        ("C", "refused", None, "", 0, 4),
        ("D", "miss", {"t": 1}, "", 2, 5),
        ("E", "hit", {"t": 1}, "", 2, 60),           # after the live meter began: not metered
    ]
    for canon, verdict, answer, horizon, cost, minute in rows:
        store.write(table, "inference_domain", {
            "canonical": json.dumps({"q": f"{canon}_{_RUN}"}), "verdict": verdict,
            "answer": answer, "falsifier": "", "horizon": horizon,
            "provenance": {"domain": "default"}, "cost": cost,
            "created": (base + timedelta(minutes=minute)).isoformat()})


def the_migration_carries_and_meters_once():
    m, domain, trees = _migration(), _domain(), _trees()
    base = datetime(2026, 9, 1, tzinfo=timezone.utc)
    live_start = (base + timedelta(minutes=30)).isoformat()
    recorded: list[dict] = []

    def ask(body):
        live = [{"name": "inference.latency", "source": "inference_domain", "value": 3.0,
                 "info": {"verdict": "miss"}, "at": live_start}]
        return {"rows": live + [dict(r, source="inference_domain") for r in recorded]}

    def record(name, value, **kw):
        recorded.append({"name": name, "value": value, **kw})

    from cairn.tools.base.scratch import scratch_dir
    tmp = scratch_dir("testing-98ab0e9db57f-dump-")
    tree = _tree()
    with _old_shape("oldcalls") as src:
        _fill(src, base)
        dump = tmp / f"{src}.sql"
        dump.write_text(f"-- testing dump\nCOPY public.{src} (canonical) FROM stdin;\n\\.\n")
        nodump = m.migrate(source=src, table=tree, ask=ask, record=record, dump=None)
        assert nodump["exit"] != 0 and _store().owner_of(src) == "inference_domain", nodump
        assert not recorded and not _leaves(tree), "a refused migration wrote"
        report = m.migrate(source=src, table=tree, ask=ask, record=record, dump=dump)
        assert report["exit"] == 0, report
        assert _store().owner_of(src) is None, f"the source survived a clean migration: {report}"
        key = lambda c: domain.canonical_digest(domain.canonicalize({"q": f"{c}_{_RUN}"}))
        a = trees.find(key("A"), table=tree)
        assert len(a) == 1 and json.loads(a[0]["content"])["answer"] == {"text": "the newer answer to A"}, a
        assert trees.find(key("B"), table=tree) == [], "an expired answer was carried"
        assert len(trees.find(key("D"), table=tree)) == 1, "a short answer was dropped"
        assert trees.find(key("C"), table=tree) == [], "a refusal was carried as an answer"
        names = sorted((r["name"], r["info"]["verdict"]) for r in recorded)
        assert len(recorded) == 6 * 3, f"{len(recorded)} metric records for 6 pre-meter rows"
        assert all(r["info"].get("migrated") is True for r in recorded), recorded[:2]
        spent = sum(r["value"] or 0 for r in recorded if r["name"] == "inference.spent")
        saved = sum(r["value"] or 0 for r in recorded if r["name"] == "inference.saved")
        assert (spent, saved) == (3 + 4 + 6 + 2, 4), (spent, saved, names)
        lat = [r for r in recorded if r["name"] == "inference.latency"]
        assert all(r["value"] is None for r in lat), lat
        ats = sorted({r["at"] for r in recorded})
        assert ats[0] == base.isoformat() or datetime.fromisoformat(ats[0]) == base, ats[0]
        before = (len(recorded), sum(1 for _ in _leaves(tree)))
        again = m.migrate(source=src, table=tree, ask=ask, record=record, dump=dump)
        assert (len(recorded), sum(1 for _ in _leaves(tree))) == before, (again, before)
        assert again["exit"] == 0, again
    tree2 = _tree()
    with _old_shape("oldcalls") as src2:
        _fill(src2, base)
        dump2 = tmp / f"{src2}.sql"
        dump2.write_text(f"COPY public.{src2} (canonical) FROM stdin;\n\\.\n")

        def lossy(canonical, answer, **kw):
            if '"A_' in canonical:
                return
            return m.carry(canonical, answer, **kw)
        bad = m.migrate(source=src2, table=tree2, ask=lambda b: {"rows": []},
                        record=lambda *a, **k: None, dump=dump2, carry=lossy)
        assert bad["exit"] != 0, bad
        assert _store().owner_of(src2) == "inference_domain", "a mismatch dropped the source"


def _leaves(tree: str):
    return _store().query("SELECT leaf_id FROM {t}", tables={"t": tree}, params=())


# ── 7 ────────────────────────────────────────────────────────────────────────

def _dump_sums(path: Path) -> tuple[float, float, datetime]:
    """spent (miss cost) and avoided (hit cost) read off the dump's COPY section, and its
    newest row's created."""
    spent = avoided = 0.0
    newest = None
    cols = None
    with open(path, encoding="utf-8") as f:
        for line in f:
            if cols is None:
                if line.startswith(f"COPY public.{OLD} "):
                    cols = [c.strip() for c in line.split("(", 1)[1].split(")", 1)[0].split(",")]
                continue
            if line.startswith("\\."):
                break
            vals = line.rstrip("\n").split("\t")
            r = dict(zip(cols, vals))
            cost = 0.0 if r["cost"] == "\\N" else float(r["cost"])
            if r["verdict"] == "miss":
                spent += cost
            elif r["verdict"] == "hit":
                avoided += cost
            at = datetime.fromisoformat(r["created"])
            newest = at if newest is None or at > newest else newest
    assert cols is not None, f"{path} carries no COPY section for {OLD}"
    return spent, avoided, newest


def live_the_table_is_gone_and_the_meter_carried():
    store, domain = _store(), _domain()
    assert store.owner_of(OLD) is None, f"{OLD} is still registered"
    gone = store.query("SELECT 1 FROM information_schema.tables WHERE table_name = %s",
                       tables={}, params=(OLD,))
    assert not gone, f"{OLD} still exists"
    assert store.owner_of(domain.ANSWERS) == "inference_domain", store.owner_of(domain.ANSWERS)
    n = store.query("SELECT count(*) AS n FROM {t}", tables={"t": domain.ANSWERS}, params=())[0]["n"]
    assert n >= 11366, f"{n} leaves in the answer tree"
    dumps = sorted((Path.home() / ".cairn/devices/inference_domain/0/temp").glob(f"{OLD}-*.sql"))
    assert dumps, "no dump of the old table"
    spent, avoided, newest = _dump_sums(dumps[-1])
    from cairn.tools.bus_client import reach
    rows = reach("cairn").request(sender="inference_domain", to="cairn", verb="metrics",
                                  why="98ab0e9db57f tooth 7 (testing)",
                                  body={"source": "inference_domain"})["body"]["rows"]
    bound = newest + timedelta(seconds=1)
    upto = [r for r in rows if datetime.fromisoformat(r["at"]) <= bound]
    m_spent = sum(r["value"] or 0 for r in upto if r["name"] == "inference.spent")
    m_saved = sum(r["value"] or 0 for r in upto if r["name"] == "inference.saved")
    print(f"    dump spent {spent} avoided {avoided}; metrics spent {m_spent} saved {m_saved}; leaves {n}")
    assert (round(m_spent, 3), round(m_saved, 3)) == (round(spent, 3), round(avoided, 3)), (
        m_spent, m_saved, spent, avoided)


# ── 8 ────────────────────────────────────────────────────────────────────────

N_ROWS = 1000
N_LOOKUPS = 100


def a_tree_lookup_is_no_slower_than_three_table_reads():
    domain, store = _domain(), _store()
    tree = _tree()
    conn = store.connect()
    try:
        with _old_shape("oldspeed") as old:
            canons = [domain.canonicalize({"q": f"speed_{i}_{_RUN}"}) for i in range(N_ROWS)]
            for i, c in enumerate(canons):
                store.write(old, "inference_domain", {"canonical": c, "verdict": "miss",
                            "answer": {"text": f"answer {i} {_RUN}"}, "horizon": "", "cost": 1}, conn=conn)
                domain.store_answer(c, {"text": f"answer {i} {_RUN}"}, table=tree, conn=conn,
                                    meta={"horizon": "", "falsifier": "", "cost": 1.0, "provenance": {}})
            picks = [canons[(i * 37) % N_ROWS] for i in range(N_LOOKUPS)]
            now = datetime.now(timezone.utc)
            t_old, t_new = [], []
            for c in picks:
                t = time.perf_counter()
                store.read(old, where="canonical = %s AND verdict = 'miss'", params=(c,), conn=conn)
                t_old.append(time.perf_counter() - t)
                t = time.perf_counter()
                got = domain.stored_answer(c, now, table=tree, conn=conn)
                t_new.append(time.perf_counter() - t)
                assert got is not None, f"no stored answer for {c}"
    finally:
        conn.close()
    mo, mn = statistics.median(t_old) * 1000, statistics.median(t_new) * 1000
    print(f"    median table read {mo:.3f} ms, median tree lookup {mn:.3f} ms over {N_ROWS} rows")
    assert mn <= 3 * mo, f"tree lookup {mn:.3f} ms is more than 3x the table read {mo:.3f} ms"


# ── 9 ────────────────────────────────────────────────────────────────────────

def every_other_proof_under_the_device_stays_green():
    here = Path(__file__).resolve()
    red = {}
    for p in sorted(DEVICE.rglob("proofs/test_*.py")):
        if p.resolve() == here:
            continue
        r = subprocess.run([sys.executable, str(p)], cwd=str(_REPO_ROOT), capture_output=True,
                           text=True, timeout=900)
        if r.returncode != 0:
            red[p.relative_to(DEVICE).as_posix()] = (r.stdout + r.stderr).strip().splitlines()[-3:]
    assert not red, f"{len(red)} red: {red}"


TEETH = [no_module_names_the_old_table, a_repeat_is_served_from_the_tree,
         an_expired_answer_is_not_served, the_yield_report_sums_the_metrics_reply,
         the_calls_verb_reads_the_logs_tree, the_migration_carries_and_meters_once,
         live_the_table_is_gone_and_the_meter_carried,
         a_tree_lookup_is_no_slower_than_three_table_reads,
         every_other_proof_under_the_device_stays_green]


def _forget() -> None:
    for table in _TREES:
        try:
            _trees().forget_leaf(table)
        except Exception as exc:  # noqa: BLE001 — loud, never hidden
            print(f"  cleanup: forget_leaf({table}) failed: {type(exc).__name__}: {exc}")


if __name__ == "__main__":
    try:
        for fn in TEETH:
            try:
                fn()
            except Exception as exc:  # noqa: BLE001 — a proof reports, never hides
                FAIL += 1
                print(f"  RED   {fn.__name__}: {type(exc).__name__}: {exc}", flush=True)
            else:
                PASS += 1
                print(f"  green {fn.__name__}", flush=True)
    finally:
        _forget()
        _SCRATCH.close()
    print(f"{PASS} passed, {FAIL} failed out of {PASS + FAIL}")
    sys.exit(1 if FAIL else 0)
