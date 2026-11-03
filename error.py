class DomainError(Exception):
    def __init__(self, message: str, error_code: int = 400):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

class ExternalServiceError(DomainError):
    def __init__(self, message: str, error_code: int = 500):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

class AuthenticationError(DomainError):
    def __init__(self, message: str, error_code: int = 401):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)