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
import capacities_europe
import capacity_factors_pv
import capacity_factors_wind
import load_europe
import grid_europe

import update_metadata
