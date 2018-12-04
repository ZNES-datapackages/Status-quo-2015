"""
"""

import os

import pandas as pd

from datapackage import Package
from datapackage_utilities import building

from oemof.tools.economics import annuity

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
countries, year = config['regions'], config['year']

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

capacities['hyd_wo_phs'] = (capacities[' installed hydro capacities [GW]'] - capacities[' installed pumped hydro capacities [GW]']) * 1000 # MW
capacities['ror_power'] = capacities['hyd_wo_phs'] * ror_shares
capacities['rsv_power'] = capacities['hyd_wo_phs'] * (1 - ror_shares)
capacities['rsv_capacity'] = capacities[' reservoir capacity [TWh]'] * 1e6 # MWh

elements = {}
for country in countries:
    name = country + '-ror'

    capacity = capacities.loc[country, 'ror_power']

    eta = technologies.loc[(year, 'hydro', 'ror', 'efficiency'), 'value']

    if capacity > 0:

        elements[name] = {'type': 'volatile',
        'tech': 'ror',
        'carrier': 'hydro',
        'bus': country + '-electricity',
        'capacity': capacity,
        'profile': country + '-ror-profile',
        'efficiency': eta
        }


sequences = (inflows * ror_shares * 1000) / capacities['ror_power']
sequences.columns = sequences.columns.astype(str) + '-ror-profile'
building.write_sequences(
    'ror_profile.csv', sequences.set_index(building.timeindex()))

for country in countries:
    name = country + 'reservoir'

# phs
phs = pd.DataFrame(index=countries)
phs['type'], phs['tech'], phs['bus'], phs['loss'], phs['capacity'] = \
    'storage', \
    'phs', \
    phs.index.astype(str) + '-electricity', \
    0, \
    capacities.loc[phs.index, ' installed pumped hydro capacities [GW]'] * 1000

phs['storage_capacity'] = phs['capacity'] * 6  # Brown et al.
# as efficieny in data is roundtrip use sqrt of roundtrip
phs['efficiency'] = float(technologies['phs']['efficiency'])**0.5
phs = phs.assign(**technologies['phs'])[phs['capacity'] > 0].dropna()


# other hydro / reservoir
rsv = pd.DataFrame(index=countries)
rsv['type'], rsv['tech'], rsv['bus'], rsv['loss'], rsv['capacity'], rsv['storage_capacity'] = \
    'reservoir', \
    'reservoir', \
    rsv.index.astype(str) + '-electricity', \
    0, \
    (capacities.loc[ror.index, ' installed hydro capacities [GW]'] -
    capacities.loc[ror.index, ' installed pumped hydro capacities [GW]']) * (1 - ror_shares[ror.index]) * 1000, \
    capacities.loc[rsv.index, ' reservoir capacity [TWh]'] * 1e6  # to MWh

rsv = rsv.assign(**technologies['reservoir'])[rsv['capacity'] > 0].dropna()
rsv['profile'] = rsv['tech'] + '-' + rsv['bus'] + '-profile'

rsv_sequences = inflows[rsv.index] * (1 - ror_shares[rsv.index]) * 1000 # GWh -> MWh
rsv_sequences.columns = rsv_sequences.columns.map(rsv['profile'])

# write sequences to different files for better automatic foreignKey handling
# in meta data
building.write_sequences(
    'reservoir_profile.csv', rsv_sequences.set_index(building.timeindex()))
building.write_sequences(
    'ror_profile.csv', ror_sequences.set_index(building.timeindex()))

filenames = ['ror.csv', 'phs.csv', 'reservoir.csv']

for fn, df in zip(filenames, [ror, phs, rsv]):
    df.index = df.index.astype(str) + '_' + df['tech']
    df['capacity_cost'] = df.apply(
        lambda x: annuity(float(x['capacity_cost']) * 1000,
                      float(x['lifetime']),
                      config['wacc']), axis=1)
    building.write_elements(fn, df)
