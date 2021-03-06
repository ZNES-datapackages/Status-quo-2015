# -*- coding: utf-8 -*-
"""
"""

from oemof.tabular.datapackage import building, processing

processing.clean(directories=['data', 'ressources', 'results'])

# get config file
config = building.read_build_config('config.toml')

# initialize directories etc. based on config file
building.initialize(config)

import hubs
import dispatchable
import dispatchable_de
import volatile
import volatile_profiles
import hydro
import load
import grid
import excess
import shortage

building.infer_metadata(package_name='Status quo 2015',
                        foreign_keys={
                            'bus': ['volatile', 'dispatchable',
                                    'load', 'excess', 'shortage', 'ror', 'phs', 'reservoir'],
                            'profile': ['load', 'volatile', 'ror', 'reservoir'],
                            'from_to_bus': ['grid'],
                            'chp': []
                            }
                        )
