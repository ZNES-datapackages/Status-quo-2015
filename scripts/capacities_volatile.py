# -*- coding: utf-8 -*-
"""
"""

import pandas as pd

from datapackage_utilities import building

# TODO: replace EMHIRES (downscaled MERRA data) with ERA-5
# https://www.sciencedirect.com/science/article/pii/S0960148118303677

# TODO: check if timeseries localized


def create_resource(path):
    from datapackage import Resource
    resource = Resource({'path': path})
    resource.infer()
    resource.descriptor['schema']['primaryKey'] = 'timeindex'
    resource.descriptor['description'] = 'EMHIRES capacity factors for wind onshore, offshore and solar power'
    resource.descriptor['title'] = 'Solar and wind profiles'
    resource.descriptor['sources'] = [
        {
            'title': 'Gonzalez Aparicio, Iratxe; Zucker, Andreas; Careri, Francesco; Monforti Ferrario, Fabio; Huld, Thomas; Badger, Jake (2016):  Wind hourly generation time series at country, NUTS 1, NUTS 2 level and bidding zones. European Commission, Joint Research Centre (JRC) [Dataset] PID: http://data.europa.eu/89h/jrc-emhires-wind-generation-time-series',
            'path': 'http://data.jrc.ec.europa.eu/dataset/jrc-emhires-wind-generation-time-series'
        },
        {
            'title': 'Gonzalez Aparicio, Iratxe (2017):  Solar hourly generation time series at country, NUTS 1, NUTS 2 level and bidding zones. European Commission, Joint Research Centre (JRC) [Dataset] PID: http://data.europa.eu/89h/jrc-emhires-solar-generation-time-series',
            'path': 'http://data.jrc.ec.europa.eu/dataset/jrc-emhires-solar-generation-time-series'
        },
        {
            'title': 'EMHIRES datasets',
            'path': 'https://setis.ec.europa.eu/EMHIRES-datasets',
            'files': ['TS_CF_COUNTRY_30yr_date.zip',
                      'TS_CF_OFFSHORE_30yr_date.zip',
                      'EMHIRESPV_country_level.zip']
        }]


    resource.commit()

    if resource.valid:
        resource.save('resources/' + resource.name + '.json')

config = building.get_config()
countries, year = config['countries'], str(config['year'])

sources = [
        (
            'wind-onshore',
            'http://setis.ec.europa.eu/sites/default/files/EMHIRES_DATA/TS_CF_COUNTRY_30yr_date.zip',
            'TS.CF.COUNTRY.30yr.date.txt'
        ),
        (
            'wind-offshore',
            'http://setis.ec.europa.eu/sites/default/files/EMHIRES_DATA/TS_CF_OFFSHORE_30yr_date.zip',
            'TS.CF.OFFSHORE.30yr.date.txt'
        )]

# create wind-onshore / wind-offshore profiles
for tech, filepath, filename in sources:
    df = pd.read_csv(
        building.download_data(filepath, unzip_file=filename), sep='\t')

    timesteps = df.loc[df['Year'] == int(year), :].index

    df.index = pd.to_datetime(df[['Year', 'Month', 'Day', 'Hour']])
    df = df.loc[year, [c for c in countries if c in df.columns]]
    df.rename(columns={c: tech + '-' + c + '-profile' for c in countries}, inplace=True)

    path = building.write_sequences('generator-profiles.csv', df)
    create_resource(path)

# create solar profiles
df = pd.read_csv(
    building.download_data(
        'https://setis.ec.europa.eu/sites/default/files/EMHIRES_DATA/Solar/'
        + 'EMHIRESPV_country_level.zip',
        unzip_file='EMHIRESPV_TSh_CF_Country_19862015.txt'),
    sep=' ')

df = df.loc[timesteps, [c for c in countries if c in df.columns]]
df.index = pd.date_range(
    '2015-01-01 00:00:00', '2015-12-31 23:00:00', freq='H')

df.rename(columns={c: 'solar' + '-' + c + '-profile' for c in countries},
          inplace=True)

path = building.write_sequences('generator-profiles.csv', df)
create_resource(path)

# wind / solar capacities
filepath = building.download_data(
    'https://ec.europa.eu/energy/sites/ener/files/documents/'
    'countrydatasheets_june2018.xlsx')


c_data = pd.read_csv('archive/capacities.csv', sep=';', index_col=[0, 1, 2])

wind_off_capas = c_data.loc[pd.IndexSlice[:, :, 'wind-offshore'], :].\
    reset_index(level=['year', 'technology'])

# EMHIRES profile for wind-offshore Sweden not available
wind_off_capas.drop(index=['SE'], inplace=True)

xl = pd.ExcelFile(filepath)

elements = {}
for c in countries:
    if c in ['NO', 'CH']:
        wind_total = c_data.loc[(int(year), c, 'wind-total'), 'value']

    else:
        df = xl.parse(
            c, header=0, index_col=2, skiprows=7, keep_default_na=False)
        wind_total = df.loc['Wind Cumulative Installed Capacity - MW', int(year)]

    # wind-offshore
    if c in wind_off_capas.index:

        element_name = 'wind-offshore-' + c

        element = {
            'capacity': wind_off_capas.loc[c, 'value'],
            'bus': c + '-electricity',
            'profile': 'wind-offshore-' + c + '-profile',
            'type': 'volatile',
            'carrier': 'wind',
            'tech': 'wind-offshore'}

        elements[element_name] = element

        wind_total -= wind_off_capas.loc[c, 'value']

    # wind-onshore
    element_name = 'wind-onshore-' + c

    element = {
        'capacity': wind_total,
        'bus': c + '-electricity',
        'profile': 'wind-onshore-' + c + '-profile',
        'carrier': 'wind',
        'type': 'volatile',
        'tech': 'wind-onshore'}

    elements[element_name] = element

    # solar
    element_name = 'solar-' + c

    element = {
        'capacity': df.loc['Solar Total Installed Capacity - MW', int(year)],
        'bus': c + '-electricity',
        'profile': 'solar-' + c + '-profile',
        'type': 'volatile',
        'tech': 'solar',
        'carrier': 'solar'}

    elements[element_name] = element

def create_resource(path):
    from datapackage import Resource
    resource = Resource({'path': path})
    resource.infer()
    resource.descriptor['schema']['primaryKey'] = 'timeindex'
    resource.descriptor['description'] = 'Data on solar, wind-onshore and wind-offshore components'
    resource.descriptor['title'] = 'Solar and wind components'
    resource.descriptor['sources'] = [
        {
            'title': 'EU Commission, DG ENER, Unit A4 - ENERGY STATISTICS',
            'path': 'https://ec.europa.eu/energy/sites/ener/files/documents/countrydatasheets_june2018.xlsx',
            'files': ['countrydatasheets_june2018.xlsx']
        }]

    resource.descriptor['schema']['foreignKeys'] = [{
        "fields": "bus",
        "reference": {
            "resource": "bus",
            "fields": "name"}}]


    resource.descriptor['schema']['foreignKeys'].append({
        "fields": "profile",
        "reference": {
            "resource": "generator-profiles"}})

    resource.commit()

    resource.save('resources/' + resource.name + '.json')

path = building.write_elements('volatile-generator.csv',
                        pd.DataFrame.from_dict(elements, orient='index'))
create_resource(path)
