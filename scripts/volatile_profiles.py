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

import os

import pandas as pd

from oemof.tabular.datapackage import building
from datetime import datetime


config = building.read_build_config('config.toml')

countries, year = config['countries'], str(config['year'])

filepath = building.download_data(
    "https://www.renewables.ninja/static/downloads/ninja_europe_pv_v1.1.zip",
    unzip_file="ninja_pv_europe_v1.1_merra2.csv")

raw_data = pd.read_csv(filepath, index_col=[0], parse_dates=True)

df = raw_data.loc[year]

sequences_df = pd.DataFrame(index=df.index)

for c in countries:
    sequence_name = c + "-pv-profile"
    sequences_df[sequence_name] = raw_data.loc[year][c].values

sequences_df.index = building.timeindex(year)

building.write_sequences("volatile_profile.csv", sequences_df)

filepath = building.download_data(
    "https://www.renewables.ninja/static/downloads/ninja_europe_wind_v1.1.zip",
    unzip_file="ninja_wind_europe_v1.1_current_on-offshore.csv")

raw_data = pd.read_csv(filepath, index_col=[0], parse_dates=True)

# not in ninja dataset, as new market zones? (replace by german factor)
raw_data['LU_ON'] = raw_data['DE_ON']
raw_data['AT_ON'] = raw_data['DE_ON']
raw_data['CH_ON'] = raw_data['DE_ON']
raw_data['CZ_ON'] = raw_data['DE_ON']
raw_data['PL_OFF'] = raw_data['SE_OFF']

df = raw_data.loc[year]

sequences_df = pd.DataFrame(index=df.index)

for c in countries:
    if c + '_OFF' in df.columns:
        sequences_df[c + "-wind-offshore-profile"] = df[c + "_OFF"]
    sequence_name = c + "-wind-onshore-profile"
    sequences_df[sequence_name] = df[c + "_ON"]

sequences_df.index = building.timeindex(year)
building.write_sequences("volatile_profile.csv", sequences_df)
