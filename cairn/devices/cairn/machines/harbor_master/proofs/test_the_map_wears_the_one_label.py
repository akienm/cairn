"""Proof that the harbor map wears the one status label operator_inbox's reader derives (ticket cbbb651f4552).

Ruled 2026-09-06 (ticket 3feb201c84ea): a ticket has ONE status, and the inbox, the codemother
dashboard and the harbor map are venn diagrams of one reader. Until this ticket the map's half
of that was measured from operator_inbox's proof, which imported the harbor master (RULE 1: a
ticket's proofs measure only that component), so the map's teeth berth here with their owner.

Over one fixture (the forms the three readers used to disagree on: WATCHME(x):waiting, a prose
cursor, a PROVED ticket, a component whose history standing is prose) and over the live world:

  - every open map row wears the label operator_inbox.read_tickets gives that id, and the map
    lists exactly the reader's open set;
  - the map's status groups are the reader's labels, counted and ordered as the inbox header
    orders them, with no 'other';
  - a prose history standing is a FINDING line, never a status group;
  - a crossing patch reloads the ticket, so the cache wears the phase, not the bare target.

    python3 cairn/devices/cairn/machines/harbor_master/proofs/test_the_map_wears_the_one_label.py
"""

from __future__ import annotations

import json
import re
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[6]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"cbbb651f4552": {
    "1": "test_fixture_map_rows_wear_the_reader_label",
    "2": "test_fixture_map_groups_are_the_inbox_header",
    "3": "test_fixture_prose_standing_is_a_finding_not_a_status",
    "4": "test_crossing_patch_reloads_the_ticket_not_the_target",
    "5": "test_live_map_rows_wear_the_reader_label",
}}

_ROW = re.compile(r"^\s*(\d{4}-\d{2}-\d{2})\s+(\S+)\s+([0-9a-f]{12})\s+(.*)$")
_GROUP = re.compile(r"^\s*(\S+) \((\d+)\):$")

_WF = "code-seam@v2: THINKME -> TICKETME -> BUILDME -> PROVEME -> WATCHME(fx) -> PROVED"


def _wf(cursor: str) -> str:
    seat = cursor.split("(")[0].split(":")[0]
    stages = _WF.split(": ", 1)[1].split(" -> ")
    return "code-seam@v2: " + " -> ".join(
        f"[{cursor}]" if s.split("(")[0] == seat else s for s in stages)


