from dataclasses import dataclass, asdict
from math import isfinite


@dataclass
class EKKReading:
    measured_active_power_kw: float
    measured_reactive_power_kvar: float
    target_reactive_power_kvar: float
    reactive_error_kvar: float
    reactive_command_kvar: float
    active_power_limit_kw: float
    active_power_limit_exceeded: bool
    active_power_command_kw: float

    def to_dict(self):
        return asdict(self)


class EKK:

    def __init__(
        self,
        active_power_limit_kw: float = 800.0,
        target_reactive_power_kvar: float = 0.0
    ):
        self.active_power_limit_kw = active_power_limit_kw
        self.target_reactive_power_kvar = target_reactive_power_kvar

    def control(
        self,
        measured_active_power_kw: float,
        measured_reactive_power_kvar: float,
        current_inverter_reactive_kvar: float,
        available_active_power_kw: float,
        transformer_efficiency: float= 0.99
    ) -> EKKReading:

        values = (
            measured_active_power_kw,
            measured_reactive_power_kvar,
            current_inverter_reactive_kvar,
            self.active_power_limit_kw,
            self.target_reactive_power_kvar
        )

        if not all(isfinite(v) for v in values):
            raise ValueError("Kontrol değerleri sonlu olmalıdır.")

        if self.active_power_limit_kw < 0:
            raise ValueError("Aktif güç limiti negatif olamaz.")

        # Hedef ile ölçülen reaktif güç arasındaki fark
        reactive_error = (
            self.target_reactive_power_kvar
            - measured_reactive_power_kvar
        )

        # Bir sonraki adımda invertöre gönderilecek Q komutu
        reactive_command = (
            current_inverter_reactive_kvar
            + reactive_error
        )

        # Aktif güç limit kontrolü
        limit_exceeded = (
            measured_active_power_kw
            > self.active_power_limit_kw
        )

        if available_active_power_kw < 0:
            raise ValueError("Kullanılabilir aktif güç negatif olamaz.")

        if not 0 < transformer_efficiency <= 1:
            raise ValueError("Trafo verimi 0 ile 1 arasında olmalıdır.")

        # Şebeke tarafındaki limitin invertör AC tarafındaki karşılığı
        max_inverter_power_kw = (
                self.active_power_limit_kw / transformer_efficiency
        )

        # Kullanılabilir üretim daha düşükse gereksiz sınırlama yapma
        active_command = max_inverter_power_kw


        return EKKReading(
            measured_active_power_kw=round(measured_active_power_kw, 3),
            measured_reactive_power_kvar=round(measured_reactive_power_kvar, 3),
            target_reactive_power_kvar=self.target_reactive_power_kvar,
            reactive_error_kvar=round(reactive_error, 3),
            reactive_command_kvar=round(reactive_command, 3),
            active_power_limit_kw=self.active_power_limit_kw,
            active_power_limit_exceeded=limit_exceeded,
            active_power_command_kw = round(active_command, 3)
        )