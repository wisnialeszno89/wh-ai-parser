import time


class RuntimeWaiters:

    def short(self):

        print(
            "[WAIT] short"
        )

        time.sleep(0.2)

    def medium(self):

        print(
            "[WAIT] medium"
        )

        time.sleep(0.5)

    def long(self):

        print(
            "[WAIT] long"
        )

        time.sleep(1.0)