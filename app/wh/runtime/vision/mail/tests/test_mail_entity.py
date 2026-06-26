from app.wh.runtime.vision.mail.mail_entity import (
    MailEntity
)


def test_mail_entity():

    entity = (

        MailEntity(

            entity_type="COLOR",

            value="Anthracite",

            confidence=0.95

        )

    )

    assert entity.entity_type == "COLOR"

    assert entity.value == "Anthracite"

    assert entity.confidence == 0.95