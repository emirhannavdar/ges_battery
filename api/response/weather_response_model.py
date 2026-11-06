from pydantic import BaseModel, ConfigDict, Field
from datetime import date, time


class _WeatherHour(BaseModel):
    model_config = ConfigDict(extra="allow")

    datetime: time
    temp: float
    cloudcover: float
    solarradiation: float
    solarenergy: float


class _WeatherDay(BaseModel):
    model_config = ConfigDict(extra="allow")

    datetime: date
    temp: float
    cloudcover: float
    solarradiation: float
    solarenergy: float

    hours: list[_WeatherHour]


class WeatherData(BaseModel):
    model_config = ConfigDict(extra="allow")

    address: str
    timezone: str

    days: list[_WeatherDay]