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

import unittest
import esdl
import uuid
import numpy as np
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock
import pandas as pd

from typing import Tuple

from omotes_simulator_core.adapter.transforms.mappers import (
    EsdlControllerMapper
)
from omotes_simulator_core.entities.esdl_object import EsdlObject
from omotes_simulator_core.entities.simulation_configuration import SimulationConfiguration
from omotes_simulator_core.infrastructure.simulation_manager import SimulationManager
from omotes_simulator_core.infrastructure.utils import pyesdl_from_file
from omotes_simulator_core.solver.utils.fluid_properties import fluid_props


class HeatDemandTest(unittest.TestCase):
    """Class to store the heat demand tests."""

    def setUp(self) -> None:
        """Setting up and running the simulation used for the tests."""
        esdl_file_path = str(Path(__file__).parent / ".." / ".." / "testdata" / "test1.esdl")
        esdl_object = EsdlObject(pyesdl_from_file(esdl_file_path))
        self.controller = EsdlControllerMapper().to_entity(esdl_object)
        self.start_time = datetime.strptime("2019-01-01T00:00:00", "%Y-%m-%dT%H:%M:%S")
        self.end_time = datetime.strptime("2019-01-01T06:00:00", "%Y-%m-%dT%H:%M:%S")
        config = SimulationConfiguration(
            simulation_id=uuid.uuid1(),
            name="test run",
            timestep=3600,
            start=self.start_time,
            stop=self.end_time
        )
        callback = Mock()
        app = SimulationManager(EsdlObject(pyesdl_from_file(esdl_file_path)), config)
        self.result = app.execute(callback)

        energy_system = esdl_object.energy_system_handler.energy_system

        # Collect demands
        self.demands = []
        for element in energy_system.eAllContents():
            if isinstance(element, esdl.HeatingDemand):
                self.demands.append(element)

        # Collect id of in and out ports of each demand.
        self.in_out_demand_dict = dict()
        for demand in self.demands:
            self.in_out_demand_dict[demand.id] = dict()
            for port in demand.port:
                if isinstance(port, esdl.InPort):
                    self.in_out_demand_dict[demand.id]["InPort"] = port.id
                elif isinstance(port, esdl.OutPort):
                    self.in_out_demand_dict[demand.id]["OutPort"] = port.id

    def _get_demand_in_out_temperatures(self, in_out_ports: dict) -> Tuple[dict, dict]:
        """Gets the temperatures at the in and out ports of the demand assets in the simulation."""
        temp_in_dict = dict()
        temp_out_dict = dict()
        for demand in self.demands:
            in_port_id = in_out_ports[demand.id]["InPort"]
            out_port_id = in_out_ports[demand.id]["OutPort"]

            temp_in_dict[demand.id] = np.array(self.result[(in_port_id, 'temperature')])
            temp_out_dict[demand.id] = np.array(self.result[(out_port_id, 'temperature')])

        return temp_in_dict, temp_out_dict

    def test_heat_power(self) -> None:
        """
        This test checks if the heat power supplied matches the demand profiles.

        It first computes the heat consumption and the demand assets using the mass flow,
        heat capacity and temperature delta and then compares it with esdl demand profile.
        """
        q_dot_demand_computed = dict()
        temp_in_dict, temp_out_dict = self._get_demand_in_out_temperatures(self.in_out_demand_dict)
        q_dot_demand_esdl = dict()
        consumers_object = self.controller.consumers

        for demand in self.demands:
            in_port_id = self.in_out_demand_dict[demand.id]["InPort"]
            out_port_id = self.in_out_demand_dict[demand.id]["OutPort"]
            m_dot_in_array = np.array(self.result[(in_port_id, 'mass_flow')])
            m_dot_out_array = np.array(self.result[(out_port_id, 'mass_flow')])
            m_dot = (-m_dot_in_array + m_dot_out_array) / 2
            cp = np.array([])
            temp_in_array = temp_in_dict[demand.id]
            temp_out_array = temp_out_dict[demand.id]

            for temp_in, temp_out in zip(temp_in_array, temp_out_array):
                cp = np.append(cp, fluid_props.get_heat_capacity((temp_in + temp_out) / 2))

            q_dot_demand_computed[demand.id] = m_dot * cp * (temp_in_array - temp_out_array)

        # Obtain demand profiles from the esdl
        for demand in consumers_object:
            demand_id = demand.id
            profile_dates = demand.profile["date"]
            profile_vals = demand.profile["values"]
            start_timestamp = pd.Timestamp(self.start_time).tz_localize('UTC')
            end_timestamp = pd.Timestamp(self.end_time).tz_localize('UTC')
            idx_start_prof = profile_dates.tolist().index(start_timestamp)
            idx_end_prof = profile_dates.tolist().index(end_timestamp)
            q_dot_demand_esdl[demand_id] = profile_vals[idx_start_prof:idx_end_prof]

        # Compare the computed heat consumption with the demand profiles in the esdl.
        for demand in consumers_object:
            demand_id = demand.id
            q_dot_esdl = np.array(q_dot_demand_esdl[demand_id])
            q_dot_computed = q_dot_demand_computed[demand_id]
            np.testing.assert_allclose(q_dot_esdl, q_dot_computed, rtol=0.001)

    def test_primary_return_temperature(self) -> None:
        """
        This test checks wether the return temperatures are always lower than the primary ones.

        It does it by comparing the temperatures at the in and out ports.
        """
        temp_in_dict, temp_out_dict = self._get_demand_in_out_temperatures(self.in_out_demand_dict)
        for demand in self.demands:
            temp_in_array = temp_in_dict[demand.id]
            temp_out_array = temp_out_dict[demand.id]
            np.testing.assert_array_less(temp_out_array, temp_in_array + 1e-5)
