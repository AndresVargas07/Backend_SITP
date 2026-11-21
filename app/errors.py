"""Error de la API con código HTTP; Flask lo convierte en JSON."""


class ApiError(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status, self.message = status, message
