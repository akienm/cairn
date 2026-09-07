"""PROOF — a ticket has ONE status, and the three reports are venn diagrams of one reader.

Ticket 3feb201c84ea (Akien, 2026-09-06): "for a given ticket that appers in all the
places, i should see the same status. it has one status." / "they're kinda venn
diagrams. so whatever's in the way of that's a bug."

The three reports `akienupdate` prints — the operator inbox, the codemother
dashboard, the harbor map — are rendered here over ONE fixture and over the LIVE
world, and every ticket id that appears on more than one of them must wear the
byte-identical status label on each. The label is derived once, in
operator_inbox.read_tickets; nothing here re-derives it — the teeth compare the
printed rows, which is what Akien reads.

What a hollow build cannot pass (Law 8):
  - A report that parses the cursor its own way (the pre-3feb state: three readers,
    three regexes) fails test_fixture_one_label_per_id_across_all_three the moment
    a WATCHME(x):waiting or a prose cursor is in the fixture — those are the forms the
    three readers disagreed on.
  - A header that buckets 'other' fails test_fixture_headers_sum_with_no_other.
  - A harbor map that prints a component's history standing as a status group fails
    test_fixture_prose_standing_is_a_finding_not_a_status.
  - A crossing patch that writes the bare target into the cache fails
    test_crossing_patch_reloads_the_ticket_not_the_target.
  - A build whose fixture is green but whose world is not fails the live teeth.

    python3 cairn/tools/operator_inbox/proofs/test_one_status_everywhere.py   # exit 0 = green
"""

from __future__ import annotations

import json
import re
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.base.transitions import TERMINAL_STATES                      # noqa: E402
from cairn.tools.operator_inbox.inbox import (                                 # noqa: E402
    UNPARSED,
    format_inbox,
    format_summary,
    read_tickets,
)
from cairn.devices.codemother.dashboard import format_dashboard                # noqa: E402
from cairn.devices.cairn.machines.harbor_master.device import HarborMasterDevice  # noqa: E402
from cairn.devices.cairn.machines.harbor_master.register import register      # noqa: E402

_ROW = re.compile(r"^\s*(\d{4}-\d{2}-\d{2})\s+(\S+)\s+([0-9a-f]{12})\s+(.*)$")
_GROUP = re.compile(r"^\s*(\S+) \((\d+)\):$")
_COMMONS = _REPO_ROOT.parent / "CairnCommons"


# --- the fixture -------------------------------------------------------------

_WF = "code-seam@v2: THINKME -> TICKETME -> BUILDME -> PROVEME -> WATCHME(fx) -> PROVED"


def _wf(cursor: str) -> str:
    """Render the class path with the bracketed cursor at its own seat."""
    seat = cursor.split("(")[0].split(":")[0]
    stages = _WF.split(": ", 1)[1].split(" -> ")
    out = []
    for s in stages:
        out.append(f"[{cursor}]" if s.split("(")[0] == seat else s)
    return "code-seam@v2: " + " -> ".join(out)


FIXTURE_TICKETS = [
    # id, title, date, workflow_and_state, owning_intention
    ("aa0000000001", "think-about-it", "2026-09-01", _wf("THINKME"),
     "cairn/tools/fx_widget/intention+why.json"),
    ("aa0000000002", "cast-it", "2026-09-02", _wf("TICKETME:waiting"),
     "cairn/tools/fx_widget/intention+why.json"),
    ("aa0000000003", "prove-it", "2026-09-03", _wf("PROVEME:waiting"),
     "cairn/tools/fx_widget/intention+why.json"),
    ("aa0000000004", "watch-it-waiting", "2026-09-04", _wf("WATCHME(fx):waiting"),
     "cairn/tools/other_thing/intention+why.json"),
    ("aa0000000005", "watch-it-armed", "2026-09-05", _wf("WATCHME(fx)"),
     "cairn/tools/other_thing/intention+why.json"),
    ("aa0000000006", "done-and-dusted", "2026-09-06", _wf("PROVED"),
     "cairn/tools/fx_widget/intention+why.json"),
    ("aa0000000007", "prose-state", "2026-09-06", "waiting on akien",
     None),
]
_NON_TERMINAL = {t[0] for t in FIXTURE_TICKETS if t[3] != _wf("PROVED")}


