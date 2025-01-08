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

"""Abstract class for asset."""

from abc import ABC, abstractmethod
from pandas import DataFrame, concat

from omotes_simulator_core.entities.assets.esdl_asset_object import EsdlAssetObject
from omotes_simulator_core.solver.utils.fluid_properties import fluid_props
from omotes_simulator_core.solver.network.assets.base_asset import BaseAsset
from omotes_simulator_core.entities.assets.asset_defaults import (
    PROPERTY_MASSFLOW,
    PROPERTY_PRESSURE,
    PROPERTY_TEMPERATURE,
    PROPERTY_VOLUMEFLOW,
)


class AssetAbstract(ABC):
    """Abstract class for Asset."""

    name: str
    """The name of the asset."""

    asset_id: str
    """The unique identifier of the asset."""

    outputs: list[list[dict[str, float]]]
    """The output of the asset as a list with a dictionary per timestep."""

    connected_ports: list[str]
    """List of ids of the connected ports."""
    solver_asset: BaseAsset
    """The asset object use for the solver."""
    asset_type = "asset_abstract"
    """The type of the asset."""
    number_of_con_points: int = 2
    """The number of connection points of the asset."""

    def __init__(self, asset_name: str, asset_id: str, connected_ports: list[str]) -> None:
        """Basic constructor for asset objects.

        :param str asset_name: The name of the asset.
        :param str asset_id: The unique identifier of the asset.
        :param List[str] connected_ports: List of ids of the connected ports.
        """
        self.from_junction = None
        self.to_junction = None
        self.name = asset_name
        self.asset_id = asset_id
        self.connected_ports = connected_ports
        self.outputs = [[] for _ in range(len(self.connected_ports))]

    def __repr__(self) -> str:
        """Method to print string with the name of the asset."""
        return self.__class__.__name__ + " " + self.name

    @abstractmethod
    def set_setpoints(self, setpoints: dict) -> None:
        """Placeholder to set the setpoints of an asset prior to a simulation.

        :param Dict setpoints: The setpoints that should be set for the asset.
            The keys of the dictionary are the names of the setpoints and the values are the values
        """

    def get_setpoints(self) -> dict[str, float]:
        """Placeholder to get the setpoint attributes of an asset.

        :return Dict: The setpoints of the asset. The keys of the dictionary are the names of the
            setpoints and the values are the values.
        """
        return {}

    @abstractmethod
    def add_physical_data(self, esdl_asset: EsdlAssetObject) -> None:
        """Placeholder method to add physical data to an asset."""

    def write_standard_output(self) -> None:
        """Write the standard time step results of the asset to the output list.

        The output list is a list of list with dictionaries, where each dictionary
        represents the output of its asset for a specific timestep of a specific port.
        The basic properties mass flow rate, pressure and temperature are stored.
        All assets can add their own properties to the dictionary via the write_output method.
        """
        for i in range(len(self.connected_ports)):
            output_dict_temp = {
                PROPERTY_MASSFLOW: self.solver_asset.get_mass_flow_rate(i),
                PROPERTY_PRESSURE: self.solver_asset.get_pressure(i),
                PROPERTY_TEMPERATURE: self.solver_asset.get_temperature(i),
                PROPERTY_VOLUMEFLOW: self.get_volume_flow_rate(i),
            }
            self.outputs[i].append(output_dict_temp)

    def get_volume_flow_rate(self, i: int) -> float:
        """Calculates and returns the volume flow rate for the given port.

        The volumetric flow rate is calculated for the specified asset port based on fluid
        temperature/density and mass flow rate from last computed timestep

        :param int i: The index of the port.
        :return float: The volume flow rate.
        """
        rho = fluid_props.get_density(self.solver_asset.get_temperature(i))
        return self.solver_asset.get_mass_flow_rate(i) / rho

    @abstractmethod
    def write_to_output(self) -> None:
        """Placeholder to write time step results to the output dict.

        The output list is a list of dictionaries, where each dictionary
        represents the output of the asset for a specific timestep.
        """

    def get_timeseries(self) -> DataFrame:
        """Get timeseries as a dataframe from a asset.

        The header is a tuple of the port id and the property name.
        """
        # Create dataframe

        temp_data = DataFrame()
        for i in range(len(self.connected_ports)):
            temp_frame = DataFrame(self.outputs[i])
            temp_frame.columns = [
                (self.connected_ports[i], column_name) for column_name in temp_frame.columns
            ]
            temp_data = concat([temp_data, temp_frame], axis=1)
        return temp_data
