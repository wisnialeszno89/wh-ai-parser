"""Free-text goal does not inherit a compulsory new-offer workflow."""
from app.agent.learning.windowhub_training_context import windowhub_skill_knowledge


def test_skill_knowledge_does_not_force_new_offer_and_customer_selection():
    info = windowhub_skill_knowledge()
    assert not info["business_goal"].startswith("Create a WindowHub window offer")
    assert "specific objective" in info["business_goal"]
    assert "without opening a new offer" in info["business_goal"]
    assert any("not an assumed default workflow" in note for note in info["general_computer_skills"])
    assert any("print template" in note for note in info["general_computer_skills"])
