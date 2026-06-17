from dataclasses import dataclass


@dataclass
class AgentEvent:

    type: str

    message: str