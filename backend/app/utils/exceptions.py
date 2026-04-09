"""自定义异常"""
class AppException(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)

class FileValidationError(AppException):
    pass

class AIServiceError(AppException):
    def __init__(self, message: str):
        super().__init__(message, status_code=503)
