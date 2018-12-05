"""
"""

import pandas as pd

from datapackage_utilities import building

config = building.get_config()

buses = building.read_elements('bus.csv')
buses.index.name = 'bus'

elements = pd.DataFrame(buses.index)

elements['type'] = 'shortage'
elements['name'] = elements['bus'].str[:2] + '-shortage'
elements['capacity'] = 50000
elements['marginal_cost'] = 1000

elements.set_index('name', inplace=True)
building.write_elements('shortage.csv', elements)
