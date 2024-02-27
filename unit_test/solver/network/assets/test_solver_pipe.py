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

"""Test Solver Pipe entities."""
import unittest
from unittest.mock import patch
from uuid import uuid4

import numpy as np

from simulator_core.entities.assets.asset_defaults import (
    PROPERTY_DIAMETER,
    PROPERTY_LENGTH,
    PROPERTY_ROUGHNESS,
)
from simulator_core.solver.matrix.core_enum import NUMBER_CORE_QUANTITIES, IndexEnum
from simulator_core.solver.network.assets.node import Node
from simulator_core.solver.network.assets.solver_pipe import SolverPipe
from simulator_core.solver.utils.fluid_properties import fluid_props


class SolverPipeTest(unittest.TestCase):
    """Testcase for SolverPipe class."""

    def setUp(self) -> None:
        """Set up the test case."""
        # Create a ProductionAsset object
        self.asset = SolverPipe(
            name=uuid4(),
        )
        # Create supply, connection_point:0 and return node, connection_point:1
        self.supply_node = Node(name=uuid4())
        self.return_node = Node(name=uuid4())
        # Connect the nodes to the asset
        self.asset.connect_node(node=self.supply_node, connection_point=0)
        self.asset.connect_node(node=self.return_node, connection_point=1)

    def test_set_physical_properties(self) -> None:
        """Test the set_physical_properties method."""
        # arrange
        physical_properties_dict = {
            PROPERTY_DIAMETER: 0.5,
            PROPERTY_LENGTH: 2000.0,
            PROPERTY_ROUGHNESS: 0.002,
        }

        # act
        self.asset.set_physical_properties(physical_properties=physical_properties_dict)  # act

        # assert
        self.assertEqual(self.asset.diameter, physical_properties_dict[PROPERTY_DIAMETER])
        self.assertEqual(self.asset.length, physical_properties_dict[PROPERTY_LENGTH])
        self.assertEqual(self.asset.roughness, physical_properties_dict[PROPERTY_ROUGHNESS])
        self.assertEqual(self.asset.area, 0.19634954084936207)

    def test_calculate_reynolds_number_laminar_low_temp(self) -> None:
        """Test the calculate_reynolds_number method for a laminar flow at low temperature."""
        # arrange
        fluid_temperature = 293.15
        input_reynolds_number = 100.0
        fluid_viscosity = fluid_props.get_viscosity(fluid_temperature)
        fluid_density = fluid_props.get_density(fluid_temperature)
        velocity = input_reynolds_number * fluid_viscosity / self.asset.diameter
        self.asset.prev_sol[IndexEnum.internal_energy] = fluid_props.get_ie(fluid_temperature)
        self.asset.prev_sol[IndexEnum.discharge] = velocity * self.asset.area * fluid_density

        # act
        calculated_reynolds_number = self.asset.calculate_reynolds_number()  # act

        # assert
        self.assertEqual(np.round(calculated_reynolds_number, 2), 100.00)

    def test_calculate_reynolds_number_turbulent_high_temp(self) -> None:
        """Test the calculate_reynolds_number method for a turbulent flow at higher temperature."""
        # arrange
        fluid_temperature = 400.0
        input_reynolds_number = 2500.0
        fluid_viscosity = fluid_props.get_viscosity(fluid_temperature)
        fluid_density = fluid_props.get_density(fluid_temperature)
        velocity = input_reynolds_number * fluid_viscosity / self.asset.diameter
        self.asset.prev_sol[IndexEnum.internal_energy] = fluid_props.get_ie(fluid_temperature)
        self.asset.prev_sol[IndexEnum.discharge] = velocity * self.asset.area * fluid_density

        # act
        calculated_reynolds_number = self.asset.calculate_reynolds_number()  # act

        # assert
        self.assertEqual(np.round(calculated_reynolds_number, 2), input_reynolds_number)

    @patch.object(SolverPipe, "calculate_reynolds_number", return_value=50.0)
    def test_calc_lambda_loss_laminar_smaller_than_100(self, mock_reynolds_number) -> None:
        """Test the calc_lambda_loss method for a Reynolds number below 100."""
        # arrange

        # act
        self.asset.calc_lambda_loss()  # act

        # assert
        self.assertEqual(self.asset.lambda_loss, 0.64)
        mock_reynolds_number.assert_called_once()

    @patch.object(SolverPipe, "calculate_reynolds_number", return_value=1990.0)
    def test_calc_lambda_loss_laminar_smaller_than_2000(self, mock_reynolds_number) -> None:
        """Test the calc_lambda_loss method for Reynolds number < 2000.0."""
        # arrange

        # act
        self.asset.calc_lambda_loss()  # act

        # assert
        self.assertEqual(self.asset.lambda_loss, 64.0 / 1990.0)
        mock_reynolds_number.assert_called_once()

    @patch.object(SolverPipe, "calculate_reynolds_number", return_value=37743.12811445107)
    def test_calc_lambda_loss_laminar_greater_than_4000(self, mock_reynolds_number) -> None:
        """Test the calc_lambda_loss method with a Reynolds number above 4000.0."""
        # arrange

        # act
        self.asset.calc_lambda_loss()  # act

        # assert
        self.assertEqual(np.round(self.asset.lambda_loss, 4), 0.0327)
        mock_reynolds_number.assert_called_once()

    @patch.object(SolverPipe, "calculate_reynolds_number", return_value=3500.0)
    def test_calc_lambda_loss_laminar_greater_than_2000_smaller_than_4000(
        self, mock_reynolds_number
    ) -> None:
        """Test the calc_lambda_loss method for 2000.0<Re<4000.0."""
        # arrange

        # act
        self.asset.calc_lambda_loss()  # act

        # assert
        self.assertEqual(np.round(self.asset.lambda_loss, 4), 0.0426)
        mock_reynolds_number.assert_called_once()

    def test_update_heat_supplied_high_velocity(self) -> None:
        """Test the update_heat_supplied method."""
        # arrange
        self.asset.prev_sol[IndexEnum.discharge] = 290.6  # kg/s
        self.asset.prev_sol[IndexEnum.internal_energy] = fluid_props.get_ie(
            56.8500061035156 + 273.15
        )
        self.asset.alpha_value = 0.1  # W/m2K
        self.asset.length = 3e5  # m
        self.asset._grid_size = 10  # pylint: disable=protected-access
        self.asset.diameter = 1.0  # m

        # act
        self.asset.update_heat_supplied()  # act

        # assert
        self.assertEqual(np.round(self.asset.heat_supplied * 1e-6, 1), -3.3)
        self.assertEqual(
            np.round(fluid_props.get_t(self.asset._internal_energy_grid[-1][0]) - 273.15, 2), 54.11
        )  # pylint: disable=protected-access

    def test_update_heat_supplied_negative_velocity(self) -> None:
        """Test the update_heat_supplied method."""
        # arrange
        self.asset.prev_sol[IndexEnum.discharge] = -2.906  # kg/s
        self.asset.prev_sol[IndexEnum.internal_energy + NUMBER_CORE_QUANTITIES] = (
            fluid_props.get_ie(56.8500061035156 + 273.15)
        )
        self.asset.alpha_value = 0.1  # W/m2K
        self.asset.length = 3e5  # m
        self.asset._grid_size = 10  # pylint: disable=protected-access
        self.asset.diameter = 1.0  # m

        # act
        self.asset.update_heat_supplied()  # act

        # assert
        self.assertEqual(np.round(self.asset.heat_supplied * 1e-3, 1), -446.3)
        self.assertEqual(
            np.round(fluid_props.get_t(self.asset._internal_energy_grid[0][0]) - 273.15, 2), 20.12
        )  # pylint: disable=protected-access

    def test_update_heat_supplied_positive_velocity(self) -> None:
        """Test the update_heat_supplied method."""
        # arrange
        self.asset.prev_sol[IndexEnum.discharge] = 2.906  # kg/s
        self.asset.prev_sol[IndexEnum.internal_energy] = fluid_props.get_ie(
            56.8500061035156 + 273.15
        )
        self.asset.alpha_value = 0.1  # W/m2K
        self.asset.length = 3e5  # m
        self.asset._grid_size = 10  # pylint: disable=protected-access
        self.asset.diameter = 1.0  # m

        # act
        self.asset.update_heat_supplied()  # act

        # assert
        self.assertEqual(np.round(self.asset.heat_supplied * 1e-3, 1), -446.3)
        self.assertEqual(
            np.round(fluid_props.get_t(self.asset._internal_energy_grid[-1][0]) - 273.15, 2), 20.12
        )  # pylint: disable=protected-access
