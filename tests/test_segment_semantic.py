from app.knowledge.semantics.segment_semantic import (
    SegmentSemantic
)


def test_segment_semantic():

    semantic = SegmentSemantic(

        opening="fixed",

        operation="create_fix",

        role="fix"
    )

    assert (

        semantic.operation

        ==

        "create_fix"
    )

    assert (

        semantic.role

        ==

        "fix"
    )