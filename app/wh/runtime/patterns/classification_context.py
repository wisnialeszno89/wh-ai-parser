class ClassificationContext:

    def __init__(

        self,

        labels

    ):

        self.labels = labels

    def has(

        self,

        label

    ):

        return (

            label

            in

            self.labels

        )

    def has_any(

        self,

        *labels

    ):

        return any(

            label in self.labels

            for label in labels

        )

    def has_all(

        self,

        *labels

    ):

        return all(

            label in self.labels

            for label in labels

        )