import json
from uuid import uuid4, UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session
from database.database import get_db
from api.errors.exceptions import DomainError
from auth.auth import User, get_current_user, get_current_active_user
from simulation.simulation_manager import SimulationManager
from datetime import date, datetime, time, timedelta
from database.simulation_repository import (
    save_daily_simulation,
    get_simulations_by_user,
    get_simulation_detail,
    compare_simulations_db,
    get_user_simulation,
    get_user_simulation_for_update,
    update_simulation_state
)
from auth.admin_roles import operator_require_roles

inverter_router = APIRouter(
    prefix="/inverter",
    tags=["Inverter Simulation"]
)

simulation_manager = SimulationManager()

class InverterStepRequest(BaseModel):
    saat_kac: str = Field(default="11:00:00")
    hangi_gun: str = Field(default="yyyy-aa-gg")
    dt_seconds: float = Field(default=3600, gt=0)

class DailySimulationRequest(BaseModel):
    simulation_date: date

    inverter_count: int = Field(
        default=3,
        ge=1,
        le=100
    )

    inverter_ac_rated_kw: float = Field(
        default=900,
        gt=0
    )

    inverter_dc_rated_kw: float = Field(
        default=1000,
        gt=0
    )

    ekk_active_power_limit_kw: float = Field(
        default=800,
        ge=0
    )

class InverterFaultRequest(BaseModel):
    inverter_id: str
    reason: str = Field(min_length=1)

class CreateSimulationRequest(BaseModel):
    inverter_count: int = Field(default=3, ge=1, le=100)

def load_session_manager(
        db: Session,
        simulation_id: UUID,
        user_id: int,
        require_running: bool = True
):
    simulation = get_user_simulation_for_update(
        db=db,
        simulation_id=simulation_id,
        user_id=user_id
    )

    if simulation is None:
        raise HTTPException(
            status_code=404,
            detail="Simulasyon bulunamadı"
        )

    if require_running and simulation["status"] != "running":
        raise HTTPException(
            status_code=409,
            detail="Simulasyon çalışır durumda değil."
        )

    manager = SimulationManager.from_state(
        simulation["state"]
    )

    return simulation, manager

@inverter_router.post('/sessions', status_code=201)
def create_simulation(
        request: CreateSimulationRequest,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_active_user),
        user_roles: dict = Depends(operator_require_roles())
):
    simulation_id = str(uuid4())

    manager = SimulationManager(inverter_count=request.inverter_count)

    state = manager.export_state()

    try:
        db.execute(
            text(
                """
                    INSERT INTO simulation_sessions (
                        id,
                        user_id,
                        inverter_count,
                        status,
                        state
                    )
                    VALUES (
                        :id,
                        :user_id,
                        :inverter_count,
                        :status,
                        CAST(:state AS JSONB)
                    )
                """
            ), {
                "id": simulation_id,
                "user_id": user.id,
                "inverter_count": request.inverter_count,
                "status": "created",
                "state": json.dumps(state)
            }
        )

        db.commit()
    except Exception:
        db.rollback()
        raise

    return {
        "simulation_id": simulation_id,
        "status": "created"
    }

@inverter_router.post("/sessions/{simulation_id}/start")
def start_simulation_session(
    simulation_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_active_user),
    user_roles: dict = Depends(operator_require_roles())
):
    try:
        simulation = get_user_simulation_for_update(
            db, simulation_id, user.id
        )

        if simulation is None:
            raise HTTPException(404, "Simülasyon bulunamadı.")

        if simulation["status"] != "created":
            raise HTTPException(
                409, "Simülasyon zaten başlatılmış."
            )

        manager = SimulationManager.from_state(
            simulation["state"]
        )

        manager.start()

        update_simulation_state(
            db=db,
            simulation_id=simulation_id,
            user_id=user.id,
            state=manager.export_state(),
            status="running"
        )

        db.commit()

        return {
            "success": True,
            "simulation_id": simulation_id,
            "status": "running"
        }

    except Exception:
        db.rollback()
        raise

