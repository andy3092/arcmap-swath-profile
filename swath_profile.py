import math
import logging
import collections

import numpy as np
import scipy.stats
#import arcpy

#-----------------------------------------
# Set up logging 
#-----------------------------------------
logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)

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
    minus_std = mean - std
    plus_1std = mean + std
    kurtosis = scipy.stats.kurtosis(array, axis=1, fisher=True, bias=True)
    
    #logging.debug('mean: {}'.format(mean))
    #logging.debug('min: {}'.format(min))
    #logging.debug('max: {}'.format(max))
    #logging.debug('median: {}'.format(median))
    #logging.debug('std: {}'.format(std))
    #logging.debug('lower quartile: {}'.format(lower_quatile))
    #logging.debug('upper quartile: {}'.format(upper_quatile))
    #logging.debug('distance: {}'.format(distance))
    
    return np.column_stack((distance, maximum, minimum, mean, std, minus_std, plus_1std, kurtosis))

def main(dem_raster, stats_type, profile_line, output_table):
    """
    The main processing of the data and extraction 
    of the profile data. 
    """
    pass

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
    # Get the parameters
    #input_raster = arcpy.GetParameterAsText(0)
    #stats_type = arcpy.GetParameterAsText(1)
    #output_raster_name = arcpy.GetParameterAsText(2)
    #profile_line = arcpy.GetParameter(3)

    test()




