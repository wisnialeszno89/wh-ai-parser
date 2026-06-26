class RetryEngine:

    def execute(

        self,

        func,

        retry_count=3

    ):

        for _ in range(

            retry_count

        ):

            if (

                func()

            ):

                return True

        return False