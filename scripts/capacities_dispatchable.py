# -*- coding: utf-8 -*-
"""
"""

import pandas as pd

from datapackage_utilities import building
from datapackage import Package

def create_resource(path):

    from datapackage import Resource
    resource = Resource({'path': path})
    resource.infer()
    resource.descriptor['schema']['primaryKey'] = 'name'
    resource.descriptor['description'] = 'Installed capacities, costs and technical parameters for dispatchable generators'
    resource.descriptor['title'] = '{} components'.format(resource.name.title())
    resource.descriptor['sources'] = [
        {
            'title': 'powerplantmatching',
            'path': 'https://github.com/FRESNA/powerplantmatching',
            'files': ['Matched_CARMA_ENTSOE_GEO_OPSD_WRI_reduced.csv']
        },
        {
            'title': 'Current and Prospective Costs of Electricity Generation until 2050',
            'path': 'https://www.diw.de/documents/publikationen/73/diw_01.c.424566.de/diw_datadoc_2013-068.pdf'
        },
        {
            'title': 'CO2 Emission Factors for Fossil Fuels',
            'path': 'https://www.umweltbundesamt.de/sites/default/files/medien/1968/publikationen/co2_emission_factors_for_fossil_fuels_correction.pdf'
        }]

    resource.descriptor['schema']['foreignKeys'] = [{
        "fields": "bus",
        "reference": {
            "resource": "bus",
            "fields": "name"}}]

    resource.commit()

    if resource.valid:
        resource.save('resources/' + resource.name + '.json')
    else:
        print('Resource is not valid, writing resource anyway...')
        resource.save('resources/' + resource.name + '.json')


config = building.get_config()
countries, year = config['countries'], config['year']

t_data = pd.read_csv('archive/technologies.csv', sep=';', index_col=[0, 1])

c_data = pd.read_csv('archive/commodities.csv', sep=';', index_col=[0, 1])


countrycodes = Package(
        'https://raw.githubusercontent.com/datasets/country-codes/master/datapackage.json').\
        get_resource('country-codes').read(keyed=True)

countrynames = {
        v['official_name_en']: i
        for i in countries
    for v in countrycodes if v['ISO3166-1-Alpha-2'] == i}


# https://github.com/FRESNA/powerplantmatching
path = building.download_data(
    'https://media.githubusercontent.com/media/FRESNA/powerplantmatching/6378fd03b1ea461fe9c7a5c9c3801c9acbac52c2/data/out/Matched_CARMA_ENTSOE_GEO_OPSD_WRI_reduced.csv')


df = pd.read_csv(path, encoding='utf-8')
idx = ((df['Country'].isin(countrynames.keys())) & (~df['Fueltype'].isin(['Wind', 'Solar', 'Hydro'])))
df = df.loc[idx, :]
df['Technology'].fillna('Unknown', inplace=True)
idx = df[((df['Fueltype'] == 'Natural Gas') & (df['Technology'] == 'Storage Technologies'))].index
df.drop(idx, inplace=True)

# Other
mapper = {('Bioenergy', 'Steam Turbine'): 'biomass',
          ('Bioenergy', 'Unknown'): 'biomass',
          ('Hard Coal', 'CCGT'): 'hard_coal_ccgt',
          ('Hard Coal', 'Steam Turbine'): 'hard_coal_st',
          ('Hard Coal', 'Unknown'): 'hard_coal_st',
          ('Lignite', 'Steam Turbine'): 'lignite',
          ('Natural Gas', 'CCGT'): 'gas_ccgt',
          ('Natural Gas', 'OCGT'): 'gas_ocgt',
          ('Natural Gas', 'Steam Turbine'): 'gas_st',
          ('Natural Gas', 'Unknown'): 'gas_ccgt',
          ('Nuclear', 'Unknown'): 'nuclear',
          ('Nuclear', 'Steam Turbine'): 'nuclear',
          ('Natural Gas', 'Steam Turbine'): 'nuclear',
          ('Oil', 'CCGT'): 'oil',
          ('Oil', 'OCGT'): 'oil',
          ('Oil', 'Steam Turbine'): 'oil',
          ('Oil', 'Unknown'): 'oil',
          ('Other', 'Unknown'): 'waste',
          ('Waste', 'Steam Turbine'): 'waste'}

df.loc[:, 'Technology'] = [mapper[tuple(i)] for i in df[['Fueltype', 'Technology']].values]

s = df.groupby(['Country', 'Technology'])['Capacity'].sum()

elements = {}

for (c, t), capacity in s.iteritems():

    element_name = t + '-' + countrynames[c]

    fuel = 'gas' if 'gas' in t else ('hard_coal' if 'coal' in t else t)

    marginal_cost = (
        (c_data.loc[(year, fuel), 'cost'] +
            c_data.loc[(year, fuel), 'emission'] *
            c_data.loc[(year, 'co2'), 'cost']) /
        t_data.loc[(year, t), 'electrical-efficiency'])

    element = {
        'capacity': capacity,
        'bus': countrynames[c] + '-electricity',
        'marginal_cost': marginal_cost,
        'type': 'generator',
        'tech': t}

    elements[element_name] = element

path = building.write_elements('dispatchable-generator.csv',
                        pd.DataFrame.from_dict(elements, orient='index'))
create_resource(path)
