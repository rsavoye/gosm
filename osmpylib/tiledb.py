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
from urllib.parse import urlparse
from sys import argv
sys.path.append(os.path.dirname(argv[0]) + '/osmpylib')
from pySmartDL import SmartDL
import mercantile
from osgeo import gdal
from string import Template
from osgeo import ogr


class tiledb(object):
    COMPLEX_SOURCE_XML = Template('''
    <$SourceType>
        <SourceFilename relativeToVRT="0">$Dataset</SourceFilename>
        <SourceBand>$SourceBand</SourceBand>
        <SrcRect xOff="$xOff" yOff="$yOff" xSize="$xSize" ySize="$ySize"/>
        <DstRect xOff="0" yOff="0" xSize="$xSize" ySize="$ySize"/>
    </$SourceType> ''')
    
    def __init__(self, top=None, levels=None):
        """Initialize and manage a database of map tiles"""
        self.perms = 0o755
        self.dest = None
        if top is None:
            self.storage = "./tiledb"
        else:
            self.storage = "./tiledb/" + top
        # Default zooms levels. Below these are usually too far away to
        # be useful, and above this, the files are huge.
        if levels is None:
            self.zooms = [13, 14, 15, 16, 17]
        else:
            self.zooms = levels
        self.makeDir(self.storage)
        self.data = dict()
        for zoom in self.zooms:
            self.data[zoom] = dict()
            for xdir in self.getXDirs(zoom):
                for ydir in self.getYDirs(zoom, xdir):
                    x = dict()
                    x[xdir] = ydir
                try:
                    self.data[zoom] = x
                except:
                    pass
        self.tilesize = 256

    def createVRT(self, tile=None):
        self.drv = gdal.GetDriverByName("VRT")
        path = self.formatPath(tile) + '/'
        self.vrt = self.drv.Create(path + str(tile.y) + ".vrt", self.tilesize, self.tilesize, bands=0)
        self.metadata = self.drv.GetMetadata()
        self.vrt.AddBand(gdal.GDT_Byte)
        band = self.vrt.GetRasterBand(1)
        #idx = "%s/%s/%s" % (tile.z, tile.x, tile.y)
        # Changed `x_size` and `y_size` to `x_source_size` and `y_source_size`
        # on the "SourceProperties" line, since the `RasterXSize` and `RasterYSize`
        # attributes should correspond to this source file's pixel size.
        simple = '<SourceFilename relativeToVRT=\"1\">%s</SourceFilename>' % (str(tile.y) + ".png")
        #self.metadata['SimpleSource'] = simple
#        simple += '<SourceBand>%i</SourceBand>' % 1
#        simple += '<SourceProperties RasterXSize="%i" RasterYSize="%i" DataType="Real" BlockXSize="%i" BlockYSize="%i"/>' % (self.tilesize, self.tilesize, self.tilesize, 16)
#        simple += '<SrcRect xOff="%i" yOff="%i" xSize="%i" ySize="%i"/>' % (0, 0, self.tilesize, self.tilesize)
#        simple += '<DstRect xOff="%i" yOff="%i" xSize="%i" ySize="%i"/>' % (0, 0, self.tilesize, self.tilesize)

        pngfile = gdal.Open(path + str(tile.y) + ".png", gdal.GA_ReadOnly)
        #png = gdal.GetDriverByName("GTiff")
        #png.CreateCopy(path + str(tile.y) + "X.tif", pngfile)
        #png.SetMetadataItem()
        
        band.SetMetadataItem("SimpleSource", simple)
        #epdb.set_trace()
        bbox = mercantile.bounds(tile)
        # x=0.0, y=0.0, z=0.0, pixel=0.0, line=0.0,
        gcpList = [gdal.GCP(bbox.west,bbox.north,0,0,0),
                   gdal.GCP(bbox.east,bbox.north,0,256,0),
                   gdal.GCP(bbox.east,bbox.south,0,256,256),
                   gdal.GCP(bbox.west,bbox.south,0,0,256)]
        self.vrt.SetGCPs(gcpList, str(''))  # Add the GCPs to the VRT file
        #ds1 = gdal.Translate(self.formatPath(tile) + str(tile.y) + '.tif',self.vrt,outputSRS = 'EPSG:26711',GCPs = gcpList)
        self.makeTileDir(tile)
        outfile = self.formatPath(tile) + '/' + str(tile.y) + '.tif'
        infile = self.formatPath(tile) + '/' + str(tile.y) + '.png'
        #ds = gdal.Open(infile)
        ds1 = gdal.Translate(outfile,pngfile,GCPs = gcpList)
        #warped = gdal.Warp('', , format = 'MEM', tps = True)

        # self.COMPLEX_SOURCE_XML.substitute(
        #     Dataset='test.vrt',
        #     SourceBand=1,
        #     SourceType='GTiff',
        #     xSize=self.tilesize,
        #     ySize=self.tilesize,
        #     xOff=0,
        #     yOff=0)

    def download(self, url=None, dest=None):
        if url is None:
            logging.error("You need to specify a URL!")
            return None
        logging.debug("Downloading from: %r" % url)
        if type(url) == list:
            item = url[0]
        else:
            item = url
        if item.find('&') > 0:
            foo = urlparse(item)
            tmp = item.split('&')
            end = len(tmp)
            path = "/%s/%s/%s/" % (tmp[3][2:], tmp[1][2:], tmp[2][2:])
            self.dest = self.storage + path
            i = 0

            while i < len(url):
                #url[i] =  html.escape(url[i])
                url[i] =  url[i].replace('=', '%3D')
                url[i] =  url[i].replace('&', '%26')
                print("FIXME: %r" % url[i])
                i += 1
        else:
            tmp = item.split("/")
            end = len(tmp)
            path = "/%s/%s/%s/" % (tmp[end-3], tmp[end-2], tmp[end-1].replace('.png', ''))
            logging.debug("PATH: %r" % path)
            self.dest = self.storage + path
        #epdb.set_trace()
        if os.path.exists(self.dest + tmp[end-1]) is False:
            try:
                dl = SmartDL(url, dest=self.dest, connect_default_logger=True)
                print("DEST: %r" % dl.get_dest())
                dl.start()
                if dl.isSuccessful():
                    logging.info("Speed: %s" % dl.get_speed(human=True))
            except:
                logging.error("Couldn't download from %r!" % item)
                return False
        else:
            logging.debug("Tile %r already exists." % self.dest)
        return True
        
    def formatPath(self, tile=None):
        if tile is None:
            logging.error("You need to supply a tile!")
            return None
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
            #print(xdirs)
            for dir in xdirs:
                if os.path.isdir(dir) is True:
                    files.append(dir)
        else:
            xdirs = list()
        return xdirs

    def getYDirs(self, zoom=14, x=0):
        top = self.storage + '/' + str(zoom)
        top += "/" + str(x)
        files = list()
        if os.path.isdir(top) is True:
            ydirs = os.listdir(top)
            #print(ydirs)
            for dir in ydirs:
                if os.path.isdir(dir) is True:
                    files.append(dir)
        else:
            ydirs = list()
        return ydirs

    def getTile(self, zoom=14, x=0, y=0):
        if self.tileExists(tile) is False:
            return False
        return True

    def writeTif(self):    
        driver = gdal.GetDriverByName("GTiff")
        metadata = driver.GetMetadata()
        if metadata.get(gdal.DCAP_CREATE) == "YES":
            print("Driver {} supports Create() method.".format(fileformat))
            
            if metadata.get(gdal.DCAP_CREATE) == "YES":
                print("Driver {} supports CreateCopy() method.".format(fileformat))
