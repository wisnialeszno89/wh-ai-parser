from collections import Counter


class MatchStatistics:

    def summarize(

        self,

        reports

    ):

        winners = [

            report.winner

            for _, report

            in reports

        ]

        counter = Counter(

            winners

        )

        print()

        print(

            "===== MATCH STATISTICS ====="

        )

        for name, count in counter.items():

            print(

                f"{name}: {count}"

            )

        print()

        return counter