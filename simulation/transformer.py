from math import sqrt


class Transformer:

    def __init__(
        self,
        rated_kva=1600,
        lv_voltage_v=400,
        hv_voltage_v=34500,
        efficiency=0.99
    ):
        self.rated_kva = rated_kva
        self.lv_voltage_v = lv_voltage_v
        self.hv_voltage_v = hv_voltage_v
        self.efficiency = efficiency

    def step(
        self,
        active_power_kw,
        reactive_power_kvar
    ):
        # AG tarafı görünür güç
        input_kva = sqrt(
            active_power_kw ** 2
            + reactive_power_kvar ** 2
        )

        # Trafo kapasitesi kontrolü
        overloaded = input_kva > self.rated_kva

        # Basitleştirilmiş aktif güç kaybı
        output_kw = active_power_kw * self.efficiency

        loss_kw = active_power_kw - output_kw

        # İlk sürümde reaktif güç değişmiyor
        output_kvar = reactive_power_kvar

        # OG tarafı görünür güç
        output_kva = sqrt(
            output_kw ** 2
            + output_kvar ** 2
        )

        # OG tarafı hat akımı
        output_current_a = (
            output_kva * 1000
            / (sqrt(3) * self.hv_voltage_v)
        )

        return {
            "input_power_kw": round(active_power_kw, 3),
            "input_reactive_kvar": round(reactive_power_kvar, 3),
            "input_apparent_kva": round(input_kva, 3),
            "output_power_kw": round(output_kw, 3),
            "output_reactive_kvar": round(output_kvar, 3),
            "output_apparent_kva": round(output_kva, 3),
            "output_voltage_v": self.hv_voltage_v,
            "output_current_a": round(output_current_a, 3),
            "loss_kw": round(loss_kw, 3),
            "overloaded": overloaded
        }