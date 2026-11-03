import os
import subprocess
import sys
from pathlib import Path

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPOSITORY_ROOT / "tools" / "live_windowhub_quantity_action.py"


@pytest.mark.skipif(os.name != "nt", reason="The live WindowHub tool is Windows-only.")
def test_live_quantity_tool_resolves_repository_imports_when_run_as_script():
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    assert "--quantity" in result.stdout
    assert "--execute-live" in result.stdout
    assert "--focus-delay-seconds" in result.stdout
