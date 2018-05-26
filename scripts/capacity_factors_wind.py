# -*- coding: utf-8 -*-
"""
"""

import pandas as pd

from datapackage_utilities import building


def create_resource(path):
    from datapackage import Resource
    resource = Resource({'path': path})
    resource.infer()
    resource.descriptor['schema']['primaryKey'] = 'timeindex'
    resource.descriptor['description'] = 'Wind profiles (capacity factors) from renewables ninja for each country'
    resource.descriptor['title'] = 'Wind profiles'
    resource.descriptor['sources'] = [{
        'title': 'Renewables Ninja Wind Capacity Factors',
        'path': 'https://www.renewables.ninja/static/downloads/ninja_europe_wind_v1.1.zip'}]
    resource.commit()

    if resource.valid:
        resource.save('resources/' + resource.name + '.json')

config = building.get_config()

filepath = building.download_data(
    'https://www.renewables.ninja/static/downloads/ninja_europe_wind_v1.1.zip',
    unzip_file='ninja_wind_europe_v1.1_current_on-offshore.csv')

year = str(config['year'])

raw_data = pd.read_csv(filepath, index_col=[0], parse_dates=True)

elements = building.read_elements('volatile-generators.csv')

mapper = {'wind-onshore': '_ON', 'wind-offshore': '_OFF'}

for k, v in mapper.items():

    idx = elements.index.str.contains(k)
    countries = elements[idx].index.str[-2:]

    df = raw_data.loc[year][[c + v for c in countries]]

    sequences_df = pd.DataFrame(index=df.index)

    for c in countries:
        sequence_name = k + '-' + c + '-profile'
        sequences_df[sequence_name] = df[c + v].values

    sequences_df.index = building.timeindex()

    path = building.write_sequences('generator-profiles.csv', sequences_df)

create_resource(path)
