"""

Open Power System Data. 2017. Data Package Time series. Version 2017-07-09. https://data.open-power-system-data.org/time_series/2017-07-09/. (Primary data from various sources, for a complete list see URL)

https://data.open-power-system-data.org/time_series/2017-07-09/time_series_60min_singleindex.csv
https://data.open-power-system-data.org/time_series/2017-07-09/time_series_60min_singleindex.csv

ToDo
----

Load series misses entries for 2015-12-31 23:00:00
"""

import json
import pandas as pd

from datapackage_utilities import building


config = building.get_config()
countries, year = config['countries'], str(config['year'])


raw_data = pd.read_csv(
        building.download_data(
            'https://data.open-power-system-data.org/time_series/2017-07-09/'
            'time_series_60min_singleindex.csv'),
    index_col=[0], parse_dates=True, low_memory=False)


suffix = '_load_old'


column_names = [c + suffix for c in countries]

timeseries = raw_data.loc[year, column_names]
load_total = timeseries.sum()
load_profile = timeseries / load_total

elements = {}

sequences_df = pd.DataFrame(index=load_profile.index)

for c in countries:
    element_name = 'electricity-load-' + c
    sequence_name = element_name +  '-profile'

    sequences_df[sequence_name] = load_profile[c + suffix].values

    element = {
        'bus': c + '-electricity',
        'amount': load_total[c + suffix],
        'profile': sequence_name,
        'tech': 'load',
        'type': 'load'
    }

    elements[element_name] = element

building.write_elements('load.csv',
        pd.DataFrame.from_dict(elements, orient='index'))

sequences_df.index = building.timeindex()
building.write_sequences('load-profiles.csv', sequences_df)