def _build_fixture(root: Path) -> tuple[Path, Path]:
    tickets = root / "tickets"
    tickets.mkdir()
    for tid, title, date, wf, owning in FIXTURE_TICKETS:
        doc = {"id": tid, "title": title, "date": date, "workflow_and_state": wf,
               "node_class": "code-seam"}
        if owning:
            doc["owning_intention"] = owning
        (tickets / f"{tid}-{title}.json").write_text(json.dumps(doc, indent=2))
    (tickets / "_charter+why.json").write_text(json.dumps({"role": "store-charter"}))
    cairn_root = root / "cairn"
    comp = cairn_root / "tools" / "fx_widget"
    comp.mkdir(parents=True)
    (comp / "widget.py").write_text("# fixture component\n")
    (comp / "history.json").write_text(json.dumps([
        {"at": "2026-08-28", "seq": 0,
         "standing": "Built and proved — three teeth green, probe armed"}]))
    return tickets, cairn_root


def _stub_data(tickets_dir: Path) -> dict:
    """The inbox's data dict with every lane but tickets stubbed empty — the tickets
    lane is the real reader over the fixture."""
    return {
        "troubles": {"live": [], "live_count": 0, "total_count": 0},
        "email": {"count": 0},
        "adjudications": {"findings": [], "count": 0},
        "lap": {"items": [], "count": 0, "error": None},
        "questions": {"open": [], "count": 0},
        "design": {},
        "tickets": read_tickets(tickets_dir=tickets_dir),
        "intentions": {"count": 0, "items": []},
        "ideas": {"count": 0, "items": []},
    }


def _render_three(tickets_dir: Path, cairn_root: Path) -> tuple[str, str, str, HarborMasterDevice]:
    data = _stub_data(tickets_dir)
    inbox = format_inbox(data)
    dash = format_dashboard(data, tickets_dir=tickets_dir)
    dev = HarborMasterDevice()
    dev._fleet_cache = register(cairn_root=cairn_root, tickets_dir=tickets_dir)
    fleet = dev._filter_fleet(dev._fleet_cache, "open")
    return inbox, dash, dev._render_fleet_map(fleet), dev


# --- readers over the PRINTED text (what Akien sees) -------------------------

def _rows(text: str) -> dict[str, str]:
    """{id: label} for every ticket atom printed. A single id printed with two labels
    on one report is itself a divergence, and raises here."""
    out: dict[str, str] = {}
    for line in text.splitlines():
        m = _ROW.match(line)
        if not m:
            continue
        _, label, tid, _ = m.groups()
        assert out.get(tid, label) == label, (
            f"{tid} printed twice with two labels on one report: {out[tid]} / {label}")
        out[tid] = label
    return out


def _groups(text: str, start: str | None = None, stop: str | None = None) -> dict[str, int]:
    """{label: n} from the 'LABEL (n):' group headers between two markers."""
    lines = text.splitlines()
    if start is not None:
        lines = lines[next(i for i, l in enumerate(lines) if start in l) + 1:]
    if stop is not None:
        lines = lines[:next(i for i, l in enumerate(lines) if stop in l)]
    out: dict[str, int] = {}
    for line in lines:
        m = _GROUP.match(line)
        if m and not m.group(1).startswith("DONE"):
            out[m.group(1)] = int(m.group(2))
    return out


def _header_counts(summary: str) -> dict[str, int]:
    """{label: n} from the inbox header's '(LABEL n, LABEL n)'."""
    m = re.search(r"tickets \(([^)]*)\)", summary)
    assert m, f"no ticket breakdown in the summary: {summary!r}"
    out = {}
    for part in m.group(1).split(", "):
        label, n = part.rsplit(" ", 1)
        out[label] = int(n)
    return out


# --- fixture teeth ------------------------------------------------------------

