"""Read-only local preflight for supervised NaviMind / WindowHub acceptance.

No WindowHub activation, clicks, screenshots, PDF reads, credentials output,
network calls or model invocation. Never grants a native input permit.
Run: python tools/run_navimind_offer_preflight.py
"""
from __future__ import annotations

import importlib.util
import json
import os
import platform
import sys


def _has_module(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ModuleNotFoundError, ValueError):
        return False


def inspect_local_preflight(*, environ=None, module_probe=None,
                            system=None, python_version=None) -> dict:
    """Pure, reproducible capability report. Never include secret contents."""
    env = os.environ if environ is None else environ
    probe = _has_module if module_probe is None else module_probe
    os_name = platform.system() if system is None else system
    py = sys.version_info[:2] if python_version is None else python_version
    modules = {
        name: bool(probe(name))
        for name in (
            "pywinauto", "pythoncom", "fitz", "dotenv", "requests",
        )
    }
    live_flag = (
        env.get("WH_REAL_WINDOWHUB") == "1"
        and env.get("COMPUTER_USE_LIVE") == "1"
    )
    reasoner_url_present = bool(
        str(env.get("NAVIMIND_AGENT_V2_URL") or
            env.get("NAVIMIND_AGENT_URL") or "").strip()
    )
    secret_present = bool(str(env.get("NAVIMIND_AGENT_SECRET") or "").strip())
    warnings = []
    if os_name != "Windows":
        warnings.append("requires_windows_desktop")
    if py < (3, 10):
        warnings.append("python_3_10_or_newer_required")
    for module, installed in modules.items():
        if not installed:
            warnings.append("missing_" + module)
    if not reasoner_url_present:
        warnings.append("reasoner_endpoint_not_configured_in_process")
    if not secret_present:
        warnings.append("reasoner_secret_not_configured_in_process")
    if not live_flag:
        warnings.append("native_input_not_armed")
    return {
        "platform": os_name,
        "python_major_minor": ".".join(map(str, py)),
        "dependencies": modules,
        "reasoner_url_configured": reasoner_url_present,
        "reasoner_secret_configured": secret_present,
        "live_flags_both_enabled": live_flag,
        "read_only_preflight": True,
        "network_checked": False,
        "windowhub_observed": False,
        "real_desktop_test_completed": False,
        "warnings": warnings,
    }


def main() -> int:
    # Native buttons are NEVER activated from preflight.
    report = inspect_local_preflight()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
