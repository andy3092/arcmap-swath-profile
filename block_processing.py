# Note that, if the input raster is multiband, the data blocks will also be
# multiband, having dimensions (bands, rows, columns).  Otherwise, they will
# have dimensions (rows, columns).

import arcpy
import numpy

def EnumRasterToNumPyArray(input_raster, num_cols=None, num_rows=None):
    """
    Takes a raster and processess and returns a generator object
     with the specified blocksize to enumerate over the array
     the raster reads from the bottom left hand corner and up first then 
     across the raster.

     Parmeters
     input_raster   Raster to convert to numpy array
     num_cols       The number of columns in the block
                    if none is given defaults to the width of the 
                    raster.
      num_rows      The number of rows in the block
                    if none is given it defaults to the height of the 
                    raster.
    """
    my_raster = arcpy.Raster(input_raster)
    if num_cols is None:
        num_cols = my_raster.width
    
    if num_rows is None:
        num_rows = my_raster.height

    arcpy.AddMessage("Number of rows: {}".format(num_rows))
    arcpy.AddMessage("Number Columns: {}".format(num_cols))

    for x in range(0, my_raster.width, num_cols):
        for y in range(0, my_raster.height, num_rows):
            mx = my_raster.extent.XMin + x * my_raster.meanCellWidth
            my = my_raster.extent.YMin + y * my_raster.meanCellHeight
            lx = min([x + num_cols, my_raster.width])
            ly = min([y + num_rows, my_raster.height])   
            my_data = arcpy.RasterToNumPyArray(my_raster, arcpy.Point(mx, my),
                                               ncols=lx-x, nrows=ly-y)
        
            yield my_data

if __name__ == "__main__":
    input_raster = arcpy.GetParameterAsText(0)
    some_data = EnumRasterToNumPyArray(input_raster, num_rows=None, num_cols=2)
    #for block in some_data:
        #arcpy.AddMessage("first_element is {}".format(block[0][0]))
        #arcpy.AddMessage("row is {}".format(block))
