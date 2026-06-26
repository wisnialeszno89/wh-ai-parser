class ProjectExecutionHistory:

    def __init__(

        self

    ):

        self.projects = []

    def remember(

        self,

        outcome

    ):

        self.projects.append(

            outcome

        )

    def count(

        self

    ):

        return len(

            self.projects

        )

    def last(

        self

    ):

        if not self.projects:

            return None

        return (

            self.projects[-1]

        )