#!/usr/bin/python3

# 
#   Copyright (C) 2017, 2018   Free Software Foundation, Inc.
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

import os
import sys
import epdb
import logging
import getopt
import re
from sys import argv
sys.path.append(os.path.dirname(argv[0]) + '/osmpylib')
import pgdb
from kml import kmlfile


class config(object):
    """Config data for this program."""
    def __init__(self, argv=list()):
        # Default values for user options
        self.options = dict()
        self.options['logging'] = True
        self.options['operation'] = "split"
        self.options['verbose'] = False
        self.options['root'] = os.path.dirname(argv[0])
        self.options['infiles'] = os.path.dirname(argv[0])
        self.options['outdir'] = "/tmp/"
        self.options['title'] = ""
        self.options['outfile'] = self.options['outdir'] + "tmp.kml"

        if len(argv) <= 2:
            self.usage(argv)

        try:
            (opts, val) = getopt.getopt(argv[1:], "h,o:,i:,v,e:,d:,t:",
                ["help", "outfile", "infiles", "verbose", "directory", "title"])
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
            elif opt == "--directory" or opt == '-d':
                self.options['outdir'] = val
            elif opt == "--title" or opt == '-t':
                self.options['title'] = val
            elif opt == "--verbose" or opt == '-v':
                self.options['verbose'] = True
                with open('plotcalls.log', 'w'):
                    pass
                logging.basicConfig(filename='plotcalls.log', level=logging.DEBUG)
                root = logging.getLogger()
                root.setLevel(logging.DEBUG)

                ch = logging.StreamHandler(sys.stdout)
                ch.setLevel(logging.DEBUG)
                formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                ch.setFormatter(formatter)
                root.addHandler(ch)

    def get(self, opt):
        try:
            return self.options[opt]
        except Exception as inst:
            return False

    # Basic help message
    def usage(self, argv):
        print(argv[0] + ": options: ")
        print("""\t--help(-h)   Help
\t--outfile(-o)   Output file name
\t--infile(-i)   Input file name(s)
\t--verbose(-v)   Enable verbosity
\t--title(-t)     Set output file title
        """)
        quit()

    def set(self, opt, val):
        self.options[opt] = val

    def get(self, opt):
        try:
            return self.options[opt]
        except Exception as inst:
            return False

    def dump(self):
        logging.info("Dumping config")
        for i, j in self.options.items():
            print("\t%s: %s" % (i, j))


class plotcalls(object):
    """Text Processing class."""
    def __init__(self, config):
        self.config = config
        self.file = False
        self.db = pgdb.pgdb(config)
        config.dump()

    def connect(self):
        self.db.connect('LocalRegion')
        
    def query(self, addr):
        return self.db.query(addr)

            
#epdb.set_trace()
dd = config(argv)

fcall = plotcalls(dd)
fcall.connect()

kml = kmlfile()
kml.open(dd.get('outfile'))
kml.header("TLFPD Calls")

calldata = open(dd.get('infile'), 'r')    
lines = calldata.readlines()
for line in lines:
    if line[1] == '#':
        continue
    index = line.find(' ')
    number = line[:index]
    street = line[index + 2:]
    street = street.replace("\n", '')
    street = street.strip()

    query = "SELECT ST_AsKML(way) from planet_osm_point"
    query += " WHERE \"addr:housenumber\"='" + number + "'"
    query += " AND tags->'addr:street'='"+ street + "';"
    logging.info(query)

    foo = ""
    ret = fcall.query(query)
    #epdb.set_trace()
    if len(ret) == 1:
        logging.debug("FIXME: query(%r)" % ret)
        kml.placemark('', 'waypoint', ret[0][0])
    else:
        logging.warning("%r %r Not found!" % (number, street))

kml.footer()
