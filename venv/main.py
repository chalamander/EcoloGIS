import os, time, calendar, pandas, json, datetime
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, session
from werkzeug.utils import secure_filename
from fileprocessing import *
from visualisation import *
from dateutil.parser import parse as date_parse
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = 'DqE0&|JoXIMIwOt@89T/Z0yf:qD"v.'
DATE_FORMAT = '%Y-%m-%d %H:%S:%f'

@app.route('/')
def index():
    return redirect(url_for('new'))

@app.route("/new/", methods=['GET', 'POST'])
def new():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            #create filepath to save uploaded file
            filename = secure_filename(str(calendar.timegm(time.gmtime())) + "_rawdata")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            #process csv and save as formatted geojson, removing raw uploaded file
            movedata = process_csv(filepath)
            os.remove(filepath)
            data_id = secure_filename(str(calendar.timegm(time.gmtime())) + "_data")
            savedata(movedata, data_id, True, True)
            #store study details as session variables
            data_boundaries = find_boundary_indices(movedata) #get start & end data rows
            individual_ids = find_individual_ids(movedata) #get list of individual ids
            session['startlat'] = movedata['lat'].iloc[0]
            session['startlong'] = movedata['long'].iloc[0]
            session['startdate'] = movedata['timestamp'].loc[data_boundaries[0]]
            session['enddate'] = movedata['timestamp'].loc[data_boundaries[1]]
            session['studyname'] = movedata['study-name'].iloc[0]
            #get the description from the post request of the previous page
            session['description'] = request.form.get('description','')
            session['author'] = request.form.get('author','')
            session['numpoints'] = str(len(movedata.index))
            session['numuniqueentities'] = len(individual_ids)
            session['individualids'] = individual_ids
            return redirect(url_for('map', data_id = data_id))
    return render_template('new.html')

@app.route('/map/<data_id>/', methods=['GET'])
def map(data_id):
    if(data_id):
        is_filtered = True
        fulldata_id = data_id
        filtereddata_id = data_id
        #process filtering queries
        selected_start_date = request.args.get('startdate', None)
        selected_start_time = request.args.get('starttime', None)
        selected_time_length = request.args.get('timelength', None)
        selected_individual = request.args.get('individual', 'all')
        map_style = request.args.get('mapstyle', 'dark-v10')
        use_all_data = request.args.get('usealldata', 0)

        if (selected_start_date and selected_start_time and selected_time_length and selected_time_length.isdigit() and selected_individual) or use_all_data == "1":
            filtered_data_info = []
            if use_all_data != "1":
                length_seconds = int(selected_time_length)
                start_datetime = date_parse(selected_start_date + " " + selected_start_time)
                selected_start_epoch = calendar.timegm( start_datetime.timetuple())
                end_datetime = start_datetime + datetime.timedelta(seconds=int(length_seconds))
                selected_end_epoch = calendar.timegm(end_datetime.timetuple())
                filtered_data_info = filter_data(data_id, selected_start_epoch, selected_end_epoch, selected_individual)
            else:
                filtered_data_info = filter_data(data_id)
            filtered_data_id = filtered_data_info[0]
            filtered_num_points = filtered_data_info[1]
            filtered_start_date = filtered_data_info[2]
            filtered_end_date = filtered_data_info[3]
            filtereddata_id = filtered_data_id
            filtered_individuals = filtered_data_info[4]
        else:
            is_filtered = False
            filtered_num_points = 0
            filtered_start_date = 0
            filtered_end_date = 0
            filtered_individuals = []

        #read study data from session state
        latitude = session.get('startlat',52.486659)
        longitude = session.get('startlong',-1.888357)
        studyname = session.get('studyname','New Study')
        starttime = session.get('startdate','')
        endtime = session.get('enddate','')
        numpoints = session.get('numpoints','unknown')
        description = session.get('description','')
        author = session.get('author','')
        numuniqueentities = session['numuniqueentities']
        individual_ids = dict(session['individualids'])

        #format dates for rendering
        starttime_tuple = starttime.timetuple()
        endtime_tuple = endtime.timetuple()
        starttime_epoch = calendar.timegm(starttime_tuple)
        endtime_epoch = calendar.timegm(endtime_tuple)
        start_date = starttime.strftime('%Y-%m-%d')
        end_date = endtime.strftime('%Y-%m-%d')

        return render_template('map.html', lat=latitude, long=longitude, fulldata_id=fulldata_id, study_name=studyname, full_start_date=starttime, full_end_date=endtime, num_points=numpoints, starttime_epoch=starttime_epoch, endtime_epoch=endtime_epoch, description=description, start_date=start_date, end_date=end_date, author=author, is_filtered=is_filtered, filtered_num_points=filtered_num_points, filtered_start_date=filtered_start_date, filtered_end_date=filtered_end_date, filtereddata_id=filtereddata_id, individual_id_list=individual_ids, num_unique_entities=numuniqueentities, map_style=map_style, filtered_individuals=filtered_individuals)
    return redirect(url_for('new'))

@app.route("/<unknown>/")
def unknown(unknown):
    return "Unknown url! I don't know what " + unknown + " is."

@app.route("/visualise/<data_id>/")
def visualise(data_id):
    if(data_id):
        visualisation_type = request.args.get('visualisationtype','StackedSpaceTimeDensities')
        map_style = request.args.get('mapstyle', 'dark-v10')

        if(visualisation_type == 'StackedSpaceTimeDensities'):
            returnvals = generate_sstd_points(data_id)
            if returnvals[0] == 0:
                return render_template('error.html')
            else:
                return render_template('visualisation.html', data_id=returnvals[2], startlong=returnvals[1][0], startlat=returnvals[1][1], vis_type=visualisation_type, visualisation_name='Stacked Space Time Densities', map_style=map_style)
        else:
            (startlong, startlat) = generate_xyt_points(data_id)
            return render_template('visualisation.html', data_id=data_id, startlong=startlong, startlat=startlat, vis_type=visualisation_type, visualisation_name='XYT', map_style=map_style)

    return redirect(url_for('new'))
