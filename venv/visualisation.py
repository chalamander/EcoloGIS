import os, pandas, geojson, pyproj, math, numpy, pprint, sys
from fileprocessing import *
from stacked_space_time_densities import *
from flask import flash
from werkzeug.utils import secure_filename
from itertools import product
#setup projections
crs_wgs = pyproj.Proj(init='EPSG:4326') #WGS84 geographic coord system
crs_mercator = pyproj.Proj(init='EPSG:3857') #Web Mercator geographic coord system
numpy.set_printoptions(threshold=sys.maxsize)

def generate_xyt_points(data_id):
    dataframe = read_data_id(data_id)
    data_boundaries = find_boundary_indices(dataframe)
    starttime_epoch = dataframe['timestamp_epoch'].loc[data_boundaries[0]]
    endtimestamp_epoch = dataframe['timestamp_epoch'].loc[data_boundaries[1]] - starttime_epoch

    features = []
    #Cast the geographic coordinate pair to the projected orthographic system
    dataframe.apply(
        lambda df: features.append(
            {"position": [df['long'], df['lat'], ((df['timestamp_epoch'] - starttime_epoch)/float(endtimestamp_epoch))*100000], "normal": [-1, 0, 0], "color": [255, 255, 0], "timepercentage":((df['timestamp_epoch'] - starttime_epoch)/float(endtimestamp_epoch))
            }
        ), axis=1
    )
    points_filepath = os.path.join(UPLOAD_FOLDER, data_id + "_points.geojson")
    with open(points_filepath, 'w+') as fp:
        geojson.dump(features, fp, sort_keys=True)
    return (dataframe['long'].loc[data_boundaries[0]], dataframe['lat'].loc[data_boundaries[0]])

