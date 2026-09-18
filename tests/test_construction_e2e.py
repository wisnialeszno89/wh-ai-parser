import unittest

from app.wh.runtime.construction_parser import ConstructionParser
from app.wh.runtime.construction_normalizer import ConstructionNormalizer
from app.window_model.construction_mapper import ConstructionMapper
from app.simulator.semantic_runner import SemanticWindowSimulator
from app.window_model.model import WindowElementType


class ConstructionE2ETests(unittest.TestCase):
    def test_ru_ru_request_builds_complete_simulated_window(self) -> None:
        normalized = ConstructionNormalizer().normalize("RU+RU")
        schema = ConstructionParser().parse(normalized)

        schema.width = 2100
        schema.height = 1500

        model, topology = ConstructionMapper().map(schema)

        self.assertEqual(model.properties["width"], 2100)
        self.assertEqual(model.properties["height"], 1500)
        self.assertEqual(model.properties["cells"], 2)

        self.assertEqual(
            len(model.elements_of_type(WindowElementType.FRAME)),
            1,
        )
        self.assertEqual(
            len(model.elements_of_type(WindowElementType.SASH)),
            2,
        )
        self.assertEqual(
            len(model.elements_of_type(WindowElementType.GLASS)),
            2,
        )
        self.assertEqual(
            len(model.elements_of_type(WindowElementType.HARDWARE)),
            2,
        )

        runner = SemanticWindowSimulator()
        result = runner.run(model, topology)

        self.assertEqual(result.simulation.rejected, ())
        self.assertTrue(
            runner.simulator.hardware_readiness().ready
        )
        self.assertEqual(
            runner.simulator.hardware.selected.product,
            "UR Activpilot",
        )


def test_agent_compiler_model_can_reconstruct_semantic_topology() -> None:
    from app.agent.offers.agent_construction_compiler import (
        AgentConstructionCompiler,
    )
    from app.agent.offers.offer_context import OfferContext
    from app.window_model.construction_mapper import ConstructionMapper
    from app.window_model.model import WindowElementType
    from app.window_model.topology import infer_topology

    context = OfferContext(
        raw_request="Okno 2000x1500 DKR + FIX",
        width=2000,
        height=1500,
        product_type="window",
        openings=(
            "RIGHT_TILT_TURN",
            "FIX",
        ),
    )

    project = AgentConstructionCompiler().compile(context)

    assert project is not None

    model, mapped_topology = ConstructionMapper().map_project(project)

    topology = infer_topology(model)

    sashes = model.elements_of_type(WindowElementType.SASH)

    assert len(sashes) == 2

    first_sash_node = topology.node(sashes[0].id)
    second_sash_node = topology.node(sashes[1].id)

    assert first_sash_node is not None
    assert second_sash_node is not None

    assert first_sash_node.opening == "tilt_turn"
    assert second_sash_node.opening == "fix"

    assert sashes[0].properties["direction"] == "RIGHT"
    assert sashes[1].properties["direction"] == "NONE"


def test_agent_compiler_builds_directional_multi_opening_project() -> None:
    from app.agent.offers.agent_construction_compiler import (
        AgentConstructionCompiler,
    )
    from app.agent.offers.offer_context import OfferContext
    from app.wh.model.opening import Opening

    context = OfferContext(
        raw_request="Okno 2000x1500 DKR + FIX",
        width=2000,
        height=1500,
        product_type="window",
        openings=(
            "RIGHT_TILT_TURN",
            "FIX",
        ),
    )

    project = AgentConstructionCompiler().compile(context)

    assert project is not None
    assert project.schema.width == 2000
    assert project.schema.height == 1500
    assert len(project.schema.segments) == 2

    assert project.schema.segments[0].opening == Opening.TILT_TURN
    assert project.schema.segments[0].direction == "RIGHT"

    assert project.schema.segments[1].opening == Opening.FIX
    assert project.schema.segments[1].direction == "NONE"


def test_agent_compiler_maps_directional_project_to_window_model() -> None:
    from app.agent.offers.agent_construction_compiler import (
        AgentConstructionCompiler,
    )
    from app.agent.offers.offer_context import OfferContext
    from app.wh.model.opening import Opening
    from app.window_model.construction_mapper import ConstructionMapper

    context = OfferContext(
        raw_request="Okno 2000x1500 DKR + FIX",
        width=2000,
        height=1500,
        product_type="window",
        openings=(
            "RIGHT_TILT_TURN",
            "FIX",
        ),
    )

    project = AgentConstructionCompiler().compile(context)

    assert project is not None

    model, topology = ConstructionMapper().map_project(
        project
    )

    assert model.properties["width"] == 2000
    assert model.properties["height"] == 1500
    assert model.properties["cells"] == 2

    sashes = model.elements_of_type(
        WindowElementType.SASH
    )

    assert len(sashes) == 2
    assert sashes[0].properties["opening"] == (
        Opening.TILT_TURN.value
    )
    assert sashes[1].properties["opening"] == (
        Opening.FIX.value
    )

    assert sashes[0].properties["direction"] == "RIGHT"
    assert sashes[1].properties["direction"] == "NONE"


def test_agent_compiler_to_semantic_bridge_preserves_direction_and_side() -> None:
    from types import SimpleNamespace

    from app.agent.offers.agent_construction_compiler import AgentConstructionCompiler
    from app.agent.offers.offer_context import OfferContext
    from app.window_model.construction_mapper import ConstructionMapper
    from app.window_model.semantic_executor import SemanticExecutionBridge
    from app.window_model.topology import WindowSide

    context = OfferContext(
        raw_request="Okno 2000x1500 DKR + FIX",
        width=2000,
        height=1500,
        product_type="window",
        openings=(
            "RIGHT_TILT_TURN",
            "FIX",
        ),
    )

    project = AgentConstructionCompiler().compile(context)
    assert project is not None

    model, topology = ConstructionMapper().map_project(project)

    sash = next(
        element
        for element in model.elements.values()
        if element.id == "sash_left"
    )

    assert sash.properties["opening"] == "tilt_turn"
    assert sash.properties["direction"] == "RIGHT"

    sash_node = topology.node(sash.id)
    assert sash_node is not None
    assert sash_node.side == WindowSide.LEFT

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

    observed = model.__class__(
        properties=dict(model.properties)
    )
    observed.add_element(
        "frame",
        model.elements["frame"].type,
    )
    observed.add_element(
        "cell_left",
        model.elements["cell_left"].type,
        parent_id="frame",
        role="CELL",
    )
    observed.add_element(
        "cell_right",
        model.elements["cell_right"].type,
        parent_id="frame",
        role="CELL",
    )

    result = SemanticExecutionBridge(executor).execute_next(
        desired=model,
        topology=topology,
        observed=observed,
    )

    assert result.executed == ("sash_left",)
    assert executor.context.gui_state.panel_side == "left"

    assert len(executor.actions) == 1
    action = executor.actions[0]

    assert action.semantic_id == "sash_left"
    assert action.semantic_side == "LEFT"
    assert action.properties["opening"] == "tilt_turn"
    assert action.properties["direction"] == "RIGHT"


if __name__ == "__main__":
    unittest.main()
