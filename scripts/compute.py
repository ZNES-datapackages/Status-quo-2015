""" """

import datetime
import os
import json
import logging

from datapackage import Package
import numpy as np
import pandas as pd

from oemof.tabular import facades
from oemof.tabular.datapackage import aggregation, building, processing
from oemof.tabular.tools import postprocessing as pp
import oemof.outputlib as outputlib
from oemof.solph import EnergySystem, Model, Bus, Sink, constraints
from oemof.outputlib import views
from oemof.solph.components import GenericStorage


"""
"""

config = building.get_config()

temporal_resolution = config.get("temporal-resolution", 1)

path = os.path.expanduser('~')

ef = pd.DataFrame(
    Package('https://raw.githubusercontent.com/ZNES-datapackages/technology-cost/features/add-2015-data/datapackage.json')
    .get_resource('carrier').read(keyed=True)).set_index(
        ['year', 'carrier', 'parameter', 'unit']).sort_index() \
    .loc[(2015, slice(None), 'emission-factor', 't (CO2)/MWh'), :] \
    .reset_index().set_index('carrier')['value']

# create results path
scenario_path = os.path.join(path, 'results', config["name"])
if not os.path.exists(scenario_path):
    os.makedirs(scenario_path)

output_path = os.path.join(scenario_path, "output")
if not os.path.exists(output_path):
    os.makedirs(output_path)

# store used config file
with open(os.path.join(scenario_path, "config.json"), "w") as outfile:
    json.dump(config, outfile, indent=4)

# copy package either aggregated or the original one (only data!)
if temporal_resolution > 1:
    logging.info("Aggregating for temporal aggregation ... ")
    path = aggregation.temporal_skip(
        "datapackage.json",
        temporal_resolution,
        path=scenario_path,
        name="input"
    )
else:
    path = processing.copy_datapackage(
        "datapackage.json",
        os.path.abspath(os.path.join(scenario_path, "input")),
        subset="data",
    )

es = EnergySystem.from_datapackage(
    os.path.join(path, "datapackage.json"),
    attributemap={},
    typemap=facades.TYPEMAP,
)

m = Model(es)
m.write('tmp.lp', io_options={"symbolic_solver_labels":True})

# constraints.emission_limit(m, limit=emission_limit)

m.receive_duals()

m.solve('gurobi')

m.results = m.results()

pp.write_results(m, output_path, scalars=False)

modelstats = outputlib.processing.meta_results(m)
modelstats.pop("solver")
modelstats["problem"].pop("Sense")
with open(os.path.join(scenario_path, "modelstats.json"), "w") as outfile:
    json.dump(modelstats, outfile, indent=4)


# emissions
emissions = views.node_output_by_type(m.results, node_type=es.typemap['dispatchable'])
emissions = emissions.loc[:, [c for c in emissions.columns.get_level_values(0) if c.tech != None]]  # filter shortage
emissions = emissions.apply(lambda x: x * float(ef[(x.name[0].label.split('-')[1])])).T.groupby('to').sum().T.sum()
emissions.to_csv(os.path.join(scenario_path, 'emissions.csv'))

supply_sum = (
    pp.supply_results(
        results=m.results,
        es=m.es,
        bus=[b.label for b in es.nodes if isinstance(b, Bus)],
        types=[
            "dispatchable",
            "volatile",
            "conversion",
            "backpressure",
            "extraction",
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
    * config["temporal-resolution"]
)
supply_sum.columns = supply_sum.columns.droplevel(0)

# excess_share = (
#     excess.sum() * config["temporal-resolution"] / 1e6
# ) / supply_sum.sum(axis=1)
# excess_share.name = "excess"

summary = supply_sum #pd.concat([supply_sum, excess_share], axis=1)
summary.to_csv(os.path.join(scenario_path, 'summary.csv'))
