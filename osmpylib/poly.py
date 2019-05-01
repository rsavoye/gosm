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


class Poly(object):
    """Class to manage a map polygons"""
    def __init__(self):
        self.filespec = None
        pass
    
    def getBBox(self, filespec):
        self.filespec = filespec
        self.file = open(filespec, "r")
        
        data = list()
        lines = self.file.readlines()
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
                break
            coords = line.split()
            ring.AddPoint(float(coords[0]), float(coords[1]))

        poly = ogr.Geometry(ogr.wkbLinearRing)
        poly.AddGeometry(ring)
        # Get Envelope returns a tuple (minX, maxX, minY, maxY)
        bbox = ring.GetEnvelope()
        return bbox

    def getXapi():
        # XAPI uses:
        # minimum latitude, minimum longitude, maximum latitude, maximum longitude
        xbox = "%s,%s,%s,%s" % (bbox[2], bbox[0], bbox[3], bbox[1])
        xapi = "(\nway(%s);\nnode(%s)\nrel(%s)\n<;\n>;\n);\nout meta;" % (str(xbox), str(xbox), str(xbox))
        print(xapi)

