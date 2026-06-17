from app.wh.runtime.vision.template_registry import (
    TemplateRegistry
)

from app.wh.runtime.vision.multiple_templates_matcher import (
    MultipleTemplatesMatcher
)


class VisionBrain:

    def __init__(

        self

    ):

        self.registry = (

            TemplateRegistry()

        )

        self.matcher = (

            MultipleTemplatesMatcher()

        )

    def find(

        self,

        screen,

        action

    ):

        templates = (

            self.registry.get_templates(

                action

            )

        )

        return (

            self.matcher.find_best(

                screen,

                templates

            )

        )