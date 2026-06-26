from app.wh.runtime.vision.project_knowledge_engine import (
    ProjectKnowledgeEngine
)

from app.wh.runtime.vision.project_execution_history import (
    ProjectExecutionHistory
)

from app.wh.runtime.vision.project_outcome import (
    ProjectOutcome
)


def test_project_knowledge_engine():

    history = (

        ProjectExecutionHistory()

    )

    history.remember(

        ProjectOutcome(

            project_name="offer_001",

            success=True

        )

    )

    engine = (

        ProjectKnowledgeEngine()

    )

    knowledge = (

        engine.analyze(

            history.projects

        )

    )

    assert (

        knowledge.most_common_profile

        ==

        "Softline82"

    )

    assert (

        knowledge.most_common_color

        ==

        "winchester"

    )

    assert (

        knowledge.most_common_security

        ==

        "RC2"

    )