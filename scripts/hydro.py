""" Creating elements and sequences for hydro generation facilities reservoir,
runofriver and pumped-hydro-storage.
"""

import os

import pandas as pd

from datapackage import Package
from oemof.tabular.datapackage import building
from oemof.tabular.tools import geometry

from atlite import Cutout


config = building.read_build_config('config.toml')
countries, year = config['countries'], config['year']
filepath = building.download_data(
    'http://ec.europa.eu/eurostat/cache/GISCO/geodatafiles/'
    'NUTS_2013_10M_SH.zip',
    unzip_file='NUTS_2013_10M_SH/data/NUTS_RG_10M_2013.shp')

nuts0 = pd.Series(geometry.nuts(filepath, nuts=0, tolerance=0.1))[countries]


countrynames = pd.DataFrame(Package(
    'https://raw.githubusercontent.com/datasets/country-codes/5b645f4ea861be1362539d06641e5614353c9895/datapackage.json'
    ).get_resource('country-codes').read(keyed=True)).set_index(['official_name_en'])\
    ['ISO3166-1-Alpha-2'].to_dict()

hyd = pd.read_csv(os.path.join( config['directories']['archive'], 'EIA-annual-hydro-generation.csv'),
        skiprows=4, index_col=1
    ).drop(['Unnamed: 0', 'Unnamed: 2'], axis=1).dropna().loc[:, str(year)]
hyd = hyd.rename(index={'Czech Republic': 'Czechia'}).\
    rename(index=countrynames).T
hyd *= 1e3  # billion kWh -> MWh


path = building.download_data('sftp://5.35.252.104/home/rutherford/atlite/cutouts/eu-2015.zip',
                              username='rutherford', unzip_file='eu-2015/')
inflows = Cutout(cutout_dir='cache/eu-2015', name='eu-2015').\
    runoff(shapes=nuts0).to_pandas().T

inflows = inflows * (hyd / inflows.sum())

technologies = pd.DataFrame(
    Package('https://raw.githubusercontent.com/ZNES-datapackages/technology-cost/features/add-2015-data/datapackage.json')
    .get_resource('electricity').read(keyed=True)).set_index(
        ['year', 'carrier', 'tech', 'parameter'])

ror_shares = pd.read_csv(
    os.path.join(
        config['directories']['archive'], 'ror_ENTSOe_Restore2050.csv'),
    index_col='Country Code (ISO 3166-1)')['ror ENTSO-E\n+ Restore']

capacities = pd.read_csv(building.download_data(
    'https://zenodo.org/record/804244/files/hydropower.csv?download=1'),
    index_col=['ctrcode'])

capacities.loc['CH'] = [8.8, 12, 1.9]  # add CH elsewhere

# https://zenodo.org/record/804244 data handling
capacities['hyd_wo_phs'] = (capacities[' installed hydro capacities [GW]'] - capacities[' installed pumped hydro capacities [GW]']) * 1000 # MW
capacities['phs_power'] = capacities[' installed pumped hydro capacities [GW]'] * 1000 # MWh
capacities['ror_power'] = capacities['hyd_wo_phs'] * ror_shares
capacities['rsv_power'] = capacities['hyd_wo_phs'] * (1 - ror_shares)
capacities['rsv_capacity'] = capacities[' reservoir capacity [TWh]'] * 1e6 # MWh

# ror
elements = {}
for country in countries:
    name = country + '-ror'

    capacity = capacities.loc[country, 'ror_power']

    eta = technologies.loc[(year, 'hydro', 'ror', 'efficiency'), 'value']

    if capacity > 0:

        elements[name] = {
            'type': 'volatile',
            'tech': 'ror',
            'carrier': 'hydro',
            'bus': country + '-electricity',
            'capacity': capacity,
            'profile': country + '-ror-profile',
            'efficiency': eta
            }

building.write_elements(
    'ror.csv', pd.DataFrame.from_dict(elements, orient='index'))

sequences = (inflows * ror_shares * 1000) / capacities['ror_power']
sequences = sequences[countries].copy()
sequences.dropna(axis=1, inplace=True)
sequences.columns = sequences.columns.astype(str) + '-ror-profile'


building.write_sequences(
    'ror_profile.csv', sequences.set_index(building.timeindex(str(year))))

# reservoir
elements = {}
for country in countries:
    name = country + '-reservoir'

    capacity = capacities.loc[country, 'rsv_power']

    eta = technologies.loc[(year, 'hydro', 'reservoir', 'efficiency'), 'value']

    if capacity > 0:

        elements[name] = {
            'type': 'reservoir',
            'tech': 'reservoir',
            'carrier': 'hydro',
            'bus': country + '-electricity',
            'capacity': capacity,
            'storage_capacity': capacities.loc[country, 'rsv_capacity'],
            'profile': country + '-reservoir-profile',
            'efficiency': eta,
            'marginal_cost': 0.00000001
            }

building.write_elements(
    'reservoir.csv', pd.DataFrame.from_dict(elements, orient='index'))

sequences = inflows * (1 - ror_shares) * 1000
sequences = sequences[countries].copy()
sequences.dropna(axis=1, inplace=True)
sequences.columns = sequences.columns.astype(str) + '-reservoir-profile'
building.write_sequences(
    'reservoir_profile.csv', sequences.set_index(building.timeindex(str(year))))

# phs
elements = {}
for country in countries:
    name = country + '-phs'

    capacity = capacities.loc[country, 'phs_power']

    eta = technologies.loc[(year, 'hydro', 'phs', 'efficiency'), 'value']

    if capacity > 0:

        elements[name] = {
            'type': 'storage',
            'tech': 'phs',
            'carrier': 'hydro',
            'bus': country + '-electricity',
            'capacity': capacity,
            'loss': 0,
            'marginal_cost': 0.0000001,
            'storage_capacity': capacity * 6,  # max hours # Brown et al.
            'storage_capacity_inital': 0.5,
            'efficiency': eta
            }

building.write_elements(
    'phs.csv', pd.DataFrame.from_dict(elements, orient='index'))
