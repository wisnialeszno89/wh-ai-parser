"""Regression: WH knowledge comes from observed control maps and preserves ZLC safety."""
from app.agent.learning.windowhub_environment_knowledge import windowhub_environment_knowledge
from app.agent.learning.windowhub_training_context import windowhub_skill_knowledge


def test_order_is_read_only_and_offer_is_distinct():
    data = windowhub_environment_knowledge("order_document")
    assert data["document_policy"]["ZLC/"] == "read_only_no_mutations"
    assert "READ ONLY" in " ".join(data["rules"])
    assert data["permissions"] == "knowledge_only_never_grants_execution"


def test_dimensions_have_observed_overall_fields():
    data = windowhub_environment_knowledge("dimensions")
    names = {x["field"] for x in data["fields"]}
    assert {"width_1", "height_1"} <= names
    assert all(x["stage"] == "dimensions" for x in data["fields"])


def test_v2_training_receives_grounded_environment():
    knowledge = windowhub_skill_knowledge()
    assert "order_document" in knowledge["known_stages"]
    assert knowledge["grounded_environment"]["document_policy"]["ZLC/"] == "read_only_no_mutations"
    assert "offer_document" in knowledge["grounded_environment"]["verified_workflow"]
