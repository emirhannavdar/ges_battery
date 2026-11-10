import unittest
from inverter import Inverter, InverterConfig

class InverterTests(unittest.TestCase):
    def test_off(self):
        inv = Inverter()
        self.assertEqual(inv.step(800, 25).ac_power_kw, 0)
    def test_generation_and_energy(self):
        inv = Inverter()
        inv.start()
        r = inv.step(1000, 25, 3600)
        self.assertEqual(r.ac_power_kw, 900)
        self.assertEqual(r.energy_kwh, 900)
    def test_night(self):
        inv = Inverter()
        inv.start()
        self.assertEqual(inv.step(0, 25).status, "standby")
    def test_reactive_limit(self):
        inv = Inverter()
        inv.start()
        inv.set_reactive_power(800)
        r = inv.step(1000, 25)
        self.assertAlmostEqual(r.ac_power_kw, 600)
        self.assertAlmostEqual(r.apparent_power_kva, 1000)
    def test_fault(self):
        inv = Inverter()
        inv.start()
        inv.set_fault("overtemperature")
        self.assertEqual(inv.step(800, 25).status, "fault")
        with self.assertRaises(RuntimeError): inv.start()
        inv.reset_fault()
        inv.start()
        self.assertEqual(inv.step(800, 25).status, "running")
    def test_invalid_config(self):
        with self.assertRaises(ValueError): InverterConfig(efficiency=1.2)

if __name__ == "__main__":
    unittest.main()
