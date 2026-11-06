import requests
import logging

from api.errors.exceptions import ExternalServiceError

logger = logging.getLogger(__name__)  # her doya özelinde logger olusturma

def handle_request_error(error: requests.exceptions.RequestException,service_name: str):
    if isinstance(error, requests.exceptions.Timeout):
        message = f"{service_name} isteği zaman aşımına uğradı."

    elif isinstance(error, requests.exceptions.HTTPError):
        status_code = error.response.status_code if error.response is not None else None

        if status_code == 401:
            message = f"{service_name} kimlik doğrulama hatası."
        elif status_code == 403:
            message = f"{service_name} erişim izni hatası."
        elif status_code == 404:
            message = f"{service_name} endpoint bulunamadı."
        elif status_code == 429:
            message = f"{service_name} istek limitine ulaşıldı."
        elif status_code is not None and status_code >= 500:
            message = f"{service_name} sunucu hatası."
        else:
            message = f"{service_name} HTTP servis hatası."

    else:
        message = f"{service_name} bağlantı hatası."


    logger.error(   # hata kayıtları
        "Servis: %s | Hata: %s | Detay: %s",
        service_name,
        message,
        str(error),
        exc_info=True,      # hatasının traceback bilgisi
    )

    raise ExternalServiceError(message=message) from error