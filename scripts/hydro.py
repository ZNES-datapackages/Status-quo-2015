""" Creating elements and sequences for hydro generation facilities reservoir,
runofriver and pumped-hydro-storage.
"""

import os

import pandas as pd

from datapackage import Package
from oemof.tabular.datapackage import building

def get_hydro_inflow(inflow_dir=None):
    """ Adapted from https://github.com/FRESNA/vresutils/blob/master/vresutils/hydro.py
    """

    def read_inflow(country):
        return (pd.read_csv(os.path.join(inflow_dir,
                                         'Hydro_Inflow_{}.csv'.format(country)),
                            parse_dates={'date': [0,1,2]})
                .set_index('date')['Inflow [GWh]'])

    europe = ['AT','BA','BE','BG','CH','CZ','DE',
              'ES','FI','FR','HR','HU','IE','IT','KV',
              'LT','LV','ME','MK','NL','NO','PL','PT',
              'RO','RS','SE','SI','SK']

    hyd = pd.DataFrame({cname: read_inflow(cname) for cname in europe})

    hydro = hyd.resample('H').interpolate('cubic')

    if True: #default norm
        normalization_factor = (hydro.index.size/float(hyd.index.size)) #normalize to new sampling frequency
    else:
        normalization_factor = hydro.sum() / hyd.sum() #conserve total inflow for each country separately
    hydro /= normalization_factor
    return hydro


config = building.get_config()
countries, year = config['countries'], config['year']

inflows = (get_hydro_inflow(building.download_data(
        'https://zenodo.org/record/804244/files/Hydro_Inflow.zip?download=1',
        unzip_file='Hydro_Inflow/')))

inflows = inflows.loc[inflows.index.year == 2011, :].copy()
inflows['DK'], inflows['LU'] = 0, inflows['BE']

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
    'ror_profile.csv', sequences.set_index(building.timeindex()))

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
            'efficiency': eta
            }

building.write_elements(
    'reservoir.csv', pd.DataFrame.from_dict(elements, orient='index'))

sequences = inflows * (1 - ror_shares) * 1000
sequences = sequences[countries].copy()
sequences.dropna(axis=1, inplace=True)
sequences.columns = sequences.columns.astype(str) + '-reservoir-profile'
building.write_sequences(
    'reservoir_profile.csv', sequences.set_index(building.timeindex()))

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
            'storage_capacity': capacity * 6, # max hours # Brown et al.
            'storage_capacity_inital': 0.5,
            'efficiency': eta
            }

building.write_elements(
    'phs.csv', pd.DataFrame.from_dict(elements, orient='index'))
