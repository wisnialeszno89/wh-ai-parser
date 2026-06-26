import re

from app.wh.runtime.vision.mail_metadata import (
    MailMetadata
)


class MailParser:

    EMAIL_REGEX = (

        r"[A-Za-z0-9._%+-]+"

        r"@"

        r"[A-Za-z0-9.-]+"

        r"\.[A-Za-z]{2,}"

    )

    def parse(

        self,

        subject,

        body

    ):

        text = (

            f"{subject}\n{body}"

        )

        return (

            MailMetadata(

                sender_email=(

                    self.extract_email(

                        text

                    )

                ),

                language=(

                    self.detect_language(

                        text

                    )

                ),

                priority=(

                    self.detect_priority(

                        text

                    )

                ),

                request_type=(

                    self.detect_request_type(

                        text

                    )

                )

            )

        )

    def extract_email(

        self,

        text

    ):

        match = re.search(

            self.EMAIL_REGEX,

            text

        )

        if match:

            return match.group(

                0

            )

        return ""

    def detect_language(

        self,

        text

    ):

        lower = text.lower()

        german = [

            "angebot",

            "fenster",

            "bitte",

            "anfrage",

            "guten tag",

            "haustür"

        ]

        english = [

            "quotation",

            "window",

            "please",

            "hello",

            "offer"

        ]

        if any(

            word in lower

            for word in german

        ):

            return "de"

        if any(

            word in lower

            for word in english

        ):

            return "en"

        return "unknown"

    def detect_priority(

        self,

        text

    ):

        lower = text.lower()

        urgent = [

            "urgent",

            "asap",

            "dringend",

            "sofort"

        ]

        if any(

            word in lower

            for word in urgent

        ):

            return "high"

        return "normal"

    def detect_request_type(

        self,

        text

    ):

        lower = text.lower()

        quotation = [

            "quotation",

            "angebot",

            "offer",

            "price",

            "preis"

        ]

        if any(

            word in lower

            for word in quotation

        ):

            return "quotation"

        return "unknown"