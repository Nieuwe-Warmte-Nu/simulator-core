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

"""Module containing the Esdl to asset mapper class."""
import esdl
import numpy as np

from omotes_simulator_core.entities.assets.asset_abstract import AssetAbstract
from omotes_simulator_core.entities.assets.controller.asset_controller_abstract import (
    AssetControllerAbstract,
)
from omotes_simulator_core.entities.assets.esdl_asset_object import EsdlAssetObject
from omotes_simulator_core.entities.assets.controller.controller_producer import ControllerProducer
from omotes_simulator_core.entities.assets.controller.controller_consumer import ControllerConsumer
from omotes_simulator_core.entities.assets.controller.controller_storage import ControllerStorage

from omotes_simulator_core.simulation.mappers.mappers import EsdlMapperAbstract
from omotes_simulator_core.adapter.transforms.esdl_asset_mappers.pipe_mapper import (
    EsdlAssetPipeMapper,
)
from omotes_simulator_core.adapter.transforms.esdl_asset_mappers.producer_mapper import (
    EsdlAssetProducerMapper,
)
from omotes_simulator_core.adapter.transforms.esdl_asset_mappers.consumer_mapper import (
    EsdlAssetConsumerMapper,
)
from omotes_simulator_core.adapter.transforms.esdl_asset_mappers.heat_pump_mapper import (
    EsdlAssetHeatPumpMapper,
)
from omotes_simulator_core.adapter.transforms.esdl_asset_mappers.ates_mapper import (
    EsdlAssetAtesMapper,
)
from omotes_simulator_core.adapter.transforms.esdl_asset_mappers.heat_buffer_mapper import (
    EsdlAssetHeatBufferMapper,
)

# Define the conversion dictionary
conversion_dict_mappers: dict[type, type[EsdlMapperAbstract]] = {
    esdl.Producer: EsdlAssetProducerMapper,
    esdl.GenericProducer: EsdlAssetProducerMapper,
    esdl.Consumer: EsdlAssetConsumerMapper,
    esdl.GenericConsumer: EsdlAssetConsumerMapper,
    esdl.HeatingDemand: EsdlAssetConsumerMapper,
    esdl.Pipe: EsdlAssetPipeMapper,
    esdl.HeatPump: EsdlAssetHeatPumpMapper,
    esdl.ATES: EsdlAssetAtesMapper,
    esdl.WaterBuffer: EsdlAssetHeatBufferMapper,
}


class EsdlAssetMapper:
    """Creates entity Asset objects based on a PyESDL EnergySystem assets."""

    @staticmethod
    def to_esdl(entity: AssetAbstract) -> EsdlAssetObject:
        """Maps entity object to PyEsdl objects."""
        raise NotImplementedError("EsdlAssetMapper.to_esdl()")

    @staticmethod
    def to_entity(model: EsdlAssetObject) -> AssetAbstract:
        """Method to map an esdl asset to an asset entity class.

        :param EsdlAssetObject model: Object to be converted to an asset entity.

        :return: Entity object of type AssetAbstract.
        """
        if type(model.esdl_asset) not in conversion_dict_mappers:
            raise NotImplementedError(str(model.esdl_asset) + " not implemented in conversion")

        # Use the dictionary to get the appropriate mapper
        asset_type = type(model.esdl_asset)
        mapper = conversion_dict_mappers[asset_type]()
        return mapper.to_entity(model)  # type: ignore


class EsdlAssetControllerProducerMapper(EsdlMapperAbstract):
    """Class to map an esdl asset to a producer entity class."""

    def to_esdl(self, entity: AssetControllerAbstract) -> EsdlAssetObject:
        """Map an Entity to a EsdlAsset."""
        raise NotImplementedError("EsdlAssetControllerProducerMapper.to_esdl()")

    def to_entity(self, esdl_asset: EsdlAssetObject) -> ControllerProducer:
        """Method to map an esdl asset to a producer entity class.

        :param EsdlAssetObject model: Object to be converted to an asset entity.

        :return: Entity object.
        """
        result = esdl_asset.get_property(esdl_property_name="power", default_value=0)
        if result[1]:
            power = result[0]
        else:
            raise ValueError(f"No power found for asset: {esdl_asset.esdl_asset.name}")
        marginal_costs = esdl_asset.get_marginal_costs()
        temperature_supply = esdl_asset.get_supply_temperature("Out")
        temperature_return = esdl_asset.get_return_temperature("In")
        contr_producer = ControllerProducer(
            name=esdl_asset.esdl_asset.name,
            identifier=esdl_asset.esdl_asset.id,
            temperature_supply=temperature_supply,
            temperature_return=temperature_return,
            power=power,
            marginal_costs=marginal_costs,
        )
        return contr_producer


class EsdlAssetControllerConsumerMapper(EsdlMapperAbstract):
    """Class to map an esdl asset to a consumer entity class."""

    def to_esdl(self, entity: AssetControllerAbstract) -> EsdlAssetObject:
        """Map an Entity to a EsdlAsset."""
        raise NotImplementedError("EsdlAssetControllerProducerMapper.to_esdl()")

    def to_entity(self, esdl_asset: EsdlAssetObject) -> ControllerConsumer:
        """Method to map an esdl asset to a consumer entity class.

        :param EsdlAssetObject model: Object to be converted to an asset entity.

        :return: Entity object.
        """
        result = esdl_asset.get_property(esdl_property_name="power", default_value=np.inf)
        power = np.inf
        if result[1]:
            power = result[0]
        if power == 0:
            power = np.inf

        # It looks like they are switch, but this is because of the definition used in ESDL,
        # which is different as what we use.
        temperature_supply = esdl_asset.get_return_temperature("Out")
        temperature_return = esdl_asset.get_supply_temperature("In")
        profile = esdl_asset.get_profile()
        contr_consumer = ControllerConsumer(
            name=esdl_asset.esdl_asset.name,
            identifier=esdl_asset.esdl_asset.id,
            temperature_supply=temperature_supply,
            temperature_return=temperature_return,
            max_power=power,
            profile=profile,
        )
        return contr_consumer


class EsdlAssetControllerStorageMapper(EsdlMapperAbstract):
    """Class to map an esdl asset to a storage entity class."""

    def to_esdl(self, entity: AssetControllerAbstract) -> EsdlAssetObject:
        """Map an Entity to a EsdlAsset."""
        raise NotImplementedError("EsdlAssetControllerStorageMapper.to_esdl()")

    def to_entity(self, esdl_asset: EsdlAssetObject) -> ControllerStorage:
        """Method to map an esdl asset to a storage entity class.

        :param EsdlAssetObject model: Object to be converted to an asset entity.

        :return: Entity object.
        """
        result = esdl_asset.get_property(
            esdl_property_name="maxDischargeRate", default_value=np.inf
        )
        discharge_power = np.inf
        if result[1]:
            discharge_power = result[0]

        result = esdl_asset.get_property(esdl_property_name="maxChargeRate", default_value=np.inf)
        charge_power = np.inf
        if result[1]:
            charge_power = result[0]

        temperature_supply = esdl_asset.get_supply_temperature("In")
        temperature_return = esdl_asset.get_return_temperature("Out")
        profile = esdl_asset.get_profile()
        contr_storage = ControllerStorage(
            name=esdl_asset.esdl_asset.name,
            identifier=esdl_asset.esdl_asset.id,
            temperature_supply=temperature_supply,
            temperature_return=temperature_return,
            max_charge_power=charge_power,
            max_discharge_power=discharge_power,
            profile=profile,
        )
        return contr_storage
