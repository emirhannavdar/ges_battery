import pytest
from simulation.inverter import Inverter, InverterConfig, InverterStatus

@pytest.fixture(autouse=True)
def inverter():
    config = InverterConfig(
        ac_rated_kw=900,
        dc_rated_kw=1200,
        efficiency=0.97
    )

    inv = Inverter(config=config)
    inv.start()

    return inv

def test_inverter_step(inverter):
    with pytest.raises(ValueError, match="irradiance must be nonnegative and dt_seconds positive"):
        inverter.step(
            irradiance_w_m2= -100,
            cell_temperature_c= 25,
            dt_seconds=5
        )
        inverter.step()

def test_step_status_off():
    config = InverterConfig(
        ac_rated_kw=900,
        dc_rated_kw=1200,
        efficiency=0.97
    )

    inv = Inverter(config=config)
    inv.status = InverterStatus.OFF

    result = inv.step(
        irradiance_w_m2= 800,
        cell_temperature_c=25
    )

    assert result.status == "off"
    assert result.dc_power_kw == 0.0
    assert result.ac_power_kw == 0.0
    assert result.energy_kwh == 0.0

def test_step_fault(inverter):
    inverter.status = InverterStatus.FAULT

    result = inverter.step(
        irradiance_w_m2= 800,
        cell_temperature_c=25
    )

    assert result.status == "fault"
    assert result.dc_power_kw == 0.0
    assert result.ac_power_kw == 0.0
    assert result.energy_kwh == 0.0

def test_minimum_irradiance_w_m2(inverter):
    result = inverter.step(
        irradiance_w_m2= 19,
        cell_temperature_c=25
    )
    assert result.status == "standby"
    assert result.dc_power_kw == 0.0
    assert result.ac_power_kw == 0.0
