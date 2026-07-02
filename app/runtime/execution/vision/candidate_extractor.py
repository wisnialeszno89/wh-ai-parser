from app.vision.extract_icon_candidates_v2 import (
    extract_icon_candidates_v2,
)


class CandidateExtractor:

    def extract(
        self,
        screenshot,
    ):

        return extract_icon_candidates_v2(
            screenshot
        )