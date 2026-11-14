from .errors import PublishError
from .match import matches


class Subscription:
    """A handler registered on a bus for a topic pattern."""

    def __init__(self, bus, topic, handler, priority, order):
        self._bus = bus
        self.topic = topic
        self.handler = handler
        self.priority = priority
        self.order = order
        self.cancelled = False

    def cancel(self):
        """Remove this subscription from its bus.  Safe to call repeatedly."""
        if self.cancelled:
            return
        self.cancelled = True
        self._bus._remove(self)


class Bus:
    def __init__(self):
        self._subs = []
        self._next_order = 0

    def subscribe(self, topic, handler, priority=0):
        sub = Subscription(self, topic, handler, priority, self._next_order)
        self._next_order += 1
        self._subs.append(sub)
        return sub

    def _remove(self, sub):
        try:
            self._subs.remove(sub)
        except ValueError:
            pass

    def publish(self, topic, payload=None):
        matched = [s for s in self._subs if not s.cancelled and matches(s.topic, topic)]
        matched.sort(key=lambda s: (-s.priority, s.order))

        errors = []
        for sub in matched:
            try:
                sub.handler(topic, payload)
            except Exception as exc:
                errors.append(exc)

        if errors:
            raise PublishError(errors)
        return len(matched)
