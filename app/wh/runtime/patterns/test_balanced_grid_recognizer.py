from app.wh.runtime.topology.topology_signature import (
    TopologySignature
)

from app.wh.runtime.patterns.balanced_grid_recognizer import (
    BalancedGridRecognizer
)


def test_balanced_grid_recognizer():

    signature = TopologySignature(

        rows=2,

        columns=2,

        balanced=True,

        single_row=False,

        single_column=False

    )

    recognizer = (

        BalancedGridRecognizer()

    )

    assert (

        recognizer.matches(

            signature

        )

        is True

    )