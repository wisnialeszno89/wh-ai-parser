class ExecutionHistory:

    def __init__(self):

        self.records = []

    def add(
        self,
        record,
    ):

        self.records.append(record)

    def last(self):

        if not self.records:

            return None

        return self.records[-1]