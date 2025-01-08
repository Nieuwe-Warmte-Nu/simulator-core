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

"""demandCluster class."""
from omotes_simulator_core.entities.assets.asset_abstract import AssetAbstract
from omotes_simulator_core.entities.assets.asset_defaults import (
    DEFAULT_DIAMETER,
    DEFAULT_POWER,
    DEFAULT_PRESSURE,
    DEFAULT_TEMPERATURE,
    DEFAULT_TEMPERATURE_DIFFERENCE,
    PROPERTY_TEMPERATURE_RETURN,
    PROPERTY_TEMPERATURE_SUPPLY,
    PROPERTY_HEAT_DEMAND,
    PROPERTY_HEAT_DEMAND_SET_POINT,
)
from omotes_simulator_core.entities.assets.esdl_asset_object import EsdlAssetObject
from omotes_simulator_core.entities.assets.utils import (
    heat_demand_and_temperature_to_mass_flow,
)
from omotes_simulator_core.solver.network.assets.production_asset import ProductionAsset


class DemandCluster(AssetAbstract):
    """A DemandCluster represents an asset that consumes heat."""

    def __init__(self, asset_name: str, asset_id: str, port_ids: list[str]):
        """Initialize a DemandCluster object.

        :param str asset_name: The name of the asset.
        :param str asset_id: The unique identifier of the asset.
        :param List[str] port_ids: List of ids of the connected ports.
        """
        super().__init__(asset_name=asset_name, asset_id=asset_id, connected_ports=port_ids)

        self._internal_diameter = DEFAULT_DIAMETER
        self.temperature_supply = DEFAULT_TEMPERATURE
        self.temperature_return: float = DEFAULT_TEMPERATURE - DEFAULT_TEMPERATURE_DIFFERENCE
        self.temperature_return_target = self.temperature_return
        self.pressure_input = DEFAULT_PRESSURE
        self.thermal_power_allocation = DEFAULT_POWER
        self.mass_flowrate = 0.0
        self.solver_asset = ProductionAsset(name=self.name, _id=self.asset_id)
        self.output: list = []

    def set_setpoints(self, setpoints: dict) -> None:
        """Placeholder to set the setpoints of an asset prior to a simulation.

        :param Dict setpoints: The setpoints that should be set for the asset.
            The keys of the dictionary are the names of the setpoints and the values are the values
        """
        # Default keys required
        necessary_setpoints = {
            PROPERTY_TEMPERATURE_SUPPLY,
            PROPERTY_TEMPERATURE_RETURN,
            PROPERTY_HEAT_DEMAND,
        }
        # Dict to set
        setpoints_set = set(setpoints.keys())
        # Check if all setpoints are in the setpoints
        if not necessary_setpoints.issubset(setpoints_set):
            # Print missing setpoints
            raise ValueError(
                f"The setpoints {necessary_setpoints.difference(setpoints_set)} are missing."
            )
        self.thermal_power_allocation = -setpoints[PROPERTY_HEAT_DEMAND]
        self.temperature_return_target = setpoints[PROPERTY_TEMPERATURE_RETURN]
        self.temperature_supply = setpoints[PROPERTY_TEMPERATURE_SUPPLY]
        adjusted_mass_flowrate = heat_demand_and_temperature_to_mass_flow(
            self.thermal_power_allocation, self.temperature_supply, self.temperature_return_target
        )
        self.solver_asset.supply_temperature = self.temperature_supply
        self.solver_asset.mass_flow_rate_set_point = adjusted_mass_flowrate  # type: ignore

    def add_physical_data(self, esdl_asset: EsdlAssetObject) -> None:
        """Method to add physical data to the asset.

        :param EsdlAssetObject esdl_asset: The esdl asset object to add the physical data from.
         :return:
        """

    def write_to_output(self) -> None:
        """Method to write time step results to the output dict.

        The output list is a list of dictionaries, where each dictionary
        represents the output of the asset for a specific timestep.
        """
        output_dict_temp = {
            PROPERTY_HEAT_DEMAND_SET_POINT: -self.thermal_power_allocation,
            PROPERTY_HEAT_DEMAND: self.get_actual_heat_supplied(),
        }
        self.outputs[1][-1].update(output_dict_temp)

    def get_actual_heat_supplied(self) -> float:
        """Get the actual heat supplied by the asset.

        :return float: The actual heat supplied by the asset [W].
        """
        return (
            self.solver_asset.get_internal_energy(1) - self.solver_asset.get_internal_energy(0)
        ) * self.solver_asset.get_mass_flow_rate(0)