def generate_sstd_points(data_id):
    #read saved data by id
    dataframe = read_data_id(data_id).filter(['timestamp_epoch','ID','traj_id','long','lat'], axis=1)

    #find earliest and latest data points
    data_boundaries = find_boundary_indices(dataframe)
    starttime_epoch = dataframe['timestamp_epoch'].loc[data_boundaries[0]]
    endtimestamp_seconds = dataframe['timestamp_epoch'].loc[data_boundaries[1]] - starttime_epoch

    #convert data to sstd format:
    #convert WGS84 coords to Web Mercator projected coordinates
    dataframe['x'], dataframe['y'] = zip(*dataframe[['long','lat']].apply(lambda coords: convert_coordinates(*coords), axis=1))
    dataframe.drop(['long', 'lat'], axis=1, inplace=True)

    #Calcluate the extent of the sstd volume
    min_x = dataframe['x'].min()
    max_x = dataframe['x'].max()
    min_y = dataframe['y'].min()
    max_y = dataframe['y'].max()
    extent_size = max(distance(min_x, max_x), distance(min_y, max_y))

    #convert epoch timestamp to relative seconds count within the data set
    dataframe['t'] = dataframe['timestamp_epoch'].apply(lambda timestamp: ((timestamp - starttime_epoch)/endtimestamp_seconds)*extent_size)
    dataframe.drop('timestamp_epoch', axis=1, inplace=True)

    # find the spread of the positional data
    raw_x_diff = distance(min_x, max_x)
    raw_y_diff = distance(min_y, max_y)
    raw_max_diff = max(raw_x_diff, raw_y_diff)

    print "rmd: " + str(raw_max_diff)
    #if the spread is larger than 10,000 kilometers, display error
    if raw_max_diff > 1000000:
        flash('Data slice contains positions with >1,000km in seperation, please select a more geographically constraigned data slice. Seperation found: ' + str(round(raw_max_diff/1000,2)) + 'km')
        return [0, (0,0)]
    #set voxel size and kernel size in metres
    if(raw_max_diff > 100000):
        voxel_size = 10000
        kernel_size = 100000
    elif(raw_max_diff > 10000):
        voxel_size = 1000
        kernel_size = 10000
    elif(raw_max_diff > 1000):
        voxel_size = 100
        kernel_size = 10000
    else:
        voxel_size = 10
        kernel_size = 100

    #to create a cubic mesh of coordinates, we must find the distance between the max and min of x and y, and use the largest distance of the two as the extent for both x, y, and z domains
    starting_x = math.floor(min_x/voxel_size) * voxel_size
    starting_y = math.floor(min_y/voxel_size) * voxel_size
    starting_z = 0

    #calculate distance between min and max x coords
    x_distance = distance(starting_x, math.ceil(max_x/voxel_size) * voxel_size)
    y_distance = distance(math.floor(min_y/voxel_size) * voxel_size, math.ceil(max_y/voxel_size) * voxel_size)
    extent_distance = max(x_distance, y_distance)

    #calculate the ending coords as the min coords plus the cube's metric extent
    ending_x = starting_x + extent_distance
    ending_y = starting_y + extent_distance
    ending_z = starting_z + extent_distance

    #Build volume space
    x = numpy.linspace(start=starting_x, stop=ending_x, num=((ending_x - starting_x) / voxel_size)+1)
    y = numpy.linspace(start=starting_y, stop=ending_y, num=((ending_y - starting_y) / voxel_size)+1)
    z = numpy.linspace(start=starting_z, stop=ending_z, num=((ending_z - starting_z) / voxel_size)+1)

    M = numpy.meshgrid(x, y, z, indexing= 'xy')

    xcoord = M[0]
    ycoord = M[1]
    zcoord = M[2]

    #initialise the total density as a 3D array of zeros with the same dimensions as xcoord/ycoord/zcoord volumes
    total_density = numpy.zeros(xcoord.shape)

    # ------------------------------------------------
    #loop across all movement objects (animals)
    objects_list = dataframe['ID'].unique()
    num_objects = len(objects_list)

    for movementobject in range(0, num_objects):
        #initialise individual object density as zeros everywhere in as 3D array of the same size as the xcoord/ycoord/zcoord volumes
        object_density = numpy.zeros(xcoord.shape)

        #find where the movementobject is in the data frame, and get just the trajectories of that object
        trajectory_df = dataframe[dataframe['ID'] == objects_list[movementobject]]

        #count the number of different trajectories (days) for this movement object, and populate a list containing the number of points in each trajectory
        traj_ids = trajectory_df['traj_id'].unique()
        num_traj = len(traj_ids)
        traj_lengths = numpy.zeros(num_traj)
        for i in range(0, num_traj):
            #find indices that have this trajectory id
            traj_id_data = trajectory_df[trajectory_df['traj_id'] == traj_ids[i]]
            #assign the number of points to the list of lengths
            traj_lengths[i] = len(traj_id_data)

        #---------------------------
        #loop through the trajectory data using the list of unique trajectory ids and for each unique traj_id extract the trajectory points and calculate the density

        for i in range(0, num_traj):
            #find the id of the current trajectory
            current_traj_id = traj_ids[i]
            current_traj_length = traj_lengths[i]

            #create a submatrix of trajectory_df containing only the points associated with the current trajectory id
            current_line = trajectory_df[trajectory_df['traj_id'] == current_traj_id]

            #calculate density for current trajectory
            density = numpy.zeros(xcoord.shape)

            #if trajectory has two or more points, calculate stacked densities around each segment
            if(current_traj_length > 1):
                density = density_around_trajectory(current_line, kernel_size, xcoord, ycoord, zcoord, voxel_size)
            #if trajectory has one point then calculate density around this point
            else:
                density = density_around_one_point(current_line, kernel_size, xcoord, ycoord, zcoord, voxel_size)

            object_density = numpy.add(object_density, density)

        #normalise object's density by dividing by number of trajectories (days)
        object_density = numpy.divide(object_density, num_traj)

        #add this individual object's density to the total density
        total_density = numpy.add(total_density, object_density)

    #normalise total density with number of individual objects
    total_density = numpy.divide(total_density, num_objects)

    #construct pandas dataframe containing (x,y,z,density) values, with number of rows = (extent/voxel_size)^3
    x_range = xcoord[0,:,0]
    y_range = ycoord[:,0,0]
    z_range = zcoord[0,0,:]

    density_df = pandas.DataFrame(list(product(xcoord[0,:,0], ycoord[:,0,0], zcoord[0,0,:])), columns=['x','y','z'])
    density_df['density'] = density_df.apply(lambda row: total_density[numpy.where(x_range == row['x'])[0][0], numpy.where(y_range == row['y'])[0][0], numpy.where(z_range == row['z'])[0][0]], axis=1)

    #create key-value pairs between projected web mercator coordinates to gps wgs84 spherical coordinates
    projected_coordinates = list(product(xcoord[0,:,0], ycoord[:,0,0]))
    coordinate_conversion_dict = {(x,y):convert_coordinates(x, y, False) for (x, y) in projected_coordinates}

    #Cast the projected orthographic coordinate pair to the gps geographic coordinate system
    density_df['long'], density_df['lat'] = zip(*density_df[['x','y']].apply(lambda coords: coordinate_conversion_dict.get((coords[0],coords[1])), axis=1))
    density_df.drop(['x', 'y'], axis=1, inplace=True)
    density_df = density_df[density_df['density'] != 0]
    density_df = density_df[density_df['density'] > density_df['density'].quantile(0.5)]

    #save density of all objects
    new_data_id = secure_filename(data_id + "_density")
    save_density(density_df, new_data_id)

    return [1, (density_df['long'].iloc[0], density_df['lat'].iloc[0]), new_data_id]

#return the Web Mercator projected geographic coord system for a given WGS84 x,y pair
def convert_coordinates(incoord1, incoord2, forwards = True):
    outcoord1 = 0
    outcoord2 = 0

    if(forwards):
        (coord1, coord2) = pyproj.transform(crs_wgs, crs_mercator, incoord1, incoord2)
    else:
        (coord1, coord2) = pyproj.transform(crs_mercator, crs_wgs, incoord1, incoord2)
    return (coord1, coord2)

#get difference between two signed values
def distance(a, b):
    if (a == b):
        return 0
    elif (a < 0) and (b < 0) or (a > 0) and (b >= 0): # fix: b >= 0 to cover case b == 0
        if (a < b):
            return (abs(abs(a) - abs(b)))
        else:
            return -(abs(abs(a) - abs(b)))
    else:
        return math.copysign((abs(a) + abs(b)),b)
