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
"""Module containing the network class."""
import uuid

from simulator_core.solver.network.assets.base_asset import BaseAsset
from simulator_core.solver.network.assets.boundary import BaseBoundary
from simulator_core.solver.network.assets.fall_type import FallType
from simulator_core.solver.network.assets.node import Node
from simulator_core.solver.network.assets.production_asset import \
    ProductionAsset
from simulator_core.solver.network.assets.solver_pipe import SolverPipe


class Network:
    """Class to store a network consisting of nodes and assets."""

    str_to_class_dict = {
        "Boundary": BaseBoundary,
        "Asset": BaseAsset,
        "Fall": FallType,
        "Production": ProductionAsset,
        "Pipe": SolverPipe,
    }

    def __init__(self) -> None:
        """Constructor of the network class.

        Initializes the class properties and loads the fluid properties.
        """
        self.assets: dict[uuid.UUID, BaseAsset] = {}
        self.nodes: dict[uuid.UUID, Node] = {}

    def add_asset(self, asset_type: str, name: uuid.UUID | None = None) -> uuid.UUID:
        """Method to add an asset to the network.

        This method creates and asset of the given type.
        If the type does not exist a ValueError is raised.
        The unique id which is created for this asset is returned.
        :param name: Unique name of the asset, if not given a random uuid is created.
        :param str asset_type: The type of asset to be added
        :return: Unique id of the asset.
        """
        if asset_type not in self.str_to_class_dict:
            raise ValueError(asset_type + " not recognized")
        if name is None:
            name = uuid.uuid4()
        self.assets[name] = self.str_to_class_dict[asset_type](name)
        return name

    def add_existing_asset(self, asset: BaseAsset) -> uuid.UUID:
        """Method to add an existing asset to the network.

        This method adds an existing asset to the network. It checks if the asset already exists.
        If it does a ValueError is raised.
        :param BaseAsset asset: The asset to be added to the network.
        :return: Unique id of the asset.
        """
        if asset.name in self.assets:
            raise ValueError(f"{asset.name} already exists in network")
        self.assets[asset.name] = asset
        return asset.name

    def connect_assets(
        self, asset1: uuid.UUID, connection_point_1: int, asset2: uuid.UUID, connection_point_2: int
    ) -> uuid.UUID:
        """Method to connect to assets at the given connection points.

        This method connects the two assets if the exists. It checks if they already are connected.
        If not a new node is created. Otherwise, both are connected to the existing node.
        The id of the node connecting the two is returned

        :param asset1: id of first asset to be connected
        :param connection_point_1: Connection point of first asset to be connected
        :param asset2: id of second asset to be connected
        :param connection_point_2: Connection point of second asset to be connected
        :return: id of node connecting the two assets
        """
        if not self.exists_asset(asset1):
            raise ValueError(str(asset1) + " does not exists in network")
        elif not self.exists_asset(asset2):
            raise ValueError(str(asset2) + " does not exists in network")
        elif (not self.assets[asset1].is_connected(connection_point_1)) and not (
            self.assets[asset2].is_connected(connection_point_2)
        ):
            # both asset connect points not connected
            asset_id = uuid.uuid4()
            self.nodes[asset_id] = Node(name=asset_id)
            self.assets[asset1].connect_node(connection_point_1, self.nodes[asset_id])
            self.assets[asset2].connect_node(connection_point_2, self.nodes[asset_id])
            self.nodes[asset_id].connect_asset(self.assets[asset1], connection_point_1)
            self.nodes[asset_id].connect_asset(self.assets[asset2], connection_point_2)
            return asset_id
        elif (self.assets[asset1].is_connected(connection_point_1)) and not (
            self.assets[asset2].is_connected(connection_point_2)
        ):
            # asset 1 connected asset 2 not
            node = self.assets[asset1].get_connected_node(connection_point_1)
            self.assets[asset2].connect_node(connection_point_2, node)
            node.connect_asset(self.assets[asset2], connection_point_2)
            return node.name
        elif not self.assets[asset1].is_connected(connection_point_1) and self.assets[
            asset2
        ].is_connected(connection_point_2):
            # asset 2 connected asset 1 not
            node = self.assets[asset2].get_connected_node(connection_point_2)
            self.assets[asset1].connect_node(connection_point_1, node)
            node.connect_asset(self.assets[asset1], connection_point_1)
            return node.name
        elif not self.assets[asset1].is_connected(connection_point_1) and (
            not self.assets[asset2].is_connected(connection_point_2)
        ):
            # both asset already connected need to delete one node.
            raise NotImplementedError("Assets already connected to assets")
        else:
            raise NotImplementedError("Something has gone wrong assets already connected to node")

    def exists_asset(self, asset_id: uuid.UUID) -> bool:
        """Method returns true when an asset with the given id exists in the network.

        :param uuid.UUID asset_id: unique id of the asset to check.
        :return:True when asset exists and False when not
        """
        return asset_id in self.assets

    def exists_node(self, asset_id: uuid.UUID) -> bool:
        """Method returns true when a node with the given id exists in the network.

        :param uuid.UUID asset_id: unique id of the node to check.
        :return:True when node exists and False when not
        """
        return asset_id in self.nodes

    def remove_asset(self) -> None:
        """Method to remove an asset from the network."""

    def disconnect_asset(self) -> None:
        """Method to disconnect an asset from the network."""

    def get_asset(self, asset_id: uuid.UUID) -> BaseAsset:
        """Method to get an asset in the network.

        Method returns the asset with the given id, when it exists in the network.
        when it does not exist a ValueError is raised.

        :param id: asset_id of the asset which needs to be retrieved.
        :type asset_id: uuid.UUID
        :return: Asset
        """
        if not self.exists_asset(asset_id):
            raise ValueError(str(asset_id) + " Not a valid asset id")
        return self.assets[asset_id]

    def get_node(self, asset_id: uuid.UUID) -> Node:
        """Method to get a node in the network.

        Method returns the node with the given id, when it exists in the network.
        when it does not exist a ValueError is raised.

        :param asset_id: asset_id of the node which needs to be retrieved.
        :type asset_id: uuid.UUID
        :return: Node
        """
        if not self.exists_node(asset_id):
            raise ValueError(str(asset_id) + " Not a valid node id")
        return self.nodes[asset_id]

    def check_connectivity_assets(self) -> bool:
        """Method to check if all assets are connected.

        Method returns True when all assets are connected and False when an asset is not connected.
        :return: True or False depending on if all assets are connected
        """
        # TODO pass back which assets are not connected.
        result = [asset.is_all_connected() for _, asset in self.assets.items()]
        return all(result)

    def check_connectivity_nodes(self) -> bool:
        """Method to check if all nodes are connected.

        Method returns True when all nodes are connected and False when an node is not connected.
        :return: True or False depending on if all nodes are connected
        """
        result = [node.is_connected() for _, node in self.nodes.items()]
        return all(result)

    def check_connectivity(self) -> bool:
        """Method to check if all nodes and assets are connected.

        :return:True when everything is connected and False when not.
        """
        return self.check_connectivity_assets() and self.check_connectivity_nodes()

    def set_result_asset(self, solution: list[float]) -> None:
        """Method to transfer the solution to the asset in the network.

        :param list[float] solution:Solution to be transferred to the assets.
        :return: None
        """
        for asset in self.assets:
            index = self.get_asset(asset).matrix_index
            nou = self.get_asset(asset).number_of_unknowns
            self.get_asset(asset).prev_sol = solution[index: index + nou]

    def set_result_node(self, solution: list[float]) -> None:
        """Method to transfer the solution to the nodes in the network.

        :param list[float] solution:Solution to be transferred to the nodes.
        :return: None
        """
        for node in self.nodes:
            index = self.get_node(node).matrix_index
            nou = self.get_node(node).number_of_unknowns
            self.get_node(node).prev_sol = solution[index: index + nou]

    def print_result(self) -> None:
        """Method to print the result of the network."""
        for asset in self.assets:
            print(type(self.get_asset(asset)))
            print(self.get_asset(asset).get_result())