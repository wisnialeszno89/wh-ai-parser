from app.wh.runtime.topology.topology_signature import (
    TopologySignature
)

from app.wh.runtime.patterns.pattern_recognizer import (
    PatternRecognizer
)


class TopologySignatureEngine:

    def __init__(

        self

    ):

        self.recognizer = (

            PatternRecognizer()

        )

    def build(

        self,

        construction

    ):

        rows = len(

            construction.topology

        )

        columns = len(

            construction.topology[0]

        )

        return TopologySignature(

            rows=rows,

            columns=columns,

            balanced=self.recognizer.is_balanced(

                construction

            ),

            single_row=self.recognizer.is_single_row(

                construction

            ),

            single_column=self.recognizer.is_single_column(

                construction

            )

        )