import logging
from api.services.visual_crossing import OOP_VisualCrossing
from database.weather_db import save_weather_data
from tasks.celery_app import celery_app
from api.config.config import settings
from database.database import SessionLocal

logger = logging.getLogger(__name__)

LATITUDE = settings._ENLEM
LONGITUDE = settings._BOYLAM

LOCATION_ID = 1

@celery_app.task(
    bind=True,
    name="tasks.weather_tasks.collect_weather",
    max_retries=3,
    default_retry_delay=60
)
def collect_weather(self):
    db = None

    try:
        logger.info(
            "Otomatik hava durumu toplama başladı: lat=%s, lon=%s",
            LATITUDE,
            LONGITUDE,
        )

        weather_client = OOP_VisualCrossing()

        weather_data = weather_client.get_havadurumu(
            enlem=LATITUDE,
            boylam=LONGITUDE
        )

        with SessionLocal() as db:
            try:
                save_weather_data(
                    db=db,
                    location_id=LOCATION_ID,
                    weather_data=weather_data
                )
            except Exception:
                db.rollback()
                raise

        logger.info(
            "Hava durumu verileri PostgreSQL'e kaydedildi."
        )

        return {
            "success": True,
            "location_id": LOCATION_ID
        }

    except Exception as exc:
        logger.exception(
            "Otomatik hava durumu toplama başarısız."
        )

        raise self.retry(exc=exc)




