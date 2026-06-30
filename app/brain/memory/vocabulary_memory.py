class VocabularyMemory:

    def __init__(self):

        self.aliases = {}

    def add(
        self,
        alias,
        canonical
    ):

        self.aliases[
            alias.lower()
        ] = canonical

    def resolve(
        self,
        alias
    ):

        return self.aliases.get(
            alias.lower()
        )