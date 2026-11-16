"""Free-text goal does not inherit a compulsory new-offer workflow."""
from app.agent.learning.windowhub_training_context import windowhub_skill_knowledge


def test_skill_knowledge_does_not_force_new_offer_and_customer_selection():
    info = windowhub_skill_knowledge()
    assert not info["business_goal"].startswith("Create a WindowHub window offer")
    assert "specific objective" in info["business_goal"]
    assert "without opening a new offer" in info["business_goal"]
    assert any("not an assumed default workflow" in note for note in info["general_computer_skills"])
    assert any("print template" in note for note in info["general_computer_skills"])


def test_training_distinguishes_new_offer_add_position_and_existing_edit():
    info = windowhub_skill_knowledge()
    skills = " ".join(info["general_computer_skills"]).casefold()
    semantics = " ".join(info["windowhub_semantics"]).casefold()
    assert "add a position" in skills
    assert "edit an existing position" in skills
    assert "multiple open offers" in skills
    assert "start1" in semantics
    assert "verify which mdi document owns" in semantics
    assert "do not create a new position without a reason" in skills
