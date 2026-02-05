class ExceptionBase(Exception):
    def __init__(self, detail: str):
        self.detail = detail


class ConflictException(ExceptionBase): ...
