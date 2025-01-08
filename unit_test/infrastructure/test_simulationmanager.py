#  Copyright (c) 2024. Deltares & TNO
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.

import unittest
import uuid
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock

from omotes_simulator_core.entities.esdl_object import EsdlObject
from omotes_simulator_core.entities.simulation_configuration import SimulationConfiguration
from omotes_simulator_core.infrastructure.simulation_manager import SimulationManager
from omotes_simulator_core.infrastructure.utils import pyesdl_from_file


class SimulationManagerTest(unittest.TestCase):
    """Test clas for the SimulationManager."""

    def test_network_simulation_run(self) -> None:
        """Test for simulation."""
        # Arrange
        esdl_file_path = str(Path(__file__).parent / ".." / ".." / "testdata" / "test1.esdl")
        config = SimulationConfiguration(
            simulation_id=uuid.uuid1(),
            name="test run",
            timestep=3600,
            start=datetime.strptime("2019-01-01T00:00:00", "%Y-%m-%dT%H:%M:%S"),
            stop=datetime.strptime("2019-01-01T01:00:00", "%Y-%m-%dT%H:%M:%S"),
        )
        callback = Mock()
        app = SimulationManager(EsdlObject(pyesdl_from_file(esdl_file_path)), config)

        # Act
        result = app.execute(callback)

        # Assert
        self.assertIsNotNone(result)
        self.assertTrue(callback.called)
        self.assertEqual(result.shape, (1, 46))
