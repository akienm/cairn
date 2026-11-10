"""Fixture for test_an_admission_holds_at_any_depth.py, tooth 1: a synthetic graph and a rule
admitting a file no repo holds (bus/proofs/test_x.py). It berths under fixtures/ so the admission
sieve (build_inspector's sole_path_admissions_are_entered) does not read it as a live rule
(ticket 3751ba501581)."""

DIALS = ("urllib.request", "urllib.error", "http.client", "requests", "httpx",
         "aiohttp", "socket", "ftplib", "telnetlib")

GRAPH = {"cairn/machines/bus/proofs/test_x.py": {"socket"},
         "cairn/machines/bus/other.py": {"socket"},
         "cairn/machines/xbus/proofs/test_x.py": {"socket"}}
RULE = {"kind": "sole_path", "capability": "the host", "modules": DIALS,
        "only": ("bus/proofs/test_x.py",)}
