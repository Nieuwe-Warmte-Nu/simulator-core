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
"""Module containing pipe class."""
from omotes_simulator_core.entities.assets.asset_abstract import AssetAbstract
from omotes_simulator_core.entities.assets.esdl_asset_object import EsdlAssetObject
from omotes_simulator_core.solver.network.assets.solver_pipe import SolverPipe
from omotes_simulator_core.entities.assets.asset_defaults import (
    PROPERTY_VELOCITY,
    PROPERTY_PRESSURE_LOSS,
    PROPERTY_PRESSURE_LOSS_PER_LENGTH,
    PROPERTY_HEAT_LOSS,
)


class Pipe(AssetAbstract):
    """A class representing a pipe in a heat network."""

    output: list[dict[str, float]]
    """The output list of the pipe with a dictionaries for each timestep."""

    length: float
    """The length of the pipe [m]."""

    diameter: float
    """The inner diameter of the pipe [m]."""

    roughness: float
    """The wall roughness of the pipe [m]."""

    alpha_value: float
    """The alpha value of the pipe [W/(m2 K)]."""

    minor_loss_coefficient: float
    """The minor loss coefficient of the pipe [-]."""

    external_temperature: float
    """The external temperature surrounding the pipe [K]."""

    qheat_external: float
    """The external heat flow into the pipe [W]."""

    name: str
    """The name of the pipe."""

    def __init__(
        self,
        asset_name: str,
        asset_id: str,
        port_ids: list[str],
        length: float,
        inner_diameter: float,
        roughness: float,
        alpha_value: float,
        minor_loss_coefficient: float,
        external_temperature: float,
        qheat_external: float,
    ):
        """Initialize a Pipe object.

        :param str asset_name: The name of the asset.
        :param str asset_id: The unique identifier of the asset.
        :param List[str] port_ids: List of ids of the connected ports.
        :param float length: The length of the pipe [m].
        :param float inner_diameter: The inner diameter of the pipe [m].
        :param float minor_loss_coefficient: The minor loss coefficient of the pipe [-].
        :param float external_temperature: The external temperature surrounding the pipe [K].
        :param float qheat_external: The external heat flow into the pipe [W].
        :param float roughness: The wall roughness of the pipe [m].
        :param float alpha_value: The alpha value of the pipe [W/(m2 K)].
        """
        super().__init__(asset_name=asset_name, asset_id=asset_id, connected_ports=port_ids)
        # Initialize the default values of the pipe
        self.minor_loss_coefficient = minor_loss_coefficient
        self.external_temperature = external_temperature
        self.qheat_external = qheat_external
        # Define properties of the pipe
        self.length = length
        self.inner_diameter = inner_diameter
        self.roughness = roughness
        self.alpha_value = alpha_value
        self.solver_asset: SolverPipe = SolverPipe(
            name=self.name,
            _id=self.asset_id,
            length=self.length,
            diameter=self.inner_diameter,
            roughness=self.roughness,
        )

    def add_physical_data(self, esdl_asset: EsdlAssetObject) -> None:
        """Method to add physical data to the asset."""

    def set_setpoints(self, setpoints: dict) -> None:
        """Set the setpoints of the pipe prior to a simulation.

        :param Dict setpoints: The setpoints that should be set for the pipe.
            The keys of the dictionary are the names of the setpoints and the values are the values
        """

    def write_to_output(self) -> None:
        """Method to write time step results to the output dict.

        The output list is a list of dictionaries, where each dictionary
        represents the output of the asset for a specific timestep.
        """
        for i in range(len(self.connected_ports)):
            output_dict_temp = {PROPERTY_VELOCITY: self.get_velocity(i)}
            self.outputs[i][-1].update(output_dict_temp)

        # only for the second connection point these properties are added
        self.outputs[1][-1].update(
            {
                PROPERTY_PRESSURE_LOSS: self.get_pressure_loss(),
                PROPERTY_PRESSURE_LOSS_PER_LENGTH: self.get_pressure_loss_per_length(),
                PROPERTY_HEAT_LOSS: self.get_heat_loss(),
            }
        )

    def get_velocity(self, port: int) -> float:
        """Get the velocity of the fluid in the pipe at the given connection point.

        :param int port: The port of the pipe for which to get the velocity.
        :return: The velocity of the fluid in the pipe [m/s].
        """
        return float(self.get_volume_flow_rate(port) / self.solver_asset.area)

    def get_pressure_loss(self) -> float:
        """Get the pressure loss of the pipe."""
        return self.solver_asset.get_pressure(1) - self.solver_asset.get_pressure(0)

    def get_pressure_loss_per_length(self) -> float:
        """Get the pressure loss of the pipe per length."""
        return self.get_pressure_loss() / self.length

    def get_heat_loss(self) -> float:
        """Get the heat loss of the pipe.

        The minus sign is added to make it a loss instead of supply.
        """
        return -self.solver_asset.heat_supplied
