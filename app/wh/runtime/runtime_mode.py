from enum import Enum


class RuntimeMode(str, Enum):

    DRY_RUN = "dry_run"

    REAL_RUN = "real_run"

    DEBUG = "debug"