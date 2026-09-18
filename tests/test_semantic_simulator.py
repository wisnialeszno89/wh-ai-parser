import unittest

from app.simulator.semantic_runner import SemanticWindowSimulator
from app.window_model.semantic_executor import two_cell_target


class SemanticSimulatorTests(unittest.TestCase):
    def test_two_cell_target_runs_to_hardware_ready(self) -> None:
        desired, topology = two_cell_target()
        runner = SemanticWindowSimulator()

        result = runner.run(desired, topology)

        self.assertEqual(result.simulation.rejected, ())
        self.assertEqual(
            result.simulation.applied,
            (
                "select_tool",
                "draw_frame",
                "select_tool",
                "insert_mullion",
                "select_tool",
                "add_sash",
                "select_tool",
                "add_sash",
                "select_tool",
                "add_glass",
                "select_tool",
                "add_glass",
                "select_tool",
                "select_hardware",
                "add_hardware",
            ),
        )
        self.assertEqual(
            tuple(item["kind"] for item in result.final_snapshot["elements"]),
            (
                "FRAME",
                "MULLION",
                "SASH",
                "SASH",
                "GLASS",
                "GLASS",
                "HARDWARE",
                "HARDWARE",
            ),
        )
        self.assertEqual(
            runner.simulator.hardware.selected.product,
            "UR Activpilot",
        )
        self.assertTrue(runner.simulator.hardware_readiness().ready)

    def test_hardware_is_not_selected_before_structure_is_built(self) -> None:
        desired, topology = two_cell_target()
        runner = SemanticWindowSimulator()
        actions = runner.build_actions(desired, topology)

        hardware_index = next(
            i
            for i, action in enumerate(actions)
            if action.action_type == "select_hardware"
        )
        structure = actions[:hardware_index]

        runner.simulator.apply(structure)

        self.assertFalse(runner.simulator.hardware_readiness().ready)
        self.assertIsNone(runner.simulator.hardware.selected)
        self.assertEqual(
            tuple(item.kind for item in runner.simulator.scene.elements),
            ("FRAME", "MULLION", "SASH", "SASH", "GLASS", "GLASS"),
        )

    def test_explicit_hardware_system_is_preserved(self) -> None:
        desired, topology = two_cell_target()
        desired.elements["hardware_left"].properties["system"] = "activPilot Concept"

        runner = SemanticWindowSimulator()
        result = runner.run(desired, topology)

        self.assertEqual(result.simulation.rejected, ())
        self.assertEqual(
            runner.simulator.hardware.selected.product,
            "activPilot Concept",
        )
        self.assertTrue(runner.simulator.hardware_readiness().ready)


if __name__ == "__main__":
    unittest.main()


def test_semantic_bridge_forwards_sash_properties_to_executor():
    from types import SimpleNamespace

    from app.gui.enums.gui_intent import GuiIntent
    from app.gui.enums.gui_tool import GuiTool
    from app.window_model.model import WindowElementType, WindowModel
    from app.window_model.semantic_executor import SemanticExecutionBridge
    from app.window_model.topology import WindowSide, WindowTopology

    class FakeExecutor:
        def __init__(self):
            self.actions = []
            self.context = SimpleNamespace(
                gui_state=SimpleNamespace(
                    last_created_point=(100, 100),
                    created_element_points={},
                    created_element_sides={},
                    panel_side=None,
                )
            )

        def execute(self, action):
            self.actions.append(action)
            return SimpleNamespace(success=True)

    model = WindowModel(
        properties={"width": 2000, "height": 1500, "schema": "RU|FIX"}
    )
    frame = model.add_element("frame", WindowElementType.FRAME)
    cell = model.add_element(
        "cell_left",
        WindowElementType.MULLION,
        parent_id=frame.id,
        role="CELL",
    )
    sash = model.add_element(
        "sash_left",
        WindowElementType.SASH,
        parent_id=cell.id,
        opening="tilt_turn",
        direction="RIGHT",
        width_ratio=0.5,
        height_ratio=1.0,
    )

    topology = WindowTopology()
    topology.add(frame, side=WindowSide.CENTER)
    topology.add(cell, side=WindowSide.LEFT, role="CELL")
    topology.add(sash, side=WindowSide.LEFT, opening="tilt_turn")

    observed = WindowModel(
        properties={"width": 2000, "height": 1500, "schema": "RU|FIX"}
    )
    observed_frame = observed.add_element("frame", WindowElementType.FRAME)
    observed_cell = observed.add_element(
        "cell_left",
        WindowElementType.MULLION,
        parent_id=observed_frame.id,
        role="CELL",
    )

    executor = FakeExecutor()
    bridge = SemanticExecutionBridge(executor)

    result = bridge.execute_next(
        desired=model,
        topology=topology,
        observed=observed,
    )

    assert result.executed == ("sash_left",)
    assert len(executor.actions) == 1

    sash_action = executor.actions[0]
    assert sash_action.intent == GuiIntent.CREATE
    assert sash_action.tool == GuiTool.SASH
    assert sash_action.semantic_id == "sash_left"
    assert sash_action.semantic_side == "LEFT"
    assert sash_action.properties["opening"] == "tilt_turn"
    assert sash_action.properties["direction"] == "RIGHT"
    assert sash_action.properties["width_ratio"] == 0.5
    assert sash_action.properties["height_ratio"] == 1.0

def test_semantic_bridge_applies_sash_direction_to_panel_side():
    from types import SimpleNamespace

    from app.window_model.model import WindowElementType, WindowModel
    from app.window_model.semantic_executor import SemanticExecutionBridge
    from app.window_model.topology import WindowSide, WindowTopology

    model = WindowModel(
        properties={"width": 2000, "height": 1500, "schema": "RU|FIX"}
    )
    frame = model.add_element("frame", WindowElementType.FRAME)
    cell = model.add_element(
        "cell_right",
        WindowElementType.MULLION,
        parent_id=frame.id,
        role="CELL",
    )
    model.add_element(
        "sash_right",
        WindowElementType.SASH,
        parent_id=cell.id,
        opening="tilt_turn",
        direction="RIGHT",
    )

    topology = WindowTopology()
    topology.add(frame, side=WindowSide.CENTER)
    topology.add(cell, side=WindowSide.RIGHT, role="CELL")
    topology.add(
        model.elements["sash_right"],
        side=WindowSide.RIGHT,
        opening="tilt_turn",
    )

    observed = WindowModel(
        properties={"width": 2000, "height": 1500, "schema": "RU|FIX"}
    )
    observed_frame = observed.add_element("frame", WindowElementType.FRAME)
    observed.add_element(
        "cell_right",
        WindowElementType.MULLION,
        parent_id=observed_frame.id,
        role="CELL",
    )

    executor = SimpleNamespace(
        actions=[],
        context=SimpleNamespace(
            gui_state=SimpleNamespace(
                last_created_point=(100, 100),
                created_element_points={},
                created_element_sides={},
                panel_side=None,
            )
        ),
    )

    def execute(action):
        executor.actions.append(action)
        return SimpleNamespace(success=True)

    executor.execute = execute

    result = SemanticExecutionBridge(executor).execute_next(
        desired=model,
        topology=topology,
        observed=observed,
    )

    assert result.executed == ("sash_right",)
    assert executor.context.gui_state.panel_side == "right"
