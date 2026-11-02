from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

import pytest


@pytest.mark.skipif(
    os.name == "nt",
    reason="The subprocess guard test must not run live Windows diagnostics.",
)
def test_dialog_diagnostic_script_resolves_repo_import_from_outside_root(
    tmp_path: Path,
):
    repository_root = Path(__file__).resolve().parents[1]
    script = repository_root / "tools" / "diagnose_windowhub_dialog_children.py"

    completed = subprocess.run(
        [sys.executable, str(script)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )

    # On non-Windows hosts, successful imports reach the platform guard.
    # Import errors instead produce a traceback and a different exit code.
    assert completed.returncode == 2
    assert '"reason": "requires_windows"' in completed.stdout
    assert "ModuleNotFoundError" not in completed.stderr
    assert "Traceback" not in completed.stderr