FIXTURE_TICKETS = [
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
    ("aa0000000007", "prose-state", "2026-09-06", "waiting on akien", None),
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


def _map(tickets_dir: Path, cairn_root: Path):
    """The harbor's open map over the fixture, and the device that rendered it."""
    from cairn.devices.cairn.machines.harbor_master.device import HarborMasterDevice
    from cairn.devices.cairn.machines.harbor_master.register import register
    dev = HarborMasterDevice()
    dev._fleet_cache = register(cairn_root=cairn_root, tickets_dir=tickets_dir)
    return dev._render_fleet_map(dev._filter_fleet(dev._fleet_cache, "open")), dev


def _rows(text: str) -> dict[str, str]:
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


def _labels(tickets_dir: Path | None = None) -> dict[str, str]:
    from cairn.tools.operator_inbox.inbox import read_tickets
    kw = {"tickets_dir": tickets_dir} if tickets_dir is not None else {}
    return {r["id"]: r["label"] for r in read_tickets(**kw)["records"]}


def _header(tickets_dir: Path) -> dict[str, int]:
    """The inbox header's '(LABEL n, LABEL n)' — the reader's own count and order."""
    from cairn.tools.operator_inbox.inbox import format_summary, read_tickets
    summary = format_summary({
        "troubles": {"live": [], "live_count": 0, "total_count": 0}, "email": {"count": 0},
        "adjudications": {"findings": [], "count": 0}, "lap": {"items": [], "count": 0, "error": None},
        "questions": {"open": [], "count": 0}, "design": {},
        "tickets": read_tickets(tickets_dir=tickets_dir),
        "intentions": {"count": 0, "items": []}, "ideas": {"count": 0, "items": []}})
    assert "other" not in summary.lower(), summary
    m = re.search(r"tickets \(([^)]*)\)", summary)
    assert m, f"no ticket breakdown in the inbox summary: {summary!r}"
    return {p.rsplit(" ", 1)[0]: int(p.rsplit(" ", 1)[1]) for p in m.group(1).split(", ")}


def test_fixture_map_rows_wear_the_reader_label():
    from cairn.tools.operator_inbox.inbox import UNPARSED
    with tempfile.TemporaryDirectory() as td:
        tickets_dir, cairn_root = _build_fixture(Path(td))
        hmap, _ = _map(tickets_dir, cairn_root)
        rows, labels = _rows(hmap), _labels(tickets_dir)
        assert set(rows) == _NON_TERMINAL == set(labels), (
            f"map rows {sorted(rows)}, reader {sorted(labels)}")
        divergent = {tid: (rows[tid], labels[tid]) for tid in rows if rows[tid] != labels[tid]}
        assert not divergent, f"one ticket, two statuses (map, reader): {divergent}"
        assert rows["aa0000000004"] == "WATCHME:waiting"
        assert rows["aa0000000005"] == "WATCHME"
        assert rows["aa0000000002"] == "TICKETME:waiting"
        assert rows["aa0000000007"] == UNPARSED, "a prose cursor is loud (Law 7), never hidden"
        assert "aa0000000006" not in rows, "a PROVED ticket is not an open one on the map"


def test_fixture_map_groups_are_the_inbox_header():
    from cairn.tools.operator_inbox.inbox import UNPARSED
    with tempfile.TemporaryDirectory() as td:
        tickets_dir, cairn_root = _build_fixture(Path(td))
        hmap, _ = _map(tickets_dir, cairn_root)
        groups = _groups(hmap, "OPEN — by status:", "IN PORT — by component:")
        header = _header(tickets_dir)
        assert groups == header, f"map groups {groups} vs the inbox header {header}"
        assert list(groups) == list(header), "the map's group order is not the reader's order"
        assert list(groups)[0] == "THINKME" and list(groups)[-1] == UNPARSED, list(groups)
        assert sum(groups.values()) == len(_NON_TERMINAL)


def test_fixture_prose_standing_is_a_finding_not_a_status():
    with tempfile.TemporaryDirectory() as td:
        tickets_dir, cairn_root = _build_fixture(Path(td))
        hmap, dev = _map(tickets_dir, cairn_root)
        assert "FINDING: tools/fx_widget history standing is prose: Built and proved" in hmap, hmap
        assert not any(g.startswith("Built") for g in _groups(hmap)), hmap
        port = hmap.split("IN PORT — by component:", 1)[1]
        widget = port.split("tools/fx_widget (", 1)[1]
        assert _rows(widget.split("\n\n")[0]) == {"aa0000000001": "THINKME",
                                                    "aa0000000002": "TICKETME:waiting",
                                                    "aa0000000003": "PROVEME:waiting"}
        assert "tools/other_thing (2):" in port, "a component with no history still berths its tickets"
        assert "unassigned (1):" in port, "a ticket naming no owner is berthed loud, not dropped"
        fleet = dev._fleet_cache
        assert [f["component"] for f in fleet["findings"]] == ["tools/fx_widget"]
        assert set(fleet) >= {"open", "in_port", "findings", "fleet", "counts"}, sorted(fleet)
        # the harbor's own charter names the findings berth and the one reader; read beside
        # the module, so a reverted charter (hollow) reds here
        charter = Path(__file__).resolve().parents[1] / "intention+why.json"
        what = json.loads(charter.read_text()).get("what", "")
        assert "findings" in what and "operator_inbox" in what, (
            f"the harbor charter's `what` does not name the findings berth and the one reader: {what[:200]}")


def test_crossing_patch_reloads_the_ticket_not_the_target():
    with tempfile.TemporaryDirectory() as td:
        tickets_dir, cairn_root = _build_fixture(Path(td))
        before, dev = _map(tickets_dir, cairn_root)
        assert _rows(before)["aa0000000002"] == "TICKETME:waiting"
        path = next(tickets_dir.glob("aa0000000002-*.json"))
        doc = json.loads(path.read_text())
        doc["workflow_and_state"] = _wf("BUILDME:waiting")
        path.write_text(json.dumps(doc))
        dev._patch_fleet({"component": "cairn/tools/fx_widget", "from": "TICKETME",
                          "to": "BUILDME", "direction": "forward", "ticket": "aa0000000002"})
        after = dev._render_fleet_map(dev._filter_fleet(dev._fleet_cache, "open"))
        assert _rows(after)["aa0000000002"] == _labels(tickets_dir)["aa0000000002"] == "BUILDME:waiting", (
            "the cache wore the bare target (or the stale label) while the reader wore the phase")
        port = after.split("IN PORT — by component:", 1)[1]
        assert _rows(port)["aa0000000002"] == "BUILDME:waiting"


def test_live_map_rows_wear_the_reader_label():
    from cairn.devices.cairn.machines.harbor_master.device import HarborMasterDevice
    labels = _labels()
    assert labels, "no live tickets — a green here would be hollow"
    hmap = HarborMasterDevice()._handle_show({
        "id": "proof", "sender": "proof", "to": "harbor_master",
        "verb": "show", "body": {"what": "map", "args": ["open"]}})["text"]
    rows = _rows(hmap)
    assert set(rows) == set(labels), (
        f"map-only {sorted(set(rows) - set(labels))[:5]}, reader-only {sorted(set(labels) - set(rows))[:5]}")
    divergent = {tid: (rows[tid], labels[tid]) for tid in rows if rows[tid] != labels[tid]}
    assert not divergent, f"one ticket, two statuses, live (map, reader): {dict(list(divergent.items())[:10])}"
    print(f"    (live: {len(rows)} open tickets, the map wears the reader's label on each)")


def _main() -> int:
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_")]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"  PASS  {name}")
        except Exception as exc:  # noqa: BLE001 — a proof reports every red (Law 7)
            failed += 1
            print(f"  FAIL  {name}: {type(exc).__name__}: {exc}")
    print(f"\n{len(tests) - failed}/{len(tests)} green")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(_main())
