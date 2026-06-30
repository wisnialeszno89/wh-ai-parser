from dataclasses import dataclass, field


@dataclass
class ConstructionNode:

    node_type: str

    children: list["ConstructionNode"] = field(
        default_factory=list
    )

    payload: dict = field(
        default_factory=dict
    )

    def add_child(
        self,
        child: "ConstructionNode"
    ):

        self.children.append(child)