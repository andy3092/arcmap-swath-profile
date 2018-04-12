import math
import logging
import collections

import numpy as np
import scipy.stats
#import arcpy

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
    return 180 - north_bearing

def row_stats(array, pixel_size):
    """
    Takes a numpy array and pixcel size. Returns a table of the 
    stats for each row. Min, Max, Mean, std. That can then be used for
    plotting swath graphs. 
    """
    number_rows = np.shape(array)[0]
    distance = np.arange(0, number_rows * pixel_size, pixel_size)
    mean = np.mean(array, axis=1)
    minimum = np.amin(array, axis=1)
    maximum = np.amax(array, axis=1)
    #median = np.median(array, axis=1)
    std = np.std(array, axis=1)
    minus_1std = mean - std
    plus_1std = mean + std
    kurtosis = scipy.stats.kurtosis(array, axis=1, fisher=True, bias=True)
    
    #logging.debug('distance: {}'.format(distance))
    
    return np.column_stack((distance, maximum, minimum, mean, std, minus_1std, 
                            plus_1std, kurtosis))

def main(profile_line, dem, swath_width, output_csv):
    """
    The main processing of the data and extraction 
    of the profile data. Takes a
    line feature class or feature set
    raster dem 
    buffer distance as linar units e.g. ("5 Meters")
    outputfile_name
    """
    # Collect data from our input layers
    #arcpy.AddMessage("No DataValue: {}".format(dem_nodata))                                                             
    spatail_reference = arcpy.Describe(profile_line).spatialReference

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
            buffer_fc = 'in_memory//buffer'
            # Need to halve the width to get the correct buffer distance
            buffer_distance = float(swath_width.split()[0])/2 
            buffer_linear_units = "{} {}".format(buffer_distance, swath_width.split()[1])
            arcpy.AddMessage("Buffering the profile line by: {}".format(buffer_linear_units))
            arcpy.Buffer_analysis(line, buffer_fc, 
                              buffer_distance, "FULL", "FLAT", "NONE", "", "GEODESIC")

            # Clip the dem to the buffer
            arcpy.AddMessage("Clipping the raster by the buffer")
            output_clip = "in_memory//clip"
            arcpy.Clip_management(dem, "", output_clip, buffer_fc, "", "ClippingGeometry", 
                                  "MAINTAIN_EXTENT")

            # Roate the dem so that it is upright
            bearing = north_bearing(line.firstPoint, line.lastPoint)
            rotation = rotation_angle(bearing) 
            arcpy.AddMessage("Rotating raster by {}".format(rotation))
            out_rotate = "in_memory//rotate"
            arcpy.Rotate_management(output_clip, out_rotate, rotation)

            # Convert the dem to a numpy array and prepear it for the stats
            # need to skip nodata values in array
            # need to stip out lines of nodata
            arcpy.AddMessage("Converting the roated dem to a numpy array")
            dem_array = arcpy.RasterToNumPyArray(out_rotate, nodata_to_value=-9999)
            dem_array_skip_nd = np.ma.masked_array(dem_array, dem_array == -9999)
            mask_nd_rows = np.all(np.isnan(dem_array_skip_nd), axis=1)
            dem_arr = dem_array_skip_nd[~mask_nd_rows]

            # Run the Stats and save the output csv file
            dem_cellsize_result = arcpy.GetRasterProperties_management(out_rotate, "CELLSIZEY")
            dem_cell_size = dem_cellsize_result.getOutput(0)
            stats = row_stats(dem_arr, dem_cell_size)
            arcpy.AddMessage("Writing () to disk.".format(output_csv))
            np.savetxt(output_csv, stats, 
                       header="distance, max, min, mean, std, minus_1std, plus_1std, kurtosis", 
                       fmt='%1d,  %1.3f,  %1.3f,  %1.3f, %1.3f, %1.3f, %1.3f, %1.3f', 
                       comments='')

        
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
    main(profile_line, dem, swath_width, output_csv)


    # Get the parameters
    #input_raster = arcpy.GetParameterAsText(0)
    #stats_type = arcpy.GetParameterAsText(1)
    #output_raster_name = arcpy.GetParameterAsText(2)
    #profile_line = arcpy.GetParameter(3)

    #test()




