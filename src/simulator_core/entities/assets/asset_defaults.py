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

"""Define default values and names for assets."""
from dataclasses import dataclass

# Default values
DEFAULT_DIAMETER = 1.2  # [m]
DEFAULT_PRESSURE = 10.0  # [bar]
DEFAULT_PRESSURE_DIFFERENCE = 5  # [bar]
DEFAULT_TEMPERATURE = 300.0  # [K]
DEFAULT_TEMPERATURE_DIFFERENCE = 30.0  # [K]
DEFAULT_NODE_HEIGHT = 0.0  # [m]
DEFAULT_MASS_FLOW_RATE = 1.0  # [kg/s]


@dataclass
class PipeDefaults:
    """Class containing the default values for a pipe.

    :param float k_value: The k value of the pipe [m].
    :param float alpha_value: The alpha value of the pipe [W/(m2 K)].
    :param float minor_loss_coefficient: The minor loss coefficient of the pipe [-].
    :param float external_temperature: The external temperature of the pipe [K].
    :param float qheat_external: The external heat flow of the pipe [W].
    """

    k_value: float = 2e-3
    alpha_value: float = 0.0
    minor_loss_coefficient: float = 0.0
    external_temperature: float = 273.15 + 20.0
    qheat_external: float = 0.0
    length: float = 1.0
    diameter: float = DEFAULT_DIAMETER


# Default names
PROPERTY_HEAT_DEMAND = "heat_demand"
PROPERTY_TEMPERATURE_SUPPLY = "temperature_supply"
PROPERTY_TEMPERATURE_RETURN = "temperature_return"
PROPERTY_PRESSURE_SUPPLY = "pressure_supply"
PROPERTY_PRESSURE_RETURN = "pressure_return"
PROPERTY_MASSFLOW = "mass_flow"
PROPERTY_VOLUMEFLOW = "volume_flow"
PROPERTY_THERMAL_POWER = "thermal_power"
PROPERTY_VELOCITY_SUPPLY = "velocity_supply"
PROPERTY_VELOCITY_RETURN = "velocity_return"
PROPERTY_SET_PRESSURE = "set_pressure"

# Static members
PIPE_DEFAULTS = PipeDefaults()
