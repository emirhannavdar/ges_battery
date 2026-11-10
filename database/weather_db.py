from sqlalchemy import text

def save_weather_data(db, location_id: int, weather_data: dict):

    timezone_name = weather_data["timezone"]

    from datetime import datetime
    from zoneinfo import ZoneInfo

    tz = ZoneInfo(timezone_name)

    for day in weather_data["days"]:
        for hour in day["hours"]:

            measurement_time = datetime.fromisoformat(
                f'{day["datetime"]}T{hour["datetime"]}'
            ).replace(tzinfo=tz)

            db.execute(
                text("""
                    INSERT INTO weather_data (
                        location_id,
                        measurement_time,
                        temperature,
                        solar_radiation,
                        cloud_cover,
                        datetime_hours,
                        datetime_days,
                        updated_at
                    )
                    VALUES (
                        :location_id,
                        :measurement_time,
                        :temperature,
                        :solar_radiation,
                        :cloud_cover,
                        :datetime_hours,
                        :datetime_days,
                        NOW()
                    )
                    ON CONFLICT (location_id, measurement_time)
                    DO UPDATE SET
                        temperature = EXCLUDED.temperature,
                        solar_radiation = EXCLUDED.solar_radiation,
                        cloud_cover = EXCLUDED.cloud_cover,
                        datetime_hours = EXCLUDED.datetime_hours,
                        datetime_days = EXCLUDED.datetime_days,
                        updated_at = NOW()
                """),
                {
                    "location_id": location_id,
                    "measurement_time": measurement_time,
                    "temperature": hour.get("temp"),
                    "solar_radiation": hour.get("solarradiation"),
                    "cloud_cover": hour.get("cloudcover"),
                    "datetime_hours": hour.get("datetime"),
                    "datetime_days": day.get("datetime")
                }
            )

    db.commit()