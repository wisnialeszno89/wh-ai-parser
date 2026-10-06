from enum import Enum


class AgentMode(str, Enum):
    """
    High-level operating mode for the digital worker.

    Autonomous execution is controlled separately by the runtime.
    This mode describes the user's interaction with the worker.
    """

    EXECUTE = "execute"
    LEARN = "learn"
    ASSIST = "assist"
