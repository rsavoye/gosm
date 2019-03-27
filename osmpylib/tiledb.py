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
from osgeo import ogr
from urllib.parse import urlparse


class tiledb(object):
    """Class to manage a map tiles"""
    def __init__(self, top=None, levels=None):
        """Initialize and manage a database of map tiles"""
        self.perms = 0o755
        self.dest = None
        self.tifs = list()
        if top is None:
            self.storage = "./tiledb"
        else:
            self.storage = "./tiledb/" + top
        # Default zoom levels. Below these are usually too far away to
        # be useful, and above this, the files are huge.
        if levels is None:
            self.zooms = ( 13, 14, 15, 16 )
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
        self.errors = 0

    def createVRT(self, filespec=None, tile=None):
        if filespec is None:
            logging.error("Need to supply a file to process!")
            return

        self.drv = gdal.GetDriverByName("VRT")
        base = os.path.splitext(filespec)
        self.vrt = self.drv.Create(base[0] + ".vrt", self.tilesize, self.tilesize, bands=0)
        self.metadata = self.drv.GetMetadata()
        self.vrt.AddBand(gdal.GDT_Byte)
        band = self.vrt.GetRasterBand(1)
        #idx = "%s/%s/%s" % (tile.z, tile.x, tile.y)
        simple = '<SourceFilename relativeToVRT=\"1\">%s</SourceFilename>' % os.path.basename(filespec)
        
        band.SetMetadataItem("SimpleSource", simple)
        bbox = mercantile.bounds(tile)
        # x=0.0, y=0.0, z=0.0, pixel=0.0, line=0.0,
        gcpList = [gdal.GCP(bbox.west,bbox.north,0,0,0),
                   gdal.GCP(bbox.east,bbox.north,0,256,0),
                   gdal.GCP(bbox.east,bbox.south,0,256,256),
                   gdal.GCP(bbox.west,bbox.south,0,0,256)]
        self.vrt.SetGCPs(gcpList, str(''))  # Add the GCPs to the VRT file
        self.makeTileDir(tile)
        tmpfile = base[0] + '-tmp.tif'
        outfile = base[0] + '.tif'
        imgfile = gdal.Open(filespec, gdal.GA_ReadOnly)
        ds1 = gdal.Translate(tmpfile, imgfile, GCPs = gcpList)
        gdal.Warp(outfile, ds1, format='GTiff')
        self.tifs.append(outfile)
        os.remove(tmpfile)

    def getTifs(self):
        return self.tifs

    def download(self, mirrors=None, tiles=None):
        """ Download the specified tiles from the list of mirrors"""
        if mirrors is None:
            logging.error("You need to specify a URL!")
            return None
        if tiles is None:
            logging.error("You need to specify a tile!")
            return None

        for tile in tiles:
            fixed = ()
            for url in mirrors:
                new = url.format(tile.z, tile.x, tile.y)
                fixed = fixed + (new,)

            # Download path for files. Due to how Z/X/Y are arranged,
            # it's possible the path we use for tile storage isn't
            # the path part of the URL.
            self.dest = self.formatPath(tile) + "/"
            #logging.debug("DEST: %r" % self.dest)

            path = urlparse(url)[2]
            tmp = os.path.splitext(os.path.basename(fixed[0]))
            ext = tmp[1]
            # If there is no extension, it's a directory. Usually
            # in that case, it's a jpeg. We test the actual file
            # type later after it's downloaded, but this is to test
            # for the existence of an existing file, post download.
            if ext == '':
                filespec = self.dest + str(tile.y) + ".jpg"
            else:
                filespec = self.dest + str(tile.y) + ".png"

            #logging.debug("FILESPEC: %r" % filespec)
            if os.path.exists(filespec) is False:
                try:
                    logging.debug("Downloading %r/%r!" % (self.dest, path))
                    dl = SmartDL(fixed, dest=self.dest, connect_default_logger=True)
                    #logging.debug("SmartDL DEST: %r" % fixed[0])
                    dl.start()
                except:
                    logging.error("Couldn't download from %r!" %  dl.get_errors())
                    self.errors += 1
                    #epdb.set_trace()
                if dl.isSuccessful():
                    if dl.get_speed() > 0.0:
                        logging.info("Speed: %s" % dl.get_speed(human=True))
                    # ERSI does't append the filename
                    tmp = os.path.splitext(dl.get_dest())
                    if ext == '':
                        os.rename(dl.get_dest(), filespec)
                        logging.debug("Renamed %r" % dl.get_dest())
                        ext = ".jpg"  # FIXME: probably right, but shouldbe a better test
                    else:
                        ext = tmp[1]

            self.createVRT(filespec, tile)
        return True
        
    def formatPath(self, tile=None):
        if tile is None:
            logging.error("You need to supply a tile!")
            return None
        path = "%s/%s/%s/%s" % (self.storage, tile.z, tile.x, tile.y)
        return path
        

    def getErrors(self):
        return self.errors

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

    def getZDirs(self):
        top = self.storage + '/'
        files = list()
        if os.path.isdir(top) is True:
            zdirs = os.listdir(top)
            #print(zdirs)
            for dir in zdirs:
                if os.path.isdir(dir) is True:
                    files.append(dir)
        else:
            xdirs = list()
        return zdirs

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

    def mosaic(self, tiles=None):
        if tiles is None:
            logging.error("Need to specify tiles!")
            return

        for tile in tiles:
            file = topodb.formatPath(tile) + "/" + str(tile.y) + ".tif"
            src = rasterio.open(file)
            src.colorinterp = [ColorInterp.red, ColorInterp.green, ColorInterp.blue]
            logging.debug("Y: %r" % file)
            tifs.append(src)

            # # Merge function returns a single mosaic array and the transformation info

            mosaic, out_trans = merge(tifs)
            out_meta = src.meta.copy()

            # Update the metadata
            out_meta.update({"driver": "GTiff",
                             "height": mosaic.shape[1],
                             "width": mosaic.shape[2],
                             "transform": out_trans,
                             "crs": "+proj=utm +zone=35 +ellps=GRS80 +units=m +no_defs "
            }
            )

        with rasterio.open("Terrain.tif", "w", **out_meta) as dest:
            #dest.colorinterp = [ ColorInterp.red, ColorInterp.green, ColorInterp.blue]
            dest.write(mosaic)
