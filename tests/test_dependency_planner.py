from app.gui.enums.gui_tool import GuiTool
from app.window_model.dependency_planner import DependencyPlanner
from app.window_model.model import WindowElementType, WindowModel
from app.window_model.topology import WindowSide, WindowTopology


def test_dependency_planner_orders_construction_steps():
    model = WindowModel(properties={"width": 1000, "height": 1000, "schema": "R"})
    model.add_element(
        "frame",
        WindowElementType.FRAME,
        role="frame",
    )
    model.add_element(
        "cell_left",
        WindowElementType.MULLION,
        parent_id="frame",
        role="CELL",
    )
    model.add_element(
        "sash_left",
        WindowElementType.SASH,
        parent_id="cell_left",
        opening="TURN",
    )
    model.add_element(
        "glass_left",
        WindowElementType.GLASS,
        parent_id="sash_left",
        panes=3,
    )
    model.add_element(
        "hardware_left",
        WindowElementType.HARDWARE,
        parent_id="sash_left",
        system="unknown",
    )

    topology = WindowTopology()
    topology.add(model.elements["frame"], side=WindowSide.UNKNOWN)
    topology.add(model.elements["cell_left"], side=WindowSide.LEFT)
    topology.add(model.elements["sash_left"], side=WindowSide.LEFT)
    topology.add(model.elements["glass_left"], side=WindowSide.LEFT)
    topology.add(model.elements["hardware_left"], side=WindowSide.LEFT)

    plan = DependencyPlanner().plan(model, topology)

    assert [step.element_id for step in plan] == [
        "frame",
        "cell_left",
        "sash_left",
        "glass_left",
        "hardware_left",
    ]

    assert [step.gui_tool for step in plan] == [
        GuiTool.FRAME,
        GuiTool.MULLION,
        GuiTool.SASH,
        GuiTool.GLASS,
        GuiTool.HARDWARE,
    ]

    assert plan[-1].side == WindowSide.LEFT

def test_dependency_planner_preserves_sash_semantic_properties():
    model = WindowModel(properties={"width": 2000, "height": 1500, "schema": "RU|FIX"})
    model.add_element("frame", WindowElementType.FRAME)
    model.add_element(
        "cell_left",
        WindowElementType.MULLION,
        parent_id="frame",
        role="CELL",
    )
    model.add_element(
        "sash_left",
        WindowElementType.SASH,
        parent_id="cell_left",
        opening="tilt_turn",
        direction="RIGHT",
        width_ratio=0.5,
        height_ratio=1.0,
    )

    topology = WindowTopology()
    topology.add(model.elements["frame"], side=WindowSide.CENTER)
    topology.add(model.elements["cell_left"], side=WindowSide.LEFT)
    topology.add(model.elements["sash_left"], side=WindowSide.LEFT, opening="tilt_turn")

    plan = DependencyPlanner().plan(model, topology)

    sash_step = next(step for step in plan if step.element_id == "sash_left")

    assert sash_step.properties["opening"] == "tilt_turn"
    assert sash_step.properties["direction"] == "RIGHT"
    assert sash_step.properties["width_ratio"] == 0.5
    assert sash_step.properties["height_ratio"] == 1.0
