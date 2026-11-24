"""Describe precisely what the Top Trans request means before GUI entry."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.runtime.navimind_toptrans_live_preflight import (
    top_trans_acceptance, top_trans_report,
)


if __name__ == "__main__":
    print(top_trans_report(), end="")
    print("SPECIFICATION_JSON_BEGIN")
    print(top_trans_acceptance().serialize())
    print("SPECIFICATION_JSON_END")
