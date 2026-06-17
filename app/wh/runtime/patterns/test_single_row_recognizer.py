from app.wh.runtime.topology.topology_signature import (
    TopologySignature
)

from app.wh.runtime.patterns.single_row_recognizer import (
    SingleRowRecognizer
)


def test_single_row_recognizer():

    signature = TopologySignature(

        rows=1,

        columns=2,

        balanced=True,

        single_row=True,

        single_column=False

    )

    recognizer = (

        SingleRowRecognizer()

    )

    assert (

        recognizer.matches(

            signature

        )

        is True

    )