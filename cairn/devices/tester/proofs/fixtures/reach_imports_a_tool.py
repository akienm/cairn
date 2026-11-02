"""A reach fixture — imports one other component (validation_store) and exits green.

Sealed by test_a_seal_records_what_it_reached.py (ticket 734b22d09f2e, clause 1): the seal
must carry cairn/tools/validation_store in evidence.reached.
"""
import cairn.tools.validation_store.validation_store  # noqa: F401

print("  ok   test_the_fixture_imported_a_tool")
raise SystemExit(0)
