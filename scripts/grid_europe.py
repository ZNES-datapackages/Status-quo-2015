# -*- coding: utf-8 -*-
"""
"""

import pandas as pd

from datapackage_utilities import building


def create_resource(path):
    from datapackage import Resource
    resource = Resource({'path': path})
    resource.infer()
    resource.descriptor['schema']['primaryKey'] = 'name'
    resource.descriptor['description'] = 'Installed transmission capacities based on ENTSO-E values'
    resource.descriptor['title'] = 'Installed transmission capacities'
    resource.descriptor['sources'] = [{
        'title': 'ENTSO-E publications. (2016, March 21). NTC Values Winter 2010-2011.',
        'path': 'https://www.entsoe.eu/fileadmin/user_upload/_library/ntc/archive/NTC-Values-Winter-2010-2011.pdf'
    }]

    resource.descriptor['schema']['foreignKeys'] = [
        {
            "fields": "from_bus",
            "reference": {
                "resource": "bus",
                "fields": "name"}},
        {
            "fields": "to_bus",
            "reference": {
                "resource": "bus",
                "fields": "name"}}]

    resource.commit()

    if resource.valid:
        resource.save('resources/' + resource.name + '.json')

config = building.get_config()

loss = 0.03
countries = config['countries']

filepath = building.input_filepath('transmission-data.csv')

data = pd.read_csv(filepath, skiprows=3, sep=';', index_col=['from', 'to'])

elements = {}
for (x, y), (value, _) in data.iterrows():

    from_bus, to_bus = x + '-electricity', y + '-electricity'

    element = {
        'type': 'connection',
        'loss': loss,
        'to_bus': to_bus,
        'from_bus': from_bus,
        'capacity': value
    }

    elements[from_bus + '-' + to_bus] = element

path = building.write_elements(
    'transshipment.csv', pd.DataFrame.from_dict(elements, orient='index'))

create_resource(path)
