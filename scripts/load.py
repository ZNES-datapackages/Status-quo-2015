# -*- coding: utf-8 -*-
"""
"""

import json
import pandas as pd

from datapackage_utilities import building


config = building.get_config()
filepath = building.download_data(
    'https://data.open-power-system-data.org/time_series/2017-07-09/' +
    'time_series_60min_singleindex.csv')

raw_data = pd.read_csv(filepath, index_col=[0], parse_dates=True)

suffix = '_load_entsoe_power_statistics'

countries, year = config['countries'], str(config['year'])

columns = [c + suffix for c in countries]

timeseries = raw_data.loc[year, columns]

demand_total = timeseries.sum()

demand_profile = timeseries / demand_total

elements = {}

sequences_df = pd.DataFrame(index=demand_profile.index)

for c in countries:
    element_name = 'electricity-demand-' + c
    sequence_name = element_name +  '-profile'

    sequences_df[sequence_name] = demand_profile[c + suffix].values

    element = {
        'type': 'demand',
        'profile': sequence_name,
        'type': 'demand',
        'tech': 'demand',
        'bus': c + '-electricity',
        'amount': demand_total[c + suffix]
    }

    elements[element_name] = element

def create_resource(path):
    """
    """

    from datapackage import Resource
    resource = Resource({'path': path})
    resource.infer()
    resource.descriptor['schema']['primaryKey'] = 'name'
    resource.descriptor['description'] = 'Demand components'
    resource.descriptor['title'] = '{} components'.format(resource.name.title())
    resource.descriptor['sources'] = [{
        'title': 'Open Power System Data. 2017. Data Package Time series. Version 2017-07-09. https://data.open-power-system-data.org/time_series/2017-07-09/. (Primary data from various sources, for a complete list see URL)',
        'path': 'https://data.open-power-system-data.org/time_series/2017-07-09/time_series_60min_singleindex.csv'}]


    resource.descriptor['schema']['foreignKeys'] =   [{
        "fields": "bus",
        "reference": {
            "resource": "bus",
            "fields": "name"}}]


    resource.descriptor['schema']['foreignKeys'] .append({
        "fields": "profile",
        "reference": {
            "resource": "demand-profiles"}})

    resource.commit()

    if resource.valid:
        resource.save('resources/'+ resource.name + '.json')
    else:
        print('Resource is not valid, writing resource anyway...')
        resource.save('resources/'+ resource.name + '.json')

path = building.write_elements('demand.csv', pd.DataFrame.from_dict(elements, orient='index'))

create_resource(path)

def create_resource(path):
    from datapackage import Resource
    resource = Resource({'path': path})
    resource.infer()
    resource.descriptor['schema']['primaryKey'] = 'timeindex'
    resource.descriptor['description'] = 'Demand profiles per country'
    resource.descriptor['title'] = 'Demand profiles'
    resource.descriptor['sources'] = [{
        'title': 'OPSD timeseries',
        'path': 'https://data.open-power-system-data.org/time_series/2017-07-09/' +
                'time_series_60min_singleindex.csv'}]
    resource.commit()

    if resource.valid:
        resource.save('resources/'+ resource.name + '.json')

sequences_df.index = building.timeindex()
path = building.write_sequences('demand-profiles.csv', sequences_df)

create_resource(path)