@inverter_router.get('/sessions/{simulation_id}')
def get_simulations(
        simulation_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
        user_roles: dict = Depends(operator_require_roles())
):
    simulation = get_user_simulation(
        db=db,
        simulation_id = simulation_id,
        user_id=current_user.id
    )

    if simulation is None:
        raise HTTPException(
            status_code=404,
            detail="Simulasyon bulunamadı."
        )

    return dict(simulation)

@inverter_router.post("/start")
def start_inverter(
        current_user: User = Depends(get_current_user),
        active_user: User = Depends(get_current_active_user),
        user_roles: dict = Depends(operator_require_roles())
):

    simulation_manager.start()

    return {
        "success": True,
        "message": "İnvertör başlatıldı."
    }

@inverter_router.post("/sessions/{simulation_id}/step")
def step_simulation_session(
    simulation_id: UUID,
    request: InverterStepRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_active_user),
    user_roles: dict = Depends(operator_require_roles())
):
    try:
        simulation = get_user_simulation_for_update(
            db, simulation_id, user.id
        )

        if simulation is None:
            raise HTTPException(404, "Simülasyon bulunamadı.")

        if simulation["status"] != "running":
            raise HTTPException(
                409, "Önce simülasyonu başlatmalısınız."
            )

        weather = db.execute(
            text("""
                SELECT temperature, solar_radiation,
                       cloud_cover, datetime_days, datetime_hours
                FROM weather_data
                WHERE datetime_days = :day
                  AND datetime_hours = :hour
                LIMIT 1
            """),
            {
                "day": request.hangi_gun,
                "hour": request.saat_kac
            }
        ).mappings().first()

        if weather is None:
            raise HTTPException(404, "Hava durumu bulunamadı.")

        if (
            weather["temperature"] is None
            or weather["solar_radiation"] is None
        ):
            raise HTTPException(
                422, "Hava durumu verileri eksik."
            )

        manager = SimulationManager.from_state(
            simulation["state"]
        )

        try:
            result = manager.step(
                irradiance=float(weather["solar_radiation"]),
                ambient_temp=float(weather["temperature"]),
                dt_seconds=request.dt_seconds,
                cloud_cover=weather["cloud_cover"],
                datetime_days=str(weather["datetime_days"]),
                datetime_hours=str(weather["datetime_hours"])
            )
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc

        update_simulation_state(
            db=db,
            simulation_id=simulation_id,
            user_id=user.id,
            state=manager.export_state(),
            status="running"
        )

        db.commit()

        return {
            "success": True,
            "simulation_id": simulation_id,
            "data": result
        }

    except Exception:
        db.rollback()
        raise

@inverter_router.post("/sessions/{simulation_id}/reset")
def reset_simulation_session(
        simulation_id: UUID,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_active_user),
        user_roles: dict = Depends(operator_require_roles())
):
    try:
        simulation, manager = load_session_manager(
            db, simulation_id, user.id,
            require_running=False
        )

        manager.reset()

        update_simulation_state(
            db=db,
            simulation_id=simulation_id,
            user_id=user.id,
            state=manager.export_state(),
            status="created"
        )

        db.commit()

        return {
            "success": True,
            "simulation_id": simulation_id,
            "status": "created",
            "message": "Simulasyon sıfırlandı."
        }

    except Exception:
        db.rollback()
        raise

@inverter_router.post("/sessions/{simulation_id}/fault")
def create_session_inverter_fault(
    simulation_id: UUID,
    request: InverterFaultRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_active_user),
    user_roles: dict = Depends(operator_require_roles())
):
    try:
        simulation, manager = load_session_manager(
            db, simulation_id, user.id
        )

        try:
            manager.set_inverter_fault(
                inverter_id=request.inverter_id,
                reason=request.reason
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail=str(exc)
            ) from exc

        update_simulation_state(
            db=db,
            simulation_id=simulation_id,
            user_id=user.id,
            state=manager.export_state(),
            status="running"
        )

        db.commit()

        return {
            "success": True,
            "simulation_id": simulation_id,
            "inverter_id": request.inverter_id,
            "message": "İnvertör arızaya alındı."
        }

    except Exception:
        db.rollback()
        raise


