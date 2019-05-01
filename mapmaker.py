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

## \copyright GNU Public License.
## \file mapmaker.py Creates maps from tiles

import os
import sys
import logging
import getopt
import epdb
from osgeo import ogr
from sys import argv
sys.path.append(os.path.dirname(argv[0]) + '/osmpylib')
import sqlite3
import filetype
import mercantile
from osgeo import gdal
# These modules are part of this project
import poly
from tiledb import Tile
from tiledb import Tiledb
from subprocess import PIPE, Popen, STDOUT
ON_POSIX = 'posix' in sys.builtin_module_names


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
        self.options['poly'] = None
        self.options['sqlite'] = None
        self.options['input'] = None
        self.options['format'] = "gtiff"
        #self.options['force'] = False
        self.options['outfile'] = "./exported-tiles"

        try:
            (opts, val) = getopt.getopt(argv[1:], "h,o:,s:,p:,v,f:,i:",
                ["help", "outfile", "sqlite", "poly", "verbose", "format", "input"])
        except getopt.GetoptError as e:
            logging.error('%r' % e)
            self.usage(argv)
            quit()

        for (opt, val) in opts:
            if opt == '--help' or opt == '-h':
                self.usage(argv)
            elif opt == "--outfile" or opt == '-o':
                self.options['outfile'] = val
            elif opt == "--sqlite" or opt == '-s':
                self.options['sqlite'] = val
            elif opt == "--poly" or opt == '-p':
                self.options['poly'] = val
            elif opt == "--input" or opt == '-i':
                self.options['input'] = val
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
                if val is not None:
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
    def usage(self, argv=["mapmaker.py"]):
        print("This program creates maps from tiles")
        print(argv[0] + ": options:")
        print("""\t--help(-h)   Help
\t--outfile(-o)  Output filename if expanding into tiles
\t--source(-s)   Map data source
\t--poly(-p)     Input OSM polyfile
\t--input(-i)    Text file of filenames
\t--format(-f)   Output file format,
                 ie... GTiff, PDF, AQM, OSMAND
\t--verbose(-v)  Enable verbosity
        """)
        quit()


dd = myconfig(argv)
#dd.checkOptions()
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


