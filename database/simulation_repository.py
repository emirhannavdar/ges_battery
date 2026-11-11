from sqlalchemy import text
from sqlalchemy.orm import Session


def save_daily_simulation(
    db: Session,
    username: str,
    result: dict,
    inverter_count: int,
    config: dict
) -> int:

    try:
        run_result = db.execute(
            text("""
                INSERT INTO simulation_runs (
                    username,
                    simulation_date,
                    inverter_count,
                    processed_hours,
                    total_inverter_energy_kwh,
                    total_grid_energy_kwh,
                    total_transformer_loss_kwh,
                    total_curtailed_energy_kwh,
                    inverter_ac_rated_kw,
                    inverter_dc_rated_kw,
                    ekk_active_power_limit_kw,
                    transformer_efficiency
                )
                VALUES (
                    :username,
                    :simulation_date,
                    :inverter_count,
                    :processed_hours,
                    :total_inverter_energy_kwh,
                    :total_grid_energy_kwh,
                    :total_transformer_loss_kwh,
                    :total_curtailed_energy_kwh,
                    :inverter_ac_rated_kw,
                    :inverter_dc_rated_kw,
                    :ekk_active_power_limit_kw,
                    :transformer_efficiency
                )
                RETURNING id
            """),
            {
                "username": username,
                "simulation_date": result["date"],
                "inverter_count": inverter_count,
                "processed_hours": result["processed_hours"],
                "total_inverter_energy_kwh":
                    result["total_inverter_energy_kwh"],
                "total_grid_energy_kwh":
                    result["total_grid_energy_kwh"],
                "total_transformer_loss_kwh":
                    result["total_transformer_loss_kwh"],
                "total_curtailed_energy_kwh":
                    result["total_curtailed_energy_kwh"],
                "inverter_ac_rated_kw":
                    config["inverter_ac_rated_kw"],
                "inverter_dc_rated_kw":
                    config["inverter_dc_rated_kw"],
                "ekk_active_power_limit_kw":
                    config["ekk_active_power_limit_kw"],
                "transformer_efficiency":
                    config["transformer_efficiency"]
            }
        )

        simulation_id = run_result.scalar_one()

        hourly_parameters = [
            {
                "simulation_id": simulation_id,
                "hour": item["hour"],
                "irradiance_w_m2":
                    item["irradiance_w_m2"],
                "ambient_temperature_c":
                    item["ambient_temperature_c"],
                "inverter_power_kw":
                    item["inverter_power_kw"],
                "grid_power_kw":
                    item["grid_power_kw"],
                "transformer_loss_kw":
                    item["transformer_loss_kw"],
                "ekk_limit_exceeded":
                    item["ekk_limit_exceeded"],
                "available_active_power_kw":
                    item["available_active_power_kw"],
                "curtailed_power_kw":
                    item["curtailed_power_kw"],
                "curtailed_energy_kwh":
                    item["curtailed_energy_kwh"]
            }
            for item in result["hourly_results"]
        ]

        db.execute(
            text("""
                INSERT INTO simulation_hourly_results (
                    simulation_id,
                    hour,
                    irradiance_w_m2,
                    ambient_temperature_c,
                    inverter_power_kw,
                    grid_power_kw,
                    transformer_loss_kw,
                    ekk_limit_exceeded,
                    available_active_power_kw,
                    curtailed_power_kw,
                    curtailed_energy_kwh
                )
                VALUES (
                    :simulation_id,
                    :hour,
                    :irradiance_w_m2,
                    :ambient_temperature_c,
                    :inverter_power_kw,
                    :grid_power_kw,
                    :transformer_loss_kw,
                    :ekk_limit_exceeded,
                    :available_active_power_kw,
                    :curtailed_power_kw,
                    :curtailed_energy_kwh
                )
            """),
            hourly_parameters
        )

        db.commit()
        return simulation_id

    except Exception:
        db.rollback()
        raise




def get_simulations_by_user(
    db: Session,
    username: str
):
    result = db.execute(
        text("""
            SELECT
                id,
                simulation_date,
                inverter_count,
                processed_hours,
                total_inverter_energy_kwh,
                total_grid_energy_kwh,
                total_transformer_loss_kwh,
                created_at
            FROM simulation_runs
            WHERE username = :username
            ORDER BY created_at DESC, id DESC
        """),
        {"username": username}
    )

    return [
        dict(row)
        for row in result.mappings().all()
    ]


def get_simulation_detail(
    db: Session,
    simulation_id: int,
    username: str
):
    result = db.execute(
        text("""
            SELECT *
            FROM simulation_runs
            WHERE id = :simulation_id
              AND username = :username
        """),
        {
            "simulation_id": simulation_id,
            "username": username
        }
    )

    simulation = result.mappings().first()

    if simulation is None:
        return None

    hourly_result = db.execute(
        text("""
            SELECT
                hour,
                irradiance_w_m2,
                ambient_temperature_c,
                inverter_power_kw,
                grid_power_kw,
                transformer_loss_kw,
                ekk_limit_exceeded
            FROM simulation_hourly_results
            WHERE simulation_id = :simulation_id
            ORDER BY hour ASC
        """),
        {"simulation_id": simulation_id}
    )

    data = dict(simulation)
    data["hourly_results"] = [
        dict(row)
        for row in hourly_result.mappings().all()
    ]

    return data


def compare_simulations_db(
    db: Session,
    username: str,
    simulation_id_1: int,
    simulation_id_2: int
):
    result = db.execute(
        text("""
            SELECT
                id,
                simulation_date,
                inverter_count,
                inverter_ac_rated_kw,
                inverter_dc_rated_kw,
                ekk_active_power_limit_kw,
                transformer_efficiency,
                total_inverter_energy_kwh,
                total_grid_energy_kwh,
                total_transformer_loss_kwh
            FROM simulation_runs
            WHERE username = :username
              AND id IN (:id_1, :id_2)
        """),
        {
            "username": username,
            "id_1": simulation_id_1,
            "id_2": simulation_id_2
        }
    )

    rows = {
        row["id"]: dict(row)
        for row in result.mappings().all()
    }

    return (
        rows.get(simulation_id_1),
        rows.get(simulation_id_2)
    )