@inverter_router.post(
    "/sessions/{simulation_id}/fault/reset/{inverter_id}"
)
def reset_session_inverter_fault(
    simulation_id: UUID,
    inverter_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_active_user),
    user_roles: dict = Depends(operator_require_roles())
):
    try:
        simulation, manager = load_session_manager(
            db, simulation_id, user.id
        )

        if inverter_id not in manager.inverters:
            raise HTTPException(
                status_code=404,
                detail="İnvertör bulunamadı."
            )

        manager.reset_inverter_fault(inverter_id)

        update_simulation_state(
            db=db,
            simulation_id=simulation_id,
            user_id=user.id,
            state=manager.export_state(),
            status="running"
        )

        db.commit()

        return {
            "success": True,
            "simulation_id": simulation_id,
            "inverter_id": inverter_id,
            "message": "İnvertör arızası sıfırlandı."
        }

    except Exception:
        db.rollback()
        raise


@inverter_router.get("/sessions/{simulation_id}/data")
def get_session_inverter_data(
    simulation_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_active_user),
    user_roles: dict = Depends(operator_require_roles())
):
    simulation = get_user_simulation(
        db=db,
        simulation_id=simulation_id,
        user_id=user.id
    )

    if simulation is None:
        raise HTTPException(
            status_code=404,
            detail="Simülasyon bulunamadı."
        )

    manager = SimulationManager.from_state(
        simulation["state"]
    )

    return {
        "success": True,
        "simulation_id": simulation_id,
        "status": simulation["status"],
        "current_time": (
            manager.clock.current_time.isoformat()
            if manager.clock.current_time is not None
            else None
        ),
        "data": manager.get_inverter_data()
    }

@inverter_router.post("/reset")
def reset_simulator(
    active_user: User = Depends(get_current_active_user),
    user_roles: dict = Depends(operator_require_roles())
):
    simulation_manager.reset()

    return {
        "success": True,
        "message": "Simülasyon sıfırlandı."
    }


@inverter_router.post("/step")
def step_inverter(
        request: InverterStepRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        active_user: User = Depends(get_current_active_user),
        user_roles: dict = Depends(operator_require_roles())
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
    try:
        result = simulation_manager.step(
            irradiance=irradiance,
            ambient_temp=ambient_temp,
            dt_seconds=request.dt_seconds,
            cloud_cover=weather["cloud_cover"],
            datetime_days=weather["datetime_days"],
            datetime_hours=weather["datetime_hours"]
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        ) from exc

    return {
        "success": True,
        "data": result
    }

@inverter_router.post('/fault')
def create_inverter_fault(
        request: InverterFaultRequest,
        active_user: User = Depends(get_current_active_user),
        user_roles: dict = Depends(operator_require_roles())
):
    try:
        simulation_manager.set_inverter_fault(
            inverter_id=request.inverter_id,
            reason=request.reason
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        ) from exc

    return {
        "success": True,
        "message": "Inverter arıza üretti."
    }

@inverter_router.post('/fault/reset/{inverter_id}')
def clear_inverter_fault(
        inverter_id: str,
        active_user: User = Depends(get_current_active_user),
        user_roles: dict = Depends(operator_require_roles())
):
    try:
        simulation_manager.reset_inverter_fault(inverter_id)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        ) from e

    return {
        "success": True,
        "message": "Inverter arızası sıfırlandı"
    }



