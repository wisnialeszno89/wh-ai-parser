from app.wh.runtime.vision.mail.detectors.language_detector import (
    LanguageDetector
)


def test_language_detector():

    detector = (

        LanguageDetector()

    )

    assert (

        detector.detect(

            "Bitte senden Sie ein Angebot."

        )

        ==

        "de"

    )

    assert (

        detector.detect(

            "Please send quotation."

        )

        ==

        "en"

    )

    assert (

        detector.detect(

            "Proszę o ofertę."

        )

        ==

        "pl"

    )