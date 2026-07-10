from enum import Enum


class ExecutionMode(Enum):

    DRY_RUN = "dry_run"

    MOVE_ONLY = "move_only"

    LIVE = "live"