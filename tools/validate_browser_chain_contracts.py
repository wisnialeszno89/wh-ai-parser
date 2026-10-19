"""Small static audit for the staged browser integration chain.

This helper intentionally performs no network or browser actions. It checks
that the expected provider-neutral browser contract files and fail-closed
configuration markers remain present before the staged PR chain is advanced.
Run from the repository root: python tools/validate_browser_chain_contracts.py
"""
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = (
    "app/agent/adapters/browser_adapter.py",
    "app/agent/execution/playwright_browser_provider.py",
    "tests/test_browser_adapter.py",
    "tests/test_browser_verification.py",
    "tests/test_playwright_browser_provider.py",
    "tests/test_browser_navimind_bridge.py",
)
REQUIRED_MARKERS = {
    "app/agent/execution/playwright_browser_provider.py": (
        "AGENT_BROWSER_ENABLED",
        "SUPPORTED_BROWSER_TYPES",
    ),
    "app/agent/adapters/browser_adapter.py": (
        "_validate_url",
        "BrowserPage",
    ),
}


def main() -> int:
    failures: list[str] = []
    for relative in REQUIRED_FILES:
        if not (ROOT / relative).is_file():
            failures.append(f"missing required contract file: {relative}")

    for relative, markers in REQUIRED_MARKERS.items():
        path = ROOT / relative
        if not path.is_file():
            continue
        content = path.read_text(encoding="utf-8-sig")
        for marker in markers:
            if marker not in content:
                failures.append(f"{relative}: required marker not found: {marker}")

    if failures:
        print("Browser chain static validation FAILED:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print(f"Browser chain static validation passed ({len(REQUIRED_FILES)} files).")
    print("This is a file/contract-presence check, not a substitute for pytest or live E2E.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
