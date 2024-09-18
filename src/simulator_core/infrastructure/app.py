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

"""Entry point for running simulator-core library from cmdline."""
import logging
import sys
import traceback
import uuid
from datetime import datetime

import pandas as pd

from simulator_core.entities.esdl_object import EsdlObject
from simulator_core.entities.simulation_configuration import SimulationConfiguration
from simulator_core.infrastructure.simulation_manager import SimulationManager
from simulator_core.infrastructure.utils import pyesdl_from_file

logger = logging.getLogger(__name__)


def progressLogger(progress: float, message: str) -> None:
    """Function to report progress to logging/stdout."""
    logger.info(f"{message} ({progress*100:.2f}%)")


def run_simulator(file_path: str | None = None) -> pd.DataFrame:
    """Main run function for the heat network simulator."""
    config = SimulationConfiguration(
        simulation_id=uuid.uuid1(),
        name="test run",
        timestep=3600,
        start=datetime.strptime("2019-01-01T00:00:00", "%Y-%m-%dT%H:%M:%S"),
        stop=datetime.strptime("2019-01-02T01:00:00", "%Y-%m-%dT%H:%M:%S"),
    )

    esdl_file_path = sys.argv[1] if file_path is None else file_path
    try:
        app = SimulationManager(EsdlObject(pyesdl_from_file(esdl_file_path)), config)
        result = app.execute(progressLogger)
        return result
    except Exception as error:
        logger.error(f"Error occured: {error} at: {traceback.format_exc(limit=-1)}")
        logger.debug(traceback.format_exc())
        raise error


def main() -> None:
    """Main function for the OMOTES simulator."""
    # Set loglevel to logging.DEBUG for more verbose output
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(levelname)s]:%(name)s - %(message)s"
    )
    t1 = datetime.now()
    result = run_simulator(r".\testdata\test1.esdl")
    t2 = datetime.now()

    logger.info(f"Results dataframe shape=({result.shape})")
    logger.info(f"Execution time: {t2-t1}")
    logger.debug(result.head())


if __name__ == "__main__":
    main()
