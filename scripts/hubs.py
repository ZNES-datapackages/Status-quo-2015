# -*- coding: utf-8 -*-
"""
NUTS Shapefiles
http://ec.europa.eu/eurostat/cache/GISCO/geodatafiles/NUTS_2013_10M_SH.zip
"""

import pandas as pd

from datapackage_utilities import building, geometry

config = building.get_config()

filepath = building.download_data(
    'http://ec.europa.eu/eurostat/cache/GISCO/geodatafiles/'
    'NUTS_2013_10M_SH.zip',
    unzip_file='NUTS_2013_10M_SH/data/NUTS_RG_10M_2013.shp')

building.download_data(
    'http://ec.europa.eu/eurostat/cache/GISCO/geodatafiles/'
    'NUTS_2013_10M_SH.zip',
    unzip_file='NUTS_2013_10M_SH/data/NUTS_RG_10M_2013.dbf')

# get nuts 1 regions for german neighbours
nuts0 = pd.Series(geometry.nuts(filepath, nuts=0, tolerance=0.1))

hubs = pd.Series(name='geometry')
hubs.index.name = 'name'

# add hubs and their geometry
for r in config['countries']:
    hubs[r + '-electricity'] = nuts0[r]

hub_elements = pd.DataFrame(hubs).drop('geometry', axis=1)
hub_elements.loc[:, 'type'] = 'bus'
hub_elements.loc[:, 'balanced'] = True
hub_elements.loc[:, 'geometry'] = hubs.index

building.write_geometries('buses.csv', hubs)
building.write_elements('bus.csv', hub_elements)
