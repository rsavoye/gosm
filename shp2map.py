#!/usr/bin/python3

# 
#   Copyright (C) 2017, 2018   Free Software Foundation, Inc.
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

# To change the SRID to something more standard
# ogr2ogr -f "ESRI Shapefile" RoadCenterlines-new.shp RoadCenterlines.shp -t_srs "EPSG:4326"
 
import os
import sys
import logging
import osm
import shp
import config
from sys import argv
sys.path.append(os.path.dirname(argv[0]) + '/osmpylib')


dd = config.config(argv)
dd.dump()

# The logfile contains multiple runs, so add a useful delimiter
logging.info("-----------------------\nStarting: %r " % argv)

# if verbose, dump to the terminal as well as the logfile.
if dd.get('verbose') == 1:
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    root.addHandler(ch)

# Enable to make it easy to set breakpoints in pdb when debugging
# import pdb; pdb.set_trace()

# Read Shape (ERSI) file
shp = shp.shpfile(dd)
if dd.get('infile') == "":
    # infile = "/work/Mapping/Utah/Trails/Trails-new.shp"
    infile = "/work/Mapping/MapData/Gilpin/RoadCenterlines/RoadCenterlines-new"
else:
    infile = dd.get('infile')

shp.open(infile)
if dd.get('dump') is True:
    shp.dump()
    quit()

# Write KML file
# if dd.get('format') == 'kml':
#     if dd.get('outfile') == "":
#         kmlfile = '/tmp/tmp.kml'
#     else:
#         kmlfile = dd.get('outfile')
#     kml = kml.kmlfile()
#     kml.open(kmlfile)
#     shp.makeKML(osm)

# Write OSM file
elif dd.get('format') == "osm":
    outdir = dd.get('outdir')
    osmfile = dd.get('outfile')
    osm = osm.osmfile(dd, osmfile)
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

