from app.wh.runtime.topology.topology_navigator import (
    TopologyNavigator
)


class TopologyContext:

    def __init__(

        self,

        topology

    ):

        self.topology = topology

        self.navigator = (

            TopologyNavigator()

        )

    def left(

        self,

        field

    ):

        return self.navigator.left(

            self.topology,

            field

        )

    def right(

        self,

        field

    ):

        return self.navigator.right(

            self.topology,

            field

        )

    def top(

        self,

        field

    ):

        return self.navigator.top(

            self.topology,

            field

        )

    def bottom(

        self,

        field

    ):

        return self.navigator.bottom(

            self.topology,

            field

        )