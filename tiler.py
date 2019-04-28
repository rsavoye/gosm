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
from tiledb import tiledb
import rasterio
from rasterio.merge import merge
from rasterio.enums import ColorInterp
import overpy
import osm
import urllib.request
from urllib.parse import urlparse


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
        self.options['zooms'] = 13,14,15
        self.options['poly'] = ""
        self.options['source'] = "ersi,topo,terrain"
        self.options['format'] = "gtiff"
        #self.options['force'] = False
        self.options['outdir'] = "./"
        # FIXME: 
        self.options['mosaic'] = False
        self.options['download'] = False
        self.options['ersi'] = False
        self.options['topo'] = False
        self.options['terrain'] = False
        self.options['gtiff'] = False
        self.options['pdf'] = False
        self.options['osmand'] = False

        try:
            (opts, val) = getopt.getopt(argv[1:], "h,o:,s:,p:,v,z:,f:,d,m",
                ["help", "outdir", "source", "poly", "verbose", "zooms", "format", "download", "mosaic"])
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
            elif opt == "--download" or opt == '-d':
                self.options['download'] = True
            elif opt == "--mosaic" or opt == '-m':
                self.options['mosaic'] = True
            elif opt == "--zooms" or opt == '-z':
                self.options['zooms'] = ( val.split(',' ) )
            elif opt == "--format" or opt == '-f':
                self.options['format'] = val
            elif opt == "--verbose" or opt == '-v':
                self.options['verbose'] = True
                logging.basicConfig(filename='tiler.log',level=logging.DEBUG)

    def checkOptions(self):
        """Range check some of the ptions here to reduce cutter when parsing"""
        logging.info("Range check options")
        if self.options['poly'] == None:
            print("ERROR: need to specify a polygon!")
            usage()
        for name, val in self.options.items():
            print("\t%s: %s" % (name, val))
            if name == "zooms":
                for i in val:
                    if int(i) < 14 or int(i) > 18:
                        print("%r out of zoom range" % i)
                        self.usage()
            if name == "source":
                srcs = val.split(',')
                for i in srcs:
                    if i == "ersi" or i == "topo" or i == "terrain":
                        self.options[i] = True
                        continue
                    else:
                        print("%r unsupported source" % i)
                        self.usage()
            if name == "format":
                fmts = val.split(',')
                for i in fmts:
                    if i == "gtiff" or i == "pdf" or i == "osmand":
                        self.options[i] = True
                        continue
                    else:
                        print("%r unsupported format" % i)
                        self.usage()

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
    def usage(self, argv=["tiler.py"]):
        print("This program downloads map tiles and the geo-references them")
        print(argv[0] + ": options:")
        print("""\t--help(-h)   Help
\t--outdir(-o)  Output directory for tiles
\t--source(-s)  Map source (default, topo)
                ie... topo,terrain,ersi
\t--poly(-p)    Input OSM polyfile
\t--format(-f)  Output file format,
                ie... GTiff, PDF, AQM, OSMAND
\t--zooms(-z)   Zoom levels to download (14-18)
\t--verbose(-v) Enable verbosity
        """)
        quit()


dd = myconfig(argv)
dd.checkOptions()
#dd.dump()
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

#poly = poly.poly(dd.get('poly'))

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
# print(bbox)
# print(ring.GetArea())
# print(ring.Length())
# kml = ring.ExportToKML()

# XAPI uses:
# minimum latitude, minimum longitude, maximum latitude, maximum longitude
xbox = "%s,%s,%s,%s" % (bbox[2], bbox[0], bbox[3], bbox[1])
print("------------------------")
#xapi = "(\n  way(%s);\n  node(%s);\n  rel(%s);\n  <;\n  >;\n);\nout meta;" % (box , xbox, xbox)
xapi = "(way(%s);node(%s);rel(%s);<;>;);out meta;" % (xbox, xbox, xbox)
#print(xapi)

polyfile = dd.get('poly')
polyname = os.path.basename(polyfile.replace(".poly", ""))
uri = 'https://overpass-api.de/api/interpreter'
headers = dict()
headers['Content-Type'] = 'application/x-www-form-urlencoded'
req = urllib.request.Request(uri, headers=headers)
x = urllib.request.urlopen(req, data=xapi.encode('utf-8'))
osmfile = open(polyname + '.osm', 'w')
output = x.read().decode('utf-8')
osmfile.write(output)
osmfile.close()

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

topodb = tiledb("Topo")
terraindb = tiledb("Terrain")
hybridb = tiledb("Hybrid")
ersidb = tiledb("ERSI")

# tiles = list(mercantile.tiles(bbox[0], bbox[2], bbox[1], bbox[3], dd.get('zooms')))
zoom = 14,15,16,17
#zoom =  tuple(dd.get('zooms'))
tiles = list(mercantile.tiles(bbox[0], bbox[2], bbox[1], bbox[3], zoom))
# (OpenTopo uses Z/X/Y.png format
url = ".tile.opentopomap.org/{0}/{1}/{2}.png"
mirrors = [ "https://a" + url, "https://b" + url, "https://c" + url ]
if dd.get('download') and dd.get('topo'):
    if topodb.download(mirrors, tiles):
        logging.info("Done downloading Terrain data")
if dd.get('mosaic') is True and dd.get('topo'):
    topodb.mosaic(tiles)

# Zooms seems to go to 19, 18 was huge, and 17 was fine
zoom = 15,16,17
tiles = list(mercantile.tiles(bbox[0], bbox[2], bbox[1], bbox[3], zoom))
url = "http://clarity.maptiles.arcgis.com/arcgis/rest/services/World_Imagery/MapServer/tile/{0}/{2}/{1}"
mirrors = [url]
if dd.get('download') and dd.get('ersi'):
    if ersidb.download(mirrors, tiles):
        logging.info("Done downloading Sat imagery")
if dd.get('mosaic') is True and dd.get('ersi'):
    ersidb.mosaic(tiles)

# 16 appears to be the max zoom level available
zoom = 15,16
tiles = list(mercantile.tiles(bbox[0], bbox[2], bbox[1], bbox[3], zoom))
url = "http://caltopo.s3.amazonaws.com/topo/$Z/$X/$Y.png"
mirrors = [url]
if dd.get('download') and dd.get('terrain'):
    if terraindb.download(mirrors, tiles):
        logging.info("Done downloading Topo data")
if dd.get('mosaic') is True and dd.get('terrain'):        
    terraindb.mosaic()

    
#url = ".google.com/vt/lyrs=h&x=$X&y=$Y&z=$Z&scale=1" % (tile.x, tile.y, tile.z)
#mirrors = [ "https://mt0" + url, "https://mt1" + url, "https://mt2" + url ]
#print("lynx " + url + '\n')
#hybridb.download(mirrors)

# # lat increases northward, 0 - 90
# # lon increases eastward, 0 - 180 

