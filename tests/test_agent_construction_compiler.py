from app.agent.offers.agent_construction_compiler import (
    AgentConstructionCompiler
)
from app.agent.offers.offer_context import OfferContext
from app.wh.model.opening import Opening


def test_compiles_right_tilt_turn():
    context = OfferContext(
        raw_request="Potrzebuję okno 1200x1500 DKR",
        width=1200,
        height=1500,
        product_type="window",
        opening="RIGHT_TILT_TURN",
    )

    project = AgentConstructionCompiler().compile(context)

    assert project is not None
    assert project.schema.width == 1200
    assert project.schema.height == 1500
    assert project.schema.segments[0].opening == Opening.TILT_TURN
    assert len(project.schema.segments) == 1


def test_compiles_left_tilt_turn():
    context = OfferContext(
        raw_request="Potrzebuję okno 1200x1500 DKL",
        width=1200,
        height=1500,
        product_type="window",
        opening="LEFT_TILT_TURN",
    )

    project = AgentConstructionCompiler().compile(context)

    assert project is not None
    assert project.schema.segments[0].opening == Opening.TILT_TURN


def test_compiles_fix():
    context = OfferContext(
        raw_request="Potrzebuję okno 1200x1500 FIX",
        width=1200,
        height=1500,
        product_type="window",
        opening="FIX",
    )

    project = AgentConstructionCompiler().compile(context)

    assert project is not None
    assert project.schema.segments[0].opening == Opening.FIX


def test_missing_opening_returns_none():
    context = OfferContext(
        raw_request="Potrzebuję okno 1200x1500",
        width=1200,
        height=1500,
        product_type="window",
    )

    project = AgentConstructionCompiler().compile(context)

    assert project is None


def test_unknown_opening_returns_none():
    context = OfferContext(
        raw_request="Potrzebuję okno 1200x1500 XYZ",
        width=1200,
        height=1500,
        product_type="window",
        opening="UNKNOWN",
    )

    project = AgentConstructionCompiler().compile(context)

    assert project is None


def test_invalid_dimensions_return_none():
    context = OfferContext(
        raw_request="Potrzebuję okno 0x1500 DKR",
        width=0,
        height=1500,
        product_type="window",
        opening="RIGHT_TILT_TURN",
    )

    project = AgentConstructionCompiler().compile(context)

    assert project is None
