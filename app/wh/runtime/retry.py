import time


class Retry:

    @staticmethod
    def run(

        callback,

        attempts=3,

        delay=0.3
    ):

        last_error = None

        for attempt in range(

            1,
            attempts + 1
        ):

            try:

                print(
                    f"[RETRY] "
                    f"attempt "
                    f"{attempt}/"
                    f"{attempts}"
                )

                return callback()

            except Exception as e:

                last_error = e

                print(
                    f"[RETRY] failed: "
                    f"{e}"
                )

                time.sleep(delay)

        raise RuntimeError(

            f"Retry failed after "
            f"{attempts} attempts. "

            f"Last error: "
            f"{last_error}"
        )