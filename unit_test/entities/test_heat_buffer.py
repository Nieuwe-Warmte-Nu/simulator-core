#  Copyright (c) 2023. Deltares & TNO
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

"""Test Ates Cluster entities."""
import faulthandler
import unittest

faulthandler.disable()
from omotes_simulator_core.entities.assets.heat_buffer import HeatBuffer  # noqa: E402

faulthandler.enable()
from omotes_simulator_core.entities.assets.asset_defaults import (  # noqa: E402
    PROPERTY_HEAT_DEMAND,
)


class HeatBufferTest(unittest.TestCase):
    """Testcase for HeatBuffer class."""

    def setUp(self) -> None:
        """Set up before each test case."""
        # Create a production cluster object
        self.heat_buffer = HeatBuffer(
            asset_name="heat_buffer", asset_id="heat_buffer_id", port_ids=["test1", "test2"],
            maximum_volume=1, fill_level=0.5
        )
        self.heat_buffer.temperature_supply = 353.15
        self.heat_buffer.temperature_return = 313.15
        faulthandler.disable()

    def tearDown(self):
        """Clean up after each test case."""
        faulthandler.enable()

    def test_injection(self) -> None:
        """Test injection to Heat Buffer."""
        # Arrange
        setpoints = {
            PROPERTY_HEAT_DEMAND: 1e4,
        }

        # Act
        self.heat_buffer.set_setpoints(setpoints=setpoints)

        # Assert
        self.assertAlmostEqual(self.heat_buffer.temperature_supply, 353.15, delta=0.1)
        self.assertAlmostEqual(self.heat_buffer.temperature_return, 313.15, delta=0.1)
        self.assertAlmostEqual(self.heat_buffer.fill_level, 0.72, delta=0.01)

    def test_production(self) -> None:
        """Test production from Heat Buffer."""
        # Arrange
        setpoints = {
            PROPERTY_HEAT_DEMAND: -1e4,
        }

        # Act
        self.heat_buffer.set_setpoints(setpoints=setpoints)

        # Assert
        self.assertAlmostEqual(self.heat_buffer.temperature_supply, 353.15, delta=0.1)
        self.assertAlmostEqual(self.heat_buffer.temperature_return, 313.15, delta=0.1)
        self.assertAlmostEqual(self.heat_buffer.fill_level, 0.27, delta=0.01)