def test_fixture_one_label_per_id_across_all_three():
    with tempfile.TemporaryDirectory() as td:
        tickets_dir, cairn_root = _build_fixture(Path(td))
        inbox, dash, hmap, _ = _render_three(tickets_dir, cairn_root)
        i_rows, d_rows, m_rows = _rows(inbox), _rows(dash), _rows(hmap)
        # the dashboard and the open map list every non-terminal ticket — the same set
        assert set(d_rows) == _NON_TERMINAL, f"dashboard rows {sorted(d_rows)}"
        assert set(m_rows) == _NON_TERMINAL, f"map rows {sorted(m_rows)}"
        # the inbox lists the design lane (THINKME) — a subset, same labels
        assert i_rows and set(i_rows) <= set(d_rows), f"inbox rows {sorted(i_rows)}"
        divergent = [(tid, i_rows.get(tid), d_rows.get(tid), m_rows.get(tid))
                     for tid in set(i_rows) | set(d_rows) | set(m_rows)
                     if len({r[tid] for r in (i_rows, d_rows, m_rows) if tid in r}) != 1]
        assert not divergent, f"one ticket, two statuses: {divergent}"
        # and the labels are the ones the fixture carries — the forms that used to diverge
        assert d_rows["aa0000000004"] == "WATCHME:waiting"
        assert d_rows["aa0000000005"] == "WATCHME"
        assert d_rows["aa0000000002"] == "TICKETME:waiting"
        assert d_rows["aa0000000007"] == UNPARSED, "a prose cursor is loud (Law 7), never hidden"
        assert "aa0000000006" not in m_rows and "aa0000000006" not in d_rows, \
            "a PROVED ticket is not an open one on any surface"
        assert "PROVED (1)" in dash, "the dashboard counts the done ticket under DONE"


def test_fixture_headers_sum_with_no_other():
    with tempfile.TemporaryDirectory() as td:
        tickets_dir, cairn_root = _build_fixture(Path(td))
        data = _stub_data(tickets_dir)
        inbox, dash, hmap, _ = _render_three(tickets_dir, cairn_root)
        header = _header_counts(format_summary(data))
        assert "other" not in format_summary(data).lower(), format_summary(data)
        assert sum(header.values()) == len(_NON_TERMINAL) == data["tickets"]["total_not_done"]
        dash_groups = _groups(dash)
        map_groups = _groups(hmap, "OPEN — by status:", "IN PORT — by component:")
        assert header == dash_groups == map_groups, (
            f"the three headers disagree:\n inbox {header}\n dash  {dash_groups}\n map   {map_groups}")
        # priority order is the one order, on every surface
        assert list(header) == list(dash_groups) == list(map_groups)
        assert list(header)[0] == "THINKME" and list(header)[-1] == UNPARSED


def test_fixture_prose_standing_is_a_finding_not_a_status():
    with tempfile.TemporaryDirectory() as td:
        tickets_dir, cairn_root = _build_fixture(Path(td))
        _, _, hmap, dev = _render_three(tickets_dir, cairn_root)
        assert "FINDING: tools/fx_widget history standing is prose: Built and proved" in hmap, hmap
        # the prose never becomes a group header on the map
        assert not any(g.startswith("Built") for g in _groups(hmap)), hmap
        # in port: the SAME rows, grouped by the component the ticket names
        port = hmap.split("IN PORT — by component:", 1)[1]
        widget = port.split("tools/fx_widget (", 1)[1]
        assert _rows(widget.split("\n\n")[0]) == {"aa0000000001": "THINKME",
                                                    "aa0000000002": "TICKETME:waiting",
                                                    "aa0000000003": "PROVEME:waiting"}
        assert "tools/other_thing (2):" in port, "a component with no history still berths its tickets"
        assert "unassigned (1):" in port, "a ticket naming no owner is berthed loud, not dropped"
        fleet = dev._fleet_cache
        assert [f["component"] for f in fleet["findings"]] == ["tools/fx_widget"]


