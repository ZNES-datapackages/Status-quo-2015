# -*- coding: utf-8 -*-
"""
This script constructs a pandas.Series `hubs` with hub-names as index and
polygons of these hubs as values. It uses the NUTS shapefile.
"""

import pandas as pd

from datapackage_utilities import building, geometry

def create_resource(path):
    """
    """
    from datapackage import Resource
    resource = Resource({'path': path})
    resource.infer()
    resource.descriptor['schema']['primaryKey'] = 'name'
    resource.descriptor['description'] = 'Contains the hubs (nodes) for the energy system representation'
    resource.descriptor['title'] = 'Energy system hubs for DE and its electrical neighbours'
    resource.descriptor['sources'] = [{
        'title': 'NUTS Shapefiles',
        'path': 'http://ec.europa.eu/eurostat/cache/GISCO/geodatafiles/NUTS_2013_10M_SH.zip',
        'files': ['NUTS_2013_10M_SH/data/NUTS_RG_10M_2013.shp',
                  'NUTS_2013_10M_SH/data/NUTS_RG_10M_2013.dbf']}]

    if 'geometries' in path:

        resource.descriptor['schema']['foreignKeys'] =   [{
            "fields": "bus",
            "reference": {
                "resource": "bus",
                "fields": "name"}}]

    resource.commit()
    resource.descriptor

    if resource.valid:
        resource.save('resources/' + resource.name + '.json')

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

path = building.write_geometries('buses.csv', hubs)

create_resource(path)

path = building.write_elements('bus.csv', hub_elements)
create_resource(path)
