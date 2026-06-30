from app.construction.models.construction_node import (
    ConstructionNode
)


def test_graph():

    frame = ConstructionNode("FRAME")

    sash = ConstructionNode("SASH")

    frame.add_child(sash)

    assert len(frame.children) == 1

    assert frame.children[0].node_type == "SASH"