# -*- coding: utf-8 -*-
"""
"""

from datapackage_utilities import building, processing

processing.clean_datapackage(directories=['data', 'ressources', 'results'])

# get config file
config = building.get_config()

# initialize directories etc. based on config file
building.initialize_dpkg()

import hubs
import capacities_dispatchable
import capacities_volatile
import capacities_hydro
import load
import grid

import update_metadata
