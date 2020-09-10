# arcmap-swath-profile
A simple tool that creates a swath profile from a Digital Surface Model (DSM). 
The tool is written for ArcMap 10.x and is therefore in Python 2.7

Allows you to specify the width of the profile. 

The tool works by buffering the profile line, then clips the raster to the buffer. The raster is then roated 
so that it runs from north to south with a bearing of 0 degrees. 
 The stats is then found for each row of the raster file and the results are placed in a csv file with the distance
 ready for plotting. 

The general methold is discussed in the following link.  
https://sites.google.com/site/sorsbysj/geospatial-processing/geospatial-analyses/swath-profiles
