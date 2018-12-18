"""
"""
import pandas as pd

from oemof.tabular.datapackage import building

buses = building.read_elements('bus.csv')
buses.index.name = 'bus'

elements = pd.DataFrame(buses.index)

elements['type'] = 'excess'
elements['name'] = elements['bus'].str[:2] + '-excess'
elements['marginal_cost'] = 0

elements.set_index('name', inplace=True)
building.write_elements('excess.csv', elements)
