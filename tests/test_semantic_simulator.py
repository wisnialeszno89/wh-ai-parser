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
