# Status-quo-2015 datapackage

## Preparation

If you want to build the package all you need to do is run one script.

### Requirements

To run the script, make sure the requirements are met e.g. via pip installation. Package six has to be installed beforehand.

    pip install six
    pip install pip==18.1

    pip install --process-dependency-links -U -r requirements.txt


### Scope

The spatial resolution is at NUTS 0 level, thus on the level of national states. Which national states (nodes) are included is defined in the config.toml.

### Build

To build the package locally run the python script

    python scripts/build_package.py

This will initialize all directories if they don't exist, download raw data,
create the meta-data file. The output data are stored under:

    /data

### Sources & Attributions

The administrative units are provided by Eurostat. Information on the copyright and license policy is available [here](https://ec.europa.eu/eurostat/web/gisco/geodata/reference-data/administrative-units-statistical-units).

EN: © EuroGeographics for the administrative boundaries

Load data and data on the conventional power plant capacity in Germany is provided by the [Open Power System Data - A free and open data platform for power system modelling](https://open-power-system-data.org/).

Open Power System Data. 2018. Data Package Time series. Version 2018-06-30. https://doi.org/10.25832/time_series/2018-06-30. (Primary data from various sources, for a complete list see URL).

Open Power System Data. 2018. Data Package Conventional power plants. Version 2018-12-20. https://doi.org/10.25832/conventional_power_plants/2018-12-20. (Primary data from various sources, for a complete list see URL)

Data on capacity factors for wind and pv in European countries is downloaded from [www.renewables.ninja](https://www.renewables.ninja/) .

Stefan Pfenninger and Iain Staffell (2016). Long-term patterns of European PV output using 30 years of validated hourly reanalysis and satellite data. Energy 114, pp. 1251-1265. doi: 10.1016/j.energy.2016.08.060.

I. Staffell and S. Pfenninger, 2016. Using Bias-Corrected Reanalysis to Simulate Current and Future Wind Power Output. Energy, 114, 1224–1239. http://dx.doi.org/10.1016/j.energy.2016.08.068

Data on powerplant capacities in European countries is provided by the [powerplantmatching module](https://github.com/FRESNA/powerplantmatching) developed by FRESNA.

FabianHofmann, Jonas Hörsch, & Fabian Gotzens. (2018, December 3). FRESNA/powerplantmatching: python3 adjustments (Version v0.3). Zenodo. http://doi.org/10.5281/zenodo.1889465

Data on cost assumptions is taken from the [Technology Cost for Electrictiy Generation datapackage](https://github.com/ZNES-datapackages/technology-cost).

Capacities of hydro power plants is included in a dataset on [Hydro Energy Inflow for Power System Studies](https://zenodo.org/record/804244).

Alexander Kies, Lueder von Bremen, & Detlev Heinemann. (2017). Hydro Energy Inflow for Power System Studies [Data set]. Zenodo. http://doi.org/10.5281/zenodo.804244.

Data on hydro inflows is calculated with [atlite](https://github.com/FRESNA/atlite) based on the ERA5 dataset.

Contains modified Copernicus Climate Change Service information [2015]

Copernicus Climate Change Service (C3S) (2017): ERA5: Fifth generation of ECMWF atmospheric reanalyses of the global climate . Copernicus Climate Change Service Climate Data Store (CDS), date of citation. https://cds.climate.copernicus.eu/cdsapp#!/home

Additional data, stored in the archive directory, is used as well. Sources are mentioned separately within each file.

Thanks for sharing!!

### Hydro data handling

In the cached file hydropower.csv column **installed hydro capacities** represent the combined hydro capacities of reservoir, ror and phs powerplants. In order to get separate ror and reservoir capacities the phs capacity, part of hydropower.csv, is substracted and the intermediary result is multiplied with the ror-share (archive/ror\_ENTSOe\_Restore2050.csv) or the complement of that share.

Inflow data created with atlite is scaled to represent the IEA's annual hydro electricity generation (Hydroelectric generation excludes generation from hydroelectric pumped storage, where separately reported) and attributed as inflow to ror (in the form of capacity factors) and reservoir powerplants based on the ror-share.

The value of the initial state of stored energy of reservoir powerplants has to be met at the last timestep of the optimization.

### Distinctions made in the case of Germany

German dispatchable powerplants defined on the basis of OPSD data are divided into separate entities beyond the fuel and technology level. Powerplants are further clustered into quantiles based on their capacity.

## Contributors

Simon Hilpert, Martin Söthe, Clemens Wingenbach
