class ReflectionMemory:

    def __init__(

        self

    ):

        self.reflections = []

    def remember(

        self,

        reflection

    ):

        self.reflections.append(

            reflection

        )

    def count(

        self

    ):

        return len(

            self.reflections

        )

    def last(

        self

    ):

        if not self.reflections:

            return None

        return (

            self.reflections[-1]

        )