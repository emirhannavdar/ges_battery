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


def test_inverter_available_power(inverter):
    result = inverter.calculate_available_power(
        irradiance_w_m2=800,
        cell_temperature_c=25
    )

    assert result == pytest.approx(900)        # assert bir koşulun doğru olup olmadığını test eder.
                                                    # pytest.approx() ise ondalıklı sayılarda küçük farkları tolere eder

def test_inverter_negative_irradiance(inverter):
    with pytest.raises(ValueError, match="irradiance must be nonnegative"):
        inverter.calculate_available_power(
            irradiance_w_m2=-100,
            cell_temperature_c=25
        )

def test_inver_ac_power_limit(inverter):
    result = inverter.calculate_available_power(
        irradiance_w_m2=1200,
        cell_temperature_c=25
    )

    expected = 900

    assert result == pytest.approx(expected)

def test_calculate_available_power_does_not_change_energy(inverter):
    energy_before= inverter.energy_kwh

    inverter.calculate_available_power(
        irradiance_w_m2=1000,
        cell_temperature_c=25
    )

    assert inverter.energy_kwh == energy_before

def test_inverter_zero_irradiance(inverter):
    result = inverter.calculate_available_power(
        irradiance_w_m2=0,
        cell_temperature_c=25
    )
    expected = 0.0
    assert result == expected

def test_inverter_status_off():
    config = InverterConfig(
        ac_rated_kw=900,
        dc_rated_kw=1200,
        efficiency=0.97
    )

    inv = Inverter(config=config)
    inv.status = InverterStatus.OFF

    result = inv.calculate_available_power(
        irradiance_w_m2=1000,
        cell_temperature_c=25
    )

    expected = 0.0
    assert result == pytest.approx(expected)

def test_inverter_status_fault(inverter):
    inverter.status = InverterStatus.FAULT

    result = inverter.calculate_available_power(
        irradiance_w_m2=1000,
        cell_temperature_c=25
    )
    expected = 0.0

    assert result == pytest.approx(expected)

def test_inverter_temperature_factor(inverter):
    inverter.calculate_available_power(
        irradiance_w_m2=1000,
        cell_temperature_c=35
    )

    result = inverter.temperature_factor
    expected = 0.965

    assert result == pytest.approx(expected)

def test_inverter_dc_kw(inverter):
    inverter.calculate_available_power(
        irradiance_w_m2=1000,
        cell_temperature_c=35
    )

    result = inverter.dc_kw

    assert result == pytest.approx(1158)

def test_available_kw(inverter):
    inverter.calculate_available_power(
        irradiance_w_m2=1000,
        cell_temperature_c=35
    )

    result = inverter.available_kw

    assert result == pytest.approx(900)




