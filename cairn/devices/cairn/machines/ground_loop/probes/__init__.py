"""The ground loop's registration folder — it holds no probes, and that is the point.

Discovery names a device by the folder that holds its ``probes/`` (``discovery.device_folders``),
and ``reach``/``shim_for`` find a device's ``shim.py`` beside that folder. The heartbeat's six
probes were deleted in 6c7fdb62 (bae622881f03: nothing fires on the beat), which left this folder
on disk holding only stale ``__pycache__`` — untracked, so a clean checkout had no ground loop on
the roster and ``reach("ground_loop")`` raised LookupError once efb670ff1dd8 dropped the
listener's special name. Measured by efb's hollow re-read 2026-10-02.

So the folder is tracked by this file alone: an empty watch folder is a device with nothing to
fire, which is honest, not absent (``device_folders``' own docstring).
"""
