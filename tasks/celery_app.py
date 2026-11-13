import os
from datetime import timedelta
from pathlib import Path

from celery import Celery
from celery.schedules import crontab
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

REDIS_URL = os.getenv("_REDIS_URL")

celery_app = Celery(
    "ges_battery",
    broker=REDIS_URL,
    include=["tasks.weather_tasks", "tasks.epias_tasks"]
)

celery_app.conf.update(
    broker_url=REDIS_URL,
    timezone="Europe/Istanbul",
    enable_utc=True,
    task_serializer="json",
    accept_content=["json"],
    task_ignore_result=True,
    broker_connection_retry_on_startup=True,
    beat_schedule={
        "collect-ankara-weather-hourly": {
            "task": "tasks.weather_tasks.collect_weather",
            "schedule": timedelta(weeks=2)
        },
        "collect-epias-daily": {
            "task": "tasks.epias_tasks.collect_epias",
            "schedule": crontab(hour=14, minute=10),
        }
    },
)
