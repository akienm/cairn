"""A deliberately-failing proof fixture — exits non-zero.

The hollow-tester killer's ammunition: test_tester.py points the tester at this
known-red subject and asserts it validates RED. An always-green tester passes every
other check and dies on this one. Run by the tester as a subprocess.
"""

raise SystemExit(1)
