"""Proof for ticket 9447b97e4fd8 — CairnCommons/tickets/_schema-v2.json is the decided ticket-v2 schema.

d421051bc1f7 D3 / D11 / D25 / D27: ticket-v2 is compiled from a census over the rehearsal records'
decision lines, never authored first, and the census is stored beside the schema so every later
builder reads it from git. These teeth read the committed file and measure it against what the
decisions name; a file that is absent, reshaped or altered fails them.

1. the_file_has_exactly_three_keys: keys == schema_version, schema, census; schema_version 'ticket-v2';
2. the_schema_names_d11s_twenty_one_fields: the keys of schema are exactly D11's 21 field names and
   every value is a non-empty one-line string;
3. the_census_is_the_verbatim_measurement: census minus 'how', re-serialised with
   json.dumps(indent=1) plus a newline, has the sha256 d421051bc1f7 D3 names;
4. the_census_says_how_to_rerun_it: census.how is a non-empty string naming CairnCommons/rehearsals.

The commons file is read from beside the code root, else from the home checkout (a hollow worktree
has no commons beside it).

Run bare:  PYTHONPATH=. python3 cairn/tools/base/proofs/test_the_ticket_v2_schema_file_is_the_decided_one.py
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]

PROVES = {
    "9447b97e4fd8": {
        "1": "test_the_file_has_exactly_three_keys",
        "2": "test_the_schema_names_d11s_twenty_one_fields",
        "3": "test_the_census_is_the_verbatim_measurement",
        "4": "test_the_census_says_how_to_rerun_it",
    },
}

# D11 of ticket d421051bc1f7, field names in the order it spells them.
D11_FIELDS = [
    "id", "title", "node_class", "task_or_ticket", "workflow_and_state", "date", "created",
    "author", "from_idea", "intent_berth", "sorted_berth", "owner", "owning_intention",
    "questions", "falsifier", "watchme", "depends_on", "follow_ons", "schema_version",
    "rehearsal", "decisions",
]
# D3 / D25 of d421051bc1f7: the census file's sha256.
CENSUS_SHA256 = "4b8e394bfe8d9602ceb17e8f3859735f6af414c8e92a879ed1b0ddd5e1d3ae79"


def _schema_path() -> Path:
    beside = REPO.parent / "CairnCommons" / "tickets" / "_schema-v2.json"
    if beside.is_file():
        return beside
    return Path.home() / "dev" / "src" / "CairnCommons" / "tickets" / "_schema-v2.json"


def _load() -> dict:
    return json.loads(_schema_path().read_text(encoding="utf-8"))


def test_the_file_has_exactly_three_keys():
    doc = _load()
    assert sorted(doc) == ["census", "schema", "schema_version"], sorted(doc)
    assert doc["schema_version"] == "ticket-v2", doc["schema_version"]


def test_the_schema_names_d11s_twenty_one_fields():
    schema = _load()["schema"]
    assert isinstance(schema, dict), type(schema)
    assert sorted(schema) == sorted(D11_FIELDS), (
        f"missing {sorted(set(D11_FIELDS) - set(schema))}, extra {sorted(set(schema) - set(D11_FIELDS))}")
    for name, meaning in schema.items():
        assert isinstance(meaning, str) and meaning.strip(), f"{name}: blank meaning"
        assert "\n" not in meaning, f"{name}: meaning is not one line"


def test_the_census_is_the_verbatim_measurement():
    census = dict(_load()["census"])
    census.pop("how", None)
    raw = (json.dumps(census, indent=1) + "\n").encode("utf-8")
    got = hashlib.sha256(raw).hexdigest()
    assert got == CENSUS_SHA256, f"census sha256 {got}, decided {CENSUS_SHA256}"


def test_the_census_says_how_to_rerun_it():
    how = _load()["census"].get("how")
    assert isinstance(how, str) and how.strip(), f"census.how is {how!r}"
    assert "CairnCommons/rehearsals" in how, how


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
