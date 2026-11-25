"""Safe local WH Okna catalogue probe; no click, focus, save, SQL or API.

Use in a local Windows session with one visible WH Okna wizard (foreground not required):
  python tools/inspect_navimind_catalogues_live.py
  python tools/inspect_navimind_catalogues_live.py --show-local-options

The operator may MANUALLY open a dropdown before the second call. A native popup may close when focus changes, so lack of rows is not proof of an empty catalogue. Output
labels are shown locally only and are NOT sent to a server by this script.
They are NOT asserted to belong to a particular dropdown until native
ancestry and a selection readback are separately proven.
"""
from __future__ import annotations

import argparse
import json
import os
import sys


def run_probe(*, show_local_options=False, observe=None):
    from app.agent.runtime.navimind_catalogue_readiness import (
        inspect_catalogue_scene, summarize_catalogue_readiness,
        visible_unattributed_catalogue_items,
    )
    if observe is None:
        from app.agent.runtime.navimind_catalogue_background_probe import (
            read_catalogue_window_without_focus,
        )
        scene, reason = read_catalogue_window_without_focus()
        if scene is None:
            return {
                "error": reason,
                "input_performed": False,
                "foreground_changed": False,
            }
    else:
        scene = observe()
    audit = inspect_catalogue_scene(scene)
    result = {
        "summary": summarize_catalogue_readiness(audit),
        "visible_unattributed_items": visible_unattributed_catalogue_items(scene),
        "options_owned_by_specific_field": False,
        "selection_test_performed": False,
        "input_performed": False,
        "database_connection_performed": False,
        "data_sent_to_cloud": False,
    }
    if show_local_options:
        result["unattributed_local_option_labels"] = list(
            visible_unattributed_catalogue_items(
                scene, include_labels=True, limit=25,
            )
        )
        result["warning"] = (
            "List item names shown ONLY on this computer. "
            "Do not assume they belong to the active combo. "
            "Remove client or pricing data before sharing output."
        )
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--show-local-options", action="store_true",
        help="Display up to 25 currently visible native list rows locally.",
    )
    args = parser.parse_args(argv)
    initialized = False
    try:
        if os.name == "nt":
            try:
                import pythoncom
                pythoncom.CoInitialize()
                initialized = True
            except ImportError:
                pass
        report = run_probe(show_local_options=args.show_local_options)
    except Exception as exc:
        report = {
            "error": "local_catalogue_observation_failed",
            "error_type": type(exc).__name__,
            "input_performed": False,
        }
    finally:
        if initialized:
            pythoncom.CoUninitialize()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if "error" not in report else 2


if __name__ == "__main__":
    raise SystemExit(main())
