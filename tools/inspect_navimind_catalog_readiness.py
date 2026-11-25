"""No-click local catalogue map audit of the currently open WindowHub wizard.

Usage:
    python tools/inspect_navimind_catalog_readiness.py
    python tools/inspect_navimind_catalog_readiness.py --observe

Default prints the known fields and limitations with no Windows access.
--observe captures ONE local foreground UIA snapshot (no clicks, no PDF,
no HTTP or SQL access). Values and user/customer information are omitted.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.agent.runtime.navimind_catalog_audit import (
    CATALOG_FIELD_GROUPS,
    audit_catalogue_scene,
)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--observe", action="store_true",
        help="Read one local foreground desktop scene; no clicks or HTTP",
    )
    args = parser.parse_args(argv)
    if not args.observe:
        report = {
            "mode": "offline",
            "groups": {key: list(value) for key, value in CATALOG_FIELD_GROUPS.items()},
            "next_step": "Open an unsaved WindowHub test offer wizard, "
                         "navigate manually to the chosen catalogue page, "
                         "then run this command with --observe.",
            "catalogue_verified": False,
            "no_input": True,
        }
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    if sys.platform != "win32":
        print(json.dumps({
            "status": "windows_required", "no_input": True,
        }))
        return 2
    # COM initialization is restricted to the one observing thread.
    import pythoncom
    pythoncom.CoInitialize()
    try:
        from app.agent.runtime.windows_desktop_agent_control_loop import (
            create_windows_desktop_agent_control_loop,
        )
        from app.agent.perception.windowhub_semantic_world import (
            enrich_windowhub_scene,
        )
        from app.agent.runtime.windowhub_mdi_native_probe import (
            enrich_native_mdi_document_scope,
        )
        loop = create_windows_desktop_agent_control_loop()
        scene = enrich_windowhub_scene(
            enrich_native_mdi_document_scope(loop.observe_scene())
        )
        report = audit_catalogue_scene(scene).safe_summary()
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report["safe_observation"] else 3
    except Exception as exc:
        # Do not print raw exceptions that could contain local paths, the
        # connection string or customer data.
        print(json.dumps({
            "status": "observation_unavailable",
            "error_type": type(exc).__name__,
            "no_input": True,
        }))
        return 4
    finally:
        pythoncom.CoUninitialize()


if __name__ == "__main__":
    raise SystemExit(main())
