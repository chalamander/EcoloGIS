# EcoloGIS
This project aims to bring together the fields of movement ecology and data geovisualisation in order to develop an advanced web-based movement data visualisation tool, EcoloGIS.

### Prerequisites:
 - python 2.7 (sudo apt-get install python2.7)
 - pip - Python package manager (sudo apt-get install python-pip)
 - virtualenv - Python package for self-contained python environments (sudo pip install virtualenv)

### After installing the prerequisites:
To run the application on Linux systems execute the bash script run.sh, which should activate the python virtual environment, export the flask application evironment variable, and then start running a flask server locally. The URI of the server should appear in the console output - open this in the web browser of your choice (firefox / chrome recommended). The link should navigate you to [localhost:5000]/new/ and you should see the 'create a new study' screen of EcoloGIS. Upload the example movement data file '2015 Tsinghua waterfowl (Yangtze).csv', or any other compatible .csv from www.movebank.org with open access, and the file will be uploaded to the system for analysis.
