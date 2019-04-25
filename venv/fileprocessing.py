import os, csv, pandas, geojson, calendar, math, numpy, pyproj
from dateutil.parser import parse as date_parse
from werkzeug.utils import secure_filename
BASEDIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = BASEDIR + '/static/data/'
ALLOWED_EXTENSIONS = set(['csv'])
CSV_COLNAMES = ['TIMESTAMP', 'LONG', 'LOCATION-LONG','LAT','LOCATION-LAT','INDIVIDUAL-TAXON-CANONICAL-NAME', 'INDIVIDUAL-LOCAL-IDENTIFIER','STUDY-NAME']
#Setup projections
crs_wgs = pyproj.Proj(init='epsg:4326') #WGS84 geographic coord system
crs_mercator = pyproj.Proj(init='epsg:3857') #Web Mercator geographic coord system

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_csv(filepath):
    with open(filepath) as csv_file:
        dataframe = pandas.read_csv(csv_file, usecols=lambda x: x.upper() in CSV_COLNAMES, parse_dates = [0], infer_datetime_format = True)
        dataframe = dataframe.dropna()
        if 'location-long' in dataframe.columns:
            print "test1"
            dataframe.rename(columns={'location-long': 'long'}, inplace=True)
        if 'location-lat' in dataframe.columns:
            print "test2"
            dataframe.rename(columns={'location-lat': 'lat'}, inplace=True)
        if 'individual-local-identifier' in dataframe.columns:
            dataframe.rename(columns={'individual-local-identifier' : 'ID'}, inplace=True)
        if 'individual-taxon-canonical-name' in dataframe.columns:
            dataframe.rename(columns={'individual-taxon-canonical-name' : 'indiv-name'}, inplace=True)

        #create timestamp epoch column, for easily comparable indexable dates
        dataframe['timestamp_epoch'] = dataframe['timestamp'].apply(lambda timestamp: timestamp.timestamp())

        #create trajectory id data column, to seperate trajectories by day
        dataframe['traj_id'] = dataframe['timestamp'].apply(lambda date: process_traj_id(date))

        unique_ids = dataframe['ID'].unique()
        dataframe['real-ID'] = dataframe['ID']
        dataframe['ID'] = dataframe.apply(lambda row: numpy.where(unique_ids == row['ID'])[0][0], axis=1)
        dataframe.set_index(['timestamp_epoch', 'ID'], drop=False, inplace=True)
        print(dataframe)
        print "ndim: " + str(dataframe.ndim)
        print "size: " + str(dataframe.size)
        print "columns: " + str(dataframe.columns)
        print "numcolumns: " + str(len(dataframe.columns))
        print "numrows: " + str(len(dataframe.index))
        print "study: " + dataframe['study-name'].iloc[0]
    return dataframe

#save a pandas dataframe object to geojson and pkl dataframe
def savedata(df, data_id, json = True, pkl = False):
    if(json):
        filename_json = os.path.join(UPLOAD_FOLDER, data_id + ".geojson")
        features = []
        df.apply(lambda X: features.append(
                geojson.Feature(
                geometry=geojson.Point((X["long"], X["lat"])),
                properties=dict(
                time=str(X["timestamp"]),
                timestamp_epoch=int(X['timestamp_epoch'])
                ))), axis=1)
        with open(filename_json, 'w+') as fp:
            geojson.dump(geojson.FeatureCollection(features), fp, sort_keys=True)
    if(pkl):
        filename_pkl = os.path.join(UPLOAD_FOLDER, data_id + ".pkl")
        df.to_pickle(filename_pkl)

#take a pandas row of data and return epoch time of the data entry
def process_epoch_time(row):
    epochtime = 0
    if row['timestamp']:
        epochtime = calendar.timegm(date_parse(str(row['timestamp'])).timetuple())
    return epochtime

#take a timestamp string and return as a date string
def process_traj_id(timestamp):
    if timestamp:
        return timestamp.date()

