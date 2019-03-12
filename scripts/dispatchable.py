# -*- coding: utf-8 -*-
""" Define dispatchable powerplants for Europe without Germany
"""

import os
import json

import pandas as pd
import numpy as np

from oemof.tabular.datapackage import building
from datapackage import Package
from ast import literal_eval
from shapely.geometry import Point, MultiPoint


def find(g):
    if isinstance(g, dict):
        return find(g.get('OPSD', []))
    return g

config = building.read_build_config('config.toml')
countries, year = config['countries'], config['year']
countries = list(filter(lambda i: i != 'DE', countries))



technologies = pd.DataFrame(
    #Package('/home/planet/data/datapackages/technology-cost/datapackage.json')
    Package('https://raw.githubusercontent.com/ZNES-datapackages/technology-cost/features/add-2015-data/datapackage.json')
    .get_resource('electricity').read(keyed=True)).set_index(
        ['year', 'carrier', 'tech', 'parameter'])

carriers = pd.DataFrame(
    #Package('/home/planet/data/datapackages/technology-cost/datapackage.json')
    Package('https://raw.githubusercontent.com/ZNES-datapackages/technology-cost/features/add-2015-data/datapackage.json')
    .get_resource('carrier').read(keyed=True)).set_index(
        ['year', 'carrier', 'parameter', 'unit']).sort_index()

isocodes = dict(pd.DataFrame(
    Package('https://raw.githubusercontent.com/datasets/country-codes/master/datapackage.json')
    .get_resource('country-codes').read(keyed=True))
    [['ISO3166-1-Alpha-2', 'official_name_en']].values)

isocodes['CZ'] = 'Czech Republic'
isocodes['GB'] = 'United Kingdom'

df = pd.read_csv(building.download_data(
    'https://media.githubusercontent.com/media/FRESNA/powerplantmatching/master/data/out/default/powerplants.csv'),
    encoding='utf-8', converters={'projectID': literal_eval})

df['Country'] = df['Country'].map({y:x for x, y in isocodes.items()})

cond1 = df['Fueltype'].isin(['Wind', 'Solar', 'Hydro', 'Geothermal'])
cond2 = (df['Fueltype'] == 'Natural Gas') & df['Technology'].isin(['Pv', 'Storage Technologies', 'Caes'])
cond3 = (df['Fueltype'] == 'Other') & (df['Technology'] == 'Storage Technologies')
cond4 = (df['Fueltype'] == 'Bioenergy') & (df['Technology'] == 'Pv')
cond5 = df['Country'].isin(countries)

df = df.loc[~cond1 & ~cond2 & ~cond3 & ~cond4 & cond5, :].copy()

df.fillna({'Technology': 'Unknown'}, inplace=True)

# Other
mapper = {('Bioenergy', 'Steam Turbine'): ('biomass', 'biomass'),
          ('Bioenergy', 'Unknown'): ('biomass', 'biomass'),
          ('Bioenergy', 'CCGT'): ('biomass', 'biomass'),
          ('Hard Coal', 'CCGT'): ('coal', 'ccgt'),
          ('Hard Coal', 'Steam Turbine'): ('coal', 'st'),
          ('Hard Coal', 'Unknown'): ('coal', 'st'),
          ('Lignite', 'Steam Turbine'): ('lignite', 'boa'),
          ('Lignite', 'Unknown'): ('lignite', 'boa'),
          ('Natural Gas', 'CCGT'): ('gas', 'ccgt'),
          ('Natural Gas', 'CCGT, Thermal'): ('gas', 'ccgt'),
          ('Natural Gas', 'OCGT'): ('gas', 'ocgt'),
          ('Natural Gas', 'Steam Turbine'): ('gas', 'st'),
          ('Natural Gas', 'Unknown'): ('gas', 'ccgt'),
          ('Other', 'CCGT'): ('gas', 'ccgt'),
          ('Nuclear', 'Unknown'): ('uranium', 'st'),
          ('Nuclear', 'Steam Turbine'): ('uranium', 'st'),
          ('Oil', 'CCGT'): ('oil', 'st'),
          ('Oil', 'OCGT'): ('oil', 'st'),
          ('Oil', 'Steam Turbine'): ('oil', 'st'),
          ('Oil', 'Unknown'): ('oil', 'st'),
          ('Other', 'Unknown'): ('waste', 'chp'),
          ('Other', 'Steam Turbine'): ('waste', 'chp'),
          ('Waste', 'Steam Turbine'): ('waste', 'chp'),
          ('Waste', 'CCGT'): ('waste', 'chp'),
          ('Waste', 'Unknown'): ('waste', 'chp')}


df['carrier'], df['tech'] = zip(*[mapper[tuple(i)] for i in df[['Fueltype', 'Technology']].values])
df['Point'] = df[['lon', 'lat']].apply(lambda x: Point(x), axis=1)


methods = {'Capacity': sum,
           'Point': lambda x: MultiPoint(list(x)).centroid}
s = df.groupby(['Country', 'carrier', 'tech']).agg(methods)

elements = {}
geometry = {}

co2 = carriers.at[(year, 'co2', 'cost', 'EUR/t'), 'value']

# energy availability factor
eaf = pd.read_csv(
    os.path.join(
        config['directories']['archive'], 'literature-values.csv'),
    index_col=['year', 'country', 'carrier', 'technology', 'parameter']).\
    loc[pd.IndexSlice[year, np.nan, np.nan, np.nan, 'eaf'], 'value']

for (country, carrier, tech), row in s.iterrows():
    capacity, geom = row.values
    name = country + '-' + carrier + '-' + tech

    vom = technologies.at[(year, carrier, tech, 'vom'), 'value']
    eta = technologies.at[(year, carrier, tech, 'efficiency'), 'value']
    ef = carriers.at[(year, carrier, 'emission-factor', 't (CO2)/MWh'), 'value']
    fuel = carriers.at[(year, carrier, 'cost', 'EUR/MWh'), 'value']

    marginal_cost = (fuel + vom + co2 * ef) / eta

    geometry[name] = geom

    element = {
        'bus': country + '-electricity',
        'tech': tech,
        'carrier': carrier,
        'capacity': capacity,
        'marginal_cost': float(marginal_cost),
        'output_parameters': json.dumps(
            {'max': eaf, 'emission_factor': float(ef / eta)}),
        'type': 'dispatchable'}

    elements[name] = element

building.write_geometries('dispatchable.geojson', pd.Series(
    list(geometry.values()), index=geometry.keys()))
building.write_elements('dispatchable.csv', pd.DataFrame.from_dict(elements, orient='index'))
