"""A reach fixture — a meta-proof: runs the green fixture proof as a python subprocess.

Sealed by test_a_seal_records_what_it_reached.py (ticket 734b22d09f2e, clause 5): the
subprocess's loaded files are unioned into the seal's fingerprint_closure, so a change to
green_proof.py alone expires this seal.
"""
import subprocess
import sys
from pathlib import Path

subprocess.run([sys.executable, str(Path(__file__).resolve().parent / "green_proof.py")],
               check=True, capture_output=True)
print("  ok   test_the_fixture_ran_a_proof")
raise SystemExit(0)
