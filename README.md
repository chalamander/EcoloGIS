# EcoloGIS
This project aims to bring together the fields of movement ecology and data geovisualisation in order to develop an advanced web-based movement data visualisation tool, EcoloGIS.

### Prerequisites:
 - python 2.7 (sudo apt-get install python2.7)
 - pip - Python package manager (sudo apt-get install python-pip)
 - virtualenv - Python package for self-contained python environments (sudo pip install virtualenv)

### After installing the prerequisites:
To run the application on Linux systems execute the bash script run.sh, which should activate the python virtual environment, export the flask application evironment variable, and then start running a flask server locally. The URI of the server should appear in the console output - open this in the web browser of your choice (firefox / chrome recommended). The link should navigate you to [localhost:5000]/new/ and you should see the 'create a new study' screen of EcoloGIS. Upload the example movement data file '2015 Tsinghua waterfowl (Yangtze).csv', or any other compatible .csv from www.movebank.org with open access, and the file will be uploaded to the system for analysis.

Example data source: Si, Y. et al. (2018) Spring migration patterns, habitat use and stopover site protection status for two declining waterfowl species wintering in China as revealed by satellite tracking. Ecology and Evolution. https://doi.org/10.1002/ece3.4174 Zhang, et al. (2018). Multi-scale habitat selection by two declining East Asian waterfowl species at their core spring stopover area. Ecological Indicators, 87, 127-135. doi: https://doi.org/10.1016/j.ecolind.2017.12.035: Li, X. et al. (2017). Dynamic response of East Asian Greater White-fronted Geese to changes of environment during migration: Use of multi-temporal species distribution model. Ecological Modelling, 360, 70-79. doi: https://doi.org/10.1016/j.ecolmodel.2017.06.004
