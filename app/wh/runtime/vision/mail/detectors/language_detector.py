class LanguageDetector:

    GERMAN = (

        "angebot",

        "fenster",

        "haustür",

        "bitte",

        "anfrage",

        "guten tag",

        "preis",

        "farbe"

    )

    ENGLISH = (

        "quotation",

        "window",

        "offer",

        "price",

        "hello",

        "colour",

        "please"

    )

    POLISH = (

        "okno",

        "okna",

        "oferta",

        "kolor",

        "proszę",

        "wycena"

    )

    def detect(

        self,

        text

    ):

        text = text.lower()

        if any(

            word in text

            for word in self.GERMAN

        ):

            return "de"

        if any(

            word in text

            for word in self.ENGLISH

        ):

            return "en"

        if any(

            word in text

            for word in self.POLISH

        ):

            return "pl"

        return "unknown"