@inverter_router.post("/daily")
def daily_simulation(
    request: DailySimulationRequest,
    db: Session = Depends(get_db),
    active_user: User = Depends(get_current_active_user),
    user_roles: dict = Depends(operator_require_roles())
):
    # 1. Seçilen günün hava durumu verilerini al
    result_db = db.execute(
        text("""
            SELECT
                measurement_time,
                temperature,
                solar_radiation,
                cloud_cover,
                datetime_days,
                datetime_hours
            FROM weather_data
            WHERE datetime_days = :target_day
            ORDER BY datetime_hours ASC
        """),
        {"target_day": request.simulation_date.isoformat()}
    )

    weather_rows = result_db.mappings().all()

    if not weather_rows:
        raise HTTPException(
            status_code=404,
            detail="Seçilen güne ait hava durumu verisi bulunamadı."
        )

    # 2. Saatlik kayıtları doğrula
    hourly_weather = {}

    for weather in weather_rows:
        raw_hour = weather["datetime_hours"]

        if isinstance(raw_hour, time):
            hour_value = raw_hour
        else:
            try:
                hour_value = time.fromisoformat(str(raw_hour))
            except (ValueError, TypeError) as exc:
                raise HTTPException(
                    status_code=422,
                    detail="Veritabanında geçersiz saat değeri var."
                ) from exc

        if (
            hour_value.minute != 0
            or hour_value.second != 0
            or hour_value.microsecond != 0
        ):
            raise HTTPException(
                status_code=422,
                detail="Saatlik simülasyon için tam saat kayıtları gerekiyor."
            )

        hour = hour_value.hour

        if hour in hourly_weather:
            raise HTTPException(
                status_code=409,
                detail=f"{hour:02d}:00 için birden fazla kayıt var."
            )

        if (
            weather["temperature"] is None
            or weather["solar_radiation"] is None
        ):
            raise HTTPException(
                status_code=422,
                detail=f"{hour:02d}:00 hava durumu verisi eksik."
            )

        hourly_weather[hour] = weather

    missing_hours = [
        f"{hour:02d}:00"
        for hour in range(24)
        if hour not in hourly_weather
    ]

    if missing_hours:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "24 saatlik veri eksik.",
                "missing_hours": missing_hours
            }
        )

    # 3. Bağımsız bir simülasyon başlat

    daily_manager = SimulationManager(
        inverter_count=request.inverter_count,
        inverter_ac_rated_kw=request.inverter_ac_rated_kw,
        inverter_dc_rated_kw=request.inverter_dc_rated_kw,
        ekk_active_power_limit_kw=request.ekk_active_power_limit_kw
    )

    daily_manager.start()

    hourly_results = []
    total_grid_energy_kwh = 0.0
    total_transformer_loss_kwh = 0.0
    total_curtailed_energy_kwh = 0.0

    # 4. Saatlik simülasyonu çalıştır
    for hour in range(24):
        weather = hourly_weather[hour]

        result = daily_manager.step(
            irradiance=float(weather["solar_radiation"]),
            ambient_temp=float(weather["temperature"]),
            dt_seconds=3600,
            cloud_cover=weather["cloud_cover"],
            datetime_days=request.simulation_date.isoformat(),
            datetime_hours=f"{hour:02d}:00:00"
        )

        transformer = result["transformer"]
        curtailment = result["curtailment"]

        # 1 saatlik adımda kW * 1 saat = kWh
        grid_energy_kwh = transformer["output_power_kw"]
        loss_energy_kwh = transformer["loss_kw"]

        total_grid_energy_kwh += grid_energy_kwh
        total_transformer_loss_kwh += loss_energy_kwh
        total_curtailed_energy_kwh += curtailment["curtailed_energy_kwh"]

        hourly_results.append({
            "hour": f"{hour:02d}:00",

            "irradiance_w_m2": float(
                weather["solar_radiation"]
            ),

            "ambient_temperature_c": float(
                weather["temperature"]
            ),

            "inverter_power_kw": result["total"][
                "active_power_kw"
            ],

            "grid_power_kw": transformer["output_power_kw"],

            "transformer_loss_kw": transformer["loss_kw"],

            "ekk_limit_exceeded": result["ekk"][
                "active_power_limit_exceeded"
            ],

            "available_active_power_kw": curtailment[
                "available_active_power_kw"
            ],

            "curtailed_power_kw": curtailment[
                "curtailed_power_kw"
            ],

            "curtailed_energy_kwh": curtailment[
                "curtailed_energy_kwh"
            ]
        })

    # 5. İnvertörlerin toplam birikmiş enerjisi
    inverter_data = daily_manager.get_inverter_data()

    total_inverter_energy_kwh = sum(
        inverter["energy_kwh"]
        for inverter in inverter_data.values()
    )

    simulation_data = {
        "date": request.simulation_date.isoformat(),

        "processed_hours": len(hourly_results),

        "total_inverter_energy_kwh": round(
            total_inverter_energy_kwh, 3
        ),

        "total_grid_energy_kwh": round(
            total_grid_energy_kwh, 3
        ),

        "total_transformer_loss_kwh": round(
            total_transformer_loss_kwh, 3
        ),

        "total_curtailed_energy_kwh": round(
            total_curtailed_energy_kwh, 3
        ),

        "hourly_results": hourly_results
    }

    simulation_id = save_daily_simulation(
        db=db,
        username=active_user.username,
        result=simulation_data,
        inverter_count=len(daily_manager.inverters),
        config={
            "inverter_ac_rated_kw": request.inverter_ac_rated_kw,
            "inverter_dc_rated_kw": request.inverter_dc_rated_kw,
            "ekk_active_power_limit_kw":
                request.ekk_active_power_limit_kw,
            "transformer_efficiency":
                daily_manager.transformer.efficiency
        }
    )

    simulation_data["simulation_id"] = simulation_id

    return {
        "success": True,
        "data": simulation_data
    }


