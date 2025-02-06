#  Copyright (c) 2024. Deltares & TNO
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
"""HeatPump module."""

from omotes_simulator_core.entities.assets.asset_abstract import AssetAbstract
from omotes_simulator_core.entities.assets.esdl_asset_object import EsdlAssetObject
from omotes_simulator_core.solver.network.assets.base_asset import BaseAsset


class HeatPump(AssetAbstract):
    """A HeatPump represents an asset that delivers heat."""

    def __init__(self, asset_name: str, asset_id: str, port_ids: list[str]):
        """Initialize a HeatPump object.

        :param str asset_name: The name of the asset.
        :param str asset_id: The unique identifier of the asset.
        :param List[str] port_ids: List of ids of the connected ports.
        """
        super().__init__(asset_name=asset_name, asset_id=asset_id, connected_ports=port_ids)
        self.number_of_con_points = 4
        self.solver_asset = BaseAsset(
            name=self.name,
            _id=self.asset_id,
            number_of_unknowns=12,
            number_connection_points=self.number_of_con_points,
        )

    def set_setpoints(self, setpoints: dict) -> None:
        """Placeholder to set the setpoints of an asset prior to a simulation."""
        pass

    def add_physical_data(self, esdl_asset: EsdlAssetObject) -> None:
        """Add physical data to the asset."""
        pass

    def write_to_output(self) -> None:
        """Write the output of the asset to the output list."""
        pass
