class CaseMemory:

    def __init__(self):

        self.cases = []

    def remember(
        self,
        case
    ):

        self.cases.append(
            case
        )

    def all(self):

        return self.cases