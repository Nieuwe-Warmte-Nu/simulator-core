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
<<<<<<<< HEAD:unit_test/infrastructure/__init__.py
"""__init__.py file for initialization code."""
========
"""This file contains the class for the core quantities of the matrix."""
import dataclasses


@dataclasses.dataclass
class IndexCoreQuantity:
    """Enum for the index of the matrix.

    This is used to store the order of the core quants in the matrix.
    The number of core quantities is the maximum number of core quantities used.
    for the indices these should be in increasing order. This is not checked.
    """

    number_core_quantities = 3
    discharge = 0
    pressure = 1
    internal_energy = 2
>>>>>>>> 9aed530 (Changed index_enum class to dataclass):src/simulator_core/solver/matrix/index_core_quantity.py
