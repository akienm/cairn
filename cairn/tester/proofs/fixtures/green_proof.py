"""A deliberately-passing proof fixture — exits 0.

Not a proof of anything real; it exists so test_tester.py can point the tester at a
known-green subject and assert it validates green. Run by the tester as a subprocess.
"""

raise SystemExit(0)
