from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session
from simulation.inverter import Inverter
from database.database import get_db
from api.errors.exceptions import DomainError
from simulation.energy_analyzer import EnergyAnalyzer
from simulation.transformer import Transformer
from simulation.ekk import EKK
from auth.auth import User, get_current_user

inverter_router = APIRouter(
    prefix="/inverter",
    tags=["Inverter Simulation"]
)

inverter = Inverter()
analyzer = EnergyAnalyzer()
transformer = Transformer()
ekk = EKK(active_power_limit_kw=800, target_reactive_power_kvar=0)

class InverterStepRequest(BaseModel):
    saat_kac: str = Field(default="11:00:00")
    hangi_gun: str = Field(default="yyyy-aa-gg")
    dt_seconds: float = Field(default=3600, gt=0)


@inverter_router.post("/start")
def start_inverter(
        current_user: User = Depends(get_current_user)
):

    inverter.start()

    return {
        "success": True,
        "message": "İnvertör başlatıldı."
    }


@inverter_router.post("/step")
def step_inverter(
        request: InverterStepRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):

    result_db = db.execute(
        text("""
            SELECT measurement_time, temperature, solar_radiation, cloud_cover, datetime_days, datetime_hours
            FROM weather_data
            WHERE datetime_hours = :target_time and datetime_days = :target_days LIMIT 1
        """), {"target_time": request.saat_kac, "target_days": request.hangi_gun}
    )

    weather = result_db.mappings().first()

    if weather is None:
        raise DomainError("Veri bulunamadı")

    ambient_temp = weather["temperature"]
    irradiance = weather["solar_radiation"]

    if ambient_temp is None or irradiance is None:
        raise DomainError(
            "Sıcaklık veya güneş ışınımı verisi eksik."
        )

    cell_temp = ambient_temp + (irradiance / 800) * 20

    print(
        "STEP ÖNCESİ SETPOINT:",
        inverter.reactive_power_setpoint_kvar
    )

    inverter.step(
        irradiance_w_m2=irradiance,
        cell_temperature_c=cell_temp,
        dt_seconds=request.dt_seconds
    )

    result = inverter.get_data()

    analyzer_reading = analyzer.measure(
        active_power_kw=result["ac_power_kw"],
        reactive_power_kvar=result["reactive_power_kvar"],
        voltage_v=result["line_voltage_v"],
        frequency_hz=result["frequency_hz"],
        dt_seconds=request.dt_seconds
    )

    transformer_data = transformer.step(
        active_power_kw=result["ac_power_kw"],
        reactive_power_kvar=result["reactive_power_kvar"]
    )

    ekk_reading = ekk.control(
        measured_active_power_kw=transformer_data["output_power_kw"],
        measured_reactive_power_kvar=transformer_data["output_reactive_kvar"],
        current_inverter_reactive_kvar=result["reactive_power_kvar"]
    )
    print(
        "EKK ÖNCESİ:",
        inverter.reactive_power_setpoint_kvar
    )
    inverter.set_reactive_power(
        ekk_reading.reactive_command_kvar
    )
    print(
        "EKK SONRASI:",
        inverter.reactive_power_setpoint_kvar
    )
    result["ambient_temperature_c"] = ambient_temp
    result["cell_temperature_c"] = cell_temp
    result["solarradiation"] = irradiance
    result["cloud_cover"] = weather["cloud_cover"]
    result["datetime_days"] = weather["datetime_days"]
    result["datetime_hours"] = weather["datetime_hours"]

    return {
        "success": True,
        "data": {
            "invertor": result,
            "energy_analyzer": analyzer_reading.to_dict(),
            "transformer": transformer_data,
            "ekk": ekk_reading.to_dict()
        }
    }


@inverter_router.get("/data")
def get_inverter_data(current_user: User = Depends(get_current_user)):

    return {
        "success": True,
        "data": inverter.get_data()
    }