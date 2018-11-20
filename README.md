# Status-quo-2015 datapackage

## Preparation

If you want to build the package all you need to do is to run one script.

### Requirements

To run the script, make sure the requirements e.g. via pip

    pip install -U -r requirements.txt


### Build

To build the packages locally run the python script

    python scripts/build.py

This will initialize all directories if they don't exist, download raw data,
create the meta-data file. The output data are stored under:

    /data


## Hydro

Installed capacities are taken from 

https://zenodo.org/record/804244. 

Hydropower.csv comes with the following structure

reservoir capacity [TWh], installed hydro capacities [GW], installed pumped hydro

Installed hydro capacities each represent the sum of installed pumped hydro, run-of-river and reservoir capacities.

run-of-river capacity is the product of the so-called run-of-river share taken from run-of-river-shares.csv times the installed hydro capacities field.

In order to get reservoir capacity substract installed pumped hydro and run-of-river capacity from installed pumped hydro.


Inflow timeseries are given in GWh per day for each country. These timeseries are normalized based on statistical data on today’s average
daily generation in the corresponding country. 

This data for a particular year can be normalized again to other statitical values, e.g. yearly hydroelectricity generation (IEA).

To attribute the inflow timeseries to either run-of-river or reservoir powerplants the relation of run-of-river to reservoir with regard to yearly electricity generation can be used, ENTSO-E values.


In case of reservoir max inflow is not limited. Reservoir capacity has to be same value as the beginning of the year.

In case of run-of-river the attributed inflow per hour might exceed installed capacity. This will be handled in preprocessing.

## Contributors

Simon Hilpert, Martin Söthe, Clemens Wingenbach
