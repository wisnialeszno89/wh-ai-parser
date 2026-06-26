from app.wh.runtime.vision.project_knowledge import (
    ProjectKnowledge
)


def test_project_knowledge():

    knowledge = (

        ProjectKnowledge(

            most_common_profile="Softline82",

            most_common_color="winchester",

            most_common_security="RC2"

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