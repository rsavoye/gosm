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

from sys import argv
import shapefile
import ogr
import gosm
import osm
import kml

# file="/home/rob/.gosmrc"
# if __name__ == '__main__':

#     """Start Stuff"""
#     def __init__(self, file=""):
#         self.file = file        

dd = gosm.config(argv)
dd.dump()

# Read the conversion data
ctable = gosm.datafile()
ctable.open("/work/Mapping/OSM/osmtools/default.conv")
ctable.read()
#print ("BAR: %s " % ctable.match('name1'))

#shp="/work/Mapping/Utah/ArchaeologySites/ArchaeologySites.shp"
#shp = open("/work/Mapping/Utah/Trails/Trails-new.shp", "rb")
#dbf = open("/work/Mapping/Utah/Trails/Trails-new.dbf", "rb")
#sf = shapefile.Reader(shp=shp, dbf=dbf)
#fields = sf.fields
# fcount = len(sf.fields)
#
#shapes = sf.shapes()
#print ("Shapes: %d" % len(shapes))

# Read Shape (ERSI) file
shp = gosm.shpfile(dd)
shp.open("/work/Mapping/Utah/Trails/Trails-new.shp")
#shp.dump()

# Write KML file
if dd.get('format') == 'kml':
    kmlfile = '/tmp/tmp.kml'
    kml = kml.kmlfile()
    kml.open(kmlfile)
    shp.makeKML(osm)

# Write OSM file
if dd.get('format') == "osm":
    osmfile = "/tmp/tmp.osm"
    osm = osm.osmfile(dd)
    osm.open(osmfile, shp)
    shp.makeOSM(osm)

