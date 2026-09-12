"""Proofs for the pure half of openai_wire (clause b of the falsifier, plus the
stdlib-only half of clause a). Dicts in, dicts out, nothing dialed — a hollow
translate that passed messages through untouched fails every direction tooth,
and one that reached for a device fails the imports tooth.

Provenance: ticket 76639374d9f9.
"""
import json
import sys
from pathlib import Path

from cairn.machines.openai_wire import translate
from cairn.tools.import_sieve.sieve import imports_in

PASS = 0
FAIL = 0
HERE = Path(__file__).resolve().parent.parent


def _tooth(name, fn):
    global PASS, FAIL
    try:
        fn()
    except Exception as exc:
        FAIL += 1
        print(f"  RED   {name}: {type(exc).__name__}: {exc}")
        return
    PASS += 1
    print(f"  green {name}")


def inbound_string_arguments_become_objects():
    msgs = [{"role": "assistant", "content": None,
             "tool_calls": [{"id": "call_x", "type": "function",
                             "function": {"name": "read_file", "arguments": '{"path": "a.py"}'}}]}]
    out = translate.to_provider(msgs)
    assert out[0]["tool_calls"][0]["function"]["arguments"] == {"path": "a.py"}, out
    assert out[0]["content"] == "", "null content must become '' on the way in"


def inbound_does_not_mutate_its_input():
    msgs = [{"role": "assistant", "content": None,
             "tool_calls": [{"function": {"name": "f", "arguments": '{"a": 1}'}}]}]
    frozen = json.dumps(msgs, sort_keys=True)
    translate.to_provider(msgs)
    assert json.dumps(msgs, sort_keys=True) == frozen, "to_provider mutated the caller's messages"


def inbound_unparseable_arguments_stay_loud():
    msgs = [{"role": "assistant", "content": "",
             "tool_calls": [{"function": {"name": "f", "arguments": "{not json"}}]}]
    out = translate.to_provider(msgs)
    assert out[0]["tool_calls"][0]["function"]["arguments"] == {"_unparsed": "{not json"}, out


def inbound_empty_arguments_become_empty_object():
    msgs = [{"role": "assistant", "content": "x",
             "tool_calls": [{"function": {"name": "f", "arguments": "   "}}]}]
    out = translate.to_provider(msgs)
    assert out[0]["tool_calls"][0]["function"]["arguments"] == {}, out


def inbound_plain_messages_ride_through():
    msgs = [{"role": "user", "content": "hi"}, {"role": "tool", "content": "42", "tool_call_id": "call_x"}]
    assert translate.to_provider(msgs) == msgs


def outbound_object_arguments_become_strings_with_id_and_type():
    answer = {"text": "", "role": "assistant",
              "tool_calls": [{"function": {"name": "read_file", "arguments": {"path": "a.py"}}}]}
    msg = translate.to_openai(answer)
    call = msg["tool_calls"][0]
    assert call["type"] == "function", call
    assert call["id"].startswith("call_") and len(call["id"]) > 5, call
    assert isinstance(call["function"]["arguments"], str), call
    assert json.loads(call["function"]["arguments"]) == {"path": "a.py"}, call
    assert call["function"]["name"] == "read_file"
    assert msg["content"] is None, "empty text beside tool calls must be null content"


def outbound_ids_are_distinct_per_call():
    answer = {"text": "", "tool_calls": [{"function": {"name": "a", "arguments": {}}},
                                         {"function": {"name": "b", "arguments": {}}}]}
    ids = [c["id"] for c in translate.to_openai(answer)["tool_calls"]]
    assert len(set(ids)) == 2, ids


def outbound_text_only_has_no_tool_calls_key():
    msg = translate.to_openai({"text": "alive", "role": "assistant", "tool_calls": []})
    assert msg == {"role": "assistant", "content": "alive"}, msg


def envelope_finish_reason_follows_tool_calls():
    plain = translate.completion({"text": "alive"}, "m", {"prompt_tokens": 3, "completion_tokens": 2})
    assert plain["object"] == "chat.completion" and plain["id"].startswith("chatcmpl-"), plain
    assert plain["model"] == "m"
    assert plain["choices"][0]["finish_reason"] == "stop", plain
    assert plain["usage"] == {"prompt_tokens": 3, "completion_tokens": 2, "total_tokens": 5}, plain
    tooled = translate.completion({"text": "", "tool_calls": [{"function": {"name": "f", "arguments": {}}}]}, "m")
    assert tooled["choices"][0]["finish_reason"] == "tool_calls", tooled
    assert tooled["usage"] == {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}, \
        "absent usage reads 0, never invented"


def translate_imports_stdlib_only():
    found = imports_in((HERE / "translate.py").read_text(encoding="utf-8"))
    assert found and not any(m == "cairn" or m.startswith("cairn.") for m in found), found
    assert found <= {"json", "time", "uuid"}, found


TEETH = [
    inbound_string_arguments_become_objects,
    inbound_does_not_mutate_its_input,
    inbound_unparseable_arguments_stay_loud,
    inbound_empty_arguments_become_empty_object,
    inbound_plain_messages_ride_through,
    outbound_object_arguments_become_strings_with_id_and_type,
    outbound_ids_are_distinct_per_call,
    outbound_text_only_has_no_tool_calls_key,
    envelope_finish_reason_follows_tool_calls,
    translate_imports_stdlib_only,
]

if __name__ == "__main__":
    for tooth in TEETH:
        _tooth(tooth.__name__, tooth)
    print(f"\n{PASS} passed, {FAIL} failed out of {PASS + FAIL}")
    sys.exit(1 if FAIL else 0)
