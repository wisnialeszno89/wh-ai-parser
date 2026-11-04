"""Safe CLI smoke: help must never touch the desktop."""
import os
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "live_windowhub_next_step.py"


@pytest.mark.skipif(os.name != "nt", reason="Live WindowHub tool is Windows-only.")
def test_next_step_cli_bootstraps_repo_and_exposes_explicit_live_opt_in():
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        cwd=ROOT, capture_output=True, text=True, timeout=20, check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert "--quantity" in result.stdout
    assert "--execute-live" in result.stdout
    assert "--focus-delay-seconds" in result.stdout
