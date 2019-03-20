""" """

import os
import shutil
import pandas as pd


from oemof.tabular import facades
from oemof.tabular.datapackage import building
from oemof.tabular.tools import postprocessing as pp
from oemof.solph import EnergySystem, Model, Bus

"""
"""

timesteps = 8760

for f in os.listdir('data/sequences/'):
    fname = os.path.join('data', 'sequences', f)
    df = pd.read_csv(fname, sep=';')
    df = df.iloc[:timesteps]
    df.to_csv(fname, index=False, sep=';')

config = building.read_build_config('config.toml')

es = EnergySystem.from_datapackage(
    "datapackage.json",
    attributemap={},
    typemap=facades.TYPEMAP,
)

m = Model(es)

m.write('tmp.lp', io_options={"symbolic_solver_labels":True})

m.receive_duals()

m.solve('gurobi')

m.results = m.results()

if os.path.exists('results'):
    shutil.rmtree('results')
os.mkdir('results')

pp.write_results(m, 'results', scalars=False)

# create short summary
supply_sum = (
    pp.supply_results(
        results=m.results,
        es=m.es,
        bus=[b.label for b in es.nodes if isinstance(b, Bus)],
        types=[
            "dispatchable",
            "volatile",
            "reservoir",
        ],
    )
    .sum()
    .reset_index()
)

supply_sum['from'] = supply_sum['from'].apply(lambda i: '-'.join(i.label.split("-")[1:3:]))
supply_sum = supply_sum.groupby(['from', 'to', 'type']).sum().reset_index()

supply_sum.drop("type", axis=1, inplace=True)
supply_sum = (
    supply_sum.set_index(["from", "to"]).unstack("from")
    / 1e6
)

supply_sum.columns = supply_sum.columns.droplevel(0)
supply_sum.to_csv(os.path.join('results', 'summary.csv'))
