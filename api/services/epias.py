import requests
import logging

from api.config.config import EPIAS_BASE_URI

from api.errors.exceptions import (
    DomainError,
    ExternalServiceError,
    AuthenticationError
)

from api.services.epias_params import (
    TGT_URL,
    PTF_ENDPOINT,
    KPTF_ENDPOINT,
    get_tgt_headers,
    get_tgt_body,
    get_epias_headers,
    get_ptf_body,
    get_kptf_body
)

from api.errors.request_errors import handle_request_error


logger = logging.getLogger(__name__)


class OOP_Epias:

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.token = None
        self.session = requests.Session()

    def token_varmi(self):
        if not self.token:
            raise AuthenticationError("İşlem yapabilmek için önce TGT token alınız")
        return self.token


    def post_TGT_token(self, username: str, password: str):
        try:
            response = self.session.post(
                TGT_URL,
                headers=get_tgt_headers(),
                data=get_tgt_body(username, password),
                timeout=30
            )

            response.raise_for_status()

            token = response.text.strip()

            if not token.startswith("TGT-"):
                raise ExternalServiceError("EPİAŞ geçerli bir TGT token döndürmedi")

            self.token = token
            return self.token

        except requests.exceptions.RequestException as e:
            handle_request_error(e, service_name="EPİAŞ")

    # ortak
    def __post_epias(self, endpoint: str, body: dict):
        self.token_varmi()
        try:
            url = f"{self.base_url}{endpoint}"

            response = self.session.post(
                url,
                headers=get_epias_headers(self.token),
                json=body,
                timeout=30
            )

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            self.__handle_request_error(e)

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
            endpoint=PTF_ENDPOINT,
            body=body
        )

        items = response_data.get("items", [])

        if not items:
            raise DomainError(
                "Başlangıç günü olarak bugün'ü girmelisiniz. "
                "Eğer saat 14:00'ı geçmişse bitiş olarak bir sonraki günü girebilirsiniz."
            )

        return response_data


    def post_KPTF(self, startDate: str):
        body = get_kptf_body(startDate=startDate)

        response_data = self.__post_epias(
            endpoint=KPTF_ENDPOINT,
            body=body
        )

        items = response_data.get("items", [])

        if not items:
            raise DomainError(
                "Eğer saat 14:00' geçmediyse, başlangıç olarak bugünü girmelisiniz."
            )

        return response_data


epias_client = OOP_Epias(EPIAS_BASE_URI)


def get_epias_client():
    return epias_client
