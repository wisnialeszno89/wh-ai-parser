class AdaptiveLogger:

    def log(

        self,

        message,

        context

    ):

        if not (

            context.enable_logging

        ):

            return

        print(

            message

        )