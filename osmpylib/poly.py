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
## \file poly.py Handle polygon files

import os
import sys
import logging
import getopt
import epdb
from osgeo import ogr
from sys import argv
sys.path.append(os.path.dirname(argv[0]) + '/osmpylib')
import mercantile

# https://wiki.openstreetmap.org/wiki/Osmosis/Polygon_Filter_File_Format
# This class currently this class ignores subtracting areas, since our
# whole purpose is on processing map tiles. Subtracted parts don't
# apply to basemaps.
class Poly(object):
    """Class to manage a OSM map polygons"""
    def __init__(self, filespec=None):
        self.filespec = None
        self.geometry = None
        if filespec is not None:
            self.filespec = filespec
            self.readPolygon(filespec)

    def getName(self):
        return self.filespec

    def readPolygon(self, filespec):
        self.filespec = filespec
        self.file = open(filespec, "r")
        #data = list()
        lines = self.file.readlines()
        #curname = ""
        ring = ogr.Geometry(ogr.wkbLinearRing)
        for line in lines:
            # Ignore the first two lines
            if line[0] != ' ':
                continue
            line = line.rstrip()
            line = line.lstrip()
            if line == 'END' or line == '1' or line == '2' or line[0] == '!':
                #break
                continue
            coords = line.split()
            if len(coords) > 1:
                ring.AddPoint(float(coords[0]), float(coords[1]))

        poly = ogr.Geometry(ogr.wkbPolygon)
        poly.AddGeometry(ring)

        multipoly = ogr.Geometry(ogr.wkbMultiPolygon)
        multipoly.AddGeometry(poly)
        multipoly.CloseRings()
        self.geometry = multipoly
        # ExportToWkt adds a 0 elevation, which has to be stripped off as
        # it's not used by the TM database
        #text =  multipoly.ExportToWkt().replace(" 0,", ",")
        #return text.replace("0)", ")")
        return self.geometry

    def getWkt(self):
        text = self.geometry.ExportToWkt().replace(" 0,", ",")
        return text.replace("0)", ")")

    def getGeometry(self):
        return self.geometry

    def exportKMLBBox(self, filespec=None):
        bbox = self.getBBox(filespec)
        kml = """<coordinates>\n\t\t%g,%g %g,%g %g,%g %g,%g %g,%g\n\t    </coordinates>""" % (bbox[0], bbox[3], bbox[1], bbox[3], bbox[1], bbox[2], bbox[0], bbox[2], bbox[0], bbox[3])
        return kml

    def getBBox(self, filespec=None):
        if filespec is None:
            filespec = self.filespec
        else:
            self.filespec = filespec
        self.file = open(filespec, "r")
        
        #data = list()
        lines = self.file.readlines()
        #curname = ""
        ring = ogr.Geometry(ogr.wkbLinearRing)
        for line in lines:
            # Ignore the first two lines
            if line[0] != ' ':
                continue
            line = line.rstrip()
            line = line.lstrip()
            if line == 'END' or line == '1' or line == '2' or line[0] == '!':
                continue
            coords = line.split()
            if len(coords) > 1:
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

    def dump(self):
        if self.geometry is None:
            logging.warning("No data yet")
            return 1
        print("Area:\t %d" % self.geometry.GetArea())
        print("Wkt:\t %s" % self.getWkt())
        print("Centroid: %s" % self.geometry.Centroid())
        #print("KML:\t%s" % self.getKML())
        bbox = self.geometry.GetEnvelope()
        print("Envelope: (%s, %s, %s ,%s)" % (bbox[0], bbox[1], bbox[2], bbox[3]))
