from app.wh.runtime.topology.topology_signature import (
    TopologySignature
)

from app.wh.runtime.patterns.topology_classifier import (
    TopologyClassifier
)


def test_topology_classifier():

    signature = TopologySignature(

        rows=2,

        columns=2,

        balanced=True,

        single_row=False,

        single_column=False

    )

    classifier = (

        TopologyClassifier()

    )

    labels = (

        classifier.classify(

            signature

        )

    )

    assert (

        "balanced_grid"

        in labels

    )