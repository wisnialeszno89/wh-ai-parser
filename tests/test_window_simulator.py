import unittest

from app.actions.models.action import Action
from app.simulator.window_simulator import WindowSimulator


class WindowSimulatorTests(unittest.TestCase):
    def test_build_two_sash_window(self) -> None:
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


if __name__ == "__main__":
    unittest.main()
