import json
import pytest

from simulation.simulation_manager import SimulationManager

def test_simulation_state_restore():
    manager = SimulationManager(inverter_count=2)
    manager.start()

    manager.step(
        irradiance=500,
        ambient_temp=25,
        dt_seconds=3600,
        datetime_days="2026-11-18",
        datetime_hours="10:00:00"
    )

    # JSONB'ye yazılıp okunmasını taklit et
    state = json.loads(json.dumps(manager.export_state()))

    restored = SimulationManager.from_state(state)

    assert restored.export_state() == state

    assert restored.clock.current_time == manager.clock.current_time

    assert (
        restored.inverters["inverter_1"].energy_kwh
        == manager.inverters["inverter_1"].energy_kwh
    )


def test_simulation_continues_after_restore():
    manager = SimulationManager(inverter_count=2)
    manager.start()

    manager.step(
        irradiance=500,
        ambient_temp=25,
        dt_seconds=3600,
        datetime_days="2026-11-18",
        datetime_hours="10:00:00"
    )

    state = json.loads(json.dumps(manager.export_state()))
    restored = SimulationManager.from_state(state)

    result_original = manager.step(
        irradiance=600,
        ambient_temp=26,
        dt_seconds=3600,
        datetime_days="2026-11-18",
        datetime_hours="11:00:00"
    )

    result_restored = restored.step(
        irradiance=600,
        ambient_temp=26,
        dt_seconds=3600,
        datetime_days="2026-11-18",
        datetime_hours="11:00:00"
    )

    assert result_original == result_restored


def test_simulation_state_invalid_version():
    manager = SimulationManager()
    state = manager.export_state()

    state["schema_version"] = 999

    with pytest.raises(ValueError):
        SimulationManager.from_state(state)