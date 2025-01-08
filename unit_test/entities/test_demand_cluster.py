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

"""Test demand cluster."""

import unittest
from unittest.mock import patch
from omotes_simulator_core.entities.assets.demand_cluster import DemandCluster
from omotes_simulator_core.entities.assets.asset_defaults import (
    DEFAULT_DIAMETER,
    DEFAULT_POWER,
    DEFAULT_PRESSURE,
    DEFAULT_TEMPERATURE,
    DEFAULT_TEMPERATURE_DIFFERENCE,
)


class TestDemandCluster(unittest.TestCase):
    """Test demand cluster."""

    def setUp(self) -> None:
        """Set up test case."""
        # Create a production cluster object
        self.heat_demand = DemandCluster(
            asset_name="production_cluster",
            asset_id="production_cluster_id",
            port_ids=["test1", "test2"],
        )

    def test_demand_cluster_create(self):
        """Evaluate the creation of a demand cluster object."""
        # Arrange

        # Act
        demand_cluster = DemandCluster(
            asset_name="demand_cluster",
            asset_id="demand_cluster_id",
            port_ids=["test1", "test2"],
        )

        # Assert
        self.assertEqual(demand_cluster.name, "demand_cluster")
        self.assertEqual(demand_cluster.asset_id, "demand_cluster_id")
        self.assertEqual(demand_cluster.connected_ports, ["test1", "test2"])
        self.assertEqual(demand_cluster._internal_diameter, DEFAULT_DIAMETER)
        self.assertEqual(demand_cluster.temperature_supply, DEFAULT_TEMPERATURE)
        self.assertEqual(
            demand_cluster.temperature_return, DEFAULT_TEMPERATURE - DEFAULT_TEMPERATURE_DIFFERENCE
        )
        self.assertEqual(
            demand_cluster.temperature_return_target,
            DEFAULT_TEMPERATURE - DEFAULT_TEMPERATURE_DIFFERENCE,
        )
        self.assertEqual(demand_cluster.pressure_input, DEFAULT_PRESSURE)
        self.assertEqual(demand_cluster.thermal_power_allocation, DEFAULT_POWER)
        self.assertEqual(demand_cluster.mass_flowrate, 0.0)
        self.assertEqual(demand_cluster.solver_asset.name, "demand_cluster")
        self.assertEqual(demand_cluster.output, [])

    def test_get_actual_heat_supplied(self):
        """Evaluate the get_actual_heat_supplied method."""
        pass  # need to not have a blank line after the docstring.

        # Arrange
        def get_internal_energy(_, i: int):
            if i == 0:
                return 1.0e6
            if i == 1:
                return 2.0e6

        def get_mass_flow_rate(_, i: int):
            return 0.5

        with patch(
            "omotes_simulator_core.solver.network.assets.base_asset.BaseAsset.get_internal_energy",
            get_internal_energy,
        ), patch(
            "omotes_simulator_core.solver.network.assets.base_asset.BaseAsset.get_mass_flow_rate",
            get_mass_flow_rate,
        ):
            # Act
            actual_heat_supplied = self.heat_demand.get_actual_heat_supplied()
            # Assert
            self.assertEqual(actual_heat_supplied, 0.5 * 1e6)
