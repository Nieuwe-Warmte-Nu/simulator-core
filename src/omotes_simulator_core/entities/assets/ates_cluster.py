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
import os
import math

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
    PROPERTY_TIMESTEP
)
from omotes_simulator_core.entities.assets.asset_defaults import ATES_DEFAULTS

from omotes_simulator_core.entities.assets.esdl_asset_object import EsdlAssetObject
from omotes_simulator_core.entities.assets.pyjnius_loader import PyjniusLoader
from omotes_simulator_core.solver.network.assets.production_asset import ProductionAsset
from omotes_simulator_core.entities.assets.utils import (
    heat_demand_and_temperature_to_mass_flow,
)


class AtesCluster(AssetAbstract):
    """A AtesCluster represents an asset that consumes heat and produces heat."""

    temperature_supply: float
    """The supply temperature of the asset [K]."""

    temperature_return: float
    """The return temperature of the asset [K]."""

    thermal_power_allocation: float
    """The thermal for injection (positive) or production (negative) by the asset [W]."""

    mass_flowrate: float
    """The flow rate going in or out by the asset [kg/s]."""

    def __init__(self, asset_name: str, asset_id: str, port_ids: list[str]):
        """Initialize a AtesCluster object.

        :param str asset_name: The name of the asset.
        :param str asset_id: The unique identifier of the asset.
        """
        super().__init__(asset_name=asset_name, asset_id=asset_id, connected_ports=port_ids)

        self.temperature_supply = DEFAULT_TEMPERATURE
        self.temperature_return = DEFAULT_TEMPERATURE - DEFAULT_TEMPERATURE_DIFFERENCE
        self.thermal_power_allocation = 0  # Watt
        self.mass_flowrate = 0  # kg/s
        self.solver_asset = ProductionAsset(name=self.name, _id=self.asset_id)
        # ATES default properties
        self.aquifer_depth = ATES_DEFAULTS.aquifer_depth  # meters
        self.aquifer_thickness = ATES_DEFAULTS.aquifer_thickness  # meters
        self.aquifer_mid_temperature = ATES_DEFAULTS.aquifer_mid_temperature  # Celcius
        self.aquifer_net_to_gross = ATES_DEFAULTS.aquifer_net_to_gross  # percentage
        self.aquifer_porosity = ATES_DEFAULTS.aquifer_porosity  # percentage
        self.aquifer_permeability = ATES_DEFAULTS.aquifer_permeability  # mD
        self.aquifer_anisotropy = ATES_DEFAULTS.aquifer_anisotropy  # -
        self.salinity = ATES_DEFAULTS.salinity  # ppm
        self.well_casing_size = ATES_DEFAULTS.well_casing_size  # inch
        self.well_distance = ATES_DEFAULTS.well_distance  # meters
        self.maximum_flow_charge = ATES_DEFAULTS.maximum_flow_charge  # m3/h
        self.maximum_flow_discharge = ATES_DEFAULTS.maximum_flow_discharge  # m3/h
        self.rosim_timestep = 1

        # Output list
        self.output: list = []

        self.pyjnius_loader = PyjniusLoader.get_loader()

    def _calculate_massflowrate(self) -> None:
        """Calculate mass flowrate of the asset."""
        self.mass_flowrate = heat_demand_and_temperature_to_mass_flow(
            self.thermal_power_allocation, self.temperature_supply, self.temperature_return
        )

    def _set_solver_asset_setpoint(self) -> None:
        """Set the setpoint of solver asset."""
        if self.mass_flowrate > 0:
            self.solver_asset.supply_temperature = self.temperature_return
        else:
            self.solver_asset.supply_temperature = self.temperature_supply
        self.solver_asset.mass_flow_rate_set_point = self.mass_flowrate  # type: ignore

    def set_setpoints(self, setpoints: Dict) -> None:
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
        if necessary_setpoints.issubset(setpoints_set):
            self.thermal_power_allocation = setpoints[PROPERTY_HEAT_DEMAND]
            self.temperature_return = setpoints[PROPERTY_TEMPERATURE_RETURN]
            self.temperature_supply = setpoints[PROPERTY_TEMPERATURE_SUPPLY]
            self.rosim_timestep = setpoints[PROPERTY_TIMESTEP] / 3600  # convert to 1 hour

            self._calculate_massflowrate()
            self._run_rosim()
            self._set_solver_asset_setpoint()
        else:
            # Print missing setpoints
            raise ValueError(
                f"The setpoints {necessary_setpoints.difference(setpoints_set)} are missing."
            )

    def add_physical_data(self, esdl_asset: EsdlAssetObject) -> None:
        """Method to add physical data to the asset.

        :param EsdlAssetObject esdl_asset: The esdl asset object to add the physical data from.
         :return:
        """
        self.aquifer_depth, _ = esdl_asset.get_property(
            esdl_property_name="aquiferTopDepth", default_value=self.aquifer_depth
        )
        self.aquifer_thickness, _ = esdl_asset.get_property(
            esdl_property_name="aquiferThickness", default_value=self.aquifer_thickness
        )
        self.aquifer_mid_temperature, _ = esdl_asset.get_property(
            esdl_property_name="aquiferMidTemperature", default_value=self.aquifer_mid_temperature
        )
        self.aquifer_net_to_gross, _ = esdl_asset.get_property(
            esdl_property_name="aquiferNetToGross", default_value=self.aquifer_net_to_gross
        )
        self.aquifer_porosity, _ = esdl_asset.get_property(
            esdl_property_name="aquiferPorosity", default_value=self.aquifer_porosity
        )
        self.aquifer_permeability, _ = esdl_asset.get_property(
            esdl_property_name="aquiferPermeability", default_value=self.aquifer_permeability
        )
        self.aquifer_anisotropy, _ = esdl_asset.get_property(
            esdl_property_name="aquiferAnisotropy", default_value=self.aquifer_anisotropy
        )
        self.salinity, _ = esdl_asset.get_property(
            esdl_property_name="salinity", default_value=self.salinity
        )
        self.well_casing_size, _ = esdl_asset.get_property(
            esdl_property_name="wellCasingSize", default_value=self.well_casing_size
        )
        self.well_distance, _ = esdl_asset.get_property(
            esdl_property_name="wellDistance", default_value=self.well_distance
        )

        maximum_charge_power, _ = esdl_asset.get_property(
            esdl_property_name="maxChargeRate", default_value=12e7
        )

        self.maximum_flow_charge = heat_demand_and_temperature_to_mass_flow(
            maximum_charge_power, self.temperature_supply, self.temperature_return
        )

        maximum_discharge_power, _ = esdl_asset.get_property(
            esdl_property_name="maxChargeRate", default_value=12e7
        )

        self.maximum_flow_discharge = heat_demand_and_temperature_to_mass_flow(
            maximum_discharge_power, self.temperature_supply, self.temperature_return
        )

        self._init_rosim()

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
        }
        self.output.append(output_dict)

    def _init_rosim(self) -> None:
        """Function to initailized Rosim from XML file."""
        path = os.path.dirname(__file__)
        xmlfile = os.path.join(path, "bin/sequentialTemplate_v0.4.2_template.xml")
        with open(xmlfile, "r") as fd:
            xml_str = fd.read()

        # overwrite template value with ESDL properties for ROSIM input

        MODEL_TOP = self.aquifer_depth - 100
        AQUIFER_THICKNESS = self.aquifer_thickness
        NZ_AQUIFER = math.floor(AQUIFER_THICKNESS / 2)
        NZ = NZ_AQUIFER + 8
        AQUIFER_TOP = self.aquifer_depth
        AQUIFER_BASE = self.aquifer_depth + self.aquifer_thickness
        SURFACE_TEMPERATURE = self.aquifer_mid_temperature - 0.034 * (
            self.aquifer_depth + self.aquifer_thickness / 2
        )
        AQUIFER_NTG = self.aquifer_net_to_gross
        AQUIFER_PORO = self.aquifer_porosity
        AQUIFER_PERM_XY = self.aquifer_permeability
        AQUIFER_PERM_Z = AQUIFER_PERM_XY / self.aquifer_anisotropy
        SALINITY = self.salinity
        WELL2_X = self.well_distance + 300
        CASING_SIZE = self.well_casing_size

        xml_str = xml_str.replace("$NZ$", str(NZ))
        xml_str = xml_str.replace("$MODEL_TOP$", str(MODEL_TOP))
        xml_str = xml_str.replace("$TIME_STEP_UNIT$", str(2))
        xml_str = xml_str.replace("$WELL2_X$", str(WELL2_X))
        xml_str = xml_str.replace("$AQUIFER_TOP$", str(AQUIFER_TOP))
        xml_str = xml_str.replace("$AQUIFER_BASE$", str(AQUIFER_BASE))
        xml_str = xml_str.replace("$CASING_SIZE$", str(CASING_SIZE))
        xml_str = xml_str.replace("$SURFACE_TEMPERATURE$", str(SURFACE_TEMPERATURE))
        xml_str = xml_str.replace("$SALINITY$", str(SALINITY))
        xml_str = xml_str.replace("$NZ_AQUIFER$", str(NZ_AQUIFER))
        xml_str = xml_str.replace("$AQUIFER_THICKNESS$", str(AQUIFER_THICKNESS))
        xml_str = xml_str.replace("$AQUIFER_PORO$", str(AQUIFER_PORO))
        xml_str = xml_str.replace("$AQUIFER_NTG$", str(AQUIFER_NTG))
        xml_str = xml_str.replace("$AQUIFER_PERM_XY$", str(AQUIFER_PERM_XY))
        xml_str = xml_str.replace("$AQUIFER_PERM_Z$", str(AQUIFER_PERM_Z))

        temp_xmlfile_path = os.path.join(path, "bin/ates_sequential_temp.xml")
        with open(temp_xmlfile_path, "w") as temp_xmlfile:
            temp_xmlfile.write(xml_str)

        javaioFile = self.pyjnius_loader.load_class("java.io.File")
        RosimSequential = self.pyjnius_loader.load_class("tno.calc.RosimSequential")
        xmlfilejava = javaioFile(temp_xmlfile_path)
        self.rosim = RosimSequential(xmlfilejava, False, 2)

    def _run_rosim(self) -> None:
        """Function to calculate storage temperature after injection and production."""
        volume_flow = self.mass_flowrate * 3600 / 1027  # convert to second and hardcoded saline
        # density needs to change with PVT calculation
        timestep = self.rosim_timestep

        rosim_input__flow = [volume_flow, -1 * volume_flow]  # first elemnt is for producer well
        # and second element is for injection well, positive flow is going upward and negative flow
        # is downward

        if volume_flow > 0:
            rosim_input_temperature = [self.temperature_supply - 273.15, -1]  # Celcius, -1 in
            # injection well to make sure it is not used
        elif volume_flow < 0:
            rosim_input_temperature = [-1, self.temperature_return - 273.15]  # Celcius, -1 in
            # producer well to make sure it is not used
        else:
            rosim_input_temperature = [-1, -1]  # -1 in both producer and injection well to make
            # sure it is not used

        ates_temperature = self.rosim.getTempsNextTimeStep(
            rosim_input__flow, rosim_input_temperature, timestep
        )

        hot_well_temperature = ates_temperature[0] + 273.15  # convert to K
        cold_well_temperature = ates_temperature[1] + 273.15  # convert to K

        # update supply return temperature from ATES
        self.temperature_supply = hot_well_temperature
        self.temperature_return = cold_well_temperature
