#!/usr/bin/python3

# 
#   Copyright (C) 2018   Free Software Foundation, Inc.
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

# This script is where you wat to import data, but all the names are all in
# upper cases, which isn't appropriaye for OSM. This fixes addresses
# specifically and nothing else by just capitalizing he first letter of
# every word in the value..
import os
import sys
import re
import string
import logging
import getopt
from config import config
from sys import argv
sys.path.append(os.path.dirname(argv[0]) + '/osmpylib')


class myconfig(config):
    def __init__(self, argv=list()):
        # Default values for user options
        self.options = dict()
        self.options['logging'] = True
        self.options['dump'] = False
        self.options['verbose'] = False
        self.options['infile'] = os.path.dirname(argv[0])
        self.options['outfile'] = "./out.osm"

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
            elif opt == '--filter' or opt == '-f':
                self.options['filter'] = val
            elif opt == "--outfile" or opt == '-o':
                self.options['outfile'] = val
            elif opt == "--infile" or opt == '-i':
                self.options['infile'] = val
            elif opt == "--extra" or opt == '-e':
                self.options['extra'] = val
            elif opt == "--type" or opt == '-t':
                if val == "way" or val == "line":
                    self.options['type'] = val
                else:
                    self.usage(argv)
            elif opt == "--verbose" or opt == '-v':
                self.options['verbose'] = True
                logging.basicConfig(filename='shp2map.log',level=logging.DEBUG)
            elif opt == "--dump" or opt == '-d':
                self.options['dump'] = True
            elif opt == "convfile" or opt == '-c':
                self.options['convfile'] = val

    # Basic help message
    def usage(self, argv):
        print(argv[0] + ": options: ")
        print("""\t--help(-h)   Help
\t--user          OSM User name (optional)
\t--uid           OSM User ID (optional)
\t--dump{-d)      Dump the Shape fields
\t--outfile(-o)   Output file name
\t--infile(-i)    Input file name
\t--verbose(-v)   Enable verbosity
        """)
        quit()
    

dd = myconfig(argv)
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

filespec = dd.get('infile')
file = open(filespec, "r")
filespec = dd.get('outfile')
outfile = open(filespec, "w")
try:
    lines = file.readlines()
    for line in lines:
        newline = line
        # Circle is incomplete
        m = re.search(" Cir\"", line)
        if m is not None:
            newline = line[0:m.start()]
            newline += ' Circle' + '\"/>\n'

        m = re.search(" Ln\"", line)
        if m is not None:
            newline = line[0:m.start()]
            newline += ' Lane' + '\"/>\n'

        m = re.search("Dr\"", line)
        if m is not None:
            newline = line[0:m.start()]
            newline += ' Drive' + '\"/>\n'

        m = re.search(" Pl\"", line)
        if m is not None:
            newline = line[0:m.start()]
            newline += ' Place' + '\"/>\n'
            
        m = re.search(" Rd\"", line)
        if m is not None:
            newline = line[0:m.start()]
            newline += ' Road' + '\"/>\n'

        # This tag is obsolete as of 2012
        #m = re.search("tiger:name_type", line)
        #m = re.search("addr:state", line)
        m = re.search(".*\"[ A-Z][A-Z ]*\"", line)
        # if m is not None:
        length = len(line)
        end = line.find(' v=')
        sub = line[0:end]
        tag = line[10:end - 1]
        match = line[end + 4:length - 4]
        # 4 seems to be a practical length 
        re.search("tiger:name_type", line)
        #if m is None:
        #import epdb ; epdb.set_trace()
        #print("FIXME: %r" % tag)
        if tag == "addr:street" or tag == "addr:full":
            print("FOO: %r" % tag)
            match = match.capitalize()
            match = string.capwords(match)
            newline = sub + ' v="' + match + '\"/>\n'
        if tag == "tiger:name_type":
            type = match
            print("BAR: %r" % type)
            outfile.write(newline)

except Exception as inst:
    print("Couldn't read lines from %s" % filespec)

