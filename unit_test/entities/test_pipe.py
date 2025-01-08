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

"""Test Junction entities."""
import unittest
from unittest.mock import patch

from omotes_simulator_core.entities.assets.pipe import Pipe


class PipeTest(unittest.TestCase):
    """Testcase for HeatNetwork class."""

    def setUp(self) -> None:
        """Define the variables used in the tests."""
        self.length: float = 5
        self.inner_diameter: float = 1
        self.roughness: float = 0.001
        self.alpha_value: float = 0.8
        self.minor_loss_coefficient: float = 0.0
        self.external_temperature: float = 273.15 + 20.0
        self.qheat_external: float = 0.0
        self.pipe = Pipe(
            asset_name="pipe",
            asset_id="pipe_id",
            port_ids=["test1", "test2"],
            length=self.length,
            inner_diameter=self.inner_diameter,
            roughness=self.roughness,
            alpha_value=self.alpha_value,
            minor_loss_coefficient=self.minor_loss_coefficient,
            external_temperature=self.external_temperature,
            qheat_external=self.qheat_external,
        )

    def test_pipe_create(self) -> None:
        """Evaluate the creation of a pipe object."""
        # Arrange

        # Act
        pipe = Pipe(
            asset_name="pipe",
            asset_id="pipe_id",
            port_ids=["test1", "test2"],
            length=self.length,
            inner_diameter=self.inner_diameter,
            roughness=self.roughness,
            alpha_value=self.alpha_value,
            minor_loss_coefficient=self.minor_loss_coefficient,
            external_temperature=self.external_temperature,
            qheat_external=self.qheat_external,
        )

        # Assert
        self.assertIsInstance(pipe, Pipe)
        self.assertEqual(pipe.name, "pipe")
        self.assertEqual(pipe.asset_id, "pipe_id")
        self.assertEqual(pipe.length, self.length)
        self.assertEqual(pipe.inner_diameter, self.inner_diameter)
        self.assertEqual(pipe.roughness, self.roughness)
        self.assertEqual(pipe.alpha_value, self.alpha_value)
        self.assertEqual(pipe.minor_loss_coefficient, self.minor_loss_coefficient)
        self.assertEqual(pipe.external_temperature, self.external_temperature)
        self.assertEqual(pipe.qheat_external, self.qheat_external)

    def test_get_velocity(self):
        """Test the get_velocity method."""
        # arrange
        with (
            patch.object(
                self.pipe,
                "get_volume_flow_rate",
            ) as get_volume_flow_rate,
        ):
            get_volume_flow_rate.return_value = 10.0
            # act
            velocity = self.pipe.get_velocity(port=0)
        # assert
        self.assertAlmostEquals(velocity, 12.732, places=3)

    def test_get_pressure_loss(self):
        """Test the get_pressure_loss."""  # noqa: D202

        # arrange
        def get_pressure(_, i: int):
            if i == 0:
                return 1.0
            if i == 1:
                return 2.0

        with patch(
            "omotes_simulator_core.solver.network.assets.solver_pipe.SolverPipe.get_pressure",
            get_pressure,
        ):
            # act
            pressure_loss = self.pipe.get_pressure_loss()

        # assert
        self.assertEqual(pressure_loss, 1.0)

    def test_get_pressure_loss_per_length(self):
        """Test for the get_pressure_loss_per_length method."""  # noqa: D202

        # arrange
        def get_pressure(_, i: int):
            if i == 0:
                return 10.0
            if i == 1:
                return 20.0

        with patch(
            "omotes_simulator_core.solver.network.assets.solver_pipe.SolverPipe.get_pressure",
            get_pressure,
        ):
            # act
            pressure_loss = self.pipe.get_pressure_loss_per_length()

        # assert
        self.assertEqual(pressure_loss, 2.0)

    def test_get_heat_loss(self):
        """Test the get_heat_loss method."""
        # arrange
        self.pipe.solver_asset.heat_supplied = 1000.0

        # act
        heat_loss = self.pipe.get_heat_loss()

        # assert
        self.assertEqual(heat_loss, -1000.0)
