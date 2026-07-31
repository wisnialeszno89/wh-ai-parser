class RuntimeEventBus:

    def __init__(self):

        self.listeners = []

    def subscribe(
        self,
        listener,
    ):

        self.listeners.append(listener)

    def emit(
        self,
        event,
    ):

        for listener in self.listeners:

            listener(event)