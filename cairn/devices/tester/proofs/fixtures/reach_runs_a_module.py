"""A reach fixture — imports nothing from cairn itself, and runs `python -m` on a module of
another component (system_word) as a subprocess.

Sealed by test_a_seal_records_what_it_reached.py (ticket 734b22d09f2e, clause 2): the
subprocess's reach rides the seal, so cairn/tools/system_word lands in evidence.reached.
"""
import subprocess
import sys

subprocess.run([sys.executable, "-W", "ignore", "-m", "cairn.tools.system_word.system_word"],
               check=True)
print("  ok   test_the_fixture_ran_a_module")
raise SystemExit(0)
