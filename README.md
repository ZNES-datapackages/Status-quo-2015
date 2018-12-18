# Status-quo-2015 datapackage

## Preparation

If you want to build the package all you need to do is to run one script.

### Requirements

To run the script, make sure the requirements e.g. via pip

    pip install --process-dependency-links -U -r requirements.txt


### Build

To build the packages locally run the python script

    python scripts/build.py

This will initialize all directories if they don't exist, download raw data,
create the meta-data file. The output data are stored under:

    /data


## Hydro

The datapackage includes data on hydro electricity powerplants. Data for these powerplants is prepared as follows.
Installed hydro capacities are based on Alexander Kies, Lueder von Bremen, & Detlev Heinemann. (2017). Hydro Energy Inflow for Power System Studies [Data set]. Zenodo. http://doi.org/10.5281/zenodo.804244.
Thanks for sharing!!

The dataset includes hydropower.csv, in which hydro capacities are listed for 27 countries. Column **installed hydro capacities** represent the combined capacities of reservoir, run-of-river and pumped-hydro powerplants in each country. To derive run-of-river capacities the run-of-river share present in an additional file Run-Of-River-Shares.csv is multiplied with **installed hydro capacities**. In order to access the installed reservoir capacity run-of-river and pumped-hydro capacity is substracted from **installed hydro capacities**.

Hydro inflow timeseries are also included in the dataset. The underlying hydro model is described in A Kies, K Chattopadhyay, L von Bremen, E Lorenz, D Heinemann ,Simulation of renewable feed-in for power system studies, RESTORE 2050 project report. For each country the hydro inflow in GWh per day is given in the timeframe from 2003 up until 2012. The data is normalized with today's average daily hydro generation. For a particular year, e.g. 2012, the data can potentially normalized based on other statistics, e.g. yearly hydro-electricity-generation provided by the [IEA website](https://www.eia.gov/beta/international/data/browser/#/?pa=000000000000000000000000000000g&c=00280008002gg0040000000000400000gg0004000008&ct=0&ug=8&tl_type=a&tl_id=12-A&vs=INTL.33-12-AUT-BKWH.A&vo=0&v=H&start=2011&end=2015&s=INTL.33-12-DEU-BKWH.A). The corresponding [EIA table notes](https://www.eia.gov/beta/international/data/browser/views/partials/table_notes.html) state that "*Hydroelectric generation excludes generation from hydroelectric pumped storage, where separately reported "*.

Then the inflow in GWh/day has to be attributed to either reservoir or run-of-river power plants. This is done via the ratio of the two technologies' reported yearly electricity generation accessable on the ENTSO-E transparency platform.

The associated inflow towards reservoir powerplants will be stored in full in the reservoir basin. The initial value of the reservoir's storage capacity is the same at the end of year or time period. Hydro inflow attributed to the run-of-river powerplants might exceed the actual installed capacity of the powerplant. Prepocessing will handle it...

## Contributors

Simon Hilpert, Martin Söthe, Clemens Wingenbach
