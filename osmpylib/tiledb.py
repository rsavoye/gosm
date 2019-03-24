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

import os
import sys
import logging
import epdb
from sys import argv
sys.path.append(os.path.dirname(argv[0]) + '/osmpylib')
import mercantile


class tiledb(object):
    def __init__(self, top=None):
        """Initialize and manage a database of map tiles"""
        self.perms = 0o755
        if top is None:
            self.storage = "tiledb"
        else:
            self.storage = top
        # Default zooms levels. Below these are usually too far away to
        # be useful, and above this, the files are huge.
        self.zooms = [14, 15, 16, 17]
        self.makeDir(self.storage)

    def formatPath(self, tile=None):
        path = "%s/%s/%s/%s" % (self.storage, tile.z, tile.x, tile.y)
        return path
        

    def makeTileDir(self, tile=None):
        if tile is None:
            logging.error("Need to specify a tile!")
            return False

        return self.makeDir(self.formatPath(tile))
        
    def makeDir(self, dir=None):
        if dir is None: 
            logging.error("Need to specify a directory!")
            return False

        if os.path.isdir(dir) is False:
            try:
                os.makedirs(dir, self.perms)
                return False
            except OSError:  
                print ("Creation of the directory %s failed" % dir)
        return True

    def tileExists(self, tile=None):
        if tile is None:
            logging.error("Need to specify a tile!")
            return False
        return os.path.exists(self.formatPath(tile))

    def getXDirs(self, zoom=14):
        top = self.storage + '/' + str(zoom)
        files = list()
        if os.path.isdir(top) is True:
            xdirs = os.listdir(top)
            print(xdirs)
            for dir in xdirs:
                if os.path.isdir(dir) is True:
                    files.append(dir)
        else:
            xdirs = list()
        return xdirs

    def getX\YDirs(self, zoom=14, x=0):
        top = self.storage + '/' + str(zoom)
        top += "/" + x
        files = list()
        if os.path.isdir(top) is True:
            xdirs = os.listdir(top)
            print(xdirs)
            for dir in xdirs:
                if os.path.isdir(dir) is True:
                    files.append(dir)
        else:
            xdirs = list()
        return xdirs

    def getTile(self, zoom=14, x=0, y=0):
        if self.tileExists(tile) is False:
            return False
        return True

    def writeTile(self, tile=None):
        if tile is None:
            logging.error("Tile doesn't exist! x=%s, y=%s, z=%s" % (tile.x, tile.y, tile.z))
            return False
        print(self.formatPath(tile))
        return True
        
