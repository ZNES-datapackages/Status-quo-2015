"""


How to use atlite to return hydro inflow data for europe as seen on
https://github.com/FRESNA/vresutils/blob/master/vresutils/hydro.py!! Thanks
for sharing!
"""

import os
import math

import pandas as pd

from datapackage import Package, Resource
from datapackage_utilities import building


def is_leap_and_Feb29(s):
    """ Adapted from: https://stackoverflow.com/questions/34966422/remove-leap-year-day-from-pandas-dataframe
    """
    return (
        (s.index.is_leap_year) &
        (s.index.month == 2) &
        (s.index.day == 29))


def get_hydro_inflow(countries, inflow_dir=None):
    """ Return hydro inflow data for given countries. [GWh]

    Notes
    -----
    Copied and adapted from: https://github.com/FRESNA/vresutils,
    Copyright 2015-2017 Frankfurt Institute for Advanced Studies
    """

    def read_inflow(country):
        return (pd.read_csv(os.path.join(inflow_dir,
                                         'Hydro_Inflow_{}.csv'.format(country)),
                            parse_dates={'time': [0,1,2]})
                .set_index('time')['Inflow [GWh]'])

    hyd = pd.DataFrame({cname: read_inflow(cname) for cname in countries})

    hyd.columns.name = 'countries'

    hydro = hyd.resample('H').interpolate('cubic')

    if True: #default norm
        normalization_factor = (hydro.index.size/float(hyd.index.size)) #normalize to new sampling frequency
    else:
        normalization_factor = hydro.sum() / hyd.sum() #conserve total inflow for each country separately
    hydro /= normalization_factor

    return hydro


def create_elements_resource(path):
    """
    """
    resource = Resource({'path': path})
    resource.infer()
    resource.descriptor['schema']['primaryKey'] = 'name'
    resource.descriptor['description'] = 'Installed capacities, costs and technical parameters for hydro components'
    resource.descriptor['title'] = '{} components'.format(resource.name.title())
    resource.descriptor['sources'] = [
        {
            'title': 'NUTS Shapefiles',
            'path': 'http://ec.europa.eu/eurostat/cache/GISCO/geodatafiles/NUTS_2013_10M_SH.zip',
            'files': ['NUTS_2013_10M_SH/data/NUTS_RG_10M_2013.shp', 'NUTS_2013_10M_SH/data/NUTS_RG_10M_2013.dbf']
        },
        {
            'title': 'country-codes datapackage',
            'path': 'https://github.com/datasets/country-codes'
        },
        {
            'tite': 'Hydro Energy Inflow for Power System Studies',
            'path': 'Alexander Kies, Lueder von Bremen, & Detlev Heinemann. (2017). Hydro Energy Inflow for Power System Studies [Data set]. Zenodo. http://doi.org/10.5281/zenodo.804244'
        },
        {
            'title': 'International Energy Statistics',
            'path': 'https://www.eia.gov/beta/international/data/browser/#/?pa=000000000000000000000000000000g&c=00280008002gg0040000000000400000gg0004000008&ct=0&ug=8&tl_type=a&tl_id=12-A&vs=INTL.33-12-AUT-BKWH.A&vo=0&v=H&start=2011&end=2015&s=INTL.33-12-DEU-BKWH.A',
            'files': ['EIA-annual-hydro-generation.csv']
        }]

    resource.descriptor['schema']['foreignKeys'] = [{
        "fields": "bus",
        "reference": {
            "resource": "bus",
            "fields": "name"}}]

    if 'run-of-river' in resource.name:
        resource.descriptor['schema']['foreignKeys'].append({
            "fields": "profile",
            "reference": {
                "resource": "hydro-profiles"}})

    if 'reservoir' in resource.name:
        resource.descriptor['schema']['foreignKeys'].append({
            "fields": "inflow",
            "reference": {
                "resource": "hydro-profiles"}})

    resource.commit()

    if resource.valid:
        resource.save('resources/' + resource.name + '.json')
    else:
        print('Resource is not valid, writing resource anyway...')
        resource.save('resources/' + resource.name + '.json')


