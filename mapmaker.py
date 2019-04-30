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
from tiledb import tiledb
import sqlite3


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
        self.options['source'] = None
        self.options['input'] = None
        self.options['format'] = "gtiff"
        #self.options['force'] = False
        self.options['outfile'] = "./exported-tiles"

        try:
            (opts, val) = getopt.getopt(argv[1:], "h,o:,s:,p:,v,f:,i:",
                ["help", "outfile", "source", "poly", "verbose", "format", "input"])
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


class Tile(object):
    def __init__(self, imgfile=None):
        """Class to hold Tile data"""
        if imgfile is not None:
            parts = imgfile.split('/')
            size = len(parts)
            self.x = parts[size - 2]
            self.y = parts[size - 3]
            self.z = parts[size - 4]
            self.blob = self.readTile(imgfile)

    def setCoords(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def setImage(self, image):
        self.blob = image

    def getX(self):
        return self.x

    def getY(self):
        return self.y

    def getZ(self):
        return self.z

    def getImage(self):
        return self.blob

    def readTile(self, filespec):
        """Load the image into memory"""
        logging.debug("Reading tile %r into memory" % filespec)
        try:
            file = open(filespec, "rb")
        except:
            logging.error(e)
        #bytes = file.read(253210)
        self.blob = file.read()
        file.close()
        return self.blob

    def writeTile(self, path):
        """Write the image to disk"""
        filespec = "%s/%s/%s/%s/%s.png" % (path, self.z, self.x, self.y, self.y)
        #os.mkdir(os.path.dirname(filespec))
        file = open(filespec, "wb")
        bytes = self.blob
        logging.debug("Writing %r bytes to %r" % (len(bytes), filespec))
        file.write(bytes)
        file.close()
        logging.info("Wrote %r" % filespec)
        return True

    def dump(self):
        if self.blob is not None:
            image = "not loaded"
        else:
            image = "loaded"
        print("X=%s, Y=%s, Z=%s, Image is %s" % (self.z, self.x, self.y, image))

class Osmand(object):
    def __init__(self, db):
        """Class for managing an Osm sqlite database"""
        self.db = sqlite3.connect(db)
        self.cursor = self.db.cursor()
        logging.debug("Opened database %r" % db)
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

        
    def createDB(self, db):
        """Create an Osmand compatable database"""
        #self.db = sqlite3.connect(db)
        #self.cursor = self.db.cursor()
        
        sql = list()
        sql.append("CREATE TABLE IF NOT EXISTS tiles (x int, y int, z int, s int, image blob, PRIMARY KEY (x,y,z,s));")
        sql.append("CREATE INDEX IND on tiles (x,y,z,s);")
        sql.append("CREATE IF NOT EXISTS TABLE info(minzoom,maxzoom);")
        sql.append("CREATE IF NOT EXISTS TABLE android_metadata (locale TEXT);")

        for i in sql:
            self.cursor.execute(i)

    def addTile(self, tile):
        """Add a tile to the database"""
        x = tile.getX()
        y = tile.getY()
        z = tile.getZ()
        s = 0                   # This field appears to always be zero
        blob = sqlite3.Binary(tile.getImage())
        logging.debug("Adding tile %r/%r/%r into the database" % (z,x,y))
        # This field appears to always be zero
        s = 0
        #sql = "INSERT INTO tiles(x,y,z,s) VALUES(%r,%r,%r,%r)" % (x, y, z, s)
        #sql = "INSERT INTO tiles(x,y,z,s,image) VALUES(%r,%r,%r,%r)", (x, y, z, s)
        sql = "INSERT INTO tiles(x,y,z,s,image) VALUES(?,?,?,?,?);", (x,y,z,s,blob)
        try:
            self.cursor.execute(sql)
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

    def allDone(self):
        """Close the database so changes don't get lost"""
        logging.debug("Closing the database %r" % self.db)
        self.db.close()

    def writeTiles(self):
        """This writes all the tiles in a database to disk"""
        for level in self.zooms:
            self.cursor.execute("SELECT * FROM tiles WHERE z=%r" % level)
            tmp = self.cursor.fetchone()
#
# Main body
#
db = dd.get('source')
osmand = Osmand(db)
#osmand.createDB("foo.sqlitedb")

png = Tile("/work/Mapping/gosm.git/tiledb/Topo/16/13532/24818/24818.png")
#osmand.addTile(tile)
png.writeTile("./")

tile = Tile()
tile = osmand.readTile(3389, 6200, 3)
if tile is not None:
    tile.dump()
    tile.writeTile("./")

osmand.allDone()
