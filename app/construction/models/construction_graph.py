from dataclasses import dataclass

from app.construction.models.construction_node import (
    ConstructionNode
)


@dataclass
class ConstructionGraph:

    root: ConstructionNode