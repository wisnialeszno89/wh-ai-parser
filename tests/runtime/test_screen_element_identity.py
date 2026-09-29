from app.agent.perception.screen_element import ScreenElement
from app.agent.perception.screen_element_identity import (
    ScreenElementIdentityResolver,
)


def test_tracked_object_id_is_strong_identity():
    element = ScreenElement(
        kind="icon",
        label=None,
        metadata={
            "tracked_object_id": "TO-0004",
            "source": "windowhub_vision_pipeline",
        },
    )

    identity = ScreenElementIdentityResolver().resolve(element)

    assert identity.tracked_object_id == "TO-0004"
    assert identity.has_strong_identity is True


def test_semantic_name_is_used_when_explicit():
    element = ScreenElement(
        kind="button",
        metadata={
            "provider_element_id": "uia-42",
            "semantic_name": "save",
        },
    )

    identity = ScreenElementIdentityResolver().resolve(element)

    assert identity.provider_id == "uia-42"
    assert identity.semantic_name == "save"
    assert identity.has_strong_identity is True


def test_geometry_alone_does_not_create_identity():
    element = ScreenElement(
        kind="button",
        x=10,
        y=20,
        width=80,
        height=30,
    )

    identity = ScreenElementIdentityResolver().resolve(element)

    assert identity.provider_id is None
    assert identity.semantic_name is None
    assert identity.tracked_object_id is None
    assert identity.label is None
    assert identity.has_strong_identity is False


def test_empty_metadata_is_normalized():
    element = ScreenElement(
        kind="unknown",
        label="   ",
        metadata={
            "name": " ",
            "tracked_object_id": "",
        },
    )

    identity = ScreenElementIdentityResolver().resolve(element)

    assert identity.has_strong_identity is False
