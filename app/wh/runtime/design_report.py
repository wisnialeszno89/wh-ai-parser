from dataclasses import (
    dataclass,
    field
)

from app.wh.runtime.topology_candidate import (
    TopologyCandidate
)


@dataclass
class DesignReport:

    winner: TopologyCandidate = None

    candidates: list = field(

        default_factory=list

    )