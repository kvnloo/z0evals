import itertools
from .errors import PublishError
from .match import matches


class Subscription:
    def __init__(self, bus, key):
        self._bus, self._key = bus, key

    def cancel(self):
        self._bus._subs.pop(self._key, None)


class Bus:
    def __init__(self):
        self._subs = {}
        self._seq = itertools.count()

    def subscribe(self, topic, handler, priority=0):
        key = next(self._seq)
        self._subs[key] = (topic, handler, priority)
        return Subscription(self, key)

    def publish(self, topic, payload=None):
        hits = [(k, h, pr) for k, (pat, h, pr) in self._subs.items() if matches(pat, topic)]
        hits.sort(key=lambda x: (-x[2], x[0]))
        errors = []
        for _k, h, _pr in hits:
            try:
                h(topic, payload)
            except Exception as e:
                errors.append(e)
        if errors:
            raise PublishError(errors)
        return len(hits)
