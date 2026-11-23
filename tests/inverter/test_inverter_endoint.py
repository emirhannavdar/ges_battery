from unittest.mock import patch
from uuid import UUID
from api.api import app
from fastapi.testclient import TestClient
from simulation.simulation_manager import SimulationManager

client = TestClient(app)

