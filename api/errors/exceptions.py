from api.errors.error_codes import ErrorCode

class AppError(Exception):
    def __init__(
            self,
            message: str,
            error_code: int,
            status_code: int
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code

# Tarih yanlıs girilmiş, veri bulunamadıysa kullan
class DomainError(AppError):
    def __init__( self,message: str):
        super().__init__(
            message,
            ErrorCode.DOMAIN_ERROR,
            400
        )

# Token kimlik doğrulama hataları
class AuthenticationError(AppError):
    def __init__( self,message: str):
        super().__init__(
            message,
            ErrorCode.AUTHENTICATION_ERROR,
            401
        )

# EPİAS apisine bağlanılamaması veya geçersiz bilgi alınması
class ExternalServiceError(AppError):
    def __init__( self,message: str, error_code: int = 102):
        super().__init__(
            message,
            ErrorCode.EXTERNAL_SERVICE_ERROR,
            502
        )

#weather_data hatası denemek için yaptım kullanılıyor

class WeatherDataError(AppError):
    def __init__( self,message: str):
        super().__init__(
            message,
            ErrorCode.WEATHER_DATA_ERROR,
            502
        )