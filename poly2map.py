#!/usr/bin/python3

# 
# Copyright (C) 2019, 2020   Free Software Foundation, Inc.
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

# ogr2ogr -t_srs EPSG:4326 Roads-new.shp hwy_road_aerial.shp

# lynx  https://clarity.maptiles.arcgis.com/arcgis/rest/services/World_Imagery/MapServer/tile/14/6193/3359
# lynx https://c.tile.opentopomap.org/14/3359/6193.png
# lynx https://caltopo.s3.amazonaws.com/topo/13/1679/3096.png

import os
import sys
import logging
import getopt
import epdb
from osgeo import gdal,ogr,osr
from sys import argv
sys.path.append(os.path.dirname(argv[0]) + '/osmpylib')
import logging
from sys import argv
sys.path.append(os.path.dirname(argv[0]) + '/osmpylib')
import osm
#import config
from poly import Poly
from kml import kmlfile


class myconfig(object):
    def __init__(self, argv=list()):
        # Read the config file to get our OSM credentials, if we have any
        file = os.getenv('HOME') + "/.gosmrc"
        try:
            gosmfile = open(file, 'r')
        except Exception as inst:
            logging.warning("Couldn't open %s for writing! not using OSM credentials" % file)
            return
         # Default values for user options
        self.options = dict()
        self.options['logging'] = True
        self.options['verbose'] = False
        self.options['poly'] = ""

        try:
            (opts, val) = getopt.getopt(argv[1:], "h,p:,v",
                                        ["help", "poly", "verbose"])
        except getopt.GetoptError as e:
            logging.error('%r' % e)
            self.usage(argv)
            quit()

        for (opt, val) in opts:
            if opt == '--help' or opt == '-h':
                self.usage(argv)
            elif opt == "--poly" or opt == '-p':
                self.options['poly'] = val
            elif opt == "--verbose" or opt == '-v':
                self.options['verbose'] = True
                logging.basicConfig(filename='tiler.log',level=logging.DEBUG)

    def checkOptions(self):
        # make this a nop for now
        pass
         
    def get(self, opt):
        try:
            return self.options[opt]
        except Exception as inst:
            return False

    def dump(self):
        logging.info("Dumping config")

        for i, j in self.options.items():
            print("\t%s: %s" % (i, j))

    # Basic help message
    def usage(self, argv=["poly2map.py"]):
        print("This program reads an OSM poly file, and exports it as a KML MultyiPolygon")
        print(argv[0] + ": options:")
        print("""\t--help(-h)   Help
\t--poly(-p)      Input OSM polyfile
\t--verbose(-v)   Enable verbosity
        """)
        quit()



dd = myconfig(argv)
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

if dd.get('infile') == "":
    dd.usage()
    quit()
else:
    infile = dd.get('poly')

filespec = infile.replace(".poly", "")
base = os.path.basename(filespec)

tmp = base + ".kml"
kml = kmlfile()
kml.open(tmp)
print("Output file: %r" % tmp)
kml.header(os.path.basename(tmp))

poly = Poly(infile)
poly.dump()
#for index in fooby:
#    way = fooby[index].ExportToKML()
#    if index < 0:
#        way.replace("outer", "inner")
        # We do want to add map data for internal areas, so ignore inner
        # boundaries.
        #kml.placemark("Inner test " + str(index), 'polygon', way.replace("outer", "inner"), 'inner')

kml.placemark("Outer test", 'multipolygon', poly.getPolygons())
kml.footer()

#way = poly.ExportToKML()

quit()

# Write OSM file
tmp = base + ".osm"
osm = osm.osmfile(dd, tmp)
print("Output file: %r" % tmp)
osm.header()

bbox = poly.getBBox()
refs = []
# Make a rectangular polygon for tasking  manager
#Upper left
# top line
attrs = dict()
attrs['lat'] = str(bbox[3])
attrs['lon'] = str(bbox[0])
node = osm.node(list(), attrs) + 1
refs.append(node)

# Upper Right
attrs = dict()
attrs['lat'] = str(bbox[3])
attrs['lon'] = str(bbox[1])
node = osm.node(list(), attrs) + 1
refs.append(node)

# Right side
# Lower Right
attrs = dict()
attrs['lat'] = str(bbox[2])
attrs['lon'] = str(bbox[1])
node = osm.node(list(), attrs) + 1
refs.append(node)

# Lower Left
attrs = dict()
attrs['lat'] = str(bbox[2])
attrs['lon'] = str(bbox[0])
node = osm.node(list(), attrs) + 1
refs.append(node)
refs.append(node - 1)

# bottom
# Close the polygon
attrs = dict()
attrs['lat'] = str(bbox[3])
attrs['lon'] = str(bbox[0])
node = osm.node(list(), attrs)
refs.append(node)

alltags = list()
tag = osm.makeTag("name", infile)
alltags.append(tag)
tag = osm.makeTag("type", "multipolygon")
alltags.append(tag)
print(refs)
osm.makeWay(refs, alltags)

osm.footer()
