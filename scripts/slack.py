# -*- coding: utf-8 -*-
"""
"""

import pandas as pd

from datapackage_utilities import building

# excess
def create_resource(path):
    """
    """
    from datapackage import Resource
    resource = Resource({'path': path})
    resource.infer()
    resource.descriptor['schema']['primaryKey'] = 'name'
    resource.descriptor['description'] = 'Excess slacks for each electricity hub in the energy system representation'
    resource.descriptor['title'] = 'Excess slacks for DE and its electrical neighbours'

    resource.descriptor['schema']['foreignKeys'] =   [{
        "fields": "bus",
        "reference": {
            "resource": "bus",
            "fields": "name"}}]

    resource.commit()
    resource.descriptor

    if resource.valid:
        resource.save('resources/'+ resource.name + '.json')

config = building.get_config()

buses = building.read_elements('bus.csv')
buses.index.name = 'bus'

elements = pd.DataFrame(buses.index)

elements['type'] = 'excess'
elements['name'] = 'excess-' + elements['bus'].str[:2]
elements['marginal_cost'] = 0

elements.set_index('name', inplace=True)

path = building.write_elements('excess.csv', elements)

create_resource(path)

# shortage
def create_resource(path):
    """
    """
    from datapackage import Resource
    resource = Resource({'path': path})
    resource.infer()
    resource.descriptor['schema']['primaryKey'] = 'name'
    resource.descriptor['description'] = 'Shortage slacks for each electricity hub in the energy system representation'
    resource.descriptor['title'] = 'Shortage slacks for DE and its electrical neighbours'

    resource.descriptor['schema']['foreignKeys'] =   [{
        "fields": "bus",
        "reference": {
            "resource": "bus",
            "fields": "name"}}]

    resource.commit()
    resource.descriptor

    if resource.valid:
        resource.save('resources/'+ resource.name + '.json')

config = building.get_config()

buses = building.read_elements('bus.csv')
buses.index.name = 'bus'

elements = pd.DataFrame(buses.index)

elements['type'] = 'generator'
elements['name'] = 'shortage-' + elements['bus'].str[:2]
elements['capacity'] = 50000
elements['marginal_cost'] = 1000

elements.set_index('name', inplace=True)

path = building.write_elements('shortage.csv', elements)
create_resource(path)
