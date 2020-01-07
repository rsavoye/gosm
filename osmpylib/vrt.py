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
# https://gdal.org/python/osgeo.gdal-module.html

import os
import sys
import logging
import epdb
from osgeo import gdal,ogr,osr
from sys import argv
sys.path.append(os.path.dirname(argv[0]) + '/osmpylib')


class gdalGCP(object):
    def __init__(self, tile=None, gps=None):
        """Initialize a VRT file for gdal transformations"""
        if  tile is None:
            self.x = 0
            self.y = 0
        else:
            self.x = tile.x
            self.y = tile.y
        if gps is None:
            self.lon = 0
            self.lat = 0
        else:
            self.lat = gps.lat
            self.lon = gps.lon

    def addGPS(self, gps=None):
        if gps is None:
            logging.error("")
            return False
        else:
            self.lat = gps.lat
            self.lon = gps.lon

    def addTile(self, tile=None):
        if tile is None:
            logging.error("")
            return False
        else:
            self.x = tile.x
            self.y = tile.y

    def getString(self, str=None):
        if self.x == 0 or self.y == 0 or self.lat == 0 or self.lon == 0:
            logging.error("Incomplete data for GCP!")
            return None
        str = "<GCP Id=\"\" Pixel=\"%s\" Line=\"%s\" X=\"%s\" Y=\"%s\" % (self.x, self.y, self.lon, self.lat)"
        return str


class gdalVRT(object):
    def __init__(self, options=None):
        """Initialize a VRT file for gdal transformations"""
        self.gcp = list()
        self.options = options

    def addGCP(self, gcp=None):
        if gcp is None:
            logging.error("")
            return False
        self.gcp.append(gcp)

    def writeVRT(self, filespec="./out.vrt"):
        file = open(filespec, "x")
        for i in self.gcp:
            print(self.getString())

    def create(self, layer):
        """Create a VRT file for this layer to use as the datasource"""
        outdir = os.path.dirname(self.options.get('outfile')) + "/"
        outdir = "/tmp/"
        poly = os.path.basename(self.options.get('poly')).replace(".poly", "")
        basedir = self.options.get('basedir') + "/vrt/"
        template = basedir + layer + ".vrt"
        infile = open(template, "r")
        # FIXME: output file in current directory
        outfile = outdir + poly + "-" + layer + ".vrt"
        out = open(outfile, "w")
        for line in infile.readlines():
            # Ignore blank lines or comments
            if line == '' or line[1] == '#':
                continue
            comp = line.lstrip()
            if comp[:14] == "<SrcDataSource":
                line = line.replace("XxXxX", "bar2.osm")
            out.write(line)
        out.close()

    def build(self):
        opts = gdal.BuildVRTOptions(outputSRS='EPSG:4326')
        gdal.BuildVRT(opts)

    def apply(self):
        """Apply the datasource to the original file"""
        infile = self.options.get('input')
        pdffile = self.options.get('outfile')
        imgfile = gdal.Open(infile)
        # imgfile.RasterXSize, imgfile.RasterYSize
        # This creates a new PDF with this data source layer on top
        pdfdriver = gdal.GetDriverByName("PDF")
        pdfdriver.CreateCopy(pdffile, imgfile, 
                             options=['OGR_DATASOURCE=test-addrs.vrt',
                                      'AUTHOR=Rob Savoye',
                                      'OGR_DISPLAY_FIELD=num'])

        # # opts = gdal.WarpOptions(format='PDF', dstSRS='EPSG:4326')
        # # opts = gdal.TranslateOptions("barby2.pdf", imgfile)
        # # ds1 = gdal.Warp("barby2.pdf", infile)

        # logging.debug("Attempting to add layer to %s" % infile)
        osmdriver = ogr.GetDriverByName("OSM")
        # # all OSM files produced by this software use negative numbers,
        # # and should never be uploaded.
        # gdal.SetConfigOption('OSM_USE_CUSTOM_INDEXING', 'NO')
        pdfdriver = ogr.GetDriverByName("PDF")
        outpdf = pdfdriver.Open(infile, 0)
        layer = outpdf.CreateLayer("barby", geom_type=ogr.wkbPoint)
        # layer = outpdf.GetLayer()
        # Execute SQL query on OSM file
        sql = 'SELECT addr_street,addr_housenumber AS num FROM points WHERE addr_housenumber is not NULL'
        osmfile = ogr.Open("bar2.osm")
        points = osmfile.ExecuteSQL(sql)
        # #layer = datasrc.CreateLayer("barby", geom_type=ogr.wkbPoint)
        for feature in points:
            feature.SetStyleString('LABEL(f:"Times New Roman",s:29px,t:{num},c:#000000FF)')
            geom = feature.geometry()
            print(feature.GetField('num'), geom.GetPoint_2D())
            layer.CreateFeature(feature)
        # #gdal.VectorTranslate("fur.pdf", osmfile, format="PDF", SQLStatement='%s' % sql)
        # #layer.SyncToDisk()