def create_sequences_resource(path):

    resource = Resource({'path': path})
    resource.infer()
    resource.descriptor['schema']['primaryKey'] = 'timeindex'
    resource.descriptor['description'] = 'Hydro inflow profiles based on run-off data normalized by EIA statistics'
    resource.descriptor['title'] = 'Hydro profiles'
    resource.descriptor['sources'] = [
        {
            'title': 'International Energy Statistics',
            'path': 'https://www.eia.gov/beta/international/data/browser/#/?pa=000000000000000000000000000000g&c=00280008002gg0040000000000400000gg0004000008&ct=0&ug=8&tl_type=a&tl_id=12-A&vs=INTL.33-12-AUT-BKWH.A&vo=0&v=H&start=2011&end=2015&s=INTL.33-12-DEU-BKWH.A',
            'files': ['EIA-annual-hydro-generation.csv']
        },
        {
            'title': 'ERA5 data',
            'path': 'https://software.ecmwf.int/wiki/display/CKB/ERA5+data+documentation'
        },
        {
            'tite': 'Hydro Energy Inflow for Power System Studies',
            'path': 'Alexander Kies, Lueder von Bremen, & Detlev Heinemann. (2017). Hydro Energy Inflow for Power System Studies [Data set]. Zenodo. http://doi.org/10.5281/zenodo.804244'
        }]


    resource.commit()

    resource.save('resources/' + resource.name + '.json')


config = building.get_config()
countries, year = config['countries'], config['year']

# load archive files
c_data = pd.read_csv('archive/cost.csv', sep=';', index_col=[0, 1, 2])
capas = pd.read_csv('archive/capacities.csv', sep=';', index_col=[0, 1, 2])

# download country-codes datapackage
# TODO: retrieve from archive
country_naming = pd.DataFrame(
    Package(
        'https://raw.githubusercontent.com/datasets/country-codes/5b645f4ea861be1362539d06641e5614353c9895/datapackage.json'
        ).get_resource('country-codes').read(keyed=True))

country_naming.set_index(['official_name_en'], inplace=True)
name_to_isocode = country_naming['ISO3166-1-Alpha-2'].to_dict()

# EIA hydro electricity generation 2015
hydro_total = pd.read_csv(
        os.path.join(
            config['directories']['archive'],
            'EIA-annual-hydro-generation.csv'),
        skiprows=4, index_col=1
    ).drop(['Unnamed: 0', 'Unnamed: 2'], axis=1).dropna().loc[:, str(year)]

hydro_total = hydro_total.rename(index={'Czech Republic': 'Czechia'}).\
    rename(index=name_to_isocode).T
hydro_total *= 1e6  # billion kWh -> MWh

# reservoir capacity, hydro capacity, pumped hydro capacity for Europe
# http://doi.org/10.5281/zenodo.804244
# TODO: replace with Status quo hydro capacities?
hydro_capas = pd.read_csv(
    building.download_data(
        'https://zenodo.org/record/804244/files/hydropower.csv?download=1'
    ), index_col=['ctrcode'])

_swiss_capas = capas.loc[(
    2015, 'CH', ['reservoir', 'hydro', 'pumped-storage']), :].value

hydro_capas = hydro_capas.append(
    pd.Series(dict(zip(hydro_capas.columns, _swiss_capas)), name='CH'))

# remove countries w/o hydro capacities
countries = [c for c in countries if ~(hydro_capas == 0.0).all(axis=1)[c]]

# http://doi.org/10.5281/zenodo.804244
run_of_river_shares = pd.read_csv(
    building.download_data(
        'https://zenodo.org/record/804244/files/'
        'Run-Of-River%20Shares.csv?download=1'
    ), index_col=['ctrcode'])

# Inflow timeseries 2003-2012
# http://doi.org/10.5281/zenodo.804244
hyd_inflow = (get_hydro_inflow(
    [c for c in countries if c != 'LU'],
    building.download_data(
        'https://zenodo.org/record/804244/files/Hydro_Inflow.zip?download=1',
        unzip_file='Hydro_Inflow/')))

# remove leap year hours
hyd_inflow = hyd_inflow[~is_leap_and_Feb29(hyd_inflow)]

