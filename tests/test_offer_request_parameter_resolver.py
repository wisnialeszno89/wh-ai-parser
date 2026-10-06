from app.agent.agent_request import AgentRequest
from app.agent.learning.learned_workflow import LearnedWorkflow
from app.agent.offers.offer_request_parameter_resolver import (
    OfferRequestParameterResolver,
)


def test_offer_parameter_resolver_maps_normalized_offer_context_to_semantic_labels():
    resolver = OfferRequestParameterResolver()

    request = AgentRequest(
        message=(
            "Potrzebuję 3 szt. okien 1200x1500 "
            "antracyt z zewnątrz trzyszybowe"
        )
    )

    values = resolver.resolve(
        request,
        LearnedWorkflow(
            workflow_id="wf",
            name="x",
            application="WindowHub",
            trigger="x",
        ),
    )

    assert values["width"] == 1200
    assert values["height"] == 1500
    assert values["quantity"] == 3
    assert values["color_outside"] == "anthracite"
    assert values["kolor_zewnetrzny"] == "anthracite"
    assert values["glazing"] == "triple"


def test_offer_parameter_resolver_exposes_width_alias_for_polish_label():
    resolver = OfferRequestParameterResolver()

    values = resolver.resolve(
        AgentRequest(message="Okno 1350x1500"),
        LearnedWorkflow(
            workflow_id="wf",
            name="x",
            application="WindowHub",
            trigger="x",
        ),
    )

    assert values["szerokosc"] == 1350
    assert resolver.parameter_for_label("Szerokość") == "width"


def test_offer_parameter_resolver_parses_quantity_from_plain_product_count():
    resolver = OfferRequestParameterResolver()

    values = resolver.resolve(
        AgentRequest(
            message="dodaj nowe okno 6 okien 1200x1500"
        ),
        LearnedWorkflow(
            workflow_id="wf",
            name="x",
            application="WindowHub",
            trigger="dodaj nowe okno",
        ),
    )

    assert values["quantity"] == 6
