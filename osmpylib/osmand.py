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

import os
import sys
import logging
import epdb
from sys import argv
sys.path.append(os.path.dirname(argv[0]) + '/osmpylib')
from tiledb import Tile
from tiledb import Tiledb

#http://osmand.net/help-online/technical-articles#OsmAnd_SQLite_Spec

# OsmAnd sqlitedb schema
# CREATE TABLE tiles (x int, y int, z int, s int, image blob, time long, PRIMARY KEY (x,y,z,s));
# CREATE INDEX IND on tiles (x,y,z,s);
# CREATE TABLE info(tilenumbering,minzoom,maxzoom,timecolumn,url,rule,referer);
# CREATE TABLE android_metadata (locale TEXT);

# sqlite> SELECT * FROM tiles LIMIT 5;
# 3391|6200|3|0|����
# 3391|6201|3|0|����
# 3391|6202|3|0|����
# 3392|6200|3|0|����
# 3392|6201|3|0|����
# sqlite> 
# sqlite> SELECT * FROM info;
# 2|3
# sqlite>
# sqlite> SELECT * FROM android_metadata;
# en_US
# sqlite> 

# OsmAnd sqlite is based on "Bigplanet sqlite" which was supported by MOBAC before OsmAnd.
# OsmAnd added couple of columns & tables to extend the format:

# Table "info":

#     url - url template to download tiles with zoom - $1, x - $2 , y - $3
#     rule - specific to osmand (mostly "" or "beanshell" for evaluating url template for downloading tiles)
#     tilenumbering - supported "BigPlanet" or "". If BigPlanet zoom will be inverted and calculated as z = 17 - zoom
#     timeSupported - "yes", "no" - means that tiles table has column "time" means when tile was retrieved
#     expireminutes - integer - if tiles should be expired in given minutes, they will be displayed but they will be downloaded again
#     ellipsoid - integer 1/0. Elliptic mercator (Yandex tiles)
#     minzoom, maxzoom - (also should be inversive in case of BigPlanet)
#     referer - to be used while downloading

# Table "tiles"

#     Columns x, y, z - zoom could be inversive in case of BigPlanet - indicates tile mercaator coordinates
#     image - blob of bytes of image
#     time - timestamp when image was downloaded.


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
        #sql.append("CREATE TABLE IF NOT EXISTS android_metadata (locale TEXT);")

        for i in sql:
            self.cursor.execute(i)

    def addTile(self, tile):
        zoomosm = dict()
        zoomosm[10] = 7
        zoomosm[11] = 6
        zoomosm[12] = 5
        zoomosm[13] = 4
        zoomosm[14] = 3
        zoomosm[15] = 2
        zoomosm[16] = 1
        zoomosm[17] = 0
        zoomosm[18] = -1
        zoomosm[19] = -2
        min = 0
        max = 0
        """Add a tile to the database"""
        x = tile.getX()
        y = tile.getY()
        # FIXME: this is the actual zoom level, needs to be converted
        # to 1,2,3 etc...
        z = zoomosm[int(tile.z)]
        filespec = tile.getFilespec()
        s = 0                   # This field appears to always be zero
        blob = sqlite3.Binary(tile.getImage())
        if blob is None:
            logging.warning("Tile $r/%r/%r has no image!" % (z,x,y))
            return False
            
        logging.debug("Adding tile for %s into the database" % filespec)
        # This field appears to always be zero
        s = 0
        sql = """INSERT INTO tiles(x,y,z,s,image) VALUES(?,?,?,?,?);"""
        try:
            self.cursor.execute(sql, (y,x,z,s,blob))
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
                z = tile.getZ()
                if z < min:
                    min = z
                if z > max:
                    max = z
        sql = """INSERT INTO info(minzoom,maxzoom) VALUES(?,?);"""
        try:
            zooms = self.cursor.fetchall()
            self.cursor.execute(sql, (min, max))
        except:
            return False

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
            newtile.dump()
            osmand.addTile(newtile)

    def addFromFile(self, filespec):
        file = open(filespec, "r")
        lines = file.readlines()
        for line in lines:
            if line[0] == '#':
                continue

            newtile = Tile(line.rstrip())
            newtile.dump()
            osmand.addTile(newtile)
        sql = """DELETE FROM info;"""
        try:
            self.cursor.execute(sql)
            self.cursor.fetchall()
        except:
            return False
        sql = """INSERT INTO info(minzoom,maxzoom) VALUES(?,?);"""
        try:
            zooms = self.cursor.fetchall()
            self.cursor.execute(sql, (min(self.zooms), max(self.zooms)))
        except:
            return False
        logging.info("Wrote to database")

    def allDone(self):
        """Close the database so changes don't get lost"""
        logging.debug("Closing the database %r" % self.db)

        self.db.commit()
        self.db.close()
