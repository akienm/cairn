#!/usr/bin/env python3
"""Proof: the web server renders the trouble pane and reads the trouble rows itself, with no bus
(ticket 609b038a1958).

These teeth stood in two other devices' proofs, measuring web_server code from outside it:
the four render teeth in cairn/devices/cairn/proofs/test_trouble_panel.py (importing
cairn.devices.web_server.render), and the web half of "the two readers read with no bus" in
cairn/devices/trouble/proofs/test_trouble_never_rides_the_bus.py (importing
cairn.devices.web_server.listener). RULE 1: a ticket's proofs measure only that component, so
the teeth berth here, beside the code they measure, and the other two proofs drop them.

Teeth a hollow build could not pass:
  (1) the trouble pane renders two-sided: a trouble-list, a trouble-detail, a red-light;
  (2) the red light is bright (#d33) over live troubles and dull (#998) over none;
  (3) every value a trouble carries is escaped, never live markup;
  (4) the socket's rows read a seeded store with every bus dial refused: the live top of the
      store (an unreadable file surfaced as a row), cleared/ left out, four keys a row; and an
      absent store raises rather than reading as no troubles (Law 7).

    bin/cairn test cairn/devices/web_server/proofs/test_the_web_server_renders_and_reads_troubles.py
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {"609b038a1958": {"1": "test_the_trouble_pane_renders_two_sided",
                    "2": "test_the_red_light_is_bright_only_over_live_troubles",
                    "3": "test_every_trouble_value_is_escaped",
                    "4": "test_the_socket_rows_read_the_store_with_no_bus"}}

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def _render(rows: list[dict]) -> str:
    from cairn.devices.web_server.render import render_pane
    return render_pane({"kind": "trouble", "label": "troubles", "data": rows})


def test_the_trouble_pane_renders_two_sided() -> None:
    html = _render([{"id": "t1", "standing": "OPEN", "why": "test", "count": 1,
                     "first_seen": "2026-09-01", "last_seen": "2026-09-01"}])
    missing = [c for c in ("trouble-list", "trouble-detail", "red-light") if c not in html]
    check("test_the_trouble_pane_renders_two_sided", not missing, f"missing {missing}")


def test_the_red_light_is_bright_only_over_live_troubles() -> None:
    live = _render([{"id": "t1", "standing": "OPEN", "why": "test", "count": 1}])
    none = _render([])
    ok = "#d33" in live and "#998" not in live and "#998" in none and "#d33" not in none
    check("test_the_red_light_is_bright_only_over_live_troubles", ok,
          f"live has #d33={'#d33' in live} #998={'#998' in live}; "
          f"none has #998={'#998' in none} #d33={'#d33' in none}")


def test_every_trouble_value_is_escaped() -> None:
    html = _render([{"id": "<script>", "standing": "OPEN", "why": "a&b", "count": 1}])
    ok = "<script>" not in html and "&lt;script&gt;" in html and "a&amp;b" in html
    check("test_every_trouble_value_is_escaped", ok, html[-300:] if not ok else "")


class _Refused(Exception):
    pass


def _put(folder: Path, ident: str, standing: str = "OPEN") -> None:
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{ident}.json").write_text(json.dumps(
        {"id": ident, "standing": standing, "why": f"a proof's trouble ({ident})", "count": 2,
         "first_seen": "2026-10-18T00:00:00+00:00", "last_seen": "2026-10-18T00:01:00+00:00",
         "occurrences": [{"at": "2026-10-18T00:00:00+00:00"}]}), encoding="utf-8")


def test_the_socket_rows_read_the_store_with_no_bus() -> None:
    import cairn.tools.bus_client as bc
    from cairn.devices.web_server import listener
    from cairn.tools.base.address import log_path

    saved = bc.reach

    def no_reach(*a, **kw):
        raise _Refused(f"reach{a}")

    bc.reach = no_reach
    errs: list[str] = []
    rows: list[dict] = []
    try:
        with tempfile.TemporaryDirectory(prefix="ws-trouble-rows-") as d:
            roots = {k: Path(d) for k in ("repo", "commons", "instance")}
            store = log_path("cairn", 0, roots) / "troubletickets"
            _put(store, "proof-live-a")
            _put(store, "proof-live-b")
            (store / "proof-unreadable.json").write_text("{not json", encoding="utf-8")
            _put(store / "cleared", "proof-cleared", standing="CLEARED")
            try:
                rows = listener._trouble_rows(roots)
            except Exception as exc:  # noqa: BLE001 — a reader that cannot read is the red
                errs.append(f"rows: {type(exc).__name__}: {exc}")
            absent = {k: Path(d) / "absent" for k in ("repo", "commons", "instance")}
            try:
                listener._trouble_rows(absent)
                errs.append("an absent store answered instead of raising")
            except _Refused as exc:
                errs.append(f"an absent store asked the bus: {exc}")
            except Exception:  # noqa: BLE001 — Law 7: absent is a raise, never zero troubles
                pass
    finally:
        bc.reach = saved
    want = ["proof-live-a", "proof-live-b", "proof-unreadable"]
    got = sorted(r.get("id") for r in rows)
    shaped = all(set(r) == {"id", "standing", "why", "count"} for r in rows)
    check("test_the_socket_rows_read_the_store_with_no_bus", got == want and shaped and not errs,
          f"ids={got} four_keys={shaped} errs={errs}")


TEETH = (test_the_trouble_pane_renders_two_sided, test_the_red_light_is_bright_only_over_live_troubles,
         test_every_trouble_value_is_escaped, test_the_socket_rows_read_the_store_with_no_bus)


def main() -> int:
    for tooth in TEETH:
        try:
            tooth()
        except Exception as exc:  # noqa: BLE001 — a tooth that cannot run is a red, loudly
            check(tooth.__name__, False, f"raised {type(exc).__name__}: {exc}")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
