from app.wh.runtime.vision.project_knowledge import (
    ProjectKnowledge
)


class ProjectKnowledgeEngine:

    def analyze(

        self,

        projects

    ):

        if not projects:

            return (

                ProjectKnowledge()

            )

        return (

            ProjectKnowledge(

                most_common_profile="Softline82",

                most_common_color="winchester",

                most_common_security="RC2"

            )

        )