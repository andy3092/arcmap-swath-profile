import math
import logging
import collections

import numpy as np
import scipy.stats
import arcpy
import block_processing

#-----------------------------------------
# Set up logging 
#-----------------------------------------
logging.basicConfig(format='%(levelname)s:%(message)s',
                    level=logging.DEBUG)

def north_bearing(pointA, pointB):
    """
    Takes two points that define a line
    Then calculates the bearing of the line from North
    """
    angle = math.atan2((pointB.X - pointA.X), (pointB.Y - pointA.Y))
    return math.degrees(angle)

def rotation_angle(north_bearing):
    """
    Takes the bearing from north and returns 
    the amount the dem needs to be rotated so that
    the first point entered for the profile line is at 
    the top of the dem.
    """
    return north_bearing * -1

def row_stats(numpy_array):
    """
    Takes a numpy array. Returns a table of the 
    stats for each row. Min, Max, Mean, std. That can then be used for
    plotting swath graphs. 
    The function throws a ValueError if a line of 
    NoData is passed to it.
    """
    number_rows = np.size(numpy_array, axis=0)
    mean = np.mean(numpy_array, axis=1)
    minimum = np.amin(numpy_array, axis=1)
    maximum = np.amax(numpy_array, axis=1)
    std = np.std(numpy_array, axis=1)
    minus_1std = mean - std
    plus_1std = mean + std
    kurtosis = scipy.stats.kurtosis(numpy_array, axis=1, fisher=True, bias=True)
    
    #logging.debug('distance: {}'.format(distance))
    
    #arcpy.AddMessage(distance)
    #arcpy.AddMessage(maximum)
    #arcpy.AddMessage(minimum)
    #arcpy.AddMessage(mean)
    #arcpy.AddMessage(std)
    #arcpy.AddMessage(minus_1std)
    #arcpy.AddMessage(plus_1std)
    #arcpy.AddMessage(kurtosis)

    return np.column_stack((maximum, minimum, mean, std, minus_1std, 
                            plus_1std, kurtosis))

