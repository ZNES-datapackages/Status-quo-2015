# -*- coding: utf-8 -*-
"""

Current and Prospective Costs of Electricity Generation until 2050
https://www.diw.de/documents/publikationen/73/diw_01.c.424566.de/diw_datadoc_2013-068.pdf

powerplantmatching
https://github.com/FRESNA/powerplantmatching
Matched_CARMA_ENTSOE_GEO_OPSD_WRI_reduced.csv

CO2 Emission Factors for Fossil Fuels
https://www.umweltbundesamt.de/sites/default/files/medien/1968/publikationen/co2_emission_factors_for_fossil_fuels_correction.pdf'

"""

import pandas as pd

from datapackage_utilities import building
from datapackage import Package


config = building.get_config()
countries, year = config['countries'], config['year']

technologies = pd.DataFrame(
    Package('https://raw.githubusercontent.com/ZNES-datapackages/technology-cost/features/add-2015-data/datapackage.json')
    .get_resource('electricity').read(keyed=True)).set_index(
        ['year', 'carrier', 'tech', 'parameter'])

carriers = pd.DataFrame(
    Package('https://raw.githubusercontent.com/ZNES-datapackages/technology-cost/features/add-2015-data/datapackage.json')
    .get_resource('carrier').read(keyed=True)).set_index(
        ['year', 'carrier', 'parameter']).sort_index()

isocodes = dict(pd.DataFrame(
    Package('https://raw.githubusercontent.com/datasets/country-codes/master/datapackage.json')
    .get_resource('country-codes').read(keyed=True))
    [['ISO3166-1-Alpha-2', 'official_name_en']].values)

isocodes['CZ'] = 'Czech Republic'
isocodes['GB'] = 'United Kingdom'

df = pd.read_csv(building.download_data(
    'https://media.githubusercontent.com/media/FRESNA/powerplantmatching/'
    '6378fd03b1ea461fe9c7a5c9c3801c9acbac52c2/data/out/'
    'Matched_CARMA_ENTSOE_GEO_OPSD_WRI_reduced.csv'),
    encoding='utf-8')

df['Country'] = df['Country'].map({y:x for x, y in isocodes.items()})


idx = ((df['Country'].isin(countries)) & (~df['Fueltype'].isin(['Wind', 'Solar', 'Hydro'])))

df = df.loc[idx, :].copy()

df.fillna({'Technology': 'Unknown'}, inplace=True)

idx = df[((df['Fueltype'] == 'Natural Gas') & (df['Technology'] == 'Storage Technologies'))].index

df.drop(idx, inplace=True)

# Other
mapper = {('Bioenergy', 'Steam Turbine'): ('bio', 'biomass'),
          ('Bioenergy', 'Unknown'): ('bio', 'biomass'),
          ('Hard Coal', 'CCGT'): ('coal', 'ccgt'),
          ('Hard Coal', 'Steam Turbine'): ('coal', 'st'),
          ('Hard Coal', 'Unknown'): ('coal', 'st'),
          ('Lignite', 'Steam Turbine'): ('lignite', 'boa'),
          ('Natural Gas', 'CCGT'): ('gas', 'ccgt'),
          ('Natural Gas', 'OCGT'): ('gas', 'ocgt'),
          ('Natural Gas', 'Steam Turbine'): ('gas', 'st'),
          ('Natural Gas', 'Unknown'): ('gas', 'ccgt'),
          ('Nuclear', 'Unknown'): ('uranium', 'st'),
          ('Nuclear', 'Steam Turbine'): ('uranium', 'st'),
          ('Oil', 'CCGT'): ('oil', 'st'),
          ('Oil', 'OCGT'): ('oil', 'st'),
          ('Oil', 'Steam Turbine'): ('oil', 'st'),
          ('Oil', 'Unknown'): ('oil', 'st'),
          ('Other', 'Unknown'): ('waste', 'chp'),
          ('Waste', 'Steam Turbine'): ('waste', 'chp')}


df['carrier'], df['tech'] = zip(*[mapper[tuple(i)] for i in df[['Fueltype', 'Technology']].values])

s = df.groupby(['Country', 'carrier', 'tech'])['Capacity'].sum()

elements = {}

co2 = carriers.at[(year, 'co2', 'cost'), 'value']

for (country, carrier, tech), capacity in s.iteritems():
    name = country + '-' + carrier + '-' + tech

    vom = technologies.at[(year, carrier, tech, 'vom'), 'value']
    eta = technologies.at[(year, carrier, tech, 'efficiency'), 'value']
    ef = carriers.at[(year, carrier, 'emission-factor'), 'value']

    marginal_cost = (vom + co2 * ef) / eta

    element = {
        'bus': country + '-electricity',
        'tech': tech,
        'carrier': carrier,
        'capacity': capacity,
        'marginal_cost': marginal_cost,
        'type': 'dispatchable'}

    elements[name] = element


building.write_elements('dispatchable.csv', pd.DataFrame.from_dict(elements, orient='index'))
