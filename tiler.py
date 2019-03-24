#!/usr/bin/python3

# 
#   Copyright (C) 2019   Free Software Foundation, Inc.
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

"""
This programs merges two data files together. The first one is an OSM
file of parcel boundaries, which usually includes no metadata. The
metadata is in another file, usually a CSV file. So this splices the
metadata from the CSV file into the OSM file.
"""

# lynx  https://clarity.maptiles.arcgis.com/arcgis/rest/services/World_Imagery/MapServer/tile/14/6193/3359
# lynx https://c.tile.opentopomap.org/14/3359/6193.png
# lynx https://caltopo.s3.amazonaws.com/topo/13/1679/3096.png

import os
import sys
import logging
import getopt
import epdb
from osgeo import ogr
from sys import argv
sys.path.append(os.path.dirname(argv[0]) + '/osmpylib')
import urllib.request
import math
import mercantile


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
        self.options['source'] = ""
        self.options['outdir'] = "./out"

        try:
            (opts, val) = getopt.getopt(argv[1:], "h,o:,s:,p:,v,",
                ["help", "outdir", "source", "poly", "verbose"])
        except getopt.GetoptError as e:
            logging.error('%r' % e)
            self.usage(argv)
            quit()

        for (opt, val) in opts:
            if opt == '--help' or opt == '-h':
                self.usage(argv)
            elif opt == "--outfile" or opt == '-o':
                self.options['outfile'] = val
            elif opt == "--source" or opt == '-s':
                self.options['source'] = val
            elif opt == "--poly" or opt == '-p':
                self.options['poly'] = val
            elif opt == "--verbose" or opt == '-v':
                self.options['verbose'] = True
                logging.basicConfig(filename='parcels.log',level=logging.DEBUG)

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
    def usage(self, argv):
        print(argv[0] + ": options:")
        print("""\t--help(-h)   Help
\t--outdir(-o)   Output directory for tiles
\t--source(-s)   Map source (default, topo)
                 ie... topo,terrain,sat
\t--poly(-p)     Input OSM polyfile
\t--verbose(-v)  Enable verbosity
        """)
        quit()


dd = myconfig(argv)
dd.dump()
if len(argv) <= 2:
    dd.usage(argv)

# The logfile contains multiple runs, so add a useful delimiter
try:
    logging.info("-----------------------\nStarting: %r " % argv)
except:
    pass

# if verbose, dump to the terminal as well as the logfile.
if dd.get('verbose') == 1:
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    root.addHandler(ch)

outfile = dd.get('outfile')
mod = 'action="modifiy"'

#outfile = open(filespec, "w")

file = open(dd.get('poly'), "r")
data = list()
lines = file.readlines()
curname = ""
skip = 0
ring = ogr.Geometry(ogr.wkbLinearRing)
for line in lines:
    # Ignore the first two lines
    if skip <= 2:
        skip = skip + 1
        continue
    line = line.rstrip()
    line = line.lstrip()
    if line == 'END' or line[0] == '!':
        continue
    coords = line.split()
    ring.AddPoint(float(coords[0]), float(coords[1]))

# multipolygon = ogr.Geometry(ogr.wkbMultiPolygon)
# multipolygon.AddGeometry(poly)

poly = ogr.Geometry(ogr.wkbLinearRing)
poly.AddGeometry(ring)
# Get Envelope returns a tuple (minX, maxX, minY, maxY)
bbox = ring.GetEnvelope()
print(bbox)
# print(ring.GetArea())
# print(ring.Length())
# kml = ring.ExportToKML()

# XAPI uses:
# minimum latitude, minimum longitude, maximum latitude, maximum longitude
xbox = "%s,%s,%s,%s" % (bbox[2], bbox[0], bbox[3], bbox[1])
print("------------------------")
xapi = "(\nway(%s);\nnode(%s)\nrel(%s)\n<;\n>;\n);\nout meta;" % (str(xbox), str(xbox), str(xbox))
print(xapi)

# lynx https://c.tile.opentopomap.org/14/3359/6193.png

#with urllib.request.urlopen(url) as response:
#   html = response.read()
#   print(html)
# tiles(west, south, east, north, zooms, truncate=False)

# https://clarity.maptiles.arcgis.com/arcgis/rest/services/World_Imagery/MapServer/tile/Z/Y/X
# https://caltopo.s3.amazonaws.com/topo/Z/X/Y.png
# https://a.tile.opentopomap.org/Z/X/Y.png"
# https://b.tile.opentopomap.org/Z/X/Y.png"
# https://c.tile.opentopomap.org/Z/X/Y.png"
# https://mt.google.com/vt/lyrs=s&x=${X}&amp;y=${y}&z=${Z} -- Satellite
# https://mt.google.com/vt/lyrs=y&amp;x=${X}&amp;y=${y}&z=${Z} -- Hybrid
# https://mt.google.com/vt/lyrs=t&amp;x=${X}&amp;y=${y}&z=${Z} -- Terrain 
# https://mt.google.com/vt/lyrs=p&amp;x=${X}&amp;y=${y}&z=${Z} -- Terrain, Streets and Water

# (-105.689729, -105.408747, 39.932244, 40.021688)
# https://a.tile.opentopomap.org/13/1696/3102.png
# https://basemap.nationalmap.gov/ArcGIS/rest/services/USGSTopo/MapServer/tile/13/3102/1696
# http://mt0.google.com/vt/lyrs=h&x=1696&y=3102&z=13&scale=1

zoom = 13
foo1 = mercantile.Bbox(bbox[0], bbox[2], bbox[1], bbox[3])
foo2 = list(mercantile.tiles(bbox[0], bbox[2], bbox[1], bbox[3], zoom))
for tile in foo2:
    #print("%r, %r, %r" % (tile.x, tile.y, tile.z))
    url = "http://a.tile.opentopomap.org/%s/%s/%s.png" % (tile.z, tile.x, tile.y)
    print("lynx " + url)
    
    url = "http://clarity.maptiles.arcgis.com/arcgis/rest/services/World_Imagery/MapServer/tile/%s/%s/%s" % (tile.z, tile.y, tile.x)
    print("lynx " + url)

    url = "http://caltopo.s3.amazonaws.com/topo/%s/%s/%s.png" % (tile.z, tile.x, tile.y)
    print("lynx " + url)

    url = "http://mt0.google.com/vt/lyrs=h&x=%s&y=%s&z=%s&scale=1" % (tile.x, tile.y, tile.z)
    print("lynx " + url + '\n')


#tiles = deg2num(bbox[3], bbox[0], zoom)
#print(tiles)
#url = "https://c.tile.opentopomap.org/%s/%s/%s.png" % (zoom, tiles[0], tiles[1])
#print(url)
#print("------------------------")
    
#     url = "https://clarity.maptiles.arcgis.com/arcgis/rest/services/World_Imagery/MapServer/tile/%s/%s/%s" % (t.z, t.x, t.y)
#     print(url)
#     print("------------------------")

#     url = "https://caltopo.s3.amazonaws.com/topo/%s/%s/%s.png" % (t.z, t.x, t.y)
#     print(url)
    
# lat increases northward, 0 - 90
# lon increases eastward, 0 - 180 
# X goes from 0 (left edge is 180 °W) to 2zoom − 1 (right edge is 180 °E)
# Y goes from 0 (top edge is 85.0511 °N) to 2zoom − 1 (bottom edge is 85.0511 °S) in a

