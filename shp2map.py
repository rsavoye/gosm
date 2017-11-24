#!/usr/bin/python3

# 
#   Copyright (C) 2017   Free Software Foundation, Inc.
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

# This is a simple bourne shell script to convert raw OSM data files into
# pretty KML. This way when the KML file is loaded into an offline mapping
# program, all the colors mean something. For example, ski trails and
# bike/hiking trails have difficulty ratings, so this changes the color
# of the trail. For skiing, this matches the colors the resorts use. Same
# for highways. Different types and surfaces have tags signifying what type
# it is.

# from sys import os
# cwd = os.getcwd()
# sys.path.append(cwd + '/../subdirA/')

import os
import sys
from sys import argv
sys.path.append(os.path.dirname(argv[0]) + '/osmpylib')
import getopt
import logging
import osm
import shp
import config


class config(object):
    """Config data for this program."""
    def __init__(self, argv):
        # Read the config file to get our OSM credentials, if we have any
        file = os.getenv('HOME') + "/.gosmrc"
        try:
            gosmfile = open(file, 'r')
        except:
            logging.warning("Couldn't open %s for writing! not using OSM credentials" % file)
            return

        # Default values for user options
        self.options = dict()
        self.options['logging'] = True
        self.options['limit'] = 0
        self.options['format'] = "osm"
        self.options['user'] = ""
        self.options['uid'] = 0
        self.options['dump'] = False
        self.options['verbose'] = False
        self.options['infile'] = os.path.dirname(argv[0])
        self.options['outdir'] = "/tmp/"
        self.options['outfile'] = self.options['outdir'] + "tmp." + self.options.get('format')
        self.options['convfile'] = os.path.dirname(argv[0]) + "/default.conv"

        if len(argv) <= 2:
            self.usage(argv)

        try:
            (opts, val) = getopt.getopt(argv[1:], "h,o:,i:,f:,v,c:,d",
                ["help", "format=", "outfile", "infile", "verbose", "convfile", "dump"])
        except getopt.GetoptError as e:
            logging.error('%r' % e)
            self.usage(argv)
            quit()

        for (opt, val) in opts:
            if opt == '--help' or opt == '-h':
                self.usage(argv)
            elif opt == '--format' or opt == '-f':
                self.options['format'] = val
                format = val
            elif opt == "--outfile" or opt == '-o':
                self.options['outfile'] = val
            elif opt == "--infile" or opt == '-i':
                self.options['infile'] = val
            elif opt == "--verbose" or opt == '-v':
                self.options['verbose'] = True
                logging.basicConfig(filename='shp2map.log',level=logging.DEBUG)
            elif opt == "--dump" or opt == '-d':
                self.options['dump'] = True
            elif opt == "convfile" or opt == '-c':
                self.options['convfile'] = val

        try:
            lines = gosmfile.readlines()
        except:
            logging.error("Couldn't read lines from %s" % gosmfile.name)

        for line in lines:
            if line[1] == '#':
                continue
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
            if name == "infile":
                self.options['infile'] = value[:index - 1]
            if name == "outfile":
                self.options['outfile'] = value[:index - 1]
            if name == "convfile":
                self.options['convfile'] = value[:index - 1]

    def get(self, opt):
        try:
            return self.options[opt]
        except:
            return False

    # Basic help message
    def usage(self, argv):
        print(argv[0] + ": options: ")
        print("""\t--help(-h)   Help
\t--format[-f]  output format [osm, kml, cvs] (default=osm)
\t--user          OSM User name (optional)
\t--uid           OSM User ID (optional)
\t--dump{-d)      Dump the Shape fields
\t--outfile(-o)   Output file name
\t--infile(-i)    Input file name
\t--convfile(-c)  Conversion data file name
\t--limit(-l)     Limit the output records
\t--verbose(-v)   Enable verbosity
        """)
        quit()

    def dump(self):
        logging.info("Dumping config")
        for i, j in self.options.items():
            print("\t%s: %s" % (i, j))


dd = config(argv)
dd.dump()

# The logfile contains multiple runs, so add a useful delimiter
logging.info("-----------------------\nStarting: %r " % argv)

# if verbose, dump to the terminal as well as the logfile.
if dd.get('verbose') == 1:
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    root.addHandler(ch)

# Read Shape (ERSI) file
shp = shp.shpfile(dd)
if dd.get('infile') == "":
#    infile = "/work/Mapping/Utah/Trails/Trails-new.shp"
    infile = "/work/Mapping/MapData/Gilpin/RoadCenterlines/RoadCenterlines-new"
else:
    infile = dd.get('infile')

shp.open(infile)
if dd.get('dump') is True:
    shp.dump()
    quit()

# Write KML file
if dd.get('format') == 'kml':
    if dd.get('outfile') == "":
        kmlfile = '/tmp/tmp.kml'
    else:
        kmlfile = dd.get('outfile')
    kml = kml.kmlfile()
    kml.open(kmlfile)
    shp.makeKML(osm)

# Write OSM file
elif dd.get('format') == "osm":
    outdir = dd.get('outdir')
    osmfile = dd.get('outfile')
    osm = osm.osmfile(dd, osmfile)
    shp.makeOSM(osm)
    print("Output file: %r" % osmfile)

# Write CSV file
elif dd.get('format') == "csv":
    if dd.get('outfile') == "":
        csvfile = "/tmp/tmp.csv"
    else:
        csvfile = dd.get('outfile')
    csv = csv.osmfile(dd)
    csv.open(csvfile, shp)
    shp.makeCSV(csv)
    print("Output file: %r" % csvfile)