# TODO: normalization already occours in get_hydro_inflow
# mean hourly value
idx = hyd_inflow.index
inflow_timeseries = hyd_inflow.groupby([idx.month, idx.day, idx.hour]).mean()

# assume Belgian inflow curve for Luxembourg
inflow_timeseries['LU'] = inflow_timeseries['BE'].copy()

inflow_timeseries.index = pd.date_range(
    '2015-01-01 00:00:00', '2015-12-31 23:00:00', freq='H')

# normalize with hydro total electricity generation
inflow_timeseries = (
        inflow_timeseries * hydro_total / inflow_timeseries.sum()).\
    dropna(axis=1)

# run-of-river
elements = {}
sequences = pd.DataFrame(index=building.timeindex())

for c in countries:
    element_name = 'run-of-river-' + c
    sequence_name = 'run-of-river-' + c + '-profile'

    installed_capacity = \
        hydro_capas.at[c, ' installed hydro capacities [GW]'] \
        * run_of_river_shares.at[c, 'run-of-river share'] * 1e3  # GW -> MW

    inflow = inflow_timeseries[c].values \
        * run_of_river_shares.at[c, 'run-of-river share'] \
        / installed_capacity

    inflow[inflow > 1] = 1  # assume runoff spillage

    if installed_capacity > 1:
        element = {
            'capacity': installed_capacity,
            'bus': c + '-electricity',
            'marginal_cost': 0,
            'dispatchable': False,
            'profile': sequence_name,
            'type': 'runofriver',
            'tech': 'run-of-river'}
        elements[element_name] = element
        sequences[sequence_name] = inflow

path = building.write_elements(
    'run-of-river.csv', pd.DataFrame.from_dict(elements, orient='index'))
create_elements_resource(path)

path = building.write_sequences('hydro-profiles.csv', sequences)
create_sequences_resource(path)

# reservoir
elements = {}
sequences = pd.DataFrame(index=building.timeindex())

for c in countries:
    element_name = 'reservoir-' + c
    sequence_name = 'reservoir-' + c + '-profile'

    # TODO: check efficiency
    installed_capacity = \
        hydro_capas.at[c, ' installed hydro capacities [GW]'] \
        * (1 - run_of_river_shares.at[c, 'run-of-river share']) * 1e3  # GW -> MW

    inflow = inflow_timeseries[c].values \
        * (1 - run_of_river_shares.at[c, 'run-of-river share'])

    if installed_capacity > 1:
        element = {
            'bus': c + '-electricity',
            'capacity': hydro_capas.at[c, ' reservoir capacity [TWh]'] * 1e6,  # TWh -> MWh
            'power': installed_capacity,
            'inflow': sequence_name,
            'type': 'reservoir',
            'tech': 'reservoir'}
        elements[element_name] = element
        sequences[sequence_name] = inflow

path = building.write_elements(
    'reservoir.csv', pd.DataFrame.from_dict(elements, orient='index'))
create_elements_resource(path)

path = building.write_sequences('hydro-profiles.csv', sequences)
create_sequences_resource(path)

# pumped-storage
elements = {}
sequences = pd.DataFrame(index=building.timeindex())

round_trip_eta = c_data.loc[(
    slice(None), 'pumped-storage', 'electrical-efficiency (round trip)'), :].\
    value

for c in countries:
    element_name = 'pumped-storage-' + c

    # TODO: check efficiency
    installed_capacity = \
        hydro_capas.at[c, ' installed pumped hydro capacities [GW]'] * 1e3  # GW -> MW

    if installed_capacity > 1:
        element = {
            'bus': c + '-electricity',
            'capacity': installed_capacity * 10,
            'p_max': installed_capacity,
            'p_min': 0,
            'charging_efficiency': math.sqrt(round_trip_eta),
            'discharging_efficiency': math.sqrt(round_trip_eta),
            'type': 'storage',
            'tech': 'pumped-storage'}
        elements[element_name] = element

path = building.write_elements(
    'pumped-storage.csv', pd.DataFrame.from_dict(elements, orient='index'))
create_elements_resource(path)
