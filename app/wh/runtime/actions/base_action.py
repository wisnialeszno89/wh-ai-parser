class BaseAction:

    def execute(

        self,
        runtime
    ):

        raise NotImplementedError()

    def serialize(self):

        raise NotImplementedError()

    def validate(

        self,
        runtime
    ):

        return True