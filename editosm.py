#!/usr/bin/python3

# 
#   Copyright (C) 2018, 2019   Free Software Foundation, Inc.
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
import re
import string
import logging
import getopt
import pdb
from sys import argv
sys.path.append(os.path.dirname(argv[0]) + '/osmpylib')

import correct
import osm
from lxml import etree
from lxml.etree import tostring


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
        self.options['dump'] = False
        self.options['verbose'] = False
        self.options['infile'] = os.path.dirname(argv[0])
        self.options['outfile'] = "./out.osm"
        self.options['uid'] = ''
        self.options['user'] = ''

        try:
            (opts, val) = getopt.getopt(argv[1:], "h,o:,i:,v,",
                ["help", "outfile", "infile", "verbose"])
        except getopt.GetoptError as e:
            logging.error('%r' % e)
            self.usage(argv)
            quit()

        for (opt, val) in opts:
            if opt == '--help' or opt == '-h':
                self.usage(argv)
            elif opt == "--outfile" or opt == '-o':
                self.options['outfile'] = val
            elif opt == "--infile" or opt == '-i':
                self.options['infile'] = val
            elif opt == "--verbose" or opt == '-v':
                self.options['verbose'] = True
                logging.basicConfig(filename='shp2map.log',level=logging.DEBUG)

        try:
            lines = gosmfile.readlines()
        except Exception as inst:
            logging.error("Couldn't read lines from %s" % gosmfile.name)

        for line in lines:
            try:
                # Ignore blank lines or comments
                if line is '' or line[1] is '#':
                    continue
            except Exception as inst:
                pass
            # First field of the CSV file is the name
            index = line.find('=')
            name = line[:index]
            # Second field of the CSV file is the value
            value = line[index + 1:]
            index = len(value)
#            print ("FIXME: %s %s %d" % (name, value[:index - 1], index))
            if name == "uid":
                self.options['uid'] = value[:index - 1]
            if name == "user":
                self.options['user'] = value[:index - 1]

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
    def usage(self, argv):
        print(argv[0] + ": options: ")
        print("""\t--help(-h)   Help
\t--user          OSM User name (optional)
\t--uid           OSM User ID (optional)
\t--dump{-d)      Dump the data
\t--outfile(-o)   Output file name
\t--infile(-i)    Input file name
\t--verbose(-v)   Enable verbosity
        """)
        quit()


dd = myconfig(argv)
dd.dump()
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

try:
    filespec = dd.get('infile')
    file = open(filespec, "r")
except Exception as inst:
    print("Couldn't open file %s" % filespec)

infile = dd.get('infile')
outfile = dd.get('outfile')
mod = 'action="modifiy"'

#outfile = open(filespec, "w")

osmout = osm.osmfile(dd, outfile)
osmout.header()

poly = open(infile)

osmout.footer()
