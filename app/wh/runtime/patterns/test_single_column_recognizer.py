from app.wh.runtime.topology.topology_signature import (
    TopologySignature
)

from app.wh.runtime.patterns.single_column_recognizer import (
    SingleColumnRecognizer
)


def test_single_column_recognizer():

    signature = TopologySignature(

        rows=3,

        columns=1,

        balanced=True,

        single_row=False,

        single_column=True

    )

    recognizer = (

        SingleColumnRecognizer()

    )

    assert (

        recognizer.matches(

            signature

        )

        is True

    )