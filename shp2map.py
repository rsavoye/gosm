#!/usr/bin/python3

# 
#   Copyright (C) 2017   Free Software Foundation, Inc.
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# 

# This is a simple bourne shell script to convert raw OSM data files into
# pretty KML. This way when the KML file is loaded into an offline mapping
# program, all the colors mean something. For example, ski trails and
# bike/hiking trails have difficulty ratings, so this changes the color
# of the trail. For skiing, this matches the colors the resorts use. Same
# for highways. Different types and surfaces have tags signifying what type
# it is.

# from sys import os
# cwd = os.getcwd()
# sys.path.append(cwd + '/../subdirA/')

import os
import sys
from sys import argv
sys.path.append(os.path.dirname(argv[0]) + '/osmpylib')

import logging
import osm
import shp
import config

# file="/home/rob/.gosmrc"
# if __name__ == '__main__':

#     """Start Stuff"""
#     def __init__(self, file=""):
#         self.file = file        

dd = config.config(argv)
dd.dump()

# Read Shape (ERSI) file
shp = shp.shpfile(dd)
if dd.get('infile') == "":
    infile = "/work/Mapping/Utah/Trails/Trails-new.shp"
else:
    infile = dd.get('infile')

shp.open(infile)
if dd.get('dump') is True:
    shp.dump()
    quit()

# Write KML file
if dd.get('format') == 'kml':
    if dd.get('outfile') == "":
        kmlfile = '/tmp/tmp.kml'
    else:
        kmlfile = dd.get('outfile')
    kml = kml.kmlfile()
    kml.open(kmlfile)
    shp.makeKML(osm)

# Write OSM file
elif dd.get('format') == "osm":
    if dd.get('outfile') == "":
        osmfile = "/tmp/tmp.osm"
    else:
        osmfile = dd.get('outfile')
    osm = osm.osmfile(dd)
    osm.open(osmfile, shp)
    shp.makeOSM(osm)
    print("Output file: %r" % osmfile)

# Write CSV file
elif dd.get('format') == "csv":
    if dd.get('outfile') == "":
        csvfile = "/tmp/tmp.csv"
    else:
        csvfile = dd.get('outfile')
    csv = csv.osmfile(dd)
    csv.open(csvfile, shp)
    shp.makeCSV(csv)
    print("Output file: %r" % csvfile)

