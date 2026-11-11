from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from math import sqrt, isfinite


class InverterStatus(str, Enum):
    OFF = "off"
    STANDBY = "standby"
    RUNNING = "running"
    FAULT = "fault"


@dataclass(frozen=True)
class InverterConfig:
    dc_rated_kw: float = 1000.0
    ac_rated_kw: float = 900.0
    apparent_rated_kva: float = 1000.0
    efficiency: float = 0.97
    line_voltage_v: float = 400.0
    frequency_hz: float = 50.0
    temperature_coefficient_per_c: float = -0.0035
    minimum_irradiance_w_m2: float = 20.0

    def __post_init__(self) -> None:
        for name in ("dc_rated_kw", "ac_rated_kw", "apparent_rated_kva", "line_voltage_v", "frequency_hz"):
            value = getattr(self, name)
            if not isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be a finite positive number")
        if not (0 < self.efficiency <= 1):
            raise ValueError("efficiency must be in (0, 1]")
        if self.ac_rated_kw > self.apparent_rated_kva:
            raise ValueError("ac_rated_kw cannot exceed apparent_rated_kva")
        if not isfinite(self.temperature_coefficient_per_c):
            raise ValueError("invalid temperature coefficient")
        if not isfinite(self.minimum_irradiance_w_m2) or self.minimum_irradiance_w_m2 < 0:
            raise ValueError("minimum irradiance must be nonnegative")


@dataclass(frozen=True)
class InverterReading:
    status: str
    dc_power_kw: float
    ac_power_kw: float
    reactive_power_kvar: float
    apparent_power_kva: float
    power_factor: float
    line_voltage_v: float
    line_current_a: float
    frequency_hz: float
    efficiency: float
    energy_kwh: float
    fault_reason: str | None

    def to_dict(self) -> dict:
        return asdict(self)


