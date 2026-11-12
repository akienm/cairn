"""Proof for ticket f78a1a09e8ff — device-ness asks the shim ``get status``.

The second clause of 74d4124bc0e7's falsifier: a device is fitted at the rack AND answers a
health query over the bus. Every shim answers the root view ``status``
(``cairn/tools/base/shim.py`` ``ROOT_VIEWS``). ``deviceness.answers_health`` asks it through an
injected ``ask`` (D1), so these teeth hand in fakes and open no bus.

  1. answers_health is True for exit 0 with data, False for a refusal, a raise, or data None;
  2. is_live_device is False for a fitted device whose shim is silent and True for one that
     answers, and is_device reads the same for both;
  3. deviceness.py no longer says UNBUILT and the clause names get status at shim.py.

    bin/cairn test cairn/tools/base/proofs/test_deviceness_asks_health.py
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"f78a1a09e8ff": {
    "1": "test_an_answer_is_exit_zero_with_data",
    "2": "test_a_live_device_is_fitted_and_answers",
    "3": "test_the_clause_is_built_and_names_get_status",
}}


def _reply(exit_code, data):
    return {"exit": exit_code, "text": "", "data": data, "cached": False}


def test_an_answer_is_exit_zero_with_data():
    from cairn.tools.base.deviceness import answers_health
    asked = []

    def good(dev, verb, view):
        asked.append((dev, verb, view))
        return _reply(0, {"intention": "x", "state": {}})

    assert answers_health("testing_dev", good) is True
    assert asked == [("testing_dev", "get", "status")], asked

    def boom(dev, verb, view):
        raise TimeoutError("testing: no reply")

    for silent in (lambda d, v, w: _reply(2, None),
                   lambda d, v, w: _reply(0, None),
                   lambda d, v, w: _reply(1, {"x": 1}),
                   lambda d, v, w: None,
                   boom):
        assert answers_health("testing_dev", silent) is False


def _rack(root: Path, *names: str) -> None:
    for n in names:
        d = root / "cairn" / "devices" / n
        d.mkdir(parents=True, exist_ok=True)
        (d / "intention+why.json").write_text("{}")


def test_a_live_device_is_fitted_and_answers():
    from cairn.tools.base import deviceness as D
    from cairn.tools.rack.rack import rack_ids
    root = Path(tempfile.mkdtemp(prefix="testing-deviceness-asks-"))
    _rack(root, "testing_awake", "testing_asleep")
    fitted = set(rack_ids(root))
    assert {"testing_awake", "testing_asleep"} <= fitted, fitted

    def ask(dev, verb, view):
        return _reply(0, {"state": {}}) if dev == "testing_awake" else _reply(2, None)

    assert D.is_device("testing_awake", root) and D.is_device("testing_asleep", root)
    assert D.is_live_device("testing_awake", ask, root) is True
    assert D.is_live_device("testing_asleep", ask, root) is False
    assert D.is_live_device("testing_not_racked", ask, root) is False


def test_the_clause_is_built_and_names_get_status():
    from cairn.tools.base import deviceness as D
    src = (_REPO_ROOT / "cairn/tools/base/deviceness.py").read_text()
    assert "UNBUILT" not in src
    assert "get status" in D.HEALTH_QUERY_CLAUSE
    assert "cairn/tools/base/shim.py" in D.HEALTH_QUERY_CLAUSE


def main() -> int:
    teeth = [v for k, v in globals().items() if k.startswith("test_") and callable(v)]
    failed = 0
    for t in teeth:
        try:
            t()
            print(f"  ok   {t.__name__}")
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"  FAIL {t.__name__}: {type(exc).__name__}: {exc}")
    print(f"{len(teeth) - failed}/{len(teeth)} green")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
