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

"""Module containing BaseAsset class."""
import math

import numpy as np

from omotes_simulator_core.solver.matrix.equation_object import EquationObject
from omotes_simulator_core.solver.network.assets.base_item import BaseItem
from omotes_simulator_core.solver.network.assets.base_node_item import BaseNodeItem
from omotes_simulator_core.solver.utils.fluid_properties import fluid_props


class BaseAsset(BaseItem):
    """A base class for assets in a network.

    This class inherits from BaseItem and provides methods for connecting nodes, checking connection
    status, and adding thermal and pressure equations.
    """

    connected_nodes: dict[int, BaseNodeItem]

    def __init__(
        self,
        name: str,
        _id: str,
        number_of_unknowns: int = 6,
        number_connection_points: int = 2,
        supply_temperature: float = 293.15,
    ):
        """Initializes the BaseAsset object with the given parameters.

        :param str name: The name of the asset.
        :param str _id: The unique identifier of the asset.
        :param int, optional number_of_unknowns: The number of unknown variables for the node.
        The default is 3.
        :param int, optional number_connection_points: The number of connection points for the
            asset. The default is 2, which corresponds to the inlet and outlet.
        """
        super().__init__(
            name=name,
            _id=_id,
            number_of_unknowns=number_of_unknowns,
            number_connection_points=number_connection_points,
        )
        self.supply_temperature = supply_temperature
        self.connected_nodes = {}

    def check_connection_point_valid(self, connection_point: int) -> bool:
        """Checks if the connection point is valid for the asset.

        :param connection_point: The index of the connection point to check.
        :type connection_point: int
        :return: True if the connection point is valid, otherwise raises an IndexError.
        :rtype: bool
        """
        if connection_point > self.number_of_connection_point - 1:
            raise IndexError(
                f"Asset {self.name} only has {self.number_of_connection_point - 1}. "
                f"{connection_point} is too high"
            )
        else:
            return True

    def connect_node(self, connection_point: int, node: BaseNodeItem) -> None:
        """Connects a node to a connection point of the asset.

        :param connection_point: The index of the connection point to connect.
        :type connection_point: int
        :param node: The node to connect.
        :type node: Node
        :raises ValueError: If the connection point is already connected to a node.
        """
        self.check_connection_point_valid(connection_point)
        if connection_point in self.connected_nodes:
            raise ValueError(
                f" connection point {connection_point}  of asset {self.name} "
                f" already connected to a node"
            )

        self.connected_nodes[connection_point] = node

    def disconnect_node(self, connection_point: int) -> None:
        """Disconnects a node from a connection point of the asset.

        :param connection_point: The index of the connection point to disconnect.
        :type connection_point: int
        :raises ValueError: If the connection point is not connected to a node.
        """
        self.check_connection_point_valid(connection_point)
        del self.connected_nodes[connection_point]

    def is_connected(self, connection_point: int) -> bool:
        """Checks if a connection point is connected to a node.

        :param connection_point: The index of the connection point to check.
        :type connection_point: int
        :return: True if the connection point is connected, False otherwise.
        :rtype: bool
        """
        if self.check_connection_point_valid(connection_point):
            return connection_point in self.connected_nodes
        else:
            return False

    def get_connected_node(self, connection_point: int) -> BaseNodeItem:
        """Checks if a connection point is connected to a node.

        :param connection_point: The index of the connection point to check.
        :type connection_point: int
        :return: True if the connection point is connected, False otherwise.
        :rtype: bool
        """
        self.check_connection_point_valid(connection_point)

        if self.is_connected(connection_point):
            return self.connected_nodes[connection_point]
        raise ValueError(str(connection_point) + " is not connected")

    def is_all_connected(self) -> bool:
        """Checks if all connection points are connected to nodes.

        :return: True if all connection points are connected, False otherwise.
        :rtype: bool
        """
        result = [self.is_connected(i) for i in range(self.number_of_connection_point)]
        return all(result)

    def get_thermal_equations(self, connection_point: int) -> EquationObject:
        """Gets a thermal equation for a connection point of the asset.

        :param connection_point: The index of the connection point to get the equation for.
        :type connection_point: int
        :return: An equation object representing the thermal equation.
        :rtype: EquationObject
        """
        if (
            self.prev_sol[
                self.get_index_matrix(
                    property_name="mass_flow_rate",
                    connection_point=connection_point,
                    use_relative_indexing=True,
                )
            ]
            > 0
        ):
            return self.get_prescribe_temp_equation(connection_point)
        else:
            return self.get_internal_energy_to_node_equation(connection_point)

    def get_prescribe_temp_equation(self, connection_point: int) -> EquationObject:
        """Gets a prescribed temperature equation for a connection point of the asset.

        :param connection_point: The index of the connection point to get the equation for.
        :type connection_point: int
        :return: An equation object representing the prescribed temperature equation.
        :rtype: EquationObject
        """
        if not self.is_connected(connection_point=connection_point):
            raise ValueError(
                f"Connection point {connection_point} of asset {self.name} is not connected to a"
                + " node."
            )
        equation_object = EquationObject()
        equation_object.indices = np.array(
            [
                self.get_index_matrix(
                    property_name="internal_energy",
                    connection_point=connection_point,
                    use_relative_indexing=False,
                )
            ]
        )
        equation_object.coefficients = np.array([1.0])
        equation_object.rhs = fluid_props.get_ie(self.supply_temperature)
        return equation_object

    def get_internal_energy_to_node_equation(self, connection_point: int) -> EquationObject:
        """Gets a temperature to node equation for a connection point of the asset.

        :param connection_point: The index of the connection point to get the equation for.
        :type connection_point: int
        :return: An equation object representing the temperature to node equation.
        :rtype: EquationObject
        """
        # Check if the connection point is connected to a node
        if not self.is_connected(connection_point=connection_point):
            raise ValueError(
                f"Connection point {connection_point} of asset {self.name} is not connected to a"
                + " node."
            )

        equation_object = EquationObject()
        equation_object.indices = np.array(
            [
                self.get_index_matrix(
                    property_name="internal_energy",
                    connection_point=connection_point,
                    use_relative_indexing=False,
                ),
                self.get_connected_node(connection_point).get_index_matrix(
                    property_name="internal_energy", use_relative_indexing=False
                ),
            ]
        )
        equation_object.coefficients = np.array([1.0, -1.0])
        equation_object.rhs = 0.0
        return equation_object

    def set_physical_properties(self, physical_properties: dict[str, float]) -> None:
        """Method to set the physical properties of the asset.

        This method is implemented in the derived classes of this class.
        """

    def get_press_to_node_equation(self, connection_point: int) -> EquationObject:
        """Gets a pressure to node equation for a connection point of the asset.

        :param connection_point: The index of the connection point to get the equation for.
        :type connection_point: int
        :return: An equation object representing the pressure to node equation.
        :rtype: EquationObject
        """
        # Check if the connection point is connected to a node
        if not self.is_connected(connection_point=connection_point):
            raise ValueError(
                f"Connection point {connection_point} of asset {self.name} is not connected to a"
                + " node."
            )

        equation_object = EquationObject()
        equation_object.indices = np.array(
            [
                self.get_index_matrix(
                    property_name="pressure",
                    connection_point=connection_point,
                    use_relative_indexing=False,
                ),
                self.get_connected_node(connection_point).get_index_matrix(
                    property_name="pressure", use_relative_indexing=False
                ),
            ]
        )
        equation_object.coefficients = np.array([1.0, -1.0])
        equation_object.rhs = 0.0
        return equation_object

    def get_result(self) -> list[float]:
        """Method to get the result of the asset.

        :return: a list of the unknowns which are solved.
        """
        results = []
        for i in range(self.number_of_connection_point):
            for j in range(math.floor(self.number_of_unknowns / self.number_of_connection_point)):
                if j == 2:
                    results.append(
                        fluid_props.get_t(
                            self.prev_sol[
                                i
                                * math.floor(
                                    self.number_of_unknowns / self.number_of_connection_point
                                )
                                + j
                            ]
                        )
                    )
                else:
                    results.append(
                        self.prev_sol[
                            i
                            * math.floor(self.number_of_unknowns / self.number_of_connection_point)
                            + j
                        ]
                    )
        return results

    def get_equations(self) -> list[EquationObject]:
        """Method to get the equations of the asset.

        This method is implemented in the derived classes of this class.

        :return: A list of equation objects representing the equations of the asset.
        """
        return []

    def get_mass_flow_rate(self, connection_point: int) -> float:
        """Method to get the mass flow rate of a connection point.

        :param int connection_point: The connection point for which to get the mass flow rate.
        :return: The mass flow rate of the connection point.
        """
        return float(
            self.prev_sol[
                self.get_index_matrix(
                    property_name="mass_flow_rate",
                    connection_point=connection_point,
                    use_relative_indexing=True,
                )
            ]
        )

    def get_pressure(self, connection_point: int) -> float:
        """Method to get the pressure of a connection point.

        :param int connection_point: The connection point for which to get the pressure.
        :return: The pressure of the connection point.
        """
        return float(
            self.prev_sol[
                self.get_index_matrix(
                    property_name="pressure",
                    connection_point=connection_point,
                    use_relative_indexing=True,
                )
            ]
        )

    def get_temperature(self, connection_point: int) -> float:
        """Method to get the temperature of a connection point.

        :param int connection_point: The connection point for which to get the temperature.
        :return: The temperature of the connection point.
        """
        return fluid_props.get_t(
            self.prev_sol[
                self.get_index_matrix(
                    property_name="internal_energy",
                    connection_point=connection_point,
                    use_relative_indexing=True,
                )
            ]
        )

    def get_internal_energy(self, connection_point: int) -> float:
        """Method to get the internal energy of a connection point for the last computed time step.

        :param int connection_point: The connection point for which to get the internal energy.
        :return: The internal energy of the connection point.
        """
        return float(
            self.prev_sol[
                self.get_index_matrix(
                    property_name="internal_energy",
                    connection_point=connection_point,
                    use_relative_indexing=True,
                )
            ]
        )
