from functools import lru_cache

import requests
import logging

from fastapi.params import Depends

from api.config.config import settings
from api.errors.exceptions import (DomainError,ExternalServiceError,AuthenticationError)
from api.services.epias_params import (get_tgt_headers,get_tgt_body,get_epias_headers,get_ptf_body,get_kptf_body)
from api.errors.request_errors import handle_request_error
from api.services.epias_token_manager import EpiasTokenManager
from auth.auth import get_current_active_user, User

logger = logging.getLogger(__name__)


class OOP_Epias:

    def __init__(self, base_url: str, token_manager):
        self.base_url = base_url.rstrip("/")
        self.token_manager = token_manager
        self.session = requests.Session()

    def __setattr__(self, name: str, value):
        if name == "base_url" and hasattr(self, "base_url"):
            logger.info("EPİAŞ base url kod içinden değiştirilmeye çalışıldı.")
            raise ExternalServiceError("DIKKAT: EPİAŞ base url kod içinden değiştirilemez.")

        super().__setattr__(name, value)

    def __token_varmi(self):
        if not self.token:
            raise AuthenticationError("İşlem yapabilmek için önce TGT token alınız")
        return self.token

    def post_TGT_token(self, username: str, password: str):
        try:
            response = self.session.post(
                settings._TGT_URL,
                headers=get_tgt_headers(),
                data=get_tgt_body(username, password),
                timeout=30
            )

            response.raise_for_status()

            token = response.text.strip()

            if not token.startswith("TGT-"):
                logger.info("EPİAŞ geçerli bir TGT token döndürmedi.")
                raise ExternalServiceError("EPİAŞ geçerli bir TGT token döndürmedi")

            return token

        except requests.exceptions.RequestException as e:
            handle_request_error(e, service_name="EPİAŞ")

    def get_tgt(self):
        return self.token_manager.get_token(
            create_token=lambda: self.post_TGT_token(
                settings._EPIAS_USERNAME,
                settings._EPIAS_PASSWORD
            )
        )

    # ortak
    def __post_epias(self, endpoint: str, body: dict):
        token = self.get_tgt()
        headers = get_epias_headers(token)

        try:
            url = f"{self.base_url}{endpoint}"

            response = self.session.post(
                url,
                headers=headers,
                json=body,
                timeout=30
            )

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            handle_request_error(e, service_name="EPİAŞ")


    def post_PTF(self, startDate: str, endDate: str):

        if startDate > endDate:
            raise DomainError(
                "Başlangıç değeri bitiş değerinden büyük olamaz."
            )

        body = get_ptf_body(
            startDate=startDate,
            endDate=endDate
        )

        response_data = self.__post_epias(
            endpoint= settings._PTF_ENDPOINT,
            body=body
        )

        if "items" not in response_data:
            raise ExternalServiceError(
                "EPİAŞ beklenmeyen cevap formatı döndürdü."
            )



        items = response_data["items"]

        if not isinstance(items, list):
            raise ExternalServiceError(
                "EPİAŞ items alanı liste olmalıdır."
            )

        if not items:
            raise DomainError(
                "Belirtilen tarih aralığında veri bulunamadı."
            )

        return response_data


    def post_KPTF(self, startDate: str):
        body = get_kptf_body(startDate=startDate)

        response_data = self.__post_epias(
            endpoint= settings._KPTF_ENDPOINT,
            body=body
        )

        items = response_data.get("items", [])

        if not items:
            raise DomainError(
                "Eğer saat 14:00' geçmediyse, başlangıç olarak bugünü girmelisiniz."
            )

        return response_data


@lru_cache
def get_epias_token_manager():
    return EpiasTokenManager(redis_url=settings._REDIS_URL)

def get_epias_client(
        current_user: User = Depends(get_current_active_user)
):
    token_manager = EpiasTokenManager(
        redis_url=settings._REDIS_URL,
        user_id=current_user.id
    )

    client = OOP_Epias(
        base_url=settings._EPIAS_BASE_URI,
        token_manager=token_manager
    )

    try:
        yield client
    finally:
        client.session.close()
