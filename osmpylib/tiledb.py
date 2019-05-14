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
from osgeo import gdal,ogr,osr
from urllib.parse import urlparse
import rasterio
from rasterio.merge import merge
from rasterio.enums import ColorInterp
from subprocess import PIPE, Popen, STDOUT
import filetype
from time import sleep
import queue
from datetime import datetime
from datetime import timedelta
import concurrent.futures
import threading
import glob
import shutil


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

    def readTile(self, filespec):
        """Load the image into memory"""
        #filespec = convert(filespec, "jpg")
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
        self.threads = 40       # max number of download threads
        self.cache = None
        self.perms = 0o755
        self.dest = None
        self.tifs = list()
        if top is None:
            self.storage = "./tiledb/"
        else:
            self.storage = top + '/'

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

        logging.debug("Creating VRT for %s" % filespec)
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

        total = len(tiles)
        threads = queue.Queue(maxsize=self.threads)

        with concurrent.futures.ThreadPoolExecutor(max_workers = self.threads) as executor:
            block = 0
            while block <= len(tiles):
                future = executor.submit(dlthread, self.storage, mirrors, tiles[block:block+100])
                #logging.debug("FUTURE: %r" % future.result.running())
                #logging.debug("Block %d:%d" % (block, block + 100))
                block += 100
            executor.shutdown()
        logging.info("Had %r errors downloading %d tiles for data for %r" % (self.errors, len(tiles), os.path.basename(self.storage)))
        return True

    def formatPath(self, tile=None):
        if tile is None:
            logging.error("You need to supply a tile!")
            return None
        path = "%s/%s/%s/%s" % (self.storage, tile.z, tile.x, tile.y)
        return path

    def writeCache(self, tiles, filespec=None):
        if filespec is not None:
            outfile = open(filespec, 'w')
        else:
            outfile = open(self.cache, 'w')

        # Downloaded tiles are usually png or jpg format. The Topo
        # maps use png, Sat imagery is usually jpg. GTifs are
        # produced by this program, but not used for creating an
        # mbtiles or sqlite3 file.
        for tile in tiles:
            file = self.formatPath(tile) + '/' + str(tile.y)
            if os.path.exists(file + ".jpg"):
                outfile.write(file  + ".jpg\n")
            elif os.path.exists(file + ".png"):
                outfile.write(file  + ".png\n")
            else:
                outfile.write(file  + ".tif\n")
        outfile.close()
        logging.info("Wrote cache file %r" % filespec)

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

    def makeLevels(self):
        # $x       cmd = [ "gdal_retile.py", "-pyramidOnly", "-useDirForEachRow", "-levels 3", "-targetDir", "ofoo" ]
        #ppp = Popen(cmd, stdout=PIPE, bufsize=0, close_fds=ON_POSIX)
        #glob.glob("ofoo/1/**", recursive=True)

        zooms = [1, 2, 3]
        for i in zooms:
            template = "ofoo/{0}/**/*.tif"
            pattern = template.format(i)
            files = glob.glob(pattern, recursive=True)
            #print(files)
            # Move from ofoo/1/1... to z/x/y/

            for tif in files:
                ds = gdal.Open(tif)
                if ds is None:
                    logging.error("Tile %s doesn't exist!" % tif)
                    continue
                width = ds.RasterXSize
                height = ds.RasterYSize
                # adfGeoTransform[0] /* top left x */
                # adfGeoTransform[1] /* w-e pixel resolution */
                # adfGeoTransform[2] /* 0 */
                # adfGeoTransform[3] /* top left y */
                # adfGeoTransform[4] /* 0 */
                # adfGeoTransform[5] /* n-s pixel resolution (negative value) */
                gt = ds.GetGeoTransform()
                minx = gt[0]
                miny = gt[3] + width*gt[4] + height*gt[5]
                maxx = gt[0] + width*gt[1] + height*gt[2]
                maxy = gt[3]

                # mercantile.ul()
                #print("%f,%f,%f,%f" % (minx,miny,maxx,maxy))
                m = mercantile.tile(minx, miny,15) # seems to be level 16
                #epdb.set_trace()
                filespec = "./tiledb/ERSI/15/" + str(m.x) + '/' + str(m.y) + '/' + str(m.y) + ".tif"
                dirname = os.path.dirname(filespec)
                # Create the subdirectories as pySmartDL doesn't do it for us
                if os.path.isdir(dirname) is False:
                    tmp = "."
                    paths = dirname.split('/')
                    for i in paths[1:]:
                        tmp += '/' + i
                        if os.path.isdir(tmp):
                            continue
                        else:
                            os.mkdir(tmp)

                #epdb.set_trace()
                shutil.copy(tif, filespec)
                tmp = filespec.replace('.tif', '.jpg')
                logging.debug("Copying %s to %s" % (tif, tmp))
                if not os.path.exists(tmp):
                    jpg = convert(filespec, 'jpg')
                else:
                    jpg = tmp
                #print(tif, jpg, filespec)

