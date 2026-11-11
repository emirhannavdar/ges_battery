from api.errors.exceptions import ExternalServiceError
from datetime import datetime, timedelta


class SimulationClock:

    def __init__(self):
        self.current_time: datetime | None = None

    def validate_step(
        self,
        date_value: str,
        time_value: str,
        dt_seconds: float
    ) -> datetime:

        if dt_seconds <= 0:
            raise ValueError("dt_seconds pozitif olmalıdır.")

        try:
            requested_time = datetime.fromisoformat(
                f"{date_value}T{time_value}"
            )
        except (ValueError, TypeError):
            raise ValueError("Geçersiz tarih veya saat.")

        if self.current_time is not None:
            if requested_time <= self.current_time:
                raise ExternalServiceError(
                    "Simülasyon zamanı geriye gidemez "
                    "veya aynı zaman tekrar işlenemez."
                )

            expected_time = self.current_time + timedelta(
                seconds=dt_seconds
            )

            if requested_time != expected_time:
                raise ValueError(
                    f"Beklenen zaman: {expected_time.isoformat()}, "
                    f"gelen zaman: {requested_time.isoformat()}"
                )

        return requested_time

    def commit_step(self, requested_time: datetime):
        self.current_time = requested_time

    def reset(self):
        self.current_time = None
