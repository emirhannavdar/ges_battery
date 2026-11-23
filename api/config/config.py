import os

from pathlib import Path
from typing import Final
from dotenv import load_dotenv
from dataclasses import dataclass

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / '.env')

@dataclass(frozen=True)
class Config:
    _VISUAL_CROSSING_API_KEY: Final[str] = os.environ["_VISUAL_CROSSING_API_KEY"]
    _VISUAL_CROSSING_BASE_URI: Final[str] = os.environ["_VISUAL_CROSSING_BASE_URI"]

    _EPIAS_BASE_URI: Final[str] = os.environ["_EPIAS_BASE_URI"]

    # REDİS AYARLARI
    _REDIS_URL: Final[str] = os.getenv("_REDIS_URL")
    _MAX_ATTEMPTS: Final[int] = 5
    _BLOCK_DURATION: Final[int] = 300


    _TGT_URL: Final[str] = os.getenv("_TGT_URL")

    _PTF_ENDPOINT = os.getenv("_PTF_ENDPOINT")
    _KPTF_ENDPOINT = os.getenv("_KPTF_ENDPOINT")

    _EPIAS_USERNAME: Final[str] = os.getenv("_EPIAS_USERNAME")
    _EPIAS_PASSWORD: Final[str] = os.getenv("_EPIAS_PASSWORD")

    _HASH_PASSWORD: Final[str] = os.getenv("_HASH_PASSWORD")


    _ENLEM: Final[float] = 39.97716018045437
    _BOYLAM: Final[float] = 32.68773218167581

settings = Config()

_XSECRET_KEYS = {
    "key_2026_02": os.getenv("_XSECRET_KEY_2"),
    "key_2026_01": os.getenv("_XSECRET_KEY_1")
}

_ACTIVE_KEY_ID = "key_2026_02"