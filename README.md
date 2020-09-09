# arcmap-swath-profile
A simple tool that creates a swath profile from a Digital Surface Model (DSM). 
The tool is written for ArcMap 10.x and is therefore in Python 2.7

Allows you to specify the width of the profile. 

The tool works by taking the DSM and rotating it so it is vertical. 
It then calulates the statistics for each row of the DSM. 

The general methold is discussed in the following link.
https://sites.google.com/site/sorsbysj/geospatial-processing/geospatial-analyses/swath-profiles