def dlthread(dest, mirrors, tiles):
    """Thread to handle downloads for Queue"""
    counter = -1
    errors = 0

    start = datetime.now()

    totaltime = 0.0
    logging.info("Downloading %d tiles in thread %d" % (len(tiles), threading.get_ident())
    )
    template = "{0}/{1}/{2}/{3}"
    db = Tiledb(dest)
    for tile in tiles:
        fixed = ()
        for url in mirrors:
            new = url.format(tile.z, tile.x, tile.y)
            fixed = fixed + (new,)
            
            base = template.format(dest, str(tile.z),  str(tile.x), str(tile.y), str(tile.y), str(tile.y)) + "/"
            path = urlparse(url)[2]
            tmp = os.path.splitext(os.path.basename(fixed[0]))

            ext = tmp[1]
            # If there is no extension, it's a directory. Usually
            # in that case, it's a jpeg. We test the actual file
            # type later after it's downloaded, but this is to test
            # for the existence of an existing file, post download.
            if ext == '':
                ext = ".jpg"
            else:
                ext = ".png"

            filespec = base + str(tile.y) + ext
            counter += 1
            if os.path.exists(filespec):
                logging.debug("tile %s exists" % filespec)
                continue

            dirname = os.path.dirname(filespec)
            # Create the subdirectories as pySmartDL doesn't do it for us
            if os.path.isdir(dirname) is False:
                tmp = ""
                paths = dirname.split('/')
                for i in paths[1:]:
                    tmp += '/' + i
                    if os.path.isdir(tmp):
                        continue
                    else:
                        os.mkdir(tmp)

            # Download the file
            try:
                dl = SmartDL(fixed, dest=dirname, connect_default_logger=True)
                dl.start()
                if dl.isSuccessful():
                    if dl.get_speed() > 0.0:
                        logging.info("Speed: %s" % dl.get_speed(human=True))
                        logging.info("Download time: %r" % dl.get_dl_time(human=True))
                    totaltime +=  dl.get_dl_time()
                    # ERSI does't append the filename
                    totaltime +=  dl.get_dl_time()
                    suffix = filetype.guess(dl.get_dest())
                    print('File extension: %s' % suffix.extension)
                    if suffix.extension == 'jpg':
                        os.rename(dl.get_dest(), filespec)
                        logging.debug("Renamed %r" % dl.get_dest())
                        ext = ".jpg"  # FIXME: probably right, but shouldbe a better test
                    else:
                        ext = tmp[1]
                        counter += 1
            except:
                logging.error("Couldn't download from %r: %s" %  (filespec, dl.get_errors()))
                errors += 1
                continue

            counter += 1
            db.createVRT(filespec, tile)

    end = datetime.now()
    delta = start - end
    logging.debug("%d errors out of %d tiles" % (errors, len(tiles)))
    logging.debug("Processed %d tiles in %d.%d.%d minutes" % (len(tiles), delta.minutes, delta.microseconds))
 
def convert(filespec, format):
    if os.path.exists(filespec) is False:
        return filespec
    type = filetype.guess(filespec).extension
    if type == "format":
        return filespec
    newfilespec = filespec.replace("." + type, "." + format)
    if os.path.exists(newfilespec):
        return newfilespec

    #logging.info("Converting %s to %s", (filespec, os.path.basename(newfilespec)))
    # if type != "jpg":
    opts = gdal.TranslateOptions(format='JPEG')
    #     opts = gdal.TranslateOptions(rgbExpand='RGBA', format='JPEG')
    # else:
    #     opts = gdal.TranslateOptions(format='GTIFF')
    #epdb.set_trace()
    ds1 = gdal.Translate(newfilespec, filespec, options=opts)

    return newfilespec
