from math import sqrt
from simulation.energy_analyzer import EnergyAnalyzer
from simulation.transformer import Transformer
from simulation.simulation_clock import SimulationClock
from simulation.inverter import Inverter, InverterConfig
from simulation.ekk import EKK


class SimulationManager:

    def __init__(
            self,
            inverter_count: int = 3,
            inverter_ac_rated_kw: float = 900,
            inverter_dc_rated_kw: float = 1000,
            ekk_active_power_limit_kw: float = 800
    ):
        if inverter_count < 1:
            raise ValueError("En az bir invertör olmalı.")

        if inverter_ac_rated_kw <= 0:
            raise ValueError("İnvertör AC gücü pozitif olmalı.")

        if inverter_dc_rated_kw <= 0:
            raise ValueError("İnvertör DC gücü pozitif olmalı.")

        if ekk_active_power_limit_kw < 0:
            raise ValueError("EKK aktif güç limiti negatif olamaz.")

        # Konfigürasyonu sakla
        self.config = {
            "inverter_count": inverter_count,
            "inverter_ac_rated_kw": inverter_ac_rated_kw,
            "inverter_dc_rated_kw": inverter_dc_rated_kw,
            "ekk_active_power_limit_kw": ekk_active_power_limit_kw
        }

        # Her invertör için ortak teknik konfigürasyon
        inverter_config = InverterConfig(
            ac_rated_kw=inverter_ac_rated_kw,
            dc_rated_kw=inverter_dc_rated_kw
        )

        # İnvertörleri oluştur
        self.inverters = {
            f"inverter_{i}": Inverter(config=inverter_config)
            for i in range(1, inverter_count + 1)
        }

        self.analyzer = EnergyAnalyzer()

        self.transformer = Transformer()

        self.ekk = EKK(
            active_power_limit_kw=ekk_active_power_limit_kw,
            target_reactive_power_kvar=0
        )

        self.clock = SimulationClock()

    def start(self):
        for inverter in self.inverters.values():
            inverter.set_active_power(
                inverter.config.ac_rated_kw
            )

            inverter.set_reactive_power(0.0)
            inverter.start()

    def get_inverter_data(self):
        return {
            name: inverter.get_data()
            for name, inverter in self.inverters.items()
        }

    def reset(self):
        self.__init__(**self.config)

    def step(
            self,
            irradiance: float,
            ambient_temp: float,
            dt_seconds: float,
            cloud_cover=None,
            datetime_days=None,
            datetime_hours=None
    ):
        requested_time = self.clock.validate_step(
            date_value=datetime_days,
            time_value=datetime_hours,
            dt_seconds=dt_seconds
        )

        cell_temp = ambient_temp + (irradiance / 800) * 20

        inverter_results = {}
        available_active_kw = 0.0
        total_active_kw = 0.0
        total_reactive_kvar = 0.0

        # 1. Her invertörün üretim potansiyelini hesapla
        # Bu hesap mevcut inverter.step() ile aynı
        # fiziksel DC güç modelini kullanmalıdır.
        available_by_inverter = {}

        for name, inverter in self.inverters.items():
            available_kw = inverter.calculate_available_power(
                irradiance_w_m2=irradiance,
                cell_temperature_c=cell_temp
            )

            available_by_inverter[name] = available_kw
            available_active_kw += available_kw

        # 2. EKK'nin şebeke limitini invertör tarafına çevir
        efficiency = self.transformer.efficiency

        if efficiency <= 0:
            raise ValueError("Trafo verimi sıfırdan büyük olmalı.")

        max_inverter_power_kw = (
                self.ekk.active_power_limit_kw / efficiency
        )

        commanded_total_kw = min(
            available_active_kw,
            max_inverter_power_kw
        )

        # 3. EKK komutunu kullanılabilir güce göre dağıt
        for name, inverter in self.inverters.items():
            available_kw = available_by_inverter[name]

            if available_active_kw > 0:
                share = available_kw / available_active_kw
            else:
                share = 0.0

            inverter.set_active_power(
                min(
                    inverter.config.ac_rated_kw,
                    commanded_total_kw * share
                )
            )

        # 4. Gerçek saatlik üretimi hesapla
        for name, inverter in self.inverters.items():
            inverter.step(
                irradiance_w_m2=irradiance,
                cell_temperature_c=cell_temp,
                dt_seconds=dt_seconds
            )

            data = inverter.get_data()

            data.update({
                "ambient_temperature_c": ambient_temp,
                "cell_temperature_c": cell_temp,
                "solarradiation": irradiance,
                "cloud_cover": cloud_cover,
                "datetime_days": datetime_days,
                "datetime_hours": datetime_hours
            })

            inverter_results[name] = data

            total_active_kw += data["ac_power_kw"]
            total_reactive_kvar += data["reactive_power_kvar"]

        # 5. Kısılan üretim potansiyelini hesapla
        power_difference_kw = (
                available_active_kw - total_active_kw
        )

        curtailed_power_kw = (
            max(0.0, power_difference_kw)
            if power_difference_kw > 0.01
            else 0.0
        )

        curtailed_energy_kwh = (
                curtailed_power_kw * dt_seconds / 3600
        )

        # 6. Enerji analizörü
        analyzer_reading = self.analyzer.measure(
            active_power_kw=total_active_kw,
            reactive_power_kvar=total_reactive_kvar,
            voltage_v=400,
            frequency_hz=50,
            dt_seconds=dt_seconds
        )

        # 7. Trafo
        transformer_data = self.transformer.step(
            active_power_kw=total_active_kw,
            reactive_power_kvar=total_reactive_kvar
        )

        # 8. EKK ölçüm ve reaktif güç kontrolü
        ekk_reading = self.ekk.control(
            measured_active_power_kw=transformer_data[
                "output_power_kw"
            ],
            measured_reactive_power_kvar=transformer_data[
                "output_reactive_kvar"
            ],
            current_inverter_reactive_kvar=total_reactive_kvar,
            available_active_power_kw=available_active_kw,
            transformer_efficiency=efficiency
        )

        # Reaktif güç komutu sonraki adım için uygulanır
        reactive_command = ekk_reading.reactive_command_kvar
        command_per_inverter = (
                reactive_command / len(self.inverters)
        )

        for inverter in self.inverters.values():
            inverter.set_reactive_power(command_per_inverter)

        self.clock.commit_step(requested_time)

        return {
            "inverters": inverter_results,

            "total": {
                "active_power_kw": round(total_active_kw, 3),
                "reactive_power_kvar": round(
                    total_reactive_kvar, 3
                ),
                "inverter_count": len(self.inverters)
            },

            "energy_analyzer": analyzer_reading.to_dict(),

            "transformer": transformer_data,

            "ekk": ekk_reading.to_dict(),

            "simulation": {
                "current_time": requested_time.isoformat(),
                "dt_seconds": dt_seconds
            },

            "curtailment": {
                "available_active_power_kw": round(
                    available_active_kw, 3
                ),
                "actual_active_power_kw": round(
                    total_active_kw, 3
                ),
                "curtailed_power_kw": round(
                    curtailed_power_kw, 3
                ),
                "curtailed_energy_kwh": round(
                    curtailed_energy_kwh, 3
                )
            }
        }