class Inverter:
    """Stateful, single-instance inverter model; not a detailed power electronics model."""

    def __init__(self, config: InverterConfig | None = None):
        self.config = config or InverterConfig()
        self.status = InverterStatus.OFF
        self.fault_reason: str | None = None
        self.energy_kwh = 0.0
        self.reactive_power_setpoint_kvar = 0.0
        self._last_reading = self._zero_reading()
        self.active_power_setpoint_kw = self.config.ac_rated_kw

    def _zero_reading(self) -> InverterReading:
        return InverterReading(
            status=self.status.value, dc_power_kw=0.0, ac_power_kw=0.0,
            reactive_power_kvar=0.0, apparent_power_kva=0.0,
            power_factor=1.0, line_voltage_v=self.config.line_voltage_v,
            line_current_a=0.0, frequency_hz=self.config.frequency_hz,
            efficiency=self.config.efficiency, energy_kwh=round(self.energy_kwh, 4),
            fault_reason=self.fault_reason,
        )

    def start(self) -> None:
        if self.status == InverterStatus.FAULT:
            raise RuntimeError("Clear fault before restarting")
        self.status = InverterStatus.STANDBY
        self._last_reading = self._zero_reading()

    def stop(self) -> None:
        self.status = InverterStatus.OFF
        self._last_reading = self._zero_reading()

    def set_fault(self, reason: str) -> None:
        if not reason.strip():
            raise ValueError("fault reason must not be empty")
        self.fault_reason = reason
        self.status = InverterStatus.FAULT
        self._last_reading = self._zero_reading()

    def reset_fault(self) -> None:
        self.fault_reason = None
        self.status = InverterStatus.OFF
        self._last_reading = self._zero_reading()

    def set_reactive_power(self, kvar: float) -> None:
        if not isfinite(kvar) or abs(kvar) > self.config.apparent_rated_kva:
            raise ValueError("reactive power setpoint exceeds inverter kVA rating")
        self.reactive_power_setpoint_kvar = kvar

    def set_active_power(self, kw: float) -> None:
        if not isfinite(kw) or not 0 <= kw <= self.config.ac_rated_kw:
            raise ValueError("Aktif güç setpoint'i 0 ile invertörün nominal AC gücü arasında olmalıdır.")

        self.active_power_setpoint_kw = kw

    def calculate_available_power(
            self,
            irradiance_w_m2: float,
            cell_temperature_c: float
    ) -> float:

        # 1. Giriş değerlerini doğrula
        if not isfinite(irradiance_w_m2):
            raise ValueError("irradiance_w_m2 must be finite")

        if not isfinite(cell_temperature_c):
            raise ValueError("cell_temperature_c must be finite")

        if irradiance_w_m2 < 0:
            raise ValueError("irradiance must be nonnegative")

        # 2. Kapalı veya arızalı invertör üretim yapamaz
        if self.status in (
                InverterStatus.OFF,
                InverterStatus.FAULT
        ):
            return 0.0

        # 3. Minimum ışınım kontrolü
        if irradiance_w_m2 < self.config.minimum_irradiance_w_m2:
            return 0.0

        # 4. Sıcaklık etkisi
        temperature_factor = max(
            0.0,
            1 + self.config.temperature_coefficient_per_c
            * (cell_temperature_c - 25.0)
        )

        # 5. DC üretim gücü
        dc_kw = (
                self.config.dc_rated_kw
                * irradiance_w_m2
                / 1000.0
                * temperature_factor
        )

        # 6. Reaktif güç nedeniyle oluşan aktif güç sınırı
        q_kvar = self.reactive_power_setpoint_kvar

        max_active_from_kva = sqrt(
            max(
                0.0,
                self.config.apparent_rated_kva ** 2
                - q_kvar ** 2
            )
        )

        # 7. EKK kısıtlaması olmadan üretilebilecek AC güç
        available_kw = min(
            dc_kw * self.config.efficiency,
            self.config.ac_rated_kw,
            max_active_from_kva
        )

        return max(0.0, available_kw)

    def step(self, irradiance_w_m2: float, cell_temperature_c: float, dt_seconds: float = 1.0) -> InverterReading:
        for name, value in (("irradiance_w_m2", irradiance_w_m2), ("cell_temperature_c", cell_temperature_c), ("dt_seconds", dt_seconds)):
            if not isfinite(value):
                raise ValueError(f"{name} must be finite")
        if irradiance_w_m2 < 0 or dt_seconds <= 0:
            raise ValueError("irradiance must be nonnegative and dt_seconds positive")
        if self.status in (InverterStatus.OFF, InverterStatus.FAULT):
            self._last_reading = self._zero_reading()
            return self._last_reading
        if irradiance_w_m2 < self.config.minimum_irradiance_w_m2:
            self.status = InverterStatus.STANDBY
            self._last_reading = self._zero_reading()
            return self._last_reading

        temperature_factor = max(0.0, 1 + self.config.temperature_coefficient_per_c * (cell_temperature_c - 25.0))
        dc_kw = self.config.dc_rated_kw * irradiance_w_m2 / 1000.0 * temperature_factor
        q_kvar = self.reactive_power_setpoint_kvar
        max_active_from_kva = sqrt(max(0.0, self.config.apparent_rated_kva ** 2 - q_kvar ** 2))
        ac_kw = min(
            dc_kw * self.config.efficiency,
            self.config.ac_rated_kw,
            max_active_from_kva,
            self.active_power_setpoint_kw
        )
        apparent_kva = sqrt(ac_kw ** 2 + q_kvar ** 2)
        current_a = apparent_kva * 1000.0 / (sqrt(3.0) * self.config.line_voltage_v)
        pf = ac_kw / apparent_kva if apparent_kva > 0 else 1.0
        self.energy_kwh += ac_kw * dt_seconds / 3600.0
        self.status = InverterStatus.RUNNING
        self._last_reading = InverterReading(
            status=self.status.value, dc_power_kw=round(dc_kw, 3),
            ac_power_kw=round(ac_kw, 3), reactive_power_kvar=round(q_kvar, 3),
            apparent_power_kva=round(apparent_kva, 3), power_factor=round(pf, 4),
            line_voltage_v=self.config.line_voltage_v,
            line_current_a=round(current_a, 3), frequency_hz=self.config.frequency_hz,
            efficiency=self.config.efficiency, energy_kwh=round(self.energy_kwh, 4),
            fault_reason=self.fault_reason,
        )
        return self._last_reading

    def get_data(self) -> dict:
        data = self._last_reading.to_dict()
        data["active_power_setpoint_kw"] = (
            self.active_power_setpoint_kw
        )

        return data


if __name__ == "__main__":
    inverter = Inverter()
    inverter.start()
    inverter.set_reactive_power(100)
    for hour, irradiance in enumerate((0, 200, 500, 800, 1000, 700, 300, 0)):
        reading = inverter.step(irradiance, 35, dt_seconds=3600)
        print(f"t={hour:02d}h | {reading.to_dict()}")