class Osmand(object):
    def __init__(self, db):
        """Class for managing an Osm sqlite database"""
        self.sqlite = db
        self.db = sqlite3.connect(db)
        self.cursor = self.db.cursor()
        logging.debug("Opened database %r" % db)
        self.createDB()
        # See how many records are in the database
        tmp = self.cursor.execute("SELECT COUNT(*) FROM tiles;")
        self.count =  self.cursor.fetchone()[0]
        logging.info("%s has %r tiles" % (db, self.count))
        # Get the zoom levels
        self.zooms = list()
        tmp = self.cursor.execute("SELECT DISTINCT(z) FROM tiles;")
        for i in self.cursor.fetchall():
            self.zooms.append(i[0])
            tmp = self.cursor.execute("SELECT COUNT(*) FROM tiles WHERE z=%r;" % i[0]).fetchone()
            logging.info("Zoom level %r has %r tiles" % (i[0], tmp[0]))
        logging.info("%s has zoom levels %r" % (db, self.zooms))

        
    def createDB(self):
        """Create an Osmand compatable database"""
        #self.db = sqlite3.connect(db)
        #self.cursor = self.db.cursor()
        
        sql = list()
        sql.append("CREATE TABLE IF NOT EXISTS tiles (x int, y int, z int, s int, image blob, PRIMARY KEY (x,y,z,s));")
        sql.append("CREATE INDEX IF NOT EXISTS IND on tiles (x,y,z,s);")
        sql.append("CREATE TABLE IF NOT EXISTS info(minzoom,maxzoom);")
        sql.append("CREATE TABLE IF NOT EXISTS android_metadata (locale TEXT);")

        for i in sql:
            self.cursor.execute(i)

    def addTile(self, tile):
        # 211|387|7|0|����	10
        # 423|775|6|0|����	11
        # 847|1551|5|0|����	12
        # 1694|3102|4|0|����	13
        # 3389|6204|3|0|����	14
        # 6778|12408|2|0|����	15
        zoomosm = dict()
        zoomosm[10] = 7
        zoomosm[11] = 6
        zoomosm[12] = 5
        zoomosm[13] = 4
        zoomosm[14] = 3
        zoomosm[15] = 2
        zoomosm[16] = 1
        zoomosm[17] = 0
        #zoomosm = (17, 16, 15, 14, 13, 12, 11, 10)

        """Add a tile to the database"""
        x = tile.getX()
        y = tile.getY()
        # FIXME: this is the actual zoom level, needs to be converted
        # to 1,2,3 etc...
        z = zoomosm[int(tile.z)]
        filespec = tile.getFilespec()
        s = 0                   # This field appears to always be zero
        blob = sqlite3.Binary(tile.getImage())
        logging.debug("Adding tile for %s into the database" % filespec)
        # This field appears to always be zero
        s = 0
        sql = """INSERT INTO tiles(x,y,z,s,image) VALUES(?,?,?,?,?);"""
        try:
            self.cursor.execute(sql, (x,y,z,s,blob))
            logging.debug("Got %r rows" % self.cursor.rowcount)
        except:
            return False
        
        logging.debug("Got %r rows" % self.cursor.fetchone())
        self.db.commit()
        return True

    def readTile(self, x, y, z, tile=Tile()):
        """Read a tile from the database"""
        #sql = "SELECT image FROM tiles WHERE x=%r AND y=%r AND z=%r;" % (x, y, z)
        sql = "SELECT image FROM tiles WHERE x=%r AND y=%r;" % (x, y)
        print(sql)
        try:
            self.cursor.execute(sql)
            image = self.cursor.fetchone()
            if image is None:
                logging.error("%r/%r/%r doesn't exist in the database" % (z, x, y))
                return None
            else:
                filespec = "%r/%r/%r/%r.png" % (x,y,z,y)
                tile.setCoords(x,y,z)
                tile.setImage(image[0])
        except:
            return None

        return tile

    def writeTiles(self, path):
        """This writes all the tiles in a database to disk tiles"""
        for level in self.zooms:
            logging.debug("Writing zoom level %r" % level)
            for row in self.cursor.execute("SELECT x,y,z,image FROM tiles WHERE z=%r" % level):
                #foo = mercantile.bounds(self.y, self.x, 16)
                tile = Tile()
                tile.setCoords(row[0], row[1], row[2])
                tile.setImage(row[3])
                tile.writeTile(path)

    def addLevel(self, bbox, zoom):
        tiles = list(mercantile.tiles(bbox[0], bbox[2], bbox[1], bbox[3], zoom))

        db = Tiledb("Topo")
        for tile in tiles:
            filespec = db.formatPath(tile) + '/' + str(tile.y)
            if os.path.exists(filespec + ".jpg"):
                filespec += ".jpg"
            if os.path.exists(filespec + ".png"):
                filespec += ".png"
            if os.path.exists(filespec + ".tig"):
                filespec += ".tif"

            newtile = Tile(filespec)
            osmand.addTile(newtile)

    def allDone(self):
        """Close the database so changes don't get lost"""
        logging.debug("Closing the database %r" % self.db)
        self.db.commit()
        self.db.close()

#
# Main body
#
sqlite = dd.get('sqlite')
osmand = Osmand(sqlite)
#osmand.createDB()

pp = poly.Poly()
input = dd.get('input')
bbox = pp.getBBox(input)
logging.info("Bounding box for %r is %r" % (input, bbox))

osmand.addLevel(bbox, 15)
osmand.addLevel(bbox, 16)

# This writes all the tiles in the sqlite db to disk
#path = dd.get('outfile')
#osmand.writeTiles("./foo")


# Split the single zoom level TIF file into multiple lower levels
cmd = [ 'gdal2tiles.py', '--no-kml', '--profile=raster', '/tmp/sql.tif']
#ppp = Popen(cmd, close_fds=ON_POSIX)
#ppp.wait()


osmand.allDone()
