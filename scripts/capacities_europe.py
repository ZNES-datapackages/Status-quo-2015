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
    resource.descriptor['description'] = 'Installed capacities, costs and technical parameters for components'
    resource.descriptor['title'] = '{} components'.format(resource.name.title())
    resource.descriptor['sources'] = [{
        'title': 'Scenario Outlook and Adequacy Forecast 2014-2030',
        'path': 'https://www.entsoe.eu/Documents/SDC%20documents/SOAF/140602_SOAF%202014_dataset.zip'
    }]

    resource.descriptor['schema']['foreignKeys'] = [{
        "fields": "bus",
        "reference": {
            "resource": "bus",
            "fields": "name"}}]

    if 'volatile-generator' in resource.name:
        resource.descriptor['schema']['foreignKeys'] .append({
            "fields": "profile",
            "reference": {
                "resource": "generator-profiles"}})

    resource.commit()

    if resource.valid:
        resource.save('resources/' + resource.name + '.json')
    else:
        print('Resource is not valid, writing resource anyway...')
        resource.save('resources/' + resource.name + '.json')


config = building.get_config()
countries, year = config['countries'], config['year']

t_data = pd.read_csv('archive/technologies.csv', sep=';', index_col=[0, 1])
c_data = pd.read_csv('archive/commodities.csv', sep=';', index_col=[0, 1]) * 3.6

path = building.download_data(
    'https://www.entsoe.eu/Documents/SDC%20documents/' +
    'SOAF/140602_SOAF%202014_dataset.zip', unzip_file='ScA.xlsx')

xlsx = pd.ExcelFile(path)

df = pd.DataFrame()
for country in countries:
    sheet = pd.read_excel(xlsx, sheet_name=country + ' (new)', header=[0, 1],
                          index_col=0, skiprows=11)
    s = sheet.loc[:, (year, slice(None))].mean(axis=1)
    s.name = country
    df = pd.concat([df, s], axis=1)

df.loc['pumped-storage'] = df.loc['Hydro power (total)', :] - df.loc['of which renewable hydro generation', :]

# create and write dispatchable generators
mapper = {'Biomass': 'biomass',
          'Gas': 'gas',
          'Hard Coal': 'coal',
          'Lignite': 'lignite',
          'Mixed Fuels': 'mixed-fuels',
          'Nuclear Power': 'uranium',
          'Oil': 'oil',
          'of which renewable hydro generation': 'hydro'}

df_dispatchable = df.loc[mapper.keys()]
df_dispatchable.rename(index=mapper, inplace=True)

elements = {}
for c in countries:
    for d in mapper.values():
        element_name = d + '-' + c

        marginal_cost = (
            (c_data.loc[(year, d), 'cost'] +
             c_data.loc[(year, d), 'emission'] *
             c_data.loc[(year, 'co2'), 'cost']) /
            t_data.loc[(year, d), 'electrical-efficiency'])

        installed_capacity = round(df_dispatchable.at[d, c], 4) * 1e3  # GW->MW

        if installed_capacity > 1:
            element = {
                'capacity': installed_capacity,
                'bus': c + '-electricity',
                'marginal_cost': marginal_cost,
                'type': 'generator',
                'tech': d}
            elements[element_name] = element

path = building.write_elements('dispatchable-generators.csv',
                        pd.DataFrame.from_dict(elements, orient='index'))
create_resource(path)

# create and write volatile generators
mapper = {'Solar': 'solar',
          'of which offshore': 'wind-offshore',
          'of which onshore': 'wind-onshore'}

df_volatile = df.loc[mapper.keys()]
df_volatile.rename(index=mapper, inplace=True)

elements = {}
for c in countries:
    for d in mapper.values():
        element_name = d + '-' + c
        sequence_name = element_name + '-profile'

        installed_capacity = round(df_volatile.at[d, c], 4) * 1e3  # GW->MW

        if installed_capacity > 1:
            element = {
                'capacity': installed_capacity,
                'tech': d,
                'dispatchable': False,
                'profile': sequence_name,
                'type': 'generator',
                'bus': c + '-electricity'}
            elements[element_name] = element

path = building.write_elements(
    'volatile-generators.csv',
    pd.DataFrame.from_dict(elements, orient='index'))
create_resource(path)

# create and write pumped-hydro storages
elements = {}
for c in countries:
    n = 'pumped-storage'
    element_name = n + '-' + c
    installed_capacity = round(df.at[n, c], 4) * 1e3  # GW->MW

    if installed_capacity > 1:
        element = {
            'capacity': installed_capacity * 10,
            'power': installed_capacity,
            'bus': c + '-electricity',
            'marginal_cost': 0,
            'type': 'storage',
            'tech': n,
            'efficiency': 0.8,
            'loss': 0
            }
        elements[element_name] = element

path = building.write_elements('pumped-storage.csv',
                        pd.DataFrame.from_dict(elements, orient='index'))
create_resource(path)
