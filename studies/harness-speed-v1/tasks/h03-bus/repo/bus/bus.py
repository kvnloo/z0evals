class Bus:
    def __init__(self):
        self._subs = {}

    def subscribe(self, topic, handler):
        self._subs.setdefault(topic, []).append(handler)

    def publish(self, topic, payload=None):
        for h in self._subs.get(topic, []):
            h(topic, payload)
