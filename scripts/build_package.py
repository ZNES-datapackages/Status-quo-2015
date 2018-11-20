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
import dispatchable
import volatile
import volatile_profiles
#import hydro
import load
import grid
import excess
import shortage

building.infer_metadata(package_name='Status quo 2015',
                        foreign_keys={
                            'bus': ['volatile', 'dispatchable',
                                    'load', 'excess', 'shortage'],
                            'profile': ['load', 'volatile'],
                            'from_to_bus': ['grid'],
                            'chp': []
                            }
                        )
