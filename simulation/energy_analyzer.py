from dataclasses import dataclass, asdict
from math import sqrt, isfinite


@dataclass
class AnalyzerReading:
    active_power_kw: float
    reactive_power_kvar: float
    apparent_power_kva: float
    power_factor: float
    voltage_v: float
    current_a: float
    frequency_hz: float
    energy_kwh: float

    def to_dict(self):
        return asdict(self)


class EnergyAnalyzer:

    def __init__(self):
        self.energy_kwh = 0.0
        self.last_reading = None

    def measure(
        self,
        active_power_kw: float,
        reactive_power_kvar: float,
        voltage_v: float,
        frequency_hz: float,
        dt_seconds: float
    ):

        values = (
            active_power_kw,
            reactive_power_kvar,
            voltage_v,
            frequency_hz,
            dt_seconds
        )

        if not all(isfinite(value) for value in values):
            raise ValueError("Ölçüm değerleri sonlu olmalıdır.")

        if voltage_v <= 0 or frequency_hz <= 0 or dt_seconds <= 0:
            raise ValueError("Gerilim, frekans ve süre pozitif olmalıdır.")

        # Görünür güç
        apparent_power_kva = sqrt(
            active_power_kw ** 2 +
            reactive_power_kvar ** 2
        )

        # Üç fazlı sistemde hat akımı
        current_a = (
            apparent_power_kva * 1000
            / (sqrt(3) * voltage_v)
        )

        # Güç faktörü
        power_factor = (
            abs(active_power_kw) / apparent_power_kva
            if apparent_power_kva > 0 else 1.0
        )

        # Üretilen enerjiyi biriktir
        self.energy_kwh += active_power_kw * dt_seconds / 3600

        self.last_reading = AnalyzerReading(
            active_power_kw=round(active_power_kw, 3),
            reactive_power_kvar=round(reactive_power_kvar, 3),
            apparent_power_kva=round(apparent_power_kva, 3),
            power_factor=round(power_factor, 4),
            voltage_v=voltage_v,
            current_a=round(current_a, 3),
            frequency_hz=frequency_hz,
            energy_kwh=round(self.energy_kwh, 4)
        )

        return self.last_reading

    def get_data(self):
        if self.last_reading is None:
            return None

        return self.last_reading.to_dict()