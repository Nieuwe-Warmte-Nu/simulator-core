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

"""Test production cluster."""
import unittest
from unittest.mock import patch

from omotes_simulator_core.entities.assets.asset_defaults import (
    PROPERTY_HEAT_DEMAND,
    PROPERTY_MASSFLOW,
    PROPERTY_PRESSURE,
    PROPERTY_TEMPERATURE,
    PROPERTY_VOLUMEFLOW,
    PROPERTY_SET_PRESSURE,
    PROPERTY_TEMPERATURE_RETURN,
    PROPERTY_TEMPERATURE_SUPPLY,
)
from omotes_simulator_core.entities.assets.production_cluster import ProductionCluster
from omotes_simulator_core.solver.utils.fluid_properties import fluid_props
from omotes_simulator_core.entities.assets.utils import (
    heat_demand_and_temperature_to_mass_flow,
)


class ProductionClusterTest(unittest.TestCase):
    """Testcase for ProductionCluster class."""

    def setUp(self) -> None:
        """Set up test case."""
        # Create a production cluster object
        self.production_cluster = ProductionCluster(
            asset_name="production_cluster",
            asset_id="production_cluster_id",
            port_ids=["test1", "test2"],
        )

    def test_production_cluster_create(self) -> None:
        """Evaluate the creation of a production_cluster object."""
        # Arrange

        # Act

        # Assert
        self.assertIsInstance(self.production_cluster, ProductionCluster)
        self.assertEqual(self.production_cluster.name, "production_cluster")
        self.assertEqual(self.production_cluster.asset_id, "production_cluster_id")

    def test_production_cluster_set_setpoints(self) -> None:
        """Test setting setpoints of a production cluster."""
        # Arrange
        setpoints = {
            PROPERTY_HEAT_DEMAND: 1e6,
            PROPERTY_TEMPERATURE_SUPPLY: 353.15,
            PROPERTY_TEMPERATURE_RETURN: 333.15,
            PROPERTY_SET_PRESSURE: False,
        }
        self.production_cluster.set_setpoints(setpoints=setpoints)

        # Act
        mass_flow = heat_demand_and_temperature_to_mass_flow(
            temperature_supply=setpoints[PROPERTY_TEMPERATURE_SUPPLY],
            temperature_return=setpoints[PROPERTY_TEMPERATURE_RETURN],
            thermal_demand=setpoints[PROPERTY_HEAT_DEMAND],
        )

        # Assert
        self.assertEqual(self.production_cluster.temperature_supply, 353.15)
        self.assertEqual(self.production_cluster.temperature_return, 333.15)
        self.assertEqual(self.production_cluster.controlled_mass_flow, mass_flow)
        self.assertEqual(
            self.production_cluster.solver_asset.mass_flow_rate_set_point,  # type: ignore
            self.production_cluster.controlled_mass_flow,
        )
        self.assertNotEqual(
            self.production_cluster.solver_asset.pre_scribe_mass_flow,  # type: ignore
            setpoints[PROPERTY_SET_PRESSURE],
        )

    def test_production_cluster_set_setpoints_missing_setpoint(self) -> None:
        """Test raise ValueError with missing setpoint."""
        # Arrange
        necessary_setpoints = set(
            [PROPERTY_HEAT_DEMAND, PROPERTY_TEMPERATURE_SUPPLY, PROPERTY_TEMPERATURE_RETURN]
        )
        setpoints = {
            PROPERTY_TEMPERATURE_SUPPLY: 353.15,
            PROPERTY_TEMPERATURE_RETURN: 333.15,
            PROPERTY_SET_PRESSURE: False,
        }

        # Act
        with self.assertRaises(ValueError) as cm:
            self.production_cluster.set_setpoints(setpoints=setpoints)

        # Assert
        self.assertIsInstance(cm.exception, ValueError)
        self.assertEqual(
            cm.exception.args[0],
            f"The setpoints {necessary_setpoints.difference(set(setpoints))} are missing.",
        )

    def test_production_cluster_set_setpoints_negative_mass_flow(self) -> None:
        """Test raise ValueError with negative mass flow."""
        # Arrange
        setpoints = {
            PROPERTY_HEAT_DEMAND: -1e6,
            PROPERTY_TEMPERATURE_SUPPLY: 353.15,
            PROPERTY_TEMPERATURE_RETURN: 333.15,
            PROPERTY_SET_PRESSURE: False,
        }

        # Act
        mass_flow = heat_demand_and_temperature_to_mass_flow(
            temperature_supply=setpoints[PROPERTY_TEMPERATURE_SUPPLY],
            temperature_return=setpoints[PROPERTY_TEMPERATURE_RETURN],
            thermal_demand=setpoints[PROPERTY_HEAT_DEMAND],
        )

        with self.assertRaises(ValueError) as cm:
            self.production_cluster.set_setpoints(setpoints=setpoints)

        # Assert
        self.assertIsInstance(cm.exception, ValueError)
        self.assertEqual(
            cm.exception.args[0],
            f"The mass flow rate {mass_flow} of the asset {self.production_cluster.name}"
            + " is negative.",
        )

    def test_production_cluster_set_setpoints_pressure_or_mass_flow_control(self) -> None:
        """Test setting pressure setpoint of a production cluster."""
        # Arrange
        setpoints = {
            PROPERTY_HEAT_DEMAND: 1e6,
            PROPERTY_TEMPERATURE_SUPPLY: 353.15,
            PROPERTY_TEMPERATURE_RETURN: 333.15,
            PROPERTY_SET_PRESSURE: True,
        }

        # Act
        self.production_cluster.set_setpoints(setpoints=setpoints)

        # Assert
        self.assertNotEqual(
            self.production_cluster.control_mass_flow, setpoints[PROPERTY_SET_PRESSURE]
        )
        self.assertNotEqual(
            self.production_cluster.solver_asset.pre_scribe_mass_flow,  # type: ignore
            setpoints[PROPERTY_SET_PRESSURE],
        )

    def test_production_cluster_set_pressure_supply(self) -> None:
        """Test setting pressure of a production cluster."""
        # Arrange
        pressure_supply = 2e5  # [Pa]

        # Act
        self.production_cluster.set_pressure_supply(pressure_supply=pressure_supply)

        # Assert
        self.assertEqual(self.production_cluster.pressure_supply, pressure_supply)
        self.assertEqual(
            self.production_cluster.solver_asset.set_pressure, pressure_supply  # type: ignore
        )

    def test_production_cluster_set_pressure_supply_negative(self) -> None:
        """Test raise ValueError with negative pressure."""
        # Arrange
        pressure_supply = -2e5  # [Pa]

        # Act
        with self.assertRaises(ValueError) as cm:
            self.production_cluster.set_pressure_supply(pressure_supply=pressure_supply)

        # Assert
        self.assertIsInstance(cm.exception, ValueError)
        self.assertEqual(
            cm.exception.args[0],
            f"The pressure {pressure_supply} of the asset {self.production_cluster.name}"
            + " can not be negative.",
        )

    def test_production_cluster_write_to_output(self) -> None:
        """Test writing the output of a production cluster."""
        # Arrange
        with (
            patch.object(
                self.production_cluster.solver_asset, "get_mass_flow_rate"
            ) as get_mass_flow_rate,
            patch.object(self.production_cluster.solver_asset, "get_pressure") as get_pressure,
            patch.object(
                self.production_cluster.solver_asset, "get_temperature"
            ) as get_temperature,
            patch.object(self.production_cluster, "get_volume_flow_rate") as get_volume_flow_rate,
        ):
            get_mass_flow_rate.return_value = 1e6
            get_pressure.return_value = 2e5
            get_temperature.return_value = 333.15
            get_volume_flow_rate.return_value = 100.0

            # Act
            self.production_cluster.write_standard_output()

        # Assert
        self.assertEqual(
            len(self.production_cluster.outputs), len(self.production_cluster.connected_ports)
        )
        self.assertEqual(len(self.production_cluster.outputs[0]), 1)
        self.assertEqual(
            self.production_cluster.outputs[0][0],
            {
                PROPERTY_TEMPERATURE: 333.15,
                PROPERTY_MASSFLOW: 1e6,
                PROPERTY_PRESSURE: 2e5,
                PROPERTY_VOLUMEFLOW: 100.0,
            },
        )

    def test_get_volume_flow_rate(self):
        """Test getting the volume flow rate of a production cluster."""
        # Arrange
        with (
            patch.object(
                self.production_cluster.solver_asset,
                "get_mass_flow_rate",
            ) as get_mass_flow_rate,
            patch.object(
                fluid_props,
                "get_density",
            ) as get_density,
        ):
            get_mass_flow_rate.return_value = 1000.0
            get_density.return_value = 1000.0

            # Act
            volume_flow_rate = self.production_cluster.get_volume_flow_rate(i=0)
            # Assert
            self.assertEqual(volume_flow_rate, 1.0)

    def test_get_actual_heat_supplied(self):
        """Test getting the actual heat supplied by a production cluster."""  # noqa: D202

        # Arrange
        def get_internal_energy(_, i: int):
            if i == 0:
                return 1.0e6
            if i == 1:
                return 2.0e6

        def get_mass_flow_rate(_, i: int):
            return 0.5

        with (
            patch(
                "omotes_simulator_core.solver.network.assets.base_asset."
                "BaseAsset.get_internal_energy",
                get_internal_energy,
            ),
            patch(
                "omotes_simulator_core.solver.network.assets.base_asset."
                "BaseAsset.get_mass_flow_rate",
                get_mass_flow_rate,
            ),
        ):
            # Act
            actual_heat_supplied = self.production_cluster.get_actual_heat_supplied()
            # Assert
            self.assertEqual(actual_heat_supplied, 0.5 * 1e6)