#filter data by some criteria and return (id, numpoints, startdate, enddate) of new data file
def filter_data(data_id, start_date = None, end_date = None, selected_individual = 'all'):
    #read data from file to pandas object
    filename = str(data_id) + ".pkl"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    dataframe = pandas.read_pickle(filepath)

    #filter by selected individual
    if selected_individual != 'all':
        if 'ID' in dataframe.columns:
            if dataframe['ID'].dtype == numpy.int64:
                dataframe = dataframe[dataframe['ID'] == int(selected_individual)]
            else:
                dataframe = dataframe[dataframe['ID'] == selected_individual]
        elif 'indiv-name' in dataframe.columns:
            dataframe = dataframe[dataframe['indiv-name'] == selected_individual]

    #get all mask
    data_boundaries = find_boundary_indices(dataframe)
    mask = dataframe['timestamp_epoch'].between(dataframe['timestamp_epoch'].loc[data_boundaries[0]], dataframe['timestamp_epoch'].loc[data_boundaries[1]])

    #filter date range
    if start_date and end_date:
        mask = dataframe['timestamp_epoch'].between(start_date, end_date)

    #apply mask
    filtered_dataframe = dataframe.loc[mask]

    #get unique individuals
    individuals = dataframe['real-ID'].unique()

    #gererate new filename and save as geojson
    filtered_data_id = secure_filename(str(data_id) + "_filtered")
    filtered_data_boundaries = find_boundary_indices(filtered_dataframe)
    savedata(filtered_dataframe, filtered_data_id, True, True)
    if(len(filtered_dataframe['timestamp_epoch']) > 0):
        return (filtered_data_id, len(filtered_dataframe.index), filtered_dataframe['timestamp'].loc[filtered_data_boundaries[0]], filtered_dataframe['timestamp'].loc[filtered_data_boundaries[1]], individuals)
    return (filtered_data_id, len(filtered_dataframe.index), '-', '-', [])

#find the (min, max) indices in a dataframe object
def find_boundary_indices(df):
    if len(df['timestamp_epoch']) > 0:
        minentry = [df['timestamp_epoch'].idxmin()]
        maxentry = [df['timestamp_epoch'].idxmax()]
        return (minentry[0], maxentry[0])
    return (0,0)

#returns a dataframe of [(name,id)]
def find_individual_ids(df):
    has_name = 'indiv-name' in df.columns
    has_id = 'ID' in df.columns
    has_both = has_name and has_id
    if has_both :
        individuals = df[['indiv-name','ID']]
    elif has_id:
        individuals = df['ID']
    elif has_name:
        individuals = df['indiv-name']
    else:
        return None
    return {(indiv[1] if len(individuals.columns)>0 else indiv):(str(indiv[1] if len(individuals.columns)>0 else indiv).zfill(3), indiv[0] if len(individuals.columns)>0 else "Individual " + str(indiv)) for indiv in individuals.drop_duplicates(subset='ID').values}

def read_data_id(data_id):
    source_filepath = os.path.join(UPLOAD_FOLDER, data_id + ".pkl")
    return pandas.read_pickle(source_filepath)

def save_density(df, data_id, json = True, pkl = False):
    if(json):
        features = []
        density_min = df['density'].min()
        density_max = df['density'].max()

        df.apply(
            lambda df: features.append(
                {"position": [df['long'], df['lat'], df['z']], "normal": [-1, 0, 0], "color": magnitude_rgba(df['density'], density_min, density_max), "density": df['density']
                }
            ), axis=1
        )
        points_filepath = os.path.join(UPLOAD_FOLDER, data_id + "_points.geojson")
        with open(points_filepath, 'w+') as fp:
            geojson.dump(features, fp, sort_keys=True)
    if(pkl):
        filename_pkl = os.path.join(UPLOAD_FOLDER, data_id + ".pkl")
        df.to_pickle(filename_pkl)

#returns a tuple of floats between 0 and 255 for R, G, and B
#light blue for cold (low magnitude) all the way to yellow for hot (high magnitude)
def magnitude_rgba(mag, cmin, cmax):
    # Normalize to 0-1
    try: x = float(mag-cmin)/(cmax-cmin)
    except ZeroDivisionError: x = 0.5 # cmax == cmin
    blue  = min((max((4*(0.75-x), 0.)), 1.))
    red   = min((max((4*(x-0.25), 0.)), 1.))
    green = min((max((4*math.fabs(x-0.5)-1., 0.)), 1.))
    return red*255, green*255, blue*255, (25 if x<0.3 else 255)
