"""


How to use atlite to return hydro inflow data for europe as seen on
https://github.com/FRESNA/vresutils/blob/master/vresutils/hydro.py!! Thanks
for sharing!
"""

import os
import atlite
import math

import pandas as pd

from datapackage import Package, Resource
from datapackage_utilities import building, geometry


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

c_data = pd.read_csv('archive/cost.csv', sep=';', index_col=[0, 1, 2])
capas = pd.read_csv('archive/capacities.csv', sep=';', index_col=[0, 1, 2])

country_naming = pd.DataFrame(
    Package(
        'https://raw.githubusercontent.com/datasets/country-codes/5b645f4ea861be1362539d06641e5614353c9895/datapackage.json'
        ).get_resource('country-codes').read(keyed=True))

country_naming.set_index(['official_name_en'], inplace=True)

name_to_isocode = country_naming['ISO3166-1-Alpha-2'].to_dict()

#
filepath = os.path.join(config['directories']['cache'],
                        'NUTS_2013_10M_SH/data/NUTS_RG_10M_2013.shp')
country_polygons = pd.Series(
    geometry.nuts(filepath, nuts=0)).filter(config['countries'])
country_polygons.index.name = 'countries'

#
hydro_yearly_total = pd.read_csv(
        os.path.join(
            config['directories']['archive'],
            'EIA-annual-hydro-generation.csv'),
        skiprows=4, index_col=1
    ).drop(['Unnamed: 0', 'Unnamed: 2'], axis=1).dropna()

hydro_yearly_total.rename(index={'Czech Republic': 'Czechia'}, inplace=True)
hydro_yearly_total.rename(index=name_to_isocode, inplace=True)

hyrdo_yearly_total = hydro_yearly_total * 1e6  # billion kWh -> MWh
hydro_yearly_total.index.name = 'countries'


building.download_data(
    'sftp://atlite.openmod.net/home/atlite/cutouts/eu-2015.zip', unzip_file='eu-2015/')

hydro_capacities = pd.read_csv(
    building.download_data(
        'https://zenodo.org/record/804244/files/hydropower.csv?download=1'
    ), index_col=['ctrcode'])

swiss_hydro_capacities = capas.loc[(
    2015, 'CH', ['reservoir', 'hydro', 'pumped-storage']), :].value

hydro_capacities = hydro_capacities.append(
    pd.Series(dict(zip(hydro_capacities.columns,
                       swiss_hydro_capacities)), name='CH'))

# remove countries without hydro capacities
countries = [c for c in countries if ~(hydro_capacities == 0.0).all(axis=1)[c]]

run_of_river_shares = pd.read_csv(
    building.download_data(
        'https://zenodo.org/record/804244/files/Run-Of-River%20Shares.csv?download=1'
    ), index_col=['ctrcode'])


cutout = atlite.Cutout(name='eu-2015/eu-2015/', cutout_dir=config['directories']['cache'])

# parametrization as seen on https://github.com/FRESNA/vresutils/blob/master/vresutils/hydro.py
# TODO: this is based on NCEP
inflow_timeseries = cutout.runoff(shapes=country_polygons,
                                  smooth=24,
                                  lower_threshold_quantile=0.01,
                                  normalize_using_yearly=hydro_yearly_total.T)

# run-of-river
elements = {}
sequences = pd.DataFrame(index=building.timeindex())

for c in countries:
    element_name = 'run-of-river-' + c
    sequence_name = 'run-of-river-' + c + '-profile'

    installed_capacity = \
        hydro_capacities.at[c, ' installed hydro capacities [GW]'] \
        * run_of_river_shares.at[c, 'run-of-river share'] * 1e3  # GW -> MW

    inflow = inflow_timeseries.loc[c, :].data \
        * run_of_river_shares.at[c, 'run-of-river share']

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
        hydro_capacities.at[c, ' installed hydro capacities [GW]'] \
        * (1 - run_of_river_shares.at[c, 'run-of-river share']) * 1e3  # GW -> MW

    inflow = inflow_timeseries.loc[c, :].data \
        * (1 - run_of_river_shares.at[c, 'run-of-river share'])

    if installed_capacity > 1:
        element = {
            'bus': c + '-electricity',
            'capacity': hydro_capacities.at[c, ' reservoir capacity [TWh]'] * 1e6,  # TWh -> MWh
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
        hydro_capacities.at[c, ' installed pumped hydro capacities [GW]'] * 1e3  # GW -> MW

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
