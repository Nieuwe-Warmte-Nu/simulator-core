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

"""atesCluster class."""
from typing import Dict

from omotes_simulator_core.entities.assets.asset_abstract import AssetAbstract
from omotes_simulator_core.entities.assets.asset_defaults import (
    DEFAULT_TEMPERATURE,
    DEFAULT_TEMPERATURE_DIFFERENCE,
    PROPERTY_HEAT_DEMAND,
    PROPERTY_MASSFLOW,
    PROPERTY_PRESSURE_RETURN,
    PROPERTY_PRESSURE_SUPPLY,
    PROPERTY_TEMPERATURE_RETURN,
    PROPERTY_TEMPERATURE_SUPPLY,
    PROPERTY_FILL_LEVEL,
    PROPERTY_VOLUME
)

from omotes_simulator_core.entities.assets.esdl_asset_object import EsdlAssetObject
from omotes_simulator_core.solver.network.assets.production_asset import ProductionAsset
from omotes_simulator_core.entities.assets.utils import (
    heat_demand_and_temperature_to_mass_flow,
)
from omotes_simulator_core.solver.utils.fluid_properties import fluid_props


class HeatBuffer(AssetAbstract):
    """A HeatBuffer represents an asset that stores heat. Thus, it has the possibility to supply \
    heat or consume heat for storage."""

    temperature_supply: float
    """The supply temperature of the asset [K]."""

    temperature_return: float
    """The return temperature of the asset [K]."""

    thermal_power_allocation: float
    """The thermal for injection (positive) or production (negative) by the asset [W]."""

    mass_flowrate: float
    """The flow rate going in or out by the asset [kg/s]."""

    maximum_volume: float
    """The maximum volume of the heat storage [m3]."""

    fill_level: float
    """The current fill level of the heat storage [fraction 0-1]."""

    current_volume: float
    """The current volume of the heat storage [m3]."""

    timestep: float
    """The timestep of the heat storage to calculate volume during injection \
    and production [seconds]."""

    def __init__(
        self,
        asset_name: str,
        asset_id: str,
        port_ids: list[str],
        maximum_volume: float,
        fill_level: float,
    ) -> None:
        """Initialize a HeatBuffer object.

        :param str asset_name: The name of the asset.
        :param str asset_id: The unique identifier of the asset.
        """
        super().__init__(asset_name=asset_name, asset_id=asset_id, connected_ports=port_ids)
        self.temperature_supply = DEFAULT_TEMPERATURE
        self.temperature_return = DEFAULT_TEMPERATURE - DEFAULT_TEMPERATURE_DIFFERENCE
        self.thermal_power_allocation = 0
        self.mass_flowrate = 0
        self.maximum_volume = maximum_volume
        self.fill_level = fill_level
        self.current_volume = fill_level * maximum_volume
        self.timestep = 3600
        self.solver_asset = ProductionAsset(name=self.name, _id=self.asset_id)
        # using ProductionAsset since heat buffer acts either as producer or consumer,
        # positive flow is discharge and negative flow is charge
        self.output: list = []

    def set_setpoints(self, setpoints: Dict) -> None:
        """Placeholder to set the setpoints of an asset prior to a simulation.

        :param Dict setpoints: The setpoints that should be set for the asset.
        The keys of the dictionary are the names of the setpoints and the values are the values
        """
        # Default keys required
        necessary_setpoints = {
            PROPERTY_HEAT_DEMAND,
        }
        # Dict to set
        setpoints_set = set(setpoints.keys())
        # Check if all setpoints are in the setpoints
        if necessary_setpoints.issubset(setpoints_set):
            self.thermal_power_allocation = setpoints[PROPERTY_HEAT_DEMAND]

            self._calculate_massflowrate()
            self._calculate_fill_level_and_volume()
            self._set_solver_asset_setpoint()
        else:
            # Print missing setpoints
            raise ValueError(
                f"The setpoints {necessary_setpoints.difference(setpoints_set)} are missing."
            )

    def _calculate_massflowrate(self) -> None:
        """Calculate mass flowrate of the asset."""
        self.mass_flowrate = heat_demand_and_temperature_to_mass_flow(
            self.thermal_power_allocation, self.temperature_supply, self.temperature_return
        )

    def _calculate_fill_level_and_volume(self) -> None:
        """Calculate fill level of the storage."""
        density = fluid_props.get_density(self.temperature_supply)
        original_fill_level = self.fill_level
        new_fill_level = (self.mass_flowrate / density * self.timestep + original_fill_level
                          * self.maximum_volume) / self.maximum_volume
        if new_fill_level >= 0 and new_fill_level <= 1:
            self.fill_level = new_fill_level
            self.current_volume = new_fill_level * self.maximum_volume
        else:
            raise ValueError(
                f"The new fill level is {new_fill_level}. It should be between 0 and 1."
            )

    def _set_solver_asset_setpoint(self) -> None:
        """Set the setpoint of solver asset."""
        if self.mass_flowrate > 0:
            self.solver_asset.supply_temperature = self.temperature_return
        else:
            self.solver_asset.supply_temperature = self.temperature_supply
        self.solver_asset.mass_flow_rate_set_point = self.mass_flowrate  # type: ignore

    def add_physical_data(self, esdl_asset: EsdlAssetObject) -> None:
        """Method to add physical data to the asset.

        :param EsdlAssetObject esdl_asset: The esdl asset object to add the physical data from.
         :return:
        """

    def write_to_output(self) -> None:
        """Placeholder to write the asset to the output.

        The output list is a list of dictionaries, where each dictionary
        represents the output of its asset for a specific timestep.
        """
        output_dict = {
            PROPERTY_MASSFLOW: self.solver_asset.get_mass_flow_rate(1),
            PROPERTY_PRESSURE_SUPPLY: self.solver_asset.get_pressure(0),
            PROPERTY_PRESSURE_RETURN: self.solver_asset.get_pressure(1),
            PROPERTY_TEMPERATURE_SUPPLY: self.solver_asset.get_temperature(0),
            PROPERTY_TEMPERATURE_RETURN: self.solver_asset.get_temperature(1),
            PROPERTY_FILL_LEVEL: self.fill_level,
            PROPERTY_VOLUME: self.current_volume,
        }
        self.output.append(output_dict)
