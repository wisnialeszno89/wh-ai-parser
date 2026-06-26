class FailureAnalyzer:

    def analyze(

        self,

        failure_history

    ):

        summary = {}

        for record in (

            failure_history.records

        ):

            if (

                record.reason

                not in summary

            ):

                summary[

                    record.reason

                ] = 0

            summary[

                record.reason

            ] += 1

        return summary