"""Shared entry point to the trouble lane — the tool-level interface.

The trouble DEVICE (cairn/devices/trouble/) owns the lane (Law 6), and its
single-door guarantee holds: every write goes through TroubleDevice. This module
re-exports TroubleDevice at the tool rung so devices other than db_domain can
file troubles without a cross-device import (ruling 2026-08-31: no device may
import another device except the database).
"""

from cairn.devices.trouble.trouble import TroubleDevice

__all__ = ["TroubleDevice"]
