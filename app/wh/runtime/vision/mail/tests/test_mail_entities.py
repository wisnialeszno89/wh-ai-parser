from app.wh.runtime.vision.mail.mail_entities import (
    MailEntities
)

from app.wh.runtime.vision.mail.mail_entity import (
    MailEntity
)


def test_mail_entities():

    entities = (

        MailEntities()

    )

    entities.add(

        MailEntity(

            entity_type="COLOR",

            value="Anthracite"

        )

    )

    entities.add(

        MailEntity(

            entity_type="SECURITY",

            value="RC2"

        )

    )

    colors = (

        entities.find(

            "COLOR"

        )

    )

    assert len(colors) == 1

    assert colors[0].value == "Anthracite"