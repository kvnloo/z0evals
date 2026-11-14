class PublishError(Exception):
    def __init__(self, errors):
        super().__init__(f"{len(errors)} handler(s) failed")
        self.errors = list(errors)
