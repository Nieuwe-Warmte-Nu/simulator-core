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

"""ProductionCluster class."""
from typing import Dict
from warnings import warn

import numpy as np
from pandapipes import pandapipesNet
from pandas import DataFrame

from simulator_core.entities.assets.asset_abstract import AssetAbstract
from simulator_core.entities.assets.asset_defaults import (
    DEFAULT_DIAMETER,
    DEFAULT_NODE_HEIGHT,
    DEFAULT_PRESSURE,
    DEFAULT_TEMPERATURE_DIFFERENCE,
    PROPERTY_HEAT_DEMAND,
    PROPERTY_MASSFLOW,
    PROPERTY_PRESSURE_RETURN,
    PROPERTY_PRESSURE_SUPPLY,
    PROPERTY_TEMPERATURE_RETURN,
    PROPERTY_TEMPERATURE_SUPPLY,
)
from simulator_core.entities.assets.junction import Junction
from simulator_core.entities.assets.pump import CirculationPumpConstantMass
from simulator_core.entities.assets.utils import (
    heat_demand_and_temperature_to_mass_flow,
    mass_flow_and_temperature_to_heat_demand,
)
from simulator_core.entities.assets.valve import ControlValve


class ProductionCluster(AssetAbstract):
    """A ProductionCluster represents an asset that produces heat."""

    def __init__(
        self,
        pandapipes_net: pandapipesNet,
        asset_name: str,
        asset_id: str,
        from_junction: Junction,
        to_junction: Junction,
        thermal_production_required: float,
        temperature_supply: float,
        temperature_return: float = np.NaN,
        height_m: float = DEFAULT_NODE_HEIGHT,
        internal_diameter: float = DEFAULT_DIAMETER,
        pressure_supply: float = DEFAULT_PRESSURE,
        control_mass_flow: bool = False,
    ):
        """Initialize a ProductionCluster object.

        :param pandapipesNet pandapipes_net: The pandapipes network in which the
            asset is created.
        :param str asset_name: The name of the asset.
        :param str asset_id: The unique identifier of the asset.
        :param Junction from_junction: The junction where the asset starts.
        :param Junction to_junction: The junction where the asset ends.
        :param float thermal_production_required: The thermal allocation of the asset.
            The thermal allocation should be supplied in Watts.
        :param float temperature_supply: The temperature that the asset
            delivers to the "to_junction". The temperature should be
            supplied in Kelvin.
        :param float temeprature_return: The temperature that the asset
            receives from the "from_junction". The temperature should be
            supplied in Kelvin. If the value is not supplied it defaults to
            "temperature_supply" - DEFAULT_TEMPERATURE_DIFFERENCE.
        :param float height_m: The height of the junctions. The height should
            be supplied in meters, it defaults to DEFAULT_NODE_HEIGHT.
        :param float internal_diameter: The internal diameter of the pipe.
            The internal diameter should be supplied in meters, it defaults to
            DEFAULT_DIAMETER.
        :param float pressure_supply: The pressure that the asset delivers
            to the "to_junction". The pressure should be supplied in bar, it
            defaults to DEFAULT_PRESSURE.
        :param bool control_mass_flow: If True, the mass flow rate of the asset
            is controlled by the "Control Valve". If False, the mass flow rate
            of the asset is floating.
        """
        # Define the pandapipes network
        self.pandapipes_net = pandapipes_net
        # Define the asset properties
        self.asset_name = asset_name
        self.asset_id = asset_id
        # TODO: Do we need to carry the junction ids?
        self.from_junction = from_junction
        self.to_junction = to_junction
        self.internal_diameter = internal_diameter
        self.height_m = height_m
        # DemandCluster thermal and mass flow specifications
        self.thermal_production_required = thermal_production_required
        self.temperature_supply = temperature_supply
        self.temperature_return = (
            temperature_supply - DEFAULT_TEMPERATURE_DIFFERENCE
            if np.isnan(temperature_return)
            else temperature_return
        )
        # DemandCluster pressure specifications
        self.pressure_supply = pressure_supply
        self.control_mass_flow = control_mass_flow
        self._controlled_mass_flow = heat_demand_and_temperature_to_mass_flow(
            thermal_demand=self.thermal_production_required,
            temperature_supply=self.temperature_supply,
            temperature_return=self.temperature_return,
            pandapipes_net=self.pandapipes_net,
        )
        # Objects of the asset
        self._initialized = False
        self._create()

        # Output list
        self.output = []

    def _create(self) -> None:
        """Create a representation of the asset in pandapipes.

        The ProductionCluster asset contains multiple pandapipes components.

        The component model contains the following components:
        - A flow control valve to set the mass flow rate of the system.
        - A circulation pump to set the pressure and the temperature of the
        system.
        - An intermediate junction to link both components.
        """
        if not self._initialized:
            self._initialized = True
            # Create intermediate junction
            self._intermediate_junction = Junction(
                pandapipes_net=self.pandapipes_net,
                pn_bar=self.pressure_supply,
                tfluid_k=self.temperature_supply,
                height_m=self.height_m,
                name=f"intermediate_junction_{self.asset_name}",
            )
            # Create the pump to supply pressure and or massflow
            self._circ_pump = CirculationPumpConstantMass(
                pandapipes_net=self.pandapipes_net,
                from_junction=self.from_junction,
                to_junction=self._intermediate_junction,
                p_to_junction=self.pressure_supply,
                mdot_kg_per_s=self._controlled_mass_flow,
                t_to_junction=self.temperature_supply,
                name=f"circ_pump_{self.asset_name}",
                in_service=True,
            )
            # Create the control valve
            self._flow_control = ControlValve(
                pandapipes_net=self.pandapipes_net,
                from_junction=self._intermediate_junction,
                to_junction=self.to_junction,
                controlled_mdot_kg_per_s=self._controlled_mass_flow,
                diameter_m=self.internal_diameter,
                control_active=self.control_mass_flow,
                in_service=True,
                name=f"flow_control_{self.asset_name}",
            )

    def _set_supply_temperature(self, temperature_supply: float) -> None:
        """Set the supply temperature of the asset.

        :param float temperature_supply: The supply temperature of the asset.
            The temperature should be supplied in Kelvin.
        """
        # Set the temperature of the circulation pump mass flow
        self.temperature_supply = temperature_supply
        # Retrieve the value array of the temperature
        self.pandapipes_net["circ_pump_mass"]["t_flow_k"][
            self._circ_pump.index
        ] = self.temperature_supply

    def _set_return_temperature(self, temperature_return: float) -> None:
        """Set the return temperature of the asset.

        :param float temperature_return: The return temperature of the asset.
            The temperature should be supplied in Kelvin.
        """
        # Set the return temperature of the asset
        self.temperature_return = temperature_return

    def _set_heat_demand(self, heat_demand: float) -> None:
        """Set the heat demand of the asset.

        :param float heat_demand: The heat demand of the asset.
            The heat demand should be supplied in Watts.
        """
        # Calculate the mass flow rate
        self._controlled_mass_flow = heat_demand_and_temperature_to_mass_flow(
            thermal_demand=heat_demand,
            temperature_supply=self.temperature_supply,
            temperature_return=self.temperature_return,
            pandapipes_net=self.pandapipes_net,
        )
        # Check if the mass flow rate is positive
        if self._controlled_mass_flow < 0:
            raise ValueError(
                f"The mass flow rate {self._controlled_mass_flow} of the asset {self.asset_name}"
                + " is negative."
            )
        else:
            # Set the mass flow rate of the circulation pump
            self.pandapipes_net["circ_pump_mass"]["mdot_flow_kg_per_s"][
                self._circ_pump.index
            ] = self._controlled_mass_flow
            # Set the mass flow rate of the control valve
            self.pandapipes_net["flow_control"]["controlled_mdot_kg_per_s"][
                self._flow_control.index
            ] = self._controlled_mass_flow

    def set_setpoints(self, setpoints: Dict) -> None:
        """Set the setpoints of the asset.

        :param Dict setpoints: The setpoints of the asset in a dictionary,
            as "property_name": value pairs.

        """
        # Default keys required
        necessary_setpoints = set(
            [PROPERTY_TEMPERATURE_SUPPLY, PROPERTY_TEMPERATURE_RETURN, PROPERTY_HEAT_DEMAND]
        )
        # Dict to set
        setpoints_set = set(setpoints.keys())
        # Check if all setpoints are in the setpoints
        if necessary_setpoints.issubset(setpoints_set):
            # Set the setpoints
            self._set_supply_temperature(setpoints[PROPERTY_TEMPERATURE_SUPPLY])
            self._set_return_temperature(setpoints[PROPERTY_TEMPERATURE_RETURN])
            self._set_heat_demand(setpoints[PROPERTY_HEAT_DEMAND])
            # Raise warning if there are more setpoints
            if len(setpoints_set.difference(necessary_setpoints)) > 0:
                warn(
                    f"The setpoints {setpoints_set.difference(necessary_setpoints)}"
                    + f" are not required for the asset {self.asset_name}."
                )
        else:
            # Print missing setpoints
            raise ValueError(
                f"The setpoints {necessary_setpoints.difference(setpoints_set)} are missing."
            )

    def simulation_performed(self) -> bool:
        """Check if the simulation has been performed.

        :return bool simulation_performed: True if the simulation has been performed,
            False otherwise.
        """
        if self.pandapipes_net.res_circ_pump_mass is AttributeError:
            # TODO: Implement specific error
            return False
        else:
            # Retrieve the setpoints
            return True

    def get_setpoints(self) -> Dict:
        """Get the setpoints of the asset.

        :return Dict setpoints: The setpoints of the asset in a dictionary,
            as "property_name": value pairs.
        """
        # Return the setpoints
        if self.simulation_performed():
            temp_supply = self.pandapipes_net.res_junction["t_k"][self.to_junction.index]
            temp_return = self.pandapipes_net.res_junction["t_k"][self.from_junction.index]
            mass_flow = self.pandapipes_net.res_circ_pump_mass["mdot_flow_kg_per_s"][
                self._circ_pump.index
            ]
            heat_demand = mass_flow_and_temperature_to_heat_demand(
                temperature_supply=temp_supply,
                temperature_return=temp_return,
                mass_flow=mass_flow,
                pandapipes_net=self.pandapipes_net,
            )
            return {
                PROPERTY_TEMPERATURE_SUPPLY: temp_supply,
                PROPERTY_TEMPERATURE_RETURN: temp_return,
                PROPERTY_HEAT_DEMAND: heat_demand,
            }
        else:
            raise ValueError("Simulation data not available.")

    def update(self) -> None:
        """Update the asset properties to the results from the previous (timestep) simulation.

        Sets the values of the supply temperature, return temperature and heat demand
        to the values of the previous simulation. In addition, the mass flow rate is set
        to the value of the previous simulation.
        """
        if self.simulation_performed():
            # Retrieve the setpoints (Ts, Tr, Qh)
            setpoints = self.get_setpoints()
            # Set the setpoints (Ts, Tr, Qh)
            self.set_setpoints(setpoints)
            # Set massflow
            self._controlled_mass_flow = self.pandapipes_net.res_circ_pump_mass[
                "mdot_flow_kg_per_s"
            ][self._circ_pump.index]
        else:
            raise ValueError("Simulation data not available.")

    def write_to_output(self) -> None:
        """Write the output of the asset to the output list.

        The output list is a list of dictionaries, where each dictionary
        represents the output of its asset for a specific timestep.

        The output of the asset is a dictionary with the following keys:
        - PROPERTY_HEAT_DEMAND: The heat demand of the asset.
        - PROPERTY_TEMPERATURE_SUPPLY: The supply temperature of the asset.
        - PROPERTY_TEMPERATURE_RETURN: The return temperature of the asset.
        - PROPERTY_PRESSURE_SUPPLY: The supply pressure of the asset.
        - PROPERTY_PRESSURE_RETURN: The return pressure of the asset.
        - PROPERTY_MASSFLOW: The mass flow rate of the asset.
        """
        # Retrieve the general model setpoints (Ts, Tr, Qh)
        setpoints = self.get_setpoints()
        # Retrieve the mass flow (mdot)
        setpoints[PROPERTY_MASSFLOW] = self.pandapipes_net.res_circ_pump_mass["mdot_flow_kg_per_s"][
            self._circ_pump.index
        ]
        # Retrieve the pressure (Ps, Pr)
        setpoints[PROPERTY_PRESSURE_SUPPLY] = self.pandapipes_net.res_junction["p_bar"][
            self.to_junction.index
        ]
        setpoints[PROPERTY_PRESSURE_RETURN] = self.pandapipes_net.res_junction["p_bar"][
            self.from_junction.index
        ]
        # Append dict to output list
        self.output.append(setpoints)

    def get_timeseries(self) -> DataFrame:
        """Get timeseries as a dataframe from a pandapipes asset.

        The header is a tuple of the asset id and the property name.
        """
        # Create dataframe
        temp_dataframe = DataFrame(self.output)
        # Set header
        temp_dataframe.columns = [
            (self.asset_id, column_name) for column_name in temp_dataframe.columns
        ]
        return temp_dataframe
