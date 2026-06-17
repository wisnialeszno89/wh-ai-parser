class QueryPreprocessor:

    def preprocess(

        self,

        text

    ):

        lines = [

            line.strip()

            for line in text.splitlines()

            if line.strip()

        ]

        return sorted(

            lines

        )