def main(profile_line, in_raster, swath_width, output_csv, 
         ncols=None, nrows=None):
    """
    The main processing of the data and extraction 
    of the profile data.

    Arguments:
    line feature class or feature set
    raster dem 
    buffer distance as linar units e.g. ("5 Meters")
    outputfile csv name
    Optional arguments
    ncols numbger of rows default is the raster height
    nrows number of columns default is the raster width

    The main function buffers the profile line, then clips
    the raster and roates it so that it runs from north to south
    witth a bearing of 0 degrees.
    The raster is then found for each row and placed in a csv file
    """
    # Set enviromntal variables
    arcpy.env.overwriteOutput = True

    # Collect data from our input layers
    spatail_reference = arcpy.Describe(profile_line).spatialReference
    arcpy.AddMessage("spatial reference is:{}".format(spatail_reference.name))
    
    cursor = arcpy.da.SearchCursor(profile_line, ["SHAPE@"])
    SHAPE_INDEX = 0
    for feature in cursor:
        for part in feature[SHAPE_INDEX]:    
            line = arcpy.Polyline(part, spatail_reference)
            arcpy.AddMessage("first X: {}".format(line.firstPoint.X))
            arcpy.AddMessage("first Y: {}".format(line.firstPoint.Y))
            arcpy.AddMessage("last X: {}".format(line.lastPoint.X))
            arcpy.AddMessage("last Y: {}".format(line.lastPoint.Y))
        
            # Buffer the profile line 
            #buffer_fc = "{}\\buffer".format(arcpy.env.scratchGDB)
            buffer_fc = "in_memory\\buffer"
            # Need to halve the width to get the correct buffer distance
            buffer_distance = float(swath_width.split()[0])/2 
            buffer_linear_units = "{} {}".format(buffer_distance, 
                                                 swath_width.split()[1])
            arcpy.AddMessage("Buffering the profile line by: {}"
                             .format(buffer_linear_units))
            arcpy.Buffer_analysis(line, buffer_fc, 
                                  buffer_linear_units, 
                                  "FULL", 
                                  "FLAT", 
                                  "NONE", "", 
                                  "GEODESIC")
            
            # Clip the dem to the buffer
            arcpy.AddMessage("Clipping the raster by the buffer")
            output_clip = "{}\\clip".format(arcpy.env.scratchGDB)
            arcpy.Clip_management(dem, "", 
                                  output_clip, buffer_fc,
                                  "", "ClippingGeometry") 
                                  #"MAINTAIN_EXTENT")

            # Roate the dem so that it is upright
            bearing = north_bearing(line.firstPoint, line.lastPoint)
            rotation = rotation_angle(bearing) 
            if rotation <= 1:
                arcpy.AddMessage("No rotation needed")
                out_rotate = output_clip
            else:
                arcpy.AddMessage("Rotating raster by {}".format(rotation))
                out_rotate = "{}\\rotate".format(arcpy.env.scratchGDB)
                arcpy.Rotate_management(output_clip, out_rotate, rotation)

            # Convert the dem to a numpy array and prepear it for the stats
            # need to skip nodata values in array
            # need to stip out lines of nodata
            # This needs to be done in bloks or else we run out of memory.

            arcpy.AddMessage("Converting the roated dem to a numpy array")
            dem_raster = arcpy.Raster(out_rotate)
            dem_cell_size = int(dem_raster.meanCellWidth)
            stats_result = None

            arcpy.AddMessage("Pixel Size: {} ".format(dem_cell_size))
            dem_blocks = block_processing.EnumRasterToNumPyArray(out_rotate, 
                                                                 num_rows=nrows)
            for dem_array in dem_blocks:
                dem_array_skip_nd = np.ma.masked_array(dem_array, 
                                                       dem_array == -9999)
                mask_nd_rows = np.all(np.isnan(dem_array_skip_nd), axis=1)
                dem_arr = dem_array_skip_nd[~mask_nd_rows]
                # Need to flip it as the array starts at the bottom 
                # lefthand corner
                dem_arr_flip = np.flipud(dem_arr)
                try:
                    stats = row_stats(dem_arr_flip)
                except ValueError: 
                    continue
                if stats_result is None:
                    stats_result = stats
                else:
                    stats_result = np.vstack((stats_result, stats))
            
            number_rows = np.size(stats_result, axis=0)
            distance = np.arange(0, number_rows * dem_cell_size, dem_cell_size)
            distance_reshape = distance.reshape(number_rows, 1)
            distance_stats = np.hstack((distance_reshape, stats_result))
            arcpy.AddMessage("Writing {} to disk.".format(output_csv))    
            np.savetxt(output_csv, distance_stats, 
                       header="distance, max, min, mean, std, minus_1std, plus_1std, kurtosis", 
                       fmt='%1d,  %1.3f,  %1.3f,  %1.3f, %1.3f, %1.3f, %1.3f, %1.3f', 
                       comments='')

            # Clean up
            file_list = [out_rotate, output_clip, buffer_fc]
            for file_item in file_list:
                if arcpy.Exists(file_item):
                    arcpy.Delete_management(file_item)
        
def test():
    # Set up some dummy lines
    Point = collections.namedtuple('Point', 'X Y')
    Line = collections.namedtuple('Line', 'Direction PointA PointB')
    center = Point(X=10, Y=10)
    lines = [Line(Direction='north',PointA=center, PointB=Point(X=10,Y=16)),
             Line(Direction='northeast',PointA=center, PointB=Point(X=16,Y=16)),
             Line(Direction='east',PointA=center, PointB=Point(X=16,Y=10)),
             Line(Direction='southeast',PointA=center, PointB=Point(X=19,Y=1)),
             Line(Direction='south',PointA=center, PointB=Point(X=10,Y=1)),
             Line(Direction='southwest',PointA=center, PointB=Point(X=1,Y=1)),
             Line(Direction='west',PointA=center, PointB=Point(X=1,Y=10)),
             Line(Direction='northwest',PointA=center, PointB=Point(X=1,Y=19))]

    for line in lines:
        angle = north_bearing(line.PointA,line.PointB)
        logging.debug("{} bearing: {}".format(line.Direction, angle))
        logging.debug("{} roatation angle: {}".format(line.Direction, rotation_angle(angle)))

    # Create a numpy array with a 
    mu = 100
    std = 5
    sample_data = np.random.normal(mu, std, (3,300))
    logging.debug(sample_data)
    stats = row_stats(sample_data, 15)
    np.savetxt("temp.csv", stats, 
               header="distance, max, min, mean, std, minus_1std, plus_1std, kurtosis", 
               fmt='%1d,  %1.3f,  %1.3f,  %1.3f, %1.3f, %1.3f, %1.3f, %1.3f', comments='')

if __name__ == "__main__":
    dem = arcpy.GetParameterAsText(0)
    swath_width = arcpy.GetParameterAsText(1)
    profile_line = arcpy.GetParameter(2)
    output_csv = arcpy.GetParameterAsText(3)
    main(profile_line, dem, swath_width, output_csv, nrows=100)




