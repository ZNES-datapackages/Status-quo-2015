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

c_data = pd.read_csv('archive/literature-values.csv', sep=';', index_col=[0, 1, 2])


naming = {'Luxembourg': 'LU', 'Netherlands': 'NL', 'Denmark': 'DK',
        'Sweden': 'SE', 'Poland': 'PL', 'Czechia': 'CZ', 'Austria': 'AT',
        'Norway': 'NO', 'Belgium': 'BE', 'France': 'FR', 'Switzerland': 'CH', 'Germany': 'DE'}


df = pd.read_csv(building.download_data(
    'https://media.githubusercontent.com/media/FRESNA/powerplantmatching/'
    '6378fd03b1ea461fe9c7a5c9c3801c9acbac52c2/data/out/'
    'Matched_CARMA_ENTSOE_GEO_OPSD_WRI_reduced.csv'),
    encoding='utf-8')

idx = ((df['Country'].isin(naming.keys())) & (~df['Fueltype'].isin(['Wind', 'Solar', 'Hydro'])))
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

    element_name = t + '-' + naming[c]

    fuel = 'gas' if 'gas' in t else ('hard_coal' if 'coal' in t else t)

    marginal_cost = (
        (c_data.loc[(year, t, 'variable-cost'), 'value'] +
            c_data.loc[(year, fuel, 'emission-factor'), 'value'] *
            c_data.loc[(year, 'co2', 'cost'), 'value']) /
        c_data.loc[(year, t, 'electrical-efficiency'), 'value'])

    element = {
        'bus': naming[c] + '-electricity',
        'tech': t,
        'carrier': fuel,
        'capacity': capacity,
        'marginal_cost': marginal_cost,
        'type': 'dispatchable'}

    elements[element_name] = element

building.write_elements('dispatchable.csv', pd.DataFrame.from_dict(elements, orient='index'))
