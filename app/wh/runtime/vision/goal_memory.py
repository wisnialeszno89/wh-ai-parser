class GoalMemory:

    def __init__(

        self

    ):

        self.completed = []

    def remember(

        self,

        goal

    ):

        self.completed.append(

            goal.name

        )

    def contains(

        self,

        goal_name

    ):

        return (

            goal_name

            in

            self.completed

        )