@inverter_router.get("/simulations/compare")
def compare_simulations(
    simulation_id_1: int = Query(..., ge=1),
    simulation_id_2: int = Query(..., ge=1),
    db: Session = Depends(get_db),
    active_user: User = Depends(get_current_active_user),
    user_roles: dict = Depends(operator_require_roles())
):
    if simulation_id_1 == simulation_id_2:
        raise HTTPException(
            status_code=400,
            detail="İki farklı simülasyon seçmelisiniz."
        )

    scenario_1, scenario_2 = compare_simulations_db(
        db=db,
        username=active_user.username,
        simulation_id_1=simulation_id_1,
        simulation_id_2=simulation_id_2
    )

    if scenario_1 is None or scenario_2 is None:
        raise HTTPException(
            status_code=404,
            detail="Simülasyonlardan biri bulunamadı."
        )

    energy_1 = scenario_1["total_grid_energy_kwh"]
    energy_2 = scenario_2["total_grid_energy_kwh"]

    difference = energy_2 - energy_1

    percent_change = (
        (difference / energy_1) * 100
        if energy_1 != 0
        else None
    )

    if difference > 0:
        higher_energy_id = simulation_id_2
    elif difference < 0:
        higher_energy_id = simulation_id_1
    else:
        higher_energy_id = None

    return {
        "success": True,
        "data": {
            "scenario_1": scenario_1,
            "scenario_2": scenario_2,
            "comparison": {
                "grid_energy_difference_kwh": round(
                    difference, 3
                ),
                "grid_energy_change_percent": (
                    round(percent_change, 2)
                    if percent_change is not None
                    else None
                ),
                "higher_energy_scenario_id": higher_energy_id,
                "same_weather_date": (
                    scenario_1["simulation_date"]
                    == scenario_2["simulation_date"]
                )
            }
        }
    }


@inverter_router.get("/simulations")
def list_simulations(
    db: Session = Depends(get_db),
    active_user: User = Depends(get_current_active_user),
    user_roles: dict = Depends(operator_require_roles())
):
    simulations = get_simulations_by_user(
        db=db,
        username=active_user.username
    )

    return {
        "success": True,
        "data": {
            "count": len(simulations),
            "simulations": simulations
        }
    }


@inverter_router.get("/simulations/{simulation_id}")
def simulation_detail(
    simulation_id: int,
    db: Session = Depends(get_db),
    active_user: User = Depends(get_current_active_user),
    user_roles: dict = Depends(operator_require_roles())
):
    simulation = get_simulation_detail(
        db=db,
        simulation_id=simulation_id,
        username=active_user.username
    )

    if simulation is None:
        raise HTTPException(
            status_code=404,
            detail="Simülasyon bulunamadı."
        )

    return {
        "success": True,
        "data": simulation
    }


@inverter_router.get("/data")
def get_inverter_data(
    active_user: User = Depends(get_current_active_user),
    user_roles: dict = Depends(operator_require_roles())
):
    return {
        "success": True,
        "data": simulation_manager.get_inverter_data()
    }