# -*- coding: utf-8 -*-
"""
ENTSO-E publications. (2016, March 21). NTC Values Winter 2010-2011.
https://www.entsoe.eu/fileadmin/user_upload/_library/ntc/archive/NTC-Values-Winter-2010-2011.pdf
"""

import pandas as pd

from oemof.tabular.datapackage import building

from itertools import combinations

config = building.get_config()
countries = config['countries']

loss = 0.03

filepath = building.input_filepath('transmission.csv')

data = pd.read_csv(filepath, skiprows=3, sep=';', index_col=['from', 'to'])

data = data.reindex(list(combinations(countries, 2))).dropna()

elements = {}
for (x, y), (value, _) in data.iterrows():

    from_bus, to_bus = x + '-electricity', y + '-electricity'

    element = {
        'type': 'link',
        'loss': loss,
        'to_bus': to_bus,
        'from_bus': from_bus,
        'capacity': value,
        'tech': 'transshipment'
    }

    elements[from_bus + '-' + to_bus] = element

building.write_elements(
    'grid.csv', pd.DataFrame.from_dict(elements, orient='index'))
