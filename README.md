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



## Contributors

Simon Hilpert, Martin Söthe, Clemens Wingenbach
