"""Application custom exceptions module."""


class AppError(Exception):
    """Classe base para exceções da API."""

    def __init__(self, status_code: int, message: str):
        """Initialize an application exception.

        :param status_code: HTTP status code
        :type status_code: int
        :param message: Error message
        :type message: str
        """
        self.message = message
        self.status_code = status_code
        self.status = "fail" if 400 <= status_code < 500 else "error"
        self.is_operational = True
        super().__init__(self.message)
