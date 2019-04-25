#!/bin/bash

#activate python virtual environment
. bin/activate
#set flask app environment variable
export FLASK_APP=main.py
#start flask
flask run
echo "open the uri above to start using EcoloGIS"
