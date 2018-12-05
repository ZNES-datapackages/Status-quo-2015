# -*- coding: utf-8 -*-
"""

Gonzalez Aparicio, Iratxe; Zucker, Andreas; Careri, Francesco; Monforti Ferrario, Fabio; Huld, Thomas; Badger, Jake (2016):  Wind hourly generation time series at country, NUTS 1, NUTS 2 level and bidding zones. European Commission, Joint Research Centre (JRC) [Dataset] PID: http://data.europa.eu/89h/jrc-emhires-wind-generation-time-series

Gonzalez Aparicio, Iratxe (2017):  Solar hourly generation time series at country, NUTS 1, NUTS 2 level and bidding zones. European Commission, Joint Research Centre (JRC) [Dataset] PID: http://data.europa.eu/89h/jrc-emhires-solar-generation-time-series

EU Commission, DG ENER, Unit A4 - ENERGY STATISTICS, https://ec.europa.eu/energy/sites/ener/files/documents/countrydatasheets_june2018.xlsx


ToDo
----

Replace EMHIRES (downscaled MERRA data) with ERA-5
https://www.sciencedirect.com/science/article/pii/S0960148118303677
"""

import pandas as pd

from datapackage_utilities import building
from datetime import datetime


config = building.get_config()
countries, year = config['countries'], str(config['year'])

date_parser = lambda y: datetime.strptime(y, '%Y %m %d %H')
date_columns = ['Year', 'Month', 'Day', 'Hour']

urls = ['http://setis.ec.europa.eu/sites/default/files/EMHIRES_DATA/TS_CF_COUNTRY_30yr_date.zip',
        'http://setis.ec.europa.eu/sites/default/files/EMHIRES_DATA/TS_CF_OFFSHORE_30yr_date.zip']
filenames = ['TS.CF.COUNTRY.30yr.date.txt', 'TS.CF.OFFSHORE.30yr.date.txt']
technologies = ['wind-onshore', 'wind-offshore']

for url, fname, tech in zip(urls, filenames, technologies):

    df = pd.read_csv(building.download_data(url, unzip_file=fname), sep='\t',
            parse_dates={'i': date_columns}, date_parser=date_parser,
            index_col='i').reindex(columns=countries).dropna(axis=1).loc[year, :]

    renames = {c: c + '-' + tech + '-profile' for c in countries}
    df.rename(columns=renames, inplace=True)

    building.write_sequences('volatile_profile.csv', df)

df = pd.read_csv(
        building.download_data(
        'https://setis.ec.europa.eu/sites/default/files/EMHIRES_DATA/Solar/EMHIRESPV_country_level.zip',
        unzip_file='EMHIRESPV_TSh_CF_Country_19862015.txt'),
        sep=' ').loc[:, countries].iloc[-8760::, :]  # temporal coverage to 2015-12-31 23:00:00

df.index = pd.date_range(
    '2015-01-01 00:00:00', '2015-12-31 23:00:00', freq='H')

renames = {c: c + '-pv-profile' for c in countries}
df.rename(columns=renames, inplace=True)
building.write_sequences('volatile_profile.csv', df)
