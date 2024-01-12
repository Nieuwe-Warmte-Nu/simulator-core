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

from pathlib import Path
from pandapipes import create_empty_network
from simulator_core.adapter.transforms.mappers import EsdlEnergySystemMapper
from simulator_core.entities.esdl_object import EsdlObject
from simulator_core.infrastructure.utils import pyesdl_from_file
from simulator_core.entities.assets import (Junction, AssetAbstract)
from typing import Tuple, List


class EsdlEnergySystemMapperTest(unittest.TestCase):
    """Class to test energy system mapper class."""

    def test_to_entity(self):
        """Method to test the to entity mapper class."""
        # act
        esdl_file_path = Path(__file__).parent / ".." / ".." / "testdata" / "test1.esdl"
        esdl_file_path = str(esdl_file_path)
        esdl_object = EsdlObject(pyesdl_from_file(esdl_file_path))
        pandapipes_net = create_empty_network(fluid="water")

        # arrange
        result = EsdlEnergySystemMapper(esdl_object).to_entity(pandapipes_net)

        # assert
        self.assertIsInstance(result, Tuple)
        self.assertIsInstance(result[0], List)
        self.assertIsInstance(result[0][0], AssetAbstract)
        self.assertIsInstance(result[1], List)
        self.assertIsInstance(result[1][0], Junction)
        self.assertEqual(len(result[0]), 4)
        self.assertEqual(len(result[1]), 4)