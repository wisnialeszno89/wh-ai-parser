import unittest

from app.actions.models.action import Action
from app.simulator.window_simulator import WindowSimulator


class WindowSimulatorTests(unittest.TestCase):
    def _build_two_sash_window(self) -> WindowSimulator:
        simulator = WindowSimulator()
        result = simulator.apply(
            [
                Action("select_tool", tool_name="frame_tool"),
                Action("draw_frame"),
                Action("select_tool", tool_name="mullion_tool"),
                Action("insert_mullion"),
                Action("select_tool", tool_name="sash_tool"),
                Action("add_sash", value="left"),
                Action("add_sash", value="right"),
                Action("select_tool", tool_name="glass_tool"),
                Action("add_glass", value="left"),
                Action("add_glass", value="right"),
            ]
        )
        self.assertEqual(result.rejected, ())
        return simulator

    def test_build_two_sash_window(self) -> None:
        simulator = self._build_two_sash_window()

        self.assertEqual(
            simulator.scene.kinds(),
            ("FRAME", "MULLION", "SASH", "SASH", "GLASS", "GLASS"),
        )
        self.assertTrue(simulator.scene.has("SASH", side="left"))
        self.assertTrue(simulator.scene.has("SASH", side="right"))

    def test_dependency_guard_rejects_glass_without_sash(self) -> None:
        simulator = WindowSimulator()
        result = simulator.apply(
            [
                Action("select_tool", tool_name="glass_tool"),
                Action("add_glass", value="left"),
            ]
        )
        self.assertEqual(len(result.rejected), 1)
        self.assertEqual(simulator.scene.elements, [])

    def test_hardware_requires_product_selection(self) -> None:
        simulator = self._build_two_sash_window()
        result = simulator.apply(
            [
                Action("select_tool", tool_name="hardware_tool"),
                Action("add_hardware"),
            ]
        )

        self.assertEqual(result.rejected, ("add_hardware: hardware product must be selected",))
        self.assertFalse(simulator.hardware_readiness().ready)
        self.assertEqual(simulator.scene.kinds(), ("FRAME", "MULLION", "SASH", "SASH", "GLASS", "GLASS"))

    def test_hardware_select_activpilot_and_install_both_sashes(self) -> None:
        simulator = self._build_two_sash_window()
        result = simulator.apply(
            [
                Action("select_tool", tool_name="hardware_tool"),
                Action("select_hardware", value="UR ActivPilot"),
                Action("add_hardware"),
            ]
        )

        self.assertEqual(result.rejected, ())
        self.assertEqual(
            simulator.scene.kinds(),
            ("FRAME", "MULLION", "SASH", "SASH", "GLASS", "GLASS", "HARDWARE", "HARDWARE"),
        )
        self.assertEqual(simulator.hardware.selected.product, "UR ActivPilot")
        self.assertEqual(simulator.hardware.installed_sides, {"left", "right"})
        self.assertTrue(simulator.hardware_readiness().ready)
        self.assertEqual(
            simulator.hardware_readiness().reason,
            "hardware is installed on all required sashes",
        )

    def test_hardware_rejects_incomplete_two_sash_structure(self) -> None:
        simulator = WindowSimulator()
        result = simulator.apply(
            [
                Action("select_tool", tool_name="frame_tool"),
                Action("draw_frame"),
                Action("select_tool", tool_name="sash_tool"),
                Action("add_sash", value="left"),
                Action("select_tool", tool_name="hardware_tool"),
                Action("select_hardware", value="UR ActivPilot"),
                Action("add_hardware"),
            ]
        )

        self.assertEqual(result.rejected, ("add_hardware: SASH sides missing: right",))
        self.assertFalse(simulator.hardware_readiness().ready)
        self.assertEqual(simulator.scene.kinds(), ("FRAME", "SASH"))


if __name__ == "__main__":
    unittest.main()
