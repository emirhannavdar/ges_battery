import logging
import os
import pathlib

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from api.config.config import settings
from database.database import SessionLocal
from tasks.celery_app import celery_app
from api.services.epias import OOP_Epias
from database.epias_ptf_db import save_epias_pt_data
from celery.schedules import crontab


logger = logging.getLogger(__name__)

BASE_DIR = pathlib.Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / '.env')

@celery_app.task(
    bind=True,
    name="tasks.epias_tasks.collect_epias",
    max_retries=3,
    default_retry_delay=60
)
def collect_epias(self):
    today = datetime.now(ZoneInfo("Europe/Istanbul")).date()
    try:

        logger.info('Otomatik epiaş ptf verileri toplanmaya başadı.')

        epias_client = OOP_Epias(base_url=settings._EPIAS_BASE_URI)
        epias_client.post_TGT_token(
            username=os.getenv("_EPIAS_USERNAME"),
            password=os.getenv("_EPIAS_PASSWORD"),
        )

        epias_data = epias_client.post_PTF(
            startDate=f"{today.isoformat()}T00:00:00+03:00",
            endDate=f"{(today + timedelta(days=1)).isoformat()}T00:00:00+03:00"
        )

        with SessionLocal() as db:
            try:
                save_epias_pt_data(
                    db=db,
                    epias_data=epias_data
                )
            except Exception:
                db.rollback()
                raise

        logger.info("Epias PTF verileri veritabanına kaydedildi.")

        return {
            "success": True,
            "data": len(epias_data["items"])
        }

    except Exception as exc:
        logger.exception("Otomatik PTF verisi toplama başarısız.")

        raise self.retry(exc=exc)