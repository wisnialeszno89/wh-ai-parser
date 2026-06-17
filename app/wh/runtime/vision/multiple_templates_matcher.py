from app.wh.runtime.vision.match_result import (
    MatchResult
)

from app.wh.runtime.vision.template_matcher import (
    TemplateMatcher
)


class MultipleTemplatesMatcher:

    def __init__(

        self

    ):

        self.matcher = (

            TemplateMatcher()

        )

    def find_best(

        self,

        screen,

        templates

    ):

        best = MatchResult(

            found=False,

            confidence=0.0

        )

        for template in templates:

            result = (

                self.matcher.find(

                    screen,

                    template

                )

            )

            if (

                result.confidence >

                best.confidence

            ):

                best = result

        return best