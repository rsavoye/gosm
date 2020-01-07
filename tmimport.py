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

## \file tiledb.py manage of collection of map tiles.

# ogr2ogr -t_srs EPSG:4326 Roads-new.shp hwy_road_aerial.shp

import os
import sys
import logging
import psycopg2
from sys import argv
sys.path.append(os.path.dirname(argv[0]) + '/osmpylib')
from poly import Poly
from tm import TM,Project,Info,Task
import getopt
from osgeo import gdal,ogr,osr


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
        self.options['poly'] = ""

        try:
            (opts, val) = getopt.getopt(argv[1:], "h,p:,v",
                                        ["help", "poly", "verbose"])
        except getopt.GetoptError as e:
            logging.error('%r' % e)
            self.usage(argv)
            quit()

        for (opt, val) in opts:
            if opt == '--help' or opt == '-h':
                self.usage(argv)
            elif opt == "--poly" or opt == '-p':
                self.options['poly'] = val
            elif opt == "--verbose" or opt == '-v':
                self.options['verbose'] = True
                logging.basicConfig(filename='tiler.log',level=logging.DEBUG)

    def checkOptions(self):
        # make this a nop for now
        pass
         
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
    def usage(self, argv=["tmimport.py"]):
        print("This program reads an OSM poly file, and imports it into the HOT Tasking Manager")
        print(argv[0] + ": options:")
        print("""\t--help(-h)   Help
\t--poly(-p)      Input OSM polyfile
\t--verbose(-v)   Enable verbosity
        """)
        quit()


dd = myconfig(argv)
dd.checkOptions()
# dd.dump()
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

tm = TM()
tm.dump()

poly = Poly(dd.get('poly'))
poly.dump()

project = Project()
query = project.create(id=tm.getNextProjectID(), comment="#tm-senecass", polygon=poly)
#project.dump()
print(query)
tm.query(query)

info = Info()
query = info.create("Testy", tm.getNextProjectID())
#info.dump()
print(query)
tm.query(query)

task = Task()
query = task.create(zoom=11, x=419, y=1271, project_id=tm.getNextProjectID(), id=tm.getNextTaskID())
#task.dump()
print(query)
tm.query(query)

