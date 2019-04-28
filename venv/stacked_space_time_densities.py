import numpy, math

def density_around_trajectory(current_line, kernel_size, xcoord, ycoord, zcoord, voxel_size):

    #read size of the 3d rasters - xcoord, ycoord, and zcoord must be of equal size
    raster_size = xcoord.shape

    xnn = raster_size[0]-1
    ynn = raster_size[1]-1
    znn = raster_size[2]-1

    min_x_coord = min(xcoord[0,:,0])
    max_x_coord = max(xcoord[0,:,0])
    x_range = max_x_coord-min_x_coord

    min_y_coord = min(ycoord[:,0,0])
    max_y_coord = max(ycoord[:,0,0])
    y_range = max_y_coord-min_y_coord

    min_z_coord = min(zcoord[0,0,:])
    max_z_coord = max(zcoord[0,0,:])
    z_range = max_z_coord-min_z_coord

    kx = xnn/x_range
    ky = ynn/y_range
    kz = znn/z_range

    nx = (max_x_coord-(xnn+1)*min_x_coord)/x_range
    ny = (max_y_coord-(ynn+1)*min_y_coord)/y_range
    nz = (max_z_coord-(znn+1)*min_z_coord)/z_range

    #initialise an empty vcoord (density Volume)
    vcoord = numpy.zeros(xcoord.shape)

    #get length of trajectory
    lll = current_line.shape
    points = lll[0]
    col = lll[1]

    #calculate density by going through the trajectory segment by segment
    n = 0
    while n < points - 1:
        #subsample trajectory to voxel rows:
        #take two consecutive points, P(xn, yn, zn) and P1(xn1, yn1, zn1) where P(xn1,yn1,zn1) is the first point that is temporaly away for more than a voxel size that point P1(xn,yn,zn) i.e. zn1-zn2>voxel_size
        xn = current_line["x"].iloc[n]
        yn = current_line["y"].iloc[n]
        zn = current_line["t"].iloc[n]

        #find the first next trajectory point that is in the next voxel row
        n1 = n+1
        while (n1 < points - 1) and (current_line["t"].iloc[n1] - current_line["t"].iloc[n]) <= voxel_size:
            n1 = n1+1

        xn1 = current_line['x'].iloc[n1]
        yn1 = current_line['y'].iloc[n1]
        zn1 = current_line['t'].iloc[n1]

        #define the temporal boundaries around the segment within which the density will be calculated
        kn = int(min(round(kz*zn+nz), round(kz*zn1+nz)))
        kn1 = int(max(round(kz*zn+nz), round(kz*zn1+nz)))

        #loop through all voxel layers that intersect segment P-P1
        for k in range(kn, kn1):

            #interpolate the point at level k
            #interpolated between P and P1, this point has coordinates (xc, yc, zc).
            #p = interpolation parameter on the line segment, [0,1] from P to P1
            #if kn and kn1 are in the same voxel layer, then just take the middle point between P and P1 and don't interpolate
            if kn != kn1:
                p = k/(kn1-kn) - kn/(kn1-kn)
            else:
                p = 0.5

            xc = xn+p*(xn1-xn)
            yc = yn+p*(yn1-yn)
            zc = zn+p*(zn1-zn)

            #calculate density
            for i in range(0, xnn):
                for j in range(0, ynn):

                    #calculate distance from each voxel in the bounding box around the line segment to the interpolated point on the line segment at that temporal level (i.e. at that k)
                    #(x,y,z)= voxel point(i,j,k)
                    #(xc,yx,zc)=interpolated point on line segment at level k
                    x = xcoord[j,i,k]
                    y = ycoord[j,i,k]
                    z = zcoord[j,i,k]
                    dist = math.sqrt(squared_distance_two_points((x,y,z),(xc,yc,zc)))

                    #linear decay function
                    if dist > kernel_size:
                        vcoord[j,i,k] = 0
                    else:
                        vcoord[j,i,k] = linear_decay(dist, kernel_size, voxel_size)
        n = n + 1
    return vcoord

def density_around_one_point(current_line, kernel_size, xcoord, ycoord, zcoord, voxel_size):
    #read size of the 3d rasters - xcoord, ycoord, and zcoord must be of equal size
    raster_size = xcoord.shape

    xnn = raster_size[0]-1
    ynn = raster_size[1]-1
    znn = raster_size[2]-1

    min_x_coord = min(xcoord[0,:,0])
    max_x_coord = max(xcoord[0,:,0])
    x_range = max_x_coord-min_x_coord

    min_y_coord = min(ycoord[:,0,0])
    max_y_coord = max(ycoord[:,0,0])
    y_range = max_y_coord-min_y_coord

    min_z_coord = min(zcoord[0,0,:])
    max_z_coord = max(zcoord[0,0,:])
    z_range = max_z_coord-min_z_coord

    kx = xnn/x_range
    ky = ynn/y_range
    kz = znn/z_range

    nx = (max_x_coord-(xnn+1)*min_x_coord)/x_range
    ny = (max_y_coord-(ynn+1)*min_y_coord)/y_range
    nz = (max_z_coord-(znn+1)*min_z_coord)/z_range

    #initialise and empty vcoord (density Volume)
    vcoord = numpy.zeros(xcoord.shape)

    #calculate the density by finding the layer of the given point and calculate the desnity around it
    xn = current_line["x"].iloc[0]
    yn = current_line["y"].iloc[0]
    zn = current_line["t"].iloc[0]

    #find temporal voxel layer of this point
    k = int(round(kz * zn * nz))

    #calculate density
    for i in range(0, xnn):
        for j in range(0, ynn):

            #calculate distance from each voxel in the bounding box around the line segment to the interpolated point on the line segment at that temporal level (i.e. at that k)
            #(x,y,z)= voxel point(i,j,k)
            #(xc,yx,zc)=interpolated point on line segment at level k
            x = xcoord[j,i,k]
            y = ycoord[j,i,k]
            z = zcoord[j,i,k]
            dist = math.sqrt(squared_distance_two_points((x,y,z),(xn,yn,zn)))

            #linear decay function
            if dist > kernel_size:
                vcoord[i,j,k] = 0
            else:
                vcoord[i,j,k] = linear_decay(dist, kernel_size, voxel_size)
    return vcoord

#calculates squared distance between 2 points in 3D,
#given as (x,y,z) and (x1,y1,z1).
def squared_distance_two_points((x,y,z),(x1,y1,z1)):
  return math.pow(x-x1, 2) + math.pow(y-y1, 2) + math.pow(z-z1, 2)

#calculates the linear decay weighting function
#h must be positive (kernel distance), x must be in [0,h]
#to get the density value, this is then multiplied with voxel area.
def linear_decay(distance, kernel_size, voxel_size):
    #calculate linear decay in 2D
    f = (3 / (math.pi * math.pow(kernel_size, 2))) * (kernel_size - distance) / kernel_size

    #scale to voxel area:
    #multiply with the 2D surface of the voxel
    f = f * math.pow(voxel_size, 2)

    return f
