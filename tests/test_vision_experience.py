from app.wh.vision.vision_experience import (
    VisionExperience
)


def test_vision_experience():

    experience = VisionExperience()

    result = experience.learn(

        "samples/ui",

        "templates/add_position.png"

    )

    assert len(

        result

    ) > 0