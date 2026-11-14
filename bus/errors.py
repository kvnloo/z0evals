"""Exceptions raised by :mod:`bus`."""


class PublishError(Exception):
    """Raised after a publish whose handlers raised one or more exceptions.

    ``errors`` holds the raised exceptions in the order the handlers ran.
    """

    def __init__(self, errors):
        self.errors = list(errors)
        super().__init__(
            "%d handler(s) failed during publish" % len(self.errors)
        )