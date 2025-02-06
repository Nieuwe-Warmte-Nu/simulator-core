Assets
=========================
This section provides an overview of the asset classes within the simulator core. Assets are the essential components that represent different entities and systems modeled in the simulation. These assets include energy producers, consumers, storage systems, and transport components, such as pipes. A brief overview of the assets is provided below:

#. :ref:`ates-asset`: Represents an Aquifer Thermal Energy Storage (ATES) system for storing and retrieving thermal energy from groundwater.

#. :ref:`consumer-asset`: Models energy consumers, such as households or industrial facilities, that draw energy from the network.

#. :ref:`heatpump-asset`: Defines heat pump systems, which transfer thermal energy for heating or cooling purposes.

#. :ref:`pipe-asset`: Pipes which act as conduits for energy transfer between network entities.

#. :ref:`producer-asset`: Represents energy-producing sources.

Assets consists of different class to model the different assets.
The main goal of the assets classes is to take the physical input of the
assets (e.g. inner diameter wall roughness) and translate this into
linearized equations.

.. autoclass:: omotes_simulator_core.solver.network.assets.base_item.BaseItem
   :members:
   :show-inheritance:
.. autoclass:: omotes_simulator_core.solver.network.assets.base_asset.BaseAsset
   :members:
   :show-inheritance:
.. autoclass:: omotes_simulator_core.solver.network.assets.fall_type.FallType
   :members:
   :show-inheritance:
.. autoclass:: omotes_simulator_core.solver.network.assets.solver_pipe.SolverPipe
   :members:
   :show-inheritance:
.. autoclass:: omotes_simulator_core.solver.network.assets.node.Node
   :members:
   :show-inheritance:



**Contents**

.. toctree::
    :maxdepth: 1
    :glob:

    ates_asset.rst
    consumer_asset.rst
    heat_pump_asset.rst
    pipe_asset.rst
    producer_asset.rst








