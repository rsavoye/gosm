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

## \file tiledb.py manage of collection of map tiles.

# ogr2ogr -t_srs EPSG:4326 Roads-new.shp hwy_road_aerial.shp

import operator
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
import rasterio
from rasterio.merge import merge
from rasterio.enums import ColorInterp
from subprocess import PIPE, Popen, STDOUT
import filetype


class Tile(object):
    def __init__(self, imgfile=None):
        """Class to hold Tile data"""
        if imgfile is not None:
            self.filespec = imgfile
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

    def getFilespec(self):
        return self.filespec

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

    def convert(self, filespec, format):
        #epdb.set_trace()
        if os.path.exists(filespec) is False:
            return filespec
        type = filetype.guess(filespec).extension
        if type == "format":
            return filespec
        newfilespec = filespec.replace("." + type, "." + format)
        if os.path.exists(newfilespec):
            return newfilespec

        #logging.info("Converting %s to %s", (filespec, os.path.basename(newfilespec)))
        if type != "jpg":
            opts = gdal.TranslateOptions(rgbExpand='RGBA', format='JPEG')
        else:
            opts = gdal.TranslateOptions(format='GTIFF')
        ds1 = gdal.Translate(newfilespec, filespec, options=opts)
        return newfilespec

    def readTile(self, filespec):
        """Load the image into memory"""
        filespec = self.convert(filespec, "jpg")
        logging.debug("Reading tile %r into memory" % filespec)
        try:
            file = open(filespec, "rb")
        except:
            logging.error("Couldn't read tile %s" % filespec)
            return bytes()
        #bytes = file.read(253210)
        self.blob = file.read()
        file.close()
        return self.blob

    def writeTile(self, path):
        """Write the image to disk"""
        filespec = "%s/%s/%s/%s/%s.png" % (path, self.z, self.x, self.y, self.y)
        if os.path.exists(filespec) is False:
            tmp = ""
            for i in os.path.dirname(filespec).split('/'):
                tmp += i + '/'
                if os.path.exists(tmp) is False:
                    os.mkdir(tmp)
        file = open(filespec, "wb")
        bytes = self.blob
        logging.debug("Writing %r bytes to %r" % (len(bytes), filespec))
        file.write(bytes)
        file.close()
        suffix = filetype.guess(filespec)
        print('File extension: %s' % suffix.extension)
        if suffix.extension == 'jpg':
            dest = filespec.replace(".png", ".jpg")
            logging.debug("Renaming %r to %r" % (filespec, dest))
            os.rename(filespec, dest)

        foo = mercantile.bounds(self.y, self.x, self.z + 12)
        logging.info("Wrote %r" % filespec)
        return True

    def dump(self):
        if self.blob is not None:
            image = "not loaded"
        else:
            image = "loaded"
        print("X=%s, Y=%s, Z=%s, Image is %s" % (self.z, self.x, self.y, image))

class Tiledb(object):
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
            self.zooms = ( 15, 16, 17 )
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
        if os.path.exists(filespec):
            # rgbExpand=rgba
            if "ERSI" not in filespec:
                opts = gdal.TranslateOptions(rgbExpand='RGBA', GCPs=gcpList, format='GTiff')
            else:
                opts = gdal.TranslateOptions(GCPs=gcpList, format='GTiff')

            ds1 = gdal.Translate(tmpfile, imgfile, options=opts)
            #gdal.Warp(outfile, ds1, format='GTiff', xRes=30, yRes=30)
            gdal.Warp(outfile, ds1, format='GTiff', dstSRS='EPSG:4326')
            self.tifs.append(outfile)
            os.remove(tmpfile)
            #print(gdal.Info(outfile))

    def download(self, mirrors=None, tiles=None):
        """ Download the specified tiles from the list of mirrors"""
        if mirrors is None:
            logging.error("You need to specify a URL!")
            return None
        if tiles is None:
            logging.error("You need to specify a tile!")
            return None

        counter = 0
        logging.info("Contains %r tiles"  % len(tiles))
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
            worked = False
            if os.path.exists(filespec) is False:
                try:
                    #logging.debug("Downloading %r/%r!" % (self.dest, path))
                    dl = SmartDL(fixed, dest=self.dest, connect_default_logger=True)
                    #logging.debug("SmartDL DEST: %r" % fixed[0])
                    dl.start()
                except:
                    logging.error("Couldn't download from %r!" %  dl.get_errors())
                    self.errors += 1
                    worked = False
                    logging.debug("Errors: %r %r" % (self.errors, len(tiles)))
                try:
                    if dl.isSuccessful():
                        print(".")
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
                        worked = True
                except:
                    worked = False

            counter += 1
            logging.debug("Processed %r out of %r tile. %r% done" % (counter, len(tiles), counter/len(tiles)))
            self.createVRT(filespec, tile)

        logging.info("Had %r errors downloading %d tiles for data for %r" % (self.errors, len(tiles), os.path.basename(self.storage)))
        return True
        
    def formatPath(self, tile=None):
        if tile is None:
            logging.error("You need to supply a tile!")
            return None
        path = "%s/%s/%s/%s" % (self.storage, tile.z, tile.x, tile.y)
        return path

    def writeTifs(self, filespec):
        outfile = open(filespec, 'w')
        for file in self.tifs:
            outfile.write(file + '\n')
        outfile.close()
        logging.info("Wrote cache file %r" % filespec)

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

    def mosaic(self, tiles=list()):
        """Merge all the tiles together to form the basemap"""

        logging.debug("Opening cache file %r" % self.storage + str(level) + ".txt")
        #cnf = open(self.storage + str(level) + ".txt", "w")
        files = list()
        for tile in tiles:
            path = self.formatPath(tile) + "/" + str(tile.y) + ".tif"
            if os.path.exists(path):
                files.append(path)
        #         if tile.z == int(level):
        #             cnf.write(self.formatPath(tile) + "/" + str(tile.y) + ".tif\n")
        #     # logging.debug("Closing cache file %r" % self.storage + str(level) + ".txt")
        #     cnf.close()

        rios = list()
        #epdb.set_trace()
        for file in files:
            src = rasterio.open(file)
            #logging.debug("Y: %r" % file)
            rios.append(src)

            # Merge function returns a single mosaic array and
            # the transformation info
            mosaic, out_trans = merge(rios)
            out_meta = src.meta.copy()
            #src.close()

            # Update the metadata
            out_meta.update({"driver": "GTiff",
                             "height": mosaic.shape[1],
                             "width": mosaic.shape[2],
                             "transform": out_trans,
                             "crs": "+proj=utm +zone=35 +ellps=GRS80 +units=m +no_defs "
            }
            )

            #cmd = [ "gdal_merge.py", levels[level], "-o foobar.pdf", "-of PDF" ]
            #ppp = Popen(cmd, stdout=PIPE, bufsize=0, close_fds=ON_POSIX)
            #dest.colorinterp = [ ColorInterp.red, ColorInterp.green, ColorInterp.blue]
            name = os.path.basename(self.storage + file)
            print("FIXME: %r" % name)
            with rasterio.open(name + ".tif", "w", **out_meta) as dest:
                try:
                    dest.write(mosaic)
                except:
                    logging.error("Out of memory")
