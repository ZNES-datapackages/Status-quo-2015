"""

EU Commission, DG ENER, Unit A4 - ENERGY STATISTICS, https://ec.europa.eu/energy/sites/ener/files/documents/countrydatasheets_june2018.xlsx
"""

import pandas as pd

from oemof.tabular.datapackage import building

config = building.read_build_config('config.toml')
countries, year = config['countries'], str(config['year'])

xl = pd.ExcelFile(
        building.download_data(
            'https://ec.europa.eu/energy/sites/ener/files/documents/countrydatasheets_june2018.xlsx'))

stored_capacities = pd.read_csv('archive/capacities.csv', sep=';', index_col=[0, 1, 2])

idx = pd.IndexSlice
offshore_capacities = stored_capacities.loc[idx[:, :, 'wind-offshore'], :].\
    reset_index(level=['year', 'technology'])

# volatile profile Sweden not available
offshore_capacities.drop(index=['SE'], inplace=True)


elements = {}
for country in countries:
    if country in ['NO', 'CH']:
        wind_capacity = stored_capacities.loc[(int(year), country, 'wind-total'), 'value']

    else:
        df = xl.parse(country, header=0, index_col=2, skiprows=7, keep_default_na=False)
        wind_capacity = df.loc['Wind Cumulative Installed Capacity - MW', int(year)]

    # wind-offshore
    if country in offshore_capacities.index:

        element_name = country + '-wind-offshore'

        element = {
            'bus': country + '-electricity',
            'tech': 'wind-offshore',
            'carrier': 'wind',
            'capacity': offshore_capacities.loc[country, 'value'],
            'profile': country + '-wind-offshore-profile',
            'marginal_cost': 0,
            'type': 'volatile'}

        elements[element_name] = element

        wind_capacity -= offshore_capacities.loc[country, 'value']

    # wind-onshore
    element_name = country + '-wind-onshore'

    element = {
        'bus': country + '-electricity',
        'tech': 'wind-onshore',
        'carrier': 'wind',
        'capacity': wind_capacity,
        'profile': country + '-wind-onshore-profile',
        'marginal_cost': 0,
        'type': 'volatile'}

    elements[element_name] = element

    # solar
    element_name = country + '-pv'

    element = {
        'bus': country + '-electricity',
        'tech': 'pv',
        'carrier': 'solar',
        'capacity': df.loc['Solar Total Installed Capacity - MW', int(year)],
        'profile': country + '-pv-profile',
        'marginal_cost': 0,
        'type': 'volatile'}

    elements[element_name] = element

building.write_elements('volatile.csv', pd.DataFrame.from_dict(elements, orient='index'))