def test_crossing_patch_reloads_the_ticket_not_the_target():
    with tempfile.TemporaryDirectory() as td:
        tickets_dir, cairn_root = _build_fixture(Path(td))
        _, _, before, dev = _render_three(tickets_dir, cairn_root)
        assert _rows(before)["aa0000000002"] == "TICKETME:waiting"
        # the ticket crosses to BUILDME and, as every crossing does, lands at :waiting
        path = next(tickets_dir.glob("aa0000000002-*.json"))
        doc = json.loads(path.read_text())
        doc["workflow_and_state"] = _wf("BUILDME:waiting")
        path.write_text(json.dumps(doc))
        dev._patch_fleet({"component": "cairn/tools/fx_widget", "from": "TICKETME",
                          "to": "BUILDME", "direction": "forward", "ticket": "aa0000000002"})
        after = dev._render_fleet_map(dev._filter_fleet(dev._fleet_cache, "open"))
        fresh = {r["id"]: r["label"] for r in read_tickets(tickets_dir=tickets_dir)["records"]}
        assert _rows(after)["aa0000000002"] == fresh["aa0000000002"] == "BUILDME:waiting", (
            "the cache wore the bare target (or the stale label) while the inbox wore the phase")
        # the in-port berth shows the same object, so it moved too
        port = after.split("IN PORT — by component:", 1)[1]
        assert _rows(port)["aa0000000002"] == "BUILDME:waiting"


# --- live teeth: the real world, the real three reports ----------------------

def test_live_one_label_per_id_across_the_three_reports():
    live = {r["id"]: r["label"] for r in read_tickets()["records"]}
    assert live, "no live tickets — a green here would be hollow"
    dash = format_dashboard()
    dev = HarborMasterDevice()
    hmap = dev._handle_show({"id": "proof", "sender": "proof", "to": "harbor_master",
                             "verb": "show", "body": {"what": "map", "args": ["open"]}})["text"]
    d_rows, m_rows = _rows(dash), _rows(hmap)
    assert set(d_rows) == set(m_rows) == set(live), (
        f"the dashboard, the map and the reader list different tickets: "
        f"dash-only {sorted(set(d_rows) - set(m_rows))[:5]}, map-only {sorted(set(m_rows) - set(d_rows))[:5]}, "
        f"reader-only {sorted(set(live) - set(d_rows) - set(m_rows))[:5]}")
    divergent = [(tid, live[tid], d_rows[tid], m_rows[tid]) for tid in live
                 if not (live[tid] == d_rows[tid] == m_rows[tid])]
    assert not divergent, f"one ticket, two statuses, live: {divergent[:10]}"
    assert all(lbl.split(":")[0] not in TERMINAL_STATES for lbl in live.values())
    print(f"    (live: {len(live)} open tickets, one label each across dashboard + map)")


def test_live_akienupdate_reports_agree():
    """The three files `akienupdate` writes — the exact text Akien reads. Every id on
    more than one of them wears one label."""
    files = [_COMMONS / n for n in ("AkienInbox.txt", "AkienDashboard.txt", "AkienHMMap.txt")]
    missing = [str(f) for f in files if not f.is_file()]
    assert not missing, f"akienupdate has not written: {missing}"
    per_file = [_rows(f.read_text(encoding="utf-8")) for f in files]
    seen: dict[str, set[str]] = {}
    for rows in per_file:
        for tid, label in rows.items():
            seen.setdefault(tid, set()).add(label)
    shared = [tid for tid in seen if sum(tid in r for r in per_file) >= 2]
    assert shared, "no ticket appears on two of the three reports — nothing to compare (hollow)"
    divergent = {tid: sorted(labels) for tid, labels in seen.items() if len(labels) != 1}
    assert not divergent, f"one ticket, two statuses in Akien's reports: {divergent}"
    print(f"    (akienupdate: {len(shared)} ids on 2+ reports, all agree)")


if __name__ == "__main__":
    checks = [
        test_fixture_one_label_per_id_across_all_three,
        test_fixture_headers_sum_with_no_other,
        test_fixture_prose_standing_is_a_finding_not_a_status,
        test_crossing_patch_reloads_the_ticket_not_the_target,
        test_live_one_label_per_id_across_the_three_reports,
        test_live_akienupdate_reports_agree,
    ]
    failures = 0
    for check in checks:
        try:
            check()
            print(f"  PASS  {check.__name__}")
        except Exception as exc:  # noqa: BLE001
            failures += 1
            print(f"  FAIL  {check.__name__}: {type(exc).__name__}: {exc}")
    if failures:
        print(f"RED — {failures} tooth/teeth bit")
        raise SystemExit(1)
    print("green — one reader, one label per ticket, on the inbox, the dashboard and the map")
