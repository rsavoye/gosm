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
import getopt
import epdb
from sys import argv
sys.path.append(os.path.dirname(argv[0]) + '/osmpylib')
from poly import Poly
from sql import Postgis


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
        self.options['zooms'] = None
        self.options['poly'] = ""
        self.options['source'] = "ersi,topo,usgs,terrain"
        self.options['format'] = "gtiff"
        #self.options['force'] = False
        self.options['outfile'] = "./"
        # FIXME: 
        self.options['mosaic'] = False
        self.options['download'] = False
        self.options['ersi'] = False
        self.options['usgs'] = False
        self.options['topo'] = False
        self.options['terrain'] = False
        self.options['gtiff'] = False
        self.options['pdf'] = False
        self.options['osmand'] = False

        try:
            (opts, val) = getopt.getopt(argv[1:], "h,o:,s:,p:,v,z:,f:,d,m,n",
                ["help", "outfile", "source", "poly", "verbose", "zooms", "format", "download", "mosaic", "nodata"])
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
            elif opt == "--download" or opt == '-d':
                self.options['download'] = True
            elif opt == "--mosaic" or opt == '-m':
                self.options['mosaic'] = True
            elif opt == "--zooms" or opt == '-z':
                self.options['zooms'] = ( val.split(',' ) )
            elif opt == "--format" or opt == '-f':
                self.options['format'] = val
            elif opt == "--nodata" or opt == '-n':
                self.options['nodata'] = True
            elif opt == "--verbose" or opt == '-v':
                self.options['verbose'] = True
                logging.basicConfig(filename='tiler.log',level=logging.DEBUG)

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
    def usage(self, argv=["tiler.py"]):
        print("This program downloads map tiles and the geo-references them")
        print(argv[0] + ": options:")
        print("""\t--help(-h)   Help
\t--outdir(-o)    Output directory for tiles
\t--poly(-p)      Input OSM polyfile
\t--subset(-p)    Subset of data to map
\t--title(-t)     Title
\t--verbose(-v)   Enable verbosity
        """)
        quit()

dd = myconfig(argv)
dd.checkOptions()
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
mod = 'action="modifiy"'

poly = Poly()
bbox = poly.getBBox(dd.get('poly'))
#logging.info("Bounding box is %r" % bbox)

# XAPI uses:
# minimum latitude, minimum longitude, maximum latitude, maximum longitude
xbox = "%s,%s,%s,%s" % (bbox[2], bbox[0], bbox[3], bbox[1])
#logging.info("Bounding xbox is %r" % xbox)
epdb.st()

print("------------------------")
