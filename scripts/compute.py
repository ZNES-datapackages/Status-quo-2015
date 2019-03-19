""" """

import os
import shutil


from oemof.tabular import facades
from oemof.tabular.datapackage import building
from oemof.tabular.tools import postprocessing as pp
from oemof.solph import EnergySystem, Model

"""
"""